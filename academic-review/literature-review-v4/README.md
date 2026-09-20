# Revisión de literatura V4 - paquete auditado

Esta versión no reescribe retrospectivamente el corte V3. Conserva la revisión
visual de nueve páginas proporcionada por el autor y añade una capa auditable
que separa lo ya derivado del corpus de lo que todavía requiere revisión
humana. El PDF final se genera en `output/pdf/literature-review/`.

## Arquitectura de evidencia

1. **Descubrimiento.** Identidades bibliográficas para cobertura y deduplicación.
   Nunca respalda propiedades técnicas.
2. **Mapeo sistematizado.** Señales reproducibles de título/resumen y metadatos.
   Sirve para tendencias y cobertura del corpus recuperado.
3. **Revisión técnica anidada.** Codificación por campo a partir de texto completo
   y pasajes localizados. Es la única capa que puede alimentar la matriz de
   capacidades o los antecedentes más próximos.
4. **Auditoría adversarial.** Registro explícito de los trabajos que podrían
   refutar cada componente de la contribución; no es un índice de novedad.

Los recuentos y hashes se generan con:

```powershell
python academic-review/scripts/build_v4_literature_audit.py `
  --reference-pdf 'C:\Users\walla\Downloads\MROB_literature_review_reworked (2).pdf'
```

Después se compila el PDF con `academic-review/literature-review-v4/build_v4_review.ps1`.
El generador falla si cambian los denominadores congelados. No se deben editar
manualmente los archivos de `generated/` ni `data/corpus_layers_v4.csv`.

## Estado honesto del corte

- V3 no es una revisión sistemática exhaustiva ni un meta-análisis.
- Web of Science F01/F02 y la cartera arXiv siguen parciales.
- V3 no registró doble cribado independiente ni acuerdo interrevisor.
- La matriz de capacidades histórica no se promociona a evidencia por celda:
  V4 exige pasaje, localizador, regla de decisión y confianza para cada valor.
- Los análisis de sensibilidad y la validación de un gold set quedan
  predefinidos en `data/` pero pendientes de ejecución y reporte.

## Fuentes metodológicas de reporte

El diseño utiliza PRISMA 2020 y PRISMA-S como guías de transparencia de reporte,
no como etiqueta retrospectiva de exhaustividad. Sus metadatos verificables se
conservan en la bibliografía V3: Page et al. (2021),
doi:10.1136/bmj.n71; y Rethlefsen et al. (2021),
doi:10.1186/s13643-020-01542-z.
