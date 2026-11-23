# Notas de processo — Lead Scorer (Challenge 003)

> Rascunho do process log. Cada entrada: o que aconteceu, o que decidi, por quê.
> Marque quando a ideia foi minha, quando veio da IA e quando a IA (ou eu) errou.
> Ferramenta principal: Claude (chat + execução de código).

---

## 23/11 — Leitura do desafio e auditoria dos dados

- Li o repositório inteiro e pedi para o Claude fazer uma segunda leitura procurando pegadinhas.
- Achados no repo: o `.gitignore` ignora `submissions/` → vou precisar de `git add -f` no envio.
- Achados nos dados (verificados rodando código, não só lendo):
  - O pipeline escreve `GTXPro` e o catálogo escreve `GTX Pro` → o join perde o preço sem dar erro.
  - Dos 35 vendedores, só 30 têm deals.
  - Só 2.089 dos 8.800 deals estão abertos; o resto é histórico.
  - 68% dos deals abertos não têm conta → "tamanho da conta" não serve para a maioria.
  - Os dados vão até 31/12/2017 → essa é a data de "hoje" da ferramenta.
  - Nenhum deal fechado levou mais de 138 dias, mas 81% dos deals em Engaging já passaram disso → pipeline cheio de deals "zumbis".
  - A taxa de ganho quase não varia por produto/setor/região (60–65%) → sinal fraco.
- Escolhi o 003 porque os dados têm mais estrutura aproveitável e o entregável é software.

## 23/11 — Entendendo o problema antes de codar

- **Errei e corrigi:** entre um deal de 70% × US$ 55 e outro de 50% × US$ 26.768, escolhi o primeiro. Fazendo a conta do valor esperado (probabilidade × valor), o segundo vale ~350× mais. → O score usa valor esperado.
- **Conflito:** se a probabilidade quase não varia, o ranking vira "ordenar por preço", o que o README proíbe. → A probabilidade precisa depender de algo que diferencie os deals:
  - idade do deal (dias desde o engage);
  - taxa de ganho do vendedor naquele produto (varia de 47% a 81%), misturada com a média geral quando houver poucos deals.
- **Decisão:** duas listas → **Focar** (deals vivos, ordenados) e **Limpar** (deals parados há mais de 138 dias).
- **Errei e corrigi:** propus que a ferramenta movesse sozinha os deals mortos para "perdido". Problema: o CRM não tem nenhuma coluna de último contato, então a ferramenta não saberia se o cliente ligou ontem.
- **Errei e corrigi:** sugeri treinar uma IA para descobrir isso. Não funciona: se o dado não existe, nenhum modelo consegue aprender com ele.
- **Decisão (humano no controle):** a ferramenta sugere e o vendedor decide, com os botões **Manter** / **Encerrar**. O clique em Manter salva a data como "último contato confirmado" → a ferramenta passa a gerar o dado que faltava.
- **Decisão:** cada deal mostra o cálculo do score (explicabilidade).
- **Stack:** Python + Streamlit, porque roda com um comando e cabe nas 4–6 h.

## 23/11 — Etapa 1: carregar e limpar os dados

- O Claude escreveu o `dados.py`: corrige `GTXPro`, `technolgy` e `Philipines`, fixa a data de referência e para com erro se algum join perder dados.
- Baixei os CSVs, rodei `python dados.py` e conferi: 8.800 deals, 2.089 abertos, 1.425 sem conta, 138 dias de duração máxima. Bate com a auditoria.

## 23/11 — Etapa 2: cálculo do score

- **Validei antes de confiar:** treinei o score com os deals fechados até jun/2017 e testei nos que entraram depois.
- **A IA errou (1):** o Claude tinha dito que deal mais velho tem menos chance. O teste mostrou o contrário dentro da janela normal: quem sobrevive até 120 dias ganha ~10 pontos a mais (efeito repetido nos dois períodos). Só depois de 138 dias o deal vira zumbi.
- **A IA errou (2):** vendedor × produto parecia sinal (47% a 81%), mas, dividindo os deals em duas metades aleatórias, a correlação foi −0,04. Era sorte, não talento. O score com esse fator acertou 50,2% (AUC) — igual a sortear.
- **Decisão:** tirei vendedor × produto do cálculo; mostro só como histórico na tela, com aviso. Motivo: se o histórico sumisse, o vendedor acharia que a ferramenta ignora o desempenho dele e perderia a confiança nela. Mostrando o dado com o aviso "testado, não previu resultados", a ferramenta responde essa dúvida antes que ela apareça e mantém o score honesto.

- **Por que deals mais velhos ganham mais (até 138 dias):** deals perdidos morrem cedo (mediana de 14 dias)
  e os ganhos tendem a demorar mais (mediana de 57). Quem sobrevive já passou da fase em que a maioria dos
  perdidos morre, então a chance sobe. Depois de 138 dias não há histórico → vai para Limpar.
- **Decisão — Prospecting (500 deals sem `engage_date`):** criei uma terceira lista, **Prospectar**. A idade
  não se aplica (o deal ainda não está em negociação), mas falta a data de criação no CRM. Ordenei pelo valor
  esperado e deixei um aviso na tela.

## 23/11 — Etapa 3: a tela no Streamlit

- **Decisão — desempate:** vários deals têm o mesmo valor, e a ordem mudava entre computadores. Em Limpar,
  empatados → o parado há menos tempo primeiro, porque tem mais chance de ser salvo.
- **Decisão — terceiro botão:** além de Manter e Encerrar, criei **Recomeçar como prospect**. Motivo: um deal
  parado há muito tempo pode ser retomado com uma proposta ou abordagem nova; tratar como negociação nova
  mantém o histórico honesto.
- **A IA errou (3):** na primeira versão da tela, o valor aparecia cortado ("US$ 26....") e as métricas tinham
  setas ↑ que sugeriam crescimento. Corrigido olhando a tela, não pelo teste automático.
- **A IA errou (4):** no roteiro de testes, o Claude disse que a Rosalina teria 33 deals em Limpar. Testando,
  deu 34. O 33 tinha sido medido depois de um teste que já tinha encerrado um deal dela.
- **Teste de usabilidade:** usando a tela como vendedor, não soube onde clicar na revisão. Encontrei 3 falhas:
  não saber onde ir, o que fazer e o que aconteceu depois do clique.
- **Decisão:** entre "um deal por vez" (mais guiado, mas mais lento) e "lista mais clara" (mais prática),
  escolhi a lista. Correções: botão "Revisar agora", instrução no topo, "Comece por aqui", mensagem
  após o clique e botão Desfazer.
- **A IA errou (5):** depois do clique, o seletor de listas ficava sem nenhuma opção marcada. Corrigido.
- **Reteste:** refiz o fluxo de revisão sem ler instruções: achei a lista pelo botão "Revisar agora",
  confirmei um deal e desfiz. Funcionou sem travar. Recarreguei a página (F5) e as decisões
  continuaram salvas. A opção 2 passou; a opção 1 não foi necessária.