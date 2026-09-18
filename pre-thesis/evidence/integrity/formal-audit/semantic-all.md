# Auditoría semántica exhaustiva de resultados formales

Cobertura: 166/166 resultados; completa: `true`.

## Veredictos normalizados

- `CONJECTURE`: 2
- `DUPLICATE`: 16
- `FAIL`: 43
- `LIMITED`: 87
- `PASS`: 18

## Decisiones de incorporación

- `eligible-for-manual-crosswalk-not-auto-promoted`: 3
- `monograph-candidate-with-explicit-limitation`: 89
- `proof-pass-but-claim-or-independent-evidence-unmapped`: 15
- `reject-as-formal-support`: 43
- `retain-canonical-result-only`: 16

No se produjo ninguna promoción automática. `PASS` solo cierra la revisión del enunciado y su prueba en la fuente auditada; aún exige correspondencia exacta con un claim, evidencia independiente cuando proceda y revisión de la fuente activa. `LIMITED` y `CONJECTURE` solo pueden conservarse en la monografía con su frontera explícita. `FAIL` no respalda conclusiones y `DUPLICATE` remite al resultado canónico.

La taxonomía histórica de `semantic-a.csv` se conserva en `source_verdict`; el agregado normaliza `CANDIDATE` a `LIMITED`, y `REJECT`/`NOT_FORMAL` a `FAIL`. Esta normalización no reescribe la auditoría original.
