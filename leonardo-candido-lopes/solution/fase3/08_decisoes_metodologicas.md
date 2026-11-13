# 08 — Registro de Decisões Metodológicas

**Desafio 002 · Fase 3** · Autor: Leonardo Candido Lopes · 08/11/2026
As 8 decisões abaixo foram **aprovadas pelo candidato** ao fim da Fase 2 (auditoria e EDA).

## 1. As 8 decisões

| # | Decisão | Justificativa (evidência) | Impacto no trabalho | Limitações decorrentes |
|---|---|---|---|---|
| D1 | **Tratar o Dataset 1 como sintético.** A auditoria é o achado principal; nenhum KPI real de tempo ou SLA | 8 sinais convergentes: placeholder em 100% das descrições; 100% dos e-mails `example.*`; 0% de termos de suporte nas resoluções; 12/12 pares de variáveis independentes; 49,3% de resoluções antes da 1ª resposta; 96,2% das 1ªs respostas num único dia; delta compatível com a diferença de dois horários sorteados (KS p = 0,166) | O D1 é usado só pelo esquema de campos e pela contagem de assuntos fora do escopo de TI. Os tempos ficam como "ilustrativos" | Não há linha de base de TPR, TR ou SLA, e as metas desses KPIs ficam para depois do piloto. A conclusão é inferência: não temos a documentação de origem |
| D2 | **Dataset 2 como base principal** do futuro classificador de TI (8 categorias) | 47.837 textos rotulados, sem nulos e sem duplicatas exatas; menor categoria com 1.760; vocabulário distintivo em 5 de 8 categorias | Define o Pilar 1 e as categorias elegíveis ao Pilar 2 | Domínio de TI interna, não B2C (98/300 palavras em comum). Texto já pré-processado: perdemos números de PO e códigos de erro |
| D3 | **Manter as 8 categorias originais**; avaliar Miscellaneous depois dos resultados | Mudar a taxonomia antes de ver a matriz de confusão seria decidir sem evidência | Taxonomia preservada; Misc vai para fila de revisão assistida | Misc (14,8%) é coringa e Hardware × Misc tem similaridade de 0,625. Espera-se F1 menor nessas categorias. "HR Support" só tem 20,1% de termos de RH (nome enganoso) |
| D4 | **Limpeza do D2**: preservar o original; excluir do treino os 133 textos com menos de 5 palavras e os 38 grupos de quase-duplicatas conflitantes; documentar o impacto | Textos curtos sem informação ("new starter please"); grupos conflitantes mostram rótulos inconsistentes | **235 registros excluídos (0,49%)**: 133 curtos + 102 em grupos conflitantes (sem sobreposição). Restam **47.602**. Por categoria: Hardware −77, HR −50, Access −44, Misc −37, Storage −12, Purchase −6, Admin rights −7, Internal Project −2 | O ruído de rótulo fora desses grupos continua (ex.: 19,9% dos tickets com "password" em Hardware). O critério de quase-duplicata (15 primeiras palavras) é heurístico |
| D5 | **Pesos por categoria; métrica principal F1-macro**; divisão treino/teste por grupo de quase-duplicatas | Desbalanceamento de 7,74×; acurácia premiaria acertar só Hardware e HR (51% juntos). 646 registros em grupos de quase-duplicatas vazariam entre treino e teste | Avaliação justa para as categorias pequenas (Admin rights 3,7%, Internal Project 4,4%) | F1-macro tende a ficar abaixo da acurácia; é preciso explicar isso aos gestores. Pesos podem aumentar falsos positivos nas categorias pequenas |
| D6 | **Fila Financeiro/Comercial separada** (reembolso, pagamento, entrega, cancelamento, recomendação), fora das 8 categorias de TI; o sistema reconhece quando o ticket está fora do escopo | 2.667 tickets (31,5%) do D1 sem categoria correspondente; a categoria "Purchase" do D2 é compra interna (PO) | Detector de domínio antes do classificador; tratamento HUMANO ou ASSISTIDO na matriz | O volume real da fila é desconhecido (os 31,5% vêm de dado sintético). Não há dados de treino para os subtipos B2C |
| D7 | **ROI com benchmarks públicos + premissas editáveis + 3 cenários**; separar horas recuperadas de economia financeira | Nenhum dataset tem custo, volume mensal ou tempo de atendimento | `06_roi_model.md`. Resultado honesto: no cenário base, a capacidade é de ≈150 h/mês, mas o caixa fica em −R$ 1.951/mês; ponto de equilíbrio em ≈ 8.200 chamados/mês | Várias premissas são hipóteses do autor (volume, tempo de triagem, custos de ferramenta, implementação e manutenção, retrabalho) e precisam ser substituídas por dados reais |
| D8 | **Redesign em 3 pilares**: Triagem Inteligente + Autoatendimento + Instrumentação de SLA | Respondem aos gargalos G1 (sem tempo), G2 (classificação incoerente), G5 (ambiguidade) e G6 (B2C sem fila) | Estrutura dos documentos 02 a 07 | A priorização fica por regras (não há rótulo de prioridade confiável). O autoatendimento é limitado a 11–26% do volume |

## 2. Ferramentas usadas

| Ferramenta | Uso |
|---|---|
| Python 3.11 + pandas | Leitura, perfil, agregações |
| módulo `csv` do Python | Auditoria de parsing (registros vs linhas físicas: 8.469 vs ~29.808) |
| SciPy | Qui-quadrado (aderência e independência), Cramér's V, Kruskal-Wallis, Spearman, Kolmogorov-Smirnov |
| NumPy | Teste de permutação (2.000 iterações) para o "top 10 piores combinações" (p = 0,154 → ruído) |
| scikit-learn (só a lista de stopwords) | Remoção de boilerplate (356 termos: stopwords + saudações, dias e meses) |
| Plotly | Gráficos interativos (`analysis/charts/`, `fase3/charts/`) |
| Busca web | Benchmarks de ROI: Gartner 2024, HDI, MetricNet, BLS 2024, salario.com.br 2026 |
| Assistente de IA (orquestrado pelo candidato) | Execução dos scripts, revisão metodológica, redação. As decisões D1 a D8 foram do candidato |

Scripts reproduzíveis:
- `analysis/explore_data.py`, `eda_d1.py`, `eda_d2.py`, `eda_d2_clean.py`
- `fase3/roi_calc.py`, `roi_md.py`

## 3. Escolhas de métricas

- **Mediana e percentis** em vez de média para tempos e comprimentos (caudas longas). A média só aparece em satisfação por grupo, porque a mediana é 3 em todos os grupos.
- **Cramér's V** junto com o p-valor: com n grande, o p-valor sozinho detecta diferenças irrelevantes.
- **Similaridade de cosseno e Jaccard top-200** entre categorias, calculadas **depois** de remover o boilerplate. Antes da limpeza, a similaridade ia de 0,37 a 0,89, inflada por saudações; depois, de 0,10 a 0,63.
- **F1-macro** como métrica principal do futuro modelo (D5).
- **No ROI:** capacidade (h) ≠ valor potencial (R$) ≠ economia realizada (R$).

## 4. O que ficou de fora e por quê

| Item | Motivo |
|---|---|
| Treino de modelo e protótipo | Fora do escopo desta fase, por instrução explícita |
| KPIs reais de tempo e SLA, "top 10 gargalos" | O D1 não tem `created_at` e tem timestamps incoerentes. O ranking não supera o acaso (permutação p = 0,154) |
| Priorização por aprendizado de máquina | A prioridade do D1 é aleatória (V ≤ 0,04 com todas as variáveis) |
| Classificação fina dos tickets B2C | Não há dados rotulados de B2C confiáveis |
| Join entre D1 e D2 | Nenhuma chave em comum |
| Custos evitados (multas de SLA, churn) no ROI | Não há dados |
| Revisão manual completa dos rótulos do D2 | Inviável nesta fase; substituída por sondagens por palavra-chave e pela análise de quase-duplicatas |

## 5. Contexto profissional (externo aos dados)

O candidato tem experiência como Analista Técnico de Atendimento (Salesforce, chargeback, prevenção a fraudes). Ele redesenhou o "Link de Análise Especial", que passou de 2–5 dias para tempo real e consolidou 4 processos em 1. Essa experiência influenciou duas escolhas: a ordem "instrumentar → triar → automatizar" e a decisão de manter reembolso e pagamento sob decisão humana. **Ela não é usada como evidência de nenhum número deste trabalho.**
