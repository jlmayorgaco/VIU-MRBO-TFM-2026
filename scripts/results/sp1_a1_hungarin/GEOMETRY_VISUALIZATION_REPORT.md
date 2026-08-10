# Reporte de visualización geométrica SP1.A1

Una **geometría espacial** es la distribución probabilística usada para muestrear las posiciones iniciales `(x,y)` de robots y cargas. Las regiones dibujadas describen esos generadores; no son obstáculos.

Las cinco instancias comparten `N`, `K`, `M`, identificadores, masas y cuotas. Solo cambian las posiciones iniciales.

## Comparación

| Geometría | Coste total [m] | Media/slot [m] | P95 normalizado | Libres |
|---|---:|---:|---:|---:|
| uniform | 567.506 | 28.375 | 0.38323 | 10 |
| clustered | 397.519 | 19.876 | 0.23000 | 10 |
| separated | 1045.715 | 52.286 | 0.53277 | 10 |
| ring | 560.611 | 28.031 | 0.25241 | 10 |
| corridor | 250.357 | 12.518 | 0.17403 | 10 |

## Escenarios

### uniform

- Figura: `plots/geometries/uniform_assignment.png`
- Vídeo: `videos/geometries/uniform_recruitment.mp4`
- Coaliciones: `{"L1": ["R16", "R19", "R20"], "L2": ["R4", "R28"], "L3": ["R3", "R15", "R30"], "L4": ["R7", "R24", "R27"], "L5": ["R2", "R8", "R14"], "L6": ["R22", "R23", "R29"], "L7": ["R9", "R18", "R25"]}`

### clustered

- Figura: `plots/geometries/clustered_assignment.png`
- Vídeo: `videos/geometries/clustered_recruitment.mp4`
- Coaliciones: `{"L1": ["R3", "R16", "R26"], "L2": ["R1", "R12"], "L3": ["R15", "R20", "R29"], "L4": ["R8", "R21", "R24"], "L5": ["R5", "R10", "R13"], "L6": ["R2", "R22", "R30"], "L7": ["R18", "R19", "R25"]}`

### separated

- Figura: `plots/geometries/separated_assignment.png`
- Vídeo: `videos/geometries/separated_recruitment.mp4`
- Coaliciones: `{"L1": ["R7", "R12", "R24"], "L2": ["R2", "R28"], "L3": ["R4", "R20", "R29"], "L4": ["R8", "R14", "R18"], "L5": ["R1", "R9", "R30"], "L6": ["R5", "R10", "R15"], "L7": ["R17", "R19", "R23"]}`

### ring

- Figura: `plots/geometries/ring_assignment.png`
- Vídeo: `videos/geometries/ring_recruitment.mp4`
- Coaliciones: `{"L1": ["R21", "R26", "R29"], "L2": ["R28", "R30"], "L3": ["R7", "R9", "R15"], "L4": ["R12", "R13", "R16"], "L5": ["R6", "R8", "R17"], "L6": ["R19", "R24", "R27"], "L7": ["R11", "R14", "R18"]}`

### corridor

- Figura: `plots/geometries/corridor_assignment.png`
- Vídeo: `videos/geometries/corridor_recruitment.mp4`
- Coaliciones: `{"L1": ["R5", "R9", "R16"], "L2": ["R3", "R12"], "L3": ["R10", "R18", "R28"], "L4": ["R13", "R20", "R23"], "L5": ["R7", "R8", "R27"], "L6": ["R6", "R19", "R30"], "L7": ["R14", "R15", "R24"]}`

## Vídeo combinado

`videos/geometries/all_geometries_recruitment.mp4`

## Límite metodológico

**Hungarian produce una asignación lógica estática; el movimiento mostrado es solo una ilustración cinemática.** No valida navegación, evitación de obstáculos, contacto, control ni transporte físico.
