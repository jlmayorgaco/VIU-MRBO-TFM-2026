# Informe de evidencia E9 — orden mínimo de coordinación

## Pregunta

E9 pregunta cuántos robots conectados deben cambiar a la vez para mejorar el terminal al
que llega Geo-QPG-BR desde el perfil inactivo. El cálculo no parte de una
asignación escogida a mano: vuelve a ejecutar BR y audita ese mismo endpoint.

## Qué se enumeró

Para cada mundo se probaron todas las coaliciones conectadas de dos robots en
las que ambos cambian de acción. Cuando ninguna redujo el criterio
lexicográfico, se hizo lo mismo con tres robots. La primera mejora encontrada
se conserva como testigo auditable. El procedimiento es exacto dentro de esas
dos vecindades; no examina grupos de cuatro o más robots.

## Resultado principal

En los 1.200 mundos congelados de E4, 1.156 terminales (96,3 %; IC de Wilson del
95 %: 95,1--97,3 %) tenían una mejora bilateral. Cuatro (0,3 %; 0,1--0,9 %)
necesitaron primero un grupo de tres. En los 40 restantes (3,3 %; 2,5--4,5 %)
no apareció una mejora conectada hasta orden tres. La mediana del tiempo de
búsqueda fue 9,2 ms en esta implementación y equipo.

La magnitud auditada es el orden conectado $h_{\mathrm c}^\star$, no el orden
irrestricto $h^\star$ de todas las desviaciones posibles. El orden pequeño no
implica un efecto pequeño. Entre los casos clasificados con
orden dos, pasar de BR a 2BR redujo el gap en una mediana de 34,5 puntos
porcentuales. En los cuatro casos de orden tres, el paso de 2BR a C3 lo redujo
en 42,3 puntos. Estas cifras describen las muestras correspondientes; el grupo
de orden tres es demasiado pequeño para una conclusión poblacional precisa.

## Sensibilidad y lectura

El barrido independiente de `N/K` reunió otros 1.200 mundos. La fracción `>3`
fue 11,5 % con dos robots ofertados por carga, 3,25 % con tres y 0,25 % con
cuatro. El patrón es compatible con que una mayor oferta facilite los
intercambios pequeños, pero tres puntos de diseño no establecen monotonía ni
una ley asintótica.

E9 sostiene una conclusión concreta: en este dominio, gran parte de la pérdida
de BR proviene de barreras bilaterales y una búsqueda de pares tiene una
justificación empírica clara. No sostiene que C3 sea globalmente óptimo, que el
resultado se mantenga bajo otra inicialización ni que el protocolo tolere
pérdidas o particiones de red.

## Artefactos

- Configuración: `experiments/configs/sp1_n4_hstar_v4.yaml`.
- Ejecutor: `scripts/sp1_n4_hstar.py`.
- RAW, procesados, figuras y manifiesto: `scripts/results/sp1_levels/n4_v4/`.
- Pruebas: `tests/test_sp1_n4_hstar.py`.
