-- Reproducible Cargo scene builder and structural validator for CoppeliaSim 4.10.

local sim = require 'sim'
local json = require 'dkjson'

local GENERATOR_VERSION = 'cargo-primary-scene-v1'
local EXPECTED_ALIASES = {
    '/CargoPrimary/payload',
    '/CargoPrimary/R1', '/CargoPrimary/R1/leftMotor', '/CargoPrimary/R1/rightMotor', '/CargoPrimary/R1/supportSensor',
    '/CargoPrimary/R2', '/CargoPrimary/R2/leftMotor', '/CargoPrimary/R2/rightMotor', '/CargoPrimary/R2/supportSensor',
    '/CargoPrimary/R3', '/CargoPrimary/R3/leftMotor', '/CargoPrimary/R3/rightMotor', '/CargoPrimary/R3/supportSensor',
    '/CargoPrimary/R4', '/CargoPrimary/R4/leftMotor', '/CargoPrimary/R4/rightMotor', '/CargoPrimary/R4/supportSensor',
}

local function named(name)
    local value = sim.getNamedStringParam(name)
    if value == nil or #value == 0 then error('missing named parameter ' .. name) end
    return tostring(value)
end

local function readFile(path)
    local handle, reason = io.open(path, 'rb')
    if not handle then error('cannot open ' .. path .. ': ' .. tostring(reason)) end
    local value = handle:read('*a')
    handle:close()
    return value
end

local function writeJson(path, value)
    local handle, reason = io.open(path, 'wb')
    if not handle then error('cannot write ' .. path .. ': ' .. tostring(reason)) end
    handle:write(json.encode(value, {indent = true}))
    handle:write('\n')
    handle:close()
end

local function color(shape, rgb)
    sim.setShapeColor(shape, nil, sim.colorcomponent_ambient_diffuse, rgb)
end

local function configureShape(shape, static, respondable, mass)
    sim.setObjectInt32Param(shape, sim.shapeintparam_static, static and 1 or 0)
    sim.setObjectInt32Param(shape, sim.shapeintparam_respondable, respondable and 1 or 0)
    if mass then sim.setShapeMass(shape, mass) end
    sim.setObjectSpecialProperty(
        shape,
        sim.objectspecialproperty_collidable | sim.objectspecialproperty_measurable |
            sim.objectspecialproperty_detectable_all | sim.objectspecialproperty_renderable
    )
end

local function directChild(parent, objectType, alias)
    local result = {}
    -- bit0 excludes the base and bit1 restricts the query to immediate
    -- children.  This avoids path ambiguities inside the nested P3DX model.
    for _, handle in ipairs(sim.getObjectsInTree(parent, objectType, 3)) do
        if sim.getObjectAlias(handle) == alias then result[#result + 1] = handle end
    end
    if #result ~= 1 then
        local observed = {}
        for _, handle in ipairs(sim.getObjectsInTree(parent, sim.handle_all, 3)) do
            observed[#observed + 1] = sim.getObjectAlias(handle) .. ':' .. tostring(sim.getObjectType(handle))
        end
        error(
            'expected one direct child named ' .. alias .. ', found ' .. tostring(#result) ..
                '; direct children={' .. table.concat(observed, ', ') .. '}'
        )
    end
    return result[1]
end

local function findMotor(root, token)
    local matches = {}
    for _, joint in ipairs(sim.getObjectsInTree(root, sim.sceneobject_joint, 0)) do
        local alias = string.lower(sim.getObjectAlias(joint))
        if string.find(alias, token, 1, true) then matches[#matches + 1] = joint end
    end
    if #matches ~= 1 then
        local aliases = {}
        for _, joint in ipairs(sim.getObjectsInTree(root, sim.sceneobject_joint, 0)) do
            aliases[#aliases + 1] = sim.getObjectAlias(joint)
        end
        error('could not identify unique ' .. token .. ' in {' .. table.concat(aliases, ', ') .. '}')
    end
    return matches[1]
end

local function wheelShapes(motor)
    local result = {}
    for _, shape in ipairs(sim.getObjectsInTree(motor, sim.sceneobject_shape, 1)) do
        result[#result + 1] = shape
    end
    if #result == 0 then error('motor has no wheel shape descendant') end
    return result
end

local function disableModelScripts(root)
    local scripts = sim.getObjectsInTree(root, sim.sceneobject_script, 1)
    if #scripts > 0 then sim.removeObjects(scripts) end
end

local function buildRobot(root, pioneerModel, index, offset, supportZ, payload)
    local robot = sim.loadModel(pioneerModel)
    disableModelScripts(robot)
    sim.setObjectAlias(robot, 'R' .. tostring(index))
    sim.setObjectParent(robot, root, true)
    local z = sim.getObjectPosition(robot, sim.handle_world)[3]
    sim.setObjectPosition(robot, {offset[1], offset[2], z}, sim.handle_world)
    sim.setObjectOrientation(robot, {0, 0, 0}, sim.handle_world)

    local left = findMotor(robot, 'leftmotor')
    local right = findMotor(robot, 'rightmotor')
    sim.setObjectAlias(left, 'leftMotor')
    sim.setObjectAlias(right, 'rightMotor')
    for _, motor in ipairs({left, right}) do
        sim.setJointMode(motor, sim.jointmode_dynamic)
        sim.setObjectInt32Param(motor, sim.jointintparam_dynctrlmode, sim.jointdynctrl_velocity)
        sim.setJointTargetVelocity(motor, 0.0)
        -- max_drive_force_n is a per-robot traction envelope.  Each of the
        -- two drive wheels receives half of it, converted from N to N m.
        sim.setJointTargetForce(motor, 0.5 * 12.0 * 0.0975)
    end

    local sensor = sim.createForceSensor(0, {0, 1, 10, 0, 0}, {0.06, 10000, 10000, 0, 0})
    sim.setObjectAlias(sensor, 'supportSensor')
    sim.setObjectParent(sensor, robot, true)
    sim.setObjectPosition(sensor, {offset[1], offset[2], supportZ - 0.06}, sim.handle_world)
    sim.setObjectOrientation(sensor, {0, 0, 0}, sim.handle_world)

    -- MuJoCo requires a shape on both sides of this force sensor.  Without
    -- this finite-mass spacer the immediately consecutive yaw joint leaves
    -- both the sensor and joint outside the dynamic tree.
    local spacer = sim.createPrimitiveShape(sim.primitiveshape_cuboid, {0.10, 0.10, 0.04}, 0)
    sim.setObjectAlias(spacer, 'sensorSpacer')
    configureShape(spacer, false, false, 0.50)
    color(spacer, {0.25, 0.75, 0.35})
    sim.setObjectParent(spacer, sensor, true)
    sim.setObjectPosition(spacer, {offset[1], offset[2], supportZ - 0.02}, sim.handle_world)

    local yaw = sim.createJoint(sim.joint_revolute, sim.jointmode_dynamic, 0, {0.05, 0.08})
    sim.setObjectAlias(yaw, 'passiveYaw')
    sim.setObjectInt32Param(yaw, sim.jointintparam_dynctrlmode, sim.jointdynctrl_free)
    sim.setObjectParent(yaw, spacer, true)
    sim.setObjectPosition(yaw, {offset[1], offset[2], supportZ - 0.02}, sim.handle_world)
    sim.setObjectOrientation(yaw, {0, 0, 0}, sim.handle_world)

    local pad = sim.createPrimitiveShape(sim.primitiveshape_cuboid, {0.16, 0.16, 0.04}, 0)
    sim.setObjectAlias(pad, 'supportPad')
    configureShape(pad, false, false, 0.05)
    color(pad, {0.95, 0.55, 0.10})
    sim.setObjectParent(pad, yaw, true)
    sim.setObjectPosition(pad, {offset[1], offset[2], supportZ + 0.02}, sim.handle_world)

    local padLoop = sim.createDummy(0.025)
    sim.setObjectAlias(padLoop, 'padLoop')
    sim.setObjectParent(padLoop, pad, true)
    sim.setObjectPosition(padLoop, {offset[1], offset[2], supportZ + 0.04}, sim.handle_world)
    local payloadLoop = sim.createDummy(0.025)
    sim.setObjectAlias(payloadLoop, 'payloadLoopR' .. tostring(index))
    sim.setObjectParent(payloadLoop, payload, true)
    sim.setObjectPosition(payloadLoop, {offset[1], offset[2], supportZ + 0.04}, sim.handle_world)
    sim.setLinkDummy(padLoop, payloadLoop)
    sim.setObjectInt32Param(padLoop, sim.dummyintparam_dummytype, sim.dummytype_dynloopclosure)
    sim.setObjectInt32Param(payloadLoop, sim.dummyintparam_dummytype, sim.dummytype_dynloopclosure)

    local wheels = {}
    for _, shape in ipairs(wheelShapes(left)) do wheels[#wheels + 1] = shape end
    for _, shape in ipairs(wheelShapes(right)) do wheels[#wheels + 1] = shape end
    local collisionShapes = {}
    for _, shape in ipairs(sim.getObjectsInTree(robot, sim.sceneobject_shape, 0)) do
        collisionShapes[#collisionShapes + 1] = shape
    end
    sim.setReferencedHandles(robot, wheels, 'viu.cargo.wheelShapes')
    sim.setReferencedHandles(robot, collisionShapes, 'viu.cargo.collisionShapes')
    sim.setReferencedHandles(robot, {yaw}, 'viu.cargo.passiveYaw')
    sim.setReferencedHandles(robot, {padLoop}, 'viu.cargo.padLoop')
    sim.setReferencedHandles(robot, {payloadLoop}, 'viu.cargo.payloadLoop')
    sim.setReferencedHandles(robot, {spacer, pad}, 'viu.cargo.supportTareShapes')
    return {
        base = robot,
        left = left,
        right = right,
        sensor = sensor,
        spacer = spacer,
        yaw = yaw,
        pad = pad,
        padLoop = padLoop,
        payloadLoop = payloadLoop,
        wheelShapes = wheels,
    }
end

local function buildScene(output, pioneerModel, runtimePath)
    sim.setInt32Param(sim.intparam_dynamic_engine, 4)
    if sim.getInt32Param(sim.intparam_dynamic_engine) ~= 4 then error('MuJoCo engine selection failed') end
    sim.setFloatParam(sim.floatparam_simulation_time_step, 0.005)
    local root = sim.createDummy(0.04)
    sim.setObjectAlias(root, 'CargoPrimary')

    local floor = sim.createPrimitiveShape(sim.primitiveshape_cuboid, {8.0, 5.0, 0.10}, 0)
    sim.setObjectAlias(floor, 'floor')
    configureShape(floor, true, true, nil)
    color(floor, {0.35, 0.38, 0.42})
    sim.setObjectParent(floor, root, true)
    sim.setObjectPosition(floor, {0, 0, -0.05}, sim.handle_world)
    sim.setFloatArrayProperty(floor, 'mujoco.friction', {1.0, 0.005, 0.0001})

    local supportZ = 0.36
    local payload = sim.createPrimitiveShape(sim.primitiveshape_cuboid, {1.10, 0.75, 0.25}, 0)
    sim.setObjectAlias(payload, 'payload')
    configureShape(payload, false, true, 14.0)
    color(payload, {0.12, 0.35, 0.72})
    sim.setObjectParent(payload, root, true)
    sim.setObjectPosition(payload, {0, 0, supportZ + 0.165}, sim.handle_world)

    local offsets = {{-0.45, -0.30}, {-0.45, 0.30}, {0.45, -0.30}, {0.45, 0.30}}
    local robots = {}
    for index, offset in ipairs(offsets) do
        robots[index] = buildRobot(root, pioneerModel, index, offset, supportZ, payload)
    end
    local runtime = sim.createScript(sim.scripttype_simulation, readFile(runtimePath), 0, 'lua')
    sim.setObjectAlias(runtime, 'cargoContract')
    sim.setObjectParent(runtime, root, true)
    sim.writeCustomStringData(
        root,
        'viu.cargo.scene.contract',
        json.encode({
            generator_version = GENERATOR_VERSION,
            actuation_contract = 'wheel_velocity_only',
            calibration_status = 'pending_preflight',
            native_robot_model = 'Pioneer P3DX',
            embedded_runtime_sha256 = named('viuCargoRuntimeSha256'),
        })
    )
    sim.saveScene(output)
end

local function getObject(path)
    local ok, handle = pcall(sim.getObject, path)
    if not ok then error('required alias missing: ' .. path) end
    return handle
end

local function validateScene()
    local aliases = {}
    local distinctHandles = {}
    local distinctHandleCount = 0
    for _, path in ipairs(EXPECTED_ALIASES) do
        local handle = getObject(path)
        if distinctHandles[handle] then error('aliases resolve to the same handle: ' .. path) end
        distinctHandles[handle] = true
        distinctHandleCount = distinctHandleCount + 1
        aliases[path] = {
            object_type = sim.getObjectType(handle),
            persistent_uid = sim.getObjectStringParam(handle, sim.objstringparam_unique_id),
        }
    end
    local payload = getObject('/CargoPrimary/payload')
    if sim.getObjectType(payload) ~= sim.sceneobject_shape then error('payload is not a shape') end
    local sensorCount = 0
    local passiveCount = 0
    local loopCount = 0
    local wheelJointCount = 0
    for index = 1, 4 do
        local prefix = '/CargoPrimary/R' .. tostring(index)
        local base = getObject(prefix)
        local left = getObject(prefix .. '/leftMotor')
        local right = getObject(prefix .. '/rightMotor')
        local sensor = getObject(prefix .. '/supportSensor')
        if sim.getObjectType(left) ~= sim.sceneobject_joint or sim.getObjectType(right) ~= sim.sceneobject_joint then
            error(prefix .. ' wheel aliases are not joints')
        end
        if sim.getObjectType(sensor) ~= sim.sceneobject_forcesensor then
            error(prefix .. ' supportSensor is not a force sensor')
        end
        local spacer = directChild(sensor, sim.sceneobject_shape, 'sensorSpacer')
        local yaw = directChild(spacer, sim.sceneobject_joint, 'passiveYaw')
        if sim.getJointMode(yaw) ~= sim.jointmode_dynamic then error(prefix .. ' passive yaw is not dynamic') end
        directChild(yaw, sim.sceneobject_shape, 'supportPad')
        local wheels = sim.getReferencedHandles(base, 'viu.cargo.wheelShapes')
        if #wheels < 2 then error(prefix .. ' has fewer than two referenced wheel shapes') end
        sensorCount = sensorCount + 1
        passiveCount = passiveCount + 1
        wheelJointCount = wheelJointCount + 2
        local padLoops = sim.getReferencedHandles(base, 'viu.cargo.padLoop')
        local payloadLoops = sim.getReferencedHandles(base, 'viu.cargo.payloadLoop')
        if #padLoops ~= 1 or #payloadLoops ~= 1 then error(prefix .. ' support references missing') end
        if sim.getLinkDummy(padLoops[1]) ~= payloadLoops[1] then error(prefix .. ' dynamic loop is not linked') end
        loopCount = loopCount + 1
    end
    local scripts = sim.getObjectsInTree(getObject('/CargoPrimary'), sim.sceneobject_script, 0)
    if #scripts ~= 1 then error('expected exactly one Cargo runtime script, found ' .. tostring(#scripts)) end
    if sim.getInt32Param(sim.intparam_dynamic_engine) ~= 4 then error('scene engine is not MuJoCo') end
    local persistedContract = json.decode(
        sim.readCustomStringData(getObject('/CargoPrimary'), 'viu.cargo.scene.contract')
    )
    if type(persistedContract) ~= 'table' or not persistedContract.embedded_runtime_sha256 then
        error('scene does not persist the embedded runtime SHA-256')
    end
    return {
        generator_version = GENERATOR_VERSION,
        simulator_version = sim.getInt32Param(sim.intparam_program_version),
        engine = 'mujoco',
        payload_alias = '/CargoPrimary/payload',
        robot_count = 4,
        force_sensor_count = sensorCount,
        passive_yaw_joint_count = passiveCount,
        loop_closure_count = loopCount,
        wheel_joint_count = wheelJointCount,
        runtime_script_count = #scripts,
        actuation_contract = 'wheel_velocity_only',
        calibration_status = 'pending_preflight',
        embedded_runtime_sha256 = persistedContract.embedded_runtime_sha256,
        aliases = aliases,
        required_alias_count = #EXPECTED_ALIASES,
        distinct_alias_handle_count = distinctHandleCount,
        aliases_resolve_to_distinct_handles = distinctHandleCount == #EXPECTED_ALIASES,
    }
end

function sysCall_info()
    return {autoStart = true}
end

local pending = false

local function executeBuilder()
    local statusPath = named('viuCargoStatus')
    local ok, result = xpcall(function()
        local mode = named('viuCargoBuilderMode')
        if mode == 'build' then
            buildScene(
                named('viuCargoOutput'),
                named('viuCargoPioneerModel'),
                named('viuCargoRuntimeScript')
            )
        elseif mode ~= 'validate' then
            error('unknown builder mode ' .. mode)
        end
        local status = validateScene()
        status.status = 'ok'
        status.mode = mode
        status.output = named('viuCargoOutput')
        return status
    end, debug.traceback)
    if ok then
        writeJson(statusPath, result)
        sim.addLog(sim.verbosity_scriptinfos, 'VIU Cargo scene ' .. result.mode .. ' completed')
    else
        writeJson(statusPath, {status = 'error', error = tostring(result)})
        sim.addLog(sim.verbosity_scripterrors, tostring(result))
    end
    sim.quitSimulator(true)
end

function sysCall_init()
    -- Command-line scenes are installed after add-on initialization on 4.10.
    -- Defer one non-simulation callback so validation observes the loaded
    -- scene rather than the transient default scene.
    pending = true
end

function sysCall_nonSimulation()
    if not pending then return end
    local mode = named('viuCargoBuilderMode')
    if mode == 'validate' then
        local present = pcall(sim.getObject, '/CargoPrimary')
        if not present then return end
    end
    pending = false
    executeBuilder()
end
