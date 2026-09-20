# Ficha de evidencia — C0BBF943B50C0

## Identidad y estado

- **Estado de lectura:** `lectura_cercana_verificada`.
- **Tipo de fuente:** artículo primario con análisis de complejidad, formulación
  entera y comparación experimental de asignación de coaliciones.
- **Referencia:** Guerrero, J., Oliver, G., & Valero, O. (2017). *Multi-Robot
  Coalitions Formation with Deadlines: Complexity Analysis and Solutions*.
  PLOS ONE, 12(1), e0170659.
  https://doi.org/10.1371/journal.pone.0170659
- **Copia local inspeccionada:** `C0BBF943B50C0/fulltext.html`.
- **Tema para el TFM:** SP1; baseline/oráculo de formulación, no validación de
  transporte físico cooperativo.

## Pregunta y alcance de la fuente

El estudio formaliza formación de coaliciones para asignar tareas con plazos,
incorporando interferencia física entre robots como parte del coste/utilidad de
asignación. Contrasta una formulación entera óptima, cuando se satisfacen las
condiciones de su función de utilidad, con mecanismos de subasta. El trabajo
declara explícitamente que su capa de MRTA precede, pero no sustituye, una
metodología de interacción física de bajo nivel.

## Pasajes revisados

| Localizador en la copia local | Evidencia revisada | Uso permitido |
| --- | --- | --- |
| Resumen e introducción | Define el problema como asignación de tareas por coaliciones con plazos e interferencia de acceso. | Incluir plazo e interferencia como dimensiones de la formulación de SP1. |
| `MRTA Problem Fundamentals` | Distingue la taxonomía ST/MT, SR/MR e IA/TE y sitúa la formación de coaliciones en tareas multirrobot. | Codificar el tipo de asignación y evitar comparar casos estructuralmente distintos. |
| `Conclusions and future work`, primer párrafo | Los autores reportan que, bajo las características de utilidad establecidas en su formulación, la interferencia puede modelarse linealmente y se obtiene una solución óptima por programación lineal entera. | Usar la formulación central como referencia u oráculo condicionado, reproduciendo exactamente sus supuestos. |
| `Conclusions and future work`, segundo párrafo | Para sus experimentos, MDRA alcanza aproximadamente 70 % del óptimo con plazos duros y más de 80 % con plazos blandos, con menor tiempo de cómputo que los métodos de subasta previos considerados. | Informar un resultado empírico atribuido y limitado a su escenario, funciones de utilidad y comparadores. |
| `Conclusions and future work`, limitaciones | Identifica como trabajo posterior errores cinemáticos/localización, modelos de interferencia no lineales, interacción física y reasignación preventiva. | Delimitar lo que una capa de asignación no prueba sobre SP2 físico. |

## Lectura crítica

La contribución sirve para diseñar un oráculo central honesto para SP1: si la
formulación del TFM comparte los supuestos de recursos, plazos, utilidad e
interferencia, una ILP/MILP puede establecer factibilidad o un techo de utilidad
en instancias acotadas. No es lícito trasladar su porcentaje de utilidad al TFM
ni presentar la comparación como simétrica: el oráculo dispone de una
formulación central y el mecanismo propuesto debe operar con información local.

La fuente también es una advertencia contra el salto de niveles. Aunque modela
una forma de interferencia entre robots, no acredita contacto carga-robot,
preservación de formación, reparto de wrench, seguridad de navegación ni
recuperación mecánica tras fallo.

## Afirmaciones que esta fuente puede respaldar

1. La formación de coaliciones con plazos e interferencia puede requerir
   formulaciones distintas de asignación uno-a-uno.
2. Una solución de programación entera es un baseline válido solo cuando se
   especifican y respetan las condiciones de la utilidad y restricciones del
   problema.
3. Es posible comparar una heurística/subasta con una referencia óptima en
   escenarios acotados, reportando utilidad y tiempo de cómputo.

## Afirmaciones que esta fuente no permite hacer

- Que MDRA sea óptimo, robusto, escalable o superior fuera de sus escenarios.
- Que el 70–80 % se reproduzca con capacidades heterogéneas, comunicación
  imperfecta, múltiples cargas o el modelo físico del TFM.
- Que una interferencia lineal represente todas las colisiones, restricciones
  cinemáticas o contactos de transporte cooperativo.
- Que resolver SP1 garantice la ejecución estable de SP2.

## Consecuencia para la síntesis V3

Clasificar como **baseline primario de SP1 con evidencia formal y empírica
condicionada**. La ficha alimentará la tabla de formulaciones, baselines y
límites; cualquier reutilización del modelo debe documentar una reducción o una
adaptación explícita a los recursos y cargas heterogéneas del TFM.
