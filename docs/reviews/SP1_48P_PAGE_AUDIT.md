# Auditoría editorial página por página de SP1

Fecha: 2026-08-16  
Artefacto revisado: `output/pdf/sp1_levels/SP1_levels_N1_N2_N3_N4.pdf`  
Extensión: 48 páginas

## Dictamen

La vista de 48 páginas funciona como informe técnico reproducible. No conviene
integrarla completa en la memoria VIU. El problema no es la calidad de los
experimentos, sino la cantidad de método, nomenclatura y resultados secundarios
que el lector debe retener antes de llegar al hallazgo principal de N4.

La integración final necesita una revisión mayor, no una poda de sinónimos. La
tesis que debe quedar visible es esta: al retirar el coordinador, N3 mide el coste
de reconstruir información; N4 muestra que Geo-QPG usa solo los agregados de las
cargas afectadas y que, aun con esa reducción, algunas mejoras requieren que dos
o tres robots cambien conjuntamente.

El informe independiente se conserva. La versión compacta debe escribirse como
una segunda vista, con unas 26 páginas, y no reemplazar el artefacto congelado ni
sus datos.

## Qué acepta y qué corrige este dictamen

El diagnóstico externo acierta en cinco puntos: N4 tarda demasiado en llegar a
E4; Q1--Q9 y R1--R6 compiten con la historia; las cautelas se repiten; F-II,
F-III y F-IV ocupan un espacio parecido al de la propuesta principal; y la
síntesis final reduce N4 al dato bilateral sin reunir resultado formal,
mecanismo y evidencia.

Hay dos precisiones. Primero, este PDF no es el archivo de depósito:
`thesis/main.tex` no lo importa directamente. La vista sí usa Arial 12,
interlineado 1,5 y los márgenes registrados en su manifiesto; lo pendiente es su
integración en la jerarquía y el presupuesto de la memoria completa. Segundo,
la matriz canónica define N2 mediante atomicidad. Puede mostrarse al lector como
"capacidad heterogénea" y reservar "atomicidad" para la propiedad matemática,
pero un cambio del nombre formal exige modificar `docs/02_RESEARCH_MATRIX.md`,
`docs/04_CLAIMS_EVIDENCE.md`, `docs/05_NOTATION.md` y sus pruebas.

La notación `D_4,J_4,\Psi_4` también está registrada en
`docs/05_NOTATION.md`. Quitar el subíndice es posible, pero no es una corrección
local y no debe mezclarse con la compactación editorial.

## Decisión por página

`KEEP` conserva la página como unidad argumental. `REWRITE` conserva la evidencia
pero cambia jerarquía o la combina con otra página. `MOVE-M` lleva la explicación
al capítulo de Metodología o la sustituye por una referencia. `MOVE-S` mantiene
el detalle en el informe técnico reproducible; solo una síntesis entra en la
memoria. `REMOVE` retira del relato principal material de planificación, no
resultados ejecutados.

| Pág. | Decisión | Contenido | Tratamiento para la memoria VIU |
|---:|---|---|---|
| 1 | REWRITE | Frontera homogénea/heterogénea | Abrir con la tesis información--orden; conservar una formulación compacta y la figura física. |
| 2 | REWRITE | Mapa N1--N4 | Mantener la figura; mostrar N2 como capacidad heterogénea y formular N4 como "cuántos robots deben cambiar conjuntamente". |
| 3 | MOVE-M | Seis escenarios | Trasladar la definición completa a Metodología; conservar aquí una referencia y una miniatura si hace falta. |
| 4 | MOVE-M | Generadores espaciales | La tabla pertenece a diseño experimental; no repetirla en Resultados. |
| 5 | MOVE-M | Reglas estadísticas | Unificar allí el contraste principal y los análisis de sensibilidad. |
| 6 | MOVE-M | Pipeline Monte Carlo | Conservar la figura en Metodología; Resultados necesita solo un recordatorio breve del pareamiento. |
| 7 | REWRITE | Modelo N1 y equivalencia LSAP | Reducir la derivación; conservar problema, supuesto y resultado de equivalencia. |
| 8 | KEEP | Ventana de validez | Es el límite formal que justifica N2. Acortar la prueba y remitir el desarrollo al informe técnico. |
| 9 | KEEP | E1, Húngaro frente a greedy | Mantener pregunta, estimando, IC y lectura por geometría. |
| 10 | REWRITE | E2, coste temporal | Combinar con E3 en una página de coste central y recálculo; evitar que el título sugiera ausencia universal de cuello de botella. |
| 11 | REWRITE | E3, retirada | Compartir página con E2; distinguir recálculo central de resiliencia distribuida. |
| 12 | KEEP | E4, ruptura por heterogeneidad | Mantener como transición empírica directa a N2. |
| 13 | REWRITE | Formulación N2 | Integrar con la parte esencial de la página 14 y usar "capacidad heterogénea" como rótulo lector. |
| 14 | REWRITE | Relación N1--N2 | Conservar la proposición; llevar detalles de prueba al informe técnico o al anexo formal ya existente. |
| 15 | MOVE-S | Validación del oráculo | Resumir en un párrafo de control interno; conservar figura y enumeración en el informe reproducible. |
| 16 | KEEP | E2, brecha LP--MILP | Resultado central sobre indivisibilidad; mantener figura y lectura causal limitada a la formulación. |
| 17 | KEEP | E3, presión y dispersión | Mantener porque explica cuándo la heterogeneidad afecta factibilidad. |
| 18 | KEEP | E4, certificación | Mantener la frontera temporal del oráculo y cerrar N2 en la misma página. |
| 19 | REWRITE | Contrato informativo N3 | Abrir con el coste de información y eliminar la pregunta retórica del primer renglón. |
| 20 | REWRITE | Dos métodos distribuidos | Dejar una comparación corta de información y garantías; el mecanismo detallado pasa a Metodología. |
| 21 | MOVE-M | Capacity-CBBA-RB | Trasladar pseudocódigo y diagrama operativo; en Resultados basta definir el baseline. |
| 22 | MOVE-M | Weighted-GRAPE | Igual que la página 21; conservar en el cuerpo solo la diferencia informativa con CBBA-RB. |
| 23 | REWRITE | Invariantes y diseño | Mantener invariantes verificadas; retirar pasos de depuración y detalles de campaña ya explicados en Metodología. |
| 24 | KEEP | E2, coste de descentralizar | Resultado principal de N3. Mantener factibilidad, brecha y comunicación en la misma lectura. |
| 25 | KEEP | E3, topología | Mantener el control negativo y el compromiso mensajes--calidad. |
| 26 | REWRITE | Síntesis N3 | Convertirla en el puente explícito: reconstruir más información mejora la decisión, pero cuesta comunicación. |
| 27 | REWRITE | Apertura y taxonomía N4 | Declarar F-I como método propuesto; F-II/F-III como comparadores y F-IV como piloto, en un párrafo corto. |
| 28 | MOVE-M | Atlas F-I | Conservar en el informe técnico; la memoria necesita una figura simplificada de Geo-QPG, no tres variantes equivalentes en tamaño. |
| 29 | MOVE-M | Orden y concurrencia | Mantener en el cuerpo solo la distinción entre número de robots que cambian y mecanismo de confirmación. |
| 30 | MOVE-M | Atlas F-II--F-IV | Trasladar el atlas; resumir la salida entera común en la tabla de comparadores. |
| 31 | KEEP | Suficiencia de agregados | Primer resultado central de N4. Conservar identidad, propiedad local y figura. |
| 32 | REWRITE | Vecindad de orden h | Mantener la jerarquía BR--2BR--C3; reducir reglas de revisión que no intervienen en el resultado. |
| 33 | KEEP | Barrera y orden de escape | Segundo resultado central. Mantener lema, ejemplo y vínculo con el refinamiento. |
| 34 | REWRITE | DMIS+TX | Conservar composición y atomicidad condicionada; trasladar el protocolo de cinco operaciones al informe técnico. |
| 35 | MOVE-M | F-II | Presentarlo como comparador continuo y remitir ecuaciones/dinámicas completas al informe técnico. |
| 36 | MOVE-M | F-III | Igual que F-II; evitar que parezca otra contribución principal. |
| 37 | MOVE-S | Pseudocódigos F-II/F-III y cierre | No cabe en el cuerpo final ni debe aumentar el anexo VIU; queda en el artefacto reproducible. |
| 38 | MOVE-S | F-IV temporal | Conservar como extensión exploratoria fuera del hilo principal. |
| 39 | REMOVE | Programa Q1--Q9 | Eliminar la tabla del relato. Lo ejecutado se integra por hallazgo; lo pendiente pasa a limitaciones y trabajo futuro. |
| 40 | KEEP | E4, efecto de h | Tercer resultado central. Mantener la separación entre orden, revisión y arquitectura. |
| 41 | REWRITE | Distribución de h estrella | Titular "En los mundos evaluados, el primer escape fue predominantemente bilateral" e incluir `1.156/1.200`. |
| 42 | KEEP | Vínculo h estrella--brecha y traza | Mantener: conecta resultado formal, mecanismo y mejora observada. |
| 43 | MOVE-S | Q4--Q5, arquitectura y DPOP | Reducir a un párrafo de validación y conservar las figuras completas en el informe técnico. |
| 44 | KEEP | E6, escalado | Mantener como frontera de coste; describir exponentes observados sin inferencia asintótica. |
| 45 | MOVE-S | F-II experimental | Integrar solo su resultado en una tabla comparativa de comparadores. |
| 46 | MOVE-S | F-III experimental | Integrar una fila de resultado; sustituir "los precios ayudaron" por una atribución al mecanismo primal--dual seguido del mismo cierre. |
| 47 | MOVE-S | F-IV experimental | Mantener fuera del ranking estático y resumir como piloto en limitaciones. |
| 48 | REWRITE | Síntesis final | Rehacer N4 en tres capas: suficiencia local, barrera h-local y reducción 55,7--14,8--3,2 %, con el 96,3 % bilateral y su corte h menor o igual que 3. |

El balance es 13 páginas `KEEP`, 16 `REWRITE`, 11 `MOVE-M`, siete `MOVE-S`
y una `REMOVE`. `REMOVE` afecta solo a la tabla de planificación; ninguna campaña
ni resultado desaparece del repositorio.

## Esquema objetivo de 26 páginas

| Págs. | Bloque | Contenido imprescindible |
|---:|---|---|
| 1--2 | Apertura | Problema, frontera de modelado y mapa N1--N4 con la tesis información--orden. |
| 3 | Protocolo recordatorio | Mundo--semilla, pareamiento, endpoints e IC; referencia a Metodología para generadores y contrastes. |
| 4--7 | N1 | Equivalencia y ventana; E1; E2+E3; E4 y transición. |
| 8--11 | N2 | Cobertura ponderada; control del oráculo; brecha de indivisibilidad; presión, certificación y cierre. |
| 12--16 | N3 | Contrato y baselines; invariantes; E2; E3; síntesis del coste informativo. |
| 17 | N4, posición | Geo-QPG como propuesta; comparadores y piloto en segundo plano. |
| 18 | Suficiencia local | Agregados de cargas afectadas y potencial unilateral. |
| 19--20 | Localidad estratégica | Jerarquía h, barrera bilateral y definición de h estrella. |
| 21 | Ejecución vecinal | Composición no conflictiva y alcance condicionado de DMIS+TX. |
| 22 | E4 | Efecto de ampliar h y separación frente a regla/arquitectura. |
| 23--24 | E9 | Distribución de h estrella, sensibilidad, vínculo con la brecha y traza. |
| 25 | Coste y comparadores | Escalado; tabla breve F-II/F-III; F-IV identificado como piloto. |
| 26 | Síntesis | Resultado formal, resultado mecanístico, evidencia y límites de transferencia a SP2. |

Este reparto deja 18 de 26 páginas centradas en resultados, interpretación y
límites. Cumple la prioridad VIU sin obligar a repetir el protocolo completo.

## Correcciones que no deben esperar a la compactación

1. Unificar la regla estadística. La tabla general puede declarar Wilcoxon para
   métricas continuas, pero E1 debe explicar por qué usa signo exacto como
   contraste principal y Wilcoxon como sensibilidad. La figura de protocolo debe
   mostrar esa bifurcación, no dos reglas aparentes para el mismo endpoint.
2. Sustituir la atribución causal "los precios ayudaron a producir un entero".
   El contraste cambia el mecanismo completo; la redacción válida es que el
   primal--dual seguido del mismo cierre produjo el resultado observado.
3. Retirar Q1--Q9 y R1--R6 de la prosa. Los resultados formales conservan sus
   nombres matemáticos; la tabla de trazabilidad puede quedar en el informe.
4. Cambiar anglicismos cuando no nombran un objeto técnico: `RAW` por registro
   inicial, `timeout` por límite temporal, `warm start` por inicialización desde
   la solución anterior y `endpoint` por variable de respuesta. `Commit` se
   conserva solo al definir la operación transaccional.
5. Compactar las cautelas. El PDF contiene 15 apariciones de "no se", además de
   negaciones equivalentes. Cada experimento debe cerrar con un límite concreto,
   no con varias defensas alrededor del mismo dato.
6. Cambiar el pie de la síntesis transversal. La Figura 42 debe indicar qué
   campaña aporta cada familia y que la comparación usa mundos compartidos de
   N3--N4, no una única ejecución E7 homogénea.

## Criterios de aceptación de la futura integración

- Entre 25 y 30 páginas para SP1 dentro de la memoria; la vista técnica de 48
  páginas permanece reproducible y no se modifica.
- F-I ocupa la mayor parte de N4; F-II y F-III caben en una comparación compacta
  y F-IV aparece como piloto.
- Ningún resultado pendiente figura en una tabla de resultados.
- La conclusión N4 incluye suficiencia de información, barrera h-local, la
  secuencia de brechas y el 96,3 % bilateral con corte de búsqueda explícito.
- Cada cifra conserva su fuente RAW y su claim; no se reinterpreta una asociación
  como causalidad.
- La memoria completa respeta el presupuesto VIU de cuerpo y anexos. El material
  suplementario extenso queda en el repositorio, no se vuelca al anexo de veinte
  páginas.
