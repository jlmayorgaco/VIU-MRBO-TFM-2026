# Manifest de reproducibilidad

- HEAD al generar Stage 5: `f0ea343adef7f13f0e17ace42f65c11e0797623d`
- Tesis canónica modificada: **no**
- Corpus Stage 2 SHA-256: `dee8796d4ae05a83609fd7a369fd3c013f5ea81478c8a43cacb3ca2ed4cde826`
- Matriz Stage 3 SHA-256: `61befd9d886ee189b292f2087bbedfc43ff2906db3aa621053636f1bb8737fa9`
- Resumen Stage 4 SHA-256: `54f8f43c55d017f127f3169f525532a954d7f0367a9baf43f7f6aab0d10c0934`
- WoS: `pending_external_export`

Ejecutar en orden:

```powershell
python academic-review/scripts/stage2_acquire.py --resume
python academic-review/scripts/stage3_code.py
python academic-review/scripts/stage4_synthesize.py
python academic-review/scripts/stage5_finalize.py
python -m pytest academic-review/tests -q
```

Los binarios de texto completo están excluidos de Git por licencias/tamaño;
`logs/stage2_fulltext_acquisition.csv` y los manifests por candidato registran
URL, estado, identidad, tamaño y SHA-256 para regenerarlos legalmente.
