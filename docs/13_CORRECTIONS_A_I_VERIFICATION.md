# Verificación de correcciones A--I

Fecha de cierre técnico: 2026-07-17.

## Alcance aplicado

- A: correcciones puntuales de Resumen/Abstract, reproducibilidad y vídeos SP2.
- B: definiciones y justificaciones matemáticas faltantes.
- C: reconciliación de conteos SP4/SP8, métricas Cargo y nomenclatura.
- D: punto decimal, operadores de optimización y terminología.
- E: sustituciones retóricas cerradas.
- F: síntesis de distribución, reproducibilidad, disponibilidad y trabajo futuro.
- G: regeneración vectorial de la figura comparativa SP3.
- H: corrección bibliográfica de Holm y auditoría mecánica de DOI.
- I: pruebas, compilación limpia, greps y revisión visual.

## Evidencia de verificación

- Suite: `python -m pytest -q` -> 74 pruebas superadas.
- Figura SP3: `tests/test_sp3_evidence.py` -> 1 prueba superada; el PDF vectorial fue renderizado aislado y dentro de la memoria.
- DOI: 86 identificadores consultados mediante peticiones HEAD a `https://doi.org/<doi>`; todos devolvieron HTTP 302. Kerby (`10.2466/11.IT.3.1`) quedó incluido.
- Holm (1979): la salida Biber contiene `https://www.jstor.org/stable/4615733` y no contiene `10.2307/4615733` como DOI.
- Compilación: se apartó el directorio de auxiliares previo y `thesis/build.ps1` reconstruyó el documento desde un directorio `build` nuevo.
- PDF final verificado: A4, 139 páginas. Se revisaron visualmente Resumen, contenido, índices de figuras y tablas, figura SP3 y apertura de conclusiones.
- Referencias: no hay avisos de referencias o citas indefinidas ni etiquetas duplicadas.
- Maquetación: no hay cajas desbordadas. Permanecen avisos preexistentes de sustitución de fuentes, cajas subllenas y el carácter de control U+0016 asociado al encabezado.

## Greps de cierre

Resultado cero para:

- `debe ser debe`
- `en esta versión`
- `Esta distinción es sustantiva`
- `minimize`
- `IC del 95 :`
- patrón dígito-coma-dígito en los `.tex` de `thesis/sections`

El Resumen contiene exactamente una vez `juego de reparación restauró` y el Abstract exactamente una vez `repair game restored`. Ambos conservan los valores 0.333, 359/360, 0.996, 0.989, 90/90, 328, 0.054 y 261.3.

## Limitaciones y acción humana

`latexmk` no pudo arrancar porque la instalación MiKTeX no dispone del intérprete Perl. La compilación limpia se realizó con la secuencia LuaLaTeX--Biber--LuaLaTeX--LuaLaTeX del script oficial.

El autor debe crear la etiqueta de release y, si procede, el depósito Zenodo; después debe sustituir `<TAG>` y añadir el DOI en el anexo de reproducibilidad. La revisión humana del diff completo, solicitada por el checklist, permanece como acción del autor antes del depósito final.
