# Proposta de automação com IA

**Princípio:** a IA classifica todo ticket, mas só **age sozinha** quando está confiante e o caso não é sensível. Automatizar 100% seria pior: nos tickets em que o modelo tem dúvida, ele acerta só cerca de 67%.

Reprodução: scripts em `analysis/` (Dataset 2, Kaggle adisongoh) e testes em `prototype/src/`. Protótipo: `prototype/index.html`.

---

## 1. Como os dois datasets se cruzam — e o limite que isso revela

| Dataset | Papel |
|---|---|
| 2 — 47.837 textos de TI classificados | Treina e **mede** o classificador em dados reais |
| 1 — 8.469 tickets de clientes | Mostra o que a operação não mede e **testa se o classificador serve para ela** |

**Rodamos o motor nos 8.469 textos do Dataset 1** (`prototype/src/cross_ds1.js`, sugestão da auditoria):

| Tipo do ticket (Dataset 1) | Confiança média | Encaminhado pela IA | Categoria de TI mais atribuída |
|---|---|---|---|
| Technical issue | 60% | 11% | Hardware (68%) |
| Billing inquiry | 61% | 12% | Hardware (67%) |
| Cancellation request | 61% | 11% | Hardware (68%) |
| Product inquiry | 61% | 12% | Hardware (68%) |
| Refund request | 61% | 12% | Hardware (67%) |

Duas conclusões:
1. **O texto do Dataset 1 não carrega o tipo do ticket:** os cinco tipos recebem exatamente a mesma distribuição (mais uma evidência de dados gerados por computador).
2. **O classificador de TI não reconhece a operação de clientes:** confiança média de 60% e só ~12% iria sozinho. Cobrança, reembolso e cancelamento não cabem nas 8 categorias de TI.

**Quanto histórico é preciso** (`analysis/07`, curva de aprendizado no Dataset 2): com 1.000 tickets rotulados a IA assumiria 17% sozinha; com 2.000, 27%; 5.000, 41%; 10.000, 50%; 38.000, 64% — sempre com 97% a 99% de acerto quando age. **O limiar protege a qualidade; o volume automatizado cresce com o histórico.**

**Consequência para a proposta:** o que se transfere para a operação do briefing é o **método** (treinar com o histórico rotulado da própria empresa, medir em dados nunca vistos, fixar um limiar, manter fila humana), não o modelo. Enquanto não há histórico rotulado, as filas de cliente — Retenção, Financeiro, Comercial — funcionam por regras de texto (seção 3).

## 2. O classificador

TF-IDF (palavras e pares de palavras) + regressão logística. Treinado em 38.269 tickets, testado em **9.568 que ele nunca viu: 86,1% de acerto** nas 8 categorias. Roda no navegador; o teste de paridade Python × JavaScript dá a mesma categoria em 200 de 200 casos.

**O limiar não foi ajustado no teste.** O 80% foi uma escolha de política. Para confirmar, treinamos de novo com uma parte do treino separada para validação (`analysis/06`): validação e teste dão o mesmo resultado (IA sozinha com 96,4% e 96,9% de acerto; certa entre as 2 opções em 91,1% e 90,6%).

As categorias aparecem com o nome do que contêm. "Administrative rights" é exibida como **Suporte a software (Administrative rights)**: as palavras que mais pesam nela são Outlook, Windows, instalação e atualização, não concessão de permissões.

## 3. Quem age — regras em ordem fixa

A primeira regra que bater decide. Números: efeito nas 9.568 previsões de teste.

| # | Fila | Regra | % dos tickets de teste |
|---|---|---|---|
| 1 | Segurança assume | Phishing, conta invadida, vazamento, golpe, vírus | 0,5% |
| 2 | Ouvidoria assume | Assédio, discriminação, denúncia, fraude — **nenhuma pergunta automática** | 0,1% |
| 3 | Retenção assume | Cancelar conta, contrato, assinatura; encerrar conta; reembolso; ir para concorrente. Cada ocorrência é checada: "cancelar a reunião" e "**não** quero cancelar" não contam | 0,6% |
| 4 | RH assume | Desligamento, rescisão, salários, dados pessoais | 2,3% |
| 5 | Aprovação necessária | Pedido de privilégio (administrador, acesso elevado) | 0,5% |
| 6 | Financeiro assume | Cobrança, fatura, boleto | 0,6% |
| 7 | Comercial assume | Preço, planos, orçamento | 0,6% |
| 8 | Aguardando cliente | Texto sem informação: a IA faz perguntas simples | — |
| 9 | **IA encaminhou** | Confiança ≥ 80% (≥ 90% em Suporte a software) | **60,8%**, com **96,9%** de acerto |
| 10 | Atendente escolhe | Abaixo do limiar: 2 opções, 1 clique — a certa está entre elas em **90,3%** | 33,9% |

As filas 1–7 desviam 5,3% dos tickets para pessoas mesmo quando o modelo está confiante.

**Limite das regras (auditoria fase 02).** Elas são palavras-chave e erram para os dois lados em textos que não estavam nos testes:
- **Falso alarme:** "o notebook está com vazamento de memória" → Segurança P1; "preciso discriminar os custos por centro de custo" → Ouvidoria; "a última vez que o Outlook funcionou foi ontem" → Retenção.
- **Caso que escapa:** "como faço pra desistir da assinatura?" e "tô recebendo mensagem no Teams de um perfil que se diz da TI pedindo minha senha" → encaminhados pela IA.
- **Piso de erro medido:** no Dataset 2 (TI interna, sem clientes), os desvios para Retenção (62) e Comercial (56) são falsos positivos por definição: **pelo menos 23% dos 506 desvios estão errados**.

Decidimos **não** continuar ajustando palavra por palavra (decisão 25): seria ajustar às perguntas da prova. **Em produção, os casos sensíveis precisam de um classificador próprio**, treinado com exemplos rotulados da empresa (ou um modelo de linguagem com revisão humana), medido como o classificador principal. As regras ficam como rede de segurança.

**Exemplos reais do Dataset 2** que justificam não automatizar: *"admin rights hi play around provide credentials developer"* (privilégio); *"leaver form… leaving date… forward"* e *"please delete account… she left"* (RH com dados pessoais); *"please add yet more look alike domains to anti block list"* (segurança); *"access to detailed salary history reports"* (salários).

## 4. Prioridade — só fatos sobem

| Cor | Prioridade | Regra |
|---|---|---|
| 🔴 | P1 Crítica | Impacto coletivo: "fora do ar", "ninguém da equipe consegue", "financeiro inteiro parado"; vazamento de dados. **Aviso de manutenção programada não conta** |
| 🟠 | P2 Alta | Pessoa parada ("não consigo trabalhar"), incidente de segurança, caso de Ouvidoria, ou cliente de Retenção pelas respostas (seção 5) |
| ⚪ | P3 Normal | Todo o resto |

**"Todo mundo pode pedir prioridade, mas o que define é o caso"** (decisão 22): "URGENTE", "asap", "importance high" não sobem a prioridade sozinhos — disparam a pergunta de impacto. A IA só sobe a prioridade, nunca rebaixa. P1 vinda apenas da resposta do cliente fica marcada **"a confirmar pelo atendente"**.

**Atraso:** todo ticket mostra há quanto tempo está aberto e ganha a tag **Atrasado** ao passar do limite da sua prioridade (exemplo editável: P1 1 h, P2 4 h, P3 24 h). Filtro só de atrasados, para achar o chamado simples esquecido.

## 5. Perguntas ao cliente

- **Texto vago:** assunto (11 opções em linguagem simples, incluindo cobrança e preços), se consegue trabalhar e quem mais está afetado.
- **Falha ou pedido de urgência sem impacto declarado:** o ticket é encaminhado na hora e a IA pergunta, em paralelo, se a pessoa consegue continuar trabalhando.
- **Cancelamento:** entra P3 com a tag **Risco de perder o cliente**; o cliente recebe o aviso de que uma pessoa vai falar com ele e duas perguntas. Problema não resolvido + quer resolver → P2 (melhor chance de reter); já decidiu ou vai para concorrente → P2 (janela curta); preço ou "não uso mais" → P3.
- **Ouvidoria nunca recebe perguntas automáticas.**

**Risco declarado (auditoria):** 34% dos tickets do Dataset 1 já estão "aguardando o cliente". Só o texto vago segura o ticket esperando resposta; as outras perguntas vão em paralelo. Ainda assim, "tickets parados aguardando resposta" entra como métrica de acompanhamento.

## 6. O que ficou fora do briefing, e por quê

- **Respostas sugeridas:** as resoluções do Dataset 1 são frases sem sentido ("Offer investment fish.") e o Dataset 2 não tem resoluções. Não há base honesta para sugerir respostas.
- **Detecção de duplicatas:** o Dataset 2 tem zero textos duplicados; o Dataset 1 tem textos de modelo repetidos, que seriam falsos duplicados.

## 7. Retorno estimado

**Hipótese** (desempenho de TI aplicado ao volume do briefing, base de 20% de erro manual): **1.092 h/ano liberadas (≈ R$ 21,8 mil bruto), 3.081 reencaminhamentos evitados e 2.054 h de tempo perdido evitado** (estimado pelos usuários), contra ~568 tickets/ano encaminhados errado pela IA. Sensibilidade e leitura honesta no `diagnostico.md`. O valor principal é o tempo do usuário, não a folha.

## 8. Como funciona na prática e integração

1. Ticket entra e o horário de abertura é registrado.
2. Português passa por um glossário de ~330 termos de suporte (o modelo foi treinado em inglês).
3. Classificação + regras de quem age + prioridade por fatos.
4. Perguntas ao cliente quando falta informação.
5. Registro de tudo: categoria, confiança, quem decidiu, respostas e correções do atendente.
6. Correções entram no próximo retreino.

Integração (não construída; depende do ecossistema do cliente): **Microsoft 365** — Power Automate recebe o e-mail, chama o motor (Azure Function ou Office Script), cria tarefa no Planner e manda Adaptive Card no Teams; **Google Workspace** — Apps Script (que já roda JavaScript) com gatilho no Gmail, registra numa planilha e avisa no Google Chat.

## 9. Quando desligar a IA

Auditoria semanal por amostra dos tickets encaminhados pela IA:
- **Acerto abaixo de 95% por 2 semanas seguidas → alerta e revisão.**
- **Abaixo de 93% → a IA volta a só sugerir** (todos os tickets passam pelo atendente) até o retreino.

## 10. Português: o que foi medido

| Teste | Resultado |
|---|---|
| 56 tickets reais de teste, em inglês | 96,4% |
| Os mesmos 56 traduzidos, sem glossário | 35,7% |
| Com glossário (após 1 ajuste nesses mesmos tickets — otimista) | 91,1% |
| 4 tickets independentes escritos pelo Rafael | 2 corretos; 1 bug grave corrigido; 1 levou à revisão da prioridade de cancelamento |
| ~40 tickets em português da auditoria | ~10 sem nenhuma palavra conhecida: o glossário cobre jargão de TI, não o jeito como um cliente escreve |

## 11. Correções feitas no caminho

| O que estava errado | Quem achou | Correção |
|---|---|---|
| Regra baseada no nome "Administrative rights" | Teste do Rafael | Regra olha o pedido de privilégio |
| Glossário puxava categorias com palavras genéricas | Teste do Rafael | Palavras genéricas não são traduzidas |
| Cancelamento escapava da Retenção (regras fora de ordem) | Teste do Rafael | Ordem fixa |
| Cor misturava urgência e quem age | Rafael | Cor = prioridade; rótulo = quem age |
| Dois assuntos anulavam o cancelamento; "encerrar conta", "money back" e concorrente não eram detectados; negação virava Retenção | Auditoria | Checagem por ocorrência, negação, termos novos |
| Assédio recebia questionário; phishing e vazamento iam com a IA | Auditoria | Filas de Ouvidoria e Segurança |
| "URGENTE" e "importance high" subiam a prioridade; "não é urgente" também; manutenção programada virava P1; impacto coletivo escapava | Auditoria | Só fatos sobem; exclusão de avisos; P1 ampliado |
| Cobrança e preço sem destino | Auditoria | Filas de Financeiro e Comercial |
| Cobertura de 64,4% ignorava as regras | Auditoria | Recalculada: 60,8% |
| "Correção entra no próximo treino" era falso no protótipo | Auditoria | Texto corrigido |

**43 casos de regressão** (testes do Rafael e da auditoria fase 01) rodam a cada mudança: `prototype/src/regression_test.js`. Como esses casos foram usados para corrigir as regras, eles não são teste independente — e a fase 02 da auditoria mostrou isso na prática (seção 3).

## 12. O que acompanhar depois de ligar

Acerto auditado semanal (critério da seção 9) · taxa de correção dos atendentes por categoria · tempo até o ticket chegar ao time certo, antes × depois · tickets atrasados por prioridade · tickets parados aguardando resposta do cliente · retenção: clientes que responderam "quero resolver" e foram retidos.

## Limitações

- O modelo é de TI interna; para a operação do briefing ele precisa ser retreinado com o histórico rotulado da empresa (seção 1).
- As filas por regra e a prioridade não têm métrica de acerto completa (só o piso de ≥ 23% de falsos positivos) e erram em linguagem natural (seção 3).
- Limites de atraso, custos e o ganho de tempo das perguntas ao cliente são premissas a medir.
