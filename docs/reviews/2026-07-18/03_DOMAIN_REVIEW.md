# Informe independiente de dominio MRTA, juegos y transporte cooperativo

**Recomendación:** revisión mayor.

## Resultados que sobreviven

- Teoremas y proposiciones locales dentro de sus supuestos.
- Integrabilidad marginal de SP2 para el asignador ensayado.
- Reducción de falsos positivos de la guardia planar de SP3.
- Estabilidad local de SP4 bajo contacto fijo y wrench exacto.
- Caracterización de recuperación de SP6.
- Exclusión lógica de SP7, límite de observabilidad de SP8 y resultados negativos H3/H5b.
- Cargo completó 359/360 misiones en su planta planar reducida y compuso varias funciones en un simulador.

## Defectos mayores

1. Cargo sustituye los mecanismos de SP2, SP3 y SP6 por ranking, criterio agregado y reparación voraz.
2. El tratamiento vecinal es, con mayor precisión, descubrimiento parcial de identificadores por *gossip* seguido de selección por líder con registro global.
3. El denominado certificado mecánico integrado no es un certificado de wrench: solo agrega cardinalidad, carga útil y fuerza.
4. La ablación conjunta no atribuye efecto a la guardia mecánica.
5. La recuperación mueve un sustituto a un contacto prefijado y no valida el juego, el reacoplamiento físico ni la recertificación geométrica.
6. Los SP constituyen juegos y plantas distintos; no hay un único juego incremental SP0--SP8.
7. Los proxies no permiten sostener competitividad frente a CBBA/ACBBA, ALLIANCE, CBS/ECBS u ORCA completos.
8. La validación física se limita a un cuerpo planar rígido impuesto.

La novedad defendible es una **arquitectura de contratos y fronteras entre capas, acompañada de juegos locales**, no un juego distribuido único validado extremo a extremo.
