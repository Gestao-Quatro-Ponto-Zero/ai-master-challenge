# Backend API — Triagem Inteligente de Suporte

A API carrega os modelos e módulos a partir da pasta irmã `../ml/`.

## Instalação e execução

A partir da pasta `solution/`:

```bash
python -m venv .venv
# Ative o ambiente virtual e então:
pip install -r fase4/api/requirements.txt
python fase4/api/main.py
```

Alternativamente:

```bash
cd fase4/api
uvicorn main:app --host 127.0.0.1 --port 8000
```

## Endpoints

- `POST /classify` — classifica um chamado e retorna domínio, categoria, confiança, prioridade, decisão, fila, justificativa e rastreabilidade.
- `GET /health` — status da API e carregamento dos modelos.
- `GET /test-cases` — casos e resultados históricos da suíte.
- `GET /model-metadata` — metadados do classificador.

Exemplo de corpo para `POST /classify`:

```json
{"text":"I cannot log into my account","channel":"Email"}
```

**Limitação importante:** a API recomenda classificação e encaminhamento; não executa ações externas. A política final mantém confirmação humana e não libera roteamento AUTOMATIC.
