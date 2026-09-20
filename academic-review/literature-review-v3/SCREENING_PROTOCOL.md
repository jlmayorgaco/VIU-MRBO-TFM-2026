# Protocolo de cribado V3

**Versión:** V3.0 · **Congelado:** 2026-09-13 · **Unidad de decisión:** una
identidad bibliográfica deduplicada en `data/discovery_registry_v3.csv`.

Este protocolo se aplica a la revisión sistematizada de mapeo y síntesis
crítica. No convierte búsquedas previas en una revisión retrospectivamente
prerregistrada y no permite excluir registros sin código de razón.

## Criterios de inclusión

Un estudio puede entrar a lectura a texto completo si, a partir de título y
resumen, aborda de forma sustantiva al menos una de estas interfaces:

1. **SP1:** formación de coaliciones, asignación de tareas/roles/capacidades o
   decisión distribuida para equipos heterogéneos de robots.
2. **SP2 estratégico o físico:** aproximación, acoplamiento, contacto, reparto
   de fuerza/wrench, control de formación o transporte cooperativo de una carga
   por dos o más robots.
3. **SP3:** planificación, tráfico, prioridades, reservas, congestión o
   coordinación de múltiples robots/coaliciones cuando afecta la operación de
   transporte.
4. **Eje transversal:** comunicación imperfecta, fallo, sustitución,
   heterogeneidad o explicabilidad, siempre que esté conectado con una decisión
   o ejecución multirrobot pertinente.

Se aceptan artículos revisados por pares, capítulos o actas académicas con
método identificable y revisiones de calidad. Los preprints se conservan con
marca explícita y no sustituyen la versión publicada si se identifica una.

## Criterios de exclusión

| Código | Aplicación |
| --- | --- |
| `E1_no_multirobot_relevance` | No intervienen varios robots ni existe una transferencia al problema multirrobot demostrada por el propio estudio. |
| `E2_no_tfm_interface` | El estudio no aporta decisión, control, modelo físico, baseline, métrica o revisión pertinente para SP1, SP2, SP3 o un eje transversal. |
| `E3_nonrobot_generic_domain` | Trata solo agentes abstractos, red/IoT o logística genérica sin una conexión robótica que permita interpretar sus supuestos. |
| `E4_marl_primary_only` | La contribución central es MARL y no ofrece el mecanismo white-box o el baseline contextual requerido; puede permanecer como contexto, no como evidencia del método principal. |
| `E5_inadequate_document` | No hay identidad bibliográfica suficiente, texto atribuible o una fuente académica recuperable para el uso previsto. |
| `E6_duplicate_version` | Es una versión duplicada; se conserva el alias y se retiene la versión de registro o la más completa. |
| `E7_outside_date_scope` | Está fuera de 1940–2026 y no es una referencia fundacional imprescindible documentada como excepción. |

La falta de acceso no es motivo de exclusión temática: se codifica
`requires_fulltext_or_manual_access_check` y no puede respaldar un claim de
método, garantía o resultado.

## Decisiones y códigos de evidencia

En título/resumen se utiliza solo una de estas decisiones:

- `include_fulltext_candidate`: parece pertinente y necesita texto completo.
- `include_context_candidate`: útil para contexto, taxonomía o plataforma;
  aún no es evidencia de desempeño.
- `exclude_title_abstract`: aplica uno o más códigos E1–E7.
- `uncertain_manual_check`: los metadatos no permiten una decisión fiable.

Tras la lectura completa, una fuente incluida se clasifica en `core`,
`baseline`, `enabling`, `context` o `counterevidence`, y debe registrar:
localizador, supuesto, arquitectura/información disponible, modelo de contacto
cuando aplique, garantía, baseline, escenario, métricas, límite y relación con
el TFM.

## Salvaguardas

- Ninguna decisión automática excluye definitivamente un registro; la
  automatización solo ordena candidatos y detecta posibles duplicados.
- Las afirmaciones de estabilidad, convergencia, optimalidad, seguridad,
  robustez y escalabilidad requieren texto localizado y el tipo de evidencia
  correspondiente.
- Una revisión o un resumen sirve para mapa temático; no reemplaza el estudio
  primario para un resultado cuantitativo o una garantía.
- El cribado es de un revisor asistido por herramientas. Se documentarán las
  correcciones de auditoría, no se afirmará acuerdo interrevisor.
