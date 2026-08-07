# Auditoría de voz de SP1.N1

## 1. Patrones encontrados

La revisión se hizo sobre las diez páginas del extracto, con perfil de manuscrito
técnico en español. No se buscaron palabras aisladas: se revisó qué sujeto, acción
y dato contenía cada oración.

- **Personificación del método:** «El auditor certificó una alternativa válida»
  atribuía una acción humana a HiGHS y ocultaba el recuento concreto.
- **Cierres de plantilla:** «E1 responde, por tanto» y «H-N1.X queda sustentada»
  anunciaban la conclusión en vez de formularla.
- **Sustantivos abstractos como sujeto:** «El resultado confirmatorio es parcial»
  retrasaba los cinco resultados que el lector necesitaba ver.
- **Figuras con verbos ceremoniales:** «la Figura sigue», «recorre», «comprueba»
  o «mantiene visibles» sustituían una instrucción de lectura concreta.
- **Contrastes retóricos:** «La reserva, no una nueva propiedad del algoritmo»
  tenía la estructura automática «no X, sino Y».
- **Ritmo uniforme:** varios párrafos cerraban con la misma secuencia de
  resultado, transición y limitación.

## 2. Versión reescrita

La versión completa está en `thesis/sp1_levels_23p/main.tex` y en el PDF generado
`output/pdf/sp1_n1_10p/SP1_N1_10P.pdf`. Estos cambios resumen el criterio aplicado:

| Antes | Después |
|---|---|
| El auditor certificó una alternativa válida en 897/900 falsos factibles. | De los 900 falsos factibles, HiGHS certificó 897; en los otros 3 solo obtuvo un incumbente. |
| H-N1.X queda sustentada en los perfiles ensayados. | En los perfiles probados, la tasa aumentó como predice H-N1.X. |
| El resultado confirmatorio es parcial. | El criterio se cumplió en Aleatorio, Agrupado y Pasillo; Separado y Anillo quedaron por debajo. |
| E1 responde, por tanto, que el Húngaro compensa. | El Húngaro mejora cuando varios puestos disputan los mismos robots. |
| La reserva, no una nueva propiedad del algoritmo, explica la recuperación. | La recuperación observada proviene de los robots de reserva. |
| E3 no acredita resiliencia operacional. | No medimos detección, mensajes, movimiento ni recuperación distribuida; estos resultados no bastan para afirmar resiliencia operacional. |

## 3. Qué cambió

La prosa nombra ahora el método ejecutado, el número de casos y el resultado antes
de interpretar la hipótesis. Se usa primera persona plural solo para decisiones
del experimento, por ejemplo «generamos», «medimos» y «no evaluamos». Las figuras
indican qué contiene cada panel. También se reemplazó «auditoría MILP» por
«comprobación MILP» en el gráfico de E4.

No cambiaron semillas, datos, macros numéricas, contrastes, ecuaciones ni límites
de la evidencia.

## 4. Segunda auditoría

La búsqueda final no encontró las frases señaladas ni vocabulario de plantilla de
alta frecuencia. La lectura visual detectó y corrigió dos problemas secundarios:
la tarjeta E4 excedía su caja y la fuente de la Figura 6 compartía línea con el
pie. Ambos quedaron resueltos sin reducir tipografía ni figuras.

- PDF A4 de 10 páginas.
- 32 pruebas dirigidas aprobadas.
- 5 figuras TikZ protegidas verificadas.
- 0 avisos LaTeX de desbordamiento, referencias o etiquetas.
- SHA-256: `50DF6FA5C13408561504D336247AFEF3B51AB6A59E8E1C7A50B1A0BED77636FF`.

El texto aún conserva términos técnicos como LSAP, MILP, bootstrap e incumbente.
No son señales de escritura automática en este contexto: todos cumplen una
función metodológica y se explican al primer uso.
