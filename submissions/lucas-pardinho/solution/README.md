# G4 Focus — guia operacional

Aplicativo read-only de priorização de oportunidades para o Challenge 003. O pipeline Python gera contratos JSON a partir dos CSVs reais; a aplicação Next.js usa esses mesmos contratos na interface e na API.

## Estrutura

```text
solution/
├── analytics/          # validação, normalização e scoring
├── data/
│   ├── raw/            # fonte imutável
│   └── normalized/     # gerado pelo pipeline
├── generated/         # contratos JSON gerados
├── web/               # Next.js, interface e API
├── Dockerfile
└── compose.yaml
```

## Pré-requisitos

Escolha um dos caminhos:

- Docker Engine 24+ com Compose v2; ou
- Python 3.11+, Node.js 20.9+ e npm.

O pipeline usa somente a biblioteca padrão do Python. A instalação de pacotes web deve ser feita com o lockfile versionado para manter a reprodução.

## Rodar com Docker

Na pasta `solution/`:

```bash
docker compose up --build
```

Abra:

- app: [http://localhost:3000](http://localhost:3000)
- health: [http://localhost:3000/api/health](http://localhost:3000/api/health)

O build é multi-stage: gera os dados com Python, compila o Next.js em modo standalone e executa a imagem final como usuário não-root. Os JSONs locais em `generated/` são ignorados no contexto Docker para provar que a imagem consegue regenerá-los.

Parar e remover o container:

```bash
docker compose down
```

## Rodar localmente

### 1. Gerar dados

Na pasta `solution/`:

```bash
python3 analytics/pipeline.py \
  --data-dir data/raw \
  --normalized-dir data/normalized \
  --output-dir generated
```

Saídas esperadas:

- `generated/opportunities.json`
- `generated/dashboard.json`
- `generated/model-report.json`
- `generated/data-quality.json`

### 2. Instalar, testar e iniciar a web

```bash
cd web
npm ci
npm run check
HOSTNAME=127.0.0.1 PORT=3000 npm start
```

`npm run check` executa lint, testes e build. Para desenvolvimento:

```bash
npm run dev
```

Em desenvolvimento, dados de amostra podem ser usados apenas quando os artefatos não estão disponíveis. Em produção, a ausência dos JSONs causa erro e `/api/health` retorna indisponibilidade; o fallback não mascara um pipeline quebrado.

## Testar somente o pipeline

Na pasta `solution/`:

```bash
python3 -m unittest discover -s analytics/tests -p 'test_*.py' -v
```

Os testes usam diretórios temporários e cobrem contratos, determinismo, normalização, joins, leakage, limites e filas.

## Variáveis de ambiente

| Variável | Default | Uso |
|---|---|---|
| `PORT` | `3000` | Porta HTTP. O Railway injeta esse valor. |
| `HOSTNAME` | `0.0.0.0` no container | Interface de rede usada pelo servidor standalone. |
| `GENERATED_DATA_DIR` | `../generated`, relativo a `web/` | Caminho absoluto ou relativo dos quatro contratos JSON. |
| `ALLOW_SAMPLE_DATA` | permitido fora de produção | `true` habilita fallback visual; a imagem define `false`. |
| `NEXT_TELEMETRY_DISABLED` | `1` na imagem | Desabilita telemetria durante build/runtime do container. |

Esta versão não exige `.env`, banco ou credenciais. Não versione segredos se integrar serviços externos.

## Páginas

| Rota | Objetivo |
|---|---|
| `/` | Visão executiva e prioridades. |
| `/pipeline` | Exploração do pipeline e das filas. |
| `/carteira` | Carteira filtrável para uso operacional. |
| `/metodologia` | Score, evidências, limitações e qualidade dos dados. |

## API

Todas as rotas são read-only e retornam JSON.

### Saúde

```bash
curl --fail http://localhost:3000/api/health
```

Retorna HTTP 200 somente quando o serviço consegue localizar os quatro artefatos em produção.

### Dashboard

```bash
curl http://localhost:3000/api/v1/dashboard
```

Entrega resumo calculado sobre a carteira aberta e agregações geradas pelo pipeline.

### Oportunidades

```bash
curl --get http://localhost:3000/api/v1/opportunities \
  --data-urlencode 'queue=Foco agora' \
  --data-urlencode 'regionalOffice=Central' \
  --data-urlencode 'sort=score' \
  --data-urlencode 'order=desc' \
  --data-urlencode 'page=1' \
  --data-urlencode 'pageSize=25'
```

Parâmetros:

| Parâmetro | Regra |
|---|---|
| `search` | Busca parcial por ID, conta, produto ou vendedor. |
| `queue` | Nome exato da fila. |
| `salesAgent` | Nome exato do vendedor. |
| `manager` | Nome exato do manager. |
| `regionalOffice` | Nome exato do escritório regional. |
| `dealStage` | Etapa exata. |
| `sort` | `score` (default), `value`, `age` ou `probability`. |
| `order` | `desc` (default) ou `asc`. |
| `page` | Inteiro positivo; default 1. |
| `pageSize` | Inteiro positivo; default 25, máximo 100. |

Detalhe por ID:

```bash
curl http://localhost:3000/api/v1/opportunities/4L6EX9
```

Um ID inexistente retorna HTTP 404 com envelope `error`. Indisponibilidade dos dados retorna HTTP 503.

### Modelo e qualidade

```bash
curl http://localhost:3000/api/v1/model-report
```

Retorna, no mesmo envelope, o relatório do modelo e a auditoria de qualidade.

## Railway

Conecte o fork pelo GitHub e configure o Root Directory:

```text
/submissions/lucas-pardinho/solution
```

O Railway detecta o `Dockerfile` e injeta `PORT`. Na configuração do serviço, defina o health check como `/api/health` antes de ativar o deploy. O passo a passo completo, incluindo fork, branch, commit, PR e verificação da URL pública, está em [`../docs/submission-and-deployment.md`](../docs/submission-and-deployment.md).

> A submissão não inclui `railway.toml`: o Railway bloqueou a adoção de Config as Code em serviços novos. Para este único serviço, Dockerfile, Root Directory e health check no painel são o caminho atual e mais simples. Uma evolução pode adotar `.railway/railway.ts` para Infrastructure as Code.

## Critérios de aceitação

- pipeline termina sem erro e gera exatamente os quatro contratos;
- testes Python passam;
- `npm run check` passa;
- imagem Docker constrói sem depender de artefatos gerados no host;
- processo no container não roda como root;
- `/api/health` responde 200 e informa fonte `generated`;
- interface carrega dashboard, pipeline, carteira e metodologia;
- nenhum endpoint usa fallback de amostra em produção.

## Referências operacionais

- [Railway: Dockerfiles](https://docs.railway.com/builds/dockerfiles)
- [Railway: Healthchecks](https://docs.railway.com/deployments/healthchecks)
- [Railway: GitHub autodeploys](https://docs.railway.com/deployments/github-autodeploys)
