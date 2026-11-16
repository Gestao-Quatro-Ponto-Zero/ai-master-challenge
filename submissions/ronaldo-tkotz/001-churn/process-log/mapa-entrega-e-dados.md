# Entrega pedida × o que os dados conseguem responder

> Material de apoio para desenhar o dashboard de trás para frente (D19).
> Fontes: `challenges/data-001-churn/README.md`, `submission-guide.md` e o banco `ravenstack.db` (contagens em `19_camada_sql.txt`, `20_relacoes_e_pivo.txt` e D18).
> Este documento só registra fatos sobre o enunciado e a estrutura dos dados. Ele não contém conclusões sobre o churn.

---

## 1. O que o enunciado pede

**A pergunta do CEO:** "O churn subiu, o CS diz que a satisfação está ok, o produto diz que o uso cresceu. Algo não bate."

São três afirmações, e cada uma precisa ser checada no dado:

| Afirmação | Quem diz | Campo que permite checar |
|---|---|---|
| O churn subiu | CEO ("os números") | `subscriptions.end_date`, `churn_events.churn_date` e `accounts.churn_flag` (este sem data) |
| A satisfação está ok | Time de CS | `support_tickets.satisfaction_score` |
| O uso cresceu | Time de produto | `feature_usage` (contagem, duração e data) |

**Deliverable principal:** um relatório de diagnóstico que responda a três perguntas.

1. **O que está causando o churn?** A causa raiz, e não a resposta óbvia, cruzando as tabelas.
2. **Quais segmentos estão mais em risco?** Com dados, e identificando **contas específicas**.
3. **O que a empresa deveria fazer?** Ações concretas e priorizadas, **com impacto estimado**.

**Formato:** livre (PDF, Markdown, notebook, dashboard).

**Diferenciais opcionais:**
- Um modelo preditivo que funcione.
- Um dashboard interativo.
- Uma automação que o CS use amanhã.
- Uma análise que ninguém pediu e que muda a conversa.

**Critérios de qualidade do enunciado:**
1. Cruzou as 5 tabelas?
2. Os insights são verificáveis, com os números à mostra?
3. As recomendações são acionáveis?
4. Distingue correlação de causalidade?
5. O CEO, que não é técnico, consegue ler e agir?

**Dicas do enunciado:**
- Cruzar uso com eventos de churn.
- Comparar os tickets de quem saiu com os de quem ficou.
- Testar se "o uso cresceu" vale para todos os segmentos.
- Pesar o churn por receita.
- Cuidado com correlação.

**Guia de submissão, formato que funciona bem:**
1. Executive summary de 1 parágrafo.
2. Abordagem.
3. Resultado.
4. Recomendações.
5. Limitações.

O guia também alerta: "Documento de 40 páginas onde 5 resolveriam" é sinal de submissão fraca.

**Process log (obrigatório):** precisa mostrar:
- As ferramentas usadas e por quê.
- A decomposição antes do prompt.
- Onde a IA errou e como foi corrigida.
- O que o humano acrescentou.
- O número de iterações.

---

## 2. Os níveis do dado

| Nível | Linhas | View | Liga-se a | Atributos próprios |
|---|---|---|---|---|
| **Conta** | 500 | `vw_conta` | assinaturas (2 a 19), tickets (0 a 11), eventos de churn (0 a 5) | setor (5), país (7), origem (5), plano, seats, trial, `churn_flag`, `signup_date` |
| **Assinatura** | 5.000 | `vw_assinatura` | conta (1), uso (0 a 16) | início, fim (486 preenchidos), plano, seats, MRR, ARR, trial, flags de upgrade/downgrade/churn, cobrança (anual 2.461 / mensal 2.539), renovação automática |
| **Uso** | 25.000 | `vw_uso_detalhe` | assinatura → conta | data (24 meses), recurso (40), contagem, duração, erros, beta |
| **Ticket** | 2.000 | `vw_ticket_detalhe` | conta (apenas) | data de abertura (sem hora), fechamento, horas de resolução, prioridade (4), minutos até a 1ª resposta, satisfação, escalação |
| **Evento de churn** | 600 | `vw_churn_detalhe` | conta (apenas) | data, motivo (6), refund, flags de upgrade/downgrade anterior, reativação, feedback em texto |

---

## 3. O que cada nível consegue responder

### Conta
- **Consegue:**
  - Comparar grupos (setor, país, origem, plano, trial) em assinaturas, MRR, uso, erros, tickets, satisfação e eventos de churn.
  - Listar **contas específicas** com o MRR e o ARR de cada uma, que é o peso em receita.
  - É o único nível em que as 5 tabelas se encontram.
- **Limites:**
  - O `churn_flag` da conta não tem data, então não dá para ver a evolução no tempo por ele.
  - A conta tem um único `plan_tier`, mas em 3.365 das 5.000 assinaturas o plano é diferente (N07).

### Assinatura
- **Consegue:**
  - Receita (MRR e ARR) por plano, cobrança e renovação automática.
  - Datas de início e fim, e portanto contagens mensais de entradas e saídas.
  - Uso e erros de cada assinatura.
- **Não consegue:** ligar tickets ou eventos de churn a uma assinatura específica, porque eles só se ligam à conta.

### Uso
- **Consegue:**
  - Volume por mês (24 meses), por recurso (40), por segmento da conta e por plano da assinatura.
  - Taxa de erro por recurso, e uso de recursos beta.
- **Limite (destacado, D18/D19):**
  - 19.142 dos 25.000 registros têm data anterior ao início da própria assinatura, e 13.198 são anteriores ao cadastro da conta.
  - A ficha do dataset não declara regra de data para o uso.
  - Por isso, a sequência de eventos dentro da vida de uma assinatura, como "o uso caiu antes da saída", não tem base temporal confiável. O volume por mês e por segmento não depende dessa regra.

### Ticket
- **Consegue:**
  - Volume, prioridade, escalação, horas de resolução e minutos até a primeira resposta, nos valores do campo.
  - Comparação por conta e por segmento.
- **Limites:**
  - A satisfação está vazia em 825 dos 2.000 tickets, e as notas preenchidas vão só de 3 a 5 (396, 405 e 374).
  - A data de abertura não tem hora (T03), e em 100% dos tickets o fechamento é igual à abertura mais as horas de resolução (T04).
  - 1.077 tickets são anteriores ao cadastro da conta (T08).

### Evento de churn
- **Consegue:**
  - Data, motivo (6 códigos, de 91 a 114 cada), refund, reativação e flags de upgrade/downgrade anterior.
  - Comparação por segmento da conta.
- **Limites:**
  - O feedback em texto tem só 3 frases distintas, mais 148 vazios, o que não dá base para análise de texto.
  - 175 contas têm mais de um evento.
  - Ele discorda da marcação na conta: 277 contas com evento têm `churn_flag = 0` e 35 contas marcadas não têm evento (N04 e N05).

---

## 4. O que nenhum nível tem

Nenhuma tabela contém estes dados. Qualquer resposta que dependa deles fica fora do alcance:

- Preço de lista, desconto ou histórico de reajuste.
- Usuários ativos por seat.
- Atividade do time de CS (contatos, reuniões, health score).
- NPS ou pesquisa fora dos tickets.
- Datas de lançamento de recursos.
- Concorrentes.
- Custo de aquisição.

---

## 5. Decisões em aberto, do humano

1. **Definição de churn:** qual dos três sinais usar (`churn_flag` da conta, `end_date` da assinatura ou `churn_events`), ou que combinação deles. Adiada até o dado aparecer na análise (D17).
2. **"Ativa no mês":** a regra da view mensal (D16).
3. **Política de alertas:** incluir tudo por padrão e mostrar os dois números quando um alerta mudar o resultado. Foi a proposta da IA, ainda sem decisão.
