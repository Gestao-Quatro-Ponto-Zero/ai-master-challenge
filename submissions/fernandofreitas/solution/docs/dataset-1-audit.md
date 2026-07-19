# Auditoria do Dataset 1 - Customer Support Ticket Dataset

## Objetivo

Antes de usar o dataset para diagnostico operacional, auditei sua confiabilidade para separar:

- o que podemos afirmar com seguranca;
- o que precisa de tratamento;
- o que deve aparecer como limitacao da entrega.

Arquivo auditado:

```text
C:\Users\Jufer\Downloads\datasets g4\customer_support_tickets.csv
```

---

## Estrutura geral

| Item | Valor |
|---|---:|
| Linhas | 8.469 |
| Colunas | 17 |
| Tamanho aproximado | 3,76 MB |
| Ticket IDs duplicados | 0 |
| Linhas completamente duplicadas | 0 |

Embora o briefing mencione cerca de 30.000 tickets, o arquivo publico baixado contem 8.469 registros.

---

## Colunas

| Coluna | Tipo | Nulos | Observacao |
|---|---:|---:|---|
| Ticket ID | inteiro | 0 | Identificador unico |
| Customer Name | texto | 0 | Nao sera usado na analise |
| Customer Email | texto | 0 | Nao sera usado na analise |
| Customer Age | inteiro | 0 | Valores de 18 a 70 |
| Customer Gender | texto | 0 | 3 categorias |
| Product Purchased | texto | 0 | 42 produtos |
| Date of Purchase | texto/data | 0 | Datas validas |
| Ticket Type | texto | 0 | 5 categorias |
| Ticket Subject | texto | 0 | 16 assuntos |
| Ticket Description | texto | 0 | Texto disponivel em todos os tickets |
| Ticket Status | texto | 0 | 3 status |
| Resolution | texto | 5.700 | Preenchido apenas para fechados |
| Ticket Priority | texto | 0 | 4 prioridades |
| Ticket Channel | texto | 0 | 4 canais |
| First Response Time | texto/data | 2.819 | Ausente em tickets Open |
| Time to Resolution | texto/data | 5.700 | Preenchido apenas para fechados |
| Customer Satisfaction Rating | numero | 5.700 | Preenchido apenas para fechados |

---

## Distribuicao operacional

### Status

| Status | Tickets |
|---|---:|
| Pending Customer Response | 2.881 |
| Open | 2.819 |
| Closed | 2.769 |

Interpretacao:

- Apenas 32,7% dos tickets estao fechados.
- CSAT, resolucao e tempo de resolucao so existem para tickets fechados.
- O backlog aberto/pendente e relevante para a narrativa operacional.

### Canais

| Canal | Tickets |
|---|---:|
| Email | 2.143 |
| Phone | 2.132 |
| Social media | 2.121 |
| Chat | 2.073 |

Os canais estao bem balanceados, o que ajuda comparacoes relativas.

### Tipos

| Tipo | Tickets |
|---|---:|
| Refund request | 1.752 |
| Technical issue | 1.747 |
| Cancellation request | 1.695 |
| Product inquiry | 1.641 |
| Billing inquiry | 1.634 |

Os tipos tambem estao bem balanceados.

### Prioridades

| Prioridade | Tickets |
|---|---:|
| Medium | 2.192 |
| Critical | 2.129 |
| High | 2.085 |
| Low | 2.063 |

As prioridades estao quase uniformes. Isso e bom para comparacao, mas pode ser artificial para uma operacao real.

---

## Consistencia de status

O relacionamento entre status e campos preenchidos e coerente:

| Regra | Problemas encontrados |
|---|---:|
| Closed sem Resolution | 0 |
| Closed sem Time to Resolution | 0 |
| Closed sem Satisfaction | 0 |
| Open com Resolution | 0 |
| Open com Time to Resolution | 0 |
| Pending com Resolution | 0 |
| Pending com Time to Resolution | 0 |

Conclusao:

> O dataset e consistente na regra basica de que apenas tickets fechados possuem resolucao, tempo de resolucao e satisfacao.

---

## Problema critico: timestamps

Ao calcular:

```text
Time to Resolution - First Response Time
```

o resultado bruto apresentou:

| Metrica | Valor |
|---|---:|
| Tickets fechados com delta calculavel | 2.769 |
| Deltas negativos | 1.365 |
| Deltas zero | 2 |
| Deltas positivos | 1.402 |
| Menor delta | -23,23h |
| Mediana bruta | 0,17h |
| Maior delta | 23,47h |

Isso significa que em quase metade dos tickets fechados o horario de resolucao aparece antes do horario de primeira resposta.

Possiveis explicacoes:

- timestamps foram gerados de forma sintetica;
- existe ambiguidade de data/hora;
- os campos nao representam exatamente o fluxo real;
- pode haver efeito de virada de dia.

Decisao metodologica recomendada:

- Nao usar o tempo bruto sem tratamento.
- Documentar a inconsistencia como limitacao.
- Para analises comparativas, aplicar regra de correcao de virada de dia quando o delta for negativo:

```text
se delta < 0, delta_corrigido = delta + 24h
```

Essa regra permite preservar a amostra fechada inteira, mas nao transforma a metrica em SLA oficial.

---

## Qualidade textual

### Assuntos recorrentes

| Assunto | Tickets |
|---|---:|
| Refund request | 576 |
| Software bug | 574 |
| Product compatibility | 567 |
| Delivery problem | 561 |
| Hardware issue | 547 |
| Battery life | 542 |
| Network problem | 539 |
| Installation support | 530 |
| Product setup | 529 |
| Payment issue | 526 |
| Product recommendation | 517 |
| Account access | 509 |
| Peripheral compatibility | 496 |
| Data loss | 491 |
| Cancellation request | 487 |
| Display issue | 478 |

Isso e util para construir um FAQ inicial.

### Problemas encontrados nos textos

- Todas as descricoes contem o placeholder `{product_purchased}`.
- Ha trechos com ruido e frases pouco naturais.
- Em alguns casos, `Ticket Type`, `Ticket Subject` e descricao nao combinam perfeitamente.
- `Resolution` tem textos muito curtos e frequentemente pouco informativos.

Exemplo de desalinhamento:

```text
Tipo: Billing inquiry
Assunto: Cancellation request
Descricao: problema de software bug
```

Conclusao:

> O texto serve para demonstrar triagem, FAQ e classificacao, mas nao deve ser tratado como conversa real 100% limpa.

---

## O que podemos afirmar com seguranca

Podemos usar o dataset para:

- analisar volume por status;
- analisar distribuicao por canal, tipo, prioridade e assunto;
- identificar backlog;
- comparar grupos operacionais de forma relativa;
- construir FAQ com base nos assuntos recorrentes;
- simular uma operacao de triagem;
- demonstrar um painel admin;
- estimar desperdicio com ressalvas.

---

## O que exige cuidado

Devemos ter cuidado ao afirmar:

- tempo medio exato de resolucao;
- SLA real da operacao;
- impacto causal na satisfacao;
- qualidade real das respostas dos agentes;
- conclusoes profundas baseadas no texto bruto.

---

## Parecer de confiabilidade

| Criterio | Avaliacao | Comentario |
|---|---|---|
| Integridade estrutural | Boa | IDs unicos, sem duplicidade |
| Consistencia de status | Boa | Campos de fechado/aberto coerentes |
| Cobertura de CSAT | Parcial | Apenas tickets fechados |
| Confiabilidade de timestamps | Baixa/media | Muitos deltas negativos |
| Qualidade textual | Media/baixa | Texto sintetico e ruidoso |
| Utilidade para diagnostico | Boa com ressalvas | Excelente para padroes e backlog |
| Utilidade para prototipo | Boa | Serve para FAQ, triagem e admin |

Parecer final:

> O Dataset 1 e confiavel para construir uma demonstracao operacional e identificar padroes gerais de suporte, mas nao e confiavel o bastante para conclusoes exatas de SLA sem tratamento dos timestamps. A melhor abordagem e usar o dataset com transparencia, destacando as inconsistencias como parte da maturidade analitica da entrega.

---

## Implicacoes para o produto

Com base na auditoria, o sistema deve:

1. Usar os 16 assuntos recorrentes como base do FAQ.
2. Mostrar backlog e distribuicoes com confianca.
3. Usar tempo de resolucao corrigido e sempre mencionar a regra metodologica.
4. Evitar prometer resposta automatica para todos os casos.
5. Priorizar triagem, roteamento e coleta de contexto, em vez de "resolucao autonoma" completa.
