# FASE 2 — Preparação dos Dados / Feature Engineering

**Challenge 002 — Redesign de Suporte (G4 Educação)**
**Data:** 2026-07-16 · **Autor:** Thales Barbosa (com Claude Code)

**Implementação (fonte única):** [`src/data_prep.py`](../src/data_prep.py) — features **e** premissas vivem no mesmo módulo versionado, consumido pelas fases 3, 5 e 6 (nada de cópias divergentes entre notebook, dashboard e simulador).
**Validação:** [`notebooks/feature_engineering.ipynb`](../notebooks/feature_engineering.ipynb) (executado de ponta a ponta) + [`tests/test_data_prep.py`](../tests/test_data_prep.py) (**14 testes, todos passando**).
**Saídas:** `data/processed/tickets_features.parquet` (8.469 × 40) e `data/processed/it_tickets_clean.parquet` (47.823 × 5).

**Processo:** a especificação desta fase foi submetida a um **painel de revisão com 3 lentes independentes** (rigor estatístico, negócio/ROI, avaliador do challenge) antes da implementação. Os ajustes exigidos pelo painel estão registrados em D-008/D-009 (`process-log/decisions.md`) e incorporados abaixo.

---

## 1. Convenção de status (dicionário machine-readable)

Cada feature nova tem um status declarado em `FEATURE_STATUS` (código), consultável programaticamente pela FASE 3+ via `features_by_status()`:

| Status | Significado | Regra de uso |
|---|---|---|
| `measured` (14) | Derivada direta de dado observado | Livre para análise e modelos |
| `target_derived` (3) | Derivada do `Customer Satisfaction Rating` | **Nunca** como preditor de satisfação (leakage trivial); restringe a amostra aos Closed |
| `synthetic_demo` (3) | Derivada dos timestamps sintéticos (D-005) | **Apenas** demonstrações rotuladas; proibida em agregados, gráficos de conclusão e modelos |
| `assumption` (2) | Calculada de premissas declaradas, não medida | Só conversão contábil volume→horas→custo; **proibida** como preditor ou em teste estatístico (tautologia: é função determinística de 3 categóricas) |
| `demo_only` (1) | Conteúdo de demonstração de UI (`description_demo`) | **Só** exibição no protótipo (FASE 6); proibida em treino/avaliação de modelo e em análises — guardrail coberto por teste (`test_demo_only_never_leaks_into_model_features`) |

A marcação sintética vai **no nome** (prefixo `synthetic_`), não só na documentação — sufixos em prosa não sobrevivem a um screenshot de dashboard.

---

## 2. Dataset 1 — dicionário de features (23 novas colunas)

### 2.1 Grupo A — Status, prioridade e cliente (`measured`)

| Feature | Definição | Fórmula | Justificativa |
|---|---|---|---|
| `is_closed` | Ticket resolvido | `Ticket Status == "Closed"` | Único subconjunto com satisfação/resolução (32,7%) |
| `is_open` | Ticket sem 1ª resposta | `Ticket Status == "Open"` | Estágio inicial do funil |
| `is_pending` | Aguardando cliente | `Ticket Status == "Pending Customer Response"` | Estágio intermediário |
| `is_unresolved` | **Backlog** (não fechado) | `NOT is_closed` (= Open ∪ Pending) | **Sinal central do diagnóstico pós-D-005**: 67,3% da base; a taxa de não-resolução é métrica válida onde os tempos não são |
| `is_critical` | Prioridade máxima | `Ticket Priority == "Critical"` | Pedida pelo plano; recorte de risco |
| `is_high_urgency` | Alta urgência | `Priority ∈ {High, Critical}` | Agregação útil p/ triagem (49,8% da base) |
| `priority_rank` | Prioridade ordinal | `{Low:1, Medium:2, High:3, Critical:4}` | Habilita correlações ordinais (Spearman na FASE 3) |
| `tickets_per_customer` | Tickets do mesmo e-mail | `count(Ticket ID) por Customer Email` | Único sinal relacional do dataset (288 tickets de clientes repetidos). *Caveat:* e-mails repetidos podem ser colisão do gerador sintético |
| `is_repeat_customer` | Cliente recorrente | `tickets_per_customer > 1` | Recorte de reincidência p/ FASE 3 |

Dtypes categóricos aplicados na carga: `Ticket Priority` como categórica **ordenada** (Low<Medium<High<Critical); Type/Status/Channel/Gender como categóricas — labels consistentes para todos os groupbys downstream.

### 2.2 Grupo A′ — Derivadas do rating (`target_derived`)

| Feature | Definição | Fórmula | Justificativa |
|---|---|---|---|
| `is_rated` | Tem avaliação | `Satisfaction Rating not null` | **Identidade estrutural nestes dados: `is_rated ≡ is_closed`** (validada por assert no pipeline). Mantida mesmo assim porque em operação real as duas divergem (fechado sem avaliação); a equivalência está documentada para ninguém "descobrir" correlação 1,0 |
| `is_dissatisfied` | Detrator | `rating ≤ 2` (boolean **anulável**; `NA` se não avaliado) | Alvo binário p/ FASE 3; 1.102 de 2.769 |
| `is_satisfied` | Promotor | `rating ≥ 4` (boolean anulável) | Simétrico; 1.087 de 2.769 |

**Guardrail anti-leakage:** derivam do próprio rating — usá-las como preditores de satisfação é vazamento trivial; qualquer uso restringe a amostra aos Closed (viés de seleção estrutural, D-006).

### 2.3 Grupo B — Tempo sintético (`synthetic_demo`, prefixo obrigatório)

| Feature | Definição | Fórmula | Justificativa |
|---|---|---|---|
| `synthetic_first_response_ts` | Timestamp (sintético) da 1ª resposta | `to_datetime(First Response Time)` | Parse preservado p/ rastreabilidade; NA estrutural para Open |
| `synthetic_resolution_ts` | Timestamp (sintético) da resolução | `to_datetime(Time to Resolution)` | Idem; NA para não-Closed |
| `synthetic_delta_resolution_minutes` | Delta entre os dois, **com sinal** | `(resolution_ts − first_response_ts)` em min | Preserva a evidência da auditoria (49,3% negativos). O sinal **não** é removido — `abs()` "lavaria" a prova de que não é duração |

**Nulos:** estruturais para os estágios sem o evento — `NaT` nos timestamps, `NaN` (float64) no delta — nunca imputados (D-006). (Dtypes anuláveis pandas — `boolean`/`Int32` — são usados nos grupos A′/D; aqui os tipos nativos de data/float já representam ausência corretamente.)

### 2.4 Grupo C — Esforço e custo estimados (`assumption`)

| Feature | Definição | Fórmula | Justificativa |
|---|---|---|---|
| `est_handle_minutes` | **Minutos de esforço de agente** no ciclo de vida completo do ticket (todas as interações + after-work) — *não* tempo de relógio | `aht_base(canal) × mult(tipo) × mult(prioridade)` | Âncora transparente para converter volume em horas (FASE 3), já que os tempos do dataset são sintéticos. Média resultante: 18,4 min/ticket (verificada no parquet) |
| `est_cost_brl` | Custo estimado do ticket (R$) | `est_handle_minutes / 60 × custo_hora_base` | Insumo direto do modelo de ROI; sem ele "quantificar desperdício em custo" não fecha |

Premissas completas na §3.

### 2.5 Grupo D — Texto e cliente (`measured`)

| Feature | Definição | Fórmula | Justificativa |
|---|---|---|---|
| `description_chars` / `description_words` | Comprimento da descrição | `len` / `len(split())` | Proxy de complexidade do relato |
| `description_demo` | Descrição com placeholder resolvido | `replace("{product_purchased}", Product Purchased)` | **Status `demo_only` — uso exclusivo em demonstração de UI (FASE 6).** Nunca em treino/avaliação de modelo — é texto template sintético (auditoria §1.5); o nome `_demo` + o status machine-readable + um teste dedicado garantem que não vaza para listas de features de modelo |
| `resolution_chars` / `resolution_words` | Comprimento da resolução (Int32 anulável, só Closed) | idem sobre `Resolution` | Caracteriza respostas na FASE 3; custo zero |
| `age_group` | Faixa etária | `cut(idade, [18-30, 31-43, 44-56, 57-70])`, fechados à direita | Bins de largura ~igual (13/13/13/14 anos): idade é uniforme — bins desiguais criariam contagens desiguais por artefato de binagem |

### 2.6 Rastreabilidade — as 7 features-exemplo do plano mestre

O plano (SYSTEM_INSTRUCTIONS, FASE 2) lista 7 features como *exemplos*. Uma linha por feature, nenhuma omitida:

| Feature pedida | Status | Como foi endereçada |
|---|---|---|
| `is_closed` | ✅ criada | §2.1, literal |
| `is_pending` | ✅ criada | §2.1, literal |
| `is_critical` | ✅ criada | §2.1, literal |
| `resolution_minutes` | 🔁 adaptada | → `synthetic_delta_resolution_minutes` (§2.3): é a **única** duração derivável dos dois timestamps, mantida com sinal e prefixo sintético. Fórmula pretendida pelo plano (fechamento − abertura) é incomputável |
| `response_minutes` | ❌ N/A | Fórmula pretendida: `first_response_ts − created_ts`. **Não existe timestamp de abertura no dataset** (Date of Purchase é a compra do produto, 518–1.248 dias antes — auditoria §2.1). Criar coluna 100% NaN seria burocracia com risco de uso acidental. **Recomendação de instrumentação ao cliente: registrar `created_at`** — habilita esta métrica imediatamente |
| `total_handling_minutes` | ❌ N/A | Fórmula pretendida: `resolution_ts − created_ts`. Mesma causa e mesma recomendação |
| `sla_violation` | 🔁 mecanismo real, coluna não materializada | Ver §4 (D-009) |

### 2.7 Features negadas (decisão explícita, não esquecimento)

| Feature candidata | Por que NÃO |
|---|---|
| `sla_violation` como coluna | D-009 — taxa calculada sobre delta sintético é ruído com cara de métrica; ver §4 |
| `purchase_to_response_days` | Gap de 518–1.248 dias entre duas âncoras sintéticas — sem significado |
| `response_hour`, `day_of_week`, `month` e **qualquer agregação temporal** | 3 dias de calendário, hora uniforme 0–23 (evidências do sorteio) — a classe inteira de features temporais fica vetada, não só um exemplo. A hora do FRT é computável on-demand de `synthetic_first_response_ts` para demonstrações |
| `automation_tier` / potencial de automação por tipo | Pertence à FASE 4 (exige os critérios de risco/julgamento definidos lá). Registrado aqui para não parecer omissão; a estrutura da tabela nascerá em `automation_strategy.md` e alimentará o ROI |

---

## 3. Premissas declaradas (fonte única: constantes de `src/data_prep.py`)

**Origem, com honestidade:** valores são **premissas do autor** na ordem de grandeza de benchmarks públicos de suporte/CX; não há fonte única auditável por valor. Por isso: (a) cada premissa central tem **faixa low/base/high**; (b) a análise de sensibilidade da FASE 3 e os sliders do ROI Simulator (FASE 6) variam essas faixas; (c) qualquer número downstream derivado delas é rotulado como estimativa premissa-based, nunca como medição.

### 3.1 Esforço de agente por ticket (minutos, ciclo de vida completo)

| Canal | low | **base** | high | Racional |
|---|---|---|---|---|
| Email | 12 | **18** | 25 | Assíncrono multi-toque: 2–3 interações de ~6–8 min |
| Phone | 10 | **15** | 22 | Síncrono 1:1: chamada 8–10 min + registro/after-call 3–5 min |
| Social media | 10 | **15** | 22 | Resposta pública + follow-up em DM; risco reputacional |
| Chat | 6 | **10** | 16 | ~15–18 min de relógio ÷ concorrência de 1,5–2 sessões/agente |

Definição operacional: **minutos de agente**, não de relógio — inclui after-work e multi-toque (por isso e-mail > telefone, e chat é o mais barato apesar de sessões longas).

### 3.2 Multiplicadores de esforço (valor único, premissa do autor)

| Tipo | mult | | Prioridade | mult |
|---|---|---|---|---|
| Technical issue | 1,5 | | Critical | 1,4 |
| Refund request | 1,2 | | High | 1,2 |
| Cancellation request | 1,1 | | Medium | 1,0 |
| Billing inquiry | 1,0 | | Low | 0,9 |
| Product inquiry | 0,8 | | | |

Sensibilidade dos multiplicadores é coberta pela variação do AHT base (não têm faixa própria — decisão de parcimônia).

**Premissa estrutural declarada:** o modelo é multiplicativo — assume **independência** entre canal, tipo e prioridade (sem interações). É escolha de modelagem, não fato medido.

### 3.3 Custo e anualização

| Premissa | low | **base** | high | Racional |
|---|---|---|---|---|
| Custo carregado do agente (R$/h) | 30 | **40** | 55 | Salário BR R$ 2,5–3,5k + encargos (~1,7×) ÷ ~140h produtivas/mês |
| Fator de anualização | — | **3,542** | — | `30.000 / 8.469` (D-001: amostra → operação declarada de 30k tickets/ano) |
| Matriz de SLA (h por prioridade) | — | Critical 4 · High 8 · Medium 24 · Low 48 | — | **Ilustrativa** (premissa do autor, ajustável); usada só pela função `sla_violation` em demos |

---

## 4. `sla_violation` — mecanismo real, coluna não materializada (D-009)

O plano pedia `sla_violation` como feature. O painel de design (3/3 lentes) apontou que materializá-la sobre o delta sintético criaria uma "taxa de violação" com cara de métrica real — risco máximo de contaminação de dashboard. Solução implementada:

1. **Função pura `sla_violation(duration_minutes, priority, targets_hours)`** em `src/data_prep.py` — a regra **real** de produção (`duração ≥ 0 > alvo`, **sem** `abs()`), com durações negativas tratadas como input inválido → `NA` (nunca `False` silencioso). Coberta por 5 testes unitários.
2. **Nenhuma coluna de SLA no parquet** (garantido por teste: `test_d1_shape_and_no_sla_column`).
3. **Demonstração tripla no notebook** (§1.3): (a) função correta sobre durações fabricadas válidas; (b) alimentada com o delta sintético, ela **rejeita 49,3% do input** como duração negativa — o próprio mecanismo prova que o delta não é duração; (c) **prova analítica**: se alguém calculasse a taxa mesmo assim, obteria `P(delta > t) = (1 − t/24)²/2` da distribuição triangular do gerador — verificado: Critical teórico 34,7% vs observado 32,5%; High 22,2% vs 22,4%; Medium/Low 0% vs 0%.

**Guardrail escrito:** nenhum agregado/gráfico de SLA sobre os tempos sintéticos nas fases 3–7. Se o protótipo (FASE 6) exibir um widget de SLA, será alimentado por durações simuladas *declaradas* ou pelo mecanismo aguardando dados reais — nunca pelo delta.

---

## 5. Dataset 2 — preparação

| Item | Decisão | Justificativa |
|---|---|---|
| `doc_id` | Atribuído **antes** do filtro = índice da linha no CSV bruto | Rastreabilidade permanente (os 14 removidos são identificáveis: 6 Hardware, 4 HR Support, 2 Miscellaneous, 1 Access, 1 Purchase) |
| `word_count` / `char_count` | `len(Document.split())` / `len(Document)` — tokenização: **`str.split()` em whitespace** (declarada p/ reprodutibilidade do filtro) | Insumo p/ filtro e p/ análise de comprimento na FASE 5 |
| Filtro de qualidade | Remove docs com `word_count < 3` → 47.837 → **47.823** | 14 docs (0,03%) sem conteúdo classificável |
| `Topic_group` | Dtype category com **mapeamento congelado** `TOPIC_CLASSES` (ordem alfabética, código 0–7) | FASE 5 não redefine encoding — comparabilidade garantida entre experimentos |
| Split/vetorização | **Não feitos aqui** | Pertencem à FASE 5 (com estratificação, D-007) |

---

## 6. Caveats e riscos registrados

1. **Booleans anuláveis** (`is_dissatisfied` etc.) sobrevivem ao round-trip parquet (testado no notebook), mas têm suporte irregular em libs de visualização — a FASE 6 converte explicitamente antes de plotar.
2. **`est_*` correlaciona com prioridade/canal por construção** — qualquer "achado" envolvendo essas colunas é tautologia; guardrail no dicionário (§1) e no docstring.
3. **`description_demo` parece texto real** — o nome marca o uso exclusivo em UI; o classificador da FASE 5 treina no Dataset 2 (domínio TI corporativo; a ponte para o contexto B2C do Dataset 1 será explicitada na estratégia da FASE 4).
4. **Diagnóstico premissa-dependente:** com volumes uniformes (auditoria §1.4), rankings de horas/custo por segmento derivam majoritariamente da tabela de premissas, não dos dados — a FASE 3 fará o disclosure e testará quais conclusões sobrevivem à variação low/high.

---

**Status da FASE 2: ✅ concluída** (espec revisada por painel de 3 lentes; artefatos verificados por 4 agentes adversariais — achados corrigidos, ver `process-log/iterations.md`). Artefatos: `src/data_prep.py`, `tests/test_data_prep.py` (14 ✅), `notebooks/feature_engineering.ipynb`, `data/processed/*.parquet`, este dicionário. Decisões novas: D-008, D-009 (`process-log/decisions.md`). Próxima fase (aguardando gate): **FASE 3 — Responder o Desafio**.
