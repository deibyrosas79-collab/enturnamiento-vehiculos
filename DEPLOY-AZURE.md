# Despliegue a Azure

Esta guia deja la aplicacion funcionando en paralelo con Render mientras se valida Azure.

## Arquitectura recomendada

- `Azure App Service (Linux)` para la aplicacion web y API.
- `Azure Database for PostgreSQL Flexible Server` para la base de datos principal.
- `Azure Blob Storage` para selfies, firmas y evidencias fotograficas.

## Recomendacion de inicio

Para una primera puesta en marcha empresarial, recomiendo este tamano inicial:

- `App Service Basic B1` o `Standard S1`
- `PostgreSQL Flexible Server Burstable B1ms`
- `Blob Storage Hot LRS`

Si la empresa ya va a usar el sistema en operacion diaria, el mejor equilibrio suele ser `Standard S1` para la app y `Burstable B1ms` o superior para PostgreSQL.

## Estimacion de costo mensual

El costo exacto depende de la region, almacenamiento y trafico. Como referencia practica:

- `App Service Basic B1`: aproximadamente `USD 13 a 20 / mes`
- `App Service Standard S1`: aproximadamente `USD 55 a 80 / mes`
- `Azure Database for PostgreSQL Flexible Server (B1ms + almacenamiento inicial)`: aproximadamente `USD 20 a 45 / mes`
- `Blob Storage` para fotos y firmas: aproximadamente `USD 1 a 8 / mes`

Escenario recomendado para arrancar bien:

- `B1 + PostgreSQL + Blob`: aproximadamente `USD 35 a 70 / mes`
- `S1 + PostgreSQL + Blob`: aproximadamente `USD 75 a 130 / mes`

Estas cifras son estimadas a partir de los servicios oficiales de Azure y pueden variar segun region y consumo.

Fuentes oficiales:

- [Azure App Service pricing](https://azure.microsoft.com/pricing/details/app-service/linux/)
- [Azure Database for PostgreSQL pricing](https://azure.microsoft.com/pricing/details/postgresql/flexible-server/)
- [Azure Blob Storage pricing](https://azure.microsoft.com/pricing/details/storage/blobs/)
- [Azure App Service overview](https://learn.microsoft.com/azure/app-service/overview)

## Recursos a crear en Azure

1. `Resource Group`
   - Nombre sugerido: `rg-enturnamiento-prod`

2. `App Service Plan`
   - Nombre sugerido: `plan-enturnamiento-prod`
   - Linux
   - SKU sugerido inicial: `B1` o `S1`

3. `Web App`
   - Nombre sugerido: `enturnamiento-vehiculos-prod`
   - Runtime: `Python 3.12`
   - Startup command: `python server.py`

4. `Azure Database for PostgreSQL Flexible Server`
   - Nombre sugerido: `psql-enturnamiento-prod`

5. `Storage Account`
   - Nombre sugerido: `stenturnamientoprod`

6. `Blob Container`
   - Nombre sugerido: `evidencias`

## Variables de entorno recomendadas en Azure App Service

- `HOST=0.0.0.0`
- `PORT=8000`
- `DATABASE_URL=<cadena PostgreSQL Azure>`
- `UPLOADS_DIR=/home/site/wwwroot/data/uploads`
- `FCM_SERVER_KEY=<si se usa notificacion push>`

## Estrategia segura de migracion

1. Mantener Render activo.
2. Crear Azure y dejarlo en ambiente de pruebas.
3. Exportar la base actual.
4. Restaurar esa base en Azure PostgreSQL.
5. Validar login, QR, checklist, APK, PDF y reportes.
6. Hacer corte controlado.
7. Dejar Render unos dias como respaldo temporal.

## Migracion de base de datos

Opciones recomendadas:

- `pg_dump` + `pg_restore` si el tamano es pequeno o mediano.
- `Azure Database Migration Service` si quieres una ruta mas administrada.

Fuente oficial:

- [Azure Database Migration Service for PostgreSQL](https://learn.microsoft.com/azure/postgresql/migrate/concepts-single-to-flexible)

## Cambio de dominio

Cuando Azure este validado:

1. Probar en la URL temporal de Azure.
2. Actualizar la APK para apuntar al dominio nuevo.
3. Mover dominio principal o usar subdominio corporativo.
4. Dejar Render solo como contingencia temporal.

## Importante antes del corte final

Hoy la aplicacion sigue guardando evidencias en sistema de archivos local del servidor. Para una migracion empresarial completa conviene hacer una segunda fase:

- mover evidencias a `Azure Blob Storage`
- dejar la base de datos en Azure PostgreSQL
- dejar App Service como capa web

Eso evita depender del disco local del servidor web.
