FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/app/src TZ=Europe/Berlin \
    G4_DATA_DIR=/app/data G4_ARTIFACT_DIR=/app/artifacts G4_DB_PATH=/app/var/app.db

RUN apt-get update && apt-get install -y --no-install-recommends cron curl libgomp1 tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir ".[api]"
COPY data ./data
COPY scripts ./scripts
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh scripts/run_daily.sh && mkdir -p var/logs

# Treino inicial no build: grava artifacts/vAAAA.MM.N e var/app.db dentro da imagem.
# (volumes nomeados copiam esse conteúdo na primeira criação)
RUN python -m lead_trainer train

# Cron: treino diário às 02:00 (fuso TZ). O job recarrega a API ao terminar.
RUN printf 'SHELL=/bin/bash\nPATH=/usr/local/bin:/usr/bin:/bin\nPYTHONPATH=/app/src\n0 2 * * * root cd /app && bash scripts/run_daily.sh >> /app/var/logs/cron.log 2>&1\n' > /etc/cron.d/g4-trainer \
    && chmod 0644 /etc/cron.d/g4-trainer

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD curl -fsS http://localhost:8000/api/v1/health/ready || exit 1
ENTRYPOINT ["/entrypoint.sh"]
