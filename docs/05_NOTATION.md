# 05 — Registro de notación

Mantener una notación única en código, ecuaciones, figuras y memoria. Esta tabla es inicial y debe adaptarse antes de fijar las formulaciones.

| Símbolo | Significado | Dominio/unidad | Código sugerido |
|---|---|---|---|
| `N` | Número de robots | entero positivo | `n_robots` |
| `K` | Número de cargas/tareas | entero positivo | `n_loads` |
| `i` | Índice de robot | `{1,…,N}` | `robot_id` |
| `k` | Índice de carga/tarea | `{1,…,K}` | `load_id` |
| `q_i` | Estado del robot | posición/orientación o estado dinámico | `robot_state[i]` |
| `p_i` | Posición del robot | m | `robot_position[i]` |
| `theta_i` | Orientación del robot | rad | `robot_heading[i]` |
| `u_i` | Entrada de control | según modelo | `control[i]` |
| `v_i, omega_i` | Velocidad lineal/angular | m/s, rad/s | `linear_velocity`, `angular_velocity` |
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
| `G_C(q)` | Matriz de agarre de la coalición `C` en la configuración `q` | mapea fuerzas de contacto a N y N·m | `grasp_matrix` |
| `\mathcal U_C` | Conjunto de fuerzas de contacto admisibles de la coalición `C` | N, con límites por actuador/contacto | `admissible_contact_forces` |
| `\mathcal W_C` | Conjunto de wrench realizables por la coalición `C` | N, N·m | `achievable_wrench_set` |
| `\mathcal S_k` | Catálogo de slots de soporte/contacto de la carga `k` en SP3 | conjunto finito | `load_slots[k]` |
| `\boldsymbol\lambda_k` | Esfuerzos concatenados de contacto de la coalición sobre la carga `k` | N | `contact_efforts[k]` |
| `\boldsymbol\lambda_k^\star(C_k)` | Solución del QP regularizado de esfuerzos para la coalición fija `C_k`; el residual se evalúa después en esta solución | N | `optimal_contact_efforts[k]` |
| `Q_W` | Matriz diagonal que normaliza fuerza y torque en el residual de wrench | unidades inversas cuadráticas por componente | `wrench_normalization` |
| `\rho_k^W` | Residual normalizado de wrench de la carga `k`; no confundir con preferencias `\rho_{ia}` | adimensional, `>=0` | `wrench_residual[k]` |
| `\epsilon_W` | Tolerancia del certificado planar de wrench | adimensional, positiva | `wrench_tolerance` |
| `a=(k,s)` | Acción continua robot--carga--slot del juego SP3; `a=0` indica inactividad | conjunto finito por robot | `action` |
| `\rho_{ia}` | Preferencia continua del robot `i` por la acción `a` en SP3 | adimensional, simplex | `preferences[i,a]` |
| `\boldsymbol g_{ia}` | Columna de wrench normalizada aportada por `i` en la acción `a` | adimensional, vector en `R^3` | `normalized_wrench_column[i,a]` |
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
| `r_i^w,\ell_i^w` | Radio de rueda y semivía del robot diferencial | m | `wheel_radius`, `half_track` |
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
| `\bar\tau_d,\bar\tau_a,\tau_s` | Cotas de detección, intervalo entre mejoras aceptadas y asentamiento | s | `detection_delay_s`, `event_interval_s`, `settling_time_s` |
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

## Reglas de notación

- No usar el mismo símbolo para masa, número de robots y mensaje.
- No mezclar `n_k` como requisito de cardinalidad con capacidad mecánica; usar `r_k` para requisitos multidimensionales.
- Definir si `x_ik` es binaria, fracción poblacional, probabilidad o estimación. No alternar interpretaciones.
- En la formulación común, usar `rho_ik` para preferencia continua y reservar `x_ik` para la decisión binaria cerrada.
- Reservar `x_k` para masa poblacional agregada y `x_ik` para asignación individual; no intercambiarlas.
- Elegir una convención de marcos de referencia para poses y wrench y mantenerla.
- Toda magnitud física debe indicar SI o una conversión explícita.
