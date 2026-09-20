# resources/ — corpus normativo VIU

Documentación institucional del TFM del Máster Universitario en Robótica y
Automatización de Procesos (12MROB), edición **Octubre 2025–2026**.

Es la **fuente de autoridad**. `docs/01_VIU_REQUIREMENTS.md` es la síntesis
operativa; cuando discrepen, manda lo que hay aquí.

## Normativa

| Documento | Qué gobierna |
|---|---|
| `Instrucciones_TFM_MU Robotica F.pdf` | **El documento clave.** Formato, tipografía, numeración, extensión, estilo de redacción, ecuaciones, figuras, tablas, APA 7, originalidad y estructura capítulo a capítulo |
| `Plantilla memoria TFM_ MROB.docx` | Plantilla oficial obligatoria. Autoridad visual |
| `P11_02_F02a Guia Docente_12MROB_V02.pdf` | Calendario, evidencias, **ponderación 30 % director / 70 % tribunal**, fechas de defensa |
| `Guía asignatura_V01-12MROB-TFM F.pdf` | Guía de la asignatura |
| `Texto Consolidado_Reglamento sobre Trabajo Fin de Título_1 (1).pdf` | Reglamento general de TFT |
| `NormasAPA_VIU_7ed.pdf` | APA 7ª edición, versión VIU |

## Anexos administrativos

| Documento | Cuándo |
|---|---|
| `Anexo 0_Preliminar-Encuesta MROB.docx` | Encuesta de tutorización — límite 31/03/2026 |
| `Anexo 0 A. Temas TFM MROB.pdf` | Catálogo de temas |
| `Anexo I Solicitud TFM -MROB.docx` | Solicitud de tema (objetivo general y resultados esperados) — 30/04/2026 |
| `Anexo II - Compromiso de aceptación de dirección de TFM MROB.doc` | Firmado por los directores — 30/04/2026 |
| `Anexo III_Informe del director de TFT.docx` | Informe del director — va en el **depósito** |
| `Anexo IV_Solicitud para Defensa TFT.docx` | Solicitud de defensa — va en el **depósito** |

## Defensa

| Documento | Contenido |
|---|---|
| `P11_06_F12 Plantilla PPT Defensa_v01.pptx` | Plantilla obligatoria de la presentación |
| `TFM_Tutoría colectiva final MROB 10 2025 26 PDF Fi.pdf` | Predepósito, depósito, Turnitin, pautas de defensa, errores comunes, acto de defensa, evaluación |
| `Tutoría Inicial colectiva TFM MROB PDF.pdf` | Sesión de presentación (04/03/2026) |
| `Tutoría intermedia  TFM MROB Aula A_2025_2026(1).pdf` | Sesión intermedia (17/06/2026) |

Los tres deck de tutoría son **diapositivas rasterizadas**: `pdftotext` solo
extrae los títulos. Para leer su contenido hay que rasterizar
(`pdftoppm -r 110 -png`) y leer las imágenes.

## Duplicados verificados por SHA-256

- `Instrucciones_TFM_MU Robotica F (1).pdf` es **idéntico** a
  `Instrucciones_TFM_MU Robotica F.pdf` (`467ee0ff1ce74e82…`).
- `Plantilla memoria TFM_ MROB.docx` es **idéntico** a
  `VIU_MROB_TFM_TEMPLATE.docx` (`6b213806a83f7baa…`), y ese hash es el que
  `docs/06_VIU_TEMPLATE_FIDELITY.md` declara como referencia auditada. La cadena
  de fidelidad queda cerrada: lo que audita `docs/06` es la plantilla oficial.

Se conservan ambos por si algún proceso los referencia por su nombre original.

## Lo que no está aquí

El **documento final del TFM**. Se genera desde LaTeX
(`powershell -File thesis/build.ps1` → `thesis/build/main.pdf`) y no se guarda
en `resources/`: esta carpeta es normativa de entrada, no entregable de salida.

## Cómo se usa

La habilidad `viu-compliance` lee este corpus. No dupliques sus reglas en otro
sitio: si algo cambia, cambia aquí y la habilidad lo refleja.
