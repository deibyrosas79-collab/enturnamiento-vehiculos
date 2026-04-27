#!/bin/sh
set -e

if [ "$ENABLE_HTTPS" = "true" ]; then
    echo "[start] Iniciando Caddy HTTPS para $CADDY_DOMAIN ..."
    caddy start --config /app/Caddyfile
    echo "[start] Caddy iniciado."
fi

echo "[start] Iniciando servidor Python en puerto $PORT ..."
exec python server.py
