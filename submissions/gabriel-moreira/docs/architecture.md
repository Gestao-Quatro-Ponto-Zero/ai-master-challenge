# Arquitetura da Solução

Visão geral da implementação. Para a lógica de decisões que levou aqui, ver [decisions-log.md](./decisions-log.md). Espelha os requisitos formais em [`openspec/changes/add-lead-scorer/`](../../../openspec/changes/add-lead-scorer/).

---

## Visão geral

Ferramenta de triagem de pipeline por **valor em risco**, não por probabilidade de conversão categórica. A evidência: em 6.711 negócios fechados (out/2016–dez/2017), nenhum atributo firmográfico isolado (vendedor, conta, setor, gerente, escritório) prevê ganho/perda — AUC ≈ 0,50, testes de permutação com p entre 0,26 e 0,98. A calibração hierárquica confirma isso de outra forma: os níveis conta×produto e produto×setor têm variância em excesso zero e colapsam para peso zero automaticamente.

O que diferencia uma oportunidade da outra é **valor** (produtos de US$ 55 a US$ 26.768, 487×) e **tempo até a resolução** — não quem vende, para quem, ou em que setor.

**A fórmula:**

```
PRIORIDADE = P̂ganho(produto, idade) × VALOR(produto, porte) × URGÊNCIA(idade)
CONFIANÇA  = f(conta conhecida?, etapa, idade dentro da janela observada?)   →  A | B | C | D
```

Dois números, nunca combinados: PRIORIDADE ordena a fila (em dólares — "quanto está em jogo agora"), CONFIANÇA diz o quanto acreditar na posição (A a D). Um **ESTADO** deriva dos dois e vira a etiqueta de ação que o vendedor vê: **Foco urgente, Acompanhar, Engajar, Qualificar, Desistir**.

**Toda oportunidade aberta recebe PRIORIDADE — inclusive as 1.425 sem conta e as 500 em Prospecting.** A ausência de conta custa no máximo 8% de VALOR (prior neutro de porte), nunca a viabilidade do score.

---

## Stack técnica

**Backend:**
- Python 3.10+
- FastAPI (REST API, identificação por papel, `/score` para oportunidade avulsa)
- Pandas (ETL + data layer)
- Biblioteca de assinatura de token leve (sessão sem senha, escopo assinado no servidor)

**Frontend:**
- React 18+
- TypeScript
- Recharts (visualizações)
- Tailwind CSS

**Data:**
- CSV loader (in-memory pandas), atrás de um módulo repositório
- 8.800 linhas × 4 tabelas (accounts, products, sales_pipeline, sales_teams)
- Exportação: CSV consolidado com o dataset processado + scores, regravado a cada carga

**Deployment:**
- Docker Compose (API + React bundled)
- Python deps pinned em requirements.txt
- React build output servido pelo mesmo container

**Validação:**
- Script Python standalone (importa `scoring/`) que roda:
  - Backtest out-of-time nos 6.711 negócios fechados (AUC por atributo firmográfico)
  - Permutation tests sobre agent/product/sector/account
  - Reprodução do cálculo de `k` hierárquico e do colapso de conta×produto/produto×setor
  - Verificação de monotonicidade de `risco(t)` e da fronteira de 138 dias
  - Concentração de PRIORIDADE (top 10%/30%) vs. ranking por preço puro

**Testes:**
- Unitários: motor de scoring (encolhimento, curvas, censura, confiança, estado) e resolução de escopo de acesso
- E2E: ciclo completo da API — identificação, token, listagem respeitando escopo, tentativa fora do escopo, rollup restrito, download restrito a Manager

---

## Dados

### Carregamento

```
accounts (85 linhas)
  + country / sector / employees / revenue / year_established

sales_pipeline (8.800 linhas)
  + opportunity_id / deal_stage / engage_date / close_date / close_value

products (7 itens)
  + product / sales_price

sales_teams (35 linhas)
  + sales_agent / manager / regional_office
  → hierarquia real: 35 agentes → 6 managers → 3 escritórios (Central/East/West)

MERGE:
  sales_pipeline
    LEFT JOIN accounts ON account
    LEFT JOIN products ON product
    LEFT JOIN sales_teams ON sales_agent
```

### Tratamentos de qualidade

| Problema | Correção |
|---|---|
| `technolgy` typo em sector | → `technology` |
| `GTXPro` vs `GTX Pro` | → normalizar para `GTX Pro` (1.147 negócios) |
| 1.425 deals sem `account` | pontuáveis normalmente — VALOR usa prior neutro de porte (mult=1,00), CONFIANÇA cai para B ou C |
| 500 Prospecting sem `engage_date` | pontuáveis normalmente — `p̂` = `p̂_produto` sem ajuste de idade, URGÊNCIA fixa em 0,47 |
| bimodal cycle (picos 0–19d e 60–90d) | motivou a leitura das curvas de aging como função em degraus, não decaimento contínuo |

---

## Lógica de scoring

### PRIORIDADE

```
p̂ = (n_produto × taxa_produto + k × 0,632) / (n_produto + k)     ← encolhimento hierárquico, k derivado

  se Prospecting:      p̂ = p̂_produto (sem ajuste de idade)
  se idade > 138:       p̂ = 0,632                                  ← censura: reverte ao prior
  senão:                p̂ = p̂_produto × p_ganho(min(idade,120)) / 0,632

VALOR = preço_tabela(produto) × mult_porte(porte, default 1,00)

  se Prospecting:      URGÊNCIA = 0,47
  se idade > 138:       URGÊNCIA = 0,15
  senão:                URGÊNCIA = risco_isotônico(min(idade,120))

PRIORIDADE = p̂ × VALOR × URGÊNCIA                                  ← em dólares
SCORE      = percentil(PRIORIDADE) × 100                           ← contra o histórico de negócios GANHOS, não contra o funil aberto
```

**SCORE não é relativo ao funil aberto corrente** — é o percentil de PRIORIDADE contra a distribuição de PRIORIDADE calculada sobre os 4.238 negócios historicamente **ganhos** (usando a idade real de cada um no fechamento). Essa referência é histórica e fixa; só muda no ciclo trimestral de recalibração. Consequência prática: SCORE = 82 significa literalmente "esta oportunidade vale mais, em risco agora, do que 82% dos negócios que historicamente viraram receita" — e, ao contrário de um percentil contra o funil aberto, não se move porque outra oportunidade entrou ou saiu do pipeline.

`k` não é escolhido: `k = variância_esperada_por_acaso / variância_em_excesso`. Nos dados calibrados, conta×produto e produto×setor têm variância em excesso zero e colapsam (`k = ∞`) para o nível de produto (`k = 4`).

**Achado que inverte a intuição comum de lead scoring:** `p_ganho(t)` **sobe** com a idade (0,632 aos 0 dias → 0,751 aos 120 dias) — não desce. O que a idade consome é a **janela**: em 57 dias, metade das vitórias históricas já aconteceu; em 88 dias, restam 25%. Por isso URGÊNCIA usa `risco(t)`, a probabilidade real de resolução em 30 dias (suavizada por regressão isotônica), não um proxy de "quão velho é ruim".

### Censura acima de 138 dias

Nenhum dos 6.711 negócios fechados levou mais de 138 dias. Acima disso, o sistema **não extrapola** a curva — reverte ao prior (`p̂` = 0,632, URGÊNCIA = 0,15) em vez de aplicar forward-fill, que premiaria o abandono (daria `p̂` = 0,751 a um negócio de 377 dias, o mais alto da curva, exatamente ao mais parado do funil).

### CONFIANÇA

| Nível | Regra | % do funil aberto | % da prioridade total |
|---|---|---:|---:|
| **A** | conta conhecida **e** Engaging **e** idade ≤ 138 | 4,3% | 11,3% |
| **B** | conta **ou** Engaging (um dos dois) | 17,8% | 39,2% |
| **C** | sem conta e Prospecting | 16,1% | 20,2% |
| **D** | idade > 138 — censurado | 61,8% | 29,3% |

Responde "quanto do necessário para pontuar esta oportunidade eu de fato tenho" — independente de quanto ela vale.

### ESTADO — cruza CONFIANÇA e SCORE, substitui faixas e lanes

CONFIANÇA e ESTADO não são a mesma coisa: **CONFIANÇA é o quanto acreditar no score** (o fundamento — quanto se sabe sobre a oportunidade); **ESTADO é a ação recomendada**, e a ação certa depende tanto de quanto a oportunidade vale (SCORE) quanto de quão sólido é esse número (CONFIANÇA). Diamante/Ouro/Prata/Bronze e as três lanes antigas (Prioridades/Novos/Zumbis) deram lugar a uma única tabela de decisão 4×2:

| CONFIANÇA | SCORE ≥ 50 | SCORE < 50 |
|---|---|---|
| **A** | Foco urgente | Acompanhar |
| **B** | Acompanhar | Engajar |
| **C** | Engajar | Qualificar |
| **D** | Desistir | Desistir |

O corte de SCORE é 50 — a mediana da própria distribuição de referência (negócios ganhos), não uma constante extra a derivar e congelar.

A diagonal é o ponto: um SCORE alto com CONFIANÇA fraca (ex.: B) não vira Foco urgente — vira Acompanhar, porque agir com urgência sobre um número em que não se confia totalmente é o próprio risco que CONFIANÇA sinaliza. Um SCORE baixo com CONFIANÇA C não é Desistir — é Qualificar, porque falta informação, não necessariamente falta valor. CONFIANÇA D é a única regra de mão única: abaixo do suporte histórico dos dados (idade > 138 dias), nenhum SCORE calculado é confiável o bastante para justificar outra ação que não revisão em lote.

| Estado | Ação |
|---|---|
| **Foco urgente** | Priorizar contato agora — dado confiável, alto valor em jogo na janela |
| **Acompanhar** | Follow-up regular — ou o valor não é alto o bastante, ou a confiança não sustenta agir com urgência ainda |
| **Engajar** | Buscar a informação que falta (conta ou engajamento pleno) — o valor potencial já justifica o esforço |
| **Qualificar** | Enriquecer cadastro antes de tratar como tarefa priorizada — falta informação e o valor aparente é baixo |
| **Desistir** | Revisão em lote com o gestor — fechar ou descartar, não trabalhar individualmente |

### Explicabilidade e plano de ação

Cada oportunidade expõe:

```
Foco urgente · GTX Plus Pro · US$ 5.865,74 · confiança A
p̂ +0,764 · Valor US$ 5.865,74 · Urgência 1,00 → PRIORIDADE ≈ US$ 4.482,00
"Conta conhecida, negócio em Engaging, dentro da janela histórica.
 88% das vitórias já aconteceram nesta idade — priorize contato esta semana."
```

Texto gerado por template determinístico a partir dos componentes — nunca por um modelo não determinístico ou serviço externo, para preservar auditabilidade.

---

## Controle de acesso por papel

A hierarquia real de `sales_teams.csv` (35 agentes → 6 managers → 3 escritórios) mapeia diretamente nos três papéis pedidos:

| Papel | Origem do dado | Escopo |
|---|---|---|
| **Sales Agent** | nome só em `sales_agent` | as próprias oportunidades |
| **Supervisor** | nome em `manager` | oportunidades dos agentes que reportam a ele |
| **Manager** | um dos 3 `regional_office` | todas as oportunidades do escritório |

**Sem senha.** Uma tela de seleção de identidade troca o nome/escritório por um token assinado no servidor, com escopo já resolvido. Todo endpoint de dados aplica esse escopo no servidor — um filtro de cliente só pode **restringir** dentro do escopo, nunca ampliá-lo; pedir algo fora do escopo responde 403. Isso não é autenticação real (qualquer um pode se identificar com qualquer nome da lista) — é isolamento de escopo aplicado no servidor, documentado como limitação explícita. Produção exigiria SSO/OIDC.

O rollup de gestão é restrito a Supervisor/Manager. O download do dataset processado completo é restrito a Manager.

---

## Interface

### Tiles de indicadores (restritos ao escopo da identidade ativa)

```
[total] negócios · receita ganha · valor esperado em aberto (soma de PRIORIDADE) · [n] em Desistir [ALERTA] · maior deal

intervalo de datas | idade da oportunidade mais antiga do escopo | identidade ativa
```

O tile de Desistir é o único elemento em cor de alerta (#AF4332) — reservada exclusivamente a ele, à aba Desistir e a ações destrutivas.

### Filtros

Persistidos em URL params (exceto identidade, que exige nova seleção):

- **Vendedor, Supervisor, Escritório** — sempre restritos ao escopo do token
- **Produto**
- **Estado** (checkboxes, default todos)

### Abas

1. **Foco urgente** (inicial)
2. **Acompanhar**
3. **Engajar**
4. **Qualificar**
5. **Desistir** — com filtros de idade e exportação CSV dos IDs filtrados
6. **Gestão** — oculta para Sales Agent; rollup por agente/supervisor/escritório + distribuição de esforço por produto; download do dataset processado completo (só Manager)

### Tema

Paleta [G4 Business](https://g4business.com/):

```css
--navy-primary: #001F35
--gold-accent: #B9915B
--light-bg: #FAFBFC
--border: #E5E7EB
--text-main: #001F35
--text-muted: #64748B
--alert: #AF4332          /* exclusivo de Desistir e ações destrutivas */

Font: Manrope (body, headings)
Radii: 8, 12, 16, 20, 24px
```

Foco urgente usa o acento dourado (positivo/urgente), não a cor de alerta (reservada a Desistir).

---

## Como rodar

### Pré-requisitos

```
Python 3.10+
Node.js 18+ (para React)
Docker + Docker Compose (para deployment)
```

### Via Docker (comando único)

```bash
cd solution
docker compose up --build
```

Sobe `api` (porta 8000) e `web` (porta 8080, nginx servindo o build do React e
fazendo proxy de `/api/*` para o serviço `api`). Abra `http://localhost:8080`.

### Desenvolvimento local (sem Docker)

```bash
cd solution
make install   # cria os três venvs Python + npm install do web
make dev-api   # terminal 1 — uvicorn --reload, porta 8000
make dev-web   # terminal 2 — vite dev server, porta 5173, proxy /api -> :8000
```

### Validação / backtest

```bash
cd solution
make validate
# equivalente a: cd validation && .venv/bin/python backtest.py --data-dir ../../data
```

### Testes

```bash
cd solution
make test
# roda, em sequência: pytest em scoring/, pytest em api/ (unitário + e2e),
# pytest em validation/ (determinismo + consistência), tsc -b em web/
```

---

## Como os componentes se falam

Estrutura efetivamente implementada (substitui a estrutura prevista da versão anterior deste documento):

```
scoring/
  pyproject.toml           # pacote "scoring", instalado em modo editável por api/ e validation/
  scoring/
    __init__.py
    constants.py            # taxa global, k, breakpoints das curvas, preços, mult_porte — cada um com a origem citada
    repository.py           # load_dataset(): carga dos 4 CSVs, merge, correções de origem
    shrinkage.py             # compute_k(), level_stats(), p_hat_produto() — encolhimento hierárquico
    curves.py                 # p_ganho(t), risco(t) — leitura em degraus dos breakpoints calibrados
    model.py                   # p_hat(), valor(), urgencia(), prioridade() — a fórmula
    reference.py                 # distribuição de referência (PRIORIDADE dos negócios Won) e percentil -> SCORE
    confianca.py                  # atribuição de A/B/C/D
    estado.py                      # tabela de decisão 4x2 -> Foco urgente/Acompanhar/Engajar/Qualificar/Desistir
    explicacao.py                   # decomposição + texto de plano de ação (determinístico)
    export.py                        # CSV consolidado do dataset processado
    pipeline.py                       # load_and_score(): orquestra tudo acima
  tests/                              # unitário — 59 testes, inclui os exemplos de referência dos specs

api/
  requirements.txt          # -e ../scoring + fastapi/uvicorn/pydantic/itsdangerous/pandas, tudo pinned
  main.py                     # monta a app, CORS, handlers de erro, inclui as rotas
  config.py                    # variáveis de ambiente com padrões seguros
  state.py                      # AppState: dataset+ctx+ref carregados uma vez na inicialização
  auth/
    identity.py                  # deriva papel a partir de sales_teams (Sales Agent/Supervisor/Manager)
    scope.py                       # Scope, resolve_scoped_agents() — interseção filtro x escopo do token
    tokens.py                       # itsdangerous.URLSafeTimedSerializer — emissão/validação assinada
  routes/
    identity.py    # GET /identities · POST /identify
    deals.py         # GET /deals?estado=&sales_agent=&manager=&regional_office=&product=&confianca=&idade_min=&idade_max=
    kpis.py             # GET /kpis
    management.py         # GET /rollup (403 para Sales Agent)
    scoring.py               # POST /score (avulsa)
    export.py                   # GET /export/csv (Manager)
  schemas.py, deps.py, errors.py, serialize.py
  tests/                          # unitário (resolução de escopo) + contrato + e2e (ciclo completo, RBAC)

web/
  vite.config.ts        # proxy /api -> localhost:8000 em dev
  tailwind.config.js       # tokens de tema (navy/gold/bg/border/alert, radii 8/12/16/20/24)
  src/
    api.ts                     # cliente HTTP, injeta Authorization: Bearer <token>
    types.ts
    hooks/                        # useSession (sessionStorage), useUrlState (filtros/aba na URL), useAsync
    components/                      # IdentityPicker, KpiTiles, StateTabs, FilterBar, DealTable, ManagementView
    App.tsx                             # busca as oportunidades do escopo uma vez, filtra/ordena no cliente

validation/
  requirements.txt          # -e ../scoring + pandas/scikit-learn (lightgbm trocado por
                             # HistGradientBoostingClassifier — ver nota abaixo)
  backtest.py                  # comando único, relatório de texto completo em stdout
  model_training.py               # split cronológico + AUC isolada/combinada
  permutation_tests.py               # testes de permutação, semente fixa
  shrinkage_check.py                    # reproduz k por nível, honesto sobre o achado do nível "produto"
  isotonic_check.py                        # recalcula p_ganho(t)/risco(t), verifica monotonicidade e 138 dias
  concentration.py                            # top 10%/30% de PRIORIDADE vs preço bruto
  tests/                                         # determinismo + consistência artefato/CSV/API
```

**O crítico:** `scoring/` é uma dependência limpa, sem FastAPI ou React. API, exportação CSV e validação a importam via `pip install -e` — o número exibido, o número exportado e o número validado são sempre o mesmo cálculo (ver testes de consistência em `api/tests/test_e2e.py` e `validation/tests/test_validation.py`).

**Achado registrado durante a implementação:** `validation/shrinkage_check.py` recalcula k pelo mesmo método em todos os níveis da hierarquia e, sobre estes dados, encontra colapso (`k = ∞`) não só em conta×produto e produto×setor, mas também no nível de produto — mais fraco que qualquer um dos quatro atributos testados por permutação. `constants.K_PRODUTO = 4` é mantido como constante **congelada** desta calibração (não uma escolha nova), preservando a diferenciação de ~4,5 pontos entre produtos que o desenho já descrevia; o relatório do artefato imprime essa nota explicitamente a cada execução, para a próxima recalibração trimestral avaliar.

**lightgbm -> scikit-learn:** o desenho original previa lightgbm para o modelo combinado de AUC. Na implementação, `pip install lightgbm` falhou neste ambiente por exigir `libomp` nativo via Homebrew — o que quebraria "partida por comando único, sem passos manuais" em qualquer máquina sem a lib pré-instalada. `HistGradientBoostingClassifier` do próprio scikit-learn cobre o mesmo papel (gradient boosting) sem dependência nativa extra.

---

## Limitações conhecidas

### Não faz

- **Autenticação real.** Seleção de identidade sem senha, com escopo aplicado no servidor — não impede que alguém se identifique com o nome de outra pessoa. Produção exigiria SSO/OIDC.
- **Persistência.** Tudo em memória. Banco gerenciado (Supabase ou equivalente) necessário acima de ~100 MB de dados ou múltiplos usuários simultâneos escrevendo.
- **Previsão categórica de win/loss.** `p̂` varia só entre 0,60 e 0,75 — a diferenciação real é de valor e urgência, não de probabilidade. Instrumentar dados comportamentais primeiro (ver `analise-lead-scoring.md` §6).
- **Rebalanceamento automático de portfólio.** "39,6% de esforço em 5,4% de receita" é um insight na aba Gestão; a prescrição é decisão de RevOps, fora do sistema.
- **Write-back para CRM.** Desistir exporta CSV; sem connector de CRM.

### Evoluções óbvias (MVP → produção)

1. **Database:** Supabase + schema de deals, com trigger de auto-score e regeneração do CSV processado
2. **Auth real:** SSO/OIDC + os mesmos três papéis, agora com credencial de verdade
3. **Sinal comportamental:** webhook do CRM + log de atividade (email, call, mudança de estágio). Recalibrar `p̂` com speed-to-lead
4. **A/B testing:** metade dos vendedores prioriza pelo score, metade não; medir receita/trimestre
5. **Mobile:** React Native para fieldwork

---

## Validação

`solution/validation/backtest.py` reproduz:

- AUC ≈ 0,50 por atributo firmográfico isolado, em holdout temporal
- Testes de permutação (p entre 0,26 e 0,98) para vendedor/produto/setor/conta
- Colapso de `k` para conta×produto e produto×setor (variância em excesso ≤ 0)
- Monotonicidade de `risco(t)` e fronteira de 138 dias confirmada nos dados carregados
- Concentração de PRIORIDADE: top 10% da fila concentra ~50% do valor em risco total — comparado lado a lado com ranking por preço puro, rotulado como concentração, não como validação preditiva

Conclusão: **justifica ordenar por valor em risco, não por um classificador de probabilidade.** Os 62% do funil sem precedente histórico (Desistir) ficam deprioritizados, não zerados — carregam 29,3% da prioridade total, não 0%.

---

## Referências

- [analise-lead-scoring.md](../analise-lead-scoring.md) — análise exploratória completa
- [decisions-log.md](./decisions-log.md) — decisões e por quês, passo a passo
- [openspec/changes/add-lead-scorer/](../../../openspec/changes/add-lead-scorer/) — proposta, design e specs formais
