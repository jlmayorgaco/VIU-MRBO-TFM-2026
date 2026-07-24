# Plan de ejecución — cierre V1.1 y SCALE-QPG V2

## Propósito y entregables

Esta etapa separa dos preguntas falsables:

1. `SP1_TFM_VALIDATION_CLOSURE_v1_1`: cerrar las limitaciones de validación
   detectadas después de `SP1_TFM_FINAL_QUOTA_GAME_BENCHMARK_v1`, sin alterar
   ningún artefacto primario de V1.
2. `SP1_SCALE_QPG_BENCHMARK_v2`: evaluar si un juego de cuotas finito,
   sparse, asíncrono, con compromisos atómicos y comunicación por eventos
   mejora el régimen escalar heterogéneo de alta utilización.

Los paquetes nuevos son:

- `results/sp1_validation/SP1_TFM_VALIDATION_CLOSURE_v1_1`;
- `results/sp1_validation/SP1_SCALE_QPG_BENCHMARK_v2_preview`;
- `results/sp1_validation/SP1_SCALE_QPG_BENCHMARK_v2`.

La rama es `codex/sp1-scale-qpg-validation-v2`, creada desde el commit limpio
de V1 `d0ace5bbead043e55e3592300582f345fc7068e5`. El worktree original,
masivamente sucio, permanece fuera del alcance.

## Fuentes de verdad y alcance

Se aplican, por precedencia, `docs/00_TFM_CHARTER.md`,
`docs/01_VIU_REQUIREMENTS.md`, `docs/02_RESEARCH_MATRIX.md`,
`docs/03_EXPERIMENT_PROTOCOL.md`, `docs/04_CLAIMS_EVIDENCE.md`,
`docs/05_NOTATION.md` y `docs/07_SP_SECTION_TEMPLATE.md`.

El alcance físico sigue siendo reclutamiento estratégico SP1 con capacidad
escalar indivisible. No se simulan contacto, docking, wrench, transporte,
MAPF ni hardware. La notación canónica es:

- `s_i`: compromiso físico entero;
- `p_i^S`: intención sparse sobre el conjunto activo;
- `chi_i`: capacidad escalar del robot;
- `Q_k(s)`: capacidad comprometida a la carga.

GRAPE-S y Pair-GRAPE-S fieles permanecen únicamente en el dominio separado de
servicios discretos. `Weighted-GRAPE` y `Weighted-Pair-GRAPE` son adaptaciones
propias al dominio escalar.

## Arquitectura SCALE-QPG

`SCALE-QPG-LogitBR-LocalAR` mantiene un compromiso entero en todo instante.
La intención Logit solo selecciona propuestas. Cada propuesta usa versiones
de mercado y un protocolo `free/current -> tentative -> committed`; un
conflicto, timeout o incumplimiento produce rollback sin modificar el
compromiso.

El potencial discreto es

`Phi(s) = sum_k V_k(Q_k(s)) - sum_i c_i,s_i
          - gamma_switch sum_i 1[s_i != previous_i]`,

con penalizaciones cuadráticas inferior y superior. Toda aceptación usa la
diferencia exacta del potencial. Después de la exploración Logit se ejecuta
mejor respuesta estricta hasta una época sin aceptaciones y con versiones
estables.

Cada robot almacena únicamente compromisos/versiones/precios para su conjunto
activo de tamaño máximo `L`; no almacena un vector local de longitud `K`.
Los mercados de carga son objetos locales y los mensajes se contabilizan por
evento, ruta, campo y tipo de byte.

La recuperación local construye un universo residual desde las cargas
afectadas y lo expande `h` capas. Solo robots y cargas del universo pueden
cambiar. La variante primaria no usa fallback global. La variante
`SCALE-QPG-LogitBR-GlobalAR` es una ablación explícita.

## Cierre V1.1

### Auditoría post-commit

Se verifica el commit inmutable V1, 2.200/2.200 tareas, 203/203 pruebas,
checksums, configuración, parámetros y manifiesto de tareas. Los archivos
`manifest_final.json`, `audit_final.json` y `checksums_final.sha256` se crean
en V1.1, nunca dentro de V1.

Un commit Git depende criptográficamente del contenido de sus archivos; por
tanto, un archivo versionado no puede contener de forma no circular el hash
del mismo commit que lo contiene. La auditoría registra el commit fuente V1 y
el commit de implementación ejecutado; el hash del commit final de resultados
y el estado limpio se verifican y reportan después de crear dicho commit.

### Experimentos A2--A7

- A2: muestra estratificada reproducible de mundos V1 E2--E7, common random
  numbers y diez semillas con el mismo `AugmentingRecovery`.
- A3: 180 mundos (`3 tamaños x 3 topologías x 20`) y cinco métodos, con
  límites reales de 12.000 rondas/240 s, dwell de 100 y sin recovery.
- A4: ocho bandas objetivo, 50 estados por banda y 500 redondeos por estado.
- A5: denominador homogéneo `max(epsilon, |LP lower bound|`; el delta firmado
  se separa del componente positivo.
- A6: cuatro relojes instrumentados directamente.
- A7: tres recuperaciones sobre eventos inyectados después de un compromiso
  entero factible.

## Diseño experimental SCALE-QPG

Las semillas de calibración `91000--91029`, preview `92000--92004` y
evaluación `93000+` son disjuntas. La calibración usa perfiles
predeclarados, un objetivo lexicográfico y `all_world_cost`; no se calibra por
mundo. Los parámetros elegidos se congelan antes del preview.

El preview contiene 30 mundos:
`N={20,50,100}`, cinco semillas, heterogeneidad media/alta, utilización 0,85,
banda de 10 % y grado objetivo 8.

Diseño full congelado:

- C1: 120 mundos según los conteos `30,30,30,20,10`.
- C2: 160 mundos (`K={5,10,20,40}`, `L={4,8}`, 20 semillas).
- C3: 720 mundos; por tamaño se usan 30, 30 y 20 semillas para cada celda de
  utilización y banda.
- C4: 120 mundos en `(50,10)`, `(100,20)`, `(200,40)`, dos utilizaciones y
  20 semillas por tamaño/utilización.
- C5: 120 mundos en `(100,20)`, régimen objetivo central, cuatro topologías y
  30 semillas.
- C6: 150 mundos, 30 por cada evento.
- C7: 80 mundos nuevos del régimen objetivo central, estratificados como
  30/30/20 en los tres tamaños.
- C8: 400 instancias, 20 por longitud 1--20.
- C9: 80 mundos de servicios discretos con el diseño V1, sin mezclarlos con
  el ranking escalar.

Los métodos escalares son los trece predeclarados en la petición. MILP se
ejecuta hasta el tamaño congelado y LP en todos los tamaños. Todos los métodos
comparten mundo/grafo y los cierres comunes comparten opciones.

## Gates y decisión

El preview es bloqueante. Además de conteos, finitud, resume y mensajería,
exige cero doble asignación, conflictos de versión aceptados, descensos de
potencial y ciclos; el cierre local debe demostrar que no tocó robots/cargas
fuera de su universo.

La superioridad solo se declara si se cumplen conjuntamente los diez gates
del régimen objetivo, incluido Holm. Si no, se informa el trade-off. El
reporte termina con exactamente una conclusión A--F.

## Validación y trazabilidad

Se añaden pruebas unitarias de potencial, compromisos, rollback, versiones,
active sets, ausencia de vector global, localidad, contabilidad, recuperación,
tie-breaking, checkpoints y auditoría. Se ejecutan:

```powershell
python -m pytest -q
python -m viu_mrob_tfm.cli.run_sp1_validation_closure_v1_1 --mode full --workers 6 --resume
python -m viu_mrob_tfm.cli.run_sp1_scale_qpg_v2 --mode preview --workers 6 --resume
python -m viu_mrob_tfm.cli.run_sp1_scale_qpg_v2 --mode full --workers 6 --resume
```

Los datos crudos se guardan en shards reanudables y los artefactos derivados
se regeneran desde ellos. No se descartan censuras, fallos, fallbacks ni
mundos inviables. Las figuras y tablas se producen desde datos procesados.

## Riesgos

- La fase estricta puede terminar en un óptimo unilateral pobre: se mide, no
  se presenta como óptimo social.
- La recuperación local es incompleta: se registra su universo y el motivo de
  fallo; no se oculta mediante fallback en el método primario.
- El preview puede bloquear full: en ese caso el entregable termina con la
  falsación y los artefactos de preview, sin reducir gates retrospectivamente.
- A3 puede censurarse incluso con el presupuesto ampliado: esto es un
  resultado válido y no se transforma en convergencia.
- La cuenta de bytes es payload lógico sobre aristas, no tráfico real de
  middleware.
- N=500 es evidencia finita, no una prueba asintótica.

## Hitos

- [x] Rama/worktree aislados y fuentes canónicas leídas.
- [ ] Protocolo y configuraciones congelados.
- [ ] Cierre post-commit V1 y A2--A7 implementados y ejecutados.
- [ ] Núcleo SCALE-QPG y pruebas aprobados.
- [ ] Calibración, parámetros congelados y preview auditado.
- [ ] Full C1--C9 ejecutado solo si el preview aprueba.
- [ ] Estadística, 12 figuras, reportes y claims actualizados.
- [ ] Commit final, hashes verificados y árbol limpio.

## Registro de decisiones

- 2026-07-24 — Se creó la rama desde el commit final limpio de V1, no desde el
  worktree original.
- 2026-07-24 — La premisa “V1 solo precommit” se trata como hallazgo histórico:
  V1 ya tiene commit final; V1.1 realiza una auditoría independiente de ese
  commit y conserva el manifiesto precommit original como evidencia.
- 2026-07-24 — Se fijaron los conteos no especificados de C4, C5, C7 y C8 antes
  de ejecutar datos.
