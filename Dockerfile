# Stage 1: Build der Vue-Anwendung
FROM node:20 AS build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Python Backend & Static Files serving
FROM python:3.11-slim
WORKDIR /app

# Requirements kopieren und installieren
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Gesamten Backend-Code kopieren
COPY backend/ .

# Gebaute Frontend-Dateien (aus Stage 1) in den "static"-Ordner des Backends kopieren
COPY --from=build /app/dist /app/static

ENV DATA_DIR=/app/data
RUN mkdir -p /app/data
VOLUME /app/data

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
