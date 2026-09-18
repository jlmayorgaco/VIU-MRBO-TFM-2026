# Reproducibilidad binaria del build dual

Fecha: 2026-09-09.

El script `pre-thesis/build.ps1` fija `SOURCE_DATE_EPOCH` y `FORCE_SOURCE_DATE` a partir de `pre-thesis/config/build-epoch.txt`. También inyecta desde un wrapper efímero un `/ID` PDF lógico y estable, distinto para cada documento. Se ejecutó una compilación completa en el repositorio y otra desde una copia aislada con exactamente los 291 insumos sellados más `release-manifest.json`, sin `docs/`, `material/`, `paper/`, `thesis/`, `src/`, `tests/`, `experiments/`, `results/` ni `legacy/`.

| Objetivo | SHA-256 en build 1 | SHA-256 en build 2 | Resultado |
|---|---|---|---|
| Memoria VIU | `07b32806a6f7a0ede9f93fb80ba7e68bb106dae0389e6d10b591ab0ea7c385c8` | `07b32806a6f7a0ede9f93fb80ba7e68bb106dae0389e6d10b591ab0ea7c385c8` | Idéntico entre rutas |
| Monografía | `d22f011514079e7573dded2f8e19dd4710a1a01239d5450b76eb160738e2730f` | `d22f011514079e7573dded2f8e19dd4710a1a01239d5450b76eb160738e2730f` | Idéntico entre rutas |

Ambas verificaciones devolvieron `status: passed`. La memoria conservó 97 páginas y la monografía 110; los dos PDF son A4 y versión 1.5. Antes de fijar el `/ID`, cambiar la ruta alteraba solo ese campo del trailer: al normalizarlo, los binarios eran iguales y el texto extraído coincidía en 207/207 páginas. El resultado actual demuestra reproducibilidad byte a byte entre rutas en el entorno declarado; no implica por sí solo identidad entre distribuciones TeX distintas. Un clon solo podrá reproducirlo cuando el nuevo árbol quede versionado.

El verificador de la memoria aplica dos interpretaciones simultáneas del cuerpo: 69 páginas sin referencias, con 39/69 = 56,52 % de Resultados, y 77 páginas al incluir las 8 de referencias, con 39/77 = 50,65 %. Ambas cumplen el intervalo de 50--80 páginas y el mínimo del 50 %.
