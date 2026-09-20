# Control de calidad — revisión visual exacta de seis páginas

## Entregable

- PDF: `output/pdf/MROB_literature_review_6p_exact_visual.pdf`
- Tamaño: carta, 612 × 792 pt.
- Extensión: seis páginas.
- SHA-256: `8f35d955ff5054c655d0e32859aed435bfef8159976998e50592b4fb4d20d9cc`

## Identidad del facsímil

El archivo facilitado por el autor y su copia versionada comparten SHA-256:

`840164c6e6e85be3b265c57dc033fee4f627314bfd13274776ec1fc7e9003028`

Después de insertar vectorialmente el facsímil en el entregable, ambos PDF se
renderizaron con Poppler a 160 dpi. La comparación RGB mediante Pillow produjo:

| Página | Dimensiones | Diferencia |
|---:|:---:|:---:|
| 1 | 1360 × 1760 px | `difference_bbox=None` |
| 2 | 1360 × 1760 px | `difference_bbox=None` |
| 3 | 1360 × 1760 px | `difference_bbox=None` |
| 4 | 1360 × 1760 px | `difference_bbox=None` |

Por tanto, formas, tamaños, colores, ejes, rótulos y figuras de las páginas
1--4 son visualmente idénticos al PDF de referencia; no fueron redibujados ni
rasterizados.

## Integración del corpus ampliado

- Las páginas 5--6 se compilaron dos veces con XeLaTeX y se redactaron como
  continuidad del capítulo de estado del arte.
- El log no contiene `Overfull`, `Undefined` ni `Missing character`.
- Se inspeccionaron visualmente las seis páginas renderizadas.
- El núcleo curado (`n=59`, 54 fechados) sustenta la comparación cercana; el
  corpus de mapeo (`n=244`) sustenta tendencias e intersecciones.
- Se retiraron los rótulos `Cómo leer esta edición`, `Actualización V3` y
  `Referencias suplementarias V3`.
- La Figura 7 se redibujó en TikZ como contrato de interfaces SP1--SP3. Incluye
  compuertas de validación, estados `CLOSED`, `GUARDED` y `EXECUTED`, y la
  realimentación por congestión, fallo o cambio de tarea.
- La auditoría editorial no encontró fórmulas meta, transiciones mecánicas,
  énfasis vacío ni los patrones léxicos predefinidos en las páginas reescritas.

## Pruebas

`python -m pytest -q academic-review/tests`

Resultado: `63 passed, 1 warning`. La advertencia corresponde a versiones de
dependencias de `requests` y no afecta la compilación, los datos ni el PDF.

## Reproducción

Ejecutar desde la raíz del repositorio:

```powershell
python academic-review/scripts/build_exact_visual_review.py
```

El script valida el hash y las cuatro páginas del facsímil, recompila las dos
páginas V3, ensambla el PDF de seis páginas y actualiza `build_manifest.json`.
