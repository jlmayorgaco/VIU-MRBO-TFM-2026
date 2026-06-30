# Reporte V7 modular

Este directorio es la fuente canonica del reporte final organizado por fases M0--M5.

La version larga `doc-06` fue usada como insumo y movida a la cuarentena externa
registrada en `cleanup_manifest.csv`. El cuerpo de este reporte esta podado para quedar
defendible: Smith-QR, campo unico, formacion rigida, juego vectorial wrench,
validacion compacta y anexos matematico, reproducible e inferencial.

La suite generada en `sections/generated-validation-suite-v1.tex` se incorpora como
Anexo C y corresponde al snapshot `39/39` gates de `results/validation_suite_v1`.

Compilacion desde la raiz:

```powershell
make report-pdf
```
