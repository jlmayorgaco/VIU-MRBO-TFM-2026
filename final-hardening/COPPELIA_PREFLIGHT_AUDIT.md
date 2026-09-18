# COPPELIA_PREFLIGHT_AUDIT — estado real de los gates antes de ejecutar

Fecha: 2026-09-18. Responde A4 y A4.4.
Documentación previa a cualquier ejecución. Ningún `not_executed` se convierte
aquí en `pass`.

---

## 1. Qué hay instalado y qué está construido

| Recurso | Estado | Evidencia |
|---|---|---|
| CoppeliaSim Edu | instalado | `C:\Program Files\CoppeliaRobotics\CoppeliaSimEdu\coppeliaSim.exe` |
| Cliente ZMQ | instalado | módulo `coppeliasim_zmqremoteapi_client` importable |
| Modo headless | soportado | `session.py` con `headless: bool = True` por defecto, añade `-h`; los cuatro `experiments/configs/coppelia_cargo_*.yaml` fijan `headless: true` |
| Escena Cargo | construida | `coppeliasim/real_scenes/cargo_primary_mujoco_v1.ttt`, sha256 `e36a4a91…` |
| Runtime de escena | auditado | `scripts/coppelia_cargo/cargo_primary_scene_runtime.lua`, sha256 `4a8f46a7…` |
| Motor | MuJoCo dentro de CoppeliaSim | `backend_kind: coppeliasim_mujoco` |

### 1.1 La auditoría estática de la escena pasa

`coppeliasim/real_scenes/cargo_primary_mujoco_v1.audit.json`, generada por un
auditor independiente y ligada por hash, reporta `pass: true` en los once
chequeos. Los cuatro que importan para §26 son:

- `no_direct_body_force_calls: true` — la escena no aplica fuerzas al cuerpo por API;
- `pose_setters_confined_to_apply_world: true` — no hay teletransporte de pose durante la simulación;
- `actuation_callback_has_no_mutator: true`;
- `external_wheel_velocity_surface_present: true` — **la única superficie de actuación son las velocidades de rueda**.

Es decir, el requisito de «los comandos de rueda mueven el robot y nada
teletransporta la carga» ya está auditado estáticamente, con hashes. Lo que
falta es la comprobación **dinámica**.

---

## 2. Los nueve gates físicos

Definidos en `src/viu_mrob_tfm/coppelia_cargo/preflight.py`
(`CALIBRATION_GATE_FIELDS` + `OPERATIONAL_GATE_FIELDS`). Umbrales de
`experiments/configs/coppelia_cargo_confirmatory.yaml`. Estado medido en
`results/coppelia_cargo_preflight_minimal_v5/gate_status.json`.

| gate_id | propiedad | estado | evidencia medida | umbral | significado físico | ¿bloquea la confirmatoria? |
|---|---|---|---|---|---|---|
| `config_readback_gate_pass` | El contrato SI aplicado se relee de la escena | **pass** | error abs. máx. `5,55·10⁻¹⁷` | `1·10⁻⁶` | masa, inercia, fricción y geometría son las declaradas | sí |
| `sensor_gate_pass` | Los sensores de fuerza leen el peso estático | **pass** | medido `138,0317` N frente a esperado `138,0758` N; error relativo `3,19·10⁻⁴` | `0,02` | la cadena sensor→marco de carga está calibrada en estático | sí |
| `wheel_drive_force_gate_pass` | El par de junta respeta el límite tangencial por robot | **pass** | `max_robot_drive_force_n = 12,0` | `\|τ_L\|/r+\|τ_R\|/r ≤ F_max` | el actuador no excede su límite declarado | sí |
| `scene_actuation_audit_pass` | Auditoría independiente de ausencia de actuación por pose | **pass** | `audit.json` con `pass: true`, ligado por hash | — | nada mueve la carga salvo el contacto | sí |
| **`force_transmission_gate_pass`** | **Transmisión dinámica del *wrench* a través del contacto** | **`not_executed`** | **sentinela `1,0`** | `0,05` | lo que el certificador pide llega realmente a la carga | **sí** |
| **`wheel_twist_gate_pass`** | **Mapeo de velocidades de rueda a *twist* del chasis** | **`not_executed`** | **sentinela `1,0`** | `0,05` | el robot se mueve por sus ruedas y con la cinemática declarada | **sí** |
| `contact_gate_pass` | Ciclo de trabajo de contacto | no reportado en v5 | — | `contact_duty_min = 0,95` | los apoyos permanecen en contacto | sí |
| `slip_gate_pass` | Deslizamiento relativo en los apoyos | no reportado en v5 | — | `max_relative_slip_m = 0,02` | la carga no resbala sobre los pads | sí |
| `collision_gate_pass` | Colisiones ajenas a los contactos declarados | no reportado en v5 | — | `collision_count_max = 0` | — | sí |
| `terminal_gate_pass` | Desempeño terminal | no reportado en v5 | — | pos. `0,10` m, guiñada `0,0873` rad, vel. `0,12` m/s y `0,10` rad/s, permanencia `1,00` s | la misión termina donde y como debe | sí |

Además, fuera de los nueve:

| comprobación | estado | medido | umbral |
|---|---|---|---|
| `dt_sensitivity` | **fail** | un único `dt = 0,005` s; el propio artefacto se autodescribe `single_dt_repeat_only_not_a_sensitivity_study` | dispersión pos. `0,05` m, guiñada `0,05` rad, desacuerdo de éxito `0` |
| `paired_execution_repeatability` | pass | dispersión `0,0` m y `0,0` rad | `0,01` m, `0,01745` rad |

---

## 3. Por qué los dos gates críticos están en `not_executed`

**No es que hayan fallado una medición: es que la medición no existe.**

`scripts/coppelia_cargo/cargo_primary_scene_runtime.lua`, en
`publishPartialCalibration()`, publica literalmente:

```lua
local report = {
    status = 'partial_static_only',
    sensor_static_relative_error = staticError,   -- se mide de verdad
    force_transmission_relative_error = 1.0,
    force_transmission_status = 'not_executed',
    wheel_twist_relative_error = 1.0,
    wheel_twist_status = 'not_executed',
    ...
}
```

con el comentario: *«Wheel-to-twist calibration and independent no-pose audit are
separate preflight steps. The sentinel value and explicit status keep their
gates closed; they are never presented as measured successes.»*

Y `SCENE_CONTRACT.md` lo refuerza: *«La transmisión dinámica de fuerza es un
ensayo distinto: el error estático no se reutiliza y el gate permanece cerrado
con estado `not_executed` hasta medirlo.»*

Esto es exactamente la disciplina que A4.1 exige —que el gate demuestre algo más
fuerte que «el sensor devuelve un número»— y el proyecto ya la había adoptado.
La consecuencia es que **abrir los dos gates requiere implementar la medición**,
no ejecutar un guion existente.

### 3.1 El coste real de implementarlos

La escena está sellada por hash en tres puntos:

- `runtime_sha256_matches_embedded_scene_contract`
- `runtime_sha256_matches_manifest_input`
- `scene_sha256_matches_manifest`

Modificar el Lua invalida los tres. La vía correcta es: escribir la medición,
reconstruir la escena con `build_cargo_primary_scene.py`, volver a pasar
`audit_cargo_runtime_contract.py`, actualizar el manifiesto y **luego** medir.
Es trabajo de ingeniería real con riesgo de romper una cadena de procedencia que
hoy está intacta.

### 3.2 La vía alternativa que sí es ejecutable hoy

Existe una segunda pila de CoppeliaSim, independiente de la escena Cargo:

| guion | qué mide | criterio declarado |
|---|---|---|
| `scripts/smoke_coppelia_calibracion.py` | **Transmisión de fuerza sobre carga estática**: la carga no puede moverse, luego toda la fuerza del empujador aparece como fuerza de contacto | `\|F_medida − F_mandada\|/F_mandada ≤ 5 %` **para cada fuerza ensayada** |
| `scripts/smoke_coppelia_transporte.py` | *Wrench* que la carga recibe realmente a través de los contactos frente al pedido por el certificador | contraste pedido/recibido |
| `scripts/smoke_coppelia_wrench.py` | Lectura de un peso conocido por el sensor de fuerza | — |
| `scripts/smoke_coppelia_session.py` | Sesión, sincronía y selector de motor | — |
| `scripts/smoke_coppelia_banco.py` | Rejilla de aceptación/rechazo para medir falsos positivos y negativos | — |

`smoke_coppelia_calibracion.py` mide **exactamente la propiedad del gate 5** (al
mismo 5 %) y ensaya **varios niveles de fuerza**, que es lo que A4.1 pide. Pero
lo hace sobre `viu_mrob_tfm.coppelia.escena.EscenaTransporte`, una escena
construida por programa, **no** sobre `cargo_primary_mujoco_v1.ttt`.

La cabecera del propio guion documenta por qué existe: *«Sin este cierre, ningún
número del banco vale: la primera matriz de confusión dio 4 falsos positivos de
6 que eran puro rozamiento de los empujadores.»*

---

## 4. Decisión del gate

**`COPPELIA_GATE_BLOCKED` para la campaña confirmatoria Cargo de 16 celdas.**

Motivo, en una frase: los gates de transmisión de fuerza y de rueda→*twist* no
están implementados en la escena sellada, y ejecutar la campaña sin ellos sería
precisamente «lanzar la gran campaña fingiendo que el modelo es válido».

Lo que **sí** puede hacerse sin tocar la escena sellada, y se hará en cuanto la
campaña del juego de integración libere CPU:

1. Ejecutar `smoke_coppelia_calibracion.py` con al menos dos niveles de carga,
   registrando comando, stdout, versión y checksums. Da evidencia de
   transmisión de fuerza **en el motor**, no en la escena Cargo.
2. Ejecutar `smoke_coppelia_transporte.py` para contrastar *wrench* pedido
   contra recibido.
3. Registrar el resultado como **nivel de evidencia de motor**, nunca como
   apertura del gate Cargo ni como validación física.

Lo que **no** se hará: ni lanzar las 16 celdas, ni reescribir el Lua sellado en
la recta final, ni reutilizar el error estático (0,032 %) como si fuera el error
de transmisión dinámica. El contrato de escena prohíbe explícitamente esto
último y tiene razón.

### 4.1 Consecuencia para las afirmaciones del TFM

El nivel de evidencia de CoppeliaSim **no sube** en esta fase. La memoria debe
seguir diciendo lo que ya dice: reproducción geométrica y de reejecución
cinemática, con una semilla, sin validación física ni dinámica independiente.

Se añade, eso sí, una limitación que hoy no está escrita y que el tribunal
agradecerá ver: *la escena Cargo instrumentada existe y está auditada
estáticamente, pero su calibración dinámica de transmisión de fuerza y de
rueda→twist queda pendiente, y por eso la campaña confirmatoria de 16 celdas no
se ejecutó.* Eso es un resultado negativo honesto, no una omisión.
