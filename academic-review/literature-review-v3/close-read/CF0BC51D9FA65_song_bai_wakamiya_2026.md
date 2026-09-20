# Ficha de evidencia — CF0BC51D9FA65

- **Estado:** `lectura_cercana_verificada`.
- **Versión:** preprint arXiv:2602.19070v2; no se identificó una versión de
  revista en la comprobación realizada.
- **Referencia:** Song, J., Bai, Y., & Wakamiya, N. (2026). *Cooperative
  transportation without prior object knowledge via adaptive self-allocation
  and coordination* [Preprint]. arXiv. https://arxiv.org/abs/2602.19070
- **Localizadores revisados:** resumen, problema y control, pp. 1–3;
  simulaciones y conclusión, pp. 4–5.
- **Papel en la revisión:** evidencia temprana que integra reclutamiento local,
  formación geométrica y transporte de varias cargas.

El método usa agentes con dinámica de integrador de primer orden, alcance de
sensado limitado y comunicación vecinal. Un agente que detecta una carga genera
un campo de atracción mediante una densidad variable; la teselación centroidal
de Voronoi organiza la distribución espacial y el peso del campo aumenta el
número de agentes alrededor de objetos mayores. Una capa con funciones de
barrera de control limita distancias interagente y favorece un cierre simétrico.
La simulación muestra dos cargas circulares de tamaños diferentes atendidas por
coaliciones autoorganizadas.

**Uso permitido.** Es un ejemplo especialmente próximo a la interfaz SP1–SP2:
la selección del tamaño de equipo no se resuelve como una asignación discreta
separada, sino que emerge de percepción local y control espacial.

**Límites.** Es un preprint validado solo por simulación bidimensional. El
modelo no incorpora masa o peso de la carga, fuerzas de contacto, límites
realistas de actuador, AMR no holonómicos, fallo de robots ni tráfico con
pasillos. Los autores reservan el peso realista y los experimentos físicos para
trabajo futuro; por tanto, “estable”, “robusto” y “escalable” son descripciones
de los escenarios, no garantías generales.
