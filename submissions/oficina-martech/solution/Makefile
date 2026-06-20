.PHONY: install migrate seed setup run test reset evidence

# Override do interpretador quando necessário:  make test PYTHON=python3
PYTHON ?= python
EVID   := ../process-log/execucoes

install:        ## instala dependências
	$(PYTHON) -m pip install -r requirements.txt

migrate:        ## cria/atualiza o schema (SQLite)
	$(PYTHON) -m db.migrate

seed:           ## carrega os dados reais + valida
	$(PYTHON) -m db.seed

setup: install migrate seed  ## instala tudo, do zero, pronto pra rodar

reset:          ## recria o banco do zero e recarrega
	$(PYTHON) -m db.migrate --reset && $(PYTHON) -m db.seed

run:            ## sobe o app
	$(PYTHON) -m streamlit run app/main.py

test:           ## roda os testes
	$(PYTHON) -m pytest -q

evidence:       ## regenera os .txt de evidência num comando (pytest, score, install/migrate/seed)
	$(PYTHON) -m pytest -o addopts= > $(EVID)/pytest.txt 2>&1 || true
	$(PYTHON) -m notebooks.score_distribuicao > /dev/null
	@{ \
	  echo "# Evidência de instalação — regenerada por 'make evidence'"; \
	  echo "# Executado em: submissions/oficina-martech/solution/"; \
	  echo ""; \
	  echo "## pip install -r requirements.txt"; \
	  $(PYTHON) -m pip install -r requirements.txt 2>&1 | tail -3; \
	  echo ""; \
	  echo "## python -m db.migrate --reset   (recria do zero, aplica as migrations)"; \
	  $(PYTHON) -m db.migrate --reset 2>&1; \
	  echo ""; \
	  echo "## python -m db.seed"; \
	  $(PYTHON) -m db.seed 2>&1; \
	} > $(EVID)/install-migrate-seed.txt
	@echo "Evidências regeneradas em $(EVID)/ — pytest.txt, score-distribuicao.txt, install-migrate-seed.txt"
	@echo "(app-smoke-test.txt é narrativa interativa — atualizado à mão quando a UI muda)"
