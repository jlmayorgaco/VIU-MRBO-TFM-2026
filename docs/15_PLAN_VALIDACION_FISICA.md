# 15 — Plan de validación física del certificado de wrench

Objetivo: convertir OE2 y H2 de una comprobación contra el propio modelo en una
medición contra física de contacto, y con ello sostener el objetivo general sin
rebajarlo.

Fecha de inicio: 2026-09-02.

## 1. Por qué hace falta

`src/viu_mrob_tfm/sp1_geo/certifier.py` implementa el certificado como un
**mínimos cuadrados acotado cuasi-estático**: dadas las columnas de agarre
$A$ (3×m) y las cotas de fuerza $\bar f$, resuelve

$$\min_{0 \le f \le \bar f} \; \lVert A f - w_{\text{dem}} \rVert_2$$

y acepta la coalición si el residuo normalizado cae bajo el umbral.

Ese modelo **no** representa cuatro cosas que la física sí impone:

1. **Conos de fricción.** $f \ge 0$ es unilateralidad, no fricción. Una columna
   con componente tangencial fuera del cono de Coulomb es infactible aunque el
   LSQ la acepte.
2. **Dinámica.** El wrench demandado se fija a priori; en transporte real
   depende de la aceleración instantánea de la carga.
3. **Restricción no holónoma.** Los Pioneer P3DX son diferenciales: no pueden
   generar una dirección de fuerza arbitraria sin orientarse antes.
4. **Mantenimiento del contacto.** Un contacto unilateral se pierde.

La predicción honesta es que la física **refute o acote** el certificado. Eso es
un resultado, y mejor que confirmarlo.

## 2. El experimento

Matriz de confusión del certificado contra la verdad física.

| | Física: transporta | Física: falla |
|---|---|---|
| **Certificado acepta** | Acierto | **Falso positivo** |
| **Certificado rechaza** | **Falso negativo** | Acierto |

La clave es que **hay que ejecutar también las coaliciones rechazadas.** Sin la
fila inferior no hay tasa de falsos negativos y el certificado no queda medido,
solo ilustrado. Es lo que hoy falta.

H2 dice que la guardia vectorial reduce falsos positivos frente al criterio
escalar. Con esta matriz se contrasta contra verdad física, no contra el modelo.

**Factores del diseño:** masa de la carga; geometría (offsets de contacto);
cardinalidad de la coalición; coeficiente de fricción; perfil de aceleración
demandado. Mundos y semillas pareados entre el criterio escalar y el vectorial,
como el resto del protocolo.

**Éxito físico:** la carga alcanza la pose objetivo dentro de tolerancia, sin
pérdida de contacto sostenida y sin deslizamiento acumulado por encima del
umbral declarado.

**Endpoints:** tasa de falsos positivos, tasa de falsos negativos, residuo
medido frente a residuo predicho, y deslizamiento máximo.

## 3. Estado de la infraestructura

Verificado ejecutando, el 2026-09-02:

| Elemento | Estado |
|---|---|
| CoppeliaSim | **4.10.0** (`intparam_program_version` = 41000) |
| API remota | **ZMQ, puerto 23000**. Cliente `coppeliasim-zmqremoteapi-client` |
| Motores disponibles | Bullet, ODE, Vortex, Newton y **MuJoCo**, los cinco |
| Motor elegido | **MuJoCo**, por fidelidad de contacto |
| Arranque headless | Operativo (`-h`) |
| Paso determinista | `setStepping(True)` + `step()`: un paso exacto por disparo |
| Runner de sesión | `src/viu_mrob_tfm/coppelia/session.py` |
| Humo | `scripts/smoke_coppelia_session.py` — **VEREDICTO: operativo** |

Salida del humo: dos sesiones consecutivas, 20 pasos de 0,005 s cada una,
`saltos_unicos = [0.005]`, simulación parada y confirmada al cerrar.

### 3.1 Dos errores de diagnóstico, anotados para no repetirlos

1. **La versión se leyó del nombre de un fichero de licencia**
   (`coppeliaSimEduV410XX-LicenseAgreement.txt`) y se interpretó «4.1.0». Es
   **4.10.0**. De ahí salió la conclusión falsa de que hacía falta la API
   heredada, y con ella un rodeo completo: vendorizar `sim.py` y
   `remoteApi.dll`, pelear con `rc=3` y con un puerto 19997 que nunca estuvo
   escuchando.
2. **La versión se dio por buena sin comprobar los puertos.** Lo que resolvió
   el diagnóstico fue `Get-NetTCPConnection -State Listen` filtrado por el PID:
   23000 abierto, 19997 no. **Verificar contra el sistema, no contra la
   documentación inferida.**

MuJoCo ya estaba en la instalación original de octubre de 2024
(`mujoco.dll`, `simMujoco-3-2-4.dll`). La descarga de la 4.10.0 en
`Documents\CoppeliaSim\V4_10_0` no era necesaria; se conserva porque no
depende de `Program Files` ni de permisos de administrador. El runner acepta
cualquiera de las dos rutas.

## 4. Qué hay que construir

1. ~~**Runner de sesión**~~ — **HECHO** (2026-09-02):
   `src/viu_mrob_tfm/coppelia/session.py`, humo en verde.
2. **Constructor de escena dinámica** — carga *respondable* con masa e inercia
   reales, N Pioneer P3DX dinámicos, contactos instrumentados con sensores de
   fuerza. La carga solo se mueve por las fuerzas que recibe.
3. **Lazo cerrado** — por paso: leer poses y fuerzas → calcular control en
   Python → aplicar velocidades de rueda. Nada precalculado.
4. **Controlador de pose del cuerpo compuesto** con reparto de wrench entre
   miembros.
5. **Instrumentación** — wrench medido por contacto (`sim.readForceSensor`),
   deslizamiento, pérdida de contacto, error de pose.
6. **Campaña y análisis** — driver, manifiesto con semillas y hashes, y macros
   generadas hacia `generated/*.tex` como el resto del trabajo.

## 5. Lo que esto cierra

- **OE2** deja de ser circular: el certificado se mide contra contacto.
- **H2** pasa a tener verdad física, con falsos positivos y falsos negativos.
- **HP y el objetivo general** pueden sostener «completará el transporte» para
  el dominio efectivamente validado, sin rebajar la afirmación.
- **La escena de CoppeliaSim** deja de ser una animación determinista y pasa a
  ser evidencia. El `evidence_scope` actual del fichero de escena
  («Kinematic scenario illustration only») se sustituye por el alcance real.

## 6. Calendario

No cabe en la 1ª convocatoria (depósito 08/09/2026). La 2ª tiene predepósito el
01/10 y depósito el 13/10, con defensa del 26 al 30/10: 41 días más. Este plan
necesita ese margen.
