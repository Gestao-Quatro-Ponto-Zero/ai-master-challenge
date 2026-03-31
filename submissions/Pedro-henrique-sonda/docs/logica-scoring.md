# Lógica de Scoring — Definição Final da Fórmula

**Autor:** Pedro Henrique Sonda
**Data:** 30/03/2026
**Versão:** v6 (final)

---

## 1. Como cheguei até aqui

Este documento registra a lógica final do scoring e o caminho iterativo que percorri para chegar nela. Foram 6 versões da fórmula, cada uma corrigindo problemas identificados na anterior. O processo completo está documentado nos arquivos CONTEXT1 a CONTEXT11.

---

## 2. O que o Score mede

O score mede uma coisa só: **a probabilidade de um deal fechar**, numa escala de 0 a 100, com bônus para clientes recorrentes.

### Por que separei probabilidade e valor

Tentei várias formas de combinar probabilidade e valor num único número: média ponderada (70/30), valor esperado (probabilidade × valor), log do valor esperado. Nenhuma funcionou — ou o valor distorcia o ranking, ou os scores ficavam artificialmente próximos, ou deals de $55 apareciam acima de deals de $5.000.

A raiz do problema: probabilidade é uma estimativa de 0 a 100, valor é um número real em dólares. São naturezas diferentes que não cabem numa fórmula única sem distorção.

**Decisão final:** O score mede probabilidade. O valor aparece como dado real ($). O vendedor escolhe como ordenar seus deals (por probabilidade ou por valor). Isso dá poder ao vendedor sem forçar uma lógica artificial.

---

## 3. A Fórmula

### Score de Probabilidade (0-100)

```
Score = (Setor+Produto × 0.35) + (Histórico Conta × 0.30) + (Sazonalidade × 0.20) + (Tempo × 0.15)
```

### Boost de Recorrência (aditivo)

```
Se a conta já comprou o mesmo produto:
  0 vezes  → +0 pontos (neutro)
  1-3 vezes → +5 pontos
  4-10 vezes → +10 pontos
  11+ vezes → +15 pontos
```

### Score Final

```
Se boost = 0:
    Score Final = Score de Probabilidade (sem alteração)

Se boost > 0:
    Score Bruto = Probabilidade + Boost
    Score Normalizado = (Score Bruto / 115) × 100
    Score Final = max(Probabilidade, Score Normalizado)
```

O max() garante que o boost NUNCA reduz o score abaixo da probabilidade base. Isso foi uma correção feita após identificar que a normalização por 115 penalizava deals com boost baixo.

---

## 4. Os 4 Fatores — Detalhamento

### Fator 1 — Combinação Setor + Produto (peso 35%)

**Por que esse peso:** A combinação gera variações de 52% a 73% na conversão — 20 pontos de diferença. É o segundo maior preditor nos dados. Testei setor e produto isoladamente: setor varia apenas 3,6 pontos e produto 5 pontos. Mas a combinação captura a interação entre eles que os fatores isolados perdem.

**Cálculo:**
```
taxa_combo = won / (won + lost)  por combinação setor+produto
fator = ((taxa_combo - 0.52) / (0.73 - 0.52)) × 100
fator = clamp entre 0 e 100
Fallback: combos com menos de 30 deals usam taxa média geral (63.2%)
```

**Exemplos reais:**
- telecom + MG Special: 72.9% → ~100 pontos (forte)
- services + MG Advanced: 52.0% → ~0 pontos (fraca)
- retail + GTX Basic: 69.9% → ~85 pontos (forte)

### Fator 2 — Histórico da Conta (peso 30%)

**Por que esse peso:** A taxa de conversão por conta varia de 53.1% a 75.0% — 21.9 pontos de diferença. Todas as 85 contas têm 10+ deals, então os dados são robustos. Este fator foi adicionado na v2 para resolver o problema de scores empatados — individualiza cada deal pela qualidade da conta.

**Cálculo:**
```
taxa_conta = won / (won + lost)  por conta
fator = ((taxa_conta - 0.531) / (0.750 - 0.531)) × 100
fator = clamp entre 0 e 100
Fallback: contas com menos de 5 deals usam taxa média geral (63.2%)
```

**Exemplos reais:**
- Rangreen: 75.0% → 100 pontos (melhor conta)
- Condax: 66.0% → 59 pontos (média)
- Statholdings: 53.1% → 0 pontos (pior conta)

### Fator 3 — Sazonalidade Trimestral (peso 20%)

**Por que esse peso:** Meses de fechamento de trimestre convertem ~80% vs ~49% nos outros — 34 pontos de diferença, o maior preditor em teoria. Porém, como é igual para todos os deals no mesmo momento, diferencia menos na prática. Por isso o peso é 20% e não maior.

**Análise de universalidade:** Testei se o padrão varia por setor ou produto. Resultado: TODOS os 10 setores e TODOS os 7 produtos seguem o mesmo padrão, sem exceção. Não há subgrupo que precise de tratamento diferenciado.

**Cálculo:** Usa o mês da data de referência (não datetime.now(), pois os dados são de 2016-2017):
```
data_referencia = engage_date mais recente dos deals abertos (2017-12-22)
mes = data_referencia.month (12 = dezembro)

Mês de fechamento trimestral (3, 6, 9, 12): 95 pontos
Segundo mês do trimestre (2, 5, 8, 11): 55 pontos
Primeiro mês do trimestre (1, 4, 7, 10): 35 pontos
```

### Fator 4 — Tempo no Pipeline (peso 15%)

**Por que esse peso e como cheguei nas faixas:**

Este fator passou por 3 versões antes da calibração final:

**v1 (intuição):** Penalizava deals antigos (90+ dias = score baixo). Descartada — dados mostraram o contrário.

**v2 (dados brutos):** Dava boost para deals antigos (71.3% de conversão em 90+ dias). Quase aceitei, mas questionei: existe viés de sobrevivência — os deals que chegam a 90+ dias já foram pré-filtrados naturalmente.

**v3 (quase neutra):** Tornei praticamente neutro, variação de 45 a 55 pontos.

**v6 (final, calibrada com dados reais):** Descobri um insight crítico analisando o cicle time:
- Cicle time médio Won: 52 dias
- 75% dos Won fecham em até 88 dias
- NENHUM deal na história fechou após 138 dias
- 44% dos deals abertos estão há 180+ dias — provavelmente mortos

Faixas finais:
```
Sem engage_date (Prospecting): 50 pontos (neutro)
0-30 dias: 45 pontos (deal cru, 57.4% conversão histórica)
30-60 dias: 60 pontos (amadurecendo, 65.6%)
60-90 dias: 65 pontos (zona forte, 66.4%)
90-120 dias: 60 pontos (viável mas se aproximando do limite)
120-140 dias: 45 pontos (limite — último Won histórico foi em 138 dias)
140+ dias: 20 pontos (NENHUM deal fechou após 138 dias)
```

---

## 5. Boost de Recorrência

**O que descobri:** 31.5% dos deals abertos são de combinações conta+produto que já tiveram Won antes. Exemplos: Condax comprou MG Special 30 vezes, Hottechi comprou GTX Basic 37 vezes, Stanredtax comprou MG Special 18 vezes com 100% de conversão.

**Regra:** A recorrência NÃO penaliza — apenas bonifica. Quem não tem recorrência fica neutro. Quem tem, ganha boost proporcional ao número de compras anteriores do mesmo produto pela mesma conta.

**Normalização condicional:** O boost pode adicionar até 15 pontos sobre os 100 da probabilidade (total máximo 115). Para manter a escala 0-100, normalizo dividindo por 115 × 100. Mas SOMENTE se o deal tem boost. Se não tem, o score é a probabilidade direta. E o max() garante que o boost nunca reduz o score.

---

## 6. O que NÃO entra no score e por quê

### Vendedor (excluído por design de produto)
A taxa de conversão por vendedor varia 15 pontos (55% a 70.4%). Analisei por 4 dimensões: conversão, ticket médio, volume, faturamento. Existem perfis diferentes, não um ranking linear. Mas excluí do score porque a ferramenta é para o vendedor usar — se ele visse que seus deals têm score mais baixo por ser "vendedor fraco", a ferramenta perderia adoção. Fica como evolução futura para visão de gestor.

### Stage (excluído por decisão conceitual)
O score mede POTENCIAL, não progresso. Um deal em Prospecting com conta forte e produto com alta conversão tem o mesmo potencial que o mesmo deal em Engaging. A diferença é que o Prospecting precisa de primeiro contato — o que é mais urgente, não menos valioso. Stage aparece como badge visual.

### Valor do deal (exibido separadamente)
Testei múltiplas formas de incluir valor no score. Todas geraram distorção. Valor aparece como dado real ($) e o vendedor escolhe a ordenação. O filtro de faixa de valor permite focar em deals do tamanho desejado.

### Tamanho da empresa, subsidiárias, localização, ano de fundação
Variações de 0.7 a 5 pontos percentuais. Irrelevantes estatisticamente.

---

## 7. Data de Referência

Os dados são de 2016-2017. Toda a aplicação usa a engage_date mais recente dos deals abertos como "hoje" (2017-12-22). Isso afeta o cálculo de dias no pipeline e o mês da sazonalidade (dezembro = fechamento trimestral).

---

## 8. Decisões de Design Registradas

| Decisão | Justificativa | Iteração |
|---------|---------------|----------|
| Score = probabilidade pura | Valor distorce quando combinado (testei 3 abordagens) | v5 |
| Vendedor fora do score | Ferramenta é para o vendedor, não sobre ele | v1 |
| Stage fora do score | Score mede potencial, não progresso | v4 |
| Boost de recorrência aditivo | Nunca penaliza, só bonifica. Normalização condicional | v6 |
| Faixas de tempo calibradas | Nenhum Won após 138 dias. Deals 140+ provavelmente mortos | v6 |
| Data de referência | Dados de 2016-2017, não usar datetime.now() | v2 |
| Fallback para amostras pequenas | Combos com menos de 30 deals e contas com menos de 5 deals usam média geral | v1 |
| Sazonalidade universal | Testei por setor e produto: todos seguem o padrão | v6 |

---

## 9. O que faria diferente com mais tempo ou dados

- **Lead source no CRM**: saber a origem do lead mudaria o score significativamente
- **Visão de gestor**: interface com fator vendedor para realocar esforço do time
- **Validação retroativa**: aplicar scoring nos deals históricos e verificar acurácia
- **Close value real**: usar o valor real de fechamento (que varia -34% a +34% da tabela) ao invés do preço de tabela
- **Modelo de ML**: com mais features, logistic regression ou gradient boosting capturariam interações não-lineares
- **Transição entre stages**: medir velocidade de progressão, não só tempo absoluto

---

*Este documento reflete a versão final (v6) da lógica de scoring, após 11 iterações de desenvolvimento.*
