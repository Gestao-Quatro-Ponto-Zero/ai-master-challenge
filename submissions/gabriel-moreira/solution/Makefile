.PHONY: up down install test validate dev-api dev-web

# Partida por comando único (task 7.1/7.2).
up:
	docker compose up --build

down:
	docker compose down

# Setup local sem Docker, para desenvolvimento e para rodar os testes.
# `-e ../scoring` em api/requirements.txt e validation/requirements.txt é
# resolvido pelo pip relativo ao diretório de invocação — por isso cada
# passo entra no próprio diretório antes de instalar, em vez de referenciar
# o requirements.txt por um caminho relativo a partir de solution/.
install:
	python3 -m venv scoring/.venv && cd scoring && .venv/bin/pip install -q -e . -e ".[dev]"
	python3 -m venv api/.venv && cd api && .venv/bin/pip install -q -r requirements.txt
	python3 -m venv validation/.venv && cd validation && .venv/bin/pip install -q -r requirements.txt
	cd web && npm install

# Suíte de testes completa (unitário + e2e), documentada no README (task 8.5).
test:
	cd scoring && .venv/bin/pytest
	cd api && .venv/bin/pytest
	cd validation && .venv/bin/pytest
	cd web && npx tsc -b

validate:
	cd validation && .venv/bin/python backtest.py --data-dir ../../data

dev-api:
	cd api && .venv/bin/python -m uvicorn main:app --reload --port 8000

dev-web:
	cd web && npm run dev
