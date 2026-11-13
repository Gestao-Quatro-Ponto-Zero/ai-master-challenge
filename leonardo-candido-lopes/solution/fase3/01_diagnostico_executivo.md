# 01 — Diagnóstico Executivo · Redesign de Suporte com IA

**Desafio 002 — G4 AI Master Challenge · Fase 3** · Autor: Leonardo Candido Lopes · 08/11/2026
**Público:** COO, para decidir se investe na transformação do suporte.
**Base:** auditoria e EDA (`analysis/eda_report.md`) e resultados em `analysis/eda_d1_results.json`, `eda_d2_results.json` e `eda_d2_clean_results.json`. Nenhum modelo foi treinado nesta fase.

> **Legenda de natureza da afirmação** (usada em todo o documento)
> - **[EVIDÊNCIA]** = medido diretamente nos dados
> - **[INTERPRETAÇÃO]** = leitura dos números, sem ir além deles
> - **[HIPÓTESE]** = explicação ou comportamento operacional plausível, ainda não comprovado
> - **[PROJEÇÃO]** = estimativa de melhoria futura, dependente de premissas

---

## 1. Executive Summary

**Problema.** A operação de suporte precisa reduzir esforço manual, rotear melhor e cumprir SLA. Hoje, porém, ela não consegue nem medir o próprio tempo de atendimento com os dados disponíveis.

**Dados.** Recebemos dois datasets:
- **Dataset 1 (D1):** 8.469 tickets de suporte B2C de eletrônicos, 17 campos.
- **Dataset 2 (D2):** 47.837 tickets de TI interna, classificados em 8 categorias.

Não existe chave que ligue os dois.

**Principais achados.**
1. **[EVIDÊNCIA] O D1 não serve para medir a operação.** Ele não tem data/hora de abertura do ticket. Em **49,3% dos tickets fechados (1.365 de 2.769)** a "resolução" acontece *antes* da primeira resposta. Todas as variáveis são uniformes e independentes entre si. 100% das descrições contêm o texto-modelo `{product_purchased}` não preenchido. **[INTERPRETAÇÃO]** Há oito sinais convergentes de que o dataset é sintético. Por isso, **não reportamos tempo de resposta, tempo de resolução nem SLA reais**. A auditoria em si é o achado.
2. **[EVIDÊNCIA] O D2 é uma base sólida para triagem automática.** São 47.837 textos rotulados, sem nulos nem duplicatas exatas. A menor categoria tem 1.760 exemplos. Cinco das oito categorias têm vocabulário muito distintivo: "po" aparece em 70,6% dos tickets de Purchase e em só 0,6% dos demais.
3. **[EVIDÊNCIA] As categorias são desbalanceadas:** Hardware tem 28,5% e Administrative rights 3,7%, uma razão de **7,7×**. Hardware e Miscellaneous são as mais ambíguas entre si.
4. **[EVIDÊNCIA] 31,5% dos tickets do D1 (2.667)** tratam de reembolso, pagamento, entrega, cancelamento ou recomendação. Nenhuma das 8 categorias de TI cobre esses temas. Eles exigem uma **fila Financeiro/Comercial separada**.

**Proposta.** Redesign em **3 pilares**:
1. **Triagem Inteligente:** classificação nas 8 categorias de TI + fila Financeiro/Comercial, com controle de confiança e roteamento.
2. **Autoatendimento:** focado nas categorias mais padronizadas (Purchase, Storage e parte de Access).
3. **Instrumentação de SLA:** registrar abertura, primeira resposta e resolução, que é pré-requisito para gerir qualquer meta.

O humano continua dono da fila Financeiro/Comercial, dos casos de baixa confiança, dos críticos e do escalonamento para o nível 2 (N2).

**Retorno.** **[PROJEÇÃO]** No cenário base (5.000 chamados/mês, premissas públicas e editáveis), o redesign libera **≈150 h/mês (≈1 FTE)**. Mas a economia de caixa **não cobre** o custo recorrente, a menos que o volume chegue a ≈8.200 chamados/mês ou que a empresa converta mais horas em economia. **Recomendação:** aprovar um **piloto de 90 dias** com instrumentação primeiro, e decidir a escala com números medidos, não com benchmark (ver `06_roi_model.md`).

---

## 2. Contexto e limitações dos dados

### 2.1 Dataset 1: evidências de artificialidade

| # | Sinal | Valor medido | n |
|---|---|---:|---:|
| 1 | Descrições com o texto-modelo `{product_purchased}` não preenchido | 100% | 8.469 |
| 2 | E-mails em domínios reservados (`example.com/.org/.net`) | 100% | 8.469 |
| 3 | Resoluções com algum termo de suporte (reset, replace, refund…) | 0,0% | 2.769 |
| 4 | Variáveis com distribuição uniforme (teste de aderência, p > 0,05) | 7 de 9 testadas | 8.469 |
| 5 | Pares de variáveis independentes (Cramér's V ≤ 0,07) | 12 de 12 | 2.769–8.469 |
| 6 | Assunto "Refund request" com tipo diferente de "Refund request" | 79,3% | 576 |
| 7 | Primeiras respostas concentradas em um único dia (01/06/2023) | 96,2% | 5.650 |
| 8 | Resolução registrada antes da primeira resposta | 49,3% | 2.769 |

Outros detalhes medidos:
- Há 92 tickets de software (Office, Photoshop, AutoCAD) com assunto de bateria, hardware ou tela, entre 577 tickets de software.
- A satisfação é plana: 553, 549, 580, 543 e 544 respostas para as notas 1 a 5.
- A satisfação não se relaciona com o tempo (Spearman ρ = 0,003; p = 0,92).

**[INTERPRETAÇÃO]** Nenhum sinal isolado prova que o dataset é sintético. Os oito juntos, todos na mesma direção, tornam essa a explicação mais provável. Uma ressalva: não temos a documentação de origem do dataset.

**O que ainda dá para aproveitar do D1:**
- **O esquema de campos** (canal, prioridade, tipo, status, satisfação), que ajuda a desenhar a instrumentação futura.
- **Os textos**, como teste de mudança de domínio para o classificador. Mas não há gabarito para medir acerto.
- **A contagem de assuntos fora do escopo de TI**, que dimensiona a fila Financeiro/Comercial.

**O que não dá:** tempo de primeira resposta, tempo de resolução, cumprimento de SLA, gargalos por canal, prioridade ou tipo, e a relação entre satisfação e tempo.

### 2.2 Dataset 2: o que está disponível

- **[EVIDÊNCIA]** São 47.837 textos com duas colunas: `Document` e `Topic_group` (8 categorias).
- Os textos já vêm pré-processados: tudo em minúsculas, sem pontuação e sem números.
- Mediana de 26 palavras por texto (P90 = 91).
- 38,1% das palavras são boilerplate de e-mail (saudações, datas, assinatura).
- **[INTERPRETAÇÃO]** Representa um **help desk de TI corporativo interno**: acessos, Confluence, Outlook, pastas, pedidos de compra, onboarding. Não é suporte ao consumidor.
- **[EVIDÊNCIA]** Só 20,1% dos tickets de "HR Support" têm termos clássicos de RH. As palavras dominantes da categoria são *access, new, starter, oracle, form*. **[HIPÓTESE]** A categoria cobre, na prática, sistemas de RH e onboarding.

### 2.3 O que ficou de fora do escopo do classificador de TI

| Assunto no D1 | Tickets |
|---|---:|
| Refund request | 576 |
| Delivery problem | 561 |
| Payment issue | 526 |
| Product recommendation | 517 |
| Cancellation request | 487 |
| **Total sem categoria correspondente no D2** | **2.667 (31,5% de 8.469)** |

- **[EVIDÊNCIA]** Também há **mudança de domínio** entre os datasets: só 98 das 300 palavras mais frequentes do D1 aparecem entre as 300 mais frequentes do D2, e 57,8% do vocabulário do D1 existe no D2.
- **[INTERPRETAÇÃO]** Um classificador treinado só no D2 **não deve** tentar classificar esses temas nas 8 categorias de TI. Ele precisa reconhecer que está fora do escopo e encaminhar.

---

## 3. Principais achados da auditoria

### 3.1 Volumes do Dataset 1 (descritivos, distribuição artificial)

| Dimensão | Distribuição observada | n |
|---|---|---:|
| Canal | Email 25,3% · Phone 25,2% · Social media 25,0% · Chat 24,5% | 8.469 |
| Tipo | Refund 20,7% · Technical 20,6% · Cancellation 20,0% · Product inquiry 19,4% · Billing 19,3% | 8.469 |
| Prioridade | Medium 25,9% · Critical 25,1% · High 24,6% · Low 24,4% | 8.469 |
| Status | Pending Customer Response 34,0% · Open 33,3% · Closed 32,7% | 8.469 |
| Satisfação (1 a 5) | 19,6% a 20,9% em cada nota; mediana 3 | 2.769 |

**[INTERPRETAÇÃO]** Numa operação real, seria esperado um canal dominante, "Critical" como minoria e satisfação concentrada nas notas 4–5. A uniformidade reforça o diagnóstico de dado sintético.

### 3.2 As 8 categorias do Dataset 2

| Categoria | Tickets | % | Mediana de palavras |
|---|---:|---:|---:|
| Hardware | 13.617 | 28,5% | 32 |
| HR Support | 10.915 | 22,8% | 24 |
| Access | 7.125 | 14,9% | 22 |
| Miscellaneous | 7.060 | 14,8% | 27 |
| Storage | 2.777 | 5,8% | 21 |
| Purchase | 2.464 | 5,2% | 30 |
| Internal Project | 2.119 | 4,4% | 24 |
| Administrative rights | 1.760 | 3,7% | 30 |
| **Total** | **47.837** | **100%** | **26** |

**[EVIDÊNCIA] Desbalanceamento:** a maior categoria (Hardware, 13.617) tem **7,74×** o volume da menor (Administrative rights, 1.760). As 4 maiores somam 81%.

### 3.3 Problemas de qualidade no D2

| Problema | Medida | Tratamento aprovado |
|---|---:|---|
| Textos com menos de 5 palavras | 133 (0,28%) | Excluídos do treino |
| Grupos de quase-duplicatas (mesmas 15 primeiras palavras) | 365 grupos, 646 registros | Separar treino e teste por grupo, para evitar vazamento |
| …desses grupos, com categorias conflitantes | 38 grupos (102 registros) | Excluídos do treino |
| **Total excluído do treino** (sobreposição considerada) | **235 (0,49%)**, restam 47.602 | O arquivo original é preservado |
| Palavras de boilerplate de e-mail | 38,1% das palavras | Remover antes de vetorizar o texto |
| Tickets com "password" classificados como Hardware | 19,9% de 1.646 | **[HIPÓTESE]** Ruído ou critério de rotulagem diferente; investigar na matriz de confusão |

### 3.4 Separação entre categorias (após remover boilerplate)

- **[EVIDÊNCIA]** Purchase é a categoria mais separada das demais (similaridade de vocabulário ≤ 0,24 com todas as outras).
- Os pares mais parecidos são Hardware × Miscellaneous (0,625), Hardware × Access (0,560) e Hardware × HR Support (0,530).
- **[INTERPRETAÇÃO]** Os erros de classificação devem se concentrar em volta de Hardware e Miscellaneous. Miscellaneous funciona como categoria-coringa.

---

## 4. Gargalos operacionais

| # | Gargalo | Evidência observada | Interpretação | Hipótese operacional |
|---|---|---|---|---|
| G1 | **Sem medição de tempo** | O D1 não tem data/hora de abertura; 49,3% das resoluções vêm antes da 1ª resposta | Os dados atuais não permitem medir SLA | Sem esse registro, qualquer meta de SLA é declaratória. É o gargalo nº 1 de governança |
| G2 | **Classificação manual incoerente** | Tipo × Assunto no D1 sem relação (V = 0,034); 79,3% dos "Refund" com tipo diferente | A categoria registrada não descreve o problema | Numa operação real, isso causaria roteamento errado e transferências entre filas |
| G3 | **Prioridade não muda o atendimento** | Mediana de 5,98h nos Critical vs 7,08h nos Low (só delta ≥ 0; teste p = 0,09); Critical = 25,1% do volume | **Ilustrativo** (o dado é sintético), mas mostra o padrão a evitar | Excesso de "Critical" e prioridade que não altera a fila |
| G4 | **Backlog e tickets parados** | 67,3% não fechados; 34,0% em "Pending Customer Response" | Distribuição sintética; não serve como dimensão real | Faltam follow-up automático e regras de fechamento por inatividade |
| G5 | **Categorias ambíguas no corpus de TI** | Hardware × Misc com similaridade de 0,625; Misc com 14,8% do volume | Parte da triagem vai ser inevitavelmente incerta | Exige limiar de confiança e revisão humana, e não 100% de automação |
| G6 | **Demanda B2C sem fila adequada** | 31,5% do D1 sem categoria de TI correspondente | O classificador de TI não cobre esses casos | Mandar esses casos para filas de TI gera retrabalho e risco financeiro (reembolso, chargeback) |

---

## 5. Oportunidades de melhoria com suporte nos dados

| Oportunidade | Suporte nos dados | Força |
|---|---|---|
| Triagem automática nas 8 categorias de TI | 47.837 exemplos; ≥ 1.760 por categoria; 5 categorias com vocabulário distintivo | Alta (para TI interna) |
| Autoatendimento em Purchase | "po" em 70,6%, "purchased" em 65,3%, "receipts" em 47,3% da categoria; textos padronizados | Alta |
| Autoatendimento em Storage (pastas, cota de mailbox) | "folder" em 28,8%, "accept" em 27,2%, "decline" em 25,7% | Alta |
| Reset de senha e liberação de acesso | 70,8% dos 1.646 tickets com "password" em Access; "reset" em 10,3% de Access; "confluence" em 19,6% | Média-alta |
| Fila Financeiro/Comercial dedicada | 2.667 tickets (31,5% do D1) fora do escopo de TI | Alta como necessidade; volume real a medir |
| Registro de abertura, 1ª resposta e resolução | Ausência total no D1 | Pré-requisito |

---

## 6. Impactos potenciais

Todos os impactos abaixo são **[PROJEÇÃO]** e dependem de piloto.

- **Capacidade:** ≈ 30 / 150 / 561 h/mês nos cenários conservador, base e otimista, equivalentes a 0,21 / 1,03 / 3,84 FTE (`06_roi_model.md`).
- **Caixa:** −R$ 6.788 / −R$ 1.951 / +R$ 16.837 por mês. O caso financeiro depende de escala e da taxa de realização.
- **Qualidade (não financeiro):**
  - roteamento consistente;
  - SLA mensurável pela primeira vez;
  - menos tickets parados;
  - trilha de auditoria de cada decisão automática.
- **Risco:** erros de classificação nas categorias ambíguas e uso fora do domínio de treino (B2C). Mitigações em `07_riscos.md`.

> *Contexto profissional externo (não é evidência dos datasets):* o autor já conduziu um redesign de processo, o "Link de Análise Especial", que passou de 2–5 dias para tempo real ao consolidar 4 processos em 1. A lição aplicada aqui é instrumentar e simplificar o fluxo antes de automatizar.
