# Backend do Lead Scorer — para Render/Railway/Fly (ou docker compose local).
# Sem chave de IA por padrão: os textos saem no modo template e a demo sempre funciona.
FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY data ./data
COPY config ./config

# Render/Railway injetam $PORT; local cai no 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
