# Ampliación auditada del mapa data-driven

## Objetivo

Incorporar cinco trabajos con ejecución centralizada y cinco con ejecución descentralizada al cuadrante data-driven de la Figura 3, sin clasificar por palabras del título ni añadir fuentes que solo sean tangencialmente multiagente.

## Criterios de inclusión

- Fuente primaria verificable mediante DOI, editorial oficial o arXiv.
- Aplicación directa a MRTA, coordinación/planificación multi-robot, MAPF o transporte cooperativo.
- La decisión primaria en ejecución depende de una política, valor, heurística o representación aprendida.
- La arquitectura centralizada/descentralizada se acredita en el método o en el abstract, no se infiere del nombre.
- No duplicar trabajos ya presentes en `references/LITERATURE_LEDGER.md`.

## Criterios de exclusión

- MARL genérico sin experimento multi-robot relevante.
- Aprendizaje usado solo durante entrenamiento si la decisión desplegada es completamente white-box.
- Arquitectura de ejecución ambigua sin texto primario suficiente.
- Fuentes no verificables o con metadatos inconsistentes.

## Entregables

- Diez entradas verificadas en el ledger y en `thesis/references.bib`.
- Indicadores `dec`, `loc`, `learn`, `exp`, familia y alcance SP auditados.
- Figura 3 y Anexo F actualizados sin interpretar densidad como exhaustividad bibliométrica.
- PDF recompilado y revisado visualmente.

## Estado

- [x] Definir alcance y criterios.
- [x] Verificar cinco trabajos centralizados.
- [x] Verificar cinco trabajos descentralizados.
- [ ] Actualizar fuentes, rúbrica, figura y anexo.
- [ ] Compilar y validar.

## Selección verificada

### Centralizados y data-driven

1. Wang y Gombolay (2020), RoboGNN, IEEE RA-L.
2. Wang, Liu y Gombolay (2022), ScheduleNet, *Autonomous Robots*; extensión declarada de la misma línea de RoboGNN.
3. Park, Kang y Choi (2022), asignación cooperativa ST-MR-TA con DRL, *Applied Sciences*.
4. Dai, Kim y Lee (2024), FMS con DQN en nodo maestro, *Processes*.
5. Hu et al. (2026), E2AN con planificador central y estado global, *Applied Sciences*.

### Descentralizados y data-driven

1. Zhang et al. (2020), control DQN distribuido para transporte cooperativo, IEEE Access.
2. Li et al. (2021), MADDPG-IPF/BiCNet-IPF para asignación multi-AGV, IEEE MASS.
3. Elfakharany e Ismail (2021), política PPO sensor-a-control para MRTA y navegación, *Applied Sciences*.
4. Dai, Bidwai y Sartoretti (2024), coaliciones dinámicas y ruteo mediante RL, ICRA.
5. Bezerra, dos Santos y Park (2025), MAPPO local con intercambio de intenciones para coaliciones, IEEE RA-L.

gnPN (Zhang et al., 2024) queda como reserva: procesa el grafo global y produce la asignación conjunta, pero la descripción de ejecución no usa una etiqueta arquitectónica suficientemente inequívoca para este lote. CapAM tampoco se cuenta como centralizado: su fuente primaria declara ejecución descentralizada bajo observabilidad global.
