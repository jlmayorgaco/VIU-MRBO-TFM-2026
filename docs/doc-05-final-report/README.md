# Memoria final TFM

Este directorio es la fuente canonica de la version final del TFM. Conserva formato VIU, portada institucional, resumen, tabla de contenido, secciones principales, anexos, bibliografia y PDF generado.

El contenido esta podado para defensa y entrega final: Smith-QR, campo unico, formacion rigida, juego vectorial en espacio wrench, validacion compacta y anexos matematico, reproducible e inferencial.

La suite generada en `sections/generated-validation-suite-v1.tex` se incorpora como Anexo C y corresponde al snapshot `39/39` gates de `results/validation_suite_v1`.

Compilacion desde la raiz:

```powershell
make report-pdf
```

Salida esperada: `docs/doc-05-final-report/main.pdf`.