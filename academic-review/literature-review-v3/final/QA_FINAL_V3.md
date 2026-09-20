# Control de calidad del manuscrito V3

**Fecha:** 2026-09-13  
**Manuscrito auditado:** `REVISION_SISTEMATIZADA_MRTA_COT_AMR_V3.md`  
**SHA-256:** `F95897A2F12D3422630F226E0A5505D156DE4930C147A30E3CCB9A10FE7E6757`

## Resultado

- Extensión: 9.356 palabras, 465 líneas y 22 referencias.
- Corpus analítico: 244 documentos.
- Textos aptos para lectura cercana: 168.
- Fichas con localizadores: 20.
- Registros arXiv en el corpus: 10; cuatro leídos de forma localizada.
- Figuras reproducibles: dos, ambas inspeccionadas y legibles.
- Pruebas de `academic-review/tests`: 63 superadas; una advertencia de
  compatibilidad de `requests`, sin fallos.

## Auditoría bibliográfica

- Diecinueve DOI de editor o revista resolvieron y coincidieron en título/año
  mediante Crossref.
- El DOI arXiv de Rao y Sundaram y el identificador arXiv de Song et al. se
  comprobaron contra arXiv.
- Para Savino et al. y Ferreira et al. se identificó la versión de registro
  posterior al manuscrito arXiv y se cita esa versión.
- Para Ramchurn et al. (2010), `1838186.1838191` es un identificador de registro
  de ACM/DL que distintas bases representan como `10.5555/...` o
  `10.1145/...`, pero no resolvió como DOI en Crossref. El manuscrito evita
  presentarlo como DOI y enlaza el registro DBLP verificado.
- Se corrigieron antes del cierre: candidato/venue/DOI de An et al.; título y
  páginas de Mazdin y Rinner; año y páginas de De Ryck et al.; páginas de Pi,
  Palmer, Varghese y De Simone; e iniciales de Mazdin.

## Consistencia numérica

La prueba `test_v3_final_review_consistency.py` deriva del CSV generado los
conteos principales y confirma que el texto contiene las cifras actuales. El
análisis no usa menciones de referencias como para inferir implementación: las
listas bibliográficas y páginas de paywall se excluyen de la codificación.

## Límites que deben permanecer en cualquier versión abreviada

1. Web of Science está incompleto en 255 registros de F01/F02.
2. La ejecución de la API de arXiv fue parcial; diez preprints ya adquiridos sí
   se conservaron y versionaron.
3. El corpus está enriquecido por relevancia y no estima prevalencia universal.
4. Solo 20 trabajos tienen lectura cercana; los conteos de 244 son de
   título/resumen.
5. No se realizó meta-análisis ni acuerdo interrevisor.
6. El hallazgo de baja integración SP1–SP2–SP3 se limita al corpus adquirido y
   no constituye una prueba de novedad universal.

## Veredicto

**Apto como revisión avanzada y base de capítulo/paper, con limitaciones
declaradas.** Antes de someter a una revista debe definirse el venue, adaptar su
plantilla, completar una revisión humana independiente y, si el editor exige la
etiqueta “systematic review”, completar las exportaciones WoS pendientes y una
segunda ronda de screening.
