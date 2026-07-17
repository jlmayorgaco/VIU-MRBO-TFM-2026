# Comparación de navegación AWS

A* 4-conectado se conserva como baseline. La variante TFM integra un campo continuo con juego Replicator local y filtro CBF, ejecutado digitalmente mediante Euler.

La fracción oblicua mide incrementos muestreados con cambios simultáneos en x e y; distingue la geometría observada, pero no demuestra optimalidad ni suavidad diferencial.

Los controladores usan pasos distintos (0,10 s para A* y 0,05 s para TFM), por lo que la diferencia de throughput corresponde al paquete controlador--muestreo y no es una atribución causal pura al algoritmo.

Ambas campañas registran colisiones sobre muestras; ninguna constituye una garantía de seguridad continua.
