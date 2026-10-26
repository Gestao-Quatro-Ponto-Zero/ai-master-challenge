# 🥊 Registro das 3 Rodadas de Auditoria Adversarial — Challenge 003: Lead Scorer

Este arquivo registra a evolução crítica do projeto através de três rodadas independentes de revisão, incluindo os pontos em que hipóteses geradas por IA (inclusive em rodadas anteriores de auditoria) precisaram ser corrigidas ou descartadas diante dos dados.

---

## Round 1: Red Team de Premissas Comerciais (DeepSeek API)

**Foco:** Questionar modelagem ingênua de classificação sobre atributos demográficos estáticos e dispersão de preços.

### O que se sustentou nos dados:
1. **Baixo poder discriminativo de `sector` e `regional_office` entre negócios fechados:** taxas de vitória condicionais (`Won / (Won + Lost)`) variam em faixa estreita (`~61%` a `~65%`), não justificando modelos caixa-preta sobre demografia.
2. **Dispersão de 486x nos preços de catálogo (`US$ 55` a `US$ 26.768`):** ordenar puramente por preço nominal concentra o topo em `GTK 500` e `GTX Plus Pro` mesmo quando estagnados.
3. **Separação obrigatória de `Prospecting` (`500` registros sem `engage_date`):** imputar idade artificial contaminaria o funil ativo.

### Onde a hipótese do Round 1 extrapolou os dados (corrigido depois):
- O Round 1 atribuiu a ausência de vitórias acima de `138` dias exclusivamente à censura à direita pelo corte em `31/12/2017`. A verificação empírica posterior mostrou que oportunidades abertas entre outubro/2016 e março/2017 tiveram **300 a 437 dias de observação** e ainda assim apresentaram **zero** fechamentos acima de `138` dias — porque nos escritórios `East` e `West` negócios abandonados permanecem indefinidamente em `Engaging` em vez de receberem baixa como `Lost`.

---

## Round 2: Auditoria de Implementação e Vazamento Temporal (Codex)

**Foco:** Revisão de código linha a linha em `data_loader.py`, `survival_and_scoring.py`, `backtest.py` e `app.py`.

### Problemas reais detectados e corrigidos:
1. **Vazamento futuro em `cycle_days` no backtest:** negócios abertos na data de corte que fecharam depois estavam tendo sua idade calculada com `close_date` futura em vez de `(as_of_date - engage_date)`.
2. **Desalinhamento posicional de baselines:** `score_engaging_deals` reordenava o DataFrame antes da extração de baselines, comparando fatias incompatíveis.
3. **Falha em histórico vazio (`as_of_date` anterior ao primeiro fechamento):** ausência de colunas esperadas quando `len(won) == 0`.

### Limitação do Round 2:
- Após corrigir o vazamento e o alinhamento, o backtest na subpopulação resolvida (`N = 970` em `30/06/2017`) caiu para `AUC = 0,5021` (contra `0,5070` da média histórica do vendedor). O Round 2 garantiu a correção técnica do código, mas não questionou se o motor super-parametrizado deveria ser simplificado.

---

## Round 3: Auditoria Metodológica, Epistemológica e de Consistência (Astra)

**Foco:** Confrontar o plano inicial do Argon com os resultados empíricos, a validade dos testes, a separação entre heurística e estatística e a precisão da documentação.

### Sete apontamentos estruturais e como foram resolvidos na versão final:

1. **Ancoragem no plano inicial & excesso de parâmetros sem ganho demonstrado:**
   - *Apontamento:* O motor acumulava penalidade fixa de `-50%` por conta ausente, bônus enterprise, estimativa manual de dias restantes e combinação logarítmica `0.50/0.30/0.20` sem superar baseline na subpopulação resolvida.
   - *Resolução:* Removemos todos os multiplicadores manuais e a fórmula de dias restantes. Reduzimos o motor a `EV_90d = P_90d(idade, vendedor) × Ticket_Mediano` e adicionamos ablação explícita (`P_90d` apenas por idade vs. idade + vendedor).

2. **Separação entre qualidade cadastral (`account`) e probabilidade de vitória:**
   - *Apontamento:* Falta de conta justifica tarefa de enriquecimento, não reduzir probabilidade pela metade sem evidência.
   - *Resolução:* Verificamos nos dados que `100%` dos deals fechados (`Won` e `Lost`) têm `account` preenchido (`0` ausentes em `6.711` fechados vs. `1.088` ausentes em `Engaging`), comprovando artefato de fechamento. Retiramos `account` de `P_90d` (eliminando risco de *snapshot leakage*) e isolamos `crm_hygiene_status` como governança operacional.

3. **Terminologia honesta (heurística vs. estatística):**
   - *Apontamento:* Tabela descritiva era rotulada como `"Kaplan-Meier Proxy"` e regras manuais eram chamadas de `"probabilidades calibradas"`.
   - *Resolução:* Renomeamos o gráfico descritivo para `"Proporção Histórica por Duração Observada"`, classificamos explicitamente a aba `Prospecting` como regra determinística não-probabilística e restringimos o termo probabilidade empírica a `P_90d`, acompanhado de curva de calibração em quintis *out-of-time*.

4. **População do backtest coerente com a decisão do usuário:**
   - *Apontamento:* Remover os `716` casos não-fechados avaliava uma subpopulação filtrada pelo desfecho futuro (`N = 970`), não a fila real enfrentada pelo vendedor no corte.
   - *Resolução:* Passamos a publicar **os dois regimes lado a lado**: (1) a fila aberta completa em três cortes independentes (`31/07`, `31/08`, `30/09/2017`) com horizonte fixo de +90 dias sem censura (global e intra-vendedor, com desempate neutro por `opportunity_id`), onde `EV_90d` captura `60,1%–63,7%` da receita no Top 20%; e (2) o diagnóstico condicional nos `970` resolvidos (`AUC ~0,49–0,51`), explicitando o limite dos dados estáticos do CRM.

5. **Testes que realmente detectam regressões:**
   - *Apontamento:* `test_temporal_split_zero_leakage` verificava apenas o próprio filtro de datas e `test_simulator_and_scorer_parity` testava apenas valores `> 0`.
   - *Resolução:* Substituídos por testes de mutação (invertendo `Won <-> Lost` e multiplicando `close_value * 100` pós-corte exigindo predições idênticas em `1e-12`), invariância a permutação de linhas, paridade exata entre lote e `score_single_deal_simulation` em 20 negócios reais e smoke test completo das 4 abas com `Streamlit AppTest`.

6. **Precisão na autoria das decisões no `PROCESS_LOG.md`:**
   - *Apontamento:* O botão de discordância já constava no plano inicial do Argon e não deveria figurar como adição exclusiva humana sem IA.
   - *Resolução:* Reescrevemos o `PROCESS_LOG.md` no formato `Sugestão → Origem → Evidência → Decisão Humana → Alteração → Resultado`, registrando com exatidão a origem de cada proposta.

7. **Reconciliação final entre UI, código e documentação:**
   - *Apontamento:* `app.py` ainda mencionava `4.032 negócios`, o override não alterava a prioridade e o `README` continha afirmações excessivas (`"comprova"`, `"qualquer AUC > 0,80 seria vazamento"`).
   - *Resolução:* Texto da UI alinhado aos cortes reais, override conectado funcionalmente à reordenação da fila em tempo real (`promote` / `pause` / `archive` / `none`) e afirmações absolutas removidas do `README.md`.
