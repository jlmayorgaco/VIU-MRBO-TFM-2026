# 05 — Registro de notación

Mantener una notación única en código, ecuaciones, figuras y memoria. Esta tabla es inicial y debe adaptarse antes de fijar las formulaciones.

La taxonomía vigente contiene únicamente SP1--SP3. Las menciones `SP0`--`SP8` que permanecen en esta tabla califican símbolos y variables de campañas históricas cuyos nombres de código se preservan por reproducibilidad: `sp0`--`sp3` alimentan SP1; `sp4`--`sp6` alimentan SP2; `sp7`--`sp8` alimentan SP3. En texto académico nuevo se usa el SP canónico y, cuando sea necesario, se añade entre paréntesis el código de campaña.

| Símbolo | Significado | Dominio/unidad | Código sugerido |
|---|---|---|---|
| `N` | Número de robots | entero positivo | `n_robots` |
| `K` | Número de cargas/tareas | entero positivo | `n_loads` |
| `w=(s_w,\boldsymbol\zeta_w,\sigma_w)` | Mundo o bloque experimental: escenario, factores y semilla pseudoaleatoria | tupla de configuración; índice de unidad independiente | `world`, `scenario`, `factors`, `seed` |
| `Y_w^m` | Respuesta del método `m` en el mundo `w` | según la métrica | `response[world,method]` |
| `\Delta_w^{A,B}` | Diferencia pareada entre los métodos `A` y `B` dentro del mundo `w` | misma unidad que `Y` | `paired_difference` |
| `\widehat{\Delta}_{RD}^{A,B}` | Diferencia de riesgos pareada estimada entre los métodos `A` y `B` | adimensional, `[-1,1]` | `paired_risk_difference` |
| `p_{\mathrm{Holm}}` | Valor p ajustado por el procedimiento de Holm dentro de una familia de contrastes predeclarada | adimensional, `[0,1]`; informar además contraste, familia y tamaño muestral | `p_value_holm` |
| `i` | Índice de robot | `{1,…,N}` | `robot_id` |
| `k` | Índice de carga/tarea | `{1,…,K}` | `load_id` |
| `S, s` | Número e índice de slots de rol/contacto del SP1 canónico | entero positivo; `s∈{1,…,S}` | `n_slots`, `slot_id` |
| `r_s` | Vector de requisitos multidimensionales del slot `s` | vector adimensional normalizado en la campaña canónica | `slot_requirements[s]` |
| `x_{is}` | Decisión robot--slot; un robot ocupa como máximo un slot | binaria | `assignment[i] == s` |
| `y_k` | Activación todo-o-nada de la carga `k` en el oráculo SP1 | binaria | `activated[k]` |
| `c_{is}^{SP1}` | Coste normalizado de distancia, batería, incorporación y cambio | adimensional | `pair_costs[i,s]` |
| `b_{is}^{SP1}` | Puja local: fracción de valor de la carga menos `c_{is}^{SP1}` | utilidad adimensional | `bids[i,s]` |
| `\mathcal V_i(t)` | Registros de puja visibles por el robot `i` tras `t` rondas de gossip | subconjunto de robots activos | `visibility[i]` |
| `a_i^-` | Slot previo del robot antes del fallo o cambio de prioridad; `-1` indica inactividad | entero en `{-1,0,…,S-1}` | `previous_slot[i]` |
| `\boldsymbol a_i^{res}` | Vector de recursos agregables del robot `i`: contribución cardinal, carga útil y fuerza | `(1, kg, N)` | `resources[i]` |
| `\boldsymbol b_k^{req}` | Requisitos agregados de la carga `k`: cardinalidad mínima, masa y fuerza | `(robots, kg, N)` | `requirements[k]` |
| `C_{ik}^{trav}` | Coste de reclutar `i` para `k`, compuesto por distancia, tiempo y energía con pesos declarados | puntuación de coste; cada componente conserva su unidad antes de ponderar | `costs[i,k]` |
| `\chi_{ik}` | Máscara de compatibilidad energética del par robot--carga | binaria | `compatibility[i,k]` |
| `x_{ik}^{rel}` | Participación relajada del robot `i` en la carga `k`; la masa restante corresponde a inactividad | `[0,1]`, con `sum_k x_{ik}^{rel}<=1` | `x[i,k]` |
| `\widehat{\boldsymbol\lambda}_{i,k}` | Copia local mantenida por `i` de los multiplicadores de déficit de la carga `k` | vector no negativo de tres componentes normalizados | `dual[i,k,:]` |
| `r_{prim}` | Norma del déficit de recursos; la campaña conserva versiones física y normalizada | unidades mixtas en bruto o adimensional tras dividir por requisitos | `primal_residual`, `primal_residual_normalized` |
| `r_{cons}` | Desacuerdo de copias duales respecto a su promedio | norma euclídea adimensional | `consensus_residual` |
| `J_{raw}(x)` | Coste de reclutamiento no regularizado, `C^T x` | puntuación de coste | `objective`, `raw_objective` |
| `J_{tau}(x)` | Objetivo relajado regularizado, `C^T x/c_scale-tau H([x,idle])` | adimensional | `regularized_objective` |
| `r_{stat}` | Residuo combinado del punto fijo primal y la proyección dual bajo el paso declarado | adimensional | `stationarity_residual` |
| `\widehat L_F(I)` | Estimador numérico por instancia `I` de la escala del operador normalizado; no es una constante de Lipschitz demostrada | adimensional, positivo | `operator_scale_estimate` |
| `\alpha_I` | Paso precondicionado por instancia, `clip(\eta/\widehat L_F(I),\alpha_{min},\alpha_{max})` | paso digital adimensional, positivo | `step` |
| `C_{op}` | Indicador de convergencia operacional conjunta bajo residuos relativos `10^-3` en V2 | binaria | `operational_converged` |
| `C_{ref}` | Indicador de convergencia de la fase de refinamiento; la comparabilidad exige además factibilidad normalizada `<=10^-6` | binaria | `refinement_converged`, `comparable_at_1e6` |
| `\ell_{aug}` | Longitud de una cadena de reasignación usada por la recuperación entera V2 | movimientos enteros no negativos | `maximum_chain_length`, `chain_lengths` |
| `n_{aug}^{exp}` | Número de estados enteros explorados durante la búsqueda acotada de caminos de aumento | conteo no negativo | `nodes_explored` |
| `B_w^{dir},D_w^{A*}` | Indicadores de que una ruta directa intersecta un obstáculo construido y de que A* produce un desvío medible en el mundo `w` | binarios | `direct_path_blocked`, `astar_detoured` |
| `R_\varepsilon` | Primera iteración que satisface conjuntamente los tres criterios relativos; queda censurada a la derecha si no se observa antes del límite | iteraciones digitales | `R_epsilon`, `right_censored` |
| `g_{raw}^{LP}` | Gap de `J_raw` respecto a LP-raw, definido solo para perfiles estrictamente comparables | razón adimensional | `gap_raw_lp` |
| `g_{\tau}^{LP}` | Gap de `J_tau` respecto a LP-tau con el mismo `tau` y normalización, definido solo para perfiles estrictamente comparables | razón adimensional | `gap_regularized_lp` |
| `g_{int}^{MILP}` | Gap entero respecto a un MILP factible con certificado de optimalidad y `mip_gap<=10^-8` | porcentaje | `integer_gap_milp` |
| `I_w^{comp}` | Indicador de comparabilidad estricta del mundo `w`: referencia óptima, estado finito, simplex válido y factibilidad dentro de tolerancia | binaria | `comparable_to_lp` |
| `\lambda_2(L)` | Conectividad algebraica del Laplaciano del grafo de comunicación estático | adimensional, no negativa salvo tolerancia numérica | `lambda2` |
| `q_i` | Estado del robot | posición/orientación o estado dinámico | `robot_state[i]` |
| `p_i` | Posición del robot | m | `robot_position[i]` |
| `\tilde x=x/L_x,\ \tilde y=y/L_y` | Coordenadas cartesianas normalizadas por el ancho `L_x` y el alto `L_y` del espacio de trabajo; se usan únicamente para comparar geometrías espaciales | adimensionales, `[0,1]` | `x/workspace_width`, `y/workspace_height` |
| `theta_i` | Orientación del robot | rad | `robot_heading[i]` |
| `u_i` | Entrada de control | según modelo | `control[i]` |
| `v_i, omega_i` | Velocidad lineal/angular | m/s, rad/s | `linear_velocity`, `angular_velocity` |
| `\boldsymbol h_i` | Punto geométrico auxiliar adelantado del uniciclo, `p_i+\ell(cos theta_i,sin theta_i)^T`; se usa para visualizar el rumbo y no añade estado físico | m, vector en `\mathbb R^2` | `lookahead_point[i]` cuando una ley lo utilice |
| `\ell` | Distancia positiva desde el centro del uniciclo al punto auxiliar `\boldsymbol h_i` de la Figura `fig:robot` | m, positiva | `lookahead_distance_m` cuando una ley lo utilice |
| `R^{sens}` | Radio local de sensado del AMR en el piloto AWS | m, positivo; piloto: `1,8 m` | `sensing_radius_m` |
| `R^{com}` | Radio de comunicación vecinal del AMR en el piloto AWS | m, `R^{com}>R^{sens}`; piloto: `3,2 m` | `communication_radius_m` |
| `\mathcal N_i^{com}(t)` | Vecinos cuya distancia a `i` no excede `R^{com}` en el instante muestreado | subconjunto de robots | `communication_neighbors` |
| `\mathcal O_i^{sens}(t)` | Robots, cargas y obstáculos estáticos dentro del alcance `R^{sens}` de `i` | conjunto de objetos observados | `sensed_robots`, `sensed_loads`, `sensed_static_objects` |
| `c_i` | Vector de capacidades del robot | unidades por componente | `robot_capability[i]` |
| `b_i` | Estado de batería usado en SP2 | fracción en `[0,1]` | `battery_fraction[i]` |
| `b_i^{res}` | Reserva mínima de batería usada en SP2 | fracción en `[0,1)` | `battery_reserve_fraction[i]` |
| `c_i^{pay}` | Carga útil nominal escalar del robot `i` en SP2 | kg | `nominal_payload_kg[i]` |
| `c^{ref}` | Escala de referencia que normaliza la carga útil en SP2 | kg; campaña: `1 kg` | `service_reference_kg` |
| `psi_i^b` | Factor de disponibilidad energética por encima de la reserva | adimensional, `[0,1]` | `battery_factor[i]` |
| `psi_ik^d` | Descuento operacional por distancia en SP2 | adimensional, `(0,1]` | `distance_factor[i,k]` |
| `a_ik` | Disponibilidad operacional del par robot--carga en SP2, `psi_i^b psi_ik^d` | adimensional, `[0,1]` | `operational_availability[i,k]` |
| `ell_d` | Escala operacional del descuento de distancia | m, positiva | `distance_scale_m` |
| `e_ik` | Contribución operacional normalizada del par robot--carga en SP2, `(c_i^{pay}/c^{ref})a_ik` | unidades adimensionales de servicio | `service_contribution[i,k]`; columnas archivadas: `effective_capacity[i,k]` |
| `d_k^{srv}` | Umbral escalar de servicio operacional de la carga `k` en SP2 | unidades adimensionales de servicio | `service_demand[k]`; columnas archivadas: `effective_capacity_demand[k]` |
| `S_k(x)` | Servicio operacional agregado asignado a la carga `k` | unidades adimensionales de servicio | `assigned_service[k]` |
| `V_k` | Valor/recompensa de completar la carga `k` en SP2 | puntuación adimensional | `load_value[k]` |
| `g_ik` | Coste normalizado del par robot--carga en el juego SP2 | puntuación adimensional | `normalized_pair_cost[i,k]` |
| `z_k` | Indicador de carga completa en los oráculos SP2 | binaria | `load_completed[k]` |
| `s_k` | Servicio truncado contabilizado por el oráculo SP2 | unidades de servicio, `[0,d_k^{srv}]` | `covered_capacity[k]` (nombre histórico) |
| `E_ik^{trav}` | Energía estimada de llegada del robot `i` a la carga `k` | Wh | `travel_energy_wh[i,k]` |
| `l_k` | Pose de origen de la carga | m, rad | `load_source[k]` |
| `d_k` | Pose destino de la carga | m, rad | `load_target[k]` |
| `\nu_k` | Índice de ciclo o misión vigente de la carga `k` en el piloto AWS | entero no negativo | `task_cycle[k]` |
| `d_{k,\nu}` | Destino asignado a la carga `k` durante el ciclo `\nu`; permanece fijo hasta entrega o cierre del ciclo | m, rad | `target_for_cycle(k, task_cycle)` |
| `\mathcal P_{k,\nu}` | Ruta de rejilla A* de la huella compuesta hacia `d_{k,\nu}` | secuencia finita de poses planares | `load.path` |
| `\rho_i^{nav}=(\rho_{i,L},\rho_{i,R},\rho_{i,W})` | Preferencia poblacional local del móvil `i` por las primitivas continua izquierda, derecha y espera | simplex `\Delta_3` | `navigation_preference` |
| `v_i^{RAW},v_i^{SAFE},v_i^{EXEC}` | Velocidad producida por el juego local, proyectada por las semirrectas CBF y realizada tras el límite de aceleración | m/s, vectores en `\mathbb R^2` | `raw_velocity`, `safe_velocity`, `exec_velocity` |
| `\mathcal H_i^{sens}(q)` | Semiespacios CBF construidos con obstáculos dentro de `R^{sens}` y fronteras conocidas del mapa | conjunto finito local | `local_barrier_constraints` |
| `q_k^L` | Pose planar real de la carga `k` | `(m, m, rad)` | `load_pose[k]` |
| `\hat q_k^L` | Pose planar estimada de la carga mediante percepción/proximidad | `(m, m, rad)` | `estimated_load_pose[k]` |
| `e_k^L` | Error de pose de la carga respecto a referencia/destino | `(m, m, rad)`, normalizar para normas | `load_pose_error[k]` |
| `r_k` | Vector de requisitos de la carga | unidades por componente | `load_requirement[k]` |
| `n_k` | Cardinalidad mínima | entero | `min_coalition_size[k]` |
| `\bar m_R^{\mathrm{share}}` | Masa cooperativa nominal asignada por AMR para derivar la cuota visual del piloto; no es capacidad mecánica certificada | kg/AMR, positiva | `cooperative_payload_share_kg_per_amr` |
| `C_k` | Coalición asignada a la carga `k` | subconjunto de robots | `coalition[k]` |
| `\mathcal I^{vis}` | Identificadores activos presentes en la vista del líder temporal de Cargo tras la propagación | conjunto finito | `known_indices` |
| `f_i^{max}` | Límite de fuerza planar almacenado para el robot `i` en Cargo | N | `force_limits_n[i]` |
| `\delta_C^{ref},c_C^{ref},f_C^{ref}` | Escalas de referencia de distancia, carga útil y fuerza en la puntuación Cargo | m, kg, N; campaña: `1 m`, `1 kg`, `1 N` | `CARGO_DISTANCE_REFERENCE_M`, `CARGO_PAYLOAD_REFERENCE_KG`, `CARGO_FORCE_REFERENCE_N` |
| `\bar\delta_i,\bar c_i,\bar f_i` | Distancia, carga útil y fuerza normalizadas del candidato Cargo | adimensionales | `normalized_distance`, `normalized_payload`, `normalized_force` |
| `s_i` | Puntuación empírica adimensional para ordenar candidatos Cargo de forma ascendente | adimensional | `_cargo_spatial_score` |
| `m_k^{req},F_k^{req}` | Masa soportada y fuerza planar requeridas por la carga en el certificado agregado Cargo | kg, N | `load_mass_kg`, `required_force_n` |
| `q_k(a)` | Ocupación lógica de la carga `k` bajo el perfil SP1 | entero no negativo | `load_counts[k]` |
| `rho_D` | Presión global de demanda de SP1, `(sum_k n_k)/N` | razón adimensional | `demand_pressure` |
| `D_n(a), O_n(a)` | Déficit y exceso totales respecto de las cuotas `n_k` | conteos enteros no negativos | `deficit`, `excess` |
| `J_Q(a), Phi_Q(a)` | Coste penalizado y potencial del juego lineal de cuotas de SP1 | adimensional | `penalized_cost`, `potential` |
| `B_{beta,k}(q)` | Beneficio de cuórum exponencial normalizado y saturado de la carga `k` | adimensional, `[0,1]` | `quorum_benefit` |
| `beta` | Intensidad de rendimientos crecientes antes del cuórum | adimensional, `>=0` | `quorum_beta` |
| `\mathcal Q_{\mathrm{QR}}` | Operador de cierre entero por ranking y cuórum | mapeo de preferencias a asignación binaria | `quorum_closure` |
| `F_exact` | Indicador de que toda carga ocupada tiene cardinalidad cero o exactamente `n_k` | binaria | `closed` |
| `V_comp` | Valor total de cargas cerradas | utilidad adimensional | `completed_value` |
| `D_norm, O_norm` | Déficit normalizado por demanda y exceso normalizado por flota | razones adimensionales | `normalized_deficit`, `normalized_excess` |
| `R_partial` | Fracción de robots asignados a cargas con ocupación estrictamente entre cero y `n_k` | razón adimensional | `partial_robot_fraction` |
| `x_ik` | Participación/asignación de `i` a `k` | binaria o continua; declarar | `assignment[i,k]` |
| `y_k` | Activación todo-o-nada de la tarea `k` en la extensión de selección opcional | binaria | `task_selected[k]` |
| `v_k` | Recompensa de completar la tarea opcional `k` en la reducción de complejidad | utilidad adimensional | `task_value[k]` |
| `κ_ik` | Coste de asignación normalizado; en SP0 coincide con la distancia normalizada `bar_delta_ik` | adimensional, `[0,1]` en la campaña SP0 | `costs[i,k]` |
| `a_i` | Estrategia discreta del robot `i`; `0` indica inactividad y `k` asignación a tarea `k` | `{0,…,K}` | `assignment[i]` |
| `Q_k(a)` | Capacidad útil agregada en la carga `k` bajo el perfil atómico N4 | kg | `aggregate_capacity[k]` |
| `v_k^{reg}` | Versión monótona del registro distribuido de la carga `k`; no confundir con el valor opcional `v_k` | entero no negativo | `load_versions[k]` |
| `\mathcal K_{act}` | Cargas activas cuya cobertura es obligatoria en la decisión actual; en campañas estáticas coincide con `{1,…,K}` | conjunto finito | `active_loads` |
| `D_4(a)` | Déficit total de capacidad en N4, `sum_{k\in\mathcal K_{act}} [m_k-Q_k(a)]_+` | kg | `total_deficit` |
| `J_4(a)` | Coste espacial del perfil factible N4, suma de distancias robot--carga | m | `distance_cost` |
| `\Delta D_i,\Delta J_i` | Cambios exactos al aplicar una desviación atómica unilateral | kg, m | `delta_deficit`, `delta_distance` |
| `z_k=(Q_k,v_k^{reg})` | Registro versionado de la carga `k`: capacidad agregada y versión | kg, entero | `QuotaRegister` |
| `p:C\rightarrow b_C` | Propuesta atómica de una coalición desviadora `C` hacia acciones `b_C` | mapeo discreto | `MoveProposal` |
| `\Psi_4(a)=(D_4(a),J_4(a))` | Criterio de N4 minimizado en orden lexicográfico: primero déficit y, una vez factible, recorrido | par ordenado (kg, m) | guardas `PHASE_QUOTA`, `PHASE_GEOMETRY` |
| `\Phi_Q=-D_4,\Phi_G=-J_4` | Potenciales escalares de las fases de cuota y geometría de N4 | kg y m, respectivamente | `PHASE_QUOTA`, `PHASE_GEOMETRY` |
| `u_i^X(a)=\Phi_X(a)-\Phi_X(0,a_{-i})` | Utilidad marginal tipo wonderful-life del robot `i` en la fase `X`; la identidad de potencial exacto se usa solo para desviaciones unilaterales | kg en Q; m en G | formulación F-I |
| `\mathcal F=\{a:D_4(a)=0\}` | Conjunto de perfiles atómicos factibles sobre el que se activa la fase geométrica | conjunto finito | guarda `PHASE_GEOMETRY` |
| `\Delta_pD,\Delta_pJ` | Cambios de déficit y recorrido debidos a la propuesta `p` | kg, m | `delta_deficit`, `delta_distance` |
| `g_a(p)` | Ganancia positiva de `p` en la fase activa; vale cero si la propuesta no es admisible | kg en Q; m en G | `_gain`, `build_proposal` |
| `\mathcal P_h^+(a)` | Propuestas con `|C(p)|\leq h` y `g_a(p)>0`; `h=1,2,3` define la vecindad local | conjunto finito | generadores unilateral, pair y triple |
| `\mathcal V_h(a)` | Perfiles alcanzables desde `a` cambiando entre uno y `h` robots, sin restricción de conectividad | conjunto finito de perfiles | refinamiento BR/2BR/C3 |
| `\mathcal V_h^{\mathrm c}(a)` | Perfiles de `\mathcal V_h(a)` cuyo conjunto de robots modificados induce un subgrafo conectado en `G` | conjunto finito de perfiles | E9 con `connected_only=True` |
| `h_{\mathrm c}^\star(a)` | Menor orden de una desviación conectada que reduce `\Psi_4`; E9 lo busca hasta `H=3` y, si no aparece, informa `>3` | entero positivo o categoría censurada | `minimum_improving_coalition_order` |
| `\mathcal G_C=(\mathcal P,\mathcal E_C)` | Grafo de conflicto entre propuestas calculadas sobre las mismas versiones; una arista indica robot o carga modificada compartidos | grafo simple | `proposal_conflict_graph` |
| `\mathcal B` | Lote independiente de propuestas en `\mathcal G_C` que puede componerse en paralelo bajo una fase común | subconjunto de propuestas | `distributed_mis_indices` |
| `M_{\mathrm{DMIS}}` | Conjunto independiente maximal seleccionado mediante prioridades entre vecinos de conflicto | subconjunto de propuestas | `distributed_mis_indices` |
| `\beta_t` | Inversa de temperatura de la regla log-lineal finita; en N4 v2 aumenta linealmente de 1 a 24 | adimensional, positiva | `beta` |
| `x_i\in\Delta_i`, `x_{ik}` | Intención continua del robot `i` y su componente para la carga `k` en las familias N4 F-II--F-III; no es una asignación física | simplex; fracción `[0,1]` | `initial_simplex`, `project_simplex_rows` |
| `Q_k(x)=\sum_i c_i^{pay}x_{ik}` | Capacidad relajada asociada a la carga `k`; distinta de la capacidad atómica `Q_k(a)` | kg | `population_potential_and_fitness` |
| `r_k(x)=[1-Q_k(x)/m_k]_+` | Déficit relativo de cobertura de la carga `k`; vale exactamente cero cuando la cuota continua está cubierta | adimensional | `population_potential_and_fitness` |
| `\widetilde\Phi(x)=-\frac{\alpha}{2}\sum_k r_k(x)^2-\frac{\beta}{N}\sum_{i,k}\bar d_{ik}x_{ik}` | Potencial continuo común de F-II; penalización squared-hinge más coste espacial normalizado | adimensional | `population_potential_and_fitness` |
| `F_{ik}=\partial\widetilde\Phi/\partial x_{ik}` | Fitness común de Replicator, Smith, BNN y Logit | adimensional por unidad de `x_{ik}` | `population_potential_and_fitness` |
| `\bar F_i=\sum_qx_{iq}F_{iq}` | Payoff medio de la distribución individual `x_i` | mismas unidades que `F_i` | `mean_payoff` |
| `\tau` | Temperatura de la dinámica Logit continua; no confundir con la inversa de temperatura finita `\beta_t` de Geo-LLL | mismas unidades que el payoff, positiva | formulación F-II |
| `\mathcal R(x)=a` | Postproceso central determinista común que prioriza la intención continua y aplica recuperación aumentante acotada hasta producir una asignación atómica; su tráfico no se modela | aplicación a `{0,…,K}^N` | `atomic_closure` |
| `g_k(x)=1-Q_k(x)/m_k` | Restricción compartida normalizada de F-III; la factibilidad continua exige `g_k(x)\leq0` | adimensional | `vgnekkt_residuals` |
| `\lambda_k`, `\lambda_{ik}` | Multiplicador común de la carga `k` y copia local mantenida por el robot `i` | adimensional en el problema normalizado | `solve_central_vgne`, `run_distributed_vgne` |
| `J_i(x_i)=N^{-1}\sum_k\bar d_{ik}x_{ik}+\frac{\epsilon}{2}\lVert x_i\rVert^2` | Coste individual regularizado de F-III | adimensional | `_vgne_objective` |
| `\epsilon` | Regularización cuadrática positiva de F-III; introduce monotonía fuerte y modifica explícitamente el problema continuo | adimensional, positiva | `regularization` |
| `\mathcal L(x,\lambda)=\sum_iJ_i(x_i)+\sum_k\lambda_kg_k(x)` | Lagrangiano del problema continuo regularizado con multiplicador común | adimensional | `_vgne_gradient` |
| `\mathbf F(x)=\operatorname{col}_i(\nabla_{x_i}J_i)` | Pseudogradiente del juego F-III; no confundir con el payoff poblacional `F_{ik}^{X}` | unidades de gradiente de coste | formulación vGNE |
| `\widehat g_{ik}` | Estimación DAC local del robot `i` sobre la restricción compartida normalizada de la carga `k` | adimensional | `run_distributed_vgne` |
| `T_{\mathcal C}(y)`, `\Pi_{T_{\mathcal C}(y)}` | Cono tangente de `\mathcal C` en `y` y proyección; la implementación digital usa proyección euclídea por iteración | según la variable proyectada | `project_simplex_rows`, `run_distributed_vgne` |
| `s_t`, `u_t` | Estado observable y perfil atómico decidido en la etapa `t` del piloto F-IV | estado híbrido; acción discreta | `DynamicState`, `run_event_triggered_policy` |
| `T(s_t,u_t,e_{t+1})` | Actualización determinista del estado condicionada por el evento exógeno; no es un kernel probabilístico estimado | mapeo de estados y eventos | `snapshot_world` |
| `e_t\in\{\mathrm{arrival},\mathrm{completion},\mathrm{failure}\}` | Evento exógeno que modifica trabajos o disponibilidad antes de resolver la etapa `t` | etiqueta discreta | `canonical_event_schedule` |
| `C_t(s_t,u_t)` | Coste de etapa: déficit normalizado, recorrido normalizado y conmutación respecto de `a_{t-1}` | adimensional | `stage_cost` |
| `V^pi(s_0)=\sum_{t=0}^{T-1}\gamma^t C_t` | Coste descontado finito de una política en E8 | adimensional | `discounted_cost` |
| `T_{\mathrm{UTIL}}` | Número de entradas de la tabla UTIL máxima de DPOP | conteo entero | `utility_entries` |
| `m_k(a)` | Ocupación de la tarea `k` bajo el perfil discreto `a` | entero no negativo | `task_counts[k]` |
| `\kappa_{ik}^{\mathrm{pad}}` | Coste robot--tarea en la matriz cuadrada rellenada usada por el certificado de precios de SP0 | adimensional, no negativo | `padded_cost_matrix[i,k]` |
| `D(a), E(a)` | Déficit total y exceso total de ocupación en SP0 | enteros no negativos | `deficit`, `excess` |
| `F_λ(a)` | Coste social penalizado `C(a)+λ(D(a)+E(a))` | adimensional | `penalized_cost` |
| `λ` | Peso de exclusión/cobertura del juego SP0 | adimensional; en el teorema `λ>κ_max` | `penalty` |
| `B` | Desplazamiento positivo usado en el bienestar de SP0; `B=1+0.05=1.05` en la campaña | adimensional | `welfare_offset` |
| `W_λ(a)` | Bienestar social penalizado `BK-F_λ(a)` | utilidad adimensional | `social_welfare` |
| `η_W(a)` | Bienestar relativo de SP0, `W_λ(a)/(BK-C*)` | razón adimensional | `welfare_efficiency` |
| `r(a)` | Brecha de coste por carga de una asignación factible, `(C(a)-C*)/K` | coste adimensional por carga | `regret_per_task` |
| `C*` | Coste mínimo del oráculo de asignación de SP0 | adimensional | `optimum_cost` |
| `X` | Matriz relajada de asignación tras completar SP0 con tareas ficticias | adimensional; `X in B_N` | `relaxed_assignment` |
| `B_N` | Politopo de matrices doblemente estocásticas de orden `N` | adimensional | `birkhoff_polytope` |
| `s_k(X)` | Masa u ocupación relajada total de la tarea `k` | adimensional | `task_mass[k]` |
| `pi_k` | Precio dual local asociado a la restricción de ocupación de la tarea `k` | adimensional | `task_price[k]` |
| `rho, gamma` | Ganancia de penalización aumentada y tasa de actualización dual | adimensional y s^-1, respectivamente | `augmented_penalty`, `dual_rate` |
| `tau` | Peso de regularización entrópica de la relajación SP0 | adimensional, `>0` | `entropy_weight` |
| `ε` | Tolerancia de complementariedad y mejor respuesta del juego de precios | utilidad adimensional positiva | `auction_epsilon` |
| `\mathcal G_A` | Grafo bipartito robot--carga que define compatibilidad y costes de SP0 | grafo bipartito ponderado | `assignment_graph` |
| `\mathcal G_C(R)` | Grafo robot--robot que restringe mensajes de SP0 para radio `R` | grafo no dirigido estático en el análisis SP0 | `communication_graph` |
| `\widehat{\boldsymbol\pi}_i^t` | Copia local del vector de precios de tareas mantenida por el robot `i` | utilidad adimensional, vector de longitud `N` tras padding | `local_prices[i]` |
| `\bar{\boldsymbol\pi}^t` | Promedio de las copias locales de precios | utilidad adimensional | `mean_prices` |
| `e_\pi^t` | Máximo desacuerdo local de precios respecto al promedio | utilidad adimensional, norma infinito | `price_disagreement` |
| `\mathcal D_0` | Desacuerdo inicial apilado de precios, `\|[\widehat{\boldsymbol\pi}_i^0-\bar{\boldsymbol\pi}^0]_{i=1}^N\|_F` | utilidad adimensional | `initial_consensus_error` |
| `q` | Factor espectral de contracción de consenso para `W=I-alpha L` | adimensional, `[0,1)` bajo los supuestos declarados | `consensus_contraction` |
| `R^\star` | Radio crítico mínimo que hace conexo el grafo estático de SP0 | m | `critical_communication_radius` |
| `\Delta_\star` | Separación de coste entre el óptimo único y el segundo mejor matching | utilidad adimensional positiva | `assignment_cost_separation` |
| `\mathcal M_\eta` | Valores escalares transmitidos para alcanzar error de consenso `eta` bajo el modelo SP0 | conteo | `consensus_scalar_messages` |
| `h_k(m)` | Término anónimo de ocupación de la tarea `k` cuando otros robots producen ocupación `m`; independiente de la matriz de costes en la frontera de implementabilidad SP0 | utilidad adimensional | `anonymous_occupancy_term[k]` |
| `t_{\mathrm{exact}}` | Número suficiente de rondas para que el certificado SP0 fuerce recuperación exacta del matching central en costes cuantizados | rondas | `exact_recovery_rounds` |
| `\mathcal M_{\mathrm{exact}}` | Valores escalares transmitidos hasta el certificado de recuperación exacta | conteo | `exact_recovery_scalar_messages` |
| `R^\dagger` | Radio que minimiza comunicación total sujeto a un nivel de calidad fijado; solo se estima cuando exista campaña de red | m | `communication_optimal_radius` |
| `p_j` | Precio dual de la tarea u objeto `j` en auction | utilidad adimensional | `prices[j]` |
| `rho_ik` | Preferencia continua del robot `i` por la carga `k` antes del cierre entero | adimensional, `[0,1]` | `preference[i,k]` |
| `\widehat x_{ik}^{\mathrm{rep}}` | Estimación local mantenida por el robot `i` de la masa media de preferencia hacia la carga `k` en la dinámica replicadora | adimensional, `[0,1]` salvo transitorios numéricos del consenso dinámico | `replicator_occupancy_estimate[i,k]` |
| `e_{\mathrm{cons}}^{\mathrm{comp}}` | Máximo desacuerdo en norma infinito entre estimaciones y promedio de preferencias dentro de cada componente conexa | adimensional, no negativo | `consensus_error_final` |
| `\mathcal M_{\mathrm{rep}}` | Número de valores escalares transmitidos por el consenso replicador, `2|E|K I` por evento con `I` iteraciones | conteo | `scalar_messages` |
| `sigma_i` | Modo local de misión del robot `i` | conjunto finito de modos locales | `mission_mode[i]` |
| `t_m, Delta t` | Instante de muestreo y paso de integración digital | s | `time[m]`, `time_step` |
| `\succeq` | Desigualdad componente a componente para vectores de recursos | relación de orden parcial | `np.all(lhs >= rhs)` |
| `f_ik` | Payoff del robot `i` por estrategia `k` | utilidad normalizada | `payoff[i,k]` |
| `Phi` | Potencial global del juego | escalar | `potential` |
| `delta_ik` | Distancia entre el robot `i` y la carga `k` | m | `robot_load_distance[i,k]` |
| `bar_delta_ik` | Distancia robot--carga normalizada por una cota geométrica fijada antes de resolver la instancia | adimensional, `[0,1]` | `normalized_distance[i,k]` |
| `w_k` | Peso opcional de prioridad de la carga `k` en extensiones posteriores; no interviene en SP0 | adimensional, `>0` | `task_priority_weight[k]` |
| `tilde_kappa_ik` | Coste espacial ponderado previo a la normalización final | adimensional, `>=0` | `weighted_assignment_cost[i,k]` |
| `Psi(delta_ik)` | Descuento espacial aplicado al payoff o a la revisión | adimensional, típicamente `[0,1]` | `spatial_discount[i,k]` |
| `mu_i(t)` | Tasa local de revisión estratégica del robot `i` | s^-1 | `revision_rate[i]` |
| `\nu_i` | Entrada de control estratégico del robot `i`: nueva acción, flujo de preferencia, puja o revisión según el SP | declarar por SP; no es una velocidad física | `strategic_control[i]` |
| `\boldsymbol z_0(a)` | Salida regulada de SP0, `(D(a),E(a))^T` | conteos enteros no negativos | `sp0_regulated_output` |
| `z_{1,k}(a;y)` | Error de cierre de SP1, `q_k(a)-n_k y_k`; para cargas obligatorias `y_k=1` | conteo entero | `sp1_closure_error[k]` |
| `z_{2,k}(\rho)` | Déficit normalizado de servicio de SP2, `[1-S_k(\rho)/d_k^{srv}]_+` | adimensional, `[0,1]` | `sp2_capacity_error[k]` (nombre histórico) |
| `\boldsymbol z_{3,k}^W(\rho)` | Error vectorial de wrench de SP3, `\boldsymbol d_k-\boldsymbol y_k(\rho)` | adimensional, vector en `\mathbb R^3` | `sp3_wrench_error[k]` |
| `\widehat m_{ik},\widehat q_{ik}` | Estimaciones mantenidas por el robot `i` de ocupación unitaria o cardinalidad de la carga `k` | conteos estimados | `estimated_load_count[i,k]` |
| `\widehat S_{ik}` | Estimación del robot `i` del servicio operacional agregado en la carga `k` | unidades adimensionales de servicio | `estimated_service[i,k]` |
| `\widehat{\boldsymbol y}_{ik}` | Estimación del robot `i` del wrench normalizado agregado en la carga `k` | adimensional, vector en `\mathbb R^3` | `estimated_aggregate_wrench[i,k]` |
| `\widehat h_{ia}` | Estimación del robot `i` de la violación agregada de ocupación del slot `a` | adimensional | `estimated_slot_violation[i,a]` |
| `\mathcal S` | Conjunto de estrategias poblacionales | conjunto finito | `strategy_set` |
| `x_k` | Masa o proporción poblacional en la estrategia `k` | adimensional, `[0,1]` | `population_mass[k]` |
| `\Delta` | Símplex de estados poblacionales | subconjunto de `\mathbb R^K` | `population_simplex` |
| `f_k(x)` | Payoff de la estrategia poblacional `k` en el estado `x` | utilidad normalizada | `population_payoff[k]` |
| `\bar f` | Payoff medio de la población | utilidad normalizada | `mean_payoff` |
| `\eta` | Parámetro de suavizado de la respuesta logit | utilidad normalizada | `logit_temperature` |
| `\mathcal G(t)` | Grafo de comunicación | grafo variable | `communication_graph` |
| `A(t)` | Matriz de adyacencia del grafo | adimensional | `adjacency_matrix` |
| `D(t)` | Matriz diagonal de grados | adimensional | `degree_matrix` |
| `L(t)` | Laplaciano `D(t)-A(t)` | adimensional | `graph_laplacian` |
| `\lambda_2(L)` | Conectividad algebraica de un grafo no dirigido | adimensional | `algebraic_connectivity` |
| `N_i(t)` | Vecinos de `i` | conjunto | `neighbors[i]` |
| `R` | Radio de comunicación | m | `communication_radius` |
| `tau_d` | Retardo de comunicación | s | `communication_delay` |
| `p_loss` | Probabilidad de pérdida | `[0,1]` | `packet_loss_probability` |
| `mathcal O` | Conjunto de obstáculos | conjunto geométrico | `obstacles` |
| `b_i^min` | Reserva mínima de batería del robot `i` | misma unidad que `b_i` | `minimum_battery[i]` |
| `M_k(q_k^L), h_k` | Inercia planar y términos dinámicos de la carga `k` | unidades SI compatibles con fuerza/torque | `load_inertia`, `load_dynamics_terms` |
| `W_k` | Wrench requerido/aplicado a carga `k` | N, N·m | `load_wrench[k]` |
| `q_L=(p_L,\theta_L)` | Abreviatura local de `q_k^L` cuando la derivación SP2 trata una sola carga | m, rad | `load_pose[k]` |
| `\xi_L=(v_x,v_y,\omega)` | Twist planar de la carga única de la derivación; en código conserva índice de carga | m/s, rad/s | `load_twist[k]` |
| `\dot\xi_L` | Variación temporal del twist de la carga única de la derivación | m/s², rad/s² | `load_twist_rate[k]` |
| `r_i` | Posición del pivote soportado por el robot `i`, expresada en el marco de la carga y relativa a su centro de masa | m, vector en `R^2` | `pivot_offset[i]` |
| `v_i^{\mathrm{piv}}(q_L,\xi_L)` | Velocidad mundial del pivote `i` inducida por el twist de la carga | m/s, vector en `R^2` | `pivot_velocity[i]` |
| `\mathbf e_i,\mathbf e_i^\perp` | Dirección longitudinal del robot `i` derivada de `\theta_i` y su normal lateral | vectores unitarios | `heading_unit_vector`, `lateral_unit_vector` |
| `A_i(\theta_i,q_L,r_i)` | Fila de restricción no holónoma instantánea inducida por el robot `i` | mapea twist a m/s lateral | `instantaneous_nonholonomic_row[i]` |
| `\Xi_{\mathcal C}^{\mathrm{inst}}` | Conjunto de twists admisibles con los rumbos actuales de la coalición | subconjunto de `R^2 x R` | `instantaneous_twist_set` |
| `\Theta_i^\star(v_i^{\mathrm{piv}})` | Ramas de rumbo alineadas con la velocidad no nula del pivote; distingue avance y reversa | conjunto de ángulos | `aligned_heading_branches[i]` |
| `\mathcal E_{\mathcal C}^{\mathrm{trk}}` | Envolvente cinemática extendida de seguimiento para pares `(\xi_L,\dot\xi_L)` bajo alineación y límites de rueda | subconjunto de twists y aceleraciones | `tracking_envelope` |
| `\Xi_{\mathcal C}^{\mathrm{align}}` | Proyección de la envolvente de seguimiento sobre el twist para la familia de slew rates declarada | subconjunto de `R^2 x R` | `aligned_twist_set` |
| `\Sigma_i^{\mathrm{dir}},\sigma_i^{\mathrm{dir}},\varsigma_i` | Ramas avance/reversa permitidas, rama seleccionada y signo longitudinal derivado | subconjunto de `{0,1}`; binario; `{-1,1}` | `allowed_direction_branches[i]`, `direction_branch[i]`, `longitudinal_direction_sign[i]` |
| `\varepsilon_\theta,\varepsilon_v^{\mathrm{piv}}` | Tolerancia de alineación y guarda mínima de velocidad del pivote para seguimiento continuo | rad, m/s | `heading_alignment_tolerance`, `pivot_speed_guard` |
| `\nu_i=(v_i,\omega_i)` | Velocidad reducida del robot diferencial `i` | m/s, rad/s | `robot_body_velocity[i]` |
| `q=(q_L,q_1,\ldots,q_N)` | Configuración conjunta de una carga y `N` AMR en la formulación Euler--Lagrange de SP2 | elemento de `SE(2)^{N+1}`; `3(N+1)` coordenadas locales | modelo mecánico unificado; no integrado numéricamente en la campaña actual |
| `M,C,D,g,B,\tau,J_c,\lambda,A,\gamma_A,d` | Inercia, términos giroscópicos, disipación, gravedad, mapa/entrada de actuador, Jacobiano/reacción de contacto, restricción/multiplicador no holónomo y perturbación de la ecuación de Lagrange--d'Alembert conjunta | unidades SI compatibles con fuerza y par | modelo mecánico unificado SP2; parámetros físicos pendientes de identificación |
| `M_i,C_i,D_i,B_i,J_{c,i},\tau_i,f_i` | Términos de la forma Euler--Lagrange reducida del Pioneer: inercia, Coriolis, disipación, entrada, Jacobiano de contacto, pares de rueda y reacción | unidades SI compatibles con fuerza y par | interfaz de identificación física SP2; no identificada en la campaña actual |
| `\phi_i^C(q),J_C(q)` | Restricción bilateral de posición del pivote Cargo y su Jacobiano apilado | m; mapea velocidad conjunta a m/s de restricción | modelo nominal de contacto fijo SP2-C |
| `G_C(q)` | Matriz de agarre de la coalición `C` en la configuración `q` | mapea fuerzas de contacto a N y N·m | `grasp_matrix` |
| `\mathcal U_C` | Conjunto de fuerzas de contacto admisibles de la coalición `C` | N, con límites por actuador/contacto | `admissible_contact_forces` |
| `\mathcal W_C` | Conjunto físico completo de wrench realizables por la coalición `C`, unión sobre todos los repartos normales factibles | N, N·m | `achievable_wrench_set` ideal; no se identifica por completo en la campaña SP2 |
| `\widehat{\mathcal W}_C(n_C^\star)` | Sección de wrench usada por el oráculo secuencial SP2 tras fijar un reparto normal `n_C^\star`; no hereda necesariamente la monotonía de `\mathcal W_C` | N, N·m | `certify_supported_wrench` |
| `W_d^0,W_d,M_L,D_L,\widehat W_{ext}^0` | Wrench demandado en mundo y carga, inercia, amortiguamiento y wrench externo estimado en `W_d^0=M_La_L^0+D_L\xi_L-\widehat W_{ext}^0` | N, N·m y unidades dinámicas compatibles | `desired_wrench_world`, `desired_wrench_body`, `mass_matrix`, `damping_matrix`, `external_wrench_world` |
| `a,J_L,g_0,G_3` | Lado e inercia polar de la carga cuadrada, aceleración gravitatoria y matriz de agarre del ejemplo analítico de tres apoyos | m; kg·m²; m/s²; mapa de fuerzas a wrench | ejemplo nominal SP2; no es un escenario adicional de la campaña |
| `T_f,s,h(s),q_d,e,K_P,K_D,V` | Duración, tiempo normalizado, interpolante quíntico, pose deseada, error de pose envuelto, ganancias y función de Lyapunov del caso Cargo nominal | s; adimensional; m/rad; ganancias con unidades dinámicas; J | resultado formal local de SP2 bajo contacto fijo y realización exacta de wrench |
| `t_i,n_i,\bar t_i,\bar n_i` | Reacción planar, reacción normal y límites de tracción y soporte de SP2-C | N | `forces_n[i]`, `normal_forces_n[i]`, `max_drive_force_n[i]`, `max_normal_force_n[i]` |
| `B_i` | Base ortonormal que transforma la reacción planar del marco de la carga al marco local del contacto `i` | adimensional, matriz `2 x 2` | `contact_basis[i]` |
| `\mathcal T_i(n_i)` | Polígono tangencial conservador que reúne fricción `\mu_i n_i` y límite de tracción `\bar t_i` | subconjunto de `R^2`, N | restricciones de `certify_supported_wrench` |
| `\rho,s_W` | Utilización máxima del reparto y holgura de wrench usada para diagnosticar solicitudes inviables | adimensional; N y N·m | `utilization`, `desired_wrench-achieved_wrench` |
| `\widetilde h_i,\bar\tau_i` | Rumbo del robot en el marco de la carga y límite de par por motor | vector unitario, N·m | `load_frame_heading[i]`, `max_wheel_torque[i]` |
| `\pi^{N2}` | Escala adimensional de la demanda fuerza--momento usada únicamente en el barrido reducido N2; no representa masa ni soporte vertical | adimensional, positiva | `pressure` (nombre histórico de columna) |
| `\eta^{N2}` | Máxima utilización por componente minimizada en el LP planar reducido de N2 | adimensional, no negativa | `utilization` |
| `F_{g,i}^{xy},N_{g,i},\mu_{g,i}` | Fuerza planar, carga normal y coeficiente de fricción en rueda–suelo del robot `i` | N, N, adimensional | `ground_planar_force`, `driven_wheel_normal_load`, `ground_friction_coefficient` |
| `\mu_{L,i}` | Coeficiente de fricción carga--plataforma del contacto soportado; distinto de `\mu_{g,i}` | adimensional, positivo | `SupportContact.friction_coefficient` |
| `\bar t_i` | Límite planar efectivo previo al contacto carga--plataforma, mínimo entre rueda--suelo y motores | N, positivo | `SupportContact.max_drive_force_n` |
| `\alpha_i` | Fracción de la reacción rueda--suelo soportada por el eje motriz del AMR `i`; parámetro requerido por un modelo identificado, pero no medido en la campaña | adimensional, `(0,1]` | interfaz física pendiente; la campaña configura `SupportContact.max_drive_force_n` directamente |
| `L_{\mathcal C},r_{\mathrm{sup}}` | Longitud característica de la formación y norma infinita del residual vertical normalizado por peso y momento de referencia | m; adimensional | `length_scale`, `SupportCertificate.residual_norm` |
| `\upsilon_j(f,q,w_d)` | Utilización normalizada del recurso mecánico `j` | adimensional, no negativa | `mechanical_resource_utilization[j]` |
| `\upsilon_{\max}^\star,s_{\mathrm{mech}}^\star` | Máxima utilización mínima y margen mecánico definido como `1-\upsilon_{\max}^\star` | adimensional | `optimal_max_utilization`, `mechanical_certificate_margin` |
| `s_{\mathrm{path}},f_i^\star(s_{\mathrm{path}})` | Progreso normalizado de trayectoria y programa feed-forward de reacción asignado al robot `i` | `[0,1]`, N | `path_progress`, `feedforward_contact_force[i]` |
| `\delta=(\delta_x,\delta_y,\delta_\theta)` | Resolución completa del espacio de configuración `SE(2)` para un verificador numérico de escape | m, m, rad | `caging_grid_resolution` |
| `\delta_{xy},\mathcal F_{\delta_{xy}},\partial\mathcal F_{\delta_{xy}}` | Resolución traslacional, componente libre de la rejilla de traslaciones y su frontera en la sección ilustrativa de caging con orientación fijada | m; conjuntos discretos | `caging_xy_resolution`, `free_component`, `free_component_boundary` |
| `m_{\mathrm{cage}}^\delta` | Margen de confinamiento dependiente del modelo y de la resolución declarada | unidad definida por el verificador | `caging_margin_at_resolution` |
| `m_W(\widehat W_d),\Delta_W` | Distancia ponderada del wrench estimado al exterior de la región admisible y cota del error de estimación | adimensional tras aplicar `Q_W` | `estimated_wrench_margin`, `wrench_estimation_error_bound` |
| `r_{\mathrm{rob}}` | Razón entre error acotado y margen mecánico estimado, `\Delta_W/m_W(\widehat W_d)`; requiere `r_{\mathrm{rob}}<1` | adimensional | interfaz propuesta; no cuantificada en E3 |
| `{}^AT_B` | Transformación homogénea que expresa el marco `B` respecto al marco `A`; `m`, `o_i`, `B_i`, `L` y `s_{ik}` denotan mapa, odometría, base del robot, carga y slot | m, rad en `SE(2)` | cadena de marcos propuesta para SP2.N3 |
| `x_{i,k},u_{i,k},z_{i,k},M_i` | Pose planar del robot `i`, incremento encoder--IMU, barrido LiDAR y rejilla de ocupación usados por el SLAM local en la muestra `k` | m, rad; incremento en m/rad; alcance en m; ocupación probabilística | interfaz de estimación propuesta para SP2.N3; no ejecutada en la campaña |
| `N_{\mathrm{eff}},N_{\mathrm{thr}}` | Tamaño efectivo de muestra del RBPF y umbral de remuestreo | número de partículas | configuración pendiente del SLAM SP2.N3 |
| `X_i={}^mT_{B_i},Z_{ij},\Omega_{ij},\mathcal E_z` | Pose del robot en el mapa común, medida relativa `i--j`, matriz de información y aristas del grafo de poses; `X_1=I` fija la libertad de referencia | `SE(2)`; información en unidades inversas de la covarianza; conjunto de aristas | ajuste relativo propuesto para SP2.N3 |
| `{}^{B_i}\widehat T_{B_j}=\widehat X_i^{-1}\widehat X_j` | Pose relativa estimada del robot `j` expresada en la base del robot `i`, evaluada con marcas temporales compatibles | m, rad en `SE(2)` | realimentación relativa propuesta para la coalición |
| `p_i^\star,e_{ij}^{\mathrm{rig}}` | Posición mundial deseada del slot rígido `i` y error de geometría relativa entre los slots `i,j` | m, vectores en `R^2` | referencia y error de formación rígida propuestos para SP2.N3 |
| `\widehat x_{L,i}` | Copia local del estado estimado de la carga mantenida por el robot `i`; su consenso no implica por sí solo rigidez geométrica | componentes de pose y twist en m, rad, m/s y rad/s | `local_payload_estimate[i]` |
| `c_i^{\mathrm{ct}},T_{\mathrm{hold}}` | Certificado binario de contacto del robot `i` y tiempo mínimo durante el que deben cumplirse las guardas de pose, fuerza y contacto | binario; s | interfaz de docking propuesta; no validada en hardware |
| `y_i^F,b_i^F,H_i^F` | Lectura cruda, sesgo y matriz de calibración del transductor de esfuerzo del robot `i` | señal del sensor; N y N·m tras calibrar | interfaz de instrumentación propuesta |
| `\widehat W_i^L,{}^LT_{S_i}` | Wrench del contacto `i` expresado en la carga y transformación carga--sensor usada para transportarlo | N, N·m; transformación en `SE(2)` | estimación de wrench de contacto propuesta |
| `g_i^{E},f_{n,i}^{E},f_{t,i}^{E}` | Separación normal y fuerzas normal--tangencial del contacto unilateral de empuje SP2-E | m; N; N | interfaz dinámica propuesta; no validada en la campaña actual |
| `W_\Sigma^E=(F_\Sigma^E,\tau_\Sigma^E)` | Wrench planar resultante de los empujes activos, descompuesto en fuerza y momento alrededor del centro de la carga | N y N·m | interfaz explicativa de SP2-E; no estimada en la campaña actual |
| `n_i^{E},t_i^{E},\mu_i` | Direcciones unitarias normal--tangencial del contacto de empuje y coeficiente de fricción de Coulomb | vectores adimensionales; coeficiente adimensional | modelo de contacto propuesto para SP2-E |
| `G_{\mathcal A}^{E}` | Matriz que transforma las fuerzas de los empujadores activos en wrench planar de la carga | mapea N a N y N·m | matriz de contacto propuesta para SP2-E |
| `m,k` en SP2 físico | Índice de muestra digital e índice de carga, respectivamente; `m` no denota masa en esta formulación | enteros no negativos | `step_index`, `load_index` |
| `\mathrm{RMSE}_{p},\mathrm{RMSE}_{\theta}` | Errores cuadráticos medios de posición y rumbo; nunca se suman entre sí | m; rad | `rmse_position_m`, `rmse_yaw_rad` |
| `B_{\mathrm{gen}},B_{\mathrm{queue}},B_{\mathrm{del}},B_{\mathrm{drop}}` | Bytes ofrecidos al canal, admitidos en cola, entregados y descartados durante N3 | bytes por ejecución | `generated_bytes`, `queued_bytes`, `delivered_bytes`, `dropped_bytes` |
| `\tau_{\mathrm{age}},r_{\mathrm{del}}` | Edad media de los estados recibidos en línea y razón de mensajes entregados | s; adimensional `[0,1]` | `mean_age_s`, `delivery_ratio` |
| `\mathcal U_{\mathcal C}` | Conjunto ideal acoplado de órdenes que satisfaría las condiciones cinemáticas, mecánicas e informativas declaradas | m/s, rad/s, m/s², rad/s² | objetivo conceptual; no identificado por completo |
| `\widehat{\mathcal U}_{\mathcal C}` | Aproximación operacional calculada con la sección secuencial `\widehat{\mathcal W}_{\mathcal C}`, la guarda muestreada de obstáculo y la edad de información | m/s, rad/s, m/s², rad/s² | interfaz computada para SP3; no equivale a `\mathcal U_{\mathcal C}` |
| `r_{\mathcal C},\mathcal P_{\mathcal C}^{\mathrm{disc}}` | Radio y disco circunscrito conservador que cubren la carga y los robots acoplados del modelo reducido | m; subconjunto de `R^2` | `footprint.radius_m`, `footprint.model` |
| `\mathcal A_\alpha` | Cuadrícula finita de escalas positivas consultada para ejecución nominal y frenado; el cero se reserva a `HOLD` o ausencia de autoridad | subconjunto de `(0,1]` | `governor.nominal_scale_grid`, `governor.brake_scale_grid` |
| `\mathcal E` | Conjunto terminal definido por tolerancias independientes de posición, rumbo, velocidad lineal y velocidad angular, sostenidas durante un tiempo de permanencia | m, rad, m/s, rad/s y s por componente | `governor.terminal_criterion` |
| `\Pi_{\mathrm{mode}}` | Política discreta `EXECUTE/BRAKE/HOLD/UNCONTROLLED`; `HOLD` solo es válido con velocidad casi nula y guardas factibles | política discreta | `GovernorResult.status`, `failure_policy` |
| `\widehat{\mathcal V}_{\mathcal C}` | Contrato reducido efectivamente exportado a SP3: secciones cinemáticas muestreadas, márgenes observados, huella, cuadrículas, terminal y política de modos | tupla con unidades declaradas por campo | `results/sp2_canonical/SP2_HONORS_v3/operational_envelope.json` |
| `\mathcal U_{\mathcal C}^{fis},m_{\mathrm{fis}}` | Subconjunto y margen reservados para una planta dinámica independiente o hardware | mismas unidades que `\mathcal U_C`; margen normalizado | no identificado en la campaña SP2 actual |
| `a_{L,\ell,m}^0` | Aceleración nominal calculada por el AMR de referencia `\ell` con su historia local en las cinco leyes no predictivas | m/s², rad/s² | `requested_acceleration` para PD, PID, LQR, LQI y amortiguamiento |
| `\widetilde a_{L,m}^0` | Candidato nominal después de la proyección muestreada de obstáculo y antes de la revalidación conjunta de cada escala | m/s², rad/s² | salida de `cbf_acceleration_filter` entregada a `govern_acceleration` |
| `g_{\mathrm{info}}` | Guarda binaria de frescura: vale uno si la edad de la última estimación no supera `\bar\tau` | binario | `information_fresh` |
| `\sigma_m` | Modo operacional de la muestra `m`: `EXECUTE`, `BRAKE`, `HOLD` o `UNCONTROLLED` | variable discreta | `GovernorResult.status` |
| `\alpha^\star,\beta^\star` | Mayor escala factible de la orden nominal y de la orden de frenado, respectivamente, tras revalidación conjunta | adimensional, `[0,1]` | `GovernorResult.scale`, `GovernorResult.brake_scale` |
| `\mathcal A_C(x)` | Conjunto de aceleraciones cuya actualización de twist satisface N1 y cuyo wrench demandado pertenece a `\widehat{\mathcal W}_C` | m/s², rad/s² | conjunto consultado por `govern_acceleration` |
| `\Delta\alpha,\mathrm{TV}(\alpha)` | Paso de la cuadrícula del gobernador y variación total de su secuencia muestreada | adimensional | `governor_step`, `governor_total_variation` |
| `V_{\mathrm{cmd}},V_{\mathrm{real}}` | Inviabilidad de la orden solicitada y violación del estado/acción realmente integrados; no son intercambiables | indicadores binarios y fracciones temporales | `command_infeasible`, `command_infeasible_fraction`, `physical_violation`, `realized_violation_fraction` |
| `S_{\mathrm{fis}}` | Éxito físicamente admisible; exige éxito geométrico sin violación realizada N1/N2 | indicador binario | `physically_admissible_success` |
| `u_\ell^{nom},\kappa_\ell` | Acción producida por el controlador nominal de la familia `\ell` y su ley de realimentación | unidades del actuador declarado | `nominal_control`, `controller_family` |
| `\mathcal A_{\mathcal C}^{raw},\mathcal A_{\mathcal C}^{kin},\mathcal A_{\mathcal C}^{mech},\mathcal A_{\mathcal C}^{safe}` | Conjuntos anidados de entrada para la ablación N4: nominal, cinemático, mecánico y seguro | subconjuntos del espacio de control | `raw_input_set`, `kinematic_guard_set`, `mechanical_guard_set`, `safe_guard_set` |
| `h_o,\alpha_o` | Función de barrera del obstáculo `o` y función de clase K usada por el CBF--QP | unidad de `h_o` y tasa compatible | `obstacle_barrier`, `barrier_class_k` |
| `R_g` | Peso positivo definido de la proyección de la acción nominal sobre cada conjunto de guarda | normaliza las componentes del control | `guard_projection_weight` |
| `e_L,e_f,Q_L,Q_f` | Error de pose de carga, error de formación y sus matrices de escala/peso | componentes en m y rad; normas ponderadas | `load_pose_error`, `formation_error`, `load_error_weight`, `formation_error_weight` |
| `z,K_x,K_I` | Estado integral del error de pose y ganancias proporcional e integral del LQI aumentado | unidades compatibles con la entrada | `integral_error_state`, `lqi_state_gain`, `lqi_integral_gain` |
| `H,f_d,Q_H` | Horizonte discreto, modelo de predicción y peso terminal del NMPC | pasos; mapa de estado; peso cuadrático | `prediction_horizon`, `discrete_prediction_model`, `terminal_weight` |
| `P_{\ker G_{\mathcal C}},\rho_{int}` | Proyector ortogonal al núcleo de la matriz de agarre y fracción de reacción interna | operador adimensional; razón `[0,1]` salvo tolerancia | `internal_force_projector`, `internal_force_ratio` |
| `m_{\mathrm{kin}},m_{\mathrm{wrench}}` | Márgenes normalizados `1-max|dot(phi)|/bar(omega)` y `1-rho^star`; positivos si existe holgura, cero en frontera y negativos tras exceder el límite | adimensionales | `FormationCertificate.margin`, `MechanicalCertificate.friction_margin` |
| `J_{act}` | Trabajo absoluto integrado de los actuadores de rueda | J | `absolute_actuator_work` |
| `T_{CPU}^{p50},T_{CPU}^{p95},T_{CPU}^{max}` | Mediana, percentil 95 y máximo del tiempo de cálculo por actualización | s o ms | `cpu_time_p50`, `cpu_time_p95`, `cpu_time_max` |
| `\mathcal J_{\mathrm{wheel}}` | Esfuerzo cuadrático integrado de pares de rueda de la coalición | `(N·m)^2·s` | `integrated_squared_wheel_torque` |
| `B_{\mathrm{tune}},B_{\mathrm{N4}}` | Presupuestos de evaluaciones de ajuste N3 y de tiempo de pared N4 | evaluaciones, s u h | `tuning_evaluation_budget`, `n4_wall_time_budget` |
| `\mathcal S_k` | Catálogo de slots de soporte/contacto de la carga `k` en SP3 | conjunto finito | `load_slots[k]` |
| `\boldsymbol\lambda_k` | Esfuerzos concatenados de contacto de la coalición sobre la carga `k` | N | `contact_efforts[k]` |
| `\boldsymbol\lambda_k^\star(C_k)` | Solución del QP regularizado de esfuerzos para la coalición fija `C_k`; el residual se evalúa después en esta solución | N | `optimal_contact_efforts[k]` |
| `Q_W` | Matriz diagonal que normaliza fuerza y torque en el residual de wrench | unidades inversas cuadráticas por componente | `wrench_normalization` |
| `\rho_k^W` | Residual normalizado de wrench de la carga `k`; no confundir con preferencias `\rho_{ia}` | adimensional, `>=0` | `wrench_residual[k]` |
| `\rho_k^{W,\min}` | Mínimo del residual de wrench sobre el conjunto admisible, sin penalización de esfuerzo; define el certificado exacto del modelo | adimensional, `>=0` | valor de referencia analítico; distinto del residual del QP regularizado |
| `\epsilon_W` | Tolerancia del certificado planar de wrench | adimensional, positiva | `wrench_tolerance` |
| `a=(k,s)` | Acción continua robot--carga--slot del juego SP3; `a=0` indica inactividad | conjunto finito por robot | `action` |
| `\mathcal P_i,\mathcal P` | Acciones físicas robot--carga--slot disponibles para `i` y su unión global; excluyen la acción inactiva | conjuntos finitos | `physical_actions[i]`, `physical_actions` |
| `\mathcal A_i=\{0\}\cup\mathcal P_i` | Conjunto completo de acciones del robot `i`, incluida la inactividad | conjunto finito | `actions[i]` |
| `\rho_{ia}` | Preferencia continua del robot `i` por la acción `a` en SP3 | adimensional, simplex | `preferences[i,a]` |
| `\boldsymbol g_{ia}` | Columna de wrench normalizada aportada por `i` en la acción `a` | adimensional, vector en `R^3` | `normalized_wrench_column[i,a]` |
| `c_{ia},f_{ia},h_a` | Coste, pago y restricción de ocupación del juego SP3; `c_{i0}=0`, `f_{i0}=-\alpha\rho_{i0}` y `h_a` solo existe para `a\in\mathcal P` | adimensionales | `action_cost[i,a]`, `payoff[i,a]`, `slot_constraint[a]` |
| `\boldsymbol d_k` | Demanda planar de wrench normalizada de la carga `k` en el juego | adimensional, vector en `R^3` | `normalized_wrench_demand[k]` |
| `\boldsymbol y_k(\rho)` | Wrench normalizado agregado por preferencias para la carga `k` | adimensional, vector en `R^3` | `aggregate_wrench[k]` |
| `\pi_a` | Precio dual de congestión asociado a la ocupación del slot de la acción `a` | utilidad adimensional | `slot_price[a]` |
| `\alpha` | Regularización cuadrática del potencial de wrench SP3 | utilidad adimensional, positiva | `wrench_regularization` |
| `\mathcal A_k(t)` | Conjunto de contactos de empuje activos sobre la carga `k` | subconjunto de robots/contactos | `active_push_contacts[k]` |
| `s_{ik}` | Medición de proximidad del robot `i` respecto a la carga `k` | m o lectura calibrada | `proximity_measurement[i,k]` |
| `\mathcal C_k^{\mathrm{cage}}` | Conjunto de configuraciones que satisfacen el certificado geométrico de caging | subconjunto del espacio de configuración | `caging_feasible_set[k]` |
| `e_C^{\mathrm{form}}` | Error de formación rígida de la rama Cargo | m, rad o norma normalizada | `cargo_formation_error` |
| `\xi_i=(p_{x,i},p_{y,i},\theta_i,v_i,\omega_i)` | Estado de uniciclo dinámico usado en el docking de SP4 | m, rad, m/s, rad/s | `docking_state[i]` |
| `\eta_i=(\eta_i^v,\eta_i^\omega)` | Aceleración lineal y angular solicitada al uniciclo dinámico | m/s², rad/s² | `docking_acceleration[i]` |
| `\varphi_{i,L},\varphi_{i,R}` | Ángulos de las ruedas izquierda y derecha del robot diferencial | rad | `left_wheel_angle`, `right_wheel_angle` |
| `r_i^w,\ell_i^w,\bar\omega_{w,i}` | Radio de rueda, semivía y velocidad angular máxima de rueda del robot diferencial | m, m, rad/s | `wheel_radius`, `half_track`, `max_wheel_speed` |
| `v_{i,\parallel},d_i^{\mathrm{ICR}}` | Velocidad longitudinal firmada y distancia del pivote al centro instantáneo de rotación | m/s, m | `signed_longitudinal_speed`, `icr_distance` |
| `m_i,I_i` | Masa e inercia planar del robot durante docking | kg, kg·m² | `robot_mass`, `robot_yaw_inertia` |
| `\tau_{i,R},\tau_{i,L},\tau_i^{\max}` | Pares derecho, izquierdo y límite de rueda | N·m | `right_wheel_torque`, `left_wheel_torque`, `max_wheel_torque` |
| `\mathcal R_4,\ell` | Recursos de conflicto par a par y su índice en el juego de vivacidad SP4 | conjunto finito, índice | `conflict_resources`, `resource_id` |
| `b_{ia\ell}` | Ocupación normalizada del recurso `\ell` producida por la acción `a` del robot `i` | adimensional, `[0,1]` | `pairwise_features[i,a,l]` |
| `y_\ell(\rho)` | Ocupación agregada del recurso de conflicto `\ell` | adimensional, no negativa | `resource_occupancy[l]` |
| `c_{ia}^{(4)}` | Coste normalizado de progreso, prioridad y espera de la acción SP4 | coste adimensional | `docking_action_cost[i,a]` |
| `\beta_4,\alpha_4` | Peso de congestión y regularización fuerte del potencial SP4 | adimensionales; `\beta_4>=0`, `\alpha_4>0` | `congestion_weight`, `regularization` |
| `z_4^S` | Salida regulada estratégica de SP4: violación de recursos y residual proyectado | adimensional | `sp4_strategic_output` |
| `z_4^L` | Salida regulada física de SP4: error de pose, velocidad y residual de wrench | unidades mixtas declaradas por componente | `sp4_payload_output` |
| `W_k^d` | Wrench planar deseado por el servocontrol de pose de SP4 | N, N, N·m | `desired_payload_wrench[k]` |
| `K_P,K_D,D_k` | Ganancia de pose, ganancia derivativa y amortiguamiento físico de la carga en SP4 | unidades SI compatibles con fuerza/torque | `pose_gain`, `derivative_gain`, `payload_damping` |
| `\boldsymbol r_k^W` | Residual vectorial de realización de wrench en SP4, `G_{C_k}\lambda_k^\star-W_k^d` | N, N, N·m | `wrench_realization_residual[k]` |
| `\bar f_i^{C}` | Límite tangencial instantáneo usado por Cargo, `min(F_i^{max},\mu N_i^{med})`; un contacto perdido tiene límite cero | N | `ContactAllocation.contact_force_limit_n[i]` |
| `W_k^{alloc},W_k^{med}` | Wrench producido por el reparto acotado como setpoint y wrench agregado medido por sensores, ambos en marco de la carga; su igualdad no se presupone | N, N, N·m | `WheelCommand.allocated_wrench_body`, `Observation.measured_wrench_body` |
| `k_c,k_F,k_\tau` | Admitancias Cargo que convierten, respectivamente, fuerza de contacto objetivo, error de fuerza agregada y error de torque agregado en correcciones de velocidad | m/(N·s), m/(N·s), rad/(N·m·s) | `contact_force_admittance_m_s_per_n`, `wrench_force_admittance_m_s_per_n`, `wrench_torque_admittance_rad_s_per_n_m` |
| `\ell_0,S_q` | Longitud de referencia y escala `diag(\ell_0,\ell_0,1)` usadas para expresar la cota perturbada de SP4 en coordenadas traslación--rotación normalizadas | m; transformación de coordenadas | prueba perturbada de SP4; la cota numérica depende de `\ell_0` |
| `r_R` | Radio geométrico del robot usado en la huella compuesta de SP5-C | m | `robot_radius_m` |
| `r_k^C` | Radio conservador que cubre carga y robots acoplados de la coalición Cargo | m | `compound_radius` |
| `d_{\mathrm{safe}}` | Margen geométrico adicional exigido entre la huella compuesta y un obstáculo | m | `safety_margin_m` |
| `h_j(q_k^L)` | Holgura firmada conservadora respecto del obstáculo o frontera `j` en SP5 | m | `barrier_clearance[j]` |
| `n_j` | Normal unitaria desde el obstáculo `j` hacia el centro de la carga | adimensional, vector en `\mathbb R^2` | `barrier_normal[j]` |
| `\gamma_5` | Ganancia de relajación de la desigualdad de barrera de velocidad en SP5 | s\(^{-1}\) | `barrier_gain` |
| `a_{k,tr}^{fil},\alpha_k^{nom}` | Aceleración traslacional obtenida de la velocidad filtrada y aceleración angular nominal conservada en SP5 | m/s², rad/s² | `filtered_acceleration_from_velocity` |
| `\mathcal A_k` | Conjunto admisible para la aceleración traslacional filtrada; fue `\mathbb R^2` en la campaña archivada | m/s² | `max_translational_accel_mps2` cuando se acota |
| `W_k^{\mathrm{nom}},W_k^{\mathrm{fil}},W_k^{\mathrm{apl}}` | Wrench nominal, filtrado geométricamente y aplicado tras los límites de contacto | N, N, N·m | `raw_wrench`, `safe_wrench`, `exec_wrench` |
| `\varepsilon_{act,j,m}` | Margen de realización de la desigualdad de barrera tras reparto, saturación e integración | m, no negativo | diagnóstico derivable del estado `EXEC` |
| `I_5` | Número fijo de barridos de proyección cíclica del filtro SP5 | iteraciones por muestra | `barrier_projection_sweeps` |
| `z_{5,m}^{S}` | Residuo de barrera muestreado en la etapa `S in {RAW,SAFE,EXEC}` | m/s bajo la formulación de velocidad | `stage_barrier_residual` |
| `\mathcal R_k^6` | Reserva de robots alcanzable por la carga afectada en SP6-C | conjunto finito | `reserve_robots` |
| `n_R` | Tamaño de la reserva `|\mathcal R_k^6|` | entero positivo | `reserve_size` |
| `A_6` | Número de componentes del certificado de recuperación SP6-C | entero positivo; tres en la campaña | `resource_count` |
| `\boldsymbol d_k^6` | Déficit normalizado de soporte/fuerza/torque posterior al fallo | adimensional, `\mathbb R_+^{A_6}` | `requirement` |
| `\boldsymbol c_i^6` | Contribución normalizada del robot de reserva `i` al certificado | adimensional, `\mathbb R_+^{A_6}` | `capabilities[i]` |
| `x_i^6` | Decisión binaria de que el robot `i` se incorpora a la reparación | `{0,1}` | `profile[i]` |
| `\kappa_i^6` | Coste normalizado de movilización y cambio del robot `i` en SP6 | adimensional, positivo | `costs[i]` |
| `D_6(\boldsymbol x)` | Déficit residual ponderado del certificado SP6 | adimensional, no negativo | `weighted_deficit` |
| `K_6(\boldsymbol x)` | Coste agregado de la coalición de reparación | adimensional, no negativo | `mobilization_cost` |
| `\Phi_6(\boldsymbol x)` | Potencial exacto `-\lambda_6D_6-K_6` del juego SP6-C | utilidad adimensional | `potential` |
| `U_i^6` | Utilidad marginal o wonderful-life del robot `i` en SP6-C | utilidad adimensional | `marginal_utility` |
| `\lambda_6` | Penalización del déficit en el juego de recuperación | adimensional, positiva | `theorem_penalty` |
| `\delta_{\min}` | Menor reducción unilateral máxima de déficit entre perfiles deficitarios | adimensional, positiva si la reserva completa es factible | `delta_min` |
| `T_{\mathrm{safe}}` | Tiempo seguro disponible para restaurar el certificado | s | `deadline_s` |
| `\bar\tau_d,\bar\tau_a,\tau_s` | Cotas de detección, de cada ventana agregada desde detección/último cambio aceptado hasta el siguiente cambio aceptado o certificación (incluidas activaciones sin cambio), y de asentamiento | s | `detection_delay_s`, `accepted_change_window_s`, `settling_time_s` |
| `T_coal` | Tiempo de formación | s | `coalition_time` |
| `T_rec` | Tiempo de recuperación | s | `recovery_time` |
| `\mathcal A_7, A` | Conjunto y número de coaliciones tratadas como cuerpos compuestos en SP7-C | conjunto finito, entero positivo | `coalitions`, `n_coalitions` |
| `\mathcal R_i^7, r_i` | Catálogo finito de rutas y ruta cerrada elegida por la coalición `i` | conjunto finito, índice entero | `paths[i]`, `profile[i]` |
| `\mathcal E_7, \mathcal E_{ir_i}^7` | Recursos espaciales compartidos y recursos usados por la ruta de `i` | conjuntos finitos | `route_resources` |
| `b_{ir}^7` | Coste base normalizado de la ruta `r` para la coalición `i` | adimensional, no negativo | `base_costs[i,r]` |
| `n_e(\boldsymbol r)` | Número de rutas cerradas que usan el recurso `e` | entero no negativo | `resource_counts[e]` |
| `P_7(\boldsymbol r)` | Número de pares de coaliciones cuyas rutas comparten recursos | conteo entero no negativo | `conflict_pairs` |
| `\Phi_7(\boldsymbol r)` | Potencial exacto de rutas `-\sum_i b_{ir_i}^7-\lambda_7P_7` | utilidad adimensional | `potential` |
| `U_i^7` | Utilidad de ruta: coste propio más pares de congestión que involucran a `i` | utilidad adimensional | `utility` |
| `\lambda_7` | Penalización por par de rutas que comparte un recurso | adimensional, positiva | `penalty` |
| `\theta_7` | Umbral suficiente de penalización bajo accesibilidad unilateral de rutas | adimensional, no negativo o infinito | `conflict_free_penalty_threshold` |
| `O_i(t;r_i,\pi)` | Nodo ocupado por la coalición `i` al ejecutar una ruta y orden de prioridad | nodo del grafo de configuraciones | `positions[i]` |
| `H_7` | Horizonte digital de la ejecución de tráfico SP7 | pasos muestreados | `horizon_steps` |
| `w_i, P_i` | Tiempo de espera y prioridad de misión usados para arbitrar una zona | pasos; prioridad adimensional | `waiting[i]`, `priorities[i]` |
| `\mathcal A_8, A` | Conjunto y número de coaliciones que seleccionan rutas en SP8; en la campaña cada carga usa dos robots y (N=2A) | conjunto finito, entero positivo | `coalitions`, `n_coalitions` |
| `A^C_{ij}` | Adyacencia estática y no dirigida del grafo de comunicación de SP8 | binaria | `adjacency[i,j]` |
| `P_8(\boldsymbol r),P_8^G(\boldsymbol r)` | Pares globales de rutas en conflicto y subconjunto visible a través de aristas de comunicación | conteos enteros no negativos | `global_conflict_pairs`, `visible_conflict_pairs` |
| `\Phi_8^G(\boldsymbol r)` | Potencial exacto del juego de rutas visible por la red | utilidad adimensional | `network_potential` |
| `U_i^8` | Utilidad local de ruta que penaliza costes propios y conflictos vecinales visibles | utilidad adimensional | `visible_utility` |
| `v_i^8` | Versión monótona de la intención de ruta transmitida por la coalición (i) | entero no negativo | `versions[i]` |
| `s` | Número de retransmisiones de un estado congelado en la cota (p_{\mathrm{loss}}^s) | conteo entero no negativo | `transmissions` |
| `B_{\mathrm{msg}}` | Tamaño contable de un mensaje ruta--versión en SP8 | bytes; 32 en la campaña | `message_bytes` |
| `J` | Coste/función social de referencia | declarar | `social_cost` |
| `gap` | Gap frente a oráculo | % o razón | `optimality_gap` |
| `p` | Índice de trabajo bibliográfico en la rúbrica de la Figura 3 | conjunto finito de trabajos verificados | `paper_key` |
| `\chi_p^{\mathrm{dec}}` | Autonomía de la decisión en ejecución del trabajo `p` | ordinal en `{0,0.5,1}` | `decision_autonomy_score` |
| `\chi_p^{\mathrm{loc}}` | Localidad de la información de ejecución del trabajo `p` | ordinal en `{0,0.5,1}` | `information_locality_score` |
| `\chi_p^{\mathrm{learn}}` | Dependencia del componente aprendido en la decisión primaria de `p` | ordinal en `{0,0.5,1}` | `learning_dependence_score` |
| `\chi_p^{\mathrm{exp}}` | Explicitud del mecanismo primario de `p` | ordinal en `{0,0.5,1}` | `explicitness_score` |
| `x_p, y_p` | Coordenadas nominales del trabajo `p` en la Figura 3 | adimensionales, `[-1,1]` | `methodological_map_coordinate` |
| `u_p` | Vector de coordenadas nominales $(x_p,y_p)$ del trabajo `p` | adimensional, `[-1,1]^2` | `methodological_map_nominal_vector` |
| `z_p` | Coordenada de presentación agrupada del trabajo `p`, obtenida mediante estrés anclado | adimensional, `[-1.10,1.10]^2` | `methodological_map_display_coordinate` |
| `F_p` | Familia primaria del mecanismo de `p`: juego/mercado, búsqueda/heurística, control/consenso o política aprendida | conjunto finito `{G,H,C,L}` | `primary_method_family` |
| `S_p` | Subproblemas SP0--SP8 cubiertos directamente por el trabajo `p` según el ledger | subconjunto finito | `paper_sp_scope` |
| `d_{\mathrm{met}}(p,q)` | Distancia metodológica normalizada entre los trabajos `p` y `q`, calculada con los indicadores de la Figura 3 | adimensional, `[0,1]` | `methodological_distance` |
| `d_{\mathrm{fam}}(p,q)` | Distancia binaria entre familias primarias de mecanismo | binaria en `{0,1}` | `method_family_distance` |
| `d_{\mathrm{SP}}(p,q)` | Distancia de Jaccard entre los conjuntos de SP cubiertos por `p` y `q` | adimensional, `[0,1]` | `sp_scope_distance` |
| `D(p,q)` | Distancia compuesta usada para agrupar la presentación de la Figura 3 | adimensional, `[0,1]` | `composite_paper_distance` |
| `a=(k,h)` | Acción SP1-GEO que asigna un robot a la carga `k` y al slot geométrico `h`; la inactividad es una acción separada | par de índices discretos | `load_index`, `slot_index`, `action_by_robot` |
| `E_{ikh}^{s}` | Contribución del robot `i` a la carga-slot `(k,h)` bajo la señal `s`; `s=scalar` usa capacidad efectiva y `s=physical` usa recursos alineados no negativos | vector con unidades declaradas por componente | `scalar_contributions`, `physical_contributions` |
| `S_k^s(\rho)` | Agregado de contribuciones de señal para la carga `k` | mismas unidades que `E_{ikh}^{s}` | `aggregate_signal` |
| `\Phi_\tau^s(\rho)` | Potencial cóncavo SP1-GEO con coste y entropía local de inactividad | utilidad adimensional | `signal_potential` |
| `\rho_k^{GEO}` | Residual normalizado del ajuste de wrench firmado de la carga `k` | razón adimensional no negativa | `wrench_residual` |
| `m_k^{GEO}` | Margen a la tolerancia nominal de wrench, `\varepsilon_k-\rho_k^{GEO}`; no es margen robusto frente a incertidumbre | razón adimensional | `wrench_margin` |
| `RAW,CERTIFIED,RECOVERED` | Salida entera nativa, subconjunto certificado y resultado de la recuperación común de SP1-GEO | estados discretos de cierre | `closure_stage` |
| `b_{i,e}` | Belief candidato del robot `i` sobre el hecho `e`: valor estimado, incertidumbre opcional, fuente, versión, marca temporal, saltos y confianza | tupla heterogénea; cada componente conserva su propia unidad | `beliefs[robot_id][fact_id]` |
| `B_i^{\mathrm P},B_i^{\mathrm S},\mathcal B_i` | Conjuntos de beliefs físico y estratégico, y estado epistemológico candidato `(B_i^P,B_i^S,D_i)` | conjuntos finitos de registros | `physical_beliefs`, `strategic_beliefs`, `belief_state` |
| `\operatorname{src}_e,\operatorname{seq}_e,t_e,h_{i,e},c_{i,e}` | Fuente, versión monotónica, marca temporal, saltos y confianza del hecho `e` visto por `i` | identificador; entero no negativo; s; entero no negativo; `[0,1]` | `source`, `sequence`, `timestamp_s`, `hop_count`, `confidence` |
| `D_{i\to j,s},\Delta B_{i\to j}` | Versión de la fuente `s` que `i` estima reconocida por `j` y delta candidato para el enlace `i→j` | entero no negativo; conjunto de registros | `neighbor_digest`, `belief_delta` |
| `\widehat{\mathcal K}_i(e),\mathcal C_e,\gamma_i(e)` | Cobertura estimada, conjunto de agentes relevantes y fracción de cobertura de un hecho | conjuntos finitos; razón en `[0,1]` | `acknowledged_agents`, `relevant_agents`, `coverage_ratio` |
| `\epsilon_i(d),L_i(d),U_i(d),C_e^+` | Envolvente de incertidumbre, cotas de valor y coste de transición de una guardia de commit candidata | misma unidad normalizada que el valor `V(d)` | `value_uncertainty`, `lower_value`, `upper_value`, `transition_cost` |

## Reglas de notación

- No usar el mismo símbolo para masa, número de robots y mensaje.
- No mezclar `n_k` como requisito de cardinalidad con capacidad mecánica; usar `r_k` para requisitos multidimensionales.
- Definir si `x_ik` es binaria, fracción poblacional, probabilidad o estimación. No alternar interpretaciones.
- En la formulación común, usar `rho_ik` para preferencia continua y reservar `x_ik` para la decisión binaria cerrada.
- Reservar `x_k` para masa poblacional agregada y `x_ik` para asignación individual; no intercambiarlas.
- Elegir una convención de marcos de referencia para poses y wrench y mantenerla.
- Toda magnitud física debe indicar SI o una conversión explícita.
