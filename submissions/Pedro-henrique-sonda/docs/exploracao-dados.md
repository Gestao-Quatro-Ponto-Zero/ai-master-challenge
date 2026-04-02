# Exploração dos Dados — Confronto com Hipóteses Iniciais

## 1. Visão Geral dos Dados

Antes de construir qualquer lógica de scoring, precisei entender o terreno. Rodei análises exploratórias nos 4 CSVs com apoio de IA (Claude) e aqui registro o que encontrei.

**Números gerais do pipeline:**
- 8.800 oportunidades no total
- 2.089 deals abertos (500 em Prospecting, 1.589 em Engaging)
- Taxa de conversão geral: 63,2% (Won vs Lost)
- Valor médio dos deals Won: $2.361
- Tempo médio para fechar: 51 dias (Won) vs 41 dias (Lost)

**Estrutura dos dados:**
- 85 contas em 10 setores diferentes
- 7 produtos em 3 séries (GTX, MG, GTK), com preços de $55 a $26.768
- 35 vendedores, 6 managers, 3 escritórios regionais (Central, East, West)
- Deals em Prospecting não possuem engage_date; deals em Engaging possuem 100%

---

## 2. Confronto Hipótese por Hipótese

### Hipótese 1 — O stage atual do deal importa
**Resultado: Confirmada ✅**

Prospecting e Engaging são estágios qualitativamente diferentes. Nenhum deal em Prospecting tem engage_date — são leads que ainda não tiveram interação real. Todos os deals em Engaging têm engage_date. O stage não é apenas um label, marca uma transição concreta na jornada do deal. Isso vai pesar no scoring. Porém, é importante ressaltar que um deal em Prospecting não terá necessariamente um score menor que um em Engaging — as outras features de análise (sazonalidade, combinação setor+produto, histórico do vendedor, valor potencial) podem compensar e colocar um deal em Prospecting acima de um em Engaging. O stage é um fator, não uma sentença.

### Hipótese 2 — Tempo no pipeline + stage contam uma história
**Resultado: Confirmada ✅ com uma surpresa importante**

Eu esperava que deals mais demorados fossem deals piores. Os dados mostraram o contrário: deals Won levam em média 51 dias para fechar, enquanto Lost levam 41 dias. Ou seja, deals perdidos são perdidos mais rápido. Isso muda minha abordagem — não posso penalizar automaticamente um deal que está há mais tempo no pipeline. Pode ser justamente o que está sendo trabalhado com cuidado.

Porém, isso não significa que tempo não importa. A combinação tempo + stage continua relevante: preciso investigar se existe um "ponto de inflexão" onde tempo demais realmente indica deal morto. Mas o dado mostrou que a relação não é linear e simplesmente "mais tempo = pior" seria um erro.

### Hipótese 3 — O setor da conta faz diferença
**Resultado: Fraca isoladamente ⚠️**

A variação entre setores é pequena: de 61,2% (finance) a 64,8% (marketing). São apenas 3,6 pontos percentuais. Como feature isolada, setor não é um bom preditor de conversão. Mas quando combinado com produto, a história muda completamente (ver hipótese 8).

### Hipótese 4 — O tamanho da empresa influencia
**Resultado: Fraca ⚠️**

Testei por faixas de revenue e de número de funcionários. Os resultados:
- Revenue 0-500: 64,1% de conversão
- Revenue 500-1000: 61,2%
- Revenue 1000-3000: 64,4%
- Revenue 3000+: 61,5%

Não há padrão claro. Empresas pequenas convertem praticamente igual a empresas grandes. A diferença no valor médio do deal também é marginal. Tamanho da empresa não vai ser um fator de peso no scoring.

### Hipótese 5 — Alguns produtos convertem mais que outros
**Resultado: Confirmada ✅ moderada**

A conversão por produto varia de 60,0% (GTK 500) a 64,8% (MG Special). Não é uma variação gritante. Mas o impacto real está no valor: MG Special tem ticket médio de $55, enquanto GTK 500 tem ticket de $26.707. O produto importa mais pelo valor potencial do que pela taxa de conversão. Isso é relevante porque o scoring precisa considerar as duas dimensões — e o produto afeta diretamente a dimensão de valor.

### Hipótese 6 — O vendedor faz diferença na conversão
**Resultado: Confirmada ✅ mas com nuances importantes — a realidade é mais complexa que "vendedor bom vs vendedor ruim"**

Olhar só taxa de conversão seria raso. Analisei cada vendedor por 4 dimensões: taxa de conversão, ticket médio, volume de deals fechados e faturamento total. O que encontrei:

**Existem perfis diferentes de vendedor, não um ranking linear:**

- **Darcel Schlecht** é o maior faturador disparado ($1.153.214), mas sua conversão é mediana (63,1%). Ele compensa com volume altíssimo (349 deals Won) e ticket alto ($3.304). É um vendedor de máquina — faz muito e faz bem.
- **Hayden Neloms** tem a maior conversão (70,4%), mas faturou apenas $272.111. Volume menor (107 Won), ticket bom ($2.543). É eficiente, mas opera em escala menor.
- **Versie Hillebrand** tem conversão alta (66,7%) e volume forte (176 Won), mas ticket baixo ($1.066) — resultando em faturamento modesto ($187.693). Converte muito, mas deals pequenos.
- **Donn Cantrell** tem conversão baixa (57,5%) mas ticket alto ($2.822) e faturamento robusto ($445.860). Perde mais, mas quando ganha, ganha grande.
- **Anna Snelling** tem o segundo maior volume (208 Won) mas conversão mediana (61,9%) e o ticket mais baixo entre os top por volume ($1.322), resultando em faturamento de apenas $275.056.

**O que isso significa para a ferramenta:**

O vendedor faz diferença na conversão, isso é fato. A taxa de conversão isolada varia 15 pontos (de 55% a 70,4%), o que é relevante. Porém, um vendedor com 57% de conversão pode faturar mais que um com 70% se opera em maior volume ou com ticket mais alto.

No entanto, **decidi conscientemente não usar o vendedor como fator no scoring**. A razão é de design de produto: a ferramenta é para o vendedor usar no dia a dia, não para o gestor. Se o vendedor abre a ferramenta e percebe que seus deals têm score mais baixo porque o sistema considera ele um "vendedor fraco", o efeito é o oposto do desejado — desmotivação, desconfiança e abandono da ferramenta. O score precisa ajudar o vendedor a priorizar **entre os deals dele**, não julgá-lo.

Na prática, isso significa que dois vendedores diferentes olhando para o mesmo deal veriam o mesmo score. O score reflete a qualidade do deal, não a qualidade do vendedor.

Isso não significa que a análise por vendedor foi inútil. Essa informação é valiosa para a gestão — e pode ser incluída numa visão de manager em uma evolução futura da ferramenta, onde o gestor veria o score completo com o fator vendedor para decidir onde realocar esforço do time. Mas no MVP focado no vendedor, esse fator fica de fora.

Na minha hipótese inicial, levantei que volume de atividade pode importar mais que técnica. Os dados confirmam parcialmente: Darcel Schlecht é o maior faturador pela combinação de volume + ticket, não pela conversão. Mas também mostram que conversão baixa com volume (como Anna Snelling) resulta em faturamento fraco. O ideal é o vendedor que combina as duas coisas — e poucos conseguem.

### Hipótese 7 — O valor do deal influencia a chance de fechar
**Resultado: A investigar com mais profundidade**

A distribuição de close_value vai de $38 a $30.288. A média é $2.361, mas isso é fortemente influenciada pelo produto. Preciso isolar se, dentro do mesmo produto, deals de valor mais alto convertem diferente. Fica como ponto aberto para a construção do scoring.

### Hipótese 8 — Setor + Produto (combinação)
**Resultado: Confirmada ✅ — achado forte**

Essa é uma das descobertas mais relevantes. Isoladamente, setor é fraco e produto é moderado. Mas a combinação gera variações enormes:
- Melhor: telecom + MG Special → 72,9% de conversão
- Pior: services + MG Advanced → 52,0% de conversão

São 20 pontos percentuais de diferença. Isso é maior que qualquer feature isolada exceto vendedor. A combinação setor+produto vai entrar no scoring como fator relevante.

### Hipótese 9 — Subsidiárias se comportam diferente
**Resultado: Descartada ❌**

63,1% (independente) vs 63,6% (subsidiária). Zero diferença prática. Não vou incluir isso no scoring.

### Hipótese 12 — Manager / escritório regional
**Resultado: Fraca ⚠️**

Por manager: varia de 62,1% (Rocco Neubert) a 64,4% (Cara Losch). Diferença de apenas 2,3 pontos.
Por escritório: Central 62,6%, East 63,0%, West 63,9%. Diferença de 1,3 pontos.

A variação individual do vendedor (15 pontos) é muito maior que a do manager (2,3 pontos) ou escritório (1,3 pontos). O que importa é o vendedor específico, não o time ou a região.

### Hipótese 13 — Sazonalidade
**Resultado: Confirmada ✅ — achado mais surpreendente da análise**

Esse foi o dado que mais me chamou atenção. A conversão por mês de fechamento segue um padrão trimestral muito claro:

- **Março: 82,1%** | Abril: 48,6% | Maio: 54,4%
- **Junho: 82,8%** | Julho: 49,1% | Agosto: 56,8%
- **Setembro: 79,2%** | Outubro: 49,3% | Novembro: 52,9%
- **Dezembro: 78,5%** | Janeiro/Fevereiro: sem dados

O padrão é inequívoco: meses de fechamento de trimestre (março, junho, setembro, dezembro) têm conversão em torno de 80%, enquanto o mês seguinte cai para ~49%. Isso sugere que os clientes operam com ciclos orçamentários trimestrais — e deals que estão no pipeline perto do fechamento de trimestre têm chance significativamente maior de converter.

Essa feature sozinha gera uma variação de 34 pontos percentuais. É o preditor mais forte que encontrei nos dados. E provavelmente é o tipo de insight que um prompt genérico de IA não destacaria como principal fator.

---

## 3. Ranking das Features por Impacto na Conversão

Com base na análise exploratória, esse é o ranking de impacto:

| Posição | Feature | Variação na conversão | Relevância para o Score |
|---------|---------|----------------------|------------------------|
| 1 | Sazonalidade (mês/trimestre) | ~34 pontos | Alta — preditor mais forte |
| 2 | Setor + Produto (combinação) | ~20 pontos | Alta — combinação poderosa |
| 3 | Produto (isolado) | ~5 pontos conversão | Média — mais relevante para valor do deal |
| 4 | Stage (Prospecting vs Engaging) | Qualitativo | Média — diferencia estágio da jornada |
| 5 | Setor (isolado) | ~3,6 pontos | Baixa isoladamente |
| 6 | Tamanho da empresa | ~3 pontos | Baixa — quase irrelevante |
| 7 | Subsidiária | ~0,5 pontos | Descartada |

**Nota:** O vendedor apresenta ~15 pontos de variação na conversão, mas foi excluído do scoring por decisão de design de produto (ver hipótese 6). A ferramenta é para o vendedor, não sobre o vendedor.

---

## 4. Insights que vou levar para o Scoring

1. **Sazonalidade trimestral é o fator dominante.** Deals próximos ao fechamento de trimestre devem receber boost no score.
2. **A combinação setor+produto importa mais que cada um isolado.** O scoring deve usar a taxa de conversão histórica da combinação, não de cada feature separada.
3. **Tempo no pipeline não é linearmente negativo.** Deals Won levam mais tempo que Lost. Preciso de uma abordagem mais inteligente que "mais tempo = pior".
4. **Tamanho da empresa e subsidiárias não importam.** Não vou gastar complexidade do modelo com isso.
5. **O score precisa balancear probabilidade e valor.** MG Special converte bem mas vale $55. GTK 500 converte parecido mas vale $26.707. O scoring precisa refletir essa diferença.
6. **O vendedor não entra no score — por decisão de design, não por falta de impacto.** A análise mostrou 15 pontos de variação, mas incluir esse fator prejudicaria a adoção da ferramenta pelo próprio vendedor. Essa informação fica reservada para uma futura visão de gestor.

---

## 5. Limitações desta análise

- Não investiguei a velocidade de transição entre stages (Prospecting → Engaging) por falta de dados de transição no pipeline
- A sazonalidade pode ser artefato do período dos dados — precisaria de mais anos para confirmar
- Não há dados de lead source, o que considero essencial em um cenário real (conforme hipóteses iniciais)
- A análise de valor do deal vs conversão (hipótese 7) ficou incompleta e precisa de aprofundamento

---

*Próximo passo: usar esses achados para definir a lógica e os pesos do scoring na Etapa 3.*
