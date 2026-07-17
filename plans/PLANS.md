# PLANS.md — Planes de ejecución para tareas complejas

Usar un ExecPlan cuando la tarea involucre uno o más de estos casos:

- una formulación matemática nueva;
- un SP completo;
- cambio de arquitectura;
- experimento con múltiples algoritmos/escenarios;
- redacción de una sección que dependa de código y resultados;
- refactor que afecte reproducibilidad o métricas.

Cada plan debe ser autosuficiente y mantenerse actualizado durante la ejecución.

## Plantilla obligatoria

```markdown
# [Título del plan]

## Propósito y resultado observable
Qué cambia y cómo podrá verificarse.

## Contexto y archivos canónicos
Documentos, módulos, datos y decisiones relevantes.

## Alcance y no alcance
Qué incluye y qué queda fuera.

## Supuestos y preguntas resueltas
Supuestos conservadores adoptados y su impacto.

## Diseño matemático/técnico
Variables, interfaces, algoritmo, invariantes y alternativas descartadas.

## Plan experimental
Escenarios, baselines, métricas, semillas, criterios de éxito y análisis.

## Hitos
- [ ] Hito 1 — resultado verificable.
- [ ] Hito 2 — resultado verificable.

## Validación
Comandos, pruebas, experimento de humo y criterios de aceptación.

## Riesgos y mitigaciones
Riesgos científicos, numéricos, de alcance y de reproducibilidad.

## Registro de decisiones
Fecha, decisión y razón.

## Progreso
Hechos completados, problemas encontrados y próximos pasos concretos.
```

## Reglas de ejecución

- No iniciar una implementación grande con una lista vaga de tareas.
- Actualizar el plan cuando cambie una decisión sustantiva.
- No borrar problemas encontrados; documentar resolución o limitación.
- Un plan no reemplaza pruebas, resultados ni revisión del diff.
