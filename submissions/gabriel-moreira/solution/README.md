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

Roda, em sequência: os testes unitários do motor de scoring (`scoring/`, 59 testes — inclui os exemplos de referência dos specs), os testes unitários de resolução de escopo e os testes de contrato/e2e da API (`api/`, cobrindo o ciclo completo de RBAC: identificação → token → listagem restrita → 403 fora do escopo → 401 sem token → rollup restrito por papel → download restrito a Manager), os testes de determinismo e consistência do artefato de validação (`validation/`), e a checagem de tipos do frontend (`web/`).

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
PRIORIDADE = p̂ × VALOR × URGÊNCIA                    (dólares, estável — nunca muda por causa do funil)
SCORE      = percentil(PRIORIDADE) × 100              (contra os 4.238 negócios historicamente ganhos)
CONFIANÇA  = A–D                                       (quanto se sabe sobre a oportunidade)
ESTADO     = f(CONFIANÇA, SCORE≥50)                    (Foco urgente / Acompanhar / Engajar / Qualificar / Desistir)
```

PRIORIDADE e CONFIANÇA nunca se combinam num único número — um ordena a fila, o outro diz o quanto acreditar na posição. A decomposição completa, com os exemplos de referência e o porquê de cada peça, está em [`../docs/architecture.md`](../docs/architecture.md) e nos specs formais em [`../../../openspec/changes/add-lead-scorer/specs/`](../../../openspec/changes/add-lead-scorer/specs/).

Toda oportunidade aberta recebe PRIORIDADE — inclusive as 1.425 sem conta vinculada (VALOR usa o prior neutro de porte) e as 500 em Prospecting (URGÊNCIA fixa em 0,47, sem idade imputada).

## Papéis de acesso

Sem senha — uma tela de seleção de identidade troca um nome (ou escritório) por um token de sessão assinado no servidor (`itsdangerous`), com papel e escopo derivados de `sales_teams.csv` no momento da identificação:

| Papel | Origem | Escopo |
|---|---|---|
| **Sales Agent** | nome só em `sales_agent` | as próprias oportunidades |
| **Supervisor** | nome em `manager` | oportunidades dos agentes que reportam a ele |
| **Manager** | um dos 3 `regional_office` | todas as oportunidades do escritório |

Todo endpoint de dados aplica esse escopo no servidor: um filtro do cliente só pode **restringir** dentro do escopo, nunca ampliá-lo — pedir algo fora do escopo responde 403; requisição sem token responde 401. Isso é **seleção de identidade, não autenticação real** — qualquer um pode se identificar com qualquer nome da lista. O que é real é o isolamento de escopo depois disso, aplicado e testado no servidor (`api/tests/test_e2e.py`), não só ocultado na interface.

## Estrutura

```
scoring/      pacote Python puro (sem FastAPI/React) — a fórmula, importada por api/ e validation/
api/          FastAPI — identificação por papel, listagem/filtros/rollup/avulsa/export, tudo com RBAC
web/          React + TypeScript + Tailwind — seleção de identidade, 5 abas de estado + Gestão
validation/   evidência estatística executável — AUC, permutação, k, monotonicidade, concentração
```

Ver [`../docs/architecture.md`](../docs/architecture.md) para o mapa completo de cada módulo.

## Limitações declaradas

- **Sem autenticação por senha.** Identificação com escopo aplicado no servidor, não SSO/OIDC. Documentado, não escondido — evolução de produção registrada em `../docs/architecture.md`.
- **Sem persistência.** Tudo em memória, recarregado do zero a cada inicialização. Caminho de produção: banco gerenciado (Supabase ou equivalente).
- **Sem previsão categórica de win/loss.** `p̂` varia só entre 0,60 e 0,75 — a diferenciação real vem de valor e urgência, não de probabilidade. A evidência de que isso é uma escolha correta, não uma limitação técnica, está em `validation/`.
- **A distribuição de referência de SCORE** (negócios ganhos) só se atualiza no ciclo trimestral de recalibração — um negócio fechado ontem não entra no percentil até a próxima recalibração. Decisão deliberada: é o que torna SCORE estável entre requisições.
- **`K_PRODUTO = 4` é uma constante congelada desta calibração**, não recomputada a cada execução — ver a nota impressa por `validation/backtest.py` sobre o que a reprodução honesta do método encontra no nível de produto, e `../docs/decisions-log.md`.
