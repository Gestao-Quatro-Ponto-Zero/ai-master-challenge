# Diagnóstico operacional — Dataset 1

**Pergunta do Diretor:** onde estamos perdendo tempo, o que impacta a satisfação e quanto desperdiçamos?

**Resposta curta:** com este arquivo, nenhuma dessas três perguntas tem resposta confiável. Se ele reflete o que a operação registra hoje, o primeiro achado é que ela não consegue se medir. Abaixo, o que os dados sustentam, o que é ruído e o que precisa passar a ser registrado.

> **Em linguagem de diretor:** "teste de permutação, p = 0,26" quer dizer que, embaralhando os dados ao acaso, uma diferença daquele tamanho aparece em 26% das vezes — ou seja, não é um padrão real. "p > 0,25" nas tabelas tem o mesmo sentido: diferença compatível com o acaso.

Reprodução: `analysis/01_inspecao_dados.py` e `analysis/02_diagnostico.py` sobre `customer_support_tickets.csv` (Kaggle, suraj520).

---

## Os três achados

**A. A prioridade registrada não tem efeito mensurável.**
Tickets Critical ficam sem primeira resposta na mesma proporção que os Low (32,5% × 33,7%; média geral 33,3%). Há duas explicações possíveis: a triagem por urgência não acontece, ou acontece e não é registrada. Como o arquivo tem sinais de ser gerado por computador, isto é uma **hipótese a confirmar** com dados reais — não uma conclusão. Se confirmada, as duas explicações levam à mesma ação: triagem de prioridade registrada, baseada em fatos.

**B. Os dados não medem o que gera insatisfação.**
Nenhuma variável registrada explica a nota de satisfação. Além disso, a nota só existe nos 32,7% de tickets fechados: o cliente preso no backlog, provavelmente o mais insatisfeito, nunca avalia (viés de sobrevivência; ideia vista no teste de baseline e incorporada com crédito — decisão 11).

**C. Os "gargalos" aparentes são ruído.**
A pior combinação canal × prioridade × tipo (Telefone + Low + Cancelamento) tem 80,6% de tickets não resolvidos, contra 56,6% da melhor. Parece um achado. Mas, embaralhando os dados mil vezes, diferenças desse tamanho aparecem em 26% das vezes (p = 0,26). Investir para "corrigir" esse gargalo seria desperdiçar dinheiro.

---

## 1. Onde o fluxo trava?

| Situação | Tickets | % |
|---|---|---|
| Sem primeira resposta (Open) | 2.819 | 33,3% |
| Aguardando o cliente (Pending) | 2.881 | 34,0% |
| Fechados | 2.769 | 32,7% |

Dois em cada três tickets não estão resolvidos, e a proporção é a mesma em qualquer recorte:

| Recorte | % não resolvido (mín.–máx.) | Qui-quadrado (status × recorte) |
|---|---|---|
| Canal | 66,4% – 67,8% | p = 0,77 |
| Prioridade | 65,9% – 68,8% | p = 0,23 |
| Tipo | 66,0% – 69,6% | p = 0,34 |
| 80 combinações canal × prioridade × tipo | 56,6% – 80,6% | permutação, p = 0,26 |

**Por que não analisamos tempo de resolução.** O arquivo não tem horário de abertura do ticket. Os campos `First Response Time` e `Time to Resolution` são horários soltos, todos dentro de uma janela de 27 horas, e em 49,3% dos tickets fechados a resolução aparece antes da primeira resposta. Calcular "tempo de resolução" com esses campos — mesmo filtrando os valores negativos — produz números sem significado. Por isso este diagnóstico usa o status, que é coerente.

## 2. O que impacta a satisfação?

Notas de 1 a 5 com volumes quase iguais (553 / 549 / 580 / 543 / 544; média 2,99).

| Variável | Teste | p |
|---|---|---|
| Canal | Kruskal-Wallis | 0,28 |
| Prioridade | Kruskal-Wallis | 0,63 |
| Tipo | Kruskal-Wallis | 0,70 |
| Assunto | Kruskal-Wallis | 0,81 |
| Produto | Kruskal-Wallis | 0,67 |
| Tempo entre 1ª resposta e resolução | Spearman (ρ = 0,02) | 0,25 |
| Idade | Spearman (ρ = −0,004) | 0,83 |

Um modelo (Random Forest, validação cruzada 5×) que tenta prever a nota com todas essas variáveis acerta 19,5%. Chutar sempre a nota mais comum acerta 20,9%.

## 3. Quanto estamos desperdiçando?

**Onde está o maior desperdício recuperável:** o arquivo não registra esforço nem encaminhamentos, então ele não pode ser medido aqui. Pelas premissas abaixo, o maior desperdício que dá para recuperar com IA é o **ticket encaminhado para o time errado**: custa esforço de quem reencaminha e, principalmente, tempo perdido de quem abriu o chamado. A triagem manual vem em segundo. O primeiro passo real é medir os dois (plano de medição abaixo).

Premissas explícitas, todas editáveis no protótipo:

| Premissa | Valor | Origem |
|---|---|---|
| Volume | 30.000 tickets/ano | Briefing |
| Triagem manual | 3 min/ticket (faixa 2–4) | Estimativa do Rafael; mercado usa ~5 min (Autotask). Superestima um pouco: o time que recebe ainda lê o ticket |
| Custo do atendente | R$ 20/h | R$ 3.440/mês com encargos, ~39 h/semana (Portal Salário/CAGED) |
| Erro de encaminhamento manual | 20% | **Premissa sem fonte**, estimada pelo Rafael; trocar pelo dado real (sensibilidade abaixo) |
| Esforço por reencaminhamento | 3,5 min (faixa 2–5) | Estimativa do Rafael |
| Tempo perdido por reencaminhamento | 40 min | [HappySignals](https://happysignals.com/blog/measuring-servicenow-reassignment-counts-on-employee-productivity): 40 min extras por reencaminhamento, **estimados pelos próprios usuários** de TI interna (não clientes, e não tempo de espera medido) |

**Hipótese**, não estimativa: aplica o desempenho medido em TI interna (limiar 80%; 90% em Suporte a software; filas por regra desviando ~5%) ao volume do briefing. Na operação de clientes, o modelo atual encaminharia só ~12% sozinho; os números abaixo valem para um modelo retreinado que se comporte como o de TI.

| Erro manual de hoje | Horas de atendente liberadas/ano | R$/ano (bruto) | Reencaminhamentos evitados | Tempo perdido evitado (usuários) |
|---|---|---|---|---|
| 10% | 985 h | R$ 19,7 mil | 1.257 | 838 h |
| **20% (base)** | **1.092 h** | **R$ 21,8 mil** | **3.081** | **2.054 h** |
| 30% | 1.198 h | R$ 24,0 mil | 4.905 | 3.270 h |

Em contrapartida, ~568 tickets/ano seriam encaminhados errado pela IA sozinha.

**Leitura honesta:**
- O ganho em folha é modesto (≈ 0,5 atendente) e **bruto**: a implantação (integração, retreino, auditoria semanal, manutenção das regras) precisa custar menos que ~R$ 22 mil/ano para se pagar só por esse lado.
- O valor principal está em menos tempo perdido com tickets no time errado — e esse número depende de uma premissa (erro manual) que precisa ser medida antes de qualquer investimento.
- A conta é conservadora num ponto: assume 20% de erro também na fila "Atendente escolhe", embora o atendente receba 2 opções e a certa esteja entre elas em 90% dos casos.

---

## Plano de medição (o primeiro passo, antes de qualquer automação)

1. **Data e hora de abertura** de cada ticket.
2. **Histórico de encaminhamentos** (time de origem e de destino, com horário).
3. **Motivo do contato** em categoria fechada (o protótipo já registra).
4. **Número de interações** até a resolução e **recontato** em 7 dias.
5. **Satisfação também dos tickets não resolvidos**, coletada após um prazo fixo.

Com esses cinco campos, as três perguntas do Diretor passam a ter resposta mensal.

## Limitações

- Os dados do Dataset 1 têm sinais claros de serem gerados por computador (textos com `{product_purchased}`, resoluções sem sentido, distribuições uniformes). As conclusões valem como diagnóstico **deste arquivo**, não da operação real.
- O arquivo tem 8.469 tickets, não os ~30 mil do briefing.
- As estimativas de desperdício dependem de premissas, não de medições.
