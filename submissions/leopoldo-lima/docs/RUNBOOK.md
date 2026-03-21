# Runbook de demo (Docker)

## Pré-requisitos
- Docker Desktop com Compose habilitado.

## Caminho feliz

```powershell
docker compose up --build
```

URLs:
- API health: `http://127.0.0.1:8787/health`
- API ranking: `http://127.0.0.1:8787/api/ranking?limit=3`
- UI shell: `http://127.0.0.1:8787/`

## Verificação rápida

```powershell
docker compose ps
docker compose logs lead-scorer
```

O serviço deve ficar `healthy` após alguns segundos.

## Encerrar ambiente

```powershell
docker compose down
```

## Troubleshooting básico
- Porta `8787` em uso:
  - altere o mapeamento no `docker-compose.yml` para outra porta host.
- Build falha por cache antigo:
  - `docker compose build --no-cache`
- Container não fica saudável:
  - validar `/health` em logs e confirmar que o app subiu sem erro de import.

## Observações
- A imagem usa `python:3.13-slim`.
- Sem segredos no compose atual.
- Por defeito o container usa `LEAD_SCORER_DATA_SOURCE_MODE=real_dataset` (CSVs em `data/`). Ver `docs/RUNTIME_DATA_FLOW.md`.
