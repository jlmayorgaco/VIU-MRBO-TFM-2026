# Plan reorganizado del TFM

## Criterio de madurez tomado de los TFM de referencia

Los TFM revisados muestran un patrón común de madurez: no se limitan a exponer teoría, sino que convierten una técnica de control en un proyecto completo con objeto técnico, alcance, modelo, implementación, validación, resultados, conclusiones y anexos. Las memorias analizadas se sitúan aproximadamente entre 62 y 132 páginas, con una estructura técnica densa, abundantes figuras, tablas de parámetros, capturas de simulación, código o anexos, y una separación clara entre fundamentación, diseño e implementación.

Para este TFM, el estándar mínimo debe ser:

- problema industrial claro;
- objetivo técnico y académico explícitos;
- alcance cerrado y defendible;
- modelo matemático del sistema robot-carga;
- controlador nominal de referencia;
- controlador adaptativo o robusto propuesto;
- simulación reproducible en Python;
- validación visual/aplicada en CoppeliaSim;
- métricas comparativas;
- resultados con figuras y tablas;
- discusión honesta de límites;
- anexos con configuración, código relevante y parámetros.

## Enfoque recomendado

El TFM debe mantener el interés teórico, pero presentarse como un proyecto de ingeniería aplicada en robótica avanzada. El eje conceptual debe ser:

**control cooperativo multiagente.**

La teoría central no será CoppeliaSim ni una métrica aislada, sino la relación entre control distribuido, consenso, cooperación local e incertidumbre inercial. CoppeliaSim funcionará como validación aplicada, y las métricas como instrumentos de contraste.

La contribución no debe venderse como una teoría totalmente nueva, sino como una propuesta incremental, medible y defendible:

**Arquitectura de control cooperativo adaptativo para transporte multi-AGV bajo incertidumbre inercial de la carga.**

La idea central es diseñar una estrategia en la que cada AGV actúa con información local, coopera mediante un grafo de comunicación y contribuye al transporte estable de la carga. La evaluación comparará cómo se degrada el desempeño cooperativo cuando cambian masa, centro de masas, perturbaciones externas o conectividad del grafo, y si el controlador adaptativo reduce esa degradación frente a una línea base nominal.

## Título recomendado

**Control distribuido adaptativo basado en consenso para transporte cooperativo multi-AGV bajo incertidumbre inercial de la carga**

Subtítulo operativo:

**Modelado, simulación reproducible y validación en CoppeliaSim**

## Objeto técnico

Diseñar, implementar y evaluar un esquema de control distribuido para un sistema de 2 a 4 AGVs que transportan cooperativamente una carga rígida en el plano, considerando incertidumbre en parámetros inerciales de la carga y comunicación local entre agentes.

## Objeto académico

Demostrar la integración de competencias del Máster Universitario en Robótica y Automatización de Procesos mediante un trabajo original que combine modelado dinámico, control avanzado, simulación, robótica móvil, análisis de resultados y comunicación técnica.

## Alcance

El alcance queda limitado a:

1. Modelado planar de un sistema carga-AGVs con 2 a 4 robots.
2. Grafos de comunicación local conectados o degradados de forma controlada.
3. Control nominal distribuido basado en consenso.
4. Variante adaptativa o robusta frente a incertidumbre inercial.
5. Validación cuantitativa en simulación Python.
6. Validación visual/aplicada en CoppeliaSim para el escenario base y uno o dos escenarios perturbados.
7. Comparación mediante métricas de seguimiento, formación, esfuerzo de control, convergencia y robustez.

Queda fuera del alcance:

- implementación física real en AGVs;
- identificación experimental completa de parámetros;
- percepción real con sensores;
- planificación global de rutas;
- seguridad industrial certificable;
- optimización multiobjetivo avanzada.

## Contribución teórica-técnica incremental

La contribución principal debe formularse así:

**Diseño y evaluación de una arquitectura de control cooperativo distribuido para transporte multi-AGV bajo incertidumbre inercial.**

Esta arquitectura integra:

1. control por consenso;
2. cooperación multiagente;
3. grafos de comunicación local;
4. compensación adaptativa o robusta;
5. evaluación cuantitativa de robustez cooperativa.

Como contribución secundaria de evaluación, se propone introducir un índice de robustez cooperativa:


```text
IRCCI = 1 - (D_adaptativo / D_nominal)
```

donde `D` representa la degradación relativa de desempeño respecto al caso nominal:

```text
D = w1 * degradación_error_seguimiento
  + w2 * degradación_error_formación
  + w3 * degradación_tiempo_convergencia
  + w4 * degradación_esfuerzo_control
```

Interpretación:

- `IRCCI > 0`: la estrategia adaptativa mejora la robustez.
- `IRCCI = 0`: no hay mejora neta.
- `IRCCI < 0`: la estrategia adaptativa empeora el desempeño global.

Este índice permite defender el TFM como algo más que una comparación de gráficas, pero no sustituye la contribución principal. El centro teórico sigue siendo el diseño de control cooperativo.

## Estructura propuesta de memoria

### 1. Introducción

- Contexto: robótica móvil, AGVs, logística interna e Industria 4.0.
- Problema: transporte cooperativo de cargas con incertidumbre.
- Motivación: necesidad de control distribuido robusto.
- Relación con VIU: robótica avanzada, automatización, control, simulación y aplicabilidad.
- Organización de la memoria.

### 2. Objetivos, hipótesis y alcance

- Objetivo general.
- Objetivos específicos.
- Pregunta de investigación.
- Hipótesis.
- Alcance.
- Limitaciones.
- Criterios de éxito.

### 3. Estado del arte y marco conceptual

- Transporte cooperativo multi-robot.
- AGVs y AMRs en automatización industrial.
- Control distribuido.
- Control por consenso.
- Cooperación multiagente.
- Teoría de grafos para comunicación local.
- Formación y coordinación cooperativa.
- Control adaptativo y robusto.
- Incertidumbre inercial en transporte de cargas.
- Simulación robótica y CoppeliaSim.
- Brecha que aborda el TFM.

### 4. Modelado del sistema

- Definición del sistema robot-carga.
- Estados del AGV.
- Estados de la carga.
- Cinemática planar.
- Supuestos dinámicos.
- Modelo de interacción carga-robots.
- Grafos de comunicación.
- Incertidumbre de masa, inercia y centro de masas.
- Trayectorias de referencia.

### 5. Diseño de control cooperativo

- Arquitectura general.
- Controlador nominal distribuido basado en consenso.
- Mecanismo de cooperación local entre AGVs.
- Influencia del grafo de comunicación.
- Controlador adaptativo/robusto propuesto.
- Ley de actualización o compensación.
- Condiciones de conectividad.
- Parámetros de control.
- Discusión de estabilidad o boundedness con alcance adecuado al TFM.

### 6. Implementación computacional

- Arquitectura del repositorio.
- Python como simulador reproducible.
- Configuración por experimentos.
- Métricas implementadas.
- Generación de figuras y tablas.
- CoppeliaSim como entorno de validación visual.
- Correspondencia Python-CoppeliaSim.

### 7. Diseño experimental

Escenarios:

1. Caso nominal base.
2. Variación de masa.
3. Desplazamiento del centro de masas.
4. Degradación de comunicación.
5. Perturbaciones externas.

Para cada escenario:

- parámetros;
- hipótesis esperada;
- variables medidas;
- número de repeticiones;
- semillas;
- criterio de comparación.

### 8. Resultados

- Resultados del caso nominal.
- Resultados con variación de masa.
- Resultados con desplazamiento del centro de masas.
- Resultados con degradación de comunicación.
- Resultados con perturbaciones.
- Tabla comparativa nominal vs adaptativo.
- Índice IRCCI por escenario.
- Capturas o figuras de CoppeliaSim.

### 9. Discusión

- En qué escenarios mejora el método adaptativo.
- Coste en esfuerzo de control.
- Sensibilidad a parámetros.
- Dependencia de conectividad del grafo.
- Diferencias entre simulación Python y CoppeliaSim.
- Validez externa.
- Limitaciones.

### 10. Conclusiones y trabajo futuro

- Respuesta a la pregunta de investigación.
- Verificación de hipótesis.
- Aportes técnicos.
- Aportes académicos.
- Líneas futuras: AGVs reales, ROS 2, percepción, planificación, validación física.

### Anexos

- Configuraciones de experimentos.
- Parámetros de control.
- Fragmentos de código clave.
- Capturas de CoppeliaSim.
- Instrucciones de reproducibilidad.
- Tablas extendidas.

## Plan de ataque de 4 semanas

### Semana 1: cerrar núcleo técnico

Entregables:

- modelo matemático cerrado;
- controlador nominal funcional;
- controlador adaptativo funcional;
- simulador Python operativo;
- estructura de memoria final creada;
- escenario base en CoppeliaSim definido.

### Semana 2: producir evidencia

Entregables:

- cinco experimentos ejecutados;
- tablas comparativas;
- figuras finales;
- cálculo de IRCCI;
- validación visual CoppeliaSim del caso base y un caso perturbado.

### Semana 3: escribir memoria completa

Entregables:

- capítulos 1 a 10 redactados;
- resultados integrados;
- discusión crítica;
- anexos de reproducibilidad;
- revisión bibliográfica ordenada.

### Semana 4: hacerla defendible y publicable

Entregables:

- PDF final del TFM;
- presentación de defensa;
- auditoría de citas;
- auditoría de resultados;
- versión corta tipo artículo científico.

## Conversión a paper

El paper debe salir de los capítulos 4 a 9, no de toda la memoria.

Estructura recomendada:

1. Introduction
2. Related Work
3. Problem Formulation
4. Distributed Adaptive Consensus Control
5. Simulation and CoppeliaSim Validation
6. Results
7. Discussion
8. Conclusions

La contribución publicable debe formularse así:

**This work proposes and evaluates a cooperative distributed adaptive consensus control architecture for multi-AGV load transport under inertial uncertainty. The study focuses on how local communication, graph connectivity and adaptive compensation affect cooperative tracking, formation maintenance and robustness under mass variation, center-of-mass shift, communication degradation and external disturbances.**

## Criterios de calidad para aspirar a 5/5

- El alcance está cerrado y no promete hardware real.
- La teoría se conecta con una implementación visible.
- CoppeliaSim aparece como validación aplicada, no como adorno.
- Cada figura responde una pregunta.
- Cada conclusión se apoya en una métrica.
- La comparación nominal/adaptativo es justa.
- Los resultados negativos o mixtos se discuten, no se ocultan.
- El repositorio permite reproducir experimentos.
- La memoria tiene estilo de proyecto técnico maduro, no solo ensayo teórico.
