# Despliegue en Render

## Lo que ya queda preparado

- `render.yaml` para crear el servicio web
- `DB_PATH=/var/data/enturnamiento.db`
- disco persistente para SQLite
- evidencias de calidad en `/var/data/uploads`
- `healthCheckPath: /healthz`

## Pasos recomendados

1. Sube este proyecto a GitHub.
2. En Render crea un nuevo servicio usando `Blueprint`.
3. Selecciona el repositorio.
4. Verifica que Render cree un Web Service y un disco persistente.
5. Espera el primer despliegue y abre la URL publica.

## Validacion despues del deploy

- `https://TU-APP.onrender.com/healthz`
- `https://TU-APP.onrender.com/`
- `https://TU-APP.onrender.com/driver.html`

## Primeros ajustes despues de publicar

1. Entra con `logistica`.
2. Crea usuarios reales y cambia las claves iniciales.
3. Configura la geocerca de la planta.
4. Imprime el QR del registro publico.

## Nota tecnica

SQLite funciona bien para una operacion pequena o mediana. Si despues necesitas mas concurrencia o varias sedes, la siguiente evolucion recomendada es migrar a PostgreSQL.
