# Plano — Ferramenta de Priorização de Deals (FastAPI + React)

## Contexto
Vendedores gastam tempo em deals que não fecham e deixam boas oportunidades passar. Objetivo: uma web app simples, para público não técnico, que mostre o pipeline e diga **em quais deals focar e por quê**, em linguagem clara. Começar simples, mas com arquitetura que permita evoluir (banco de dados, ML, autenticação). Código limpo e bem comentado, **tudo em português** (UI, nomes, comentários).

## Dados (pasta `dados/`) — achados da análise
- `sales_pipeline.csv` (8.800 deals): Won 4.238 · Lost 2.473 · Engaging 1.589 · Prospecting 500 → **2.089 deals abertos** a priorizar.
- Liga com `accounts` (85 contas), `products` (7), `sales_teams` (35 vendedores, managers, regional_office).
- Problemas a tratar na carga (centralizados em um único módulo):
  - Produto `GTXPro` no pipeline ≠ `GTX Pro` em products → normalizar.
  - Setor `technolgy` (typo) → `technology`.
  - 1.425 deals abertos **sem conta** (1.088 Engaging, 337 Prospecting) → tratar como "Conta não informada", score usa só os outros fatores.
  - Deals abertos não têm `close_value` → usar `sales_price` do produto como valor estimado.
  - Dados terminam em 2017-12-31 → "data de referência" = maior data do dataset (configurável), para calcular idade do deal.

## Estrutura do projeto
```
backend/
  app/
    main.py              # cria FastAPI, CORS, registra rotas
    config.py            # caminhos, data de referência, pesos do score
    dados/carregador.py  # lê CSVs, limpa, faz joins (accounts/products/sales_teams) — cache em memória
    servicos/
      estatisticas.py    # taxas de vitória históricas (por produto, setor, vendedor, conta) e ciclo médio
      pontuacao.py       # score 0–100, prioridade e motivos em linguagem simples
    rotas/
      pipeline.py        # GET /api/pipeline (filtros), GET /api/deals/{id}
      resumo.py          # GET /api/resumo (KPIs), GET /api/filtros (listas p/ dropdown)
    esquemas.py          # modelos Pydantic de resposta
  tests/                 # pytest: carregador, pontuacao, rotas
  requirements.txt       # fastapi, uvicorn, pandas, pytest, httpx
frontend/  (Vite + React + TypeScript)
  src/
    api/cliente.ts       # chamadas à API (único ponto de fetch)
    tipos.ts
    paginas/Pipeline.tsx
    componentes/
      CartoesResumo.tsx  # KPIs no topo
      FiltrosPipeline.tsx
      QuadroPipeline.tsx # colunas Prospecting | Engaging (kanban) com cartões
      CartaoDeal.tsx     # conta, produto, valor, selo de prioridade
      DetalheDeal.tsx    # painel lateral com score e motivos
      SeloPrioridade.tsx
README.md                # como rodar, arquitetura, como ajustar pesos, próximos passos
```
Cada camada tem uma responsabilidade; a regra de negócio fica só no backend (`servicos/`), o front só exibe.

## Lógica do score (explicável, sem "caixa preta")
Para cada deal aberto, a partir do histórico de deals fechados (Won/Lost):
1. **Chance de fechar** — combinação ponderada de taxas de vitória históricas: produto, setor da conta, vendedor, e a própria conta (quando existe). Com suavização (média com taxa global quando há poucas amostras) para não distorcer.
2. **Valor** — `sales_price` do produto, normalizado.
3. **Tempo parado** — dias desde `engage_date` vs. ciclo médio de deals ganhos; acima do normal reduz o score (deal "esfriando"). Prospecting não tem data → neutro.
4. **Valor esperado** = chance × valor (exibido em R$/US$).
- Score final 0–100 = pesos definidos em `config.py` (fácil de ajustar).
- Prioridade: **Alta / Média / Baixa** (faixas no config) com cor e ícone.
- **Motivos em texto simples**, ex.: "Este produto fecha 65% das vezes", "Deal parado há 140 dias — o normal é 52", "Alto valor: US$ 5.482".

## Telas (foco em clareza para não técnicos)
- **Topo — cartões de resumo**: deals abertos, valor esperado total, nº de prioridade alta, taxa de vitória geral.
- **Filtros**: vendedor (padrão "Todos"), escritório regional, manager, produto, prioridade.
- **Pipeline**: duas colunas (Prospecção, Em negociação), cartões ordenados por score; selo colorido de prioridade; alerta "esfriando".
- **Alternância lista/tabela** ordenável por score/valor (útil para muitos deals).
- **Detalhe do deal**: score, barra por fator, motivos e sugestão de ação ("Priorize", "Reavalie: está parado há muito tempo").
- Textos e rótulos em português; sem jargão técnico.

## Evolução futura (documentada no README, não implementada agora)
Trocar CSV por banco (só muda `carregador.py`), substituir score por modelo de ML (só muda `pontuacao.py`), login por vendedor, histórico/forecast.

## Verificação
1. `cd backend; pip install -r requirements.txt; pytest` — testes de limpeza (GTXPro, typo de setor, contas vazias), score dentro de 0–100, motivos gerados, rotas respondendo.
2. `uvicorn app.main:app --reload` e conferir `/docs` (Swagger) e `/api/pipeline?vendedor=...`.
3. `cd frontend; npm install; npm run dev` → abrir no navegador, testar filtros, abrir detalhe de um deal, conferir que totais batem com a API (2.089 deals abertos sem filtro).
4. `npm run build` e `tsc` sem erros.
