# SPEC-11: Single-stage build for Railway deploy
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ ./src/
COPY config/ ./config/
COPY submissions/rodolfo/data/ ./submissions/rodolfo/data/
COPY run.py .
COPY api.py .

RUN pip install --no-cache-dir -e ".[api]"

ENV PYTHONPATH=/app/src:$PYTHONPATH
ENV PIPELINE_CONFIG=config/ravenstack.yaml
ENV OUTPUT_DIR=/app/output

RUN mkdir -p /app/output

EXPOSE 8080

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
