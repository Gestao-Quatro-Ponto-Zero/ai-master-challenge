# Challenge 002 — Redesign de Suporte

**Área:** Operações / CX
**Tipo:** Diagnóstico + Automação + Build
**Time budget:** 4-6 horas

---

## Contexto

Você é o novo AI Master da área de **Suporte ao Cliente** de uma empresa de tecnologia. A operação atende ~30.000 tickets por ano via email, chat, telefone e redes sociais. O time está sobrecarregado, o tempo de resolução subiu, e a satisfação do cliente caiu.

O Diretor de Operações te chamou e disse:

> *"Quero que você olhe nossos dados de suporte e me diga três coisas: onde estamos perdendo tempo, o que pode ser automatizado com IA, e me mostre que funciona — não quero só um PowerPoint. Quero ver algo rodando."*

Este challenge testa três habilidades ao mesmo tempo: capacidade analítica (diagnóstico), pensamento de processo (o que automatizar e o que não), e capacidade de construir (protótipo funcional).

---

## Dados disponíveis

Dois datasets complementares, ambos públicos no Kaggle:

### Dataset 1 — Métricas operacionais + texto de tickets

**Dataset:** [Customer Support Ticket Dataset](https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset) (licença CC0)

| Coluna | Descrição |
|--------|-----------|
| `Ticket ID` | Identificador único |
| `Customer Name`, `Email`, `Age`, `Gender` | Dados do cliente |
| `Product Purchased` | Produto relacionado ao chamado |
| `Ticket Type` | Tipo (Technical issue, Billing inquiry, Product inquiry) |
| `Ticket Subject` | Assunto resumido |
| `Ticket Description` | **Texto completo** da reclamação/pedido do cliente |
| `Ticket Status` | Open, Closed, Pending customer response |
| `Resolution` | **Texto da resolução** aplicada pelo agente |
| `Ticket Priority` | Low, Medium, High, Critical |
| `Ticket Channel` | Email, Phone, Chat, Social media |
| `First Response Time` | Tempo até primeira resposta |
| `Time to Resolution` | Tempo total até resolução |
| `Customer Satisfaction Rating` | Nota de satisfação do cliente |

**~30.000 registros** com texto real de descrição e resolução.

### Dataset 2 — Classificação de tickets IT

**Dataset:** [IT Service Ticket Classification Dataset](https://www.kaggle.com/datasets/adisongoh/it-service-ticket-classification-dataset) (licença CC0)

| Coluna | Descrição |
|--------|-----------|
| `Document` | **Texto completo** do ticket de suporte |
| `Topic_group` | Classificação em 8 categorias (Hardware, HR Support, Access, Storage, Purchase, etc.) |

**~48.000 registros** com texto real de tickets de uma organização.

---

## O que entregar

### 1. Diagnóstico operacional (obrigatório)

Com base no Dataset 1, identifique com dados:

- **Onde o fluxo trava?** Gargalos por canal, prioridade, tipo de ticket. Quais combinações geram os piores tempos de resolução?
- **O que impacta satisfação?** Quais variáveis mais influenciam o `Customer Satisfaction Rating`? É o tempo de resposta? O canal? O tipo de problema?
- **Quanto estamos desperdiçando?** Quantifique em horas e, se possível, estime custo. Onde está o maior desperdício recuperável?

### 2. Proposta de automação com IA (obrigatório)

Com base em ambos os datasets, proponha:

- **O que automatizar** — Classificação automática, roteamento inteligente, respostas sugeridas, triagem de prioridade, detecção de duplicatas — o que fizer sentido com base nos dados.
- **O que NÃO automatizar** — Nem tudo deve ser delegado para IA. Quais tipos de ticket exigem julgamento humano? Justifique com exemplos dos dados.
- **Como funcionaria na prática** — Descreva o fluxo proposto: ticket entra → o que acontece em cada etapa → onde IA atua → onde humano intervém.

### 3. Protótipo funcional (diferencial)

Construa algo que demonstre que sua proposta funciona. Exemplos:
- Um classificador de tickets que recebe texto e retorna categoria + confiança
- Um sistema de respostas sugeridas baseado em tickets similares
- Um roteador automático que categoriza e prioriza tickets novos
- Um dashboard que mostra os gargalos em tempo real
- Qualquer coisa funcional que demonstre a automação proposta

### 4. Process log (obrigatório)

Evidências de como você usou IA. Leia o [Guia de Submissão](../../submission-guide.md).

---

## Critérios de qualidade

- Usou ambos os datasets? (um tem métricas, outro tem texto — o poder está no cruzamento)
- O diagnóstico tem números concretos ou é genérico?
- A proposta de automação é realista? (automatizar 100% é red flag, não virtude)
- Sabe distinguir onde IA ajuda de onde humano é insubstituível?
- Se construiu protótipo: funciona com dados reais, não com 3 exemplos cherry-picked?

---

## Dicas

- O Dataset 1 tem métricas operacionais. O Dataset 2 tem 48K textos classificados em 8 categorias — excelente pra treinar/testar classificadores.
- "Usar NLP para classificar tickets" é genérico. "Classificar tickets em 8 categorias com 92% de acurácia usando embeddings + zero-shot classification" é específico.
- Pense no agente de suporte: o que facilitaria a vida dele no dia a dia?
- O Diretor de Operações quer ver ROI. Se puder estimar "automação X economiza Y horas/mês", isso muda a conversa.
- Cuidado com a armadilha de automatizar tudo — os melhores candidatos sabem onde parar.
