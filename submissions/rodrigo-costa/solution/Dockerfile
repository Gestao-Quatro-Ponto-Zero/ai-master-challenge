# Imagem do Lead Scorer: só Python e a biblioteca padrão, nenhuma dependência para instalar.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOST=0.0.0.0

WORKDIR /app
COPY . .

RUN useradd --create-home --uid 1000 app
USER app

# No contêiner o servidor escuta em 0.0.0.0 (HOST) na porta da variável PORT (padrão 8000).
CMD ["python", "server.py"]
