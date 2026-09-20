# Ficha de evidencia — C4281BAF1E1C2

- **Estado:** `lectura_cercana_verificada`.
- **Referencia:** Tejada, J. C., Toro-Ossaba, A., López-Quintero, M. A., et al.
  (2025). *Enhancing Object Manipulation and Transportation in Multi-Robot
  Systems with Soft Gripper Integration and Caging-Based Control*. Journal of
  Intelligent & Robotic Systems, 111, 76.
  https://doi.org/10.1007/s10846-025-02263-y
- **Localizadores revisados:** resumen y arquitectura, p. 1; conclusión y
  limitaciones, p. 14.
- **Papel en la revisión:** evidencia primaria de caging/prehensión blanda en
  SP2.

Dos robots omnidireccionales con grippers Fin-Ray emplean control
leader–follower de distancia y ángulo para preservar el cierre alrededor del
objeto. Los autores realizan experimentos físicos con distintas geometrías y
orientaciones. La conclusión reconoce que aún faltan sensores para controlar la
fuerza de interacción y experimentos con más robots (p. 14).

**Uso permitido.** Muestra cómo la morfología del gripper puede reducir la
exigencia de tamaño de coalición y que el cierre de caging debe formar parte del
estado/control.

**Límites.** No mide reparto de wrench ni fuerza de contacto cerrada en lazo,
utiliza solo dos robots y conserva un líder. No prueba escalabilidad,
sustitución tras fallo ni navegación de múltiples coaliciones.
