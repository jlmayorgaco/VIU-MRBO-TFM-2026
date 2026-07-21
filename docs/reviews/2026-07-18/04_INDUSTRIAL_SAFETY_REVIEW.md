# Revisión independiente industrial y de seguridad AMR

**Recomendación:** revisión mayor.

## Fortalezas

- Distingue seguridad muestreada, invariancia continua y validez industrial.
- RAW--SAFE--EXEC y la medición posterior a saturación/integración son decisiones de ingeniería útiles.
- Conserva bloqueos, *timeouts* y el resultado negativo de Industrial 2.
- Reconoce pose exacta, rigidez impuesta, registro global y ausencia de hardware.

## Defectos mayores

1. Tras el acoplamiento, el código reconstruye las poses de los robots desde la carga. No conserva la dinámica no holónoma ni deriva el movimiento desde rueda--suelo.
2. El criterio agregado no comprueba soporte, centro de masa, vuelco, fricción, deslizamiento, conos de contacto ni wrench geométrico.
3. Durante el fallo la carga se congela; el reacoplamiento omite el estado transitorio más peligroso.
4. Cargo audita una envolvente en muestras de 0,1 s y solo una parte de la misión; no usa volumen barrido ni cubre todos los pares de colisión.
5. La red fuerza conectividad, usa pérdidas Bernoulli y resuelve atributos mediante registro global; 90/90 no acredita robustez inalámbrica.
6. 359/360 es una prueba de regresión del pipeline sobre un benchmark estrecho, no una tasa de fiabilidad industrial.
7. Falta una matriz explícita peligro--función--evidencia que separe CBF académico de funciones de seguridad operacional.

Antes de reforzar afirmaciones industriales se necesitarían dinámica multicuerpo/no holónoma, perturbaciones físicas, fallo en curva, auditoría continua de colisiones, red móvil con pérdidas en ráfaga y una campaña industrial con más semillas y cargas.
