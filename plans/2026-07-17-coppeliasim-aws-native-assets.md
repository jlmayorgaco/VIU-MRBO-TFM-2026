# Activos nativos AWS para CoppeliaSim Industrial 2

## Propósito y resultado observable

Reutilizar el pavimento y las texturas de embalaje de
`aws_robomaker_warehouse.ttt` en la escena Industrial 2. La captura debe mostrar
un acabado próximo al escenario AWS suministrado sin cerrar corredores AMR ni
crear objetos que parezcan suspendidos.

## Contexto y archivos canónicos

- `tmp/scripts/coppelia/build_aws_canonical_scene.py`: suelo, estanterías y captura.
- `tmp/scripts/coppelia/build_aws_industrial_adversarial_scene.py`: variante Industrial 2.
- `coppeliasim/real_scenes/*industrial2.ttt`: escena exportada.
- `results/coppeliasim_validation/aws_industrial_adversarial_industrial2/`: capturas y auditoría.

## Alcance y no alcance

El cambio es visual: usa una forma de suelo no colisionable y comparte la
textura de cajas AWS con el inventario procedural dentro de las estanterías.
No modifica rutas, tareas, capacidades, métricas, control, sensores ni el nivel
de evidencia cinemática.

## Diseño técnico

La textura `concrete_plain.png` suministrada por CoppeliaSim se repite sobre un
plano continuo de 24x18 m. El ID de textura de
`/warehouse/floor/shippingBoxes_C/visible` se aplica con mapeado cúbico a las
cajas de las baldas. Se eliminan las pilas duplicadas sobre los racks porque,
aun alineadas geométricamente, su apoyo resulta ambiguo en la vista general.

La captura identifica mediante el mapa de profundidad los píxeles del plano
lejano y sustituye únicamente esos píxeles por el degradado vertical nativo de
CoppeliaSim. La geometría oscura de la escena permanece intacta.

## Validación

- Cero nuevas colisiones de layout y cero violaciones de soporte.
- El suelo AWS está visible y no es colisionable/respondable.
- La textura AWS aparece en cajas contenidas en las estanterías.
- No hay pilas de cajas sobre las cubiertas de los racks.
- La captura mantiene libres los corredores y muestra el degradado nativo.

## Registro de decisiones

- 2026-07-17: reutilizar exclusivamente activos AWS instalados; no importar
  texturas externas ni alterar resultados experimentales.
- 2026-07-17: retirar las pilas sobre racks; su lectura visual como cajas
  suspendidas es incompatible con la presentación industrial buscada.
- 2026-07-17: aplicar el degradado solo a píxeles sin geometría, identificados
  mediante la profundidad del VisionSensor.

## Progreso

- [x] Inventariar activos y texturas del escenario AWS suministrado.
- [x] Implementar suelo nativo y densificación texturizada dentro de las baldas.
- [x] Retirar pilas superiores visualmente ambiguas.
- [x] Regenerar `.ttt`, capturas y auditoría.
- [x] Ejecutar pruebas de escena.
- [x] Integrar y revisar `thesis/build/main.pdf`.
