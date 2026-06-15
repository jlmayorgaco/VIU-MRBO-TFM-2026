# Resultados TFM - borrador de seccion 5

## Mini-outline

- Validar primero los mecanismos aislados H1-H3 para separar teoria de interacciones del benchmark.
- Presentar cuatro escenarios canonicos del benchmark v2.7: abundancia, escasez con prioridad, fallo de robot y degradacion de comunicacion.
- Usar sweeps para delimitar regimenes: carga, radio de comunicacion, precio y cierre teoria-realidad.
- Cerrar con limitaciones: las figuras de estado usan ocupaciones registradas, no coordenadas roboticas completas.

## 5.1 Banco minimo de mecanismos

El banco minimo separa los tres mecanismos teoricos antes de interpretar el benchmark completo. H1 verifica que la dinamica de Smith reproduce el water-filling en equilibrio, H2 confirma que el clearing entero reduce desperdicio bajo escasez, y H3 corrige la interpretacion del precio: el precio no mejora el equilibrio estatico, pero si aporta valor cuando hay llegadas y deadlines.

![H3-B existing delta](../results/figures_pdf/sweeps/h3b_existing_delta_by_regime.pdf)

Figura: resultado H3-B disponible. En abundancia el delta medio es 0.0000; en escasez el delta medio es 0.2785, con IC95 [0.2234, 0.3337]. La afirmacion defendible es temporal: el precio rescata valor bajo escasez dinamica, no en equilibrio estatico.

## 5.2 Escenarios canonicos v2.7

El escenario de abundancia funciona como control de sanidad: las entregas son altas y las diferencias entre metodos no deben sobrerrelatarse cuando los intervalos se solapan.

![Abundance comparison](../results/figures_pdf/scenarios/abundance/method_comparison.pdf)

En escasez con prioridad aparece el caso central para la tesis. Smith alcanza captura media 0.465, mientras que el centralizado min-cost queda en 0.416; la lectura correcta depende del IC95 y queda trazada en la figura, no solo en la media.

![Scarcity priority comparison](../results/figures_pdf/scenarios/scarcity_priority/method_comparison.pdf)

El fallo de robot mide robustez operacional. Aqui la pregunta no es solo cuanta recompensa se captura, sino si el sistema recupera asignaciones utiles sin introducir un coordinador central.

![Robot failure temporal](../results/figures_pdf/scenarios/robot_failure/temporal_metrics.pdf)

La degradacion de comunicacion delimita la frontera honesta del metodo. Smith conserva captura media 0.579 con R12, pero cae a 0.098 en R3; este resultado debe presentarse como limite de aplicabilidad, no como fallo oculto.

![Communication comparison](../results/figures_pdf/scenarios/comm_degradation/method_comparison.pdf)

## 5.3 Barridos consolidados

Los barridos convierten los escenarios puntuales en regimenes. El load sweep resume donde la carga empieza a degradar la captura; el comm sweep muestra la transicion por conectividad; el price-regime plot documenta que el precio puede restar en flujo nominal y cambiar de signo en escasez priorizada.

![Load sweep](../results/figures_pdf/sweeps/load_sweep_capture.pdf)

![Communication sweep](../results/figures_pdf/sweeps/comm_sweep_capture.pdf)

![Price regime](../results/figures_pdf/sweeps/price_regime_delta.pdf)

El cierre teoria-realidad debe leerse por regimen. La correlacion mejora en ventanas post-contacto con z* capado al peso de la carga, mientras que escenarios de baja comunicacion o escasez extrema quedan como casos limite.

![Theory reality](../results/figures_pdf/sweeps/theory_reality_r2_by_regime.pdf)

## 5.4 Diagramas de arquitectura

Los diagramas no anaden datos; ayudan a que el lector entienda la arquitectura que produce los resultados. Deben usarse antes de la discusion para conectar el mecanismo matematico con el pipeline implementado.

![Stack](../results/figures_pdf/diagrams/stack_7_layers.pdf)

![Single clock](../results/figures_pdf/diagrams/single_clock.pdf)

![Market](../results/figures_pdf/diagrams/market_supply_demand.pdf)

## Limitaciones de esta consolidacion

Los CSV v2.7 guardan ocupaciones, entregas, deficit y logs de cambio, pero no guardan coordenadas completas de robots y cargas. Por eso las figuras de estado final y las animaciones son diagnosticos de ocupacion/coalicion, no reconstrucciones geometricas del mundo. La sensibilidad H3-B frente a deadlines y tasas de llegada tampoco existe como artefacto previo; por la regla de no correr experimentos nuevos, queda registrada como pendiente de Fase 2.

## Claim-evidence map

- Claim: Smith reproduce la prediccion water-filling en el motor minimo. Evidence: `exp_results/conclusiones.md`, H1 slope 1.000000 y R2 1.000000. Status: supported.
- Claim: El clearing entero reduce desperdicio bajo escasez. Evidence: `exp_results/conclusiones.md`, H2 reduccion -32.0%. Status: supported.
- Claim: El precio es un mecanismo temporal, no estatico. Evidence: H3-A negativo estatico e H3-B delta positivo en escasez. Status: supported.
- Claim: La comunicacion limitada marca una frontera operacional. Evidence: comm sweep y comparacion R12/R3. Status: supported.
- Claim: Hay sensibilidad H3-B por deadline/tasa. Evidence: no artifact yet. Status: needs evidence.

## Self-review checklist

- Clarity: cada subseccion abre con una afirmacion unica.
- Flow: el texto avanza de mecanismos aislados a escenarios y luego a barridos.
- Terminologia: se usa Smith, clearing entero, precio temporal y teoria-realidad de forma estable.
- Unsupported claims: la sensibilidad H3-B queda explicitamente marcada como pendiente.
- Missing evidence: faltan coordenadas geometricas para animaciones espaciales reales y el sweep H3-B de Fase 2.
