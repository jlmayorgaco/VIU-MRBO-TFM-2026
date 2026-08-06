# Auditoría adversarial de SP1.N1

**Fecha:** 2026-08-06

**Objeto:** páginas experimentales E1--E4 y sus cuatro figuras cuantitativas
**Dictamen previo a correcciones:** revisión mayor de presentación y
transparencia; no se detectó una contradicción que invalide los resultados
registrados.

## Resumen ejecutivo

La campaña tiene una base defendible: protocolo congelado, mundos pareados,
semillas explícitas, RAW conservado, corrección de Holm, IC, fallos visibles y
una frontera de validez que no intenta convertir el Húngaro en un método para
capacidades heterogéneas. El principal riesgo no es la ausencia de datos, sino
que las figuras actuales esconden parte de esa solidez. Parecen resúmenes de
dashboard: títulos internos grandes, exceso de espacio en blanco, paneles
codificados sobre todo por color, boxplots que omiten outliers y barras cercanas
al 100 % sin intervalos ni denominadores visibles.

No existe una versión literalmente inmune a toda objeción. La meta razonable es
que cualquier lector pueda reconstruir qué se comparó, cuál fue la unidad
independiente, qué incertidumbre acompaña al efecto y hasta dónde llega la
conclusión.

## Hallazgos que requieren corrección

### R1 -- El contraste de E1 no debe describirse como prueba exacta de la mediana

La hipótesis congelada usa Wilcoxon unilateral sobre
`relative_saving - 0.05`. Este contraste evalúa un desplazamiento pareado
(pseudomediana bajo los supuestos habituales), no la mediana poblacional sin
condiciones adicionales. La mediana sí dispone de un IC bootstrap y el gate
confirmatorio combina ese IC con Wilcoxon. La redacción debe separar ambas
piezas. Como diagnóstico posterior, un test exacto de signo puede comprobar que
la clasificación de escenarios no depende de interpretar Wilcoxon como test de
mediana; debe rotularse como sensibilidad, no como un nuevo confirmatorio.

**Riesgo si no se corrige:** objeción metodológica directa sobre el estimando.

### R2 -- E1 omite el tamaño de efecto del contraste preespecificado

El CSV actual informa valores `p` e IC de la mediana, pero no la correlación
biserial por rangos requerida por el protocolo canónico. Debe calcularse desde
las diferencias desplazadas y conservarse junto al contraste. El cuerpo no
necesita enumerar cinco valores si la figura o el artefacto procesado los hace
auditables.

**Riesgo si no se corrige:** resultado presentado como significación sin
magnitud del efecto.

### R3 -- E3 muestra medianas de coste sin incertidumbre

La factibilidad es determinista para el modelo cardinal y coincide con la
frontera en todas las ejecuciones. El coste espacial posterior, en cambio, es
estocástico y solo aparece como una línea de medianas. Debe incluir IC bootstrap
por celda y aclarar que las cinco retiradas son tratamientos anidados dentro del
mismo mundo, no cinco réplicas independientes.

**Riesgo si no se corrige:** pseudorreplicación aparente e imposibilidad de
juzgar la precisión del aumento de coste.

### R4 -- E4 mezcla dos denominadores y las barras ocultan los pocos fallos

La certificación MILP usa todas las auditorías de cada nivel; el rescate usa
solo los falsos factibles. Las barras actuales comparten eje, pero no muestran
`n/N` ni IC, de modo que 98,2 % de rescate y 98,7 % de certificación parecen la
misma respuesta. Deben convertirse en estimados con IC de Wilson, denominador
explícito y marca `n/a` en el caso homogéneo.

**Riesgo si no se corrige:** ambigüedad del endpoint y lectura inflada de la
certificación.

### R5 -- La regresión temporal de E2 necesita un contexto más visible

El exponente 2,27 procede de siete medianas de la serie `N=M`, con 30 réplicas
por tamaño. Es un ajuste descriptivo del intervalo, no una demostración de
complejidad asintótica. La figura ya lo afirma, pero debe mostrar el ajuste
balanceado, `n=7` tamaños, las réplicas por celda y conservar P05--P95. El
manifiesto debe registrar procesador, número de CPU lógicas y versión de SciPy;
los tiempos siguen siendo específicos del equipo y de la carga del sistema.

**Riesgo si no se corrige:** confundir una curva empírica con Big-O.

## Hallazgos editoriales

### E1 -- Tamaño nominal y jerarquía

Las figuras se generan a 10,8 pulgadas y luego se reducen al ancho de texto.
Esto reduce también las fuentes y desaprovecha espacio con un segundo título
general dentro de la figura. Deben generarse cerca del ancho final de doble
columna (aprox. 183 mm), eliminar el `suptitle` y dejar que el título de la
sección y el pie expliquen el mensaje general.

### E2 -- Paneles y leyendas

Los paneles deben usar letras minúsculas consistentes, títulos breves y una
leyenda que defina estimado, intervalo y unidad. Las notas grises bajo cada eje
deben pasar al pie cuando no codifiquen datos.

### E3 -- Accesibilidad

La clasificación no puede depender solo de naranja/azul o verde/rojo. Se
requieren marcadores, trazos o rellenos redundantes, y las curvas deben seguir
siendo distinguibles en escala de grises. La paleta debe evitar arcoíris y
contrastes rojo--verde como único canal.

### E4 -- Representación de distribuciones

El boxplot de E1 declara que no dibuja outliers. Para una figura de evidencia,
es preferible P05--P95 + IQR + mediana o una distribución visible; no debe
desaparecer la cola que precisamente se pretende caracterizar.

## Elementos que ya superan la auditoría

- Los cuatro gráficos disponen de PDF vectorial y PNG.
- `pdffonts` confirma fuentes TrueType embebidas y subconjuntadas.
- Los métodos comparten mundo y semilla dentro de cada comparación.
- Los 12.630 registros RAW y 6.630 mundos independientes están inventariados.
- E4 mantiene MILP como auditor externo y no como comparador arquitectónico
  justo.
- Los límites de transporte físico, recuperación distribuida y extrapolación
  asintótica ya aparecen en la narrativa.

## Referencias editoriales empleadas

- IEEE Author Center, *Create Graphics for Your Article*:
  https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/create-graphics-for-your-article/
- IEEE Author Center, *Resolution and Size*:
  https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/create-graphics-for-your-article/resolution-and-size/
- IEEE Author Center, *File Formatting*:
  https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/create-graphics-for-your-article/file-formatting/
- Nature Research Figure Guide, *Building and exporting figure panels*:
  https://research-figure-guide.nature.com/figures/building-and-exporting-figure-panels/
- Nature Portfolio, *Reporting standards and availability of data, materials,
  code and protocols*:
  https://www.nature.com/nature-portfolio/editorial-policies/reporting-standards

## Decisión de revisión

Aplicar R1--R5 y E1--E4 sin reabrir el diseño confirmatorio. Tras regenerar, la
aceptación interna exige: PDF de diez páginas, fuentes embebidas, texto legible
al ancho final, cero solapes, conteos/IC verificables desde RAW, tests completos
y una nueva lectura adversarial que no encuentre una afirmación más fuerte que
su evidencia.

## Verificación posterior a las correcciones

**Dictamen:** apto para integrar como bloque experimental de N1, con las
limitaciones declaradas a continuación. Los hallazgos R1--R5 y E1--E4 quedaron
resueltos sin alterar la configuración congelada ni los datos RAW.

- E1 separa el IC bootstrap de la mediana y el contraste de desplazamiento de
  Wilcoxon; añade correlación biserial por rangos y un test exacto de signo
  identificado expresamente como sensibilidad.
- E2 conserva las 30 réplicas por celda, hace visibles los siete tamaños del
  ajuste y lo rotula como descriptivo del intervalo observado.
- E3 informa recuentos por celda y un IC bootstrap del aumento mediano de coste;
  las retiradas se describen como tratamientos anidados, no como réplicas.
- E4 separa certificación y rescate, muestra sus distintos denominadores y añade
  IC de Wilson; el caso sin falsos factibles aparece como no aplicable.
- Las seis figuras comparten 183 mm de ancho nominal, PDF vectorial, PNG de
  600 dpi, fuentes embebidas y codificación redundante por color y forma.
- El PDF recompilado conserva diez páginas. La inspección de las páginas 6--10
  no encontró solapes, recortes, leyendas ambiguas ni elementos fuera de caja.
- La batería cruzada terminó con 21 pruebas aprobadas, incluidas las
  protecciones TikZ y las invariantes del Húngaro.

### Límites que deben permanecer visibles

La campaña usa mundos sintéticos y estáticos. El tiempo de E2 depende del
equipo y no establece complejidad asintótica; E3 es un recálculo central con el
fallo ya conocido; E4 emplea el MILP únicamente como auditor; y ningún
experimento de N1 demuestra transporte físico, detección de fallos,
comunicación distribuida o resiliencia operacional. Estas restricciones no son
defectos de maquetación: delimitan la evidencia que corresponde a N1 y motivan
los niveles posteriores.
