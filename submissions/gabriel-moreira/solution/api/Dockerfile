# Build context: submissions/gabriel-moreira/ (o pai de solution/), para
# alcançar tanto solution/{scoring,api} quanto data/ — ver docker-compose.yml.
FROM python:3.12-slim

WORKDIR /app

# scoring/ é copiado primeiro e instalado antes do resto — é a dependência
# que api/ importa em modo editável (requirements.txt referencia ../scoring,
# que resolve para /scoring já que /app e /scoring são irmãos aqui).
COPY solution/scoring /scoring
COPY solution/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY solution/api /app
COPY data /data

ENV LEAD_SCORER_DATA_DIR=/data
ENV LEAD_SCORER_EXPORT_PATH=/app/data/processed_pipeline.csv
ENV LEAD_SCORER_CORS_ORIGINS=http://localhost:8080,http://localhost:5173

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
