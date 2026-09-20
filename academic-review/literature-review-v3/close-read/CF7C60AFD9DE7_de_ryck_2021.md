# Ficha de evidencia — CF7C60AFD9DE7

- **Estado:** `lectura_cercana_verificada`.
- **Referencia:** De Ryck, M., Pissoort, D., Holvoet, T., & Demeester, E.
  (2022). *Decentral task allocation for industrial AGV-systems with routing
  constraints*. Journal of Manufacturing Systems, 62, 135–144.
  https://doi.org/10.1016/j.jmsy.2021.11.012
- **Localizadores revisados:** resumen y arquitectura, p. 1; estrategia y
  evaluación, pp. 2–13.
- **Papel en la revisión:** puente operativo SP1–SP3.

El método incorpora información de routing en las pujas de una subasta
secuencial de ítem único mediante delegate multi-agent systems. Su objetivo es
anticipar bloqueos y retrasos que una distancia A* sin congestión omitiría. Los
autores distinguen además decisión descentralizada de despliegue físicamente
distribuido: el algoritmo puede ejecutarse en hardware común aunque la decisión
no dependa de un fleet manager único.

**Uso permitido.** Sustenta la necesidad de acoplar coste de ruta y asignación
y de definir con precisión qué significa centralizado, descentralizado y
distribuido.

**Límites.** La validación es simulada y compara con una subasta SSI sin la
restricción de routing. No trata coaliciones que comparten una carga, contacto
físico ni una garantía general contra deadlock.
