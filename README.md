# Enturnamiento de Vehiculos

Aplicacion web para logistica y calidad con registro interno, registro publico por QR, geocerca GPS, checklist con evidencias y reportes operativos.

## Modulos principales

- Panel interno para logistica y calidad
- Registro de conductores por QR en [driver.html](/C:/Users/deiby/Downloads/enturnamiento-vehiculos/driver.html)
- Roles `LOGISTICA` y `CALIDAD`
- Checklist de calidad con fotos
- Reportes de rechazo, motivos y compatibilidad de carga
- App Android nativa inicial para calidad en [android-quality-app](/C:/Users/deiby/Downloads/enturnamiento-vehiculos/android-quality-app)

## Ejecucion local

```powershell
cd C:\Users\deiby\Downloads\enturnamiento-vehiculos
python server.py
```

Luego abre [http://localhost:8000](http://localhost:8000).

## Usuarios iniciales

- `logistica` / `Logistica2026!`
- `calidad` / `Calidad2026!`

## Rutas utiles

- Panel interno: `/`
- Registro QR: `/driver.html`
- Health check: `/healthz`

## Configuracion de GPS

Para activar el registro con geocerca:

1. Ingresa con `logistica`.
2. Abre `Configuracion`.
3. Registra nombre de sede, latitud, longitud y radio permitido.

## Despliegue

El proyecto ya incluye:

- [render.yaml](/C:/Users/deiby/Downloads/enturnamiento-vehiculos/render.yaml)
- [Dockerfile](/C:/Users/deiby/Downloads/enturnamiento-vehiculos/Dockerfile)
- [.dockerignore](/C:/Users/deiby/Downloads/enturnamiento-vehiculos/.dockerignore)
- [.env.example](/C:/Users/deiby/Downloads/enturnamiento-vehiculos/.env.example)
- [GITHUB-PUBLISH.md](/C:/Users/deiby/Downloads/enturnamiento-vehiculos/GITHUB-PUBLISH.md)
- [DEPLOY-RENDER.md](/C:/Users/deiby/Downloads/enturnamiento-vehiculos/DEPLOY-RENDER.md)

La base de datos y las evidencias quedan preparadas para persistir en disco en Render.

## Android nativo

La app Android de calidad ya tiene:

- login con token
- panel de pendientes, arreglos, aptos y rechazados
- formulario de inspeccion con checklist
- carga de evidencias desde galeria

Guia de arquitectura:

- [ARQUITECTURA-MOVIL.md](/C:/Users/deiby/Downloads/enturnamiento-vehiculos/ARQUITECTURA-MOVIL.md)
- [android-quality-app/README.md](/C:/Users/deiby/Downloads/enturnamiento-vehiculos/android-quality-app/README.md)
