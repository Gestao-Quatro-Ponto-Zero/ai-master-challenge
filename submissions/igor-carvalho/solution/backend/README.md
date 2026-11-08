# G4 Lead Scorer

Priorização de oportunidades de venda. Dois aplicativos independentes sobre um núcleo compartilhado:

| Pacote | Papel |
|---|---|
| `lead_core` | features (point-in-time), faixas, motivos, calibração, bundle do modelo, SQLite |
| `lead_trainer` | **treina** o modelo (LightGBM), faz backtest, calibra, compara com a versão ativa e promove (champion/challenger) |
| `lead_api` | **serve** os scores já treinados (FastAPI + JWT + RBAC). Nunca treina numa requisição |

## Rodar
```bash
python3 -m venv .venv && source .venv/bin/activate
make install
make train      # grava artifacts/vAAAA.MM.N e ativa se passar no portão (AUC IC95% > 0,5, receita no topo > ordenar só por preço e sem piora)
make api        # http://localhost:8000/docs
make test       # rápido;  make test-all  inclui dataset real + performance
```
Configuração por variáveis `G4_*` (ver `src/lead_api/settings.py`): `G4_DATA_DIR`, `G4_ARTIFACT_DIR`, `G4_DB_PATH`,
`G4_JWT_SECRET` (≥ 32 caracteres), `G4_SHOW_PROBABILITY` (mostra a "Chance" em %; a tela avisa quando `calibration.useful` é falso), `G4_RATE_LIMIT_PER_MINUTE`, `G4_CORS_ORIGINS`.

Retreino contínuo: agende `make train` (cron) ou use `POST /api/v1/admin/retrain`. Use `python -m lead_trainer train --force` para promover ignorando o portão.

## Testar na mão (Postman)
Importe `g4-lead-scorer.postman_collection.json` no Postman e rode a pasta `00 Auth` primeiro (ela guarda os tokens nas variáveis da coleção).
Usuários: `vicki-laflamme` (vendedor), `celia-rouche` (manager), `revops` (admin).

## Esquema do banco
Congelado — ver `docs/DATABASE.md`. Qualidade e backlog técnico — `docs/QUALIDADE.md`.

## Treino diário
`scripts/run_daily.sh` (ou `make train-daily`) treina com os dados atuais, grava log em `var/logs/` e promove só se passar no portão.
Se `G4_API_URL=http://localhost:8000` estiver no `.env`, a API recarrega o modelo ativo ao final.

Agendar no macOS (todo dia às 02:00; se o Mac estiver dormindo, roda ao acordar):
```bash
mkdir -p var/logs && cp deploy/com.g4.lead-trainer.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.g4.lead-trainer.plist
launchctl start com.g4.lead-trainer        # teste imediato
launchctl unload ~/Library/LaunchAgents/com.g4.lead-trainer.plist   # desligar
```
Alternativa (cron): `0 2 * * * cd /Users/igor.carvalho/projects/g4-lead-scorer/backend && bash scripts/run_daily.sh`

**Novos leads:** o treino lê os CSVs de `G4_DATA_DIR` a cada execução. Os leads do dia precisam estar nesses arquivos (ou em outra fonte, via um novo `DealRepository`) antes das 02:00.

## Docker (tudo com um comando)
```bash
cd backend && cp .env.example .env   # defina G4_JWT_SECRET
./scripts/up.sh                      # ou: make docker-up
```
- **No build:** treina o modelo inicial (leva alguns minutos) e grava na imagem.
- **No container:** sobe o cron (todo dia às 02:00, fuso Europe/Berlin) e a API em http://localhost:8000/docs.
- **Leads novos:** atualize os CSVs em `backend/data/` (montada no container). O cron treina com eles, promove se passar no portão e recarrega a API sozinho.
- **Volumes:** modelos e banco ficam em volumes nomeados e sobrevivem a rebuilds; um rebuild NÃO substitui o modelo do volume. Para treinar agora: `make docker-train`. Para recomeçar do zero: `make docker-reset`.
- Logs: `make docker-logs`; histórico do treino em `/app/var/logs` (dentro do volume).
