# ── Etapa base ──────────────────────────────────────────────
FROM python:3.11-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Etapa development (con hot-reload) ──────────────────────
FROM base AS development

ENV PYTHONPATH=/app

# En dev el código se monta como volumen (docker-compose.yml)
# Uvicorn con --reload detecta cambios en /app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "info"]

# ── Etapa production ─────────────────────────────────────────
FROM base AS production

COPY . .

# Ensure the backend directory is in PYTHONPATH so Python can find the 'app' module
ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
