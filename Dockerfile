# ── Stage 1: Frontend bauen ──────────────────────────────────────────────────
FROM node:22-alpine AS frontend-builder
WORKDIR /build

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python-Runtime ───────────────────────────────────────────────────
FROM python:3.12-slim AS runtime
WORKDIR /app

# System-Abhängigkeiten (für bcrypt/cryptography)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Python-Pakete
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Quellcode
COPY backend/  ./backend/
COPY schema.sql ./

# Gebautes Frontend
COPY --from=frontend-builder /build/dist ./frontend/dist/

# Verzeichnisse für persistente Daten
RUN mkdir -p /app/data /app/assets

ENV PYTHONUNBUFFERED=1 \
    DATA_DIR=/app/data \
    ASSETS_DIR=/app/assets

EXPOSE 8000
WORKDIR /app/backend

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
