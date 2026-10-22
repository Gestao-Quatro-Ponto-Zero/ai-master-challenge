# RavenStack — The Churn Paradox

## Execução local com Docker Compose

Pré-requisitos: Docker com Docker Compose v2 instalado e o Docker Engine acessível ao usuário atual. Se o Docker não estiver instalado, instale o Docker Desktop ou Docker Engine com o plugin Compose. Se o daemon não estiver acessível, inicie-o e verifique o acesso da sua conta antes de continuar.

A partir deste diretório `solution/`, execute:

    docker compose up --build

Acesse a aplicação em **http://localhost:8080**. O endpoint de saúde da API, encaminhado pelo frontend, é `http://localhost:8080/api/health`. A API permanece somente na rede interna do Compose; a única porta publicada no host é `8080`.

O primeiro build pode baixar imagens Docker e dependências do npm e Python; por isso, pode levar mais tempo e requer acesso à internet. Nenhum arquivo `.env`, chave ou configuração manual da aplicação é necessário para o caminho padrão. Os CSVs necessários são incluídos na imagem da API.

Verifique os serviços com:

    docker compose ps

Para acompanhar os logs, use `docker compose logs -f`. Para encerrar os serviços deste projeto:

    docker compose down

Se a porta `8080` estiver ocupada, confira os listeners com `ss -ltn '( sport = :8080 )'` e os mapeamentos de containers com `docker ps --format 'table {{.Names}}\t{{.Ports}}'`. Não encerre serviços alheios. Libere a porta com o responsável pelo serviço existente antes de iniciar esta entrega; o Compose mantém a porta canônica `8080`.

O Compose e os Dockerfiles estão contidos neste pacote. A partir de uma cópia standalone, execute os comandos dentro de `solution/`; não é necessário o wrapper de conveniência existente fora desta pasta.

Nenhuma chave ou serviço pago é necessário. O backend falha no startup se qualquer CSV obrigatório estiver ausente; não fornece métricas de exemplo.

Na raiz independente /home/thomasleick/the_churn_paradox/, o comando pedido docker compose up --build é encaminhado para este Compose pelo wrapper compose.yaml no diretório de execução. O wrapper fica fora do pacote portátil; para copiar/submeter apenas submissions/thomasleick/, execute na pasta solution/.

## Reproduzir a análise

Com Python 3.12 e os requisitos fixados:

    python -m venv .venv
    . .venv/bin/activate
    pip install -r apps/api/requirements.lock
    PYTHONPATH=apps/api/src RAVENSTACK_DATA_DIR=data/raw python -m uvicorn main:app --host 127.0.0.1 --port 8000

Em outro terminal:

    curl http://127.0.0.1:8000/api/analysis

Reproduza os perfis e agregados apenas com a pasta submetida, a partir da raiz `solution/`:

    python scripts/audit_data.py --help
    python scripts/analyze.py --help
    python scripts/audit_data.py --data-dir data/raw --output ../process-log/evidence/reproduced-data-profile.json
    python scripts/analyze.py --data-dir data/raw --output ../process-log/evidence/reproduced-analysis-summary.json

Ambos os scripts usam `solution/data/raw/` por padrão. Sem `--output`, escrevem JSON no stdout; com `--output`, escrevem somente no caminho solicitado. Não dependem de arquivos de staging em `/tmp`. A análise declara separadamente 21 IDs de uso duplicados, 42 linhas nos grupos duplicados e 21 linhas excedentes.

Análise de direcionadores de negócio independente e aditiva (aquisição/ICP, ativação proxy, adoção, CX, coortes diagnósticas e economia contratual):

    python analysis/business_drivers/run.py --help
    python analysis/business_drivers/run.py --data-dir data/raw --output-dir analysis/business_drivers/outputs/g4-alignment
    python -m unittest discover -s analysis/business_drivers/tests -v

O diretório isolado `g4-alignment/` preserva os artefatos analíticos anteriores. O artefato JSON gerado é servido por `GET /api/business-investigation` e incluído na imagem da API. Reexecute o gerador antes de reconstruir a imagem caso os CSVs mudem. A análise não publica taxa de churn, probabilidade futura, curva de retenção ou receita perdida quando essas quantidades não são identificáveis. O relatório detalhado fica em `../docs/findings/business-driven-investigation.md`; a análise de negócio consolidada em `../docs/findings/G4-CHURN-CONSOLIDATED-REPORT.md`; o resumo para decisão executiva em `../docs/findings/G4-CHURN-EXECUTIVE-REPORT.md`; e a pesquisa pública sobre conceitos de negócio em `../docs/research/g4-business-framework.md`.

Ledger diário de carteira comercial (grão `account × plan_tier × civil day`; plano é proxy, não produto):

    PYTHONPATH=analysis python -m daily_portfolio_churn --help
    PYTHONPATH=analysis python -m daily_portfolio_churn \
      --data-dir data/raw \
      --output-dir analysis/daily_portfolio_churn/outputs/g4-alignment
    PYTHONPATH=analysis python -m unittest discover -s analysis/daily_portfolio_churn/tests -v

A execução reproduzível cobre 731 dias e projeta o mesmo ledger em 24 meses (jan/2023–dez/2024), além de períodos trimestrais, semestrais e anuais. Ela reconstitui 1.433 primeiras relações conta × plano, 43 reativações e 62 perdas. A comparação mensal separa perdas absolutas, denominadores, aquisições, reativações, eventos registrados e taxas condicionais; janeiro de 2023 tem base de abertura zero e taxas indefinidas. Para a coorte de abertura de 2024, 7/374 relações tiveram perda em algum momento (1,87%), 3/374 estavam sem cobertura no fechamento (0,80%) e 0/190 contas perderam toda a cobertura (0,00%), sob `[start_date, end_date)`. Os resultados são condicionais à semântica das datas e não são churn de produto ou taxa comercial validada. Veja `../docs/findings/DAILY-COMMERCIAL-CHURN-CONSOLIDATED.md` e `../docs/findings/G4-CHALLENGE-FINAL-ANSWERS.md`, `../docs/findings/DAILY-COMMERCIAL-CHURN-CEO-BRIEF.md` e o relatório de consolidação em `../docs/findings/RAVENSTACK-FINAL-EXECUTIVE-DELIVERY.md`.

Reconstrução independente de churn histórico pelas datas de assinatura (módulo apenas com biblioteca padrão):

    python analysis/historical_churn/reconstruct.py --help
    python analysis/historical_churn/reconstruct.py
    python -m unittest discover -s analysis/historical_churn/tests -v

O módulo lê `data/raw/`, calcula snapshots de contas/assinaturas em 2023-01-01, 2024-01-01 e 2025-01-01, taxas anuais e mensais condicionais e diagnóstico de coortes por início da primeira assinatura válida. Ele gera JSON e três CSVs sob `analysis/historical_churn/outputs/`. O endpoint `GET /api/historical-churn` calcula os resultados na inicialização da API a partir dos CSVs originais. A taxa de 2024 pela regra literal é 0/191 = 0,0% para logos e 66/655 = 10,08% para as assinaturas da base inicial; as divergências com eventos/flags estão explícitas na interface. O valor de 2023 é indefinido porque o denominador no início do ano é zero. Leia `../docs/findings/HISTORICAL-CHURN-RECONSTRUCTION.md` antes de interpretar esses cálculos como métricas de negócio.

Investigação forense independente de encerramentos de assinatura e eventos de conta:

    python analysis/contract_churn/investigate.py --help
    python analysis/contract_churn/investigate.py
    python -m unittest discover -s analysis/contract_churn/tests -v

O gerador grava um inventário dos 66 IDs encerrados na base inicial de 2024, das 443 ocorrências de evento que coincidem com uma assinatura ativa, da reconciliação por conta e de métricas descritivas. O endpoint `GET /api/contract-churn` serve os mesmos resultados; a seção **Account vs. Subscription Churn** está em Follow the Evidence. Eventos contêm `account_id`, não `subscription_id`: a análise não inventa associação evento-contrato nem chama início posterior de migração confirmada. Consulte `../docs/findings/CONTRACT-CHURN-FORENSICS.md` e o resumo `../docs/findings/CONTRACT-CHURN-EXECUTIVE-SUMMARY.md`.

## Dados e atribuição

Os cinco CSVs vêm do dataset público “SaaS Subscription & Churn Analytics”, de River @ Rivalytics: https://www.kaggle.com/datasets/rivalytics/saas-subscription-and-churn-analytics-dataset. A página do desafio declara licença MIT e o README incluso no pacote descreve a licença como MIT-like e pede atribuição. Os arquivos distribuídos são declarados sintéticos e sem PII. A proveniência, os hashes e o alerta de licença estão em process-log/evidence/ e docs/methodology/analysis.md.

## Serviços

- API: FastAPI, pandas, Pydantic; carrega e agrega os CSVs uma vez no startup.
- Web: React, TypeScript, Vite no build e Nginx estático no runtime.
- Comunicação: REST/JSON com proxy /api do Nginx para api:8000.
- Não há banco de dados persistente nem chamada a provedor de IA.

## Verificação

Para os resultados atuais de análise, testes, runtime e readiness, consulte `../docs/findings/RAVENSTACK-FINAL-EXECUTIVE-DELIVERY.md`, `../docs/findings/RAVENSTACK-SUBMISSION-READINESS.md` e `../process-log/checkpoints/41-final-consolidation-preflight.md` a `44-submission-readiness.md`. Os checkpoints anteriores permanecem como evidência histórica e não substituem as verificações atuais.
