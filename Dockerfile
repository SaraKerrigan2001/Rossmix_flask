# ============================================================
# Rossmix Flask — Dockerfile
# Imagen multi-stage para producción eficiente y segura
# ============================================================

# ── Stage 1: Builder (instala dependencias) ──────────────────
FROM python:3.13-slim AS builder

WORKDIR /app

# Variables para evitar archivos .pyc y buffering
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dependencias del sistema necesarias para psycopg y reportlab
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev \
        gcc \
        libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python en un directorio separado
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install -r requirements.txt


# ── Stage 2: Runtime (imagen final ligera) ───────────────────
FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PORT=5000

# Solo las librerías de sistema necesarias en runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    # Crear usuario no-root para mayor seguridad
    && addgroup --system rossmix \
    && adduser --system --ingroup rossmix rossmix

# Copiar dependencias instaladas del builder
COPY --from=builder /install /usr/local

# Copiar código del proyecto (excluyendo lo que está en .dockerignore)
COPY --chown=rossmix:rossmix . .

# Cambiar a usuario no-root
USER rossmix

EXPOSE $PORT

# Script de inicio: ejecuta migraciones y luego gunicorn
CMD gunicorn \
    --bind "0.0.0.0:${PORT}" \
    --workers "${GUNICORN_WORKERS:-2}" \
    --threads "${GUNICORN_THREADS:-2}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --access-logfile - \
    --error-logfile - \
    wsgi:app
