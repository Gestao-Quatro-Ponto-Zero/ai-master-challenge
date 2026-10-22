FROM python:3.12.10-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY apps/api/requirements.lock /tmp/requirements.lock
RUN python -m pip install --no-cache-dir -r /tmp/requirements.lock \
    && useradd --system --uid 10001 --create-home ravenstack

COPY --chown=ravenstack:ravenstack apps/api/src /app/apps/api/src
COPY --chown=ravenstack:ravenstack data/raw /app/data/raw
COPY --chown=ravenstack:ravenstack analysis/business_drivers/outputs /app/analysis/business_drivers/outputs
COPY --chown=ravenstack:ravenstack analysis/historical_churn /app/analysis/historical_churn
COPY --chown=ravenstack:ravenstack analysis/contract_churn /app/analysis/contract_churn
COPY --chown=ravenstack:ravenstack analysis/g4_customer_churn /app/analysis/g4_customer_churn
COPY --chown=ravenstack:ravenstack analysis/daily_portfolio_churn /app/analysis/daily_portfolio_churn
COPY --chown=ravenstack:ravenstack analysis/transition_audit /app/analysis/transition_audit
ENV PYTHONPATH=/app/apps/api/src:/app/analysis \
    RAVENSTACK_DATA_DIR=/app/data/raw

FROM base AS test
USER root
COPY apps/api/requirements-dev.txt /tmp/requirements-dev.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements-dev.txt
COPY apps/api/pyproject.toml /app/apps/api/pyproject.toml
COPY apps/api/tests /app/apps/api/tests
COPY scripts /app/scripts
COPY analysis/g4_customer_churn/tests /app/analysis/g4_customer_churn/tests
COPY analysis/daily_portfolio_churn/tests /app/analysis/daily_portfolio_churn/tests
COPY analysis/transition_audit/tests /app/analysis/transition_audit/tests
WORKDIR /app/apps/api
USER 10001:10001
CMD ["pytest", "-q", "tests", "/app/analysis/daily_portfolio_churn/tests", "/app/analysis/transition_audit/tests"]

FROM base AS runtime
EXPOSE 8000
USER 10001:10001
HEALTHCHECK --interval=20s --timeout=3s --start-period=15s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2)"]
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
