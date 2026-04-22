# Infraestructura Azure

Esta carpeta deja preparada la infraestructura base para migrar la aplicacion a Azure sin apagar Render.

## Recursos incluidos

- `Azure App Service (Linux)`
- `Azure App Service Plan`
- `Azure Database for PostgreSQL Flexible Server`
- `Azure Blob Storage`

## Archivo principal

- [main.bicep](C:/Users/deiby/Downloads/enturnamiento-vehiculos/infra/azure/main.bicep)

## Recomendacion de despliegue

1. Crear un `Resource Group`
2. Desplegar el Bicep
3. Publicar la app desde GitHub Actions
4. Restaurar la base de datos en Azure PostgreSQL
5. Validar la app en Azure
6. Hacer corte controlado desde Render

## Variables importantes despues del despliegue

- `DATABASE_URL`
- `UPLOADS_DIR`
- `FCM_SERVER_KEY` si usas notificaciones push

## Nota

El Bicep deja la base y el almacenamiento creados, pero la migracion de datos actuales debe hacerse aparte:

- Base de datos: `pg_dump` / `pg_restore`
- Evidencias: copiar desde el almacenamiento actual al contenedor Blob

## Siguiente fase recomendada

Para una operacion empresarial mas robusta, conviene que en una segunda fase la aplicacion deje de guardar evidencias en disco local y pase a guardar directamente en Azure Blob Storage.
