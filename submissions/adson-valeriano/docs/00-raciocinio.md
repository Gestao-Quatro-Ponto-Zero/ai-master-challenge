\# Entendimento do problema



\## O que o diretor quer

Ele pediu três coisas:

1\. \*\*Onde estamos perdendo tempo\*\*, com dados e não com achismo.

2\. \*\*O que dá para automatizar com IA\*\*, e o que não dá, porque nem tudo deve ficar com a máquina.

3\. \*\*Ver funcionando.\*\* Ele não quer apresentação, quer algo rodando.



O cenário: o time está sobrecarregado, os chamados estão demorando mais e a satisfação caiu.

O diretor precisa decidir onde investir: em pessoas, em processo ou em automação.



\## O que eu esperava encontrar

Estas hipóteses vêm da minha experiência no suporte da Skill-Hub. Formalizei por escrito depois

da primeira leitura dos dados, mas foram elas que guiaram o que eu fui testar.



1\. \*\*Boa parte do volume é repetitiva.\*\* Muitos chamados são a mesma dúvida escrita de outro

&#x20;  jeito: acesso, configuração, cobrança. O time perde tempo lendo e encaminhando o que já

&#x20;  tem resposta conhecida.



2\. \*\*Chamados ficam parados esperando o cliente.\*\* O cliente para de responder, ninguém retoma

&#x20;  e o chamado trava a fila. É por isso que follow-up automático é uma das automações que

&#x20;  mais implemento.



3\. \*\*A insatisfação vem mais da demora do que do problema em si.\*\* Quando o cliente reclama,

&#x20;  quase sempre é porque esperou demais ou caiu com a pessoa errada e precisou explicar tudo

&#x20;  de novo.



\## O que os dados mostraram

\- \*\*Hipótese 1: confirmada em parte.\*\* No dataset de suporte não dá para medir repetição, porque

&#x20; os textos foram gerados a partir de 16 frases-modelo. No dataset de TI, que é real, a

&#x20; classificação automática funciona: 86,6% de acerto, e 95,6% quando a IA só decide com

&#x20; 70% ou mais de confiança (o que cobre 72% dos chamados). A triagem automática se sustenta.



\- \*\*Hipótese 2: foi o único sinal aproveitável.\*\* Um terço dos chamados (2.881 de 8.469) está

&#x20; parado aguardando resposta do cliente. Considerando que o dado parece sintético, isso

&#x20; ainda aponta para follow-up automático como ganho direto.



\- \*\*Hipótese 3: não foi possível confirmar, e esse é o principal achado.\*\* Os tempos estão

&#x20; inconsistentes: em 49% dos chamados fechados, a resolução aparece antes da primeira

&#x20; resposta. A satisfação não varia com nada: fica em torno de 3 em todos os canais, e a

&#x20; correlação com o tempo é de 0,02. A empresa não mede direito o que importa. Antes de

&#x20; otimizar, é preciso medir.

&#x20; A parte de "cair com a pessoa errada" não dá para medir no dataset de suporte, mas é

&#x20; exatamente o problema que o roteamento automático do protótipo ataca.



O passo a passo de como cheguei nisso está em `process-log/diario.md`.

