# Lista de control de entrega

## Controles locales completados

- [x] La rama de trabajo es `main` y el contenido científico de la etapa 4 está versionado.
- [x] La memoria compila con LuaLaTeX + Biber.
- [x] El PDF tiene formato A4, 93 páginas y hash registrado.
- [x] El cuerpo principal ocupa 72 páginas y los anexos 8 páginas.
- [x] No quedan referencias o citas indefinidas, cajas desbordadas ni glifos ausentes.
- [x] La suite automatizada registra 350 pruebas superadas y 0 fallos.
- [x] La auditoría de afirmaciones no registra hallazgos críticos.
- [x] La auditoría local de citas no registra claves sin resolver.
- [x] Las afirmaciones principales están enlazadas con artefactos y estimandos canónicos.
- [x] El PDF de entrega coincide con la fuente canónica validada.

## Controles externos pendientes

- [ ] Generar y archivar el informe institucional de similitud.
- [ ] Revisar cualquier coincidencia señalada y documentar su resolución.
- [ ] Obtener una verificación bibliográfica independiente si la normativa o el tutor la requieren.
- [ ] Confirmar con el tutor título, autoría, convocatoria y versión definitiva.
- [ ] Comprobar el nombre de archivo, límite de tamaño y metadatos exigidos por el portal.
- [ ] Subir el PDF y verificar que el portal lo renderiza completo.
- [ ] Conservar el justificante de entrega y la versión exacta remitida.

## Regla de bloqueo

Si cambia cualquier archivo de la fuente canónica, el PDF actual deja de considerarse final. En ese caso hay que:

1. ejecutar `make report-pdf`;
2. repetir la puerta *submit-ready* y las auditorías afectadas;
3. actualizar el PDF y las copias congeladas de este directorio;
4. recalcular `PACKAGE_HASHES.sha256` y `DELIVERY_MANIFEST.json`;
5. repetir la revisión visual de las páginas modificadas.

## Criterio de cierre

El paquete puede llamarse «entregado» solo después de completar los controles externos aplicables y conservar el justificante. La calificación y la aprobación corresponden exclusivamente al tribunal o a la autoridad académica competente.
