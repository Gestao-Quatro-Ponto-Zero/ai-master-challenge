# Screenshots — Process Log

Evidências visuais das análises iterativas realizadas com Claude durante o Challenge 002.

---

![Nota sobre fit de automação não uniforme dentro de Hardware — insight sobre domain shift e distinção entre Product inquiry (alto fit) e Refund request (baixo fit)](image.png)

---

![Correção do cálculo de ROI: wall-clock time de 7,75h substituído por AHT de mercado (15-30 min/ticket), reduzindo estimativa de USD $130K/mês para USD $4.258-8.517/mês — Erro 1 documentado no process log](image-1.png)

---

![Análise de gargalo por canal e tipo: Social Media e Chat são os mais lentos; Refund e Cancellation travam mais por tipo](image-2.png)

---

![Correlação CSAT × variáveis operacionais: tempo de resolução = -0,001 (praticamente zero), idade do cliente = -0,004 — nenhuma variável isolada explica satisfação](image-3.png)

---

![Inversão de prioridade confirmada: High (7,28h) demora mais que Critical (6,55h) — evidência de triagem quebrada; pior combo absoluto: Email + Technical issue + Low → mediana 10,31h](image-4.png)

---

![Crosstab Predicted_Topic × Ticket Priority: distribuição uniforme (~25% em cada prioridade para todas as categorias) — prioridade atribuída sem critério sistemático](image-5.png)

---

![Hardware marcados como Low: 1.862 tickets, 631 Open sem resposta — CSAT de Low (3,04) ligeiramente melhor que Critical (2,93), confirmando que o sistema de priorização está quebrado](image-6.png)

---

![Validação cruzada dos números com o notebook: todos os 5 valores por Ticket Type conferem exatamente (Cancellation 1.179, Technical 1.167, Refund 1.156, Product 1.108, Billing 1.090)](image-7.png)

---

![Densidade de notas ruins por categoria predita: Miscellaneous com 44,3% de notas 1-2 é o sinal mais importante; correlação tempo × CSAT não significativa em nenhuma categoria](image-8.png)

---

![Conclusão da análise de satisfação: Hardware com notas ruins vs boas tem tempo praticamente idêntico (7,78h vs 7,71h) — o problema é resolução de mérito, não velocidade](image-9.png)
