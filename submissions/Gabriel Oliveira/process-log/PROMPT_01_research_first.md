# Prompt 01 — Research-First (AGENT-A + SKILL-01)

> **Prompt emitido:**

```
[AGENT: ARCHITECT] [SKILL: RESEARCH-FIRST]

Estou resolvendo o Challenge 003 Lead Scorer do G4 AI Master Challenge.
Brief: construir ferramenta que vendedores usem pra priorizar ~8.800 deals.
Tenho 4 CSVs: accounts.csv (~85), products.csv (7), sales_teams.csv (35),
sales_pipeline.csv (~8800). Ligados por account/product/sales_agent/opportunity_id.

Antes de codar, me ajude a:
1. Listar 5 hipóteses de negócio sobre o que faz um deal fechar
2. Quais features óbvias vs. quais um AI Master traria (não óbvias)
3. Que armadilhas devo checar no dataset (nulos, formato de data, PII)
4. Quais perguntas o Head de RevOps faria ao ver a ferramenta

Em tópicos, sem código. Quero o plano de pesquisa.
```

---

## Schema confirmado contra CSVs reais

Antes de qualquer hipótese, validei (instinto "GLM-5.2 alucina colunas") os nomes
reais das colunas em cada arquivo:

| Arquivo | Colunas |
|---------|---------|
| `accounts.csv` | `account, industry, country, acquisition_channel, revenue, employees, parent_company, has_trial` |
| `products.csv` | `product, series, sales_price` |
| `sales_teams.csv` | `sales_agent, manager, regional_office` |
| `sales_pipeline.csv` | `opportunity_id, sales_agent, product, account, deal_stage, engage_date, close_date, close_value` |

Stages observados: `Prospecting`, `Engaging`, `Won`, `Lost`.
Datas em `MM/DD/YYYY` (nÃO ISO — confirmado na primeira linha do pipeline).

---

## 1. Cinco hipóteses de negócio sobre o que faz um deal fechar

Cada hipótese é **falsificável** com os dados disponíveis. Sem isso seria achismo.

**H1 — Stage advancement é o maior predutor isolado.**
Deals em `Engaging` convertem mais que `Prospecting` porque já passaram
da fase de descoberta. Teste: win rate condicional por stage.

**H2 — Deals velhos esfriam, mas não linearmente.**
Existe uma janela ótima (ex.: 15–60 dias) onde a conversão é máxima.
Antes disso o deal não amadureceu; depois o cliente esfriou ou foi
perdido para concorrente. Teste: curva de win rate por idade decil.

**H3 — Quem vende importa tanto quanto o que se vende.**
A variância de win rate entre `sales_agent` é significativa mesmo
controlando por produto/conta. Teste: win rate por agente vs. média,
controlando por mix de produto.

**H4 — Tamanho da conta eleva ticket mas comprime conversão.**
Contas grandes (`revenue` alto, `employees` alto) geram deals maiores
mas também ciclos mais longos e mais competitivos. Teste: correlação
`tamanho da conta × dias no pipeline × close_value`.

**H5 — Aquisição por canal influencia qualidade.**
Contas trazidas por `Referral` / `Partner` podem converter melhor que
`Outbound` puro (efeito confiança prévia). Teste: win rate por
`acquisition_channel` controlado por indústria.

---

## 2. Features óbvias vs. features que só um AI Master traria

### Óbvias (qualquer baseline de IA listaria)
- `deal_stage` atual
- `close_value`
- dias desde `engage_date`
- `sales_price` do produto
- `revenue` / `employees` da conta

### Não-óbvias (trunfo do AI Master — contexto de negócio)
- **Win rate histórico do `sales_agent`** → feature de "quem está vendendo"  
  O baseline de IA tende a ignorar porque é feature derivada, não nativa.
- **Velocidade relativa ao stage** → não é "quantos dias", é  
  "quantos dias vs. mediana do mesmo stage + mesmo produto". Captura  
  deals que estão *atrasados relativamente*, não absolutamente.
- **Taxa de sucesso do `product` × `industry`** → produto certo para  
  tamanho certo. SaaS de ticket alto em contas pequudas = fricção.
- **`has_trial` como sinal de maturidade** → trial = baixa barreira  
  inicial, mas também = cliente sem skin in the game. Efeito ambíguo.
- **Gap entre `close_value` esperado e `sales_price`** → deal descontado  
  vs. deal a preço cheio mostra poder de negociação / desespero.
- **Concentração de pipeline do agente** → se um vendedor tem 50 deals  
  abertos vs. 5, atenção diluída afeta conversão (feature de carga).
- **Regional office como proxy de mercado** → escritórios diferentes  
  podem atender geografias com poder de compra diferente.

---

## 3. Armadilhas a checar no dataset

| # | Armadilha | Risco | Checagem a fazer na EDA |
|---|-----------|-------|---------------------------|
| A1 | **Formato de data `MM/DD/YYYY` (não ISO)** | NaT silencioso ao usar `pd.to_datetime` sem formato explícito | Forçar `format='%m/%d/%Y'`, contar NaTantes/depois |
| A2 | **`engage_date` nulo em `Prospecting`** | NaN propagando para features de velocity | Contar nulos por stage; decided política (0 + label explicativa) |
| A3 | **`close_date` vazio em deals não fechados** | Não é "dado faltante", é "ainda não aconteceu" | Distinguir `""` vs `NaN` real; não imputar |
| A4 | **`close_value = 0`** | Pode ser `Lost` (OK) ou erro de preenchimento em Won | Cruzar `close_value==0` × `deal_stage`; investigar anomalies |
| A5 | **PII: `sales_agent`, `account`** | Nomes reais vazando em logs / prints | Evitar printar PII; usar IDs em logs internos |
| A6 | **Vieses de survivorship** | Deal Won com valor alto é mais visível; Lost com valor baixo é "esquecido" | Distribuição completa incluindo zeros |
| A7 | **Desequilíbrio de stage** | Se Won >> Lost, win rate agregado engana | Sempre estratificar por stage |
| A8 | **`has_trial` quase sempre True/False?** | Variável sem variância não discrimina | Contar valores únicos |
| A9 | **Cardinalidade baixa em `products` (7 linhas)** | Produto com poucas amostras → ruído em win rate por produto | Intervalos de confiança, não ponto |
| A10 | **`regional_office` e `manager` correlacionados** | Colinearidade — um manager por escritório | Crosstab antes de usar ambos como features |

---

## 4. Perguntas que o Head de RevOps faria ao ver a ferramenta

Persona: segunda-feira 9h, café na mão, pipeline de 8800 deals,
vascobrainstorming "onde coloco meus 35 vendedores esta semana".

1. **"Dado este pipeline, quais 5 deals meus vendedores deveriam tocar
   hoje antes do almoço?"** → top-N priorizado é o UI core, não tabela
   geral.

2. **"Por que ESTE deal marcou 87 e não 60?"** → se a tools não explica
   cada score, ela é inútil. Explainability é keystone.

3. **"Qual dos meus vendedores está com pipeline mais eskentado?"** →
   agregação por `sales_agent` / `manager`. Filtro não é luxo, é
   requisito.

4. **"Tenho deals quentes que estão esfriando?"** → feature de
   velocity *relativa*. MostrarÄ "deals em risco de esfriar" como
   alerta, não só score.

5. **"Quanto dinheiro tenho em jogo nos próximos 30 dias?"** → soma de
   `close_value` esperado (probabilidade × valor). KPI de revenue.

6. **"Este deal vale quanto?"** → `close_value` para Won é claro;
   para deals abertos preciso estimar. UI deve distinguir "valor
   esperado" vs "valor fechado".

7. **"Estou batendo meta? Como está concentrado o pipeline?"** →
   distribuição de scores e Pareto (top 20% deals = x% do revenue).

8. **"Se eu perder o deal X, quanto perco?"** → feature de
   dependência / concentração por conta.

9. **"Quem é o próximo cliente para o vendedor Y focar depois do
   atual?"** → sugestão de próximo alvo, não só ranking estático.

10. **"Posso confiar neste score? Onde ele erra?"** → mostrar
    limitações (Regra do harness: transparência > inflar).

---

## Plano de pesquisa derivado (o que vou executar na EDA)

Com base nas hipóteses e armadilhas, a EDA precisa responder, com
números, a estas 8 perguntas antes de uma linha de scoring ser escrita:

1. Distribuição de `deal_stage` (contagem absoluta + %)
2. Win rate (Won / Won+Lost) por `sales_agent` → suporta H3
3. Win rate por `product` → suporta produto como feature
4. Win rate por `acquisition_channel` → suporta H5
5. Distribuição de `close_value` por stage → detecta A4
6. Distribuição de dias `engage → close` por stage → suporta H2
7. Nulos em `engage_date` estratificados por stage → armadilha A2
8. Crosstab `manager × regional_office` → armadilha A10

Os achados destes 8 pontos irão calibrar os pesos do scoring (Prompt 03).
**Sem EDA, sem pesos.** É a regra do Spec-Driven.

---

_Estado do harness após Prompt 01:_
- Agent: ARCHITECT ✅
- Skill: RESEARCH-FIRST ✅
- Julgamento humano aplicado: schema validado antes de hipóteses ✅
- Próximo prompt: **Prompt 02 — EDA contra schema real** (AGENT-B + SKILL-04)