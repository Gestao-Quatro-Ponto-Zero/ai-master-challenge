# Produto: o copiloto de pipeline do vendedor

Escrito pelo orquestrador a partir do desafio e da direção do Daniel: as regras do teste são o piso; o produto é o melhor que este método consegue construir para o vendedor, medido pela utilidade. O Daniel leu e aprovou este texto sem alterações em 10/11/2026; o que ele disser depois substitui o que está aqui.

## Quem usa
- O vendedor: um dos 35 do time, não técnico. Abre na segunda de manhã, entre uma ligação e outra.
- O gestor: o time dele ou a região, a mesma ferramenta com filtro.
- Quem pediu: a Head de Revenue Operations. Quer algo que o vendedor use, não um modelo que ninguém abre.

## A dor (nas palavras dela)
"Nossos vendedores gastam tempo demais em deals que não vão fechar e deixam oportunidades boas esfriar." São duas dores: tempo perdido no que não fecha, e negócio bom esfriando. Ordenar por valor não resolve nenhuma.

## O que o produto faz
1. Diz por onde começar: a lista do vendedor já ordenada pelo que vale o tempo dele (chance de fechar, valor, e o tempo esfriando), com três grupos: focar agora, manter aquecido, deixar ir.
2. Explica cada posição em linguagem de vendedor: os fatores reais daquele negócio, com o peso de cada um. Nenhum número sem explicação.
3. Indica o próximo passo: a ferramenta escolhe o passo a partir do que os dados mostram daquele negócio (tempo parado, chance, valor, o que fecha e o que não fecha em casos parecidos) e a IA redige o porquê para aquele negócio.
4. Entrega o briefing de segunda: uma página por vendedor, pronta para ler em um minuto: os cinco primeiros, o que largar, o que está esfriando.
5. Mostra ao gestor onde orientar: quem está com pipeline parado, quem insiste no que não fecha, onde está o valor do time.

## Como a IA entra, sem chave de API
- O produto completo é o score mais a tela: lista, grupos, fatores e filtros funcionam sem nenhum texto de IA. A IA só acrescenta texto.
- Os textos da IA são gerados por um pipeline real sobre os dados reais e ficam guardados no repositório com a procedência (modelo, data, o prompt, os fatos que entraram). O avaliador roda e vê tudo sem chave e sem conta.
- Todo número e todo nome num texto vem dos fatos daquele negócio, preenchido pelo código e não pela IA; um texto com dado que não esteja nos fatos é reprovado. A IA explica e redige; quem decide a ordem, o grupo e o próximo passo é o score, que é auditável.
- Com o Claude Code instalado, um comando regenera os textos. Nenhuma chave de API é usada, e nenhuma credencial vai no repositório.

## Princípios
- Simples na tela, completo por baixo: em dez segundos o vendedor sabe por onde começar.
- Honesto: o que os dados não sustentam não entra no score, e a tela diz o que não sabe.
- Cada recurso de IA responde a uma dor desta página, ou sai.
- Roda com um comando documentado e tem um endereço público.

## Depois da entrega (sustentação)
Um comando recalcula tudo quando os dados mudam; um relatório avisa quando o padrão dos dados se afasta do que o score aprendeu; e o ganho real se mede com um grupo de controle (metade do time com a ferramenta, metade sem, por um ciclo de vendas).

## Fora
Editar o CRM, login, integrações reais com e-mail ou Slack (o briefing sai como texto pronto para enviar), previsão de receita.

## Como sabemos que ficou bom
- A ordenação é medida contra "ordenar por valor" e contra a taxa média, em negócios que estavam abertos numa data de corte, e o número é publicado como saiu.
- Cada grupo (focar agora, manter aquecido, deixar ir) aparece com o que aconteceu com negócios parecidos; "deixar ir" só existe se os números mostrarem que é seguro.
- Cada número na tela e no README sai de um comando que está no repositório; cada texto da IA passa na conferência contra os fatos.
- Alguém de fora roda seguindo só o README, e um vendedor entende a tela sem explicação.
