FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV LEAD_SCORER_PORT=8787

WORKDIR /app

COPY pyproject.toml requirements-audit.txt ./
COPY src ./src
COPY scripts ./scripts
COPY data ./data
COPY config ./config
COPY public ./public
COPY contracts ./contracts

RUN python -m pip install --upgrade pip && \
    python -m pip install -e .

EXPOSE 8787

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8787/health', timeout=3)"

CMD ["python", "-m", "uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8787"]
