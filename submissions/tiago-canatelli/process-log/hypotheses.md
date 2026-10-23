# Diário de hipóteses

Formato definido na skill `churn-data-scientist`. Números reproduzíveis com `uv run --group analysis python analysis/diagnostico.py`. As tabelas completas estão em `analysis/results/diagnostico.md` e os números em `analysis/results/numbers.json`. Testado em 2026-10-23.

Decisões de base: churn é o evento em `churn_events`. O **MRR vigente é o da assinatura ativa mais recente**: o preço por licença é fixo (US$ 19 / 49 / 199) e, se somássemos todas as assinaturas abertas, a mediana seria de 225 licenças por conta, contra 15 no cadastro. Isso é implausível.

---

### H0 — O churn subiu?
- **Por que testar:** é a afirmação do CEO; o denominador muda a resposta.
- **Tabelas cruzadas:** churn_events, accounts, subscriptions.
- **Método:** eventos por trimestre ÷ contas cadastradas e ÷ assinaturas ativas.
- **Resultado:** os eventos foram de 37 (2023Q4) para 251 (2024Q4). Por conta, a taxa sobe; por assinatura ativa, fica estável em ~5% ao trimestre, porque as contas acumulam assinaturas. 55% dos churns de 2024Q4 são de contas que já tinham churnado antes.
- **Causalidade:** não se aplica (é descrição).
- **Veredito:** **confirmada** (em logos).
- **Implicação:** a pergunta certa é *quem* está saindo (H8).

### H1 — A satisfação está mascarada?
- **Por que testar:** o CS diz que a "satisfação está ok".
- **Tabelas cruzadas:** support_tickets × churn_events × accounts.
- **Método:** comparação por conta entre quem churnou e quem nunca churnou (Mann-Whitney), e janela de 90 dias antes do churn contra contas de controle na mesma data.
- **Resultado:** CSAT de 3,96 nos churners contra 3,97 nos retidos. Tickets, % escalado, tempo de primeira resposta e taxa de resposta são iguais, com todos os p > 0,2. A nota **só vai de 3 a 5** e 41% dos tickets não têm nota. **58% dos churns não abriram ticket nenhum nos 90 dias anteriores.**
- **Causalidade:** não há associação, então não há causa a testar.
- **Veredito:** **confirmada, com outra forma.** A satisfação não está "mascarada": o instrumento é **cego**, porque não separa quem vai sair de quem fica.
- **Implicação:** o CS mede a coisa errada. É preciso trocar o instrumento: escala completa, pergunta de intenção de renovação e sinal antes do ticket.

### H2 — O uso cresceu para todos?
- **Por que testar:** o Produto diz que "o uso cresceu".
- **Tabelas cruzadas:** feature_usage × subscriptions × accounts.
- **Método:** uso por trimestre, total e por conta, por plano e por indústria.
- **Resultado:** o uso é **plano**, em ~31 mil eventos por trimestre e ~63 por conta, com variação de 1,6%, em todos os segmentos. 53% do uso tem data **anterior ao cadastro** da conta, e 78% está fora do período da assinatura.
- **Causalidade:** não se aplica.
- **Veredito:** **refutada.** O uso não cresceu. E, do jeito que está registrado, o dado não sustenta nenhuma afirmação sobre tendência.
- **Implicação:** é preciso corrigir a instrumentação de produto antes de usá-la para decidir.

### H3 — Erros ou features beta antecedem o churn?
- **Tabelas cruzadas:** feature_usage × churn_events.
- **Método:** quartis da taxa de erro por conta contra churns por conta; uso, erro e beta nos 90 dias antes do churn contra controles.
- **Resultado:** Spearman ρ = 0,05 (p = 0,23), sem dose-resposta. Uso nos 90 dias anteriores contra controle: p = 0,21. A parcela de beta é igual nos dois grupos.
- **Veredito:** **refutada.**

### H4 — O motivo declarado explica o churn?
- **Tabelas cruzadas:** churn_events × subscriptions.
- **Resultado:** os 6 motivos ficam entre 91 e 114 eventos cada, não mudam ao longo do tempo (χ² p = 0,62) e têm MRR, refund e downgrade parecidos. `feedback_text` tem só 4 textos distintos.
- **Veredito:** **confirmada.** O motivo declarado não explica nada.
- **Implicação:** é preciso trocar o formulário por uma entrevista de saída estruturada, nas contas que pesam em MRR.

### H5 — Nem todo churn pesa igual
- **Tabelas cruzadas:** churn_events × subscriptions.
- **Resultado:** US$ 1,22 mi de MRR somado nos eventos. **Enterprise é 36% dos eventos e 77% do MRR perdido.** Os 10% maiores eventos concentram 43% do MRR perdido. 53 eventos não têm assinatura anterior à data do churn.
- **Veredito:** **confirmada.**
- **Implicação:** priorizar Enterprise e as contas de MRR alto.

### H6 — Algum segmento de cadastro churna mais?
- **Tabelas cruzadas:** accounts × churn_events.
- **Método:** churns por 100 contas-mês, com χ² contra a exposição e correção de Bonferroni para os 6 testes.
- **Resultado:** canal, indústria, país, plano inicial, trial e licenças: **nenhum** sobrevive à correção. `organic` deu p = 0,025, que é o tipo de falso positivo que some com múltiplos testes.
- **Veredito:** **refutada.**
- **Implicação:** não recomendar ação por canal nem por indústria.

### H7 — Mudança de plano antecede o churn?
- **Resultado:** churns com downgrade nos 90 dias anteriores: 8,8%, contra 4,4% na base de assinaturas. Com upgrade: 20,5% contra 10,6%. Qualquer mudança de plano dobra.
- **Causalidade:** as unidades são diferentes (uma janela de 90 dias contra a flag da assinatura).
- **Veredito:** **inconclusiva** (indício fraco).

### H8 — Quem está saindo: contas novas *(hipótese nova, surgiu dos dados)*
- **Por que testar:** H0 mostrou que a taxa por conta sobe enquanto nenhum segmento de cadastro explica a alta.
- **Tabelas cruzadas:** accounts × churn_events × subscriptions (painel conta-mês).
- **Método:**
  - taxa por trimestre do calendário × tempo de casa;
  - Poisson com calendário, tempo de casa e churn anterior;
  - logit de churn em 6 meses por coorte, controlando canal, plano, indústria, trial e licenças.
- **Resultado:**
  - Quem tem 12 meses ou mais churna a **0,28×** a taxa dos primeiros 3 meses (p < 0,001), com dose-resposta monotônica: 0,71 → 0,48 → 0,28.
  - Em 2024Q4, contas com 0–3 meses churnaram a **46,5 por 100 contas-mês**, contra 8,3 das que têm 12 meses ou mais.
  - Churn em 6 meses: 27% na coorte 2023H1 contra **62% na coorte 2024H1**. Com controles, a coorte 2024 tem **3,3×** a chance (IC 2,0–5,3, p = 9e-07), e nenhum controle é significativo: o mix de cadastro não mudou.
  - Contas que já churnaram não têm risco maior (RR 0,88, p = 0,17).
  - Churn no 1º trimestre de vida somado a churn repetido dá **73% dos eventos e 72% do MRR perdido**.
- **Causalidade:**
  - temporal ✅ (o tempo de casa vem antes);
  - controle por segmento ✅;
  - dose-resposta ✅;
  - alternativa ⚠️: existe também um efeito de calendário (todos churnam mais no fim de 2024), mas a coorte antiga sobe ~1,5× enquanto as contas de 0–3 meses sobem ~8×.

  O **mecanismo** (onboarding, ativação, qualificação de venda) **não está nos dados**.
- **Veredito:** **confirmada** como padrão; o mecanismo é uma hipótese a testar com experimento.
- **Implicação:** o problema está nos primeiros 90 dias das contas novas de 2024 e no ciclo de sai e volta. É aí que a ação deve concentrar.

### H9 — Quem churna volta? *(hipótese nova, surgiu na construção do gold)*
- **Por que testar:** para definir "conta ativa" e o MRR, precisei saber o que acontece depois de um churn.
- **Tabelas cruzadas:** churn_events × subscriptions.
- **Resultado:** 87% dos eventos de churn têm uma nova assinatura depois, com mediana de **16 dias** (p25 5, p75 44). Só 68 das 500 contas estão "fora" em 31/12/2024. Mas a flag de origem `is_reactivation` marca só 10%, e só 6 dos 600 churns coincidem com o fim de uma assinatura.
- **Causalidade:** não se aplica. É uma questão de **validade do dado**.
- **Veredito:** **inconclusiva.** Há duas leituras: (a) o churn é em boa parte uma interrupção curta (problema de cobrança ou renovação, não de perda real); ou (b) as assinaturas foram geradas sem ligação com os churns e a "volta" é um artefato.
- **Implicação:** H8 não depende disso, porque conta eventos e exposição desde o cadastro. Os KPIs de receita (GRR/NRR) e o estado "ativa" **dependem**, e saem com ressalva. A recomendação é validar com o log de cobrança: se (a) for verdade, parte do "churn" se resolve com dunning e renovação, não com CS.

---

## Síntese (causa raiz, no nível de evidência que os dados permitem)

1. **O churn subiu porque as contas novas falham cedo, e cada vez mais.** O mix de quem entra (canal, plano, indústria) não mudou: mudou o que acontece nos primeiros 90 dias.
2. **Os instrumentos que o CS e o Produto olham não enxergam isso.** O CSAT só vai de 3 a 5 e é igual para quem sai e quem fica, e 58% saem sem abrir ticket. O log de uso é plano e não está ancorado no tempo. Por isso "satisfação ok" e "uso cresceu" convivem com o churn em alta.
3. **O dinheiro está em Enterprise** (77% do MRR perdido) e no **ciclo de sai e volta** (41% dos eventos, 46% do MRR perdido).
4. **Ressalva sobre a receita:** 87% dos churns são seguidos de uma nova assinatura em cerca de 16 dias (H9). Se isso for real, parte do "churn" é interrupção de cobrança, não perda. Os KPIs de receita são aproximados até validarmos com o log de cobrança.
5. **O que não é causa, com evidência:** suporte, erros, uso, motivo declarado, canal, indústria, país, plano inicial, trial e licenças.
EOF
