# SP2 — ejecución y transporte cooperativo

Este subdocumento desarrolla SP2 en español y con un máximo de 20 páginas. El
modo primario es **Cargo**, con acoplamientos que transmiten
fuerza; el **caging** por contacto unilateral se conserva como extensión y no
comparte sus garantías mecánicas.

## Compilación

Desde PowerShell:

```powershell
./build.ps1
```

El script ejecuta LuaLaTeX y Biber, comprueba que no queden citas ni referencias
cruzadas sin resolver, rechaza cajas desbordadas, impone el máximo de 20 páginas
y genera `sp2.pdf` y `output/pdf/SP2_HONORS_VIU.pdf`. La lista bibliográfica no
se duplica en este extracto: se integra una sola vez en el capítulo 8 de la
memoria VIU a partir de `references.bib`.

## Alcance de la evidencia

- Las cifras N1--N4 proceden de la campaña versionada
  `results/sp2_canonical/SP2_HONORS_v3/`; no se presentan resultados de
  hardware.
- La misión Cargo integrada procede de
  `results/processed/integrated/CARGO_E2E_CONFIRMATORY_v1/`: 360 mundos y
  2.160 ejecuciones auditadas. Se presenta como demostrador híbrido hasta la
  pose de entrega, no como arquitectura distribuida completa ni como prueba de
  liberación física.
- La cadena compacta Pioneer 3-DX, el RBPF de rejilla, el grafo de poses
  relativo, docking y medida de fuerzas constituyen un diseño instrumentable.
  LiDAR, IMU, cámara y transductor se declaran como equipos añadidos; N3 no
  ejecuta esos estimadores ni una integración física.
- Dos esquemas TikZ enlazan el modelo con la plataforma: la Figura 2 muestra
  anclaje, restricción no holónoma y conversión a velocidades de rueda; la
  Figura 5 sitúa sensores, contacto y transformaciones sobre un Pioneer 3-DX.
  El subdocumento contiene doce figuras vectoriales, todas citadas y revisadas
  en su página final.
- La Figura 10 divide la misión nominal y la recuperación tras fallo en dos
  bandas horizontales. La extensión caging queda condensada en la última
  página y conserva un certificado discreto distinto del modo Cargo.
- La campaña dinámica usa una planta plana reducida, contactos fijos,
  integración muestreada y una cota isotrópica de tracción configurada. La
  identificación Euler--Lagrange, la anisotropía rueda--suelo, la calibración de
  fuerza y la validación física siguen pendientes.
- El gobernador distingue `EXECUTE`, `BRAKE`, `HOLD` y
  `UNCONTROLLED_STOP_REQUIRED`; cada candidato se revalida conjuntamente frente
  a barrera, ruedas, soporte, wrench y edad de información.
- La estructura virtual no mejora todos los canales N3. En N4, la guarda mejora
  admisibilidad modelada pero aumenta la incidencia agregada de colisión en
  0,0524 (IC95 % [0,0393; 0,0643]); H6 queda refutada. Ambos resultados
  negativos permanecen explícitos en el texto y en la matriz de evidencia.
