# Android Quality App

Proyecto Android nativo para el equipo de calidad.

## Lo que ya incluye

- login para usuarios con rol `CALIDAD`
- panel con pendientes, arreglos, aptos y rechazados
- pantalla de inspeccion
- checklist con fotos desde galeria
- envio del checklist a la API principal

## Configuracion

Edita `gradle.properties` y cambia:

```properties
API_BASE_URL=https://TU-APP.onrender.com/api/
```

## Abrir en Android Studio

1. Abre la carpeta `android-quality-app`.
2. Espera el sync de Gradle.
3. Ejecuta la app en un equipo o emulador Android.

## Nota

Esta primera version apunta al flujo de calidad. La siguiente evolucion natural es agregar captura directa con camara, cache local y sincronizacion resiliente.
