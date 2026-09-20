# Auditoría de cierre de SP2

Fecha: 2026-08-16  
Alcance: código, configuraciones, resultados y subcapítulo autónomo de SP2.

## Dictamen

El material disponible sustenta la equivalencia cinemática de N1, el
contraejemplo de capacidad agregada de N2, la comprobación discreta de caging y
varios resultados planares reutilizados de SP4--SP6. Antes de esta revisión no
sustentaba una envolvente operacional completa: el oráculo mecánico ignoraba el
equilibrio vertical y los conos de fricción, N3 medía principalmente bytes y el
bloque N4 combinaba resultados ejecutados con protocolos aún no realizados.

La versión de cierre debe mantener esas fronteras de evidencia. En particular,
la planta reducida en Python no constituye validación física y CoppeliaSim es
una simulación de mayor fidelidad, no un experimento con robots reales.

## Inventario reutilizable

| Bloque | Artefacto | Uso admisible |
|---|---|---|
| N1 | `sp2_canonical/kinematics.py` | Cinemática exacta del pivote, alineación y límites de rueda. |
| N1--N3 | `SP2_CANONICAL_SMOKE_v1` | Barrido determinista reducido y prueba de la tubería. |
| N2 | `sp2_canonical/mechanics.py` | Baseline bilateral planar; no representa por sí solo contacto físico completo. |
| Caging | `sp2_canonical/caging.py` | Comprobación de no escape a una resolución declarada. |
| N4 | campañas SP4--SP6 | Control planar, filtro de seguridad y recuperación lógica dentro de sus modelos originales. |
| Documento | `thesis/sp2_report/main.tex` | Formato autónomo alineado con los niveles N1--N4 de SP1. |

## Defectos encontrados y corrección exigida

1. **Puente incompleto entre mando y wrench.** Faltaban la dinámica nominal de
   la carga, la transformación mundo--cuerpo y una convención única de signos.
   Se añade una función explícita para calcular ambos wrenches.
2. **Soporte 2.5D ausente.** El LP planar permitía fuerzas laterales sin
   comprobar normales, centro de masas ni momentos de vuelco. Se añade el
   equilibrio vertical y sus cotas antes del reparto tangencial.
3. **Relajación mecánica demasiado permisiva.** Los límites por componente no
   representan fricción de Coulomb. Se conserva ese modelo como baseline y se
   añade un oráculo poliédrico con límites de tracción y residual de wrench.
4. **Margen cinemático incompleto.** El certificado identificaba el robot
   limitante, pero no la rueda ni un margen normalizado. Se incorporan ambos.
5. **N3 confundía volumen con calidad.** Los mensajes carecían de emisor,
   instante y canal; la estructura virtual incluía una covarianza no estimada.
   Se sustituye por mensajes trazables y un canal local reproducible con
   pérdida, retardo, alcance y presupuesto de ancho de banda.
6. **Controladores sin interfaz común.** Los resultados históricos no
   permitían comparar todos los métodos solicitados bajo la misma planta. Se
   añade una interfaz en aceleración para PD, PID, LQR, LQI,
   port-Hamiltonian y MPC central, junto con un gobernador común.
7. **Protocolos presentados junto a resultados.** El texto debe distinguir
   campaña ejecutada, evidencia histórica y extensión pendiente en el mismo
   párrafo donde aparece cada límite.
8. **Prosa metadiscursiva y rítmica.** Se detectaron repeticiones de «debe»,
   «no demuestra», «queda pendiente» y transiciones que hablaban del proceso de
   redacción. La revisión final las sustituye por descripción directa del
   modelo, el resultado y su dominio de validez.

## Fronteras de ejecución

- En el entorno de cierre no se encontró un ejecutable de CoppeliaSim en
  `PATH`. Existen escenas y resultados históricos, pero no se atribuirá a esta
  revisión una campaña nueva que no pudo ejecutarse.
- El modo primario es carga soportada con contactos fijos. Caging permanece
  como extensión no prehensil y no comparte la prueba mecánica del modo
  primario.
- Los optimizadores con información global son oráculos o baselines centrales.
  No se describen como arquitectura distribuida.
- Una simulación satisfactoria no prueba estabilidad global ni seguridad fuera
  del dominio muestreado.

## Condición de aceptación

SP2 solo se considera cerrado cuando las pruebas unitarias, la campaña
versionada, los resúmenes generados, la matriz de evidencia y el PDF proceden de
la misma revisión del código. Los fallos y tiempos agotados permanecen en los
denominadores y ningún valor experimental se introduce manualmente en LaTeX.

## Verificación posterior a la corrección

La campaña completa produjo 36 600 evaluaciones cinemáticas en N1, 720 casos
mecánicos en N2, 240 ejecuciones de red en N3 y 2 100 ejecuciones dinámicas en
N4. Los análisis pareados conservan la identidad de método, escenario y semilla;
los fallos de S6 permanecen en los denominadores. La matriz de afirmaciones y la
notación se sincronizaron con esos artefactos.

La batería seleccionada terminó con 23 pruebas superadas. La compilación del
subcapítulo no contiene referencias ni citas indefinidas, errores de LaTeX o
cajas desbordadas. El PDF final tiene 20 páginas A4 y fue inspeccionado página a
página. La compilación integral de la memoria alcanzó 120 páginas y confirmó la
presencia de las cinco figuras TikZ protegidas.

Se aplicó una segunda lectura editorial al texto extraído del PDF. No se
encontraron nombres de asistentes, instrucciones de generación, lenguaje sobre
detectores, promesas de perfección, referencias a código o cuadernos, ni
metadiscurso sobre la fabricación del documento. Esta comprobación reduce
indicios estilísticos evitables; no equivale a garantizar el resultado de un
detector propietario, cuya salida no es verificable ni estable.
