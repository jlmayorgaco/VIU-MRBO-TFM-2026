# Integración editorial: gossip delta epistemológico en `pre-thesis` v2

**Estado:** completado (2026-09-18)

## Objetivo

Incorporar la propuesta de *adaptive epistemic delta-gossip* asociada al
MegaJuego en tres niveles editoriales, sin promover a resultado los valores
numéricos del texto aportado mientras falten configuración versionada, datos
brutos, análisis procesado y manifiesto.

## Distribución acordada por evidencia

| Destino | Contenido | Estado epistemológico |
|---|---|---|
| Cuerpo de `main-v2` | Arquitectura mínima: belief físico/estratégico y digest de versiones; transmisión por diferencias; relación con la admisión de continuaciones. | Propuesta de diseño, no resultado validado. |
| Anexo VIU | Definiciones de proveniencia, versión, edad, cobertura y criterio de `COMMIT`; riesgos de información correlacionada, pérdida y retardo; coste por actualización. | Formulación candidata con supuestos explícitos. |
| Material suplementario | Especificación de paquete, reglas de actualización, protocolo A/B pareado, métricas y criterios para publicar resultados. | Diseño experimental pendiente; los números pegados son objetivos de reproducción, no evidencia. |

## Evidencia de partida

- El bundle reproducible presente en
  `pre-thesis/resources/MROB_MegaGame_E2E_bundle/` corresponde a 15 AMR y no
  contiene el A/B de 18 AMR, las trazas `adaptive_recruitment_trace.csv`, la
  configuración o el manifiesto mencionados en el texto aportado.
- Por tanto, no se incorporarán a la memoria las cifras `31.37 s`, `0.8 s`,
  `540` tramas, `21.9 kB` ni comparaciones con DNMPC/CBBA como resultados.

## Cambios previstos

1. Añadir en el bloque del MegaJuego una descripción breve y marcada como
   extensión propuesta, con referencia al anexo.
2. Añadir en el anexo una formulación compacta que no declare garantías de
   convergencia, reducción de mensajes ni fusión estadística sin validación.
3. Crear una sección suplementaria con interfaz de mensajes, protocolo de
   campañas pareadas y requisitos de reproducibilidad.
4. Registrar los símbolos nuevos en `docs/05_NOTATION.md` y en la
   nomenclatura v2.
5. Compilar `main-v2` y el suplementario; ejecutar las auditorías pre-tesis
   pertinentes y revisar el PDF renderizado.

## Riesgos y límites

- Un vector de versiones reduce retransmisiones redundantes solo bajo el
  modelo de red y de expiración especificado; no acredita escalabilidad
  asintótica ni reducción empírica de bytes.
- La cobertura declarada no equivale a conocimiento común bajo pérdida,
  retardo, partición o fallos de proceso.
- Las estimaciones con procedencia común no deben fusionarse como mediciones
  independientes. La intersección de covarianzas se conserva como alternativa
  candidata, no como componente ejecutado.

## Criterios de cierre

- [x] El cuerpo, anexo y suplemento distinguen propuesta, evidencia presente
      y campaña pendiente.
- [x] No se insertan resultados manuales ni citas no verificadas.
- [x] La notación queda sincronizada.
- [x] `main-v2` y una compilación aislada y limpia del suplementario terminan
      sin errores fatales ni referencias indefinidas atribuibles a esta adición.
- [x] Los comprobadores de fuente pre-tesis relevantes pasan (17 pruebas).

## Cierre y limitación abierta

La comprobación del reparto de páginas de la versión v2 conserva 68 páginas
de cuerpo, pero informa 50 páginas de anexos y un 42.6\% de resultados: ambos
incumplimientos ya pertenecen a la composición heredada y no se resuelven
mediante esta integración. La campaña A/B queda explícitamente pendiente de
datos y configuración reproducibles.
