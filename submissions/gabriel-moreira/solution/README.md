# Pipeline Priorizado — Lead Scorer

Ferramenta de triagem do pipeline de vendas por **valor em risco** (`PRIORIDADE = p̂ × VALOR × URGÊNCIA`), não por probabilidade categórica de fechamento — a evidência estatística por trás dessa escolha está em [`validation/`](./validation) e em [`../docs/decisions-log.md`](../docs/decisions-log.md). Este documento é o guia prático: como rodar, o que cada peça faz, e o que a solução explicitamente não faz.

## Como rodar

### Via Docker (comando único)

```bash
docker compose up --build
```

Abre em `http://localhost:8080`. O serviço `web` (nginx) serve o build do React e faz proxy de `/api/*` para o serviço `api` (FastAPI, porta 8000 também exposta no host).

### Sem Docker

```bash
make install   # cria os três venvs Python (scoring, api, validation) + npm install em web/
make dev-api   # terminal 1 — http://localhost:8000
make dev-web   # terminal 2 — http://localhost:5173 (proxy /api -> :8000)
```

Pré-requisitos: Python 3.10+, Node.js 18+. Sem banco de dados — os quatro CSVs em `../data/` carregam inteiros em memória na inicialização da API.

### Testes

```bash
make test
```

Roda, em sequência: os testes unitários do motor de scoring (`scoring/`, incluindo as duas metades de CONFIANÇA, a árvore de ESTADO, plano de ação em passos e os exemplos de referência dos specs), os testes de contrato/e2e da API (`api/`, cobrindo listagem paginada e ordenada com desempate estável, filtros de organização sem escopo de sessão, endpoint de detalhe, opções de filtro e exportação de identificadores filtrados), os testes de determinismo e consistência do artefato de validação (`validation/`, incluindo os três resultados negativos de condicionamento por setor/aging por produto/URGÊNCIA por produto), e a checagem de tipos do frontend (`web/`).

### Validação estatística

```bash
make validate
```

Imprime o relatório completo em texto: ausência de sinal preditivo firmográfico (AUC + testes de permutação), derivação de `k` por nível hierárquico, monotonicidade de `risco(t)`, fronteira de censura de 138 dias, e concentração de PRIORIDADE no topo da fila. Ver [`validation/backtest.py`](./validation/backtest.py).

[`Relatório Gerado`](./report.md)

## A fórmula, resumida

```
p̂          = encolhimento hierárquico (empirical Bayes) da taxa de ganho do produto, k derivado dos dados
VALOR      = preço de tabela × multiplicador de porte (prior neutro 1,00 se a conta é desconhecida)
URGÊNCIA   = risco(idade) — probabilidade de resolver nos próximos 30 dias, curva isotônica
PRIORIDADE = p̂ × VALOR × URGÊNCIA                    (dólares — valor intermediário auditável, não exibido)
SCORE      = percentil(PRIORIDADE) × 100              (contra os 4.238 negócios historicamente ganhos — número de prioridade exposto)
CONFIANÇA  = min(completude, suporte)                  (0–100 — veracidade do dado, não probabilidade)
ESTADO     = árvore(sem_precedente, SCORE≥95, CONFIANÇA<50)   (Priorizar / Acompanhar / Qualificar / Revisão em lote)
```

SCORE e CONFIANÇA nunca se combinam num único número — um ordena a fila, o outro diz o quanto acreditar na posição. PRIORIDADE em dólares deixou de ser exibida ou de ordenar a fila (redesenho 2026-08-20): a decomposição de `log(PRIORIDADE)` atribui 87,3% da variância a VALOR e 0,1% a `p̂` — ordenar por ela era, na prática, ordenar por preço de tabela. Permanece calculada e exportada no CSV como valor auditável. A decomposição completa, com os exemplos de referência e o porquê de cada peça, está em [`../docs/architecture.md`](../docs/architecture.md) e nos specs formais em [`../../../openspec/changes/redesign-score-confianca-estado/`](../../../openspec/changes/redesign-score-confianca-estado/).

Toda oportunidade aberta recebe SCORE — inclusive as 1.425 sem conta vinculada (VALOR usa o prior neutro de porte) e as 500 em Prospecting (URGÊNCIA fixa em 0,47, sem idade imputada).

## Abertura direta no pipeline

A aplicação abre direto na aba Oportunidades, com a fila trabalhável (993 oportunidades — os três estados `Priorizar`/`Acompanhar`/`Qualificar`) já visível — não há tela de seleção de identidade nem sessão a manter. `Revisão em lote` (1.096 oportunidades sem precedente histórico) fica numa visão própria, fora da fila padrão. Vendedor, gerente e escritório regional são **filtros ordinários** sobre o funil inteiro, iguais a produto e confiança: qualquer valor presente nos dados pode ser escolhido, e o recorte resultante é refletido na URL — compartilhável e recarregável, ao contrário da sessão que existia antes.

Todo endpoint de dados é aberto, sem cabeçalho `Authorization`. Essa é uma decisão consciente para um dataset público de demonstração, sem informação real de cliente — não uma omissão. O trade-off e o caminho de produção (SSO/OIDC real, escopo aplicado no servidor) estão registrados em [`../docs/decisions-log.md`](../docs/decisions-log.md) e em "Limitações declaradas" abaixo.

## Estrutura

```
scoring/      pacote Python puro (sem FastAPI/React) — a fórmula, importada por api/ e validation/
api/          FastAPI — listagem paginada/ordenada, filtros comuns, detalhe de oportunidade, rollup, export
web/          React + TypeScript + Tailwind — abas Oportunidades/Gestão, filtros, painel de detalhe
validation/   evidência estatística executável — AUC, permutação, k, monotonicidade, concentração
```

Ver [`../docs/architecture.md`](../docs/architecture.md) para o mapa completo de cada módulo.

## Limitações declaradas

- **Sem autenticação.** Nenhum endpoint de dados exige identificação — qualquer cliente lê o funil inteiro. Aceitável apenas porque o dataset é público e de demonstração, sem informação real de cliente. Produção exigiria SSO/OIDC real e escopo por papel aplicado no servidor — nenhum dos dois existe hoje, nem parcialmente. Documentado, não escondido — evolução de produção registrada em `../docs/architecture.md`.
- **Sem persistência.** Tudo em memória, recarregado do zero a cada inicialização. Caminho de produção: banco gerenciado (Supabase ou equivalente).
- **Sem previsão categórica de win/loss.** `p̂` varia só entre 0,60 e 0,75 — a diferenciação real vem de valor e urgência, não de probabilidade. A evidência de que isso é uma escolha correta, não uma limitação técnica, está em `validation/`.
- **A distribuição de referência de SCORE** (negócios ganhos) só se atualiza no ciclo trimestral de recalibração — um negócio fechado ontem não entra no percentil até a próxima recalibração. Decisão deliberada: é o que torna SCORE estável entre requisições.
- **`K_PRODUTO = 4` é uma constante congelada desta calibração**, não recomputada a cada execução — ver a nota impressa por `validation/backtest.py` sobre o que a reprodução honesta do método encontra no nível de produto, e `../docs/decisions-log.md`.
