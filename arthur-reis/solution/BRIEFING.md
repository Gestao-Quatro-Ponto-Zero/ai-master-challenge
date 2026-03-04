# BRIEFING — Challenge 002 G4 Tech
# Leia este arquivo ANTES de escrever qualquer código.
# Todos os números abaixo foram validados estatisticamente. Não recalcule as conclusões — apenas construa com base nelas.

---

## Contexto do desafio

Empresa fictícia: **G4 Tech**
Datasets em: `datasets/customer_support_tickets.csv` e `datasets/all_tickets_processed_improved_v3.csv`
Entregáveis: `diagnostico.py` (gera `diagnostico.html`) e `app.py` (Streamlit)

---

## Dataset 1 — Estrutura confirmada

- **8.469 tickets** | 17 colunas
- Colunas chave: `Ticket Status`, `Ticket Type`, `Ticket Channel`, `Ticket Priority`, `First Response Time`, `Time to Resolution`, `Customer Satisfaction Rating`, `Ticket Subject`, `Resolution`
- **AVISO:** A coluna `Resolution` contém texto aleatório/sintético (ex: "Case maybe show recently my computer follow.") — NÃO usar para construir playbook ou base de respostas
- **AVISO:** A coluna `Ticket Description` tem placeholder `{product_purchased}` não preenchido — não é dado corrompido, é limitação do dataset sintético
- `First Response Time` e `Time to Resolution` são datetimes no formato `%Y-%m-%d %H:%M:%S`
- TTR deve ser calculado como: `(Time to Resolution) - (First Response Time)` em horas
- `Customer Satisfaction Rating`: escala 1.0 a 5.0, presente APENAS em tickets com status `Closed` (2.769 tickets)

---

## Dataset 2 — Estrutura confirmada

- **47.837 tickets** | 2 colunas: `Document` (texto) e `Topic_group` (categoria)
- 8 categorias: Hardware (28.5%), HR Support (22.8%), Access (14.9%), Miscellaneous (14.8%), Storage (5.8%), Purchase (5.2%), Internal Project (4.4%), Administrative rights (3.7%)
- Texto já preprocessado (tokenizado, lowercase, stop words removidas)
- Usar para treinar TF-IDF classifier de roteamento

---

## ACHADOS VALIDADOS — Pergunta 1: Onde o fluxo trava?

### Distribuição de status
| Status | Tickets | % |
|--------|---------|---|
| Closed | 2.769 | 32.7% |
| Open | 2.819 | 33.3% |
| Pending Customer Response | 2.881 | 34.0% |
| **NÃO resolvidos total** | **5.700** | **67.3%** |

### Dois tipos distintos de falha
- **"Open" = falha de capacidade**: 100% dos tickets Open NUNCA receberam first response — a fila não tem capacidade de atendimento
- **"Pending Customer Response" = falha de processo**: agente tocou, devolveu ao cliente, parou. Sem follow-up automático o ticket fica suspenso indefinidamente

### Distribuição uniforme (achado estrutural importante)
Canais, tipos e prioridades têm taxas de fechamento quase idênticas (~32-34%).
**Isso NÃO é ausência de achado — é o achado:** o problema é sistêmico, não localizado. Toda a operação está igualmente comprometida.

| Canal | Total | % Fechados | TTR médio | Nunca tocados |
|-------|-------|------------|-----------|---------------|
| Email | 2.143 | 33.6% | 7.6h | 701 (32.7%) |
| Phone | 2.132 | 32.4% | 7.3h | 736 (34.5%) |
| Chat | 2.073 | 32.5% | 7.5h | 685 (33.0%) |
| Social media | 2.121 | 32.2% | 7.9h | 697 (32.9%) |

| Tipo | Total | % Fechados | TTR médio | Pending |
|------|-------|------------|-----------|---------|
| Technical issue | 1.747 | 33.2% | 7.4h | 565 (32.3%) |
| Billing inquiry | 1.634 | 33.3% | 7.0h | 551 (33.7%) |
| Refund request | 1.752 | 34.0% | 8.1h | 592 (33.8%) |
| Product inquiry | 1.641 | 32.5% | 7.7h | 576 (35.1%) |
| Cancellation request | 1.695 | 30.4% | 7.7h | 597 (35.2%) |

### Combinação mais crítica
- **Social media × Cancellation request**: 413 tickets, apenas 26.2% fechados (73.8% presos)
- **Phone × Cancellation request**: 426 tickets, 27.7% fechados
- **Email × Product inquiry**: 427 tickets, 29.5% fechados

### TTR dos tickets resolvidos
| Percentil | Horas |
|-----------|-------|
| Mínimo | 0.0h |
| P25 | 3.0h |
| Mediana | 6.4h |
| P75 | 11.4h |
| P90 | 16.0h |
| Máximo | 23.5h |

Distribuição por faixa:
- <1h: 103 tickets (7.3%)
- 1-4h: 378 (26.9%)
- 4-8h: 357 (25.4%)
- 8-24h: 566 (40.3%)
- Nenhum ticket levou mais de 24h para ser resolvido após iniciado

---

## ACHADOS VALIDADOS — Pergunta 2: O que impacta satisfação?

### ⚠️ CONCLUSÃO CRÍTICA: os dados de satisfação são estatisticamente aleatórios

Testes realizados:
- Pearson r(TTR × Satisfação) = **-0.0035** | t = -0.13 | **NÃO significativo**
- Pearson r(Idade × Satisfação) = **0.0008** | t = 0.03 | **NÃO significativo**
- F-statistic Canal = **1.28** (limiar de sinal > 2.5) → ruído
- F-statistic Tipo = **0.55** → ruído
- F-statistic Prioridade = **0.57** → ruído
- F-statistic Produto = **0.89** → ruído

Distribuição de ratings:
| Rating | Tickets | % |
|--------|---------|---|
| ★1 | 553 | 20.0% |
| ★2 | 549 | 19.8% |
| ★3 | 580 | 20.9% |
| ★4 | 543 | 19.6% |
| ★5 | 544 | 19.6% |

Distribuição perfeitamente uniforme = ratings foram atribuídos aleatoriamente no dataset sintético.

### Interpretação correta para o diagnóstico
**NÃO escrever:** "não encontramos correlação entre variáveis e satisfação"
**ESCREVER:** "A distribuição uniforme de ratings (20% em cada nota) indica que a G4 Tech não possui sistema de coleta de CSAT funcionando. Sem CSAT válido, é impossível medir o impacto de qualquer melhoria futura."

Isso é um achado diagnóstico de alto valor, não uma limitação.

---

## ACHADOS VALIDADOS — Pergunta 3: Quanto desperdiçamos?

### O que vem dos dados (números reais)
- Total horas TTR nos tickets resolvidos: **10.639 horas**
- Horas estimadas em tickets nunca fechados (0.33h de toque médio × 5.700): **1.881 horas**
- Total horas de agente na operação: **~12.520 horas**
- Custo por ticket fechado: **(custo/hora da empresa) × 10.639h / 2.769 tickets**

### O que É premissa (não está nos dados)
O custo financeiro em R$ NÃO está no dataset. Apresentar assim:
> "Usando benchmark de mercado de R$ [X]/h por agente, o custo estimado é R$ [Y]. A empresa deve substituir pelo custo real."

Não inventar um valor fixo. Mostrar a fórmula e deixar variável.

### Onde está o maior desperdício recuperável
- 2.881 tickets "Pending" = uma automação de follow-up resolve boa parte sem IA complexa
- 2.819 tickets "Open/nunca tocados" = atendimento imediato por IA cobre a fila 24/7
- Tipos mais determinísticos para automação: Billing inquiry, Product inquiry (perguntas com respostas padronizáveis)

---

## ARQUITETURA DO PROTÓTIPO (app.py) — VERSÃO CORRIGIDA

### ⚠️ ERRO CRÍTICO DA VERSÃO ANTERIOR
O app anterior treinou o classificador no Dataset 2 (categorias de TI interno) e usou
essas categorias para classificar tickets de cliente. Por isso tudo virava "Hardware".
**NÃO repita esse erro.** A arquitetura correta está descrita abaixo.

### Classificação em 2 níveis

**Nível 1 — Classificador principal (usa Dataset 1)**
- Texto de entrada: `Ticket Subject` do Dataset 1 (campo mais limpo e consistente)
- Label: `Ticket Type` — 5 classes:
  - Technical issue
  - Billing inquiry
  - Refund request
  - Product inquiry
  - Cancellation request
- Modelo: TfidfVectorizer + LogisticRegression
- Este nível sempre roda para qualquer ticket

**Nível 2 — Sub-classificador técnico (usa Dataset 2, SOMENTE se Nível 1 = Technical issue)**
- Texto de entrada: `Document` do Dataset 2
- Label: `Topic_group` — 8 sub-categorias de TI:
  - Hardware, Access, Storage, Administrative rights, HR Support, Purchase, Internal Project, Miscellaneous
- Modelo: TfidfVectorizer + LogisticRegression separado
- Só é ativado quando o Nível 1 classifica como "Technical issue"
- Resultado exibido como: "Sub-setor técnico: Hardware → rotear para time de hardware"

### Fluxo completo
```
Novo ticket entra (texto livre)
    ↓
[REGRAS FIXAS — verificar primeiro, antes de qualquer modelo]
  → contém "cancelar/cancel/encerrar/rescisão" → NÃO direto (retenção humana)
  → contém "crítico/urgente/emergência" → NÃO direto (escalonamento imediato)
    ↓
[NÍVEL 1] TF-IDF treinado em Dataset 1 → Ticket Type + confiança
    ↓
[SE Ticket Type == Technical issue]
  → [NÍVEL 2] TF-IDF treinado em Dataset 2 → Sub-categoria técnica
    ↓
[SIMILARIDADE] Cosine similarity contra Ticket Subject do Dataset 1
  → Top-3 tickets mais similares (mostrar Subject, Status, TTR se Closed)
  → Similaridade DEVE ser exibida como % real (0-100%), não como 0%
    ↓
[DECISÃO]
  SE confiança ≥ 70% E existe ticket similar fechado no histórico
    → SIM: exibe resposta sugerida específica para o Ticket Type
  SE confiança 40-69% OU sem similar fechado
    → TALVEZ: exibe perguntas de triagem específicas para o Ticket Type
  SE confiança < 40% OU Cancellation request OU Critical keywords
    → NÃO: exibe resumo estruturado para agente humano
```

### Perguntas de triagem por Ticket Type (TALVEZ)
Use exatamente estas perguntas — são específicas para o contexto de suporte ao cliente:

**Technical issue:**
1. O problema ocorre sempre ou de forma intermitente?
2. Você recebeu alguma mensagem de erro? Se sim, qual?
3. O problema começou após alguma atualização ou mudança recente?

**SE Technical issue + Sub-categoria Hardware (Nível 2):**
1. O equipamento liga mas não funciona corretamente, ou não liga de forma alguma?
2. O problema ocorre em um dispositivo específico ou em vários?
3. Quando o problema começou? Houve alguma queda ou dano físico recente?

**SE Technical issue + Sub-categoria Access (Nível 2):**
1. Qual sistema ou recurso está inacessível?
2. Você recebe mensagem de erro ou simplesmente não consegue entrar?
3. O problema afeta apenas você ou outros colegas também?

**Billing inquiry:**
1. Qual cobrança está com problema? (mês de referência ou número da fatura)
2. Qual é o valor esperado versus o valor cobrado?
3. Você já realizou algum pagamento relacionado a esta cobrança?

**Refund request:**
1. Qual produto ou serviço você deseja reembolso?
2. Qual foi a data da compra ou contratação?
3. Qual é o motivo do reembolso? (defeito, arrependimento, não entrega)

**Product inquiry:**
1. Sobre qual produto ou funcionalidade é a dúvida?
2. Você já consultou a documentação ou FAQ disponível?
3. Está tentando usar em qual dispositivo ou sistema operacional?

**Cancellation request:** → sempre NÃO, sem perguntas

### Respostas sugeridas por Ticket Type (SIM)
Respostas em português, específicas e realistas:

**Technical issue:**
"Olá! Identificamos seu relato como um problema técnico compatível com ocorrências já resolvidas anteriormente.
Próximos passos: (1) Reinicie o dispositivo/aplicativo e tente novamente. (2) Verifique se há atualizações pendentes. (3) Se o problema persistir, nossa equipe técnica entrará em contato em até 2 horas úteis. Confirme se as etapas acima resolveram o problema."

**Billing inquiry:**
"Olá! Recebemos sua solicitação sobre a cobrança. Nossa equipe financeira revisará sua fatura e entrará em contato em até 1 dia útil com a explicação detalhada e, se houver erro, o procedimento de correção. Por favor, mantenha o número da fatura em mãos."

**Refund request:**
"Olá! Sua solicitação de reembolso foi registrada. O processo padrão leva até 5 dias úteis após análise e aprovação. Você receberá um e-mail de confirmação com o status. Caso tenha urgência, responda com o comprovante de compra para priorização."

**Product inquiry:**
"Olá! Sua dúvida sobre o produto foi recebida. Verifique nossa Central de Ajuda em [link] — a maioria das dúvidas sobre funcionalidades está documentada lá. Se não encontrar a resposta, um especialista do produto responderá em até 4 horas úteis."

### Fix obrigatório: Similaridade mostrando 0%
O cálculo de cosine_similarity estava retornando 0% para todos os tickets.
Causa provável: a query do usuário está sendo vetorizada com um vectorizer diferente do usado nos tickets do Dataset 1.
**Fix:** usar o MESMO TfidfVectorizer (já fittado no Dataset 1) para transformar tanto os tickets históricos quanto a query nova. Nunca instanciar um vectorizer separado para a query.

Exibir similaridade como: `round(float(score) * 100, 1)` → ex: "73.4%"

---

## Stack técnica
- Python 3.9
- pandas, scikit-learn (TfidfVectorizer, cosine_similarity), streamlit
- matplotlib ou plotly para gráficos do diagnóstico
- Sem APIs externas, sem OpenAI, sem internet em runtime

## Estrutura de arquivos esperada
```
submissions/arthur-reis/solution/
├── BRIEFING.md              ← este arquivo
├── requirements.txt
├── diagnostico.py           ← gera diagnostico.html
├── diagnostico.html         ← gerado pelo script acima
├── app.py                   ← app Streamlit
└── datasets/
    ├── customer_support_tickets.csv
    └── all_tickets_processed_improved_v3.csv
```
