PY ?= python3
export PYTHONPATH := src
export G4_DATA_DIR ?= data
export G4_ARTIFACT_DIR ?= artifacts
export G4_DB_PATH ?= var/app.db
export G4_JWT_SECRET ?= troque-este-segredo-em-producao-0123456789

.PHONY: install train evaluate api test test-all lint complexity
install:        ## instala dependências (venv recomendado)
	$(PY) -m pip install -e ".[api,dev]"
train:          ## treina, avalia (backtest) e promove se passar no portão de qualidade
	@mkdir -p var && $(PY) -m lead_trainer train
evaluate:       ## só o backtest, sem gravar nada
	$(PY) -m lead_trainer evaluate
api:            ## sobe a API em http://localhost:8000 (docs em /docs)
	@mkdir -p var && $(PY) -m lead_api
test:           ## testes rápidos (unit + API + contrato)
	$(PY) -m pytest
test-all:       ## inclui testes lentos (dataset real) e de performance
	$(PY) -m pytest -m "slow or perf or not slow"
lint:
	$(PY) -m ruff check src tests
complexity:
	$(PY) -m radon cc src -s -a -n B

.PHONY: train-daily
train-daily:    ## o mesmo job que roda todo dia (lock + log + refresh opcional da API)
	@bash scripts/run_daily.sh

.PHONY: docker-up docker-down docker-logs docker-train docker-reset
docker-up:      ## build (treina) + cron diário + API em http://localhost:8000
	@bash scripts/up.sh
docker-down:    ## para os containers (mantém modelos e banco)
	docker compose down
docker-logs:
	docker compose logs -f app
docker-train:   ## roda agora o mesmo job do cron dentro do container
	docker compose exec app bash scripts/run_daily.sh
docker-reset:   ## CUIDADO: apaga volumes (modelos, banco e feedback)
	docker compose down -v
