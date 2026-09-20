# Contrato de escena Cargo primaria

Este paquete incluye un generador reproducible y una escena candidata
`cargo_primary_mujoco_v1.ttt`. La validación estructural del generador no
sustituye la revisión visual, la calibración ni el preflight dinámico exigidos
antes de producir evidencia.

La escena debe implementar una carga rígida soportada por cuatro Pioneer P3DX,
un apoyo pasivo de guiñada y un sensor de fuerza por robot. Durante la
simulación, el cliente solo escribe `setJointTargetVelocity` sobre las ocho
ruedas. El script de escena puede aplicar masa, inercia, centro de masa,
fricción y poses iniciales únicamente en la inicialización, nunca para mover la
carga o los robots después de arrancar la dinámica.

Cada rama inserta una masa espaciadora entre sensor y junta para que ambos sean
dinámicamente válidos. Los cuatro apoyos, incluido R1, se unen a la carga con
restricciones *overlap/weld* explícitas; ningún deslizamiento se fija a cero por
construcción. En cada reset, los dummies de la carga se recolocan según los
offsets contractuales y el error de solape entra en el readback SI.

El controlador implementado encadena PD de pose, consignas acotadas de fuerza
por contacto, admitancia del error de *wrench* y velocidades de rueda. Las
consignas de fuerza se realizan indirectamente mediante velocidad y contacto;
no son órdenes de fuerza ni implican realización exacta. Por tanto, esta
campaña puede estimar la capacidad predictiva de las tres guardas bajo un
controlador común, pero no demostrar seguimiento exacto ni optimalidad del
reparto de *wrench*.

## Señales requeridas

- Entrada `viu_cargo_world_json`: contrato SI, semilla, `world_hash`, `dt_s` y
  `contract_hash`, incluido `active_robot_count`. En la coalición mínima R4
  debe quedar estacionado fuera del contacto; en la redundante actúan R1--R4.
- Salida `viu_cargo_world_ack_json`: debe repetir `contract_hash`, declarar
  `engine: mujoco`, `actuation_contract: wheel_velocity_only` y reportar
  `readback_max_abs_error` calculado a partir de lecturas reales de masa,
  inercia, fricción y geometría aplicadas.
- Salida `viu_cargo_calibration_json`: errores relativos de calibración estática
  de sensores, transmisión de fuerza y seguimiento twist–ruedas, además de
  `scene_no_pose_actuation_audited`.
- Salida `viu_cargo_relative_slip_json`: vector `relative_slip_m`, uno por
  apoyo.
- Salida entera `viu_cargo_collision_count`: colisiones acumuladas ajenas a los
  contactos de soporte declarados.
- Salida `viu_cargo_observation_json`: muestra atómica por paso con pose y
  *twist* de carga, poses de robot, velocidades y fuerzas equivalentes de las
  ocho ruedas, lectura transformada de los cuatro sensores, máscara de
  contacto, deslizamiento, colisiones, `world_hash` y `reset_sequence`. El
  backend rechaza una muestra cuyo mundo o secuencia no coincida con el reset
  activo.

Los alias de carga, bases, ruedas y sensores están fijados en
`experiments/configs/coppelia_cargo_confirmatory.yaml`. Un alias ausente, un
motor distinto de MuJoCo, un `dt` no confirmado o cualquier señal/calibración
ausente invalida el ensayo; el runner lo registra como fallo o gate no superado.
El adaptador transforma cada lectura desde el marco local del sensor al marco
de la carga mediante la pose leída en cada muestra. El signo robot→carga se
calibra con la reacción vertical estática y se rechaza si no vale exactamente
`+1` o `-1`; no se suman directamente ejes locales arbitrarios.

La tara vertical de las masas espaciadora/plataforma se obtiene de las masas
leídas en la escena y se conserva junto con la lectura bruta. La transmisión
dinámica de fuerza es un ensayo distinto: el error estático no se reutiliza y
el gate permanece cerrado con estado `not_executed` hasta medirlo.

`robot.max_drive_force_n` es el límite tangencial total por robot/contacto. La
escena lo reparte simétricamente entre sus dos ruedas motrices: el límite de
par de cada junta es `0.5 F_max r`. El backend registra `|tau_L|/r` y
`|tau_R|/r`; el gate exige `|tau_L|/r + |tau_R|/r <= F_max` en toda la corrida.
Este gate no sustituye la calibración rueda--*twist* ni demuestra realización
exacta del *wrench*.

## Gates pendientes de la escena real

Antes de lanzar las 1 440 corridas primarias deben aprobarse, con resultados
guardados, el peso estático (2 %), la transmisión de wrench (5 %), el mapeo de
velocidades de ruedas a twist (5 %), la auditoría de ausencia de actuación por
pose, el readback SI y un piloto de contactos/deslizamiento. Después debe
ejecutarse el barrido de sensibilidad de `dt`. Ninguna salida del backend
determinista es evidencia de CoppeliaSim o del sistema físico.

La campaña confirmatoria requiere conjuntamente `--authorize-confirmatory` y
`--preflight-evidence DIR`. La segunda opción no es una declaración manual: el
runner verifica `manifest.json`, `gate_status.json`, el SHA-256 registrado para
cada artefacto, el snapshot de configuración, las corridas, MuJoCo síncrono,
actuación exclusiva por ruedas y la identidad de protocolo, controlador,
umbrales, escena, auditoría e implementación Python. Reconstruye además la
matriz de diseño y cada contrato SI para contrastar el `ack_contract_hash`; la
auditoría independiente se revalida contra sus artefactos internos. También exige éxito físico
y gates de sensor, transmisión, rueda--twist, readback, fuerza de rueda,
contacto, deslizamiento, colisión y terminal en todas las corridas del
preflight, además de sensibilidad multirrate y repetibilidad aprobadas. Esta
validación ocurre antes de crear el directorio de salida confirmatorio.
Los modos físicos (`backend.kind=coppeliasim_mujoco`) no admiten inyección de
`backend_factory`; esa interfaz queda reservada a dobles deterministas sin valor
físico.

La ausencia de actuación por pose nunca se acepta por autoafirmación del script
de escena. `audit_cargo_runtime_contract.py` verifica de forma independiente
el código, enlaza sus SHA-256 con manifiesto y `.ttt`, y produce el artefacto
que consume el backend para ese gate concreto.
