# Prompt maestro — Revisión académica integral del TFM

Actúa como un comité académico independiente que evalúa un Trabajo Fin de Máster en robótica, control no lineal, sistemas multiagente, optimización y transporte cooperativo. No limites la revisión a SP0, causalidad o estadística. Revisa el manuscrito completo y su correspondencia con teoría, implementación y evidencia.

## Material que debes leer

Documento principal:

- `docs/doc-05-final-report/main.pdf`
- `docs/reviews/CURRENT_STATUS_FOR_GPT_2026-07-11.md`

Si tienes acceso al repositorio, contrasta además:

- `docs/doc-05-final-report/sections/mainmatter/01-introduction.tex`
- `docs/doc-05-final-report/sections/mainmatter/03-hypothesis.tex`
- `docs/doc-05-final-report/sections/mainmatter/04-methodology.tex`
- `docs/doc-05-final-report/sections/mainmatter/05-theoretical-framework/index.tex`
- `docs/doc-05-final-report/sections/mainmatter/05-theoretical-framework/expanded-theory.tex`
- `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/`
- `docs/doc-05-final-report/sections/mainmatter/07-conclusions.tex`
- `docs/doc-06-explanatory-report/sections/04-metodologia.tex`
- `docs/doc-06-explanatory-report/sections/05-marco.tex`
- `src/viu_mrob_tfm/sp3/pose_dynamics.py`
- `src/viu_mrob_tfm/sp3/runner.py`
- `src/viu_mrob_tfm/sp5/methods.py`
- `src/viu_mrob_tfm/sp5/runner.py`
- `scripts/gate_integrated_math_engine.py`
- `scripts/campaigns/run_h11_integrated_engine.py`
- `results/sp3/SP3_POSE_suite_euler_lagrange_transport/report.md`
- `results/sp5/SP5_MC_cooperative_transport_high_power/report.md`

Si solo recibes el PDF, declara qué afirmaciones no puedes verificar contra código o resultados.

## Configuración del comité

Produce cinco informes independientes antes de sintetizar:

1. **Editor académico:** contribución global, coherencia, madurez, narrativa y adecuación a un TFM de alto nivel.
2. **Revisor teórico-matemático:** definiciones, proposiciones, lemas, demostraciones, originalidad y profundidad matemática.
3. **Revisor de mecánica y control:** Euler–Lagrange, wrench, Hamiltoniano, formulación port-Hamiltoniana, pasividad, estabilidad, CBF y dinámica no holónoma.
4. **Revisor metodológico-computacional:** correspondencia teoría–código–experimento, diseño estadístico, reproducibilidad, SP0–SP8 y alcance de los simuladores.
5. **Abogado del diablo:** mejor contraargumento posible contra la novedad, la integración y los claims principales.

Los cinco revisores deben razonar de forma independiente. Después, un editor debe sintetizar acuerdos y desacuerdos y emitir una decisión.

## 1. Narrativa, estructura y claridad

Evalúa la cadena completa:

```text
problema industrial → brecha científica → pregunta → objetivos → hipótesis → arquitectura → teoría → metodología → SP0–SP8 → resultados → conclusiones
```

Comprueba específicamente:

- si el título corresponde al contenido y al alcance real;
- si el problema de cargas heterogéneas conduce naturalmente a coaliciones físicas;
- si la transición desde asignación combinatoria hasta capacidad, wrench y movimiento es comprensible;
- si SP0–SP8 forman una progresión lógica o una colección de campañas débilmente conectadas;
- si se explica por qué cada SP invalida una noción de éxito del nivel anterior;
- si las ecuaciones aparecen antes de ser utilizadas y cada variable está definida;
- si existen saltos entre juegos poblacionales, cierre entero, mecánica, seguridad y aprendizaje;
- si el lector puede distinguir arquitectura conceptual, módulos implementados e integración end-to-end;
- si hay repetición, sobrecarga de siglas, párrafos demasiado densos o conclusiones que aparecen antes de la evidencia;
- si resumen, abstract, introducción, resultados y conclusiones cuentan la misma historia.

Entrega un mapa de flujo narrativo e identifica exactamente dónde se rompe o se debilita.

## 2. Novedad y aporte científico

No presupongas que algo es novedoso porque el manuscrito lo denomine “propuesto”. Clasifica cada aporte como:

- resultado conocido;
- aplicación directa de teoría conocida;
- adaptación o combinación no trivial;
- contribución metodológica;
- contribución de arquitectura/sistematización;
- nueva formulación;
- nuevo resultado teórico demostrado;
- claim empírico;
- propuesta todavía no demostrada.

Audita al menos:

1. concepto de **coalición física**;
2. escalera de validación SP0–SP8;
3. utilidad con insuficiencia, suficiencia y saturación;
4. separación entre cardinalidad, capacidad efectiva y factibilidad wrench;
5. cierre entero QR y guardias físicas;
6. precio de déficit de capacidad y precio mecánico por residual wrench;
7. integración entre dinámica poblacional, asignación, contactos y transporte;
8. variante `support_dual_wrench_market`;
9. controlador de carga denominado Hamiltoniano;
10. contrato de evidencia que conserva timeouts, fallos y cierres.

Para cada uno responde:

- ¿qué existía antes?;
- ¿qué añade exactamente el TFM?;
- ¿hay teorema, algoritmo, implementación o solo una organización conceptual?;
- ¿la evidencia demuestra el aporte?;
- ¿qué redacción de claim sería defendible ante un tribunal?

Exige una tabla `aporte → antecedente → diferencia → evidencia → nivel de novedad → claim permitido`.

## 3. Auditoría del desarrollo matemático

Revisa todas las definiciones, proposiciones, lemas y pruebas. Para cada una determina:

- corrección formal;
- suficiencia de hipótesis;
- si la conclusión es más fuerte que lo demostrado;
- si es un resultado elemental presentado como novedad;
- dependencia de convexidad, compacidad, diferenciabilidad, conectividad o discretización;
- correspondencia con la implementación;
- utilidad real dentro de los experimentos.

Presta atención a:

- monotonía del déficit de capacidad;
- residual wrench como distancia a un conjunto admisible;
- inclusión de conjuntos de wrench al añadir contactos;
- cierre entero bajo demanda visible;
- invariancia mediante CBF;
- equilibrio del reparto cuadrático;
- derivación del PoA y diferencia entre cota teórica y PoA observado;
- precios primal-dual;
- potenciales y condiciones de monotonía;
- estabilidad continua frente a discretización;
- convergencia a equilibrio frente a simple estacionariedad numérica.

Señala cualquier prueba circular, hipótesis omitida, confusión entre condición necesaria y suficiente, o extrapolación desde un caso planar hacia transporte general.

## 4. Mecánica Euler–Lagrange

Reconstruye y evalúa la cadena mecánica del modelo de carga. Comprueba si el manuscrito deriva con suficiente claridad:

1. coordenadas generalizadas de la carga, por ejemplo `q=[x,y,theta]`;
2. energía cinética y potencial;
3. Lagrangiano `L=T−V`;
4. ecuaciones de Euler–Lagrange;
5. forma matricial completa, indicando si corresponde usar
   `M(q)qdd + C(q,qd)qd + Dqd + ∇V(q) = G(q)λ + w_ext`;
6. matriz de masa/inercia y sus propiedades;
7. mapa desde fuerzas de contacto hasta wrench generalizado;
8. límites de fuerza, slots, fricción, saturación y unilateralidad del contacto;
9. diferencias entre empujar, arrastrar, sujetar y transportar;
10. acoplamiento entre carga y robots diferenciales/no holónomos.

Determina si el modelo implementado `M qdd + D qd = G(q)λ` es una simplificación explícita y legítima o si omite términos que invalidan los claims. Comprueba si `M` es constante, si `C=0` está justificado, qué representa `V(q)`, cómo se modela la orientación y si existe conservación/disipación física coherente.

Separa:

- derivación física;
- controlador de pose;
- proyección numérica de wrench;
- diagnóstico energético;
- evidencia experimental.

No aceptes como “validación Euler–Lagrange” el simple hecho de almacenar un campo con ese nombre.

## 5. Hamiltoniano y formulación port-Hamiltoniana

Determina si la tesis desarrolla realmente una formulación Hamiltoniana o solo calcula una energía diagnóstica

```text
H(q,qd)=0.5 qdᵀMqd + V(q).
```

Exige revisar:

- transformación de Legendre y momento conjugado `p=M(q)qd`;
- condiciones para que la transformación sea invertible;
- estado Hamiltoniano `(q,p)`;
- gradientes `∂H/∂q` y `∂H/∂p`;
- estructura port-Hamiltoniana `(J−R)∇H + Gu`;
- antisimetría de `J` y semidefinición positiva de `R`;
- puertos de esfuerzo/flujo y balance de potencia;
- demostración de `Hdot ≤ uᵀy` o balance equivalente;
- disipación con entrada nula;
- pasividad y qué estabilidad puede inferirse;
- incorporación de torques de rueda, inercia equivalente y restricciones no holónomas;
- continuidad de energía cuando cambia la coalición, contacto o rol;
- saltos Hamiltonianos en un sistema híbrido;
- si la variable de coalición puede modificar legítimamente potencial o inercia;
- si las identidades verificadas numéricamente son consecuencias algebraicas construidas o validaciones independientes.

Compara el PDF final con `doc-06-explanatory-report`, donde aparece un desarrollo port-Hamiltoniano más extenso. Decide:

1. qué material debe migrarse al TFM final;
2. qué material es accesorio y debe permanecer fuera;
3. si la ausencia actual rompe la narrativa o debilita el claim Hamiltoniano;
4. si debe renombrarse “control Hamiltoniano” como “control de carga con diagnóstico energético” si no existe una ley port-Hamiltoniana completa.

## 6. Integración juego–mecánica

Evalúa si existe un puente matemático real entre:

```text
déficit de coalición
→ payoff/potencial
→ dinámica poblacional
→ cierre entero
→ selección de contactos
→ wrench
→ fuerza/torque
→ dinámica Euler–Lagrange
→ energía/Hamiltoniano
→ seguridad y transporte
```

Comprueba si todas las flechas están definidas mediante ecuaciones o si algunas son únicamente narrativas. Identifica variables compartidas, interfaces, escalas temporales y condiciones de compatibilidad.

Pregunta central: ¿la tesis presenta una arquitectura modular honesta o reclama una teoría integrada que todavía no demuestra?

## 7. Profundidad matemática avanzada

Evalúa si el nivel matemático es adecuado para un TFM ambicioso y si el formalismo aporta comprensión. No premies complejidad simbólica sin función.

Valora:

- calidad de notación;
- consistencia dimensional y de unidades;
- tratamiento de restricciones;
- teoría de juegos y potenciales;
- optimización convexa/no convexa;
- asignación y cierre discreto;
- dinámica continua y discretización;
- Lyapunov, pasividad y CBF;
- estabilidad de sistemas híbridos;
- conectividad de grafos temporales;
- escalabilidad;
- separación entre resultados exactos, aproximados y empíricos.

Indica qué desarrollo avanzado falta para convertir el marco en una contribución teórica defendible, pero también qué material debería eliminarse si solo añade apariencia de sofisticación.

## 8. Correspondencia teoría–código–evidencia

Para cada claim matemático o mecánico, busca:

```text
ecuación en el manuscrito
→ implementación concreta
→ test unitario/gate
→ experimento
→ métrica
→ tabla/figura
→ conclusión
```

Marca cualquier eslabón ausente.

En particular:

- verifica que la simulación SP3 usa realmente el modelo declarado;
- verifica que el controlador Hamiltoniano de SP5 difiere operacionalmente de otros métodos;
- distingue igualdad algebraica programada de evidencia científica;
- comprueba si los saltos de energía y balances de potencia se miden con unidades físicas;
- determina si la planta, los contactos y las correcciones geométricas permiten claims de estabilidad o seguridad;
- revisa si los resultados negativos de SP3–SP5 contradicen o acotan la novedad propuesta.

## 9. Metodología, estadística y causalidad

Revisa también:

- unidad experimental y emparejamiento por mundo;
- independencia y pseudorreplicación;
- conservación de fallos y timeouts;
- censura del tiempo a solución;
- Holm y familias confirmatorias;
- efectos, intervalos y márgenes;
- relación entre cierre y resultado continuo;
- actor MARL frente a decodificador/cierre;
- validez de usar simuladores y plantas distintas por SP;
- qué resultados son construct validation, comparación competitiva o exploración.

No conviertas esta sección en el único foco de la revisión.

## 10. Calidad expositiva de ecuaciones y figuras

Comprueba:

- si cada símbolo se define una sola vez y se usa de manera estable;
- si las ecuaciones tienen interpretación física después de presentarse;
- si las figuras explican una relación o solo decoran;
- si faltan diagramas del flujo juego–mecánica;
- si las tablas distinguen teoría, implementación y evidencia;
- si los vídeos aportan casos de fallo además de ejemplos favorables;
- si el lector puede reproducir las derivaciones sin consultar el código.

## 11. Abogado del diablo

Formula el contraargumento más fuerte contra la tesis. Como mínimo considera:

- “La novedad es una taxonomía de validación, no una nueva teoría de control”.
- “El cierre global produce el éxito y no la dinámica distribuida”.
- “Euler–Lagrange y Hamiltoniano son diagnósticos estándar añadidos a posteriori”.
- “SP0–SP8 usan plantas diferentes y no prueban una arquitectura integrada”.
- “Las demostraciones son propiedades elementales o consecuencias del diseño”.
- “La ausencia de contacto 3D, fricción y dinámica diferencial completa limita el aporte mecánico”.

Después indica qué evidencia o reescritura refutaría cada contraargumento.

## 12. Salida obligatoria

Entrega:

1. **Decisión editorial:** Accept / Minor Revision / Major Revision / Reject en su estado actual.
2. **Resumen ejecutivo** de máximo 500 palabras.
3. **Cinco informes independientes** según los perfiles definidos.
4. **Mapa narrativo** con rupturas de flujo.
5. **Matriz de novedad** por aporte.
6. **Auditoría de teoremas y demostraciones**.
7. **Auditoría Euler–Lagrange** paso a paso.
8. **Auditoría Hamiltoniana/port-Hamiltoniana** paso a paso.
9. **Matriz teoría–código–evidencia**.
10. **Lista de claims defendibles, sobreafirmados y no soportados**.
11. **Top 10 cambios obligatorios**, priorizados por CRITICAL/MAJOR/MINOR.
12. **Plan de revisión por archivo y sección**, indicando qué añadir, mover, condensar, renombrar o eliminar.
13. **Evaluación cuantitativa 0–10** para narrativa, claridad, rigor matemático, mecánica, novedad, metodología, evidencia, reproducibilidad y madurez de entrega.
14. **Veredicto específico:** cuál es el aporte realmente novedoso que sobreviviría a una defensa exigente.

Cada crítica debe indicar ubicación, problema, impacto y corrección concreta. No inventes experimentos ni supongas que un nombre de método demuestra su formulación. Distingue siempre entre teoría conocida, derivación propia, implementación, evidencia empírica y trabajo futuro.

## Restricción editorial

El PDF ya ocupa 91 páginas y se encuentra dentro del límite por poco. Si recomiendas ampliar Euler–Lagrange o port-Hamiltoniano, indica también qué texto redundante debe condensarse o trasladarse a anexos. No propongas simplemente añadir páginas.