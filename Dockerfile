FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Instalar dependencias del sistema + Caddy (reverse proxy HTTPS)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
    && curl -L "https://github.com/caddyserver/caddy/releases/download/v2.9.1/caddy_2.9.1_linux_amd64.tar.gz" \
         -o /tmp/caddy.tar.gz \
    && tar xzf /tmp/caddy.tar.gz -C /usr/local/bin caddy \
    && rm /tmp/caddy.tar.gz \
    && apt-get purge -y --auto-remove curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

RUN mkdir -p /var/data /root/.local/share/caddy \
    && chmod +x /app/start.sh

EXPOSE 8000 80 443

CMD ["/app/start.sh"]
