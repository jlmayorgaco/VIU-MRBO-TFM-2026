# Ley de control Cargo v2

## Alcance

Las tres guardas (`scalar_capacity`, `planar_lsq` y
`supported_wrench_wheels`) clasifican el mismo mundo físico. No seleccionan ni
modifican el controlador. Toda ejecución usa
`cargo_pose_wrench_admittance_wheel_v2` y el único comando enviado al
simulador es la velocidad angular objetivo de cada rueda, en rad/s.

La cadena implementada es

```text
error de pose -> aceleración limitada -> wrench de referencia
              -> LSQ acotado de contactos -> admitancia -> ruedas
```

## Demanda de wrench

El PD de pose produce una aceleración planar en marco mundo,

\[
a_d=\operatorname{sat}_{\bar a}
\bigl(K_P(q_d-q)-K_D\nu\bigr),
\]

con ganancias traslacionales en s⁻² y s⁻¹, y sus equivalentes angulares. La
velocidad nominal es la integración explícita muestreada
`nu_d = sat(nu + a_d*dt)`. Para la masa, inercia y amortiguamientos declarados,
la referencia en el marco de la carga es

\[
W_d=R(q)^{\mathsf T}\bigl(Ma_d+D\nu_d\bigr),
\]

donde sus componentes tienen unidades N, N y N·m. Esta igualdad define una
demanda del modelo; no afirma que los contactos la realicen exactamente.

## Reparto acotado

Para cada contacto activo se calcula

\[
\bar f_i=\min\{F_i^{\max},\,\mu N_i^{\mathrm{med}}\}.
\]

El límite normal procede del sensor en esa muestra. Un contacto inactivo,
perdido o sin normal positiva recibe fuerza objetivo nula. La asignación
resuelve un mínimo cuadrado normalizado y regularizado,

\[
\lambda^\star=\arg\min_\lambda
\lVert Q_W^{1/2}(G\lambda-W_d)\rVert_2^2
+\varepsilon\lVert\lambda/F^{\max}\rVert_2^2,
\]

con cotas por componente
`|lambda_ix|, |lambda_iy| <= bar_f_i/sqrt(2)`. El cuadrado inscrito es
conservador: garantiza `norm(lambda_i) <= bar_f_i` sin convertir el LSQ en una
afirmación de cono de fricción exacto. Se registran el setpoint por contacto,
el wrench asignado `G*lambda`, el residual firmado `G*lambda-W_d`, su norma
adimensional, la utilización y las saturaciones.

## Admitancia y ruedas

La diferencia entre el wrench asignado y el medido se convierte en una
corrección limitada de twist mediante ganancias con unidades explícitas:

\[
\delta\nu_b=\operatorname{sat}
\left(\operatorname{diag}(k_F,k_F,k_\tau)
[G\lambda^\star-W^{\mathrm{med}}]\right),
\]

con `k_F` en m/(N·s) y `k_tau` en rad/(N·m·s). Cada velocidad de anclaje suma
además `k_c*lambda_i`, con `k_c` en m/(N·s), antes de la cinemática inversa del
Pioneer. Así la asignación influye en los comandos, pero el servo de velocidad,
la estructura bilateral y la física MuJoCo determinan el esfuerzo realizado.

## Frontera de evidencia

El LSQ es un reparto de setpoints, no un control directo de fuerza. La
realización se juzga con sensores, residual de wrench, fuerza equivalente de
rueda, contacto, deslizamiento y estado terminal. Un residual distinto de cero,
una saturación o una pérdida de contacto permanece en los datos. Sin superar
los gates físicos, esta ley solo constituye infraestructura candidata y no
evidencia de estabilidad, seguridad, transferencia a hardware ni gemelo
digital. El prototipo calcula la referencia con pose de carga y wrench agregado;
por tanto, esta campaña tampoco demuestra una implementación distribuida
extremo a extremo del lazo de control.

La elegibilidad confirmatoria no se obtiene por completar el diseño ni por
aprobar únicamente la calibración. Todas las corridas primarias y de
sensibilidad deben terminar con `physical_success=true` y con gates positivos
de contacto, deslizamiento, colisión y estado terminal, además de los gates de
escena y calibración. Un solo fallo conserva la afirmación comparativa como
pendiente.
