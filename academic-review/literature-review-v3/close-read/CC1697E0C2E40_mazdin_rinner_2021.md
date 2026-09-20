# Ficha de evidencia — CC1697E0C2E40

## Identidad y estado

- **Estado de lectura:** `lectura_cercana_verificada`.
- **Tipo de fuente:** artículo primario de simulación y análisis de
  comunicación para formación/asignación de coaliciones.
- **Referencia:** Mazdin, P., & Rinner, B. (2021). *Distributed and
  Communication-Aware Coalition Formation and Task Assignment in Multi-Robot
  Systems*. IEEE Access, 9, 35088–35100.
  https://doi.org/10.1109/ACCESS.2021.3061149
- **Copia local inspeccionada:** `CC1697E0C2E40.pdf`.
- **Tema para el TFM:** SP1 y eje transversal de comunicación; no valida SP2
  físico.

## Pregunta y alcance de la fuente

El artículo estudia un flujo cooperativo de formación de coaliciones,
asignación de tareas y ejecución conjunta bajo condiciones de comunicación no
ideales. Compara políticas de disparo temporal, por evento e híbridas y las
evalúa mediante simulación de red. El objeto de estudio es la decisión y el
intercambio de estado; no modela ni demuestra transporte físico cooperativo con
contacto carga-robot.

## Pasajes revisados

| Página | Evidencia revisada | Uso permitido |
| --- | --- | --- |
| 1, título y resumen | Identidad bibliográfica, objetivo de contrastar mecanismos distribuidos conscientes de la comunicación y una referencia centralizada. | Registrar la fuente como primaria y ubicarla en SP1/comunicación. |
| 1, figura del flujo de trabajo | Secuencia conceptual: formación de coalición, asignación y ejecución conjunta. | Representar la cadena decisión–asignación–ejecución como arquitectura de referencia, no como modelo físico. |
| 2, contribuciones y descripción de métodos | Dos métodos generan coaliciones desde proximidad antes de asignar; un tercero incorpora competencia por tareas/coaliciones. Se consideran pérdidas de mensajes y disparadores de comunicación. | Comparar familias de mecanismo distribuido y construir ablaciones de política de comunicación. |
| 12, conclusiones | Reporta un compromiso empírico para una política de reformación y plantea extensiones, entre ellas refinar heurísticas y validar con sistemas multirrobot reales. | Declarar que la evidencia es dependiente de simulación y no equivale a garantía de generalidad o despliegue físico. |

## Hallazgo delimitado

Esta fuente muestra que la política de comunicación es parte del diseño de SP1:
no basta evaluar la calidad de una coalición si no se informa el coste y el
comportamiento del mecanismo de actualización bajo pérdida de mensajes. Por
tanto, las campañas del TFM deben registrar mensajes o bytes, la regla de
disparo y la condición de red, además de factibilidad y utilidad de asignación.

## Afirmaciones que esta fuente puede respaldar

1. Existen enfoques distribuidos de formación y asignación de coaliciones que
   incorporan explícitamente el patrón de comunicación.
2. Es pertinente contrastar disparadores temporales, por evento e híbridos al
   estudiar la carga comunicacional y el comportamiento bajo pérdida de
   mensajes.
3. Una referencia centralizada puede utilizarse como comparador arquitectónico
   cuando se declara la asimetría de información.

## Afirmaciones que esta fuente no permite hacer

- Que las políticas examinadas garanticen convergencia, optimalidad social,
  seguridad o robustez para toda topología de red.
- Que los resultados de simulación sean evidencia de transporte cooperativo
  físico, reparto de wrench, preservación de contacto o evitación de colisiones.
- Que el algoritmo use exclusivamente percepción local o que sea directamente
  transferible a AMR terrestres heterogéneos sin una adaptación explícita.
- Que el compromiso observado en sus escenarios sea un parámetro universal.

## Consecuencia para la síntesis V3

Clasificar como **artículo primario relevante para SP1 y comunicación**. Debe
alimentar la matriz de dimensiones experimentales —política de disparo, pérdidas
de mensajes, carga de comunicación y referencia centralizada—, pero no el
argumento de validez mecánica de SP2.
