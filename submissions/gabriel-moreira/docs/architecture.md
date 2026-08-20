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
- FastAPI (REST API aberta — sem autenticação; listagem paginada, detalhe de oportunidade, rollup, `/score` para oportunidade avulsa)
- Pandas (ETL + data layer)

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
- Unitários: motor de scoring (encolhimento, curvas, censura, confiança, estado, plano de ação em passos)
- API: contrato dos endpoints sem autenticação, paginação (união de páginas sem repetição/lacuna, ordenação sobre o recorte inteiro, desempate estável), detalhe de oportunidade, opções de filtro, exportação de identificadores filtrados

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

#### Cálculo detalhado de p̂

A probabilidade de ganho é calculada em **três casos**, de forma determinística:

**1. Prospecting (sem `engage_date`):**
```
p̂ = p̂_produto
```
Usa apenas a taxa de vitória do produto, com encolhimento hierárquico aplicado. Sem ajuste de idade porque não há idade a medir — o lead ainda nem entrou no funil de venda estruturado.

**2. Engaging, idade > 138 dias (censura):**
```
p̂ = 0,632  (constante — o prior global)
```
Nenhum dos 6.711 negócios fechados históricos levou mais de 138 dias. Acima disso, revertemos ao prior em vez de extrapolar a curva — evita premiar abandono, que teria `p̂ = 0,751` se forward-fillássemos.

**3. Engaging, idade ≤ 138 dias (dentro da janela observada):**
```
p̂ = p̂_produto × p_ganho(min(idade, 120)) / 0,632
```
Ajusta a taxa do produto pela curva de ganho empírica. Dividi-se por 0,632 para renormalizar — `p_ganho(t)` é calibrada em absoluto, não como multiplicador.

**Exemplo:**
- GTX Pro: 64,8% taxa de vitória histórica (p̂_produto = 0,648)
- Oportunidade em Engaging, 57 dias de idade
- p_ganho(57) = 0,684 (regressão isotônica nos dados)
- p̂ = 0,648 × 0,684 / 0,632 = 0,702

#### Cálculo detalhado de URGÊNCIA

URGÊNCIA mede `P(o negócio se resolve nos próximos 30 dias | ainda aberto)` — é a probabilidade real de fechamento próximo, não um decaimento inventado. Também em **três casos**:

**1. Prospecting:**
```
URGÊNCIA = 0,47  (constante observada)
```
Representa a velocidade média de resolução para leads que entram no funil sem uma oportunidade formalizada. Calibrada empiricamente na população histórica.

**2. Engaging, idade > 138 dias (censura):**
```
URGÊNCIA = 0,15  (baixa — praticamente sem precedente)
```
Negocios com mais de 138 dias já perderam a janela normal de fechamento. A urgência cai drasticamente porque estadisticamente já não deveria estar aberto.

**3. Engaging, idade ≤ 138 dias:**
```
URGÊNCIA = risco(idade)
```
Leitura em degraus (step function) da curva isotônica calibrada:

| Idade (dias) | risco(t) | Interpretação |
|---|---:|---|
| 0–44 | 0,219 | Recém-aberto; apenas 21,9% resolvem nos próximos 30 dias |
| 45–56 | 0,322 | Começou a acelerar |
| 57–87 | 0,489 | Metade do ciclo; ~49% resolvem em 30 dias |
| 88–109 | 0,832 | Bem avançado; 83% dos negócios resolvem em 30 dias |
| ≥110 | 1,000 | Última reta; praticamente certo que resolve ou fecha |

**Exemplo:** mesma GTX Pro com 57 dias:
```
risco(57) = 0,489
```
Significa que, entre negócios em Engaging com 57 dias de idade, 48,9% resolvem (ganham ou perdem) nos próximos 30 dias — a urgência de ação é moderada, não baixa nem crítica.

### Censura acima de 138 dias

Nenhum dos 6.711 negócios fechados levou mais de 138 dias. Acima disso, o sistema **não extrapola** a curva — reverte ao prior (`p̂` = 0,632, URGÊNCIA = 0,15) em vez de aplicar forward-fill, que premiaria o abandono (daria `p̂` = 0,751 a um negócio de 377 dias, o mais alto da curva, exatamente ao mais parado do funil).

### CONFIANÇA — quanto se sabe sobre a oportunidade

CONFIANÇA responde a uma pergunta diferente de PRIORIDADE: "**quanto do necessário para pontuar esta oportunidade eu de fato tenho?**" — independente de quanto ela vale. É atribuída por regra determinística em ordem de precedência (censura > conta+Engaging > conta ou Engaging > resto):

#### Regras de atribuição

**1. Nível D — Censurado (idade > 138 dias)**
```
if stage == "Engaging" and age_days > 138:
    CONFIANÇA = D
```
Fora de qualquer precedente histórico. Nenhum negócio fechado levou mais de 138 dias — não há base factual para confiar em um score, mesmo que o número seja calculado.

**2. Nível A — Dados completos (conta + Engaging + dentro da janela)**
```
if stage == "Engaging" and has_account and age_days ≤ 138:
    CONFIANÇA = A
```
Conta conhecida, oportunidade formalizada, dentro da janela de ciclos observados. Máxima confiança — temos todos os ingredientes.

**3. Nível B — Dados parciais (conta OU Engaging, mas não ambos)**
```
if (stage == "Engaging" or has_account) and not (stage == "Engaging" and has_account):
    CONFIANÇA = B
```
Falta um dos dois: ou temos a conta mas o lead ainda é Prospecting (engajamento não confirmado), ou temos o negócio em Engaging mas sem conta vinculada (falta contexto). Moderada confiança.

**4. Nível C — Cadastro incompleto (sem conta e Prospecting)**
```
if not has_account and stage == "Prospecting":
    CONFIANÇA = C
```
Nem conta nem engajamento formalizado — é apenas um lead novo. O score é calculável, mas assenta em priors firmes (potencial de porte, taxa global).

#### Distribuição nos dados abertos

| Nível | Rótulo | Regra | % do funil | % da prioridade |
|---|---|---|---:|---:|
| **A** | Dados completos | conta ∩ Engaging ∩ idade ≤ 138 | 4,3% | 11,3% |
| **B** | Dados parciais | (conta ∪ Engaging) \ (conta ∩ Engaging) | 17,8% | 39,2% |
| **C** | Cadastro incompleto | ¬conta ∩ Prospecting | 16,1% | 20,2% |
| **D** | Fora do histórico | idade > 138 | 61,8% | 29,3% |

**Interpretação:** 61,8% do funil está em D — oportunidades paradas há mais de 138 dias, sem precedente no histórico. Mesmo assim, carrregam 29,3% da prioridade total (valor agregado alto, mas confiança baixa). A diagonal CONFIANÇA × SCORE é onde o operacional de verdade acontece — ver §ESTADO abaixo.

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

## Postura de segurança — sem autenticação

A API não exige identificação: todo endpoint de dados é aberto e opera sobre o funil completo, sem cabeçalho `Authorization`. Vendedor, gerente e escritório regional (a hierarquia real de `sales_teams.csv` — 35 agentes → 6 managers → 3 escritórios) são **filtros ordinários** sobre o funil inteiro, iguais a produto e confiança — nenhum deles restringe o que um cliente pode alcançar.

Essa é uma decisão consciente para um dataset público de demonstração, sem informação real de cliente, e está documentada como limitação assumida — não omitida (ver `decisions-log.md`). Produção exigiria SSO/OIDC real e escopo por papel aplicado no servidor, ambos hoje inexistentes. O que a API garante é apenas postura de segurança básica: CORS com origens enumeradas (nunca `*`), respostas de erro sem stack trace nem caminho de arquivo, e nenhum endpoint aceitando caminho de arquivo como parâmetro.

Rollup de gestão e download do dataset processado completo estão disponíveis a qualquer cliente, sem restrição de papel.

---

## Interface

A aplicação abre direto no pipeline — sem tela de identificação — na aba Oportunidades, com os cinco estados visíveis desde o primeiro carregamento.

### Tiles de indicadores (refletem o recorte filtrado)

```
[total] negócios · receita ganha [histórico] · valor esperado em aberto (soma de PRIORIDADE) · [n] em Desistir [ALERTA] · maior deal [histórico]

intervalo de datas | idade da oportunidade mais antiga do recorte | descrição dos filtros ativos
```

Os dois tiles históricos (receita ganha, maior negócio fechado) respondem só a filtros de organização e produto — nunca a estado, confiança ou idade, que só existem para o funil aberto — e são rotulados como tal. O tile de Desistir é o único elemento em cor de alerta (#AF4332) — reservada exclusivamente a ele, ao estado Desistir e a ações destrutivas.

### Filtros

Persistidos em URL params: vendedor, gerente, escritório, produto, confiança, estado (multi-seleção), faixa de idade (régua de dois cursores), página, ordenação e a oportunidade aberta no painel de detalhe. Vendedor/gerente/escritório são filtros comuns sobre o funil inteiro — nenhum é restrito por sessão. As opções vêm de `/filter-options`, não da página corrente da listagem.

### Duas abas

1. **Oportunidades** (inicial) — os cinco estados como filtro de chips (com contagem), listagem paginada no servidor (100 por página, ordenável por SCORE/PRIORIDADE/idade), painel lateral de detalhe ao abrir uma linha, e exportação de identificadores do recorte filtrado inteiro (não só da página carregada)
2. **Gestão** — disponível a qualquer cliente; rollup por vendedor/gerente/escritório + distribuição de esforço por produto; download do dataset processado completo

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
  requirements.txt          # -e ../scoring + fastapi/uvicorn/pydantic/pandas, tudo pinned
  main.py                     # monta a app, CORS, handlers de erro, inclui as rotas
  config.py                    # variáveis de ambiente com padrões seguros
  state.py                      # AppState: dataset+ctx+ref carregados uma vez na inicialização
  query.py                        # módulo de consulta compartilhado: filtros, ordenação com desempate por
                                   # opportunity_id, paginação — usado por /deals, /kpis, /rollup e /export/deal-ids
  routes/
    deals.py         # GET /deals (paginado/ordenado) · GET /deals/{id} (detalhe) · GET /filter-options
    kpis.py             # GET /kpis — filtros de organização/produto sempre; estado/confiança/idade só no funil aberto
    management.py         # GET /rollup — sempre os três níveis (vendedor/gerente/escritório)
    scoring.py               # POST /score (avulsa)
    export.py                   # GET /export/csv (dataset completo) · GET /export/deal-ids (identificadores filtrados)
  schemas.py, deps.py, errors.py, serialize.py
  tests/                          # contrato, paginação, detalhe, opções de filtro, indicadores — sem token/escopo

web/
  vite.config.ts        # proxy /api -> localhost:8000 em dev
  tailwind.config.js       # tokens de tema (navy/gold/bg/border/alert, radii 8/12/16/20/24)
  src/
    api.ts                     # cliente HTTP, sem cabeçalho de autenticação
    types.ts
    format.ts                     # formatUsd/formatPct/formatIdade/formatData — única fonte de formatação
    estadoColors.ts                  # mapa único de cor por ESTADO, usado em toda superfície
    hooks/                              # useUrlState (aba/filtros/estados/página/ordenação/deal na URL), useAsync
    components/                            # ViewTabs, EstadoChips, AgeRangeSlider, Tooltip, ConfidenceBadge,
                                            # FilterBar, KpiTiles, DealTable, DealDetailPanel, PaginationControls,
                                            # ManagementView
    App.tsx                                   # monta direto no pipeline; busca /deals paginado por filtro/página/ordenação

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

- **Autenticação.** Nenhum endpoint exige identificação — qualquer cliente lê o funil inteiro; vendedor/gerente/escritório são filtros, não escopo. Aceitável só porque o dataset é público e de demonstração. Produção exigiria SSO/OIDC real e escopo por papel aplicado no servidor.
- **Persistência.** Tudo em memória. Banco gerenciado (Supabase ou equivalente) necessário acima de ~100 MB de dados ou múltiplos usuários simultâneos escrevendo.
- **Previsão categórica de win/loss.** `p̂` varia só entre 0,60 e 0,75 — a diferenciação real é de valor e urgência, não de probabilidade. Instrumentar dados comportamentais primeiro (ver `analise-lead-scoring.md` §6).
- **Rebalanceamento automático de portfólio.** "39,6% de esforço em 5,4% de receita" é um insight na aba Gestão; a prescrição é decisão de RevOps, fora do sistema.
- **Write-back para CRM.** Desistir exporta CSV; sem connector de CRM.

### Evoluções óbvias (MVP → produção)

1. **Database:** Supabase + schema de deals, com trigger de auto-score e regeneração do CSV processado
2. **Auth real:** SSO/OIDC + escopo por papel aplicado no servidor sobre vendedor/gerente/escritório, hoje simples filtros sem restrição
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
