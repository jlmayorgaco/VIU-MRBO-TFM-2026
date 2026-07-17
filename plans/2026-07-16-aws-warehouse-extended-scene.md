# Ampliacion de la escena AWS Warehouse en CoppeliaSim

## Proposito y resultado observable

Consolidar el intento `tmp/coppeliasim/real_scenes/aws_canonical_coop_transport_pioneer_p3dx.*` como una escena AWS Warehouse ampliada y ejecutable. La escena resultante debe contener cuatro zonas AMR, una en cada esquina, cuatro zonas de despacho con cajas que descienden desde altura, cuatro zonas de destino, estanterias apoyadas y orientadas, pasillos transitables y una demostracion determinista de recogida y entrega.

## Contexto y archivos canonicos

- Base: escena instalada `scenes/awsRobomaker/aws_robomaker_warehouse.ttt`.
- Generador: `tmp/scripts/coppelia/build_aws_canonical_scene.py`.
- Artefactos: `tmp/coppeliasim/real_scenes/aws_canonical_coop_transport_pioneer_p3dx.{yaml,lua,ttt}`.
- Validacion: `results/coppeliasim_validation/aws_canonical/`.
- Alcance cientifico: la animacion es una prueba visual y geometrica de la escena, no evidencia de control fisico ni de estabilidad.

## Alcance y no alcance

Incluye ampliacion del suelo, paredes, estanterias, zonas, robots, rutas, cajas y camaras; comprobaciones 2-D/3-D basicas; exportacion real `.ttt`; capturas de inspeccion y prueba de humo del script embebido.

No incluye implementar el algoritmo distribuido de asignacion/control del TFM, sensores reales, agarre dinamico certificado ni resultados experimentales para SP3--SP8.

## Supuestos y preguntas resueltas

- Se interpreta "AME" como "AMR".
- Se usa una nave de 24 m x 18 m para separar zonas operativas, estanterias y pasillos.
- Cada flujo de despacho se atiende visualmente con una coalicion de dos Pioneer P3-DX; quedan cuatro robots de reserva, uno por esquina.
- La caida se representa dentro del script de demostracion con descenso vertical controlado y aterrizaje en una plataforma; no se presenta como simulacion fisica validada de impacto.

## Diseno matematico/tecnico

- Limites del plano: `x in [-12,12]`, `y in [-9,9]`.
- Zonas AMR en las cuatro esquinas; despachos en el borde norte; destinos en el borde sur.
- Estanterias en bloques centrales con pasillos longitudinales y transversales de al menos 1.5 m.
- Todas las huellas estaticas y operativas se validan con cajas delimitadoras orientadas y margen de seguridad.
- Elementos visuales deben tener soporte vertical explicito: estanterias y paredes en `z=0`, plataformas apoyadas en el suelo y luminarias sujetas a cerchas.
- El script embebido mantiene cajas y robots en poses coherentes durante caida, recogida, transporte, entrega y retorno.

## Plan experimental

Prueba unica de escena con semilla determinista implícita: validacion geometrica previa, exportacion real mediante ZMQ, carga de la escena, avance de simulacion durante varios segundos, auditoria de posiciones/orientaciones y capturas superior/oblicua.

## Hitos

- [x] Hito 1 — Diseno ampliado y validador actualizado sin solapes.
- [x] Hito 2 — YAML y Lua regenerados de forma reproducible.
- [x] Hito 3 — `.ttt` exportado desde la escena AWS instalada.
- [x] Hito 4 — Prueba de humo, capturas y auditoria final aprobadas.

## Validacion

- `python tmp/scripts/coppelia/build_aws_canonical_scene.py --no-export-ttt`
- `python tmp/scripts/coppelia/build_aws_canonical_scene.py --launch-coppelia`
- Carga remota del `.ttt`, inicio de simulacion y muestreo de cajas/robots.
- Revision de `layout_validation.json`, manifiesto y capturas.

## Riesgos y mitigaciones

- Modelos importados con origen local inesperado: auditar bounding boxes tras exportar y ajustar `z`/orientacion.
- Coste grafico de muchas estanterias: usar geometria procedural simple y limitar decoracion.
- Colision visual entre rutas: separar marcadores no respondables de la geometria fisica.
- La reproduccion cinematica no valida control: declarar el limite en metadatos y entrega.

## Registro de decisiones

- 2026-07-16: se conserva el nombre canonico del artefacto para evitar otro intento divergente y se generan copias de seguridad antes de reemplazar el `.ttt`.
- 2026-07-16: se adopta 24 m x 18 m y cuatro flujos norte--sur por legibilidad, separacion y trazabilidad.

## Progreso

Escena consolidada y exportada con 2.069 objetos. La validacion previa informa 12 zonas operativas, 20 estanterias, 12 robots, cero solapes y cero violaciones de soporte. La auditoria real de un ciclo de 42 s verifica las cuatro caidas, recogidas, trayectos y entregas; no faltan aliases ni elementos soportados. Las ruedas de los Pioneer quedaron a 0,214 mm del plano del suelo tras corregir la cota heredada. La camara oblicua se rehizo como vista ortografica orientada al centro para inspeccionar la nave completa. Cuatro pruebas unitarias cubren inventario, orientacion, layout y separacion de trayectorias respecto de estanterias/isla central.
