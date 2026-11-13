FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MPLCONFIGDIR=/tmp/matplotlib

# Fuente con acentos y símbolos para el PDF (core/informe.py)
RUN apt-get update \
 && apt-get install -y --no-install-recommends fonts-dejavu-core \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY .streamlit/ .streamlit/
COPY core/ core/
COPY app/ app/

RUN useradd --create-home --uid 10001 qrypta
USER qrypta

EXPOSE 8080
CMD ["sh", "-c", "streamlit run app/main.py --server.port=${PORT:-8080} --server.address=0.0.0.0"]
