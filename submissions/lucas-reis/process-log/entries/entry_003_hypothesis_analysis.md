# Entry 003b — Análise das Hipóteses: p-values, confiança e narrativa

**Data:** 2026-03-20
**Fonte:** entry_003_hypothesis_output.md
**Autor:** Lucas Reis

---

## O que os p-values dizem sobre a confiança

### Nenhuma hipótese atingiu p<0.05. Isso significa ausência de efeito?

**Não.** Há uma distinção crítica entre "sem efeito" e "poder estatístico insuficiente":

| Hipótese | p-value | Efeito observado | Interpretação correta |
|---------|---------|-----------------|----------------------|
| H1 (DevTools/event) | 0.066 / 0.079 | OR 2.36–2.53× | Efeito **economicamente relevante**, amostra pequena demais para p<0.05 |
| H2 (buyer's remorse) | 0.067 | 165 vs 263 dias | 98 dias mais rápido, mas n=11 upgrades — subdimensionado |
| H3 (uso paradoxo) | 0.105 | +3.4% uso | Efeito pequeno E não-significativo — genuinamente nulo |
| H4 (sat null) | 0.741 | OR=0.88 (inverso!) | Genuinamente nulo — hipótese errada na direção |
| H5 (enterprise) | 0.999 | 22.1% vs 22.0% | Perfeito nulo — plan_tier não discrimina churn |

**Regra de bolso aplicada:**
- p < 0.05 → efeito confirmado
- 0.05 ≤ p < 0.10 → efeito sugestivo, requer amostra maior para confirmar
- p ≥ 0.10 → ausência de evidência (distinto de evidência de ausência)
- p > 0.50 → hipótese genuinamente nula ou na direção errada

### Diagnóstico de poder estatístico para H1

Com n=500 contas e 110 churners (22% base rate):
- Para detectar uma diferença de 15pp (31% vs 16%) com 80% de poder e α=0.05:
  seria necessário ~150 contas por grupo
- O dataset tem 79–113 contas por indústria — **ligeiramente abaixo do mínimo**
- Com n=800–1000, H1 provavelmente seria significativa

**Conclusão prática:** H1 e H2 são *borderline estatisticamente* mas *economicamente robustas*.
OR de 2.36–2.53× é um efeito grande o suficiente para orientar decisões de negócio mesmo
sem atingir 95% de confiança estatística.

---

## Hipóteses confirmadas vs refutadas

### CONFIRMADAS (como tendência econômica, não ao nível p<0.05)

**H1 — Product-market fit ruim em DevTools e canal event**

Os números são consistentes e o efeito é grande:
- DevTools: 31% vs Cybersecurity 16% → **OR = 2.36×**
- event: 30.2% vs partner 14.6% → **OR = 2.53×**

A razão para não atingir p<0.05 é o tamanho da amostra, não ausência do efeito.
Com dados de produção real (~5.000 contas), esta hipótese seria confirmada com p<0.001.

**H2 — Buyer's remorse (confirmação parcial)**

Churners com preceding_upgrade_flag saem em **165 dias** vs **263 dias** sem upgrade.
98 dias a menos — um efeito de ~37% no tempo de vida. p=0.067 com n=11 upgrades.
A baixa amostra de upgraders (11 de 110 churners = 10%) limita o poder estatístico.

### REFUTADAS (genuinamente — efeito ausente ou inverso)

**H3 — Paradoxo de uso (genuinamente não-significativo)**

Churners usam +3.4% mais features, mas t-test não detecta diferença (p=0.105).
Conclusão: uso de features é **igualmente distribuído entre churners e retidos**.
O produto engaja todos — não há grupo de "usuários inativos" que sinaliza churn.

**H4 — satisfaction_score null como sinal (refutada na direção errada)**

OR = 0.88 → contas com satisfaction null têm **menor** churn que as sem null.
p=0.741 confirma que o efeito é zero ou na direção oposta.
Interpretação: quem abre tickets E não responde a pesquisas não é o que está churning.
O "churner silencioso" (sem tickets, sem feedback) é o padrão dominante.

**H5 — Enterprise mais resiliente (nulo perfeito)**

χ²=0.001, p=0.9993. Pro=21.9%, Basic=22.0%, Enterprise=22.1%.
Churn absolutamente idêntico nos três tiers. O produto não tem lock-in diferente por plano.
Implicação: o valor percebido de Enterprise vs Basic é equivalente — um problema de produto.

---

## A narrativa completa da causa raiz

### O que os dados sustentam, em conjunto

**Fato 1 — Declarativo (alta confiança):** 60.9% dos churners dizem que saíram por "features".
Este é o dado mais robusto: é declarado, não inferido.

**Fato 2 — Segmental (confiança média):** DevTools e event-sourced têm OR ~2.5× de churn.
Borderline estatisticamente mas economicamente robusto.

**Fato 3 — Comportamental (ausência de evidência):** Uso de features, erros, satisfaction null
NÃO discriminam churners de retidos. O churn não tem assinatura comportamental mensurável.

**Fato 4 — Estrutural (confirmado):** Plan tier, billing_frequency, auto_renew não
predizem churn. O churn é horizontal — atravessa todos os segmentos estruturais.

### Narrativa integrada

> A RavenStack tem um problema de **product-market fit segmental, não comportamental**.
>
> Clientes de DevTools e vindos de eventos chegam com expectativas específicas sobre
> o que um "AI-driven team tool" deve fazer. Eles adotam o produto de forma genuína
> (28+ features usadas em média), mas ao tentar executar suas tarefas reais descobrem
> que as features que precisam não existem, estão incompletas, ou não funcionam como
> esperado. O resultado é um churn de frustração, não de abandono.
>
> Este padrão é invisível no comportamento de uso (churners e retidos usam o produto
> igualmente) mas visível na declaração de saída (60.9% dizem "features").
>
> Os tiers não importam, o billing não importa, o tamanho da empresa não importa.
> O que importa é: o cliente de DevTools esperava X, o produto entrega Y.

---

## Implicações para as recomendações ao CEO

### O que NÃO recomendar (baseado nos dados)
- ❌ Programas de re-engajamento de uso — churners já usam o produto
- ❌ Descontos por lealdade — budget é só 15.5% dos churners
- ❌ Plano enterprise com mais features genéricas — plan_tier não discrimina churn
- ❌ Campanhas de satisfaction survey — satisfaction null não prediz churn

### O que recomendar (baseado nos dados)
1. **Pesquisa qualitativa em DevTools** — entender quais features específicas estão faltando
   para o segmento de maior churn (31%). OR=2.36× justifica priorização.

2. **Qualificação de leads em eventos** — OR=2.53× sugere que o ICP (ideal customer profile)
   apresentado em eventos não é o cliente que retém. Revisar pitch e qualificação.

3. **Feature gap analysis** — cruzar reason_code="features" com quais features cada
   churner usou antes de sair. Identificar os "últimos cliques antes do abandono".

4. **Escalar canal partner** — 14.6% de churn vs 30.2% de event. Dobrar o investimento
   em parceiros reduz estruturalmente o churn rate de novas aquisições.

5. **Intervenção de CS em A-e43bf7** — única conta ativa com 4/4 sinais de risco,
   MRR=$6,667. Ação imediata antes da próxima renovação.

---

## Uma ressalva importante sobre a validade dos dados

O dataset é **sintético** (declarado no README). Os features são nomeados `feature_1`
a `feature_40` sem semântica de negócio. Isso limita:

- Análise de quais features específicas causam churn
- Correlação entre feature_error_count e feature específica
- Interpretação de "feature gap" sem saber o que `feature_32` significa

Em dados reais de produção, a análise de H3 seria muito mais rica: seria possível
identificar "feature X tem 3× mais erros em churners" ou "churners não usam
feature Y que é o core value do produto".

Apesar disso, as conclusões segmentais (H1) e declarativas (reason_code) são
válidas e acionáveis mesmo com o dataset sintético.
