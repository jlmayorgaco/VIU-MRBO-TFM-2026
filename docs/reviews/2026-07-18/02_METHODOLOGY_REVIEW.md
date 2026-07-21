# Informe metodológico y estadístico independiente

**Recomendación:** revisión mayor.

## Fortalezas

- La unidad experimental es el mundo/escenario--semilla; robots y muestras temporales no se inflan como réplicas.
- Tratamientos pareados, fallos en denominador, hashes y auditorías en campañas recientes.
- Uso adecuado de McNemar, Wilcoxon, intervalos, Holm y agregación para evitar pseudorreplicación en Cargo y SP8.
- Resultados negativos y distinciones entre certificado, recuperación temporal, exclusión lógica y seguridad continua.

## Debilidades mayores

1. SP2--SP4 solo permiten reanálisis de observaciones archivadas; no regeneración extremo a extremo.
2. SP4-v4 usa 12 mundos y el transporte 18. La etiqueta confirmatoria excede la fuerza de esos tamaños.
3. La ablación Cargo `no_physical_guard` elimina certificado, waypoint y filtro. Solo identifica el bloque conjunto.
4. SP1 es desarrollo, explora varios valores de beta y reporta inferencia sin una familia Holm claramente declarada ni holdout para beta igual a 2.
5. Los agregados de SP5 dependen de la mezcla artificial de escenarios; faltan pesos objetivo, márgenes prácticos e interacción/estratificación.

## Pruebas mínimas sugeridas

- Recuperar/versionar generadores SP2--SP4 o reclasificar como reanálisis retrospectivo.
- Separar ablaciones Cargo; idealmente diseño factorial o *leave-one-component-out*.
- Ampliar SP4 o retirar la etiqueta confirmatoria.
- Aplicar Holm y holdout a SP1.
- Añadir resultados estratificados y márgenes de relevancia práctica.
- Incluir SHA, configuración y entorno en manifiestos finales.
