# Organización del repositorio

Estado tras la limpieza del **2026-09-02** (rama `sp1-final-refactor`).
Nada se ha borrado. Todo lo que salió de la raíz está en `legacy/`.

## 1. Qué hay en la raíz, y por qué

| Carpeta | Función | ¿Vivo? |
|---|---|---|
| `Subdocuments/` | SP1 y SP2: el texto científico en desarrollo | Sí, es donde se trabaja |
| `thesis/` | `main.tex` y el ensamblado de la memoria VIU | Sí |
| `docs/` | Contrato del TFM: charter, requisitos, matriz, protocolo, claims, notación, plantilla | Sí, precedencia sobre el código (`AGENTS.md` §2) |
| `configs/` | Configuración del proyecto | Sí |
| `coppeliasim/` | Escenas y modelos del simulador | Sí |
| `src/` | Paquete Python `viu_mrob_tfm` | Sí, lo usa `make` |
| `scripts/` | Scripts de campaña y de figuras; `scripts/results/sp1_levels/` es su salida | Sí, lo invoca `thesis/build.ps1` |
| `experiments/` | Configuraciones YAML de las campañas | Sí |
| `tests/` | Pruebas del paquete | Sí |
| `references/` | `LITERATURE_LEDGER.md` | Sí, se sigue editando |
| `resources/` | `VIU_MROB_TFM_TEMPLATE.docx`, la plantilla oficial | Sí: `docs/06` la declara **autoridad visual**. Se devolvió desde `legacy/` |
| `.claude/skills/` | Nueve habilidades del proyecto (voz, rigor, control, juegos, citas, build) | Sí |
| `AGENTS.md` `README.md` `LICENSE` `Makefile` `pyproject.toml` `requirements*` | Infraestructura del repositorio | Sí |

`src/`, `scripts/`, `experiments/`, `tests/` y `references/` **no** estaban en la
lista original de «dejar fuera», pero se han quedado: el build y la
reproducibilidad dependen de ellos por ruta (`Makefile`, `pyproject.toml`,
`thesis/build.ps1`). Moverlos a `legacy/` habría roto `make` y la compilación de
la tesis.

## 2. Qué se movió a `legacy/`

Once carpetas y `AUDIT.md`. El inventario, con recuentos y con qué sigue
dependiendo de ello, está en `legacy/README.md`.

Lo grande: `results/` (31 472 ficheros) y `tmp/` (31 823 ficheros).

## 3. Qué se tocó en el código

Tres constantes de ruta, porque leían datos de campaña que ahora están
archivados. Verificado: los dos pasos previos de `thesis/build.ps1` siguen
pasando (5 figuras protegidas, 50 macros regeneradas).

| Fichero | Cambio |
|---|---|
| `scripts/export_aws_industrial2_latex.py` | `results/` → `legacy/results/` |
| `scripts/generate_sp2_master_figures.py` | `results/` → `legacy/results/` |
| `scripts/sp1_levels_common.py` | `GEO_SOURCE_ROOT` → `legacy/results/sp1_geo/` |

Y **27 rutas `\input` / `\includegraphics`** en trece ficheros `.tex` de
`thesis/sections/`, que apuntaban a `../results/`. Esto es lo que impedía
compilar: `\input{../results/sp0/SP0_THEORY_v1/tables/sp0_method_summary.tex}`
paraba LuaLaTeX en seco. Se reescribieron a `../legacy/results/`. Las rutas
`../scripts/results/` no se tocaron: esa carpeta sigue en la raíz.

## 3 bis. Limpieza de `thesis/` (2026-09-02)

`thesis/` contenía 27 entradas; ahora tiene 11, todas fuente o configuración:

```
main.tex  references.bib  viu-mrob-thesis.sty  build.ps1  README.md
sections/  figures/  images/  config/  generated/  build/
```

Lo que salió está en `legacy/thesis-artifacts/` y `legacy/thesis-drafts/`
(inventario en `legacy/README.md`). Nada borrado.

**Estado de compilación, verificado ejecutando el build, no leyéndolo:**

| | Antes | Después |
|---|---|---|
| `thesis/build.ps1` | **Fallo**, `Emergency stop` en `sp0.tex` línea 241 | **Exit 0** |
| PDF | No se generaba | 120 páginas, 2,08 MB |
| Referencias indefinidas | — | 0 |
| `Overfull` | — | 0 |

La comprobación se hizo con un `build/` recién creado desde cero, no
incremental.

**Pendiente menor:** el log deja
`LaTeX Font Warning: Font shape 'OT1/Arial(0)/m/n' undefined`. LaTeX sustituye
la fuente. Como la VIU exige Arial 12, conviene revisarlo contra
`docs/06_VIU_TEMPLATE_FIDELITY.md` antes del depósito.

Los scripts de experimentos de `src/` siguen escribiendo en `results/` de la
raíz. Esa carpeta se recreará vacía en la próxima campaña, que es lo correcto:
lo archivado no se mezcla con lo nuevo.

## 4. Lo que queda por decidir — pasar a limpio

Esto es lo que hay que resolver, en orden. Nada de esto se ha hecho todavía.

### 4.1 Confirmar el movimiento

El árbol tiene ~26 100 renombrados sin confirmar. Hasta que se confirmen, un
`git checkout` accidental puede deshacerlos. **Es lo primero.** Un solo commit,
sólo el movimiento, sin mezclar cambios de contenido.

### 4.2 Decidir qué es basura de verdad

Por orden de rentabilidad:

- **`legacy/tmp/` (31 823 ficheros).** Casi seguro borrable entero. Revisa que no
  haya nada que sólo exista ahí.
- **`legacy/output/` (514).** Salidas regenerables. Comprueba si algún vídeo del
  catálogo no se puede reproducir.
- **`legacy/results/` (31 472).** *No borrar en bloque.* Tres scripts leen de
  aquí, y `thesis/build.ps1` depende de `coppeliasim_validation/`. Lo razonable
  es conservar las campañas citadas en el documento y archivar el resto fuera del
  repositorio.
- **`legacy/_thesis_coppelia_snapshot_20260717/` (189).** ¿Aporta algo que
  `coppeliasim/` no tenga? Si no, fuera.
- **`legacy/artifacts/`, `plans/`, `reports/`.** Historial de proceso. Útil para
  redactar la sección de metodología; inútil después.

### 4.3 Limpiar dentro de lo que se queda

- `Subdocuments/SP1/sp1.tex.bak_*` — trece backups manuales. El historial de git
  ya los cubre.
- `thesis/build-corrupt-*`, `thesis/$outDir` — residuos de compilaciones fallidas.
- Los `.log`, `.aux`, `.bcf`, `.blg` sueltos en `Subdocuments/SP1/`.

Ninguno se ha tocado: están dentro de carpetas que dijiste dejar fuera.

### 4.4 Preguntas abiertas

1. ¿`references/` es material vivo o debería fusionarse en `docs/`?
2. ¿`configs/` (8 ficheros) y `experiments/configs/` deberían ser una sola cosa?
3. ¿SP3 existe? `docs/02_RESEARCH_MATRIX.md` descompone SP1–SP3 y sólo hay
   `Subdocuments/SP1` y `SP2`.
4. ¿El repositorio debe seguir cargando 1,5 GB de resultados, o van a un
   almacenamiento externo con un manifiesto de hashes en el repositorio?

## 5. Riesgo abierto

**GitHub Desktop estaba abierto durante la reorganización** y hay un proceso que
escribe en `~/.claude/skills/` fuera de esta sesión. Antes de confirmar, cierra
GitHub Desktop: un commit desde ahí a mitad de camino dejaría el árbol partido.

Se retiró un `.git/index.lock` de cero bytes con fecha 2026-08-20 — un git que
murió hace trece días y bloqueaba cualquier operación.
