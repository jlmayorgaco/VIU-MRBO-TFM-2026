-- Runtime contract for cargo_primary_mujoco_v1.ttt.
--
-- World-dependent pose, mass, inertia and friction are written only from
-- sysCall_init, before the dynamics loop begins.  Actuation and sensing
-- callbacks never set object poses.  Wheel target velocity remains the sole
-- command surface used by the external campaign runner.

local sim = require 'sim'
local json = require 'dkjson'

local WORLD_SIGNAL = 'viu_cargo_world_json'
local ACK_SIGNAL = 'viu_cargo_world_ack_json'
local CALIBRATION_SIGNAL = 'viu_cargo_calibration_json'
local SLIP_SIGNAL = 'viu_cargo_relative_slip_json'
local COLLISION_SIGNAL = 'viu_cargo_collision_count'
local OBSERVATION_SIGNAL = 'viu_cargo_observation_json'

local payload
local floor
local robots = {}
local activeCount = 0
local collisionCount = 0
local previousForbiddenCollision = false
local calibrationPublished = false
local payloadMass = 0.0
local runStartTime = 0.0
local calibrationStepCount = 0
local calibrationRequiredSteps = 1
local forceSignRobotOnPayload = 0.0
local sensorVerticalTare = {}
local contactOffsetsBody = {}
local wheelRadius = 1.0
local resetSequence = 0
local worldHash = ''

local function encode(value)
    return json.encode(value, {indent = false})
end

local function object(path)
    return sim.getObject(path)
end

local function rotateVector(matrix, vector)
    return {
        matrix[1] * vector[1] + matrix[2] * vector[2] + matrix[3] * vector[3],
        matrix[5] * vector[1] + matrix[6] * vector[2] + matrix[7] * vector[3],
        matrix[9] * vector[1] + matrix[10] * vector[2] + matrix[11] * vector[3],
    }
end

local function maxAbs(values)
    local result = 0.0
    for _, value in ipairs(values) do result = math.max(result, math.abs(value)) end
    return result
end

local function configureInertia(contract)
    local mass = contract.payload_mass_kg
    local length = 1.10
    local width = 0.75
    local height = 0.25
    local cx = contract.com_offset_body_m[1]
    local cy = contract.com_offset_body_m[2]
    local izz = contract.yaw_inertia_kg_m2
    local ixx = mass * (width * width + height * height) / 12.0 + mass * cy * cy
    local iyy = mass * (length * length + height * height) / 12.0 + mass * cx * cx
    local inertia = {ixx, 0, 0, 0, iyy, 0, 0, 0, izz}
    local frame = {1, 0, 0, cx, 0, 1, 0, cy, 0, 0, 1, 0}
    sim.setShapeMass(payload, mass)
    sim.setShapeInertia(payload, inertia, frame)
    return inertia
end

local function setWheelFriction(mu)
    for _, robot in ipairs(robots) do
        for _, wheel in ipairs(robot.wheelShapes) do
            sim.setFloatArrayProperty(wheel, 'mujoco.friction', {mu, 0.005, 0.0001})
        end
    end
    sim.setFloatArrayProperty(floor, 'mujoco.friction', {1.0, 0.005, 0.0001})
end

local function linkSupport(index, enabled)
    local robot = robots[index]
    if index == 1 then return end
    if enabled then
        sim.setLinkDummy(robot.padLoop, robot.payloadLoop)
        sim.setObjectInt32Param(robot.padLoop, sim.dummyintparam_dummytype, sim.dummytype_dynloopclosure)
        sim.setObjectInt32Param(robot.payloadLoop, sim.dummyintparam_dummytype, sim.dummytype_dynloopclosure)
    else
        sim.setLinkDummy(robot.padLoop, -1)
        sim.setLinkDummy(robot.payloadLoop, -1)
        sim.setObjectInt32Param(robot.padLoop, sim.dummyintparam_dummytype, sim.dummytype_default)
        sim.setObjectInt32Param(robot.payloadLoop, sim.dummyintparam_dummytype, sim.dummytype_default)
    end
end

local function applyWorld(contract)
    activeCount = contract.active_robot_count
    payloadMass = contract.payload_mass_kg
    local pose = contract.initial_pose_m_rad
    local yaw = pose[3]
    local c = math.cos(yaw)
    local s = math.sin(yaw)
    for index, robot in ipairs(robots) do
        local active = index <= activeCount
        linkSupport(index, active)
        if active then
            local offset = contract.contact_offsets_body_m[index]
            local x = pose[1] + c * offset[1] - s * offset[2]
            local y = pose[2] + s * offset[1] + c * offset[2]
            local current = sim.getObjectPosition(robot.base, sim.handle_world)
            sim.setObjectPosition(robot.base, {x, y, current[3]}, sim.handle_world)
            sim.setObjectOrientation(robot.base, {0, 0, yaw}, sim.handle_world)
            local payloadLoopZ = sim.getObjectPosition(robot.payloadLoop, payload)[3]
            sim.setObjectPosition(
                robot.payloadLoop,
                {offset[1], offset[2], payloadLoopZ},
                payload
            )
        else
            local current = sim.getObjectPosition(robot.base, sim.handle_world)
            sim.setObjectPosition(robot.base, {-1.70, 1.45, current[3]}, sim.handle_world)
            sim.setObjectOrientation(robot.base, {0, 0, 0}, sim.handle_world)
        end
        sim.setJointTargetVelocity(robot.leftMotor, 0.0)
        sim.setJointTargetVelocity(robot.rightMotor, 0.0)
        local wheelTorqueLimit = 0.5 * contract.max_drive_force_n * contract.wheel_radius_m
        sim.setJointTargetForce(robot.leftMotor, wheelTorqueLimit)
        sim.setJointTargetForce(robot.rightMotor, wheelTorqueLimit)
    end
    sim.setObjectPosition(payload, {pose[1], pose[2], sim.getObjectPosition(payload, sim.handle_world)[3]}, sim.handle_world)
    sim.setObjectOrientation(payload, {0, 0, yaw}, sim.handle_world)
    local overlapErrors = {}
    for index = 1, activeCount do
        local padPosition = sim.getObjectPosition(robots[index].padLoop, sim.handle_world)
        local payloadPosition = sim.getObjectPosition(robots[index].payloadLoop, sim.handle_world)
        for axis = 1, 3 do
            overlapErrors[#overlapErrors + 1] = padPosition[axis] - payloadPosition[axis]
        end
    end
    local requestedInertia = configureInertia(contract)
    setWheelFriction(contract.friction_coefficient)
    local readMass = sim.getShapeMass(payload)
    local readInertia, readFrame = sim.getShapeInertia(payload)
    local massError = math.abs(readMass - contract.payload_mass_kg)
    local inertiaErrors = {}
    for index = 1, 9 do inertiaErrors[index] = readInertia[index] - requestedInertia[index] end
    local comErrors = {
        readFrame[4] - contract.com_offset_body_m[1],
        readFrame[8] - contract.com_offset_body_m[2],
    }
    local frictionErrors = {}
    local wheelTorqueErrors = {}
    for _, robot in ipairs(robots) do
        for _, wheel in ipairs(robot.wheelShapes) do
            local value = sim.getFloatArrayProperty(wheel, 'mujoco.friction')
            frictionErrors[#frictionErrors + 1] = value[1] - contract.friction_coefficient
        end
        local requestedWheelTorque = 0.5 * contract.max_drive_force_n * contract.wheel_radius_m
        wheelTorqueErrors[#wheelTorqueErrors + 1] = sim.getJointTargetForce(robot.leftMotor) - requestedWheelTorque
        wheelTorqueErrors[#wheelTorqueErrors + 1] = sim.getJointTargetForce(robot.rightMotor) - requestedWheelTorque
    end
    local readbackError = math.max(
        massError,
        maxAbs(inertiaErrors),
        maxAbs(comErrors),
        maxAbs(frictionErrors),
        maxAbs(wheelTorqueErrors),
        maxAbs(overlapErrors)
    )
    local engine = sim.getInt32Param(sim.intparam_dynamic_engine)
    local ack = {
        contract_hash = contract.contract_hash,
        world_hash = contract.world_hash,
        reset_sequence = contract.reset_sequence,
        engine = engine == 4 and 'mujoco' or ('engine_' .. tostring(engine)),
        actuation_contract = 'wheel_velocity_only',
        active_robot_count = activeCount,
        run_start_simulation_time_s = runStartTime,
        readback_max_abs_error = readbackError,
        readback = {
            payload_mass_kg = readMass,
            yaw_inertia_kg_m2 = readInertia[9],
            com_offset_body_m = {readFrame[4], readFrame[8]},
            friction_coefficient = contract.friction_coefficient,
            wheel_target_torque_n_m = 0.5 * contract.max_drive_force_n * contract.wheel_radius_m,
            support_overlap_max_abs_error_m = maxAbs(overlapErrors),
        },
    }
    sim.setStringSignal(ACK_SIGNAL, encode(ack))
    local slips = {}
    for index = 1, activeCount do slips[index] = 0.0 end
    sim.setStringSignal(SLIP_SIGNAL, encode({relative_slip_m = slips}))
    sim.setInt32Signal(COLLISION_SIGNAL, 0)
end

local function forbiddenCollision()
    if sim.checkCollision(payload, floor) > 0 then return true end
    for first = 1, #robots - 1 do
        for second = first + 1, #robots do
            if first <= activeCount and second <= activeCount then
                for _, shapeA in ipairs(robots[first].collisionShapes) do
                    for _, shapeB in ipairs(robots[second].collisionShapes) do
                        if sim.checkCollision(shapeA, shapeB) > 0 then return true end
                    end
                end
            end
        end
    end
    return false
end

local function publishSlip()
    local slips = {}
    for index = 1, activeCount do
        local robot = robots[index]
        local relative = sim.getObjectPosition(robot.padLoop, robot.payloadLoop)
        slips[index] = math.sqrt(relative[1] * relative[1] + relative[2] * relative[2])
    end
    sim.setStringSignal(SLIP_SIGNAL, encode({relative_slip_m = slips}))
    return slips
end

local function publishPartialCalibration()
    calibrationStepCount = calibrationStepCount + 1
    if calibrationPublished or calibrationStepCount < calibrationRequiredSteps then return end
    local signedVertical = 0.0
    local valid = 0
    local dynamicallyEnabled = 0
    local sensorTare = {}
    local totalTareWeight = 0.0
    for index = 1, activeCount do
        local tareWeight = 0.0
        for _, shape in ipairs(robots[index].supportTareShapes) do
            tareWeight = tareWeight + sim.getShapeMass(shape) * 9.81
        end
        sensorTare[index] = tareWeight
        totalTareWeight = totalTareWeight + tareWeight
        if sim.isDynamicallyEnabled(robots[index].sensor) then
            dynamicallyEnabled = dynamicallyEnabled + 1
        end
        local state, force = sim.readForceSensor(robots[index].sensor)
        if state and state > 0 and force then
            local sensorToWorld = sim.getObjectMatrix(robots[index].sensor, sim.handle_world)
            local worldForce = rotateVector(sensorToWorld, force)
            signedVertical = signedVertical + worldForce[3]
            valid = valid + 1
        end
    end
    local expected = payloadMass * 9.81
    local forceSign = signedVertical >= 0 and 1.0 or -1.0
    local measuredRaw = math.abs(signedVertical)
    local measured = math.max(0.0, measuredRaw - totalTareWeight)
    local staticError = 1.0
    if valid == activeCount and expected > 0 then
        staticError = math.abs(measured - expected) / expected
    end
    -- Wheel-to-twist calibration and independent no-pose audit are separate
    -- preflight steps.  The sentinel value and explicit status keep their
    -- gates closed; they are never presented as measured successes.
    local report = {
        status = 'partial_static_only',
        sensor_static_relative_error = staticError,
        force_transmission_relative_error = 1.0,
        force_transmission_status = 'not_executed',
        wheel_twist_relative_error = 1.0,
        wheel_twist_status = 'not_executed',
        force_sign_robot_on_payload = forceSign,
        scene_no_pose_actuation_audited = false,
        scene_pose_audit_status = 'requires_independent_preflight_audit',
        valid_force_sensors = valid,
        dynamically_enabled_force_sensors = dynamicallyEnabled,
        expected_force_n = expected,
        measured_force_raw_n = measuredRaw,
        measured_force_n = measured,
        sensor_vertical_tare_n = sensorTare,
        settling_steps = calibrationStepCount,
        settling_time_target_s = 0.50,
    }
    sim.setStringSignal(CALIBRATION_SIGNAL, encode(report))
    forceSignRobotOnPayload = forceSign
    sensorVerticalTare = sensorTare
    calibrationPublished = true
end

local function publishObservation(slips)
    if not calibrationPublished then return end
    local payloadPosition = sim.getObjectPosition(payload, sim.handle_world)
    local payloadOrientation = sim.getObjectOrientation(payload, sim.handle_world)
    local payloadLinear, payloadAngular = sim.getObjectVelocity(payload)
    local robotPoses = {}
    local wheelSpeeds = {}
    local wheelForces = {}
    local normals = {}
    local contacts = {}
    local activeMask = {}
    local fullSlip = {}
    local wrench = {0.0, 0.0, 0.0}
    for index, robot in ipairs(robots) do
        local robotPosition = sim.getObjectPosition(robot.base, sim.handle_world)
        local robotOrientation = sim.getObjectOrientation(robot.base, sim.handle_world)
        robotPoses[index] = {robotPosition[1], robotPosition[2], robotOrientation[3]}
        wheelSpeeds[index] = {
            sim.getJointVelocity(robot.leftMotor),
            sim.getJointVelocity(robot.rightMotor),
        }
        wheelForces[index] = {
            math.abs(sim.getJointForce(robot.leftMotor)) / wheelRadius,
            math.abs(sim.getJointForce(robot.rightMotor)) / wheelRadius,
        }
        local active = index <= activeCount
        activeMask[index] = active
        fullSlip[index] = active and slips[index] or 0.0
        if active then
            local state, force, torque = sim.readForceSensor(robot.sensor)
            local valid = state and state > 0 and force and torque
            contacts[index] = valid and true or false
            if valid then
                local sensorToPayload = sim.getObjectMatrix(robot.sensor, payload)
                local forceBody = rotateVector(sensorToPayload, force)
                local torqueBody = rotateVector(sensorToPayload, torque)
                for axis = 1, 3 do
                    forceBody[axis] = forceSignRobotOnPayload * forceBody[axis]
                    torqueBody[axis] = forceSignRobotOnPayload * torqueBody[axis]
                end
                normals[index] = math.max(
                    0.0,
                    math.abs(forceBody[3]) - sensorVerticalTare[index]
                )
                wrench[1] = wrench[1] + forceBody[1]
                wrench[2] = wrench[2] + forceBody[2]
                local offset = contactOffsetsBody[index]
                wrench[3] = wrench[3] + torqueBody[3]
                    + offset[1] * forceBody[2] - offset[2] * forceBody[1]
            else
                normals[index] = 0.0
            end
        else
            contacts[index] = false
            normals[index] = 0.0
        end
    end
    sim.setStringSignal(OBSERVATION_SIGNAL, encode({
        reset_sequence = resetSequence,
        world_hash = worldHash,
        simulation_time_s = sim.getSimulationTime(),
        payload_pose_m_rad = {
            payloadPosition[1], payloadPosition[2], payloadOrientation[3],
        },
        payload_twist_m_s_rad_s = {
            payloadLinear[1], payloadLinear[2], payloadAngular[3],
        },
        robot_pose_m_rad = robotPoses,
        wheel_speed_rad_s = wheelSpeeds,
        wheel_drive_force_n = wheelForces,
        measured_wrench_body = wrench,
        normal_force_n = normals,
        contact_active = contacts,
        active_robot_mask = activeMask,
        relative_slip_m = fullSlip,
        collision_count = collisionCount,
    }))
end

function sysCall_init()
    robots = {}
    activeCount = 0
    collisionCount = 0
    previousForbiddenCollision = false
    calibrationPublished = false
    forceSignRobotOnPayload = 0.0
    sensorVerticalTare = {}
    runStartTime = sim.getSimulationTime()
    payload = object('/CargoPrimary/payload')
    floor = object('/CargoPrimary/floor')
    local raw = sim.getStringSignal(WORLD_SIGNAL)
    if not raw or #raw == 0 then error('missing ' .. WORLD_SIGNAL) end
    local contract, _, decodeError = json.decode(raw, 1, nil)
    if decodeError or type(contract) ~= 'table' then error('invalid world JSON: ' .. tostring(decodeError)) end
    calibrationStepCount = 0
    calibrationRequiredSteps = math.ceil(0.50 / contract.dt_s)
    contactOffsetsBody = contract.contact_offsets_body_m
    wheelRadius = contract.wheel_radius_m
    resetSequence = contract.reset_sequence
    worldHash = contract.world_hash
    for index = 1, 4 do
        local prefix = '/CargoPrimary/R' .. tostring(index)
        local robot = {
            base = object(prefix),
            leftMotor = object(prefix .. '/leftMotor'),
            rightMotor = object(prefix .. '/rightMotor'),
            sensor = object(prefix .. '/supportSensor'),
            padLoop = -1,
            payloadLoop = -1,
            wheelShapes = {},
            collisionShapes = {},
            supportTareShapes = {},
        }
        robot.wheelShapes = sim.getReferencedHandles(robot.base, 'viu.cargo.wheelShapes')
        robot.collisionShapes = sim.getReferencedHandles(robot.base, 'viu.cargo.collisionShapes')
        robot.supportTareShapes = sim.getReferencedHandles(robot.base, 'viu.cargo.supportTareShapes')
        robot.padLoop = sim.getReferencedHandles(robot.base, 'viu.cargo.padLoop')[1]
        robot.payloadLoop = sim.getReferencedHandles(robot.base, 'viu.cargo.payloadLoop')[1]
        if not robot.padLoop or not robot.payloadLoop or #robot.supportTareShapes ~= 2 then
            error(prefix .. ' support references missing')
        end
        robots[index] = robot
    end
    applyWorld(contract)
end

function sysCall_actuation()
    -- Intentionally empty.  The external runner is the sole wheel command
    -- source and the scene never applies a body pose or external wrench here.
end

function sysCall_sensing()
    local slips = publishSlip()
    local current = forbiddenCollision()
    if current and not previousForbiddenCollision then collisionCount = collisionCount + 1 end
    previousForbiddenCollision = current
    sim.setInt32Signal(COLLISION_SIGNAL, collisionCount)
    publishPartialCalibration()
    publishObservation(slips)
end

function sysCall_cleanup()
    sim.clearStringSignal(ACK_SIGNAL)
    sim.clearStringSignal(CALIBRATION_SIGNAL)
    sim.clearStringSignal(SLIP_SIGNAL)
    sim.clearStringSignal(OBSERVATION_SIGNAL)
    sim.clearInt32Signal(COLLISION_SIGNAL)
end
