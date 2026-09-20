# Ficha de evidencia — C8195CBC30FE2

- **Estado:** `lectura_cercana_verificada`.
- **Referencia:** De Simone, M., Costanzo, M., De Maria, G., & Natale, C.
  (2026). *Cooperative Object Transport and Assembly: Pose/Force Control by
  Visual-Tactile Feedback*. IEEE Robotics and Automation Letters, 11(4),
  4315–4322.
  https://doi.org/10.1109/LRA.2026.3665445
- **Localizadores revisados:** resumen y modelo, p. 1; conclusión y
  limitaciones, p. 8.
- **Papel en la revisión:** evidencia habilitadora de pose/fuerza; no es MRTA.

La arquitectura fusiona observaciones visuales y táctiles mediante IESEKF en
`SE(3)` para estimar pose relativa, pose del objeto y tensión interna. Dos robots
heterogéneos emplean control pose/fuerza y modulación de agarre para transporte,
ensamblaje y maniobras in-hand. La estimación es centralizada; las limitaciones
de rigidez, graspability, planificación de contactos y retardos se reconocen en
la conclusión.

**Uso permitido.** Fundamenta que pose de carga, calibración relativa y tensión
interna son estados relevantes de SP2 y que la heterogeneidad puede explotarse
en la ejecución.

**Límites.** El trabajo usa manipuladores duales, no forma coaliciones de AMR ni
resuelve tráfico. La evidencia no puede trasladarse directamente a robots
móviles sin modelar locomoción, contacto y distribución del estimador.
