# Gates administrativos VIU

Fecha de comprobación local: 2026-09-08 (America/Bogota).

Este registro separa los requisitos demostrables con el corpus institucional del repositorio de los estados privados que solo puede confirmar el expediente del estudiante en el Aula VIU. Una fecha publicada no prueba por sí sola que una convocatoria esté habilitada para un expediente concreto.

## Calendario institucional

La guía docente `resources/P11_02_F02a Guia Docente_12MROB_V02.pdf`, SHA-256 `09b625928b1ead21e9bb4246419e8654f2ddbba7bd08e676b00674797e585cba`, fija para la tercera convocatoria:

| Hito | Fecha | Evidencia local | Estado |
|---|---|---|---|
| Predepósito | 2026-11-01 | página física 6, Evidencia 5 | VERIFICADO EN GUÍA |
| Depósito | 2026-11-10 | página física 7, Evidencia 6 | VERIFICADO EN GUÍA |
| Defensa | 2026-11-23 a 2026-11-27 | páginas físicas 5 y 7 | VERIFICADO EN GUÍA |

La misma guía indica que los horarios se expresan en la hora oficial de Madrid. La disponibilidad efectiva de esa convocatoria para el expediente del autor sigue `PENDIENTE_AULA`.

Comprobación de sesión: el 2026-09-09 a las 21:25 UTC se abrió `oncampus.universidadviu.com` en el navegador integrado. El sitio redirigió a `/acceder` y mostró únicamente los enlaces «Login con Microsoft 365» y «Login»; por tanto, no había una sesión autenticada reutilizable. Las comprobaciones anteriores, a las 16:21 UTC en el perfil existente de Microsoft Edge y a las 03:46 UTC en el navegador integrado, produjeron el mismo resultado. No se introdujeron credenciales, no se abrió el flujo SAML y no se automatizó la autenticación.

## Formato y plantilla

`resources/Instrucciones_TFM_MU Robotica F.pdf`, SHA-256 `467ee0ff1ce74e826a6ad82050c2fd13970c35e10aef57eabbd2dedcb080c4de`, establece en sus páginas físicas 3 y 4:

- uso obligatorio de la plantilla oficial y prohibición de modificar sus estilos predefinidos;
- borradores intermedios en Word;
- versión definitiva depositada en PDF;
- cuerpo de 50 a 80 páginas, excluidos portada, resúmenes, índices y anexos;
- anexos de hasta 20 páginas.

El documento no prescribe la herramienta con la que se genera el PDF final ni menciona LaTeX. Por tanto, la conformidad técnica de la réplica puede verificarse, pero su aceptación administrativa no debe inferirse del silencio de la norma. `resources/Plantilla memoria TFM_ MROB.docx`, SHA-256 `6b213806a83f7baa1e41eb420cb12c423d4c40f90771b5e21b621148bbd33eaa`, es la autoridad visual usada por la instantánea.

El build `-Verify` aplica además una lectura conservadora de la extensión: comprueba 69 páginas de cuerpo y 56,52 % de Resultados sin referencias, y también 77 páginas de cuerpo y 50,65 % de Resultados al contarlas. Ambas interpretaciones cumplen el intervalo y el mínimo del 50 %.

## Acciones externas pendientes

| Gate | Estado | Evidencia que lo cerraría |
|---|---|---|
| Tercera convocatoria habilitada para el autor | PENDIENTE_AULA | captura o confirmación del estado de las tareas Evidencia 5 y 6 en la sesión autenticada |
| Réplica LaTeX aceptada administrativamente | PENDIENTE_DIRECTOR/AULA | mensaje escrito del director o de soporte académico |
| Informe del director, Anexo III | PENDIENTE_EXTERNO | documento firmado incorporado al depósito |
| Solicitud de defensa, Anexo IV | PENDIENTE_EXTERNO | documento firmado incorporado al depósito |
| Copia del expediente académico | PENDIENTE_EXTERNO | archivo admitido por la tarea de depósito |
| Prueba institucional antiplagio | PENDIENTE_EXTERNO | informe Turnitin/iThenticate o resultado de la tarea del Aula |

Ninguno de estos estados se simula ni se marca como aprobado desde el repositorio.
