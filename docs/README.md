# Documentacion

La carpeta `docs/` mantiene la fuente documental vigente del TFM.

- `report/`: memoria canonica en LaTeX, anexos, figuras y PDF generado.

Los borradores historicos y artefactos sustituidos fueron movidos a la cuarentena
externa indicada en `cleanup_manifest.csv`. Para compilar el documento vigente desde la
raiz del repositorio:

```powershell
make report-pdf
```
