# Fondo nativo de CoppeliaSim e integración en `thesis/build/main.pdf`

## Propósito y resultado observable

Hacer que la escena AWS Industrial 2 use el degradado gris nativo de la vista 3D
de CoppeliaSim, depurar la captura oblicua para eliminar solapamientos visuales,
regenerar la figura empleada por la memoria y compilar la versión integrada
directamente en `thesis/build/main.pdf`.

## Contexto y archivos canónicos

- `tmp/scripts/coppelia/build_aws_canonical_scene.py` contiene la configuración
  reproducible de renderizado compartida por Industrial 2.
- `tmp/scripts/coppelia/build_aws_industrial_adversarial_scene.py` exporta la
  variante `industrial2`, sus cámaras y el archivo `.ttt`.
- `thesis/sections/mainmatter/06-results-and-analysis/aws-industrial2.tex`
  consume la captura oblicua.
- `thesis/build.ps1` es la ruta canónica de compilación final.

## Alcance y no alcance

Se modifican únicamente el fondo, la captura y el perfil visual no operacional:
se eliminan discos de radio de la vista general, los entramados superiores
decorativos, tuberías decorativas y el tablero no
legible a esta escala. No se alteran trayectorias, huellas operacionales,
colisiones, resultados C15--C19, métricas ni el nivel de evidencia. El cambio no
convierte el replay cinemático en validación física.

## Supuestos y preguntas resueltas

El color se obtendrá de una escena nueva de la misma instalación de
CoppeliaSim, en vez de estimarlo visualmente. Las cámaras de visión conservarán
su resolución, pose y parámetros geométricos.

## Diseño matemático/técnico

Persistir los dos colores RGB del fondo nativo mediante
`sim.arrayparam_background_color1` y `sim.arrayparam_background_color2`, junto
con la iluminación ambiental ya usada. Regenerar la escena con el exportador
existente y comprobar que el cambio no modifica el inventario operacional.

## Plan experimental

No aplica un nuevo experimento científico. Se ejecutarán auditoría de layout,
pruebas de escena y comparación visual antes/después.

## Hitos

- [ ] Obtener los RGB nativos y versionarlos en el generador.
- [x] Auditar uno a uno los solapamientos y definir un perfil de vista general sin ayudas redundantes.
- [x] Regenerar `.ttt` y las capturas Industrial 2 con el perfil depurado.
- [x] Validar escena, captura y pruebas pertinentes para la limpieza visual.
- [x] Compilar y revisar `thesis/build/main.pdf` con la captura depurada.

## Validación

- El fondo de la captura es un degradado gris y no negro/azul.
- La auditoría mantiene cero colisiones de layout y cero elementos sin soporte.
- Las pruebas AWS/CoppeliaSim pasan.
- `thesis/build/main.pdf` incluye la captura nueva y abre correctamente.

## Riesgos y mitigaciones

- Diferencia entre fondo de viewport y fondo de `VisionSensor`: contrastar ambos
  y fijar parámetros de escena, no posprocesar la imagen.
- Escrituras concurrentes del PDF: esperar a que LuaLaTeX quede inactivo y
  validar hash, texto y renderizado de la salida canónica.

## Registro de decisiones

- 2026-07-17: conservar el alcance cinemático; el degradado es presentación.
- 2026-07-17: retirar de la vista general 24 áreas/radios superpuestos, los
  entramados superiores, las tuberías y el tablero; se
  conservan robots, cargas, rutas, estanterías, actores y toda huella operacional.

## Progreso

Limpieza visual completada. La captura final conserva 12 AMR, 4 cargas activas,
8 cargas en cola, rutas, estanterías y actores, y elimina los elementos
decorativos que cruzaban sobre ellos. La auditoría mantiene 0 colisiones de
layout y 0 violaciones de soporte; 15 pruebas pasan. `thesis/build/main.pdf`
compila en 139 páginas y la página PDF 100 (página impresa 87) se revisó a
150 dpi sin recortes, solapamientos ni texto ilegible. El fondo gris nativo
permanece como hito separado pendiente del plan original.
