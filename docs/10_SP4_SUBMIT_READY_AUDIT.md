# Auditoría submit-ready de SP4

Fecha de cierre: 2026-07-16.

## Dictamen

SP4 queda **submit-ready con nivel de evidencia Cargo B (parcial)** para dos capas simuladas y explícitamente separadas: (i) atraque de uniciclos dinámicos a poses de contacto fijas y (ii) transporte planar de una carga rígida de orden reducido con contactos ya establecidos. No se presenta como validación física extremo a extremo, prueba en hardware ni acreditación de la rama empuje/caging.

## Contribuciones propias acreditadas

1. Juego distribuido de vivacidad con recursos de conflicto por pares, regularización fuerte y precio primal--dual compartido.
2. Servorregulación de pose de la carga mediante wrench deseado y reparto acotado de fuerzas de contacto.
3. Proposición de potencial/convexidad fuerte: bajo una instantánea congelada, el minimizador es único y coincide con el equilibrio variacional de la relajación continua.
4. Proposición de estabilidad: con wrench realizable, el equilibrio de pose es localmente asintóticamente estable; con residual, se obtiene una cota explícita de disipación perturbada.

Las demostraciones completas están en `thesis/sections/appendices/06-sp4-proofs.tex`. No se extienden al cierre entero, grafo cambiante, contacto conmutado, saturación persistente ni ejecución digital global.

## Evidencia empírica

- **Docking v3:** 108 mundos pareados, 11 métodos y 1188 ejecuciones. Replicator+CBF mejora el éxito seguro frente a CBF en 0.09259, IC 95 % [0.03704, 0.15741], con ajuste de Holm; persiste una tasa de timeout de 0.7315.
- **Reparación v4:** 12 mundos pareados. Distributed PD y Replicator+HOCBF obtienen 12/12 éxitos seguros, sin violación de barrera EXEC ni saturación de torque; el tamaño es descriptivo y no autoriza generalización amplia.
- **Transporte open_nominal:** 18 mundos pareados por método. Los cuatro controladores alcanzan el objetivo. Pose PD tarda 28.20 s y consume 213.7 J; Hamiltonian tarda 32.57 s y consume 198.5 J. El contraste Hamiltonian--Pose PD es +4.375 s, IC 95 % [4.350, 4.400], y -15.16 J, IC 95 % [-15.24, -15.08].
- **CoppeliaSim:** replay cinemático reproducible, no validación dinámica independiente.

Los artefactos se regeneran con:

```powershell
$env:PYTHONPATH='src'
python -m viu_mrob_tfm.cli.run_sp4_evidence --config experiments/configs/sp4_transport_evidence.yaml
```

## Verificaciones de cierre

- Auditoría de evidencia: `passed`, 13/13 comprobaciones.
- Regresión focal y SP0--SP3: 26 pruebas superadas.
- Compilación completa: correcta, sin citas ni referencias indefinidas.
- Revisión visual: páginas 80--86 y anexo SP4 126--128 sin recortes ni solapamientos.
- PDF final: 128 páginas; anexos 110--128, 19 páginas, dentro del máximo VIU de 20.
- Referencias de SP4: claves presentes en `thesis/references.bib` y marcadas `VERIFICADA` en `references/LITERATURE_LEDGER.md`.

## Límite que debe mantenerse en defensa

La evidencia no muestra todavía que reclutamiento, atraque, cierre de contacto y transporte operen como una única ejecución dinámica extremo a extremo. Esa afirmación permanece pendiente; SP4 acredita por separado el acoplamiento y el servolazo de transporte planar.
