FROM python:3.12-slim
# Instala uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
WORKDIR /app
ENV PYTHONPATH=/app
# Copia dependências primeiro (cache layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
# Copia código e dados
COPY . .
# Garante que o entrypoint seja executável
RUN chmod +x entrypoint.sh
# Expõe porta do Streamlit
EXPOSE 8501
ENTRYPOINT ["./entrypoint.sh"]