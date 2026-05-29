# Tarea 1 - Fundamentación de la investigación según VIU

## Entrega inmediata

Asignatura: 12MROB_10_A_2025-26_Trabajo Final de Máster (MU Robótica)

Actividad: Tarea 1. Fundamentación de la Investigación. 1ra Convocatoria.

Fecha límite: 29/05/2026.

Requisito de entrega:

- PDF original del TFM.
- Documento avanzado hasta el apartado de Metodología, incluido.
- Evaluación binaria: Aceptado / No aceptado.

## Restricciones oficiales detectadas

De las instrucciones y plantilla oficial del Máster Universitario en Robótica y Automatización de Procesos:

- El TFM debe ser individual, original e inédito.
- Debe usar la plantilla oficial de VIU.
- El cuerpo final debe tener entre 50 y 80 páginas, sin contar portada, resúmenes, índices ni anexos.
- Los anexos finales no deben superar 20 páginas.
- La citación debe seguir APA 7.ª edición.
- Debe tener aspecto profesional y maduro de posgrado.
- No deben existir encabezados consecutivos sin texto entre ellos.
- Cada capítulo o apartado debe iniciar con un párrafo introductorio.
- Las figuras, tablas y ecuaciones deben estar numeradas, tituladas y justificadas.
- Al menos el 50 % del cuerpo final del TFM debe destinarse a resultados, análisis y validación.

Para la Tarea 1, todavía no se exige ese 50 % de resultados, pero sí debe quedar claro cómo se obtendrán, medirán y validarán esos resultados.

## Tipo de TFM recomendado

La categoría más adecuada es:

**Memoria Técnica con componente de Estudio Teórico-Técnico.**

Justificación:

- Cumple con "implementación de una instalación de robótica y/o automatización de procesos industriales".
- Encaja con "diseño de sistemas robóticos móviles basados en programación de AGVs".
- Encaja con "técnicas de control avanzado".
- Encaja con "simulación de robótica aplicada".
- Permite mantener una contribución teórica incremental sin abandonar la orientación práctica esperada por VIU.

## Tema reencuadrado

Título recomendado:

**Control distribuido adaptativo basado en consenso para transporte cooperativo multi-AGV bajo incertidumbre inercial de la carga**

Subtítulo interno de trabajo:

**Modelado, simulación reproducible y validación aplicada en CoppeliaSim**

Eje teórico principal:

**Control cooperativo multiagente.**

El TFM debe defenderse desde la teoría de control y la cooperación entre agentes autónomos. La simulación, CoppeliaSim y las métricas son medios de validación, no el centro conceptual del trabajo.

## Alcance ajustado a VIU

El TFM no debe prometer una teoría completamente nueva ni una implementación física real. Debe prometer una solución técnica completa y verificable.

### Incluido

1. Modelado planar de transporte cooperativo con 2 a 4 AGVs.
2. Representación de la carga como cuerpo rígido con incertidumbre inercial.
3. Comunicación local mediante grafos conectados y degradados.
4. Controlador nominal distribuido basado en consenso.
5. Controlador adaptativo o robusto frente a incertidumbre de masa, inercia y centro de masas.
6. Simulación cuantitativa reproducible en Python.
7. Validación visual y operativa en CoppeliaSim.
8. Comparación experimental mediante métricas objetivas.
9. Discusión crítica de estabilidad práctica, robustez, limitaciones y aplicabilidad industrial.

### Excluido

1. Construcción de AGVs físicos.
2. Sensado real, SLAM o visión artificial.
3. Planificación global de rutas.
4. Certificación de seguridad industrial.
5. Identificación experimental completa de parámetros.
6. Pruebas en planta industrial real.

Esta delimitación es importante: el tribunal debe ver profundidad, pero también viabilidad.

## Profundidad teórica esperada

La teoría debe organizarse alrededor de dos conceptos principales: **control** y **cooperación**. El marco industrial y la simulación son necesarios, pero deben ocupar menos espacio que el desarrollo técnico del control cooperativo.

### Nivel 1: contexto obligatorio

Debe explicar de forma breve:

- AGVs y robótica móvil industrial.
- Transporte cooperativo multi-robot.
- Industria 4.0 y automatización flexible.
- Simulación como herramienta de validación en robótica.

Este nivel no debe dominar el TFM. Sirve para ubicar el problema.

### Nivel 2: base técnica central - control

Debe desarrollarse con mayor detalle:

- modelado dinámico y cinemático del sistema robot-carga;
- control distribuido;
- control basado en consenso;
- error de seguimiento;
- error de formación;
- incertidumbre paramétrica;
- robustez;
- control adaptativo o robusto.

Este bloque responde a la pregunta: **cómo se diseña una ley de control capaz de coordinar varios AGVs bajo incertidumbre de la carga**.

### Nivel 3: base técnica central - cooperación

Debe desarrollarse con el mismo peso que el control:

- cooperación multiagente;
- teoría de grafos aplicada a comunicación entre AGVs;
- topologías de comunicación local;
- conectividad y degradación del grafo;
- formación cooperativa;
- reparto distribuido de información;
- coordinación sin controlador central;
- efecto de la cooperación sobre seguimiento, formación y robustez.

Este bloque responde a la pregunta: **cómo emerge el comportamiento cooperativo a partir de decisiones locales y comunicación limitada**.

### Nivel 4: contribución propia

Debe presentarse como contribución incremental:

**Arquitectura de control cooperativo adaptativo para transporte multi-AGV bajo incertidumbre inercial.**

La contribución principal no es CoppeliaSim ni una métrica aislada, sino la integración razonada de:

1. cooperación multiagente;
2. consenso distribuido;
3. compensación adaptativa o robusta;
4. evaluación bajo incertidumbre inercial.

Como herramienta complementaria de evaluación, se propone el:

**Índice de Robustez Cooperativa ante Carga Incierta (IRCCI).**

El índice permite comparar la degradación del controlador adaptativo frente al nominal bajo escenarios de incertidumbre.

Forma conceptual:

```text
IRCCI = 1 - (D_adaptativo / D_nominal)
```

donde `D` agrupa degradaciones relativas en:

- error de seguimiento;
- error de formación;
- tiempo de convergencia;
- esfuerzo de control.

No debe venderse como una teoría universal, sino como una métrica propuesta para cuantificar el comportamiento cooperativo bajo incertidumbre.

## Papel correcto de CoppeliaSim

CoppeliaSim debe aparecer como entorno de validación aplicada, no como el centro científico del TFM.

Uso recomendado:

- representar la escena multi-AGV;
- visualizar transporte cooperativo;
- demostrar operación del controlador en un entorno robótico;
- generar capturas o secuencias de validación;
- confirmar que el modelo no queda como simulación abstracta desconectada de robótica.

La fuente principal de resultados debe ser Python:

- métricas;
- tablas;
- curvas;
- repetibilidad;
- comparación estadística o cuantitativa.

Relación correcta:

```text
Python = motor científico reproducible.
CoppeliaSim = validación visual, robótica y aplicada.
```

## Estructura de la Tarea 1

La entrega del 29/05/2026 debe llegar hasta Metodología. Debe tener forma de TFM real, no de esquema.

### Portada

Debe incluir:

- título;
- autor;
- director;
- máster;
- universidad;
- fecha: mayo 2026.

### Resumen provisional

Extensión: 200-300 palabras.

Debe contener:

- problema;
- objetivo;
- alcance;
- método;
- resultados esperados;
- contribución.

Palabras clave: 3-5.

Propuesta:

- control distribuido;
- AGV;
- transporte cooperativo;
- consenso adaptativo;
- CoppeliaSim.

### Índices

Para Tarea 1:

- índice de contenido;
- índice de figuras, si ya hay figuras;
- índice de tablas, si ya hay tablas;
- listado de acrónimos, si se incluyen.

### 1. Introducción

Contenido mínimo:

1. Contexto de AGVs en automatización industrial.
2. Problema del transporte cooperativo.
3. Dificultad causada por incertidumbre inercial de la carga.
4. Justificación del control distribuido.
5. Justificación de la simulación reproducible.
6. Justificación de CoppeliaSim como entorno aplicado.
7. Brecha del trabajo.
8. Estructura de la memoria.

Extensión recomendada para Tarea 1: 4-6 páginas.

### 2. Objetivos

Debe tener objetivo general y objetivos específicos medibles.

Objetivo general recomendado:

**Diseñar, implementar y evaluar un esquema de control cooperativo distribuido, basado en consenso y con compensación adaptativa o robusta, para el transporte de una carga por múltiples AGVs bajo incertidumbre inercial, mediante simulación reproducible y validación aplicada en CoppeliaSim.**

Objetivos específicos:

1. Formular un modelo planar del sistema multi-AGV-carga.
2. Definir el marco de cooperación entre AGVs mediante grafos de comunicación local.
3. Diseñar una línea base de control distribuido nominal basada en consenso.
4. Diseñar una variante adaptativa o robusta ante incertidumbre inercial.
5. Analizar cómo la topología de comunicación afecta la cooperación y el desempeño del transporte.
6. Implementar un entorno de simulación reproducible en Python.
7. Implementar una validación visual en CoppeliaSim.
8. Definir métricas de seguimiento, formación, esfuerzo, convergencia y robustez cooperativa.
9. Comparar ambos controladores en escenarios de incertidumbre y perturbación.

Extensión recomendada: 2-3 páginas.

### 3. Hipótesis de partida

Hipótesis principal:

**Una estrategia distribuida adaptativa basada en consenso puede reducir la degradación del desempeño cooperativo frente a incertidumbre inercial de la carga, en comparación con una estrategia nominal, siempre que el grafo de comunicación mantenga conectividad suficiente.**

Hipótesis secundarias:

1. El controlador adaptativo reducirá el error de seguimiento y de formación en escenarios con variación de masa y desplazamiento del centro de masas.
2. La mejora en robustez implicará un incremento moderado del esfuerzo de control.
3. La ventaja del controlador adaptativo disminuirá si la conectividad del grafo se degrada por debajo de un umbral crítico.
4. El índice IRCCI permitirá resumir de forma comparativa la robustez cooperativa de cada estrategia.

Extensión recomendada: 1.5-2 páginas.

### 4. Metodología

Debe ser el apartado más sólido de la Tarea 1. Aquí se decide si el trabajo parece viable.

Subestructura recomendada:

#### 4.1 Diseño de investigación

Investigación aplicada, cuantitativa, experimental en simulación y de carácter comparativo.

El diseño se centra en contrastar dos estrategias de control cooperativo: una línea base nominal distribuida y una variante adaptativa o robusta. La cooperación se modela mediante grafos de comunicación local, y el efecto de dicha cooperación se evalúa a través del seguimiento de la carga, el mantenimiento de la formación y la respuesta ante degradación de conectividad.

#### 4.2 Fases del trabajo

1. Revisión bibliográfica.
2. Modelado del sistema.
3. Diseño del controlador nominal.
4. Diseño del controlador adaptativo.
5. Implementación en Python.
6. Implementación visual en CoppeliaSim.
7. Diseño experimental.
8. Ejecución de experimentos.
9. Análisis de resultados.
10. Redacción y preparación del paper.

#### 4.3 Variables de estudio

Variables independientes:

- masa de la carga;
- desplazamiento del centro de masas;
- topología del grafo;
- perturbaciones externas;
- tipo de controlador.

Variables dependientes:

- error de seguimiento;
- error de formación;
- esfuerzo de control;
- tiempo de convergencia;
- índice IRCCI.

Variables controladas:

- trayectoria de referencia;
- número de AGVs;
- condiciones iniciales;
- tiempo de simulación;
- ganancias iniciales;
- semilla aleatoria.

#### 4.4 Instrumentos y herramientas

- Python 3.11+;
- NumPy/SciPy;
- Matplotlib;
- pytest;
- YAML para configuración;
- CoppeliaSim;
- Git/GitHub;
- Zotero o gestor bibliográfico;
- LaTeX/Word según plantilla VIU.

#### 4.5 Escenarios experimentales

1. Caso base nominal.
2. Variación de masa.
3. Desplazamiento del centro de masas.
4. Degradación de comunicación.
5. Perturbaciones externas.

#### 4.6 Métricas

- RMSE de seguimiento.
- Error máximo de seguimiento.
- RMSE de formación.
- Esfuerzo acumulado de control.
- Tiempo de convergencia.
- Índice IRCCI.

#### 4.7 Validación

Validación interna:

- pruebas unitarias;
- comparación nominal/adaptativo bajo los mismos escenarios;
- repetibilidad mediante semillas;
- conservación de estructura de datos.

Validación aplicada:

- escena CoppeliaSim;
- visualización de AGVs;
- trayectoria cooperativa;
- caso base y caso perturbado.

#### 4.8 Criterios de aceptación del método

El enfoque se considerará satisfactorio si:

- el simulador ejecuta todos los escenarios;
- las métricas se calculan automáticamente;
- las figuras y tablas se generan desde resultados reproducibles;
- el controlador adaptativo muestra mejora en al menos parte de los escenarios con incertidumbre;
- las limitaciones quedan justificadas.

Extensión recomendada de Metodología para Tarea 1: 6-8 páginas.

## Extensión recomendada para la Tarea 1

No conviene entregar solo 6-8 páginas. Para que parezca un TFM avanzado hasta metodología:

- portada, resumen e índices: 4-6 páginas;
- introducción: 4-6 páginas;
- objetivos: 2-3 páginas;
- hipótesis: 1.5-2 páginas;
- metodología: 6-8 páginas;
- referencias preliminares: 2-4 páginas.

Total recomendado: 18-25 páginas en PDF.

## Riesgos de No Aceptado

Riesgos principales:

- entregar un documento que parezca propuesta y no memoria TFM;
- no usar la plantilla oficial;
- objetivos demasiado generales;
- metodología sin variables ni métricas;
- CoppeliaSim mencionado sin papel claro;
- demasiada teoría sin plan de implementación;
- hipótesis no contrastables;
- ausencia de referencias APA;
- encabezados vacíos;
- no explicar cómo se validarán los resultados.

## Checklist antes de subir el PDF

- El título está cerrado y alineado con MROB.
- El resumen tiene 200-300 palabras.
- Hay 3-5 palabras clave.
- La introducción plantea problema, brecha y justificación.
- Los objetivos son medibles.
- La hipótesis se puede probar o refutar.
- La metodología incluye diseño, variables, herramientas, fases, métricas y validación.
- Se menciona CoppeliaSim con función concreta.
- Se menciona Python como base reproducible.
- Hay referencias preliminares en APA 7.
- No hay apartados vacíos.
- No hay encabezados consecutivos sin texto.
- El PDF se ve profesional.

## Plan operativo hasta el 29/05/2026

### 13-15 mayo

Cerrar alcance, título, objetivos, hipótesis y metodología.

### 16-19 mayo

Redactar Introducción y Fundamentación con referencias reales.

### 20-22 mayo

Redactar Metodología completa y diseñar tabla de variables/métricas.

### 23-25 mayo

Pasar contenido a la plantilla oficial VIU y generar primer PDF.

### 26-27 mayo

Revisión de estilo, coherencia, APA y formato.

### 28 mayo

PDF final de Tarea 1 listo.

### 29 mayo

Entrega.
