# QRYPTA - imagen para Google Cloud Run (arquitectura sin estado)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Instalar dependencias primero para aprovechar la caché de capas
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Ejecutar como usuario sin privilegios
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

# Cloud Run inyecta la variable PORT (8080 por defecto)
ENV PORT=8080
EXPOSE 8080

# Forma shell (sin corchetes) para que ${PORT} se expanda en tiempo de ejecución
CMD streamlit run app.py \
    --server.port=${PORT} \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
