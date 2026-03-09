FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install project dependencies.
COPY pyproject.toml README.md ./
COPY g4sales ./g4sales
COPY frontend ./frontend
COPY data ./data
COPY CHALLENGE.MD ./CHALLENGE.MD

RUN pip install --no-cache-dir .

EXPOSE 8000 8501
