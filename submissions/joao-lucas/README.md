# Submissão — João Lucas Marques da Silva — Challenge 002

## Sobre mim

- **Nome:** João Lucas Marques da Silva
- **LinkedIn:** https://www.linkedin.com/in/joaolucasmarquesdasilva/
- **Challenge escolhido:** 002 — Redesign de Suporte

---

## Executive Summary

Comecei validando a qualidade dos dois datasets antes de qualquer análise. O Dataset 1 apresenta inconsistências graves: 49,3% dos intervalos de tempo são negativos, as notas de satisfação têm distribuição uniforme e o campo de resolução contém texto sem sentido. Parte das perguntas do desafio, portanto, não tem resposta confiável com essa base, e optei por declarar isso em vez de estimar. O que era mensurável eu comprovei estatisticamente: o campo de prioridade não influencia o desfecho do ticket, nenhuma variável explica a satisfação do cliente, e 84,1% dos tickets podem ser classificados automaticamente. A conclusão é que o gargalo não é o tempo de atendimento, é a ausência de medição, e a solução que construí, um fluxo de agentes em n8n com mais de 40 nodes, registra cada decisão antes de automatizar qualquer etapa.

---

## Solução

### Abordagem

Trabalhei em 4 etapas, uma de cada vez, sem pular:

1. **Ler antes de rodar.** Li o brief (pelo menos 5x antes de fazer qualquer coisa, e fui conferindo durante o processo) e os dois datasets sem escrever nenhuma análise. Primeira coisa que achei: o README promete ~30.000 tickets no Dataset 1, mas o arquivo tem 8.469 linhas. Reportei antes de continuar, porque todo cálculo de "horas por ano" depende desse denominador.
2. **Auditar o dado antes de confiar nele.** Em vez de partir para gráficos, testei se os dados fazem sentido. Não fazem. Detalho abaixo.
3. **Classificar.** Usei o Dataset 2 (47.837 tickets, 8 categorias reais) para construir um classificador de verdade, medindo a acurácia a cada tentativa.
4. **Propor e construir.** Desenhei o fluxo atual, apontei onde ele quebra, e construí um protótipo funcional que ataca a causa, não o sintoma.

A decisão que mais me custou tempo foi **não juntar os dois datasets**. Era o caminho óbvio (e o que a IA sugeriu primeiro). Testei, provou não funcionar, e eu desisti dele — está explicado nos findings.

### Resultados / Findings

**O que os dados realmente são**

| O que verifiquei | Resultado |
|---|---|
| Tamanho do Dataset 1 | 8.469 linhas (o brief diz ~30.000) |
| Tickets sem nota, sem tempo e sem resolução | 5.700 de 8.469 (~67%) — restam 2.769 completos |
| Intervalos de tempo negativos (resolução antes da 1ª resposta) | 49,3% |
| Janela total de todos os timestamps | 27 horas |
| Campo `Resolution` | frases sem sentido, geradas artificialmente |
| Descrição do ticket | template com placeholder não preenchido |

**Pergunta 1 — Onde o fluxo trava?**
Não dá para responder com essa base. Os campos de tempo estão corrompidos (metade negativa, tudo comprimido em 27h) — qualquer ranking de "pior canal" seria ficção. O que dá para afirmar: a **prioridade não funciona**. Ela está distribuída ~25% em cada nível e não tem relação com o desfecho do ticket (χ², p = 0,227). Na prática, o campo que deveria organizar a fila é ruído.

**Pergunta 2 — O que impacta a satisfação?**
Nada. E isso eu testei um por um: canal (p = 0,467), prioridade (p = 0,400), tipo de ticket (p = 0,257), idade do cliente (correlação −0,004). Até um modelo de ensemble deu R² negativo (−0,19), que em linguagem simples significa: errar menos seria chutar a média. A nota de satisfação nesse dataset é aleatória.

**Pergunta 3 — Quanto estamos desperdiçando?**
Não é calculável, e eu prefiro dizer isso a inventar. Faltam dois números que não existem em lugar nenhum dos datasets: minutos médios de triagem por ticket e custo/hora do agente. Entreguei a fórmula pronta com o único parâmetro que eu tenho medido — 90,2% do volume de triagem é automatizável — para que a operação preencha o resto com dado dela.

**O classificador (4 tentativas medidas)**

| Tentativa | Acurácia |
|---|---|
| Zero-shot puro | 24,4% |
| Zero-shot calibrado | 37,5% |
| Few-shot por centroide | 72,0% |
| MLP sobre embeddings | **84,1%** |

Do modelo saíram as regras de operação: confiança ≥ 0,70 cobre 90,2% dos tickets com 88,6% de acerto; confiança < 0,50 é só 1,8% do volume e acerta 33% — essa faixa vai direto para humano, sem sobrecarregar ninguém.

**O teste que me fez mudar de ideia**
Tentei aplicar o classificador treinado em TI nos tickets de consumo do Dataset 1. A confiança média subiu (0,829 contra 0,794) — parecia ótimo. Mas quando comparei a previsão feita a partir do assunto limpo com a feita a partir da descrição, só 35,8% concordavam. Confiança alta com acerto baixo é o pior cenário possível. Descartei o cruzamento.

**O protótipo — "Mesa Viva"**
Fluxo de 21 etapas em n8n + Supabase. A regra que organiza tudo: *se não está na tabela `mv_evento`, não aconteceu*. Cinco papéis:

- **Sentinela** — detecta que 40 pessoas estão reclamando da mesma coisa e avisa quem ainda não abriu ticket. A métrica nova passa a ser *ticket evitado*.
- **Triador** — infere a urgência real do texto, já que o campo de prioridade é ruído.
- **Resolvedor** — não encaminha, **executa** dentro do limite escrito por um humano.
- **Auditor** — segundo modelo revisa a resposta antes de sair. Se não estiver apoiada em dado real do sistema, não sai.
- **Curador** — cada caso resolvido pela mesa humana vira conhecimento novo e carimbo de hora.

Implementei por inteiro a Fase 2 (etapas 9–15, 43 nodes, 5 pontos de decisão, 2 agentes com modelos diferentes) — que é justamente onde mora a decisão difícil: a IA resolve ou o humano decide?

### Recomendações

Em ordem de prioridade:

1. **Instrumentar antes de automatizar.** Ligar o registro de eventos e, em 30 dias, a empresa terá pela primeira vez tempo de atendimento real. Sem isso, nenhum ROI aqui é confiável.
2. **Aposentar o campo de prioridade manual.** Ele não separa nada. Trocar por urgência inferida do texto.
3. **Ligar a classificação automática com banda de confiança.** ≥0,70 segue o fluxo; <0,50 vai para humano.
4. **Manter o humano no que tem dinheiro e emoção.** Reembolso acima do teto e cancelamento com retenção somam 3.447 tickets (40,7% do volume) — nenhum deles é decisão de IA.
5. **Não construir respostas sugeridas ainda.** Não existe histórico de resposta boa para imitar. A base nasce vazia e é populada pelos casos que a mesa humana resolver.

### Limitações

- **Horas e custo não foram quantificados.** Não foi esquecimento — os campos de tempo do Dataset 1 são inválidos e os dois parâmetros de negócio não existem na base.
- **O diagnóstico vale para 2.769 tickets completos**, não para os 8.469.
- **Os dois datasets são de domínios diferentes** (TI x produto de consumo). Não podem ser unidos, e eu provei isso em vez de forçar.
- **O protótipo tem mocks declarados**, nunca disfarçados: a política de reembolso e as APIs da empresa são fictícias, marcadas no código como `FICTICIO_DEMO`.
- **WF1, WF3 e os agentes Sentinela/Curador estão desenhados, não implementados.** Escopo declarado, dentro do time budget.

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usei |
|------------|--------------|
| Claude Chat | Leitura do brief, auditoria dos dados, execução de Python real, testes estatísticos e desenho da arquitetura (principalmente como um copilot para tudo) |
| ChatGPT | Meta prompt e comparação de resultados |
| n8n + n8n AI | Construção do protótipo, testes e verificações |

### Workflow

1. **Estabeleci as regras antes de começar.** Disse à IA: linguagem simples, me avisar quando faltar dado, nunca inventar número, e trabalhar por etapas — sem pular para a solução.
2. **Etapa 1 — leitura.** Brief e datasets, sem análise. Aqui apareceu a divergência das 30.000 linhas.
3. **Etapa 2 — auditoria.** Pedi para testar se o dado é confiável antes de qualquer gráfico. Descobrimos que é sintético.
4. **Etapa 3 — classificação.** Quatro iterações medidas, do zero-shot ao MLP. Parei em 84,1% conscientemente, em vez de queimar horas atrás de 90%.
5. **Etapa 4 — diagnóstico.** Cinco das seis perguntas respondidas com prova estatística; a sexta declarada não calculável.
6. **Etapa 5 — proposta e protótipo.** Rejeitei a primeira arquitetura proposta e pedi algo AI-first de verdade. Saiu a malha de agentes.
7. **Revisão forense.** Pedi para a IA revisar as próprias conclusões anteriores. Ela contradisse uma delas — e eu mantive a contradição na entrega.

### Onde a IA errou e como corrigi

**Erro 1 — o plano inicial.** A primeira coisa que a IA propôs foi treinar no Dataset 2 e aplicar no Dataset 1, tratando os dois como o mesmo problema. Parecia uma boa ideia. Mandei testar antes de aceitar: confiança alta (0,829) mas só 35,8% de concordância interna. Domínios diferentes. Descartamos.

**Erro 2 — recomendação impossível.** Numa etapa a IA recomendou "respostas sugeridas baseadas em resoluções passadas". Só que nós mesmos já tínhamos provado que o campo `Resolution` é um texto gerado por Faker. Pedi a revisão forense justamente para caçar esse tipo de coisa, e ela derrubou a própria recomendação.

**Erro 3 — a tentação de estimar.** Em mais de um momento apareceu a saída fácil: assumir "10 minutos por ticket" e produzir um ROI bonito. Barrei. Se eu chutar a premissa, o número é meu, não da operação. Entreguei a fórmula em aberto.

**Erro 4 — solução genérica.** A primeira proposta de automação era classificador + dashboard. Recusei: isso é o baseline que o G4 já tem rodado em três modelos. Pedi de novo, com a régua mais alta.

### O que eu adicionei que a IA sozinha não faria

Três coisas.

**Desconfiar do dado antes de analisar.** Se eu tivesse pedido "analise esses tickets", teria recebido gráficos bonitos por cima de dados quebrados — e eles pareceriam certos. A decisão de auditar primeiro foi minha, e ela é o que separa esta submissão do baseline.

**Aceitar a resposta ruim.** Descobrir que "nada explica a satisfação" e que "não dá para calcular as horas" é péssimo para uma submissão. É muito tentador reformular até sair um número. Eu escolhi entregar o achado incômodo, porque o próprio brief diz que reprovar é "a IA disse, o candidato acreditou".

**A visão de produto — essa é inteiramente minha.** Uma empresa de tecnologia que resolve o próprio gargalo de suporte não precisa parar aí. O Mesa Viva, validado internamente por uso real, pode virar produto vendável: a mesma construção que corta custo interno abre uma linha de receita nova, já testada em casa. A IA executou o desenho. A ideia de que a solução interna é um produto foi minha.

---

## Evidências

Todas as evidências de uso de IA estão no arquivo **LOG-JOAOLUCAS**.

Criei esse arquivo como uma forma de registrar todos os meus passos e toda a lógica por trás de cada resultado que tive durante o desenvolvimento do projeto. Nesse PDF estão todos os registros, prints e links das conversas com o Claude. Toda conversa que tive com o ChatGPT eu registrei em print, tudo dentro do LOG-JOAOLUCAS.

---

## Comentários

Agradeço pela oportunidade de participar do processo. Durante o desenvolvimento consegui aplicar boa parte do meu conhecimento, mas reservei este espaço para dois comentários. Primeiro: pelo nível de complexidade do projeto, não foi necessário recorrer a tecnologias mais avançadas como skills, subagentes ou orquestração em loop, recursos que permitiriam construir automações ainda mais eficientes em um cenário maior. Segundo, sobre o protótipo: recriei as duas tabelas já cruzadas e com os dados completos, para simular um fluxo real do dia a dia, e o sistema suportou 100% do volume. Obrigado à equipe do G4.

---

_Submissão enviada em: 19/07/2026_
