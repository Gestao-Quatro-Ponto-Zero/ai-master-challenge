# Bot de suporte (Telegram). Sem porta exposta: usa long polling (o bot busca as mensagens).
# Build a partir de submissions/gustavo-paraguassu/. O modelo (solution/models/router.joblib) não está
# no git: gere com solution/analysis/03_ds2_core.py antes do build.
FROM python:3.11-slim
WORKDIR /app/solution
COPY solution/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY solution/ .
RUN test -f models/router.joblib || (echo "falta models/router.joblib: rode analysis/03_ds2_core.py" && exit 1)
# Estado (tickets, eventos) num volume persistente; chaves vêm de variáveis de ambiente / secrets.
ENV RUNTIME_DIR=/data PYTHONUNBUFFERED=1
CMD ["python", "-m", "app.telegram_bot"]
