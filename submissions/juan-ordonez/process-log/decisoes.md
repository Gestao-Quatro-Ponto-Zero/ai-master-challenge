# Decisões e achados — Lead Scorer

Log incremental das decisões tomadas durante a construção, com os porquês.
Escrito em tempo real enquanto o trabalho acontecia.

---

## Setup do ambiente

- **Modelo:** Claude Code, Opus 4.6 (claude-opus-4-6[1m]), 1M context
- **Stack de análise:** Python 3.14 + pandas + numpy em `.venv` local
- **Origem dos dados:** mirror GitHub do Maven CRM Sales dataset (licença CC0), 4 CSVs baixados localmente

---

## Por que Lead Scorer (entre os 4 desafios)

Os 4 desafios do repo testam pesos diferentes de diagnóstico / estratégia / build. Escolhi o 003 porque:

- Bate diretamente com o diferencial listado na vaga: *"construir ferramentas internas e protótipos funcionais sem suporte de engenharia"*
- É o desafio mais "end-to-end" — do CSV ao produto que um vendedor usa
- É também o que tem o baseline LLM mais alto (qualquer pessoa com Cursor faz um Streamlit em 4h), então a diferenciação tem que vir de (a) profundidade de análise dos dados e (b) qualidade da UX

Trade-off aceito: o Support Redesign (002) testa mais pilares simultaneamente, mas é mais arriscado em 4-6h. O Lead Scorer tem escopo mais contido.

---

## Achados da exploração que moldaram o score

### O dataset não é de aquisição, é de cross-sell

- 85 contas, **cada uma com 51 a 200 deals** (mediana 83). Isso não é B2B real — é dataset sintético — mas o padrão é consistente: os vendedores não prospectam, eles decidem **a quem oferecer o quê** dentro de uma carteira fixa.
- Esta constatação mudou o enquadramento da ferramenta. Não é "qualificar leads"; é "priorizar cross-sell".

### Win rate global alto: 63.2%

- Won: 4238 (48%) · Lost: 2473 (28%) · Engaging: 1589 (18%) · Prospecting: 500 (6%)
- Win rate sobre fechados = 63.2%
- Implicação: o problema não é "vendedores fechando pouco". É onde eles gastam o tempo. O score precisa priorizar, não prever sucesso absoluto.

### Sinais FORTES (entraram no score)

**1. `is_new_combo`** (combo vendedor × conta × produto inédito)
- Boost de ~4pp isolado, mais quando combinado com tier
- Interpretação: quando alguém abre um combo novo, há motivo real — viés de seleção. Deals recorrentes fecham menos porque são tentativas repetidas.

**2. Histórico do vendedor** (win rate individual)
- Spread de 15pp entre top e bottom (70% vs 55%)
- Único sinal "humano/organizacional" com discriminação real
- Manager (2.3pp) e regional office (1.4pp) são ruído — descartados

**3. Valor = sales_price**
- Desconto médio observado: 0% a 1.5%. `close_value ≈ sales_price` nos Won.
- Valor potencial é determinístico — não precisa modelar negociação

### Sinais CONTRAINTUITIVOS

**Lost morre rápido, Won demora**
- Mediana Won: 57 dias
- Mediana Lost: 14 dias
- Win rate por faixa de duração é **monotônico positivo**: ≤30d → 57%, >120d → 76%
- **Implicação crítica para UX:** idade alta de um deal Engaging NÃO é sinal de risco. Se passou dos 30 dias sem virar Lost, está se aquecendo. O vendedor precisa saber disso — é o oposto da intuição.

### Sinais FRACOS (descartados, spread <5pp cada)

| Variável | Spread win rate |
|---|---|
| Setor (10 categorias) | 4pp |
| Produto (7) — p/ probabilidade | 5pp |
| Manager (6) | 2.3pp |
| Regional office (3) | 1.4pp |
| Receita da conta (quartis) | 4.5pp |
| Nº funcionários (quartis) | 2.6pp |
| Ano de fundação | 3.2pp |
| Subsidiária vs independente | 0.6pp |
| Local geográfico da conta | ruído (baixo volume fora dos EUA) |

Nenhum passa do limiar. Todos descartados do score. Produto sai como sinal de probabilidade, mas entra como magnitude via `sales_price`.

---

## Decisão: Caminho B (lookup empírico com fallback)

Considerei três caminhos:

| Caminho | Como | Veredito |
|---|---|---|
| A · Heurística aditiva com pesos manuais | `prob = base + boost1 + boost2` | **Rejeitado** — pesos arbitrários, difícil defender |
| **B · Lookup empírico + smoothing** | Agrupa por (tier, is_new_combo), usa win rate observado do bucket | **Escolhido** |
| C · Regressão logística rasa | 3-4 features, coefs calibrados | Rejeitado — log-odds ilegíveis para vendedor |

**Por que B ganhou:** a frase de defesa é "este score é o win rate observado em N deals históricos do mesmo perfil." Os pesos vêm dos dados, não do meu palpite. O brief diz literalmente "*explainability is the multiplier*" — B maximiza isso.

### Validação empírica da interação

Testei se `tier_vendedor × is_new_combo` **interagem** (multiplicativo) ou se **somam** (aditivo). Rodei a matriz cruzada de 6 buckets com 800-1400 deals cada, comparei o win rate real com a predição aditiva:

```
                      real    aditivo   delta
top + combo novo     68.4%    69.0%    -0.6
top + recorrente     65.6%    65.3%    +0.3
mid + combo novo     65.8%    65.6%    +0.2
mid + recorrente     61.9%    61.9%    +0.1
low + combo novo     61.7%    61.6%    +0.1
low + recorrente     57.8%    57.9%    -0.1
```

**Todos os deltas <0.6pp.** Não há interação detectável. Fórmula aditiva é suficiente e mais simples de explicar.

### Buckets finais (com smoothing k=30)

| tier | combo novo | combo recorrente | n (novo/rec) |
|---|---|---|---|
| **top** (wr ≥ 65%) | **68.2%** | 65.5% | 930 / 831 |
| **mid** (55-65%) | 65.7% | 61.9% | 1150 / 1418 |
| **low** (< 55%) | 61.7% | **57.8%** | 1157 / 1225 |

Smoothing Bayesiano `(n*wr + k*prior) / (n+k)` com k=30 e prior=0.632. Volume alto em todas as células — smoothing tem efeito trivial, mas mantemos a estrutura para consistência com deals hipoteticamente em buckets menores.

---

## Decisão: stack front — HTML estático + Tailwind + Alpine + data.js

Considerei Streamlit, Next.js, e HTML puro. Escolhi **HTML estático** por três razões:

1. **Maximiza tempo na lógica** — score + explicação são onde mora a diferenciação. Next.js come tempo em config; Streamlit luta contra state.
2. **Risco zero de quebrar na entrega** — sem build, sem servidor, sem cold start. Avaliador clica, funciona.
3. **Separa Python da apresentação** — a lógica está 100% em `score.py`, o front só renderiza. O avaliador lê o cérebro num só lugar.

**Streamlit foi descartado especificamente para este desafio** porque o brief pede ferramenta de vendedor, não dashboard de analista. Streamlit grita "notebook bonito" mesmo bem feito.

### Refinamentos críticos (capturados em revisão técnica)

1. **CORS em `file://`** — `fetch('data.json')` é bloqueado pelo Chrome em duplo-clique. **Solução:** `data.js` com `window.DATA = {...}` via `<script src>`. Resolve o problema por construção.
2. **CDN offline** — Tailwind e Alpine via CDN quebram sem internet. **Solução:** ambos baixados em `web/vendor/`. 10 min, risco zero.
3. **`is_new_combo` definição ambígua** — toda a calibração dos buckets depende disso. **Definição fixada:** combo `(vendedor, conta, produto)` nunca apareceu antes no histórico ordenado por `engage_date`. Inclui deals abertos. Exclui deals sem `account`.

---

## Decisões técnicas congeladas (Etapa 1)

Valores no momento do fechamento da Etapa 1 — **vários mudaram depois**
(ver seção "Evoluções e pivôs" abaixo).

1. **Nome da pasta:** `submission/` local → `submissions/juan-ordonez/` no fork
2. **Cortes de tier absolutos:** `top ≥65%`, `mid 55-65%`, `low <55%`
3. **`SNAPSHOT_DATE = 2018-01-01`** — `max(close_date) + 1`
4. **Thresholds classify_action (versão inicial):** `prob_high=0.65`, `prob_low=0.60`, `ev_high=3000`, `ev_med=1500`
5. **6 categorias de ação (versão inicial):**
   1. Qualificar primeiro (is_new_combo NaN)
   2. Agir hoje (prob ≥ 0.65 E ev ≥ 1500)
   3. Vale o esforço (ev ≥ 3000)
   4. Volume fácil (prob ≥ 0.65)
   5. Avaliar antes (prob < 0.60)
   6. Acompanhar (caso contrário)

---

## Evoluções e pivôs desde a Etapa 1

Esta seção captura o que foi decidido inicialmente mas **mudou ao longo
do trabalho**. As seções acima são o estado da Etapa 1; aqui é a trilha
das mudanças que se seguiram.

### Pivô 1 · Buckets recalibrados com cortes absolutos

**O que mudou:** os buckets mostrados acima (Etapa 1) foram calculados
com terços empíricos. Ao aplicar cortes absolutos (`top ≥65%`, `mid 55-65%`,
`low <55%`), os volumes mudaram bruscamente.

**Consequência:** tier `low` ficou literalmente com UMA PESSOA (Lajuana
Vencill, único vendedor <55%). 18 vendedores em mid, 11 em top.

**Valores finais calibrados:**

| tier | combo novo | combo recorrente | n (novo/rec) |
|---|---|---|---|
| top  | **68.1%** | 65.3% | 1052 / 946 |
| mid  | 63.5%     | 60.5% | 2093 / 2389 |
| low  | 63.9%     | **51.5%** | 92 / 139 |

**Decisão UX crítica:** tier virou **chave interna de lookup, nunca
exibida na UI**. Resolve o desbalanceamento sem estigmatizar ninguém —
os outros 30 vendedores nunca veem a palavra "low" na tela.

### Pivô 2 · Threshold fixo → ranking per-vendedor

**O que mudou:** a classificação inicial usava thresholds fixos
(`Agir hoje` = `prob ≥ 0.65 E ev ≥ 1500`). Ao rodar no smoke test,
56% dos deals fechados caíram em "Acompanhar" — categoria dominante e vaga.

**Primeira correção:** baixar `PROB_HIGH` de 0.65 → 0.63 (alinhar com
baseline global 0.632). Reduziu "Acompanhar" pra ~35%. Mas o usuário
identificou o problema real: mesmo assim, ~60% dos deals rankeáveis
caíam em "Agir hoje". **A ferramenta etiquetava, não priorizava.**

**Solução definitiva:** substituir threshold por **ranking per-vendedor**.
"Foco da semana" passou a ser atribuído em `build_data.py` por
`assign_weekly_focus`: top 30% do pipeline rankeável de cada vendedor,
piso 5, teto 15 (`FOCUS_PCT`, `FOCUS_MIN`, `FOCUS_MAX`).

**Resultado:** cada vendedor tem entre 5 e 15 deals em Foco da semana,
**relativo ao próprio pipeline**. A ferramenta prioriza de verdade.

### Pivô 3 · Taxonomia nomeada → P1-P4 + fora-da-escala

**O que mudou:** os 6 nomes da Etapa 1 (Agir hoje · Vale o esforço ·
Volume fácil · Avaliar antes · Acompanhar · Qualificar primeiro) eram
ambíguos do ponto de vista do vendedor. Descreviam *o que o deal é*,
não *o que o vendedor faz com ele*.

**Nova taxonomia** (5 categorias com prefixo hierárquico + âncora visual):

| Antes | Depois |
|---|---|
| Agir hoje / Foco da semana | 🎯 **P1 — Foco da semana** |
| Vale o esforço | 💰 **P2 — Foco secundário** |
| Volume fácil | ⚡ **P3 — Ganho rápido** |
| Avaliar antes | 🤔 **P4 — Repensar** |
| Acompanhar | (removido — virou redundante com o ranking) |
| Qualificar primeiro | 📋 **Atribuir conta** (fora da escala P) |

**Por que "Atribuir conta" ficou fora da escala P:** se chamasse "P0 —
Incompleto", pareceria "prioridade máxima". Na verdade é bloqueio
estrutural — fora do sistema de prioridade, não competindo por atenção.
Separar visualmente evita o mal-entendido.

### Pivô 4 · Nome do P2 refinado

**O que mudou:** primeira versão era "Grandes fora do foco" — descrevia
bem mas faltava simetria com P1. Renomeado para "**Foco secundário**",
simétrico com "Foco da semana" (P1) e sem conotação negativa.

### Pivô 5 · Card fixo → enxuto + expansão no clique

**O que mudou:** primeira proposta era card de 4 linhas sempre visíveis
(identificação + contexto + explicação completa). O usuário identificou
que uma pilha de 15 cards em P1 ficaria alta demais pra escanear.

**Solução:** card enxuto por default (3 linhas) + expansão no clique
revela frase completa, meta-info (confiança, N de casos similares,
estágio do CRM). Múltiplos podem estar expandidos simultaneamente
(não acordeão puro), permitindo comparação.

### Pivô 6 · Labels explícitos no card

**O que mudou:** o enxuto inicial tinha "68% · $5.482" (números soltos).
O usuário pediu labels explícitos: "**chance de fechar 68%**" e
"**aberto há 23 dias**". Mais claro, zero interpretação exigida.

### Pivô 7 · Manager volta como filtro de navegação (não como feature de score)

**O que mudou:** na Etapa 1, manager foi descartado como feature do
score (spread win rate 2.3pp, abaixo do limiar de 5pp). Na checagem
contra o README do challenge (antes de começar a codar a UI final),
notei que "filtro por manager/região" é **bônus explícito** do brief.

**Solução:** manager entra como **filtro de navegação**, não como
feature de score. Dropdown de vendedores agrupado por manager via
`<optgroup>` HTML. Cobre o bonus sem expandir escopo.

---

## Onde a IA errou e como corrigi (casos concretos)

### Caso 1 · `is_new_combo` calculado só sobre deals fechados

**O que aconteceu:** na primeira versão do script exploratório, calculei
`is_new_combo` olhando apenas deals Won/Lost, ignorando o pipeline aberto.
Isso deu um spread de ~10pp na feature isolada e fez a taxonomia inicial
parecer mais discriminante do que realmente era.

**Como corrigi:** ao incluir deals abertos como histórico, o spread caiu
pra ~4pp (mais fiel à realidade do scoring em tempo real). Propaguei a
correção nas estimativas e documentei a definição no docstring do `score.py`.

### Caso 2 · Thresholds do script exploratório copiados por inércia

**O que aconteceu:** o script `eda/06` usou thresholds 0.70 / 0.60 / 0.55
e valores $1000 / $2000 "chutados" na fase exploratória. Ao refatorar
pra `score.py`, esses números foram inicialmente copiados sem questionar.

**Como corrigi:** reescrevi `classify_action` do zero com `PROB_HIGH=0.63`
(alinhado ao baseline empírico 0.632) e deixei um comentário explícito no
plano de refatoração lembrando que código exploratório não deve ser
copiado sem revisão de premissas.

### Caso 3 · Explicação em linguagem de analista

**O que aconteceu:** a primeira versão do texto gerado por `build_explanation`
dizia: *"68% é o win rate histórico de vendedores top em combos novos
(1052 deals similares)."*

**Como o usuário corrigiu:** identificou que "win rate histórico" e
"vendedores top" são jargões de analista, não linguagem de vendedor. Pediu
uma versão pessoal, sem jargão, com endereçamento direto.

**Resultado:** *"Primeira vez oferecendo MG Advanced pra Ganjaflex.
Vendedores como você fecham 68% dos combos novos."* Dois ganhos:
(a) referência ao combo específico dá contexto imediato; (b) "vendedores
como você" é o eufemismo do tier sem expor o rótulo.

### Caso 4 · Categoria "Acompanhar" dominante — problema ignorado inicialmente

**O que aconteceu:** no smoke test, 56% dos fechados caíram em "Acompanhar".
A IA considerou a distribuição aceitável porque os *abertos* (que são o
que importa) ainda não tinham sido processados.

**Como o usuário corrigiu:** forçou a análise mais profunda ao ver que,
mesmo com ajuste de threshold, a categoria de ação ainda rotulava 60% do
pipeline sem priorizar de verdade. A solução foi dupla — ajustar threshold
*e* mudar o conceito para ranking per-vendedor. A mudança conceitual foi
a que realmente resolveu.

### Caso 5 · Distribuição dos 6 buckets apresentada sem desbalanceamento óbvio

**O que aconteceu:** ao propor os cortes de tier absolutos, a IA não
destacou imediatamente que `low` ficaria com apenas 1 vendedor. Foi
preciso rodar uma query específica no pandas para ver explicitamente.

**Como corrigi:** adicionei a verificação de distribuição de tiers como
parte do self-test conceitual, e a partir dessa descoberta nasceu a
decisão de "tier escondido da UI".

---

## Distribuição final das 5 categorias (2.089 deals abertos)

```
P1  Foco da semana       202   9.7%
P2  Foco secundário       16   0.8%
P3  Ganho rápido         346  16.6%
P4  Repensar             100   4.8%
 —  Atribuir conta      1425  68.2%
```

- **P1** — média 7.5 deals por vendedor (min 3, max 15), dentro da regra
  top 30% com piso 5 / teto 15
- **P2** é naturalmente raro: deals de valor alto tendem a entrar no top N
  do próprio vendedor. Os 16 restantes são majoritariamente deals de
  GTX Pro ($4.821) deslocados por deals ainda maiores do mesmo vendedor
  (GTK 500 $26.768, GTX Plus Pro $5.482)
- **Atribuir conta** domina em volume (68%) — insight central da ferramenta:
  **dois terços do pipeline aberto ainda não foi qualificado**. Esta
  mensagem é o primeiro valor que a ferramenta entrega a um gestor de RevOps

---

## Ainda pendente

- [ ] Screenshots do fluxo de trabalho (**usuário está capturando em paralelo**)
- [ ] Executive Summary e Abordagem no README da submissão (fase final)
- [ ] Loom curto de demonstração (fase final, opcional mas recomendado pelo template)
- [ ] Git workflow: fork do repo oficial + branch `submission/juan-ordonez` + PR
