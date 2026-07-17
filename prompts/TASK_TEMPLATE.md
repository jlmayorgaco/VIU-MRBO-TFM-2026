# Plantilla de tarea de investigación

Copiar y completar solo los campos necesarios.

```text
Lee AGENTS.md y los documentos canónicos aplicables antes de actuar.

OBJETIVO
[Resultado concreto que se busca.]

SUBPROBLEMA Y PREGUNTA
[SP0–SP8, RQ y afirmación Cx relacionada.]

CONTEXTO
[Archivos, ecuaciones, resultados o decisiones que importan.]

RESTRICCIONES
- No inventar referencias, datos ni resultados.
- Mantener compatibilidad con la notación y el protocolo experimental.
- [Otras restricciones.]

ENTREGABLES
1. [Archivo/cambio/tabla/figura.]
2. [Pruebas o análisis.]
3. [Actualización de trazabilidad.]

VERIFICACIÓN
- [Comando o test.]
- [Criterio cuantitativo o propiedad.]

NO HACER
- [Fuera de alcance.]

TERMINADO CUANDO
[Condiciones objetivas de finalización.]
```

## Prompt — Auditoría del planteamiento

```text
Lee AGENTS.md, docs/00_TFM_CHARTER.md, docs/01_VIU_REQUIREMENTS.md y docs/02_RESEARCH_MATRIX.md. Compara el planteamiento actual de la memoria con esos documentos. No edites nada. Entrega una tabla con: contradicción, impacto, evidencia en el archivo, corrección propuesta y prioridad. Señala especialmente claims de optimalidad/convergencia, uso incorrecto del algoritmo húngaro, mezcla de tiempo continuo/discreto y alcance excesivo.
```

## Prompt — Diseñar un SP

```text
Trabaja sobre [SPX]. Primero crea un ExecPlan conforme a plans/PLANS.md. Debes entregar: formulación incremental respecto al SP anterior, supuestos, algoritmo propuesto en pseudocódigo, baseline adecuado, resultado formal alcanzable, protocolo experimental, tests e impacto en la memoria VIU. No implementes hasta comprobar consistencia dimensional y factibilidad del experimento.
```

## Prompt — Implementar experimento

```text
Implementa el experimento [ID] para [SPX] de manera config-driven. Usa semillas explícitas, salida estructurada y generación automática de figuras/tablas. Añade tests de métricas e invariantes. Ejecuta un smoke test pequeño. No redactes conclusiones científicas hasta procesar los datos y actualizar docs/04_CLAIMS_EVIDENCE.md.
```

## Prompt — Redactar una sección de tesis

```text
Redacta la sección [número/título] en español académico usando únicamente resultados y referencias verificadas presentes en el repositorio. Antes de escribir, lista las afirmaciones que la sección hará y vincúlalas con docs/04_CLAIMS_EVIDENCE.md. No rellenes vacíos con lenguaje especulativo. Distingue resultado formal, observación experimental y limitación. Mantén APA 7 y la estructura VIU.
```
