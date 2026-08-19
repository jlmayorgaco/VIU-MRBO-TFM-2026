# SP1 visual — informe de entrega (25 páginas)

> El nombre de este fichero se conserva por trazabilidad con la edición compacta
> anterior; su contenido describe la entrega visual definitiva de 25 páginas.

## Resultado

- Edición compacta anterior: 20 páginas.
- Entrega visual final: 25 páginas A4.
- PDF: `Subdocuments/SP1/sp1.pdf`.
- Compilación reproducible: `cd Subdocuments/SP1; .\build.ps1`.
- Flujo ejecutado: LuaLaTeX, Biber y dos pasadas adicionales de LuaLaTeX.

## Integridad científica

- Resultados, campañas, datos, configuraciones, macros y cifras: sin cambios.
- Ecuaciones conservadas en esta edición: (1)--(22).
- Algoritmos conservados en el cuerpo: 1--3; los algoritmos 1 y 2 se ampliaron
  con entradas, salidas, versiones, reintentos y criterios de cierre.
- Ningún archivo de evidencia ni figura generada se eliminó del repositorio.
- La selección de figuras del cuerpo se hizo con la matriz de evidencia:
  se mantuvieron los contrastes que sostienen la transición N1--N4 y se
  resumieron los diagnósticos secundarios.

## Selección editorial

- N1 conserva E1 (calidad) y E4 (frontera de heterogeneidad). Las figuras de
  escala central y recálculo tras retirada quedan fuera del cuerpo, pero sus
  datos y activos permanecen disponibles.
- N2 conserva E1 (validación por enumeración) y E2 (atomicidad LP--MILP).
  El diagrama de fase y la campaña de certificación se mantienen en los
  artefactos reproducibles.
- N3 conserva el contrato de información, los dos métodos y los resultados de
  calidad, comunicación y conectividad.
- N4 conserva E4, E9, las trazas de mecanismo, la ablación DMIS+TX, F-II/F-III
  y la síntesis transversal. DPOP, la gráfica de escala y el piloto temporal no
  compiten por espacio con la evidencia confirmatoria. F-IV conserva su frontera
  conceptual en el atlas y su lectura limitada en la comparación final; se retiró
  únicamente su página digital secundaria para mantener el límite de 25 páginas.

## Ajustes de maquetación

- La Figura 1(a) y la Figura 1(b) ocupan páginas consecutivas y conservan una
  numeración única mediante `\ContinuedFloat`.
- El atlas coalicional y el atlas continuo/temporal ocupan páginas distintas.
- E4 y E9 también ocupan páginas separadas; las distribuciones y mapas de
  sensibilidad ya no comparten espacio con la comparación de familias.
- Los gráficos N1--N3 y los resultados confirmatorios N4 se ampliaron; las
  subfiguras densas se apilaron cuando la lectura a dos columnas era insuficiente.
- El mecanismo N4 se presenta en tres filas a ancho amplio; F-II y F-III se
  muestran en dos filas completas.
- La síntesis transversal usa un Pareto a casi todo el ancho de la caja de texto.
- La ecuación (21) se partió con corchetes tipográficamente estables, sin alterar
  su formulación.

## Corrección visual de figuras 2, 5, 7 y 8

- La Figura 2 usa ahora todo el ancho disponible; sus seis escenarios se
  organizan en una retícula de tres por dos y las dos tablas aparecen debajo,
  fuera del panel gráfico.
- La Figura 5 presenta CBBA-RB y Weighted-/Pair-GRAPE en paneles más altos. Los
  algoritmos 1 y 2 dejaron de ser resúmenes telegráficos y detallan el estado
  distribuido, la difusión, los desempates y la terminación.
- La Figura 7 se reparte en cuatro páginas continuadas: taxonomía, reglas
  unilaterales, revisiones coalicionales y familias continuas/temporales. Se
  eliminaron microanotaciones redundantes que interferían con los bordes.
- La Figura 8 amplía la lectura de agregados y separa visualmente el orden
  estratégico de la regla de revisión; las flechas ya no atraviesan ecuaciones.

## Revisión de redacción

- Se sustituyeron títulos formulaicos por títulos informativos y directos.
- Los resultados N1, N2, E4, E9 y los comparadores se reescribieron como
  comparación, interpretación y límite, sin listas telegráficas de métricas.
- La conclusión dejó de repetir una secuencia simétrica N1/N2/N3/N4 y ahora
  distingue resultado, aportación principal e interfaz con SP2.
- Segunda auditoría de patrones de escritura artificial: no quedan fórmulas
  vacías de énfasis, conclusiones genéricas ni afirmaciones sin evidencia. Los
  guiones dobles restantes corresponden a rangos, nombres de métodos o sintaxis
  LaTeX.

## QA ejecutado

- `pdfinfo`: 25 páginas A4.
- Render PNG de las 25 páginas y revisión visual integral en cuatro iteraciones.
- Log sin errores, referencias/citas sin resolver ni cajas `Overfull`.
- Sin controles C0 no permitidos en las fuentes TeX inspeccionadas.
- Sin placeholders `Asset pendiente` o `TikZ pendiente` en el PDF final.

## Avisos no bloqueantes

- MiKTeX informa de `biblatex-dm.cfg` opcional no encontrado.
- Algunas figuras TikZ heredadas emiten avisos de glifos internos de Arial; no se
  detectaron caracteres C0 en los ficheros TeX fuente y la inspección visual no
  muestra glifos ausentes.
