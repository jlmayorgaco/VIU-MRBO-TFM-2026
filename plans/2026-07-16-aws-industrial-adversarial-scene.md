# Variante AWS industrial adversarial

## Proposito y resultado observable

Crear una copia independiente de la escena AWS nominal que muestre de forma mas convincente el problema industrial del TFM: cargas heterogeneas en cola, coaliciones de cardinalidad variable, trafico compartido, un cuello de botella, un fallo con sustitucion local y restricciones de seguridad visibles.

## Contexto y archivos canonicos

- Base nominal preservada: `tmp/coppeliasim/real_scenes/aws_canonical_coop_transport_pioneer_p3dx.*`.
- Generador reutilizado: `tmp/scripts/coppelia/build_aws_canonical_scene.py`.
- Nuevo generador: `tmp/scripts/coppelia/build_aws_industrial_adversarial_scene.py`.
- Nuevos artefactos: `tmp/coppeliasim/real_scenes/aws_industrial_adversarial_coop_transport_pioneer_p3dx.*`.
- Evidencia de escena: `tmp/results/coppeliasim_validation/aws_industrial_adversarial/`.

## Alcance y no alcance

Incluye composicion visual, animacion cinematica reproducible, colas, transportadores, plataformas de carga, cargas 1/2/3-AMR, cuello de botella, carretilla, peaton, AMR libre, fallo/sustitucion, señalizacion, camaras y señales de metricas.

No incluye contacto mecanico validado, agarre dinamico, percepcion real, CBF/ORCA ejecutado, planificacion distribuida completa ni evidencia de estabilidad. La escena ilustra esos problemas; los experimentos cientificos deben implementarlos y medirlos por separado.

## Supuestos y preguntas resueltas

- La escena nominal queda sin cambios y sirve como control nominal.
- La nave mantiene 24 m x 18 m para comparar ambas variantes.
- Las cajas no aparecen sin infraestructura: una tolva alimenta un transportador y un buffer visible.
- El cuello de botella central fuerza rutas convergentes y hace visible la competencia por espacio.
- Un Pioneer queda fuera de servicio y un robot de reserva se incorpora a la coalicion demostrativa.

## Diseno matematico/tecnico

- Cuatro estaciones de despacho, cada una con dos cargas en espera y una carga activa.
- Requisitos de coalicion visibles de 1, 2 y 3 AMR; masas y geometria distintas.
- Barreras longitudinales dejan una unica puerta central de 2,6 m.
- Trafico transversal determinista: carretilla, peaton y AMR libre con fases separadas.
- Plataformas solidarias a los robots representan la interfaz Cargo sin reclamar una prueba de wrench.
- El script embebido publica entregas, cola restante, estado de fallo y ocupacion del cuello de botella como señales de CoppeliaSim.

## Plan experimental

Prueba de escena determinista: validacion geometrica previa, exportacion real, capturas superior/oblicua/cuello de botella, avance muestreado de la simulacion y auditoria de presencia, soportes, movimiento, fallo/sustitucion y llegada de cargas.

## Hitos

- [x] Copia logica y rutas adversariales.
- [x] Infraestructura industrial y actores dinamicos.
- [x] Animacion, camaras y metricas.
- [x] Exportacion `.ttt` y capturas.
- [x] Pruebas y auditoria final.

## Validacion

- `python tmp/scripts/coppelia/build_aws_industrial_adversarial_scene.py --no-export-ttt`
- `python tmp/scripts/coppelia/build_aws_industrial_adversarial_scene.py --launch-coppelia`
- `python -m pytest tmp/tests/test_aws_industrial_adversarial_scene.py -q`
- Auditoria remota de un ciclo abreviado con dinamica fisica deshabilitada, porque el objetivo es verificar la coreografia y la geometria.

## Riesgos y mitigaciones

- Sobrecarga visual: usar colores industriales y limitar actores dinamicos a tres.
- Colisiones cinematograficas: desfase temporal y auditoria de trayectorias.
- Confusion entre ilustracion y validacion: metadatos y documentacion declaran el alcance cinemático.
- Coste de exportacion: reutilizar primitivas y modelos ya instalados.

## Registro de decisiones

- 2026-07-16: se crea una variante separada y no se sobrescribe la escena nominal.
- 2026-07-16: se conserva la modalidad Cargo como representacion principal mediante plataformas sobre los Pioneer.
- 2026-07-16: se sustituye la caída vertical por alimentación horizontal desde conveyor con buffer y tope.
- 2026-07-16: se añaden dos Walking Bill con rutas deterministas y arbitraje visual de prioridad en el cuello de botella.

## Progreso

Implementacion completada. Validacion estatica sin colisiones, 11 pruebas superadas y auditoria cinemática de 45 s correcta. La escena queda clasificada como demostrador visual; las afirmaciones físicas requieren experimentos separados.
