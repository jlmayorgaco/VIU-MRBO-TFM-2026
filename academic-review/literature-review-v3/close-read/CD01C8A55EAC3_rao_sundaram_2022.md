# Ficha de evidencia — CD01C8A55EAC3

- **Estado:** `lectura_cercana_verificada`.
- **Versión:** preprint arXiv:2201.13033v1.
- **Referencia:** Rao, N., & Sundaram, S. (2022). *Integrated decision control
  approach for cooperative safety-critical payload transport in a cluttered
  environment* [Preprint]. arXiv.
  https://doi.org/10.48550/arXiv.2201.13033
- **Localizadores revisados:** resumen y modelo, pp. 1–2; evaluación y
  conclusión, pp. 9–11.
- **Papel en la revisión:** baseline de control centralizado MPC–CBF para SP2.

El trabajo modela una carga rígida suspendida de varios UAV mediante enlaces
rígidos y juntas esféricas. Integra el seguimiento proporcionado por un MPC
centralizado con restricciones de seguridad obtenidas mediante funciones de
barrera exponenciales. La frontera de seguridad es la envolvente convexa del
sistema UAV–carga. Se presentan simulación numérica y Gazebo con cuatro UAV; el
control corre a 20 Hz y se estudian variaciones de masa de ±10 %, ruido de
estado y margen de seguridad. En el ensayo de ruido, el controlador de evitación
se vuelve inestable más allá de la desviación indicada por los autores
(p. 10), un resultado negativo útil para delimitar el dominio operativo.

**Uso permitido.** Aporta un comparador central para seguimiento, restricción
de oscilación y evitación de obstáculos del conjunto completo, además de una
ablación explícita de incertidumbres.

**Límites.** No hay hardware ni formación de coalición. La trayectoria global
se precalcula y la coordinación es centralizada; el artículo no demuestra que
la factibilidad de la envolvente convexa se mantenga ante pérdida de
comunicación, fallo de vehículo o reconfiguración de la coalición. Es evidencia
preprint y sus resultados permanecen ligados a los modelos simulados.
