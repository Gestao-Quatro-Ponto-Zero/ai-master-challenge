# Setup com Docker

## Pré-requisitos

- Docker instalado
- Docker Compose disponível (`docker compose`)

## Como rodar

Na raiz do projeto, execute:

```bash
docker compose up --build
```

Esse comando vai:

- construir a imagem da aplicação
- subir dois serviços
- inicializar o banco SQLite em `data/sales.sqlite3`
- iniciar API e Frontend

## O que deve aparecer quando der certo

Nos logs, você deve ver algo parecido com:

- API iniciada no `0.0.0.0:8000`
- Streamlit iniciado no `0.0.0.0:8501`

Se os dois serviços subirem corretamente, acesse:

- Frontend: `http://localhost:8501/`
- API docs (Swagger): `http://localhost:8000/docs`

## Como validar rapidamente

1. Abra `http://localhost:8501/` e confirme que a tela `G4 Sales: Priority Desk` carregou.
2. Abra `http://localhost:8000/docs` e confirme que os endpoints aparecem.
3. No frontend, aplique filtros e verifique se cards/tabela atualizam.

## Como parar

Para parar os containers:

```bash
docker compose down
```

Para parar e remover volumes associados ao compose:

```bash
docker compose down -v
```
