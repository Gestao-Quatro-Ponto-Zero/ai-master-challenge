# 🥊 Auditoria Adversarial (Red Team Review) — Challenge 003: Lead Scorer

**Data:** 24 de Outubro de 2026  
**Auditor:** DeepSeek Red Team Persona (CRO + Principal AI Architect)  
**Alvo:** Hipóteses Iniciais e Modelagem do Pipeline de Vendas CRM  

---

## 1. O Teste de Estresse das Premissas Iniciais

Durante a fase de exploração com IA, as primeiras respostas de modelos de fundação (Claude 3.5 Sonnet / GPT-4o) sugeriram:
1. Treinar modelos de classificação padrão (Random Forest ou Logistic Regression) em colunas como `sector`, `regional_office` e `sales_agent`.
2. Adotar um corte rígido determinístico: *"como nenhum deal fechado como Won durou mais de 138 dias, zerar o score para qualquer oportunidade acima de 138 dias"*.
3. Calcular Expected Value multiplicando diretamente $EV = P \times \text{Valor Nominal}$.

Submetemos essas recomendações a um **Red Team Review implacável via API do DeepSeek**. Abaixo estão os apontamentos críticos identificados:

### Crítica 1: A Falácia dos 138 Dias e o Viés de Censura à Direita (Right-Censoring)
> *"O dataset termina em 31/12/2017. Deals abertos em nov/dez/2017 simplesmente não tiveram tempo de fechar. O 'máximo de 138 dias' é um artefato da janela de observação, não uma lei do negócio. Ao impor score = 0 acima de 138d, você confunde 'não observamos fechamento após 138d' com 'não é possível fechar após 138d'. Se um deal Enterprise real de 160 dias estiver vivo, sua ferramenta manda o vendedor descartá-lo. Isso destrói a confiança do time comercial na primeira semana."*

**Ação de Engenharia:**
- Eliminamos o corte binário de 138 dias.
- Substituímos por uma curva suave de decaimento logístico/exponencial com piso de proteção e instituímos a flag auditável `Zombie Suspect` acima do P95 da coorte (~118 dias), acionando playbook de higienização em vez de descarte cego.

---

### Crítica 2: A Distorção de 486x no Preço dos Produtos ($55 a $26.768)
> *"Um único deal de GTK 500 ($26.768) com P=0.20 gera EV=$5.353, ofuscando 50 deals de MG Special ($55) com P=0.80. O ranking vira uma lista dos 10 deals mais caros, replicando o erro ingênuo do vendedor sem IA. Além disso, ignora o tempo de ciclo: $26k em 120 dias tem retorno diário muito pior que $3k em 15 dias."*

**Ação de Engenharia:**
- Criamos a métrica de **Velocidade de Receita ($EV/Dia$)**, dividindo o valor esperado pelos dias restantes estimados no ciclo.
- Normalizamos a escala combinada no `priority_score` (0-100), equilibrando a probabilidade de vitória, o yield diário e o volume absoluto.

---

### Crítica 3: A Ausência de Backtest Temporal Out-of-Time
> *"Quase todas as submissões treinam e testam in-sample ou com k-fold aleatório, vazando informação temporal. Para provar que a ferramenta funciona, é obrigatório um split temporal estrito (treino em período T, teste cego no período posterior) comparando com baselines ingênuos."*

**Ação de Engenharia:**
- Construímos o motor de validação em `src/backtest.py` com split em 30/06/2017, testando cegamente em 4.032 negócios fechados posteriormente e reportando AUC, Brier Score e Lift no Top 20%.

---

### Crítica 4: Os 500 Deals em Prospecting sem `engage_date`
> *"Misturar leads em prospecção com deals engajados polui o cálculo de aging. Excluí-los perde 24% do pipeline ativo."*

**Ação de Engenharia:**
- Particionamos o produto em duas abas dedicadas: **Closers (`Engaging` - 1.589 deals)** e **SDRs (`Prospecting` - 500 leads)** com modelo específico de Fit ICP.
