# Manifest de reproducibilidad

- HEAD al generar Stage 5: `3a320428b94f33a4ea49114104f6a03a1c3ef67c`
- Tesis canónica modificada: **no**
- Corpus Stage 2 SHA-256: `3211592ffed1b636ba9cc0d94b3618ff067c73f398bfa63e4d6d8a8960d90fc6`
- Matriz Stage 3 SHA-256: `74c93054a8a920d3c209838e5572d04972c4df6ca3086a65c2d647bce8a6e949`
- Resumen Stage 4 SHA-256: `6c0acee89539e966e016928a9fb9a4e198ba3128f2848c6eb00b6783a56ea88a`
- WoS: `present_partial` (`wos_partially_reconciled`)

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
