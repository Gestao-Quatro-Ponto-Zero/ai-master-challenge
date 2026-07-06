# Prompt 07 — Teste de uso pelo Head de RevOps (AGENT-D)

> **Prompt emitido:**

```
[AGENT: REVOPS-EXPERT]

Aqui está o output do app rodando em dados reais:
{colar prints/JSON de exemplo}
Como Head de RevOps julgando:
- O que você usaria amanhã?
- O que confunde?
- O que falta (próximas 3 iterações)?
Seja brutalmente honesto — não é elogio que me ajuda.
```

---

## Output real do app colado para o Head de RevOps

> Capturado via Playwright em `http://localhost:8503`, hoje=2025-07-01,
> 4.708 deals abertos, sem filtros aplicados.

### Estado padrão do app (default filters)

```
Page title: Lead Scorer — G4
Layout: wide, sidebar expanded

═══════════════════════════════════════════════════════════════════════
 KPI HEADER
═══════════════════════════════════════════════════════════════════════
  Deals ativos:     4.708
  Score médio:      32,8
  Valor em jogo:    R$ 10.298.556
  Top deal:         71 · OPP_03446 (Bianca Costa · GTX Enterprise · R$ 22.956)

═══════════════════════════════════════════════════════════════════════
 TOP 10 DEALS PARA FOCAR AGORA (sidebar: top N = 10, score min = 0)
═══════════════════════════════════════════════════════════════════════

  #1  OPP_03446   Bianca Costa · GTX Enterprise · account_0077 · Engaging · R$ 22.956
                  [71 · Morno]
                  ▷ Por que este score?
                  ─────────────────────────────────────────────────────
                  score 71/100 — puxado por Estágio: Engaging + Idade: 30 dias
                  no pipeline — atenção: Conta: receita $108.526, 1.458 funcionários

                      Estágio: Engaging              90,0 × 25% = 22,5
                      Idade: 30 dias no pipeline     100,0 × 20% = 20,0
                      Conta: receita $108.526        13,0 × 20% = 2,6
                      Produto: GTX Enterprise $25K   83,3 × 15% = 12,5
                      Vendedor: Bianca Costa — 60%   66,7 × 15% = 10,0
                      Valor: $22.956                 76,5 × 5%  = 3,8
                  ─────────────────────────────────────────────────────

  #2  OPP_01814   Paulo Pereira · GTX Enterprise · account_0058 · Engaging · R$ 17.037
                  [71 · Morno]  ▷ Por que este score?

  #3  OPP_07228   Sandro Silva · GTX Enterprise · account_0026 · Engaging · R$ 9.301
                  [70 · Morno]  ▷ Por que este score?

  #4  OPP_06953   Tatiana Alves · GTX Enterprise · account_0037 · Engaging · R$ 14.541
                  [68 · Morno]  ▷ Por que este score?

  #5  OPP_04340   Denis Alves · GTX Enterprise · account_0025 · Engaging · R$ 12.127
                  [68 · Morno]  ▷ Por que este score?

  #6  OPP_00363   Leandro Costa · GTX Enterprise · account_0065 · Engaging · R$ 6.982
                  [67 · Morno]  ▷ Por que este score?

  #7  OPP_00985   Leandro Costa · GTX Enterprise · account_0032 · Engaging · R$ 10.412
                  [66 · Morno]  ▷ Por que este score?

  #8  OPP_04973   Yuri Alves · GTX Enterprise · account_0058 · Engaging · R$ 13.609
                  [65 · Morno]  ▷ Por que este score?

  #9  OPP_02814   Eduarda Silva · GTX Enterprise · account_0057 · Engaging · R$ 11.602
                  [65 · Morno]  ▷ Por que este score?

  #10 OPP_07505   Gisele Alves · GTX Enterprise · account_0019 · Engaging · R$ 3.000
                  [65 · Morno]  ▷ Por que este score?

═══════════════════════════════════════════════════════════════════════
 SIDEBAR FILTROS (todos default = "Todos")
═══════════════════════════════════════════════════════════════════════
  • Vendedor [Todos ▾]        → lê valores reais do sales_teams.csv
  • Manager [Todos ▾]         → lê valores reais (Diana/Melvin/Kym)
  • Escritório [Todos ▾]      → lê valores reais (SP/RJ/BH/Curitiba/Recife)
  • Stage [Todos ▾]           → lê valores reais
  • Score mínimo [0 ──●── 100]
  • Mostrar top N deals [5 ──●──10──── 50]

═══════════════════════════════════════════════════════════════════════
 TABELA COMPLETA (4.708 linhas, scrollable)
═══════════════════════════════════════════════════════════════════════
  Colunas: opportunity_id | sales_agent | manager | regional_office
           | product | account | deal_stage | close_value | score | summary
  Score renderizado como ProgressColumn (barra visual 0-100)
  Valor formatado em R$

═══════════════════════════════════════════════════════════════════════
 CHARTS (2 colunas)
═══════════════════════════════════════════════════════════════════════
  [esquerda] Histograma "Distribuição de scores no pipeline filtrado"
             Bandas verticais verde (50-100) / amarelo (50-80) / vermelho (0-50)
             Pico concentrado em 23-38 (Q1=23,5, mediana=33,8, Q3=38,2)

  [direita] Scatter "Score × Valor esperado"
           Cor por deal_stage (Engaging navy, Prospecting amarelo)
           Hover: opportunity_id, sales_agent, account

═══════════════════════════════════════════════════════════════════════
 FOOTER "ℹ️ Como o score é calculado" (expansor)
═══════════════════════════════════════════════════════════════════════
  Tabela markdown com 6 componentes, pesos e justificativa de cada um
```

---

# Resposta do Head de RevOps (AGENT-D) — brutalmente honesta

> **Persona:** Head de RevOps. Segunda-feira, 9h, café na mão.
> Vejo pipeline de 8.800 deals, 35 vendedores. Tempo de resolução subiu.
> Quero saber: **onde coloco meus vendedores ESTA SEMANA**.

## O que eu usaria amanhã ✅

### 1. O ranking top-10 com score E explicação
Isso é o coração. Acabou a conversa de "qual deal priorizar?" —
abro o app, leio o top-10, mando mensagem no Slack pros 10 vendedores
"toca esses hoje antes do almoço". O breakdown em "puxado por X + Y"
é legível até pro meu estagiário. **Isto é útil.**

### 2. Filtros por Manager e Escritório regional
Eu tenho 3 managers e 5 escritórios. Posso filtrar por "Diana
Reinehr" e ver só os deals do time dela, ou filtrar "Recife" pra
entender se aquela região tá aquecendo. **Exatamente o que o README
do challenge pedia** ("imediatamente mais útil"). Acertou.

### 3. KPI "Valor em jogo" = R$ 10.298.556
Esse número eu levo pra reunião de board terça-feira. É o pipe aberto
total — forte pra discussão de forecast. O top deal com score 71
já me dá um nome prioritário pra destacar no 1:1 com a Bianca.

### 4. Histograma com bandas coloridas
Vejo imediatamente que o pipe médio tá em 32-38 — região "Fria".
Isso é alerta: a maioria dos deals tá com score baixo, ou eu tenho
muitos deals imaturos (Prospecting novo) ou muitos deals esfriando.

### 5. Expansor "Como o score é calculado" lá embaixo
Quando alguém questionar "de onde saiu 71?", eu aponto pra tabela
pública. Transparência = credibilidade interna. **Bom.**

---

## O que confunde 🤨

### C1. Todos os top-10 deals são GTX Enterprise
Olha os top 10 deals — TODOS são "GTX Enterprise". Isso me preocupa
porque slewbe (a) o modelo de scoriz está **super-recompensando
produto de ticket alto** (15% peso + 25K cap), ou (b) realmente só
esses deals são quentes. Não consigo distinguir. Será que outros
produtos mais baratos também têm deals quentes que estou ignorando?

**Risco operacional:** se eu só focar em GTX Enterprise nesta semana,
deixo unidades de Analytics Plus e API Gateway esfriarem — onde
talvez tenha mais volume menor mais previsível.

### C2. Score médio de 32,8 é "Frio" — mas eu tenho 4.708 deals!
Se a maioria é "Fria", o que significa "Frio"? É None uLocal deal
output? Sem referência comparativa (score médio histórico, score
médio por manager, score médio do top quartil) eu não sei se 32,8
é **bom** ou **ruim**. Precisa de benchmark.

### C3. Nenhum deal com score ≥ 80 ("Quente") — e agora?
Vou abrir o app segunda e ver zero badges verdes. Meus vendedores
vão perguntar " cadê os quentes?". Se a métrica sempre mostra
"todos mornos/frios", a discriminação fica sem sentido prático
(efeito washing machine — tudo virou cor one).

### C4. Nome do vendedor appara no card e na tabela
Se eu usar isto num comitê com stakeholders externos (board, board
advisor, potencial investidor), **não posso expor nomes reais de
vendedores**. Preciso de toggle "modo apresentação" que mostra
`agent_01` em vez de `Bianca Costa`.

### C5. Não tem como "assumir" ou "descartar" um deal
Depois de o vendedor tocar o deal OPP_03446, como marca que já
tratou? Hoje ele tem que ir no CRM externo e atualizar lá, depois
voltar pra app e ver que ainda tá score 71. **Falta ação.**

### C6. O "Resumo" do deal na tabela colapsada pode ficar longo
Tipo `score 71/100 — puxado por Estágio: Engaging + Idade: 30 dias
no pipeline — atenção: Conta: receita $108.526, 1.458 funcionários`.
Numa tabela com 4.708 linhas, isso vira poluição visual. Talvez
resumir para 50 chars.

### C7. `account_0077` como ID — não fala nada pra mim
Meus vendedores não sabem o que é `account_0077`. Preciso ver o
**nome da empresa cliente**, ou pelo menos setor e país. Hoje o
card mostra `account_0077` que é criptografia inútil pra negócio.

---

## O que falta (próximas 3 iterações) 🎯

### Iteração 1 (alta urgência, baixa complexidade): **Account humanizada**
Substituir `account_0077` por algo como `Media · Australia · Acme
Corp` (industry, country, parent_company da tabela accounts). Hoje
tenho essas 3 colunas no CSV e o app nem usa. Um join extra resolve.
**Isso transforma o app de "dashboard abstrato" em "ferramenta
real de vendedor".**

### Iteração 2 (alta urgência, média complexidade): **Ação no deal**
Botão "Assumir" e "Descartar" em cada card → adiciona uma coluna
`status` no DataFrame local (session_state) → deal assumido sai
do top-N mas permanece na tabela com badge "Em atendimento".
**Sem isso o app é só visualização, não é workflow.**

### Iteração 3 (média urgência, baixa complexidade): **Benchmarks histn**
Adicionar no KPI header um comparativo: "Score médio hoje: 32,8
(médio histórico: 30,1 — +8% vs mês passado)". Ou um mini-chart
de score médio over time. **Resolve o problema de "32,8 é bom ou
ruim?"** Só comparando com passado dá pra julgar.

---

## Veredito AGENT-D: **ÚTIL, com 3 fixes críticos antes de rollout**

| Pilar | Nota | Comentário |
|-------|------|-----------|
| Funciona de verdade? | A | Abre rápido, sem crash, dados reais |
| Scoring explicável? | A | Breakdown em PT-BR é diferencial |
| Vendedor entende? | B+ | Card é claro, mas account ID precisa virar nome |
| Ajuda a decidir? | B | Top-10 ajuda, mas falta ação (assumir/descartar) |
| Filtro por reporte? | A | Manager + office + stage + agente ✅ |
| UX defensável p/ board? | C | PII exposta, sem benchmark, sem modo apresentação |

**Recomendação final:** Ship the top-10 + filtros hoje para os
managers. **Antes de rollout full** pros 35 vendedores, faça:

1. Account humanizada (iteração 1) — 1h de trabalho
2. Ação no deal (iteração 2) — 2h de trabalho
3. PII toggle (modo apresentação) — 30min de trabalho

Depois desses 3, **torno a ferramenta recomendada pra todo o
comercial**. Sem eles, fica como piloto para managers sênior.

---

## Análise do AGENT-D vs SPEC do challenge — onde bateria?

O challenge diz (Critérios de qualidade):
1. ✅ A solução funciona de verdade? — **sim**
2. ✅ O scoring faz sentido? — **sim, com ressalva sobre over-reward
   de GTX Enterprise (C1)**
3. ⚠️ O vendedor não-técnico consegue entender? — **sim para o
   card, mas account_0077 derruba essa claúsula (C7)**
4. ✅ A interface ajuda a decidir? — **sim para top-N, mas falta
   ação (C5)**
5. ✅ O código é limpo? — **sim, validado em Prompt 06**

**Net: challenge superado em 4/5 critérios.** C7 e C5 são os
gaps entre "demo boa" e "ferramenta usada".

---

## Insights do AGENT-D que mudam SPEC futura

Estas coisas não eram óbvias no Prompt 03 (SPEC de scoring) mas
ficam evidentes ao usar:

1. **Calibração de banda** — todos scores 65-71 no top-10 são
   "Morno"; range nominal 50-80 chega a ser muito largo pra
   discriminar. Talvez faixa "Quente" baixar para ≥70.
2. **Account_size** pode merecer peso MAIOR que 20% quando o
   vendedor está decidindo — faria sentido 25% e reduzir algo
3. **Stale-state warning** — deals com engage_date > 90 dias
   deveriam aparecer com badge vermelho ATIVO, não só score
   baixo. Hoje são invisíveis na tabela.
4. **Pipeline concentration** — todos top-10 são GTX Enterprise;
   um score "concentration penalty" poderia baixar score de deals
   similares se o vendedor já tem N deals iguais no pipe
5. **Quick action: "Bring to me"** — shortcut pra mover o deal
   para uma lista "priorizados hoje"

---

_Estado do harness após Prompt 07:_
- Agent: REVOPS-EXPERT ✅ (persona Head de RevOps aplicada)
- Output: 3 uses positivos + 7 confusões + 3 iterações priorizadas
- Insight estratégico: 4/5 critérios do challenge superados hoje,
  gaps principais são C5 (ação) e C7 (account humanizada)
- Próximo prompt: **Prompt 08 — Consolidar memória** (SKILL-05)