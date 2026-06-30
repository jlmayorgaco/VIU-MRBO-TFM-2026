# Documentacion

La carpeta `docs/` mantiene las entregas documentales vigentes del TFM con numeracion de fase.

- `doc-04-advanced-report/`: informe avanzado con formato VIU, secciones y PDF de la entrega de avance.
- `doc-05-final-report/`: memoria final canonica. Esta es la version que compila `make report-pdf`.
- `doc-06-explanatory-report/`: version explicativa extendida usada como soporte tecnico y trazabilidad, no como entrega final.
- `literature/`: protocolo, criterios y artefactos de revision bibliografica.
- `VIU_GUIDELINES_ALIGNMENT.md`: mapa de secciones de la memoria final contra la estructura esperada de TFM VIU.

Los PDFs institucionales originales de la guia VIU siguen fuera del repositorio en la cuarentena externa indicada en `cleanup_manifest.csv` para evitar peso y duplicados. Para compilar la memoria final desde la raiz del repositorio:

```powershell
make report-pdf
```

Para compilar otra entrega numerada:

```powershell
make report-pdf REPORT_DIR=docs/doc-04-advanced-report
```