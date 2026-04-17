# Arquitectura movil propuesta

## Objetivo

Tener una app Android nativa para el equipo de calidad que use la API de enturnamiento y permita revisar vehiculos desde celular en planta.

## Alcance inicial ya construido

- login con token de sesion
- lectura de pendientes, arreglos, aptos y rechazados
- checklist de inspeccion
- seleccion de evidencias fotograficas
- guardado de decision `APPROVED`, `REWORK` o `REJECTED`

## Stack

- Kotlin
- Jetpack Compose
- Material 3
- MVVM
- Retrofit
- OkHttp
- Coroutines

## Endpoints usados por la app

- `POST /api/auth/login`
- `GET /api/app-state`
- `POST /api/quality/{vehicleId}/inspect`

## Siguiente fase recomendada

1. Publicar la API en Render.
2. Configurar la URL real en la app Android.
3. Abrir el proyecto en Android Studio y generar APK.
4. En una segunda fase agregar camara directa, cache local y modo offline.
