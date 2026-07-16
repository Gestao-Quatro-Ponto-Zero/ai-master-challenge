FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY config/ ./config/
COPY submissions/rodolfo/data/ ./submissions/rodolfo/data/
COPY run.py .
COPY api.py .

ENV PYTHONPATH=/app/src
ENV PIPELINE_CONFIG=config/ravenstack.yaml
ENV OUTPUT_DIR=/app/output

RUN mkdir -p /app/output

EXPOSE 8080

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
