# Decisión editorial consolidada — auditoría bulletproof 2026-07-14

## Cobertura del panel

Los cinco informes Phase 2 son utilizables. Cada revisor declaró lectura de las
2.965 líneas extraídas del PDF oficial de 78 páginas. No se incorporaron los
intentos preliminares que no superaron el gate de cobertura.

| Revisor | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | Decisión |
|---|---|---|---|---|---|---|---|---|---|
| EIC | pass | pass | pass | warn | pass | pass | pass | warn | minor_revision |
| R1 metodología | pass | pass | pass | warn | warn | warn | pass | warn | minor_revision |
| R2 dominio | warn | pass | pass | warn | pass | pass | pass | pass | minor_revision |
| R3 sistemas | pass | pass | pass | warn | warn | warn | pass | warn | minor_revision |
| Devil's Advocate | pass | warn | pass | warn | pass | pass | pass | warn | minor_revision |

## Aplicación mecánica del contrato

- **F1 — reject:** no activada; no existe `block` en D1--D3.
- **F2 — major_revision:** no activada; ningún informe asigna `warn` o peor a
  dos dimensiones obligatorias.
- **F3 — major_revision:** no activada; no existe `block` en D4--D8.
- **F4 — minor_revision:** activada. R2 asigna `warn` a D1 por la contradicción
  documental de SP8 y el Devil's Advocate asigna `warn` a D2 por el alcance de
  la palabra «distribuida» frente a cierres globales.
- **F5 — minor_revision:** activada. Los cinco revisores asignan `warn` a D4;
  también hay advertencias en D5, D6 y D8.
- **F0 — accept:** no activada antes de revisión porque D1 y D2 no reciben
  `pass` unánime.

La condición activa de mayor severidad es F4/F5. La decisión contractual es:

> **minor_revision**

No se encontró un P0 contractual, una tesis central falsa ni un teorema central
inválido. La memoria no está todavía lista para depósito porque quedan defectos
de alcance, trazabilidad y presentación que afectan una defensa exigente.

## Hallazgos consolidados y criterios de aceptación

### P1.1 — Alcance distribuido y presupuesto de centralización

**Problema.** La arquitectura contiene actualizaciones y señales locales, pero
la implementación integrada usa umbral global en A0, ranking/cierre global en
A1--A2, búsqueda global acotada en A3, unión global en A4 y candidatos globales
en FULL. «Distribuida» no puede interpretarse como extremo a extremo.

**Aceptación.** Resumen, Abstract, metodología, posicionamiento, resultados y
conclusiones declaran la misma frontera. Una tabla identifica por etapa la
información local, la operación global, el coste/mensajería y la consecuencia
para el claim. O3 permanece explícitamente parcial.

### P1.2 — Matriz de originalidad

**Problema.** La novedad está dispersa y no separa de forma auditable lo
heredado de Quijano, Barreiro-Gómez y Martínez-Piazuelo de la integración propia.

**Aceptación.** A1--A4 se vinculan con antecedentes directos, mecanismo
heredado, delta técnico, evidencia propia y límite. Smith, las dinámicas
poblacionales distribuidas, la invariancia/capacidad y el análisis discreto no
se presentan como novedades del TFM. La novedad defendida es la integración y
auditoría de cierre entero, factibilidad wrench, ejecución y recuperación.

### P1.3 — Coherencia canónica de SP8 y SP4

**Problema.** Los registros antiguos presentan SP8 como evidencia
confirmatoria, mientras el manuscrito suspende H8.1--H8.2 y deja H8.3
exploratoria. SP4 v4 y el replay Coppelia existen, pero la evidencia oficial es
SP4 v3.

**Aceptación.** `CANONICAL_RESULTS.md`, `CLAIM_LEDGER.md`, anexos y tesis usan
la misma clasificación. SP8 no sustenta intractabilidad observada ni RSS
medido. SP4 v4/Coppelia se etiqueta como complementario no canónico y como
replay cinemático, no validación dinámica independiente ni hardware.

### P1.4 — Registro completo de precisión A0--FULL

**Problema.** El cuerpo describe la regla 40--60--100, pero no expone los veinte
contrastes finales ni permite comprobar de inmediato la anchura lograda.

**Aceptación.** Una tabla trazada a `paired_contrasts_holm.csv` informa familia,
transición, n, efecto, IC95 %, anchura, pares discordantes, p de Holm y decisión.
Se declara que el tope era duro y, como resultado observado, que las veinte
anchuras finales fueron <= 0,20.

### P1.5 — Condiciones paramétricas y validez física

**Problema.** El umbral wrench, `dt`, horizonte, ganancias HOCBF y demás
parámetros físicos están congelados, pero no existe sensibilidad confirmatoria;
FULL conserva 14 % de colisiones adversas y SP4 no excita saturación de par.

**Aceptación.** Los valores y condiciones se exponen como dominio de validez,
no como robustez paramétrica. Se repiten autoridad realizable, estado inicial
seguro, modelo planar, agarre rígido y ausencia de garantía funcional. El efecto
FULL sigue atribuido al paquete, no a componentes individuales.

### P1.6 — Integridad bibliográfica y frescura

**Problema.** La auditoría local queda en `WARN`; su ruta de trazas no existe en
el snapshot y los hashes deberán cambiar después de la revisión. Algunas
referencias recientes renderizan metadatos abreviados.

**Aceptación.** Todas las claves citadas resuelven; la traza de contextos existe;
los hashes corresponden a las fuentes y al PDF finales; las entradas recientes
tienen DOI, venue, arXiv o URL estable cuando está disponible. La ausencia del
servicio institucional de similitud y de un revisor externo de otra familia se
mantiene como excepción externa explícita, nunca como `PASS` inventado.

### P1.7 — Presentación de depósito

**Problema.** Hay páginas preliminares casi vacías, una figura con fuente Type-3
y cuatro acentos graves espurios.

**Aceptación.** Índice y listas no generan páginas residuales evitables; todas
las fuentes PDF están embebidas sin Type-3; no existen referencias indefinidas
ni cajas overfull; se corrigen `éxitos`, `únicamente`, `álgebra` y `último`.

## Cierre editorial previsto

La revisión puede cerrarse sin una nueva campaña confirmatoria si se conserva
el alcance honesto. No se promoverán SP4 v4, Coppelia o SP8 para aumentar
artificialmente la fuerza del claim. Tras aplicar los criterios anteriores se
recompilará el PDF, se ejecutarán gates/tests y se repetirá la revisión de
cierre contra cada P1.
