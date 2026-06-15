# Informe avanzado

Version `doc-04` basada en el mismo formato VIU y el mismo cuerpo fuente de
`docs/doc-02-mid-report`, con el marco teorico profundizado a partir del documento
maestro consolidado del 12 de junio de 2026.

La version incluye un anexo teorico extendido con las ecuaciones de auditoria:
lift de contribucion efectiva, integrabilidad, oferta por tramos, ISS, ORCA
economico, retornabilidad energetica, handover dinamico, Smith anticipatorio
sampled-data, densidad predictiva y claridad geodesica.

Revision del 12/06/2026: se incorporo la poda fina de claims recomendada para
defensa. El marco teorico ahora distingue dominio de logaritmos, escalas de
Hessiana, energia ideal frente a implementacion perturbada, mercado heterogeneo
fluido frente a clearing entero, ISS con presupuesto de errores, ORCA con
factibilidad multiagente, y validacion experimental pendiente. La Seccion 6 se
mantiene como matriz de cierre hasta que existan resultados reales T1--T5.

## Compilacion

Desde esta carpeta:

```powershell
lualatex main.tex
bibtex main
lualatex main.tex
lualatex main.tex
```

El PDF resultante queda en `main.pdf`.
