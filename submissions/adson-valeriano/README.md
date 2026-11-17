# Submissão — Adson Valeriano — Challenge 002

## Sobre mim

- **Nome:** Adson Valeriano
- **LinkedIn:** [linkedin.com/in/adsonvaleriano](https://linkedin.com/in/adsonvaleriano)
- **Challenge escolhido:** 002 — Redesign de Suporte

---

## Executive Summary

Antes de buscar gargalos, conferi se os dados de suporte eram confiáveis, e eles não são: os tempos são inconsistentes (em 49% dos tickets fechados, a resolução aparece antes da primeira resposta), a satisfação é distribuída por igual de 1 a 5 e os textos vêm de 16 frases-modelo. Com esse dado, ninguém consegue afirmar onde se perde tempo ou o que move a satisfação. O achado principal é que **a operação não mede o que importa**. Usei o dataset de TI, que é real, para provar a automação: um classificador que acerta 86,6% dos tickets. Com o limiar de confiança de 70% e as regras de segurança ligadas (dinheiro, urgência, segurança e acesso privilegiado vão para humano), a IA decide sozinha **62,8%** dos tickets com **95,8%** de acerto. **Recomendação:** começar a medir os tempos de verdade e rodar um piloto de triagem treinado com os tickets da própria empresa. A economia direta estimada é de ~31 a ~79 horas/mês (≈ R$ 5.900 a R$ 14.700/ano); o ganho maior é velocidade de encaminhamento. Resumo de 1 página em [`RESUMO_EXECUTIVO.md`](RESUMO_EXECUTIVO.md).

---

## Solução

### Abordagem

1. **Entender o pedido.** O diretor quer três coisas: onde se perde tempo, o que automatizar (e o que não) e algo rodando. Escrevi meu raciocínio e minhas hipóteses em [`docs/00-raciocinio.md`](docs/00-raciocinio.md), a partir do que vejo no suporte da Skill-Hub.
2. **Desconfiar do dado antes de analisar.** Fiz a checagem de qualidade antes de qualquer gráfico. Isso mudou a direção do trabalho inteiro.
3. **Separar o que dá para concluir do que não dá.** Testei cada pergunta do diretor com estatística simples (ANOVA, correlação) para não confundir ruído com insight.
4. **Procurar pegadinhas.** O desafio sugere que "o poder está no cruzamento" dos datasets. Testei isso de verdade antes de assumir.
5. **Construir o que dá para provar.** Classificador com limiar de confiança, regras de passagem para humano e busca de tickets parecidos, num protótipo que roda.

### Resultados / Findings

#### 1. Onde estamos perdendo tempo? (Dataset 1, suporte)
Números completos em [`solution/resultados_diagnostico.md`](solution/resultados_diagnostico.md).

| O que testei | O que encontrei |
|---|---|
| Qualidade dos tempos | "First Response Time" e "Time to Resolution" são data/hora, não duração. Todas as primeiras respostas cabem em 27 horas. Em **49,3%** dos tickets fechados, a resolução vem antes da primeira resposta. |
| Cobertura das métricas | Só os tickets fechados (**33%**) têm tempo e satisfação. Os outros 67% não têm nada. |
| Satisfação | Distribuição praticamente igual de 1 a 5 (~550 cada). Média ~3 em tudo. |
| Canal, tipo e prioridade x status | Tudo ~33% fechado, ~33% aberto, ~33% aguardando cliente. Nenhum gargalo se destaca. |
| O que mexe na satisfação | Nada: ANOVA por canal p = 0,28, por tipo p = 0,70, por prioridade p = 0,63. Correlação com o tempo = 0,02. |
| Origem do dado | 100% das descrições têm `{product_purchased}` sem preencher; 16 frases de abertura; e-mails `example.com/.org/.net`. Sinais fortes de dado sintético. |

**Leitura:** se eu dissesse "o chat tem a melhor satisfação (3,08)", estaria vendendo ruído como insight: 3,08 contra 2,95 é diferença de sorteio. O que o dado mostra de verdade:
- **A empresa não mede de forma confiável o tempo nem a satisfação.** Antes de otimizar, precisa medir.
- **Um terço dos tickets (2.881, 34%) está parado aguardando o cliente.** É o único sinal operacional aproveitável e aponta para follow-up automático.

**Quanto estamos desperdiçando?** Com esses dados não dá para calcular o desperdício real em horas, porque o tempo registrado não é confiável. A estimativa abaixo usa premissas explícitas e deve ser validada no piloto.

#### 2. O que dá para automatizar (Dataset 2, TI, 47.837 tickets reais)
Números completos em [`solution/resultados_avaliacao.md`](solution/resultados_avaliacao.md).

Classificador TF-IDF + regressão logística, testado em **9.568 tickets que ele nunca viu** (20% separados).
- **Acurácia: 86,6%** (chutar sempre a categoria mais comum acerta 28,5%).

O ponto principal é usar a confiança do modelo para decidir quando a IA age sozinha:

| Confiança mínima | IA decide sozinha | Acerto nesses tickets |
|---|---|---|
| 50% | 88,4% | 91,2% |
| 60% | 80,0% | 93,8% |
| **70% (escolhido)** | **71,7%** | **95,6%** |
| 80% | 62,4% | 97,3% |
| 90% | 50,5% | 98,7% |

Escolhi **70%** porque equilibra volume automatizado e erro (4,4%). É uma decisão de negócio: se errar custar caro, sobe o limiar.

**Com as regras de segurança ligadas** (dinheiro, urgência, segurança e categoria sensível vão para humano), a IA decide sozinha **62,8%** dos tickets de teste, com **95,8%** de acerto. É esse o número que vale para a operação.

**Checagens de robustez** ([`solution/resultados_checagens.md`](solution/resultados_checagens.md)):
- *O acerto está inflado por chamados repetidos?* Só 6% dos chamados de teste têm um "gêmeo" no treino; sem eles, o acerto continua 86,0%.
- *O modelo cola pela assinatura/cargo no fim do texto?* Usando só as 3 últimas palavras, acerta 39,9%; sem elas, 86,1%. Ele aprende pelo problema descrito.
- *As regras de passagem para humano funcionam?* No dataset de TI, sim: tiram 9 pontos de automação (de 71,7% para 62,8%) e mantêm o acerto em 95,8%. No dataset de suporte, a regra de dinheiro por palavra-chave pega só 7,4% dos chamados de reembolso/cobrança/cancelamento, a mesma taxa dos outros tipos, porque ali o texto não tem relação com o tipo (dado sintético). Conclusão para produção: a regra de dinheiro deve usar o **campo estruturado** do chamado (o tipo que o cliente escolhe), com as palavras-chave só como reforço.

**Por categoria:** a pior é **Administrative rights** (precisão 77%), justamente a mais sensível, porque mexe com acesso e permissão. As maiores confusões são Hardware ↔ HR Support e Hardware ↔ Miscellaneous ("Miscellaneous" funciona como categoria-lixeira).

#### 3. A pegadinha do cruzamento
Os dois datasets são de mundos diferentes: o 1 é **suporte ao cliente** (cobrança, reembolso, produto) e o 2 é **service desk interno de TI** (hardware, RH, acesso). Testei aplicar o modelo do dataset 2 nos tickets do dataset 1:
- a confiança média cai de 81% para **55%**;
- só **18,6%** passam do limiar de 70%;
- **74%** viram "Hardware", inclusive pedidos de reembolso e cobrança.

**Conclusão:** o modelo não transfere. A técnica está provada, mas para o suporte da empresa ela precisa ser treinada com os tickets da própria operação, rotulados com as categorias de negócio dela. Por isso o ROI abaixo é estimativa, não promessa.

#### 4. Protótipo funcionando
Triagem inteligente em Streamlit ([como rodar](solution/COMO_RODAR.md)):

**Ticket entra → IA classifica e dá a confiança → regras decidem se vai para humano → mostra tickets parecidos já classificados → encaminha.**

Vai **sempre para humano** quando:
| Regra | Por quê |
|---|---|
| Prioridade crítica | Não pode esperar fila nem arriscar erro |
| Dinheiro ou retenção (reembolso, cobrança, cancelamento) | Envolve decisão financeira e risco de perder o cliente |
| Segurança (vazamento, fraude, invasão) | Risco alto, exige julgamento |
| Categoria Administrative rights | Pior precisão do modelo e tema de segurança |
| Confiança abaixo de 70% | A IA não tem certeza; um humano decide |

O protótipo tem três telas: **testar um ticket** (mostra a decisão e o motivo), **testar com 200 chamados** (prova em volume, com os erros barrados) e **enviar uma planilha** (um gestor sobe um CSV com os próprios chamados e baixa a planilha triada; exemplo em `solution/exemplo_planilha.csv`). Em produção, a triagem seria ligada ao sistema de chamados por webhook, sem planilha.

Os tickets parecidos dão contexto ao atendente e ajudam a conferir a sugestão da IA. É a parte de recuperação de um RAG; o próximo passo é gerar uma resposta sugerida com base em resoluções reais da empresa (as resoluções do dataset 1 são frases sem sentido e não serviram para isso).

Prints em [`process-log/screenshots/`](process-log/screenshots/).

### Recomendações

1. **Medir antes de otimizar (semana 1).** Registrar abertura, primeira resposta e resolução como duração, por canal e tipo, e pedir nota de satisfação em todo ticket fechado. Sem isso, qualquer decisão de contratar ou automatizar é no escuro.
2. **Follow-up automático para tickets aguardando o cliente (semana 1–2).** É um terço do volume. Lembrete automático em 24 h e 72 h, e fechamento com aviso depois de 7 dias sem resposta. É simples, de baixo risco e libera a fila.
3. **Piloto de triagem automática (semanas 2–6).** Rotular ~2.000 tickets da própria operação nas categorias de negócio, treinar o mesmo modelo e rodar em paralelo com a triagem humana por 2 semanas, comparando o acerto. Só ligar o encaminhamento automático se o acerto ficar ≥ 95% acima do limiar.
4. **ROI estimado para o piloto confirmar** (premissas: 30 mil tickets/ano, 3 min de triagem manual por ticket, cobertura efetiva de 62,8% e R$ 15,64/hora, que é o custo empresa de um operador de suporte técnico, R$ 3.440/mês ÷ 220 h, segundo o Portal Salário 2026):
   - **Conservador, ~377 h/ano (~31 h/mês) ≈ R$ 5.900/ano:** a IA só tria o que não envolve dinheiro. Pelas minhas próprias regras, reembolso, cancelamento e cobrança vão para humano, e no dataset de suporte esses tipos são 60% do volume.
   - **Ampliado, ~943 h/ano (~79 h/mês) ≈ R$ 14.700/ano:** a IA também *encaminha* os chamados de dinheiro para a fila do financeiro, mas quem *decide* reembolso e cancelamento continua sendo uma pessoa. Encaminhar não é decidir: o risco fica com o humano e o tempo de triagem sai da fila.
   - **Leitura honesta:** a economia direta de triagem é modesta. O valor principal da automação é velocidade (o chamado chega na fila certa na hora) e menos chamados caindo na pessoa errada. Esses ganhos só dá para medir depois de a empresa começar a registrar os tempos (recomendação 1).
5. **Metas do piloto** (hipóteses a validar): chamado na fila certa em menos de 1 minuto em ~60% dos casos; reencaminhamentos pela metade; chamados parados esperando o cliente de 34% para abaixo de 20%; linha de base de tempo de resolução e satisfação nas 2 primeiras semanas.
6. **Revisar a categoria "Miscellaneous"**, que concentra confusão e esconde demanda que poderia ter dono.

### Limitações

- O dataset de suporte tem sinais fortes de ser sintético, então não serve para medir gargalos nem satisfação reais.
- O ROI depende de duas premissas não verificadas: 3 min de triagem manual e desempenho parecido quando treinado com os tickets da empresa.
- O dataset de TI está em inglês e pré-processado (sem números, pontuação nem acento). Num suporte brasileiro real, o modelo precisa ser treinado em português.
- A proporção de chamados que envolvem dinheiro (60%), usada no ROI, vem do dataset de suporte, que parece sintético. O mix real da operação muda a estimativa.
- A regra de dinheiro por palavra-chave não pôde ser validada no dataset de suporte (o texto não tem relação com o tipo). Em produção, ela deve usar o tipo do chamado escolhido pelo cliente.
- Não implementei a geração de resposta sugerida (o "G" do RAG) porque o dataset não tem resoluções reais para usar como base.

---

## Process Log — Como usei IA

> O passo a passo completo, com horários, está em [`process-log/diario.md`](process-log/diario.md).

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| Claude (chat) | Checagem de qualidade, análise estatística, segunda varredura atrás de pegadinhas, escrita do código do protótipo e revisão dos textos |
| Python (pandas, scikit-learn, scipy, Streamlit) | Análise, classificador e protótipo |
| Git / GitHub | Versionamento e entrega (o histórico de commits mostra a evolução) |

### Workflow

1. Li os 4 desafios e escolhi o 002 por ser o mais próximo do que faço no dia a dia (suporte, agentes de IA, WhatsApp, CRM).
2. Abri alguns tickets para ver o dado com meus próprios olhos antes de pedir qualquer análise.
3. Pedi ao Claude uma checagem de qualidade antes de qualquer conclusão. Ela mostrou que o dataset de suporte tem problemas sérios.
4. Pedi a análise das três perguntas do diretor. A IA rodou os testes; eu decidi não tirar conclusão de ruído.
5. **Desconfiei:** o desafio parecia montado para pegar quem cola o brief na IA e acredita. Pedi uma segunda varredura procurando pegadinhas de propósito, e foi aí que apareceu a mais importante, a do cruzamento.
6. Formalizei meu raciocínio e minhas hipóteses (`docs/00-raciocinio.md`).
7. Pedi ao Claude o código do protótipo com as regras que eu defini, e rodei e testei na minha máquina.
8. Escrevi a entrega e revisei os números contra os arquivos gerados pelos scripts.

### Onde a IA errou e como corrigi

- **ROI que não se sustentava.** Na primeira análise, o Claude apresentou "72% automatizados com 95,6% de acerto, ~90 h/mês economizadas" como se valesse para o suporte da empresa. Quando pedi a segunda varredura, testamos aplicar o modelo nos tickets de suporte e ele não funcionou (74% viram "Hardware"). Corrigi a forma de apresentar: a técnica está provada; o ROI é estimativa a confirmar em piloto.
- **Números que mudaram com o pré-processamento.** No protótipo final, o texto é limpo antes de classificar. Os números do teste de transferência mudaram (confiança média de 60% para 55%), então passei a usar só os números gerados pelos scripts, não os da conversa.
- **ROI que contradizia as minhas próprias regras.** Numa terceira revisão, perguntei se o desafio não teria uma "subpegadinha" para quem achasse a primeira. Encontramos uma na nossa própria conta: o ROI assumia 72% de automação, mas as regras mandam dinheiro sempre para humano, e isso é 60% do volume de suporte. Reescrevi o ROI como faixa (36 a 90 h/mês, depois ajustada para 31 a 79 h/mês com a cobertura efetiva) e separei "IA encaminhar" de "IA decidir".
- **Cobertura que ignorava as regras.** Depois de enviar o PR, revisei a entrega e testei as regras de passagem para humano com números. O "72% automatizado" era só o limiar; com as regras ligadas, são 62,8%. Corrigi o README, o protótipo, o resumo executivo e o ROI.
- **Suspeita de atalho pela assinatura.** Levantamos a hipótese de que o modelo acertava pelo cargo no fim do texto. Testei em vez de só citar como risco: a hipótese caiu (86,1% sem as últimas palavras).
- **Formato do tempo.** A leitura literal do README tratava "First Response Time" como duração. Conferindo o dado, vi que é data/hora, o que mudou toda a análise de tempo.

### O que eu adicionei que a IA sozinha não faria

- **Desconfiar do desafio, e de mim mesmo.** A IA respondeu as perguntas do diretor; fui eu que suspeitei de pegadinha e pedi para procurar de propósito, o que achou o erro do cruzamento. Depois, suspeitei de uma subpegadinha para quem se achasse esperto demais, e ela estava na minha própria conta de ROI.
- **Não vender ruído como insight.** Escolhi dizer "o dado não sustenta essa conclusão" em vez de entregar um ranking de canais bonito e falso.
- **As regras de passagem para humano.** Vêm da minha experiência implantando agentes de IA de vendas e suporte: dinheiro, retenção, segurança e acesso nunca ficam só com a máquina, e confiança baixa vai para humano. Também tirei do dado que Administrative rights é a pior categoria do modelo, e por isso ela fica sempre com humano.
- **Follow-up como prioridade.** Ver um terço dos tickets parados esperando o cliente e ligar isso a uma solução simples vem de quem já implementou follow-up automático no WhatsApp.
- **Piloto antes de ligar a automação.** Não prometer ROI sem validar com os dados da própria operação.

---

## Evidências

- [x] Screenshots do protótipo rodando (`process-log/screenshots/`)
- [x] Diário do processo com horários (`process-log/diario.md`)
- [x] Raciocínio e hipóteses (`docs/00-raciocinio.md`)
- [x] Git history (commits mostrando a evolução)
- [x] Scripts reprodutíveis: qualquer pessoa roda `diagnostico.py`, `avaliar.py` e `checagens_extras.py` e chega nos mesmos números
- [x] Resumo executivo de 1 página para o diretor (`RESUMO_EXECUTIVO.md`)

---

_Submissão enviada em: 17/11/2026_
