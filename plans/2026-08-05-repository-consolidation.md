# Consolidación del repositorio y cierre progresivo de SP1

## Objetivo

Reducir el repositorio a dos productos activos: la memoria VIU completa,
compilada desde `thesis/main.tex`, y el documento editorial SP1, actualmente
cerrado al terminar SP1.N1. El material no activo se clasificará antes de moverlo
a una cuarentena recuperable; ninguna evidencia se eliminará por no aparecer de
forma directa en LaTeX.

## Punto de restauración

- Rama de trabajo: `VIU_TFM_V2`.
- Commit congelado: `1e4a77c5`.
- Etiqueta: `sp1-n1-v2-frozen-2026-08-05`.
- Artefacto congelado: versión editorial de 28 páginas con N1--N4.
- Artefacto activo: `SP1_N1_10P.pdf`, que termina después de E4 en la página 10.

## Inventario inicial

- 26.379 archivos versionados en Git.
- 25.757 eliminaciones pendientes, todas bajo `results/`; los objetos siguen
  recuperables desde Git y la rama `legacy`.
- `tmp/`: aproximadamente 32,2 GiB, de los cuales `tmp/output/` concentra
  aproximadamente 30,5 GiB de productos temporales históricos.
- `results/`: aproximadamente 1,36 GiB de campañas todavía presentes.
- `output/`: aproximadamente 61 MiB de PDFs, renders y manifiestos generados.
- Fuentes principales confirmadas: `thesis/main.tex` y
  `thesis/sp1_levels_23p/main.tex`.

## Clases de conservación

1. **Fuente activa:** LaTeX, estilos, bibliografía, configuración, código y tests
   necesarios para compilar o regenerar los dos documentos.
2. **Evidencia canónica:** RAW, procesados, manifiestos, registros de semillas y
   resultados que sostienen afirmaciones de `docs/04_CLAIMS_EVIDENCE.md`.
3. **Generado reproducible:** PDFs, renders, cachés y figuras regenerables. Solo
   se conserva el entregable final y su manifiesto; las copias se cuarentenan.
4. **Legacy verificable:** campañas supersedidas, prototipos y código histórico
   conservado por la rama `legacy` o por un commit identificado.
5. **Basura segura:** cachés, carpetas vacías, logs de prueba, renders duplicados
   y temporales sin función documental ni probatoria.

## Fases

- [x] Congelar SP1.N1 mediante commit y etiqueta.
- [x] Generar el documento activo de 10 páginas sin dependencias de N2--N4.
- [x] Compilar la memoria completa y extraer su grafo de dependencias.
- [ ] Cruzar código, configuraciones y resultados con la matriz de evidencia.
- [x] Crear `tmp/repo_cleanup_quarantine_20260805/manifest.csv` con ruta, tamaño,
  hash, clase, motivo y punto de restauración.
- [x] Mover el primer lote seguro: `tmp/output/`, compuesto por cachés, renders y
  salidas de prueba no versionadas.
- [ ] Revisar el lote legacy antes de aceptar las eliminaciones de `results/`.
- [ ] Ejecutar pruebas, ambos builds y verificación de TikZ tras cada lote.

## Reglas de seguridad

- Las figuras TikZ protegidas permanecen en la memoria final.
- Un archivo citado por LaTeX, por un manifiesto activo o por la matriz de
  evidencia no se clasifica como huérfano.
- Un resultado supersedido se mueve solo si su fuente de recuperación queda
  registrada.
- La cuarentena se mueve por lotes pequeños y se valida antes del siguiente.
- No se mezcla el commit de congelación N1 con las 25.757 eliminaciones previas.

## Siguiente lote

Auditar el build de `thesis/main.tex` y clasificar `tmp/output/`, los renders de
`output/`, `_thesis_coppelia_snapshot_20260717`, `coppelia_scene_backups/` y
`sp1_a1_results/`. No moverlos hasta confirmar que no son la única copia de una
fuente o evidencia vigente.

## Dependencias mínimas detectadas de la memoria final

La compilación de `thesis/main.tex` no autoriza a restaurar `results/` en bloque.
La primera recuperación se limita a los paquetes que la fuente cita directamente
o que los generadores de evidencia declaran como entrada:

- `results/sp0/SP0_THEORY_v1/`;
- `results/sp1/SP1_QUORUM_v1/`;
- `results/processed/sp3/SP3_WRENCH_EVIDENCE_v1/`;
- `results/sp2/SP2_MC_capacity_comparison/`;
- `results/sp2/SP2_MC_marginal_payoff_ablation/`;
- `results/sp3/SP3_WRENCH_NASH_GAME_v1_1/`;
- `results/sp4/SP4_DOCKING_GAME_CONFIRMATORY_v3/`;
- `results/sp4/SP4_DOCKING_GAME_V4_CONFIRMATORY/`;
- `results/sp5/SP5_PAYLOAD_TRANSPORT_CONFIRMATORY_v2/`.

Los productos procesados de SP2, SP4--SP8 y Cargo deben regenerarse desde las
configuraciones versionadas. Cargo requiere ejecutar antes su campaña `smoke`,
porque el protocolo confirmatorio verifica el hash de ese piloto.

## Validación del lote 1

- La memoria VIU completa recompila en A4 con 120 páginas.
- El comprobador confirma las cinco figuras TikZ protegidas antes y después de
  compilar.
- El documento editorial recompila como `SP1_N1_10P.pdf` con 10 páginas y sin
  contenido de N2 en el PDF.
- Pasan 20 pruebas dirigidas de SP1, Húngaro y figuras protegidas.
- La inspección visual cubrió portada, páginas internas y cierre de ambos PDFs.
- La cuarentena conserva 12.384 archivos y 32.799.298.059 bytes; no se eliminó
  contenido.

La compilación mantiene advertencias tipográficas previas (cajas subllenas,
algunos glifos de control y destinos bibliográficos no referenciados). No
bloquean el PDF, pero deben tratarse como deuda editorial, no confundirse con
dependencias ausentes.
