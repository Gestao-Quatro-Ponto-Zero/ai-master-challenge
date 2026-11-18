# Submissão — Gustavo Civita — Challenge 003

## Sobre mim

- **Nome:** Gustavo Civita
- **LinkedIn:** https://www.linkedin.com/in/gustavo-civita-aibuilder/
- **Challenge escolhido:** 003 — Lead Scorer

---

## Executive Summary

Construí o **Case G4 · AI Master**, uma ferramenta em que o vendedor abre, vê a fila do dia na
ordem em que deve trabalhar e registra o que aconteceu em cada contato. Olhando
os dados antes de construir, o achado principal foi que **81% do pipeline em
andamento está morto**: nenhuma negociação do histórico foi ganha depois de 138
dias, e 1.291 das 1.589 abertas já passaram disso. A ordem que a ferramenta
propõe foi testada em 24 semanas de histórico. O que se sustenta: nenhuma das
801 negociações que ela tirou da lista de ligação foi ganha depois, e a ordem
preço × chance rende de 14% a 20% mais do que ordenar as mesmas negociações só
pelo preço. Contra uma boa regra simples ("o mais caro primeiro, ignorando o
que tem mais de 90 dias") ela ganha no 3º trimestre (+9%) e empata no 4º. O que o teste **não** prova é que usar a ferramenta aumenta as
vendas; para isso proponho um piloto de um trimestre, descrito em
[docs/plano-de-piloto-e-adocao.md](docs/plano-de-piloto-e-adocao.md).

---

## Solução

Como rodar, a lógica completa e as limitações estão em
[solution/README.md](solution/README.md). Em resumo:

**Demo no ar:** <https://case-g4-gustavo-c.vercel.app/>. Escolha um perfil e um
nome; não há senha. É a mesma tela desta pasta, publicada como site estático.

Para rodar na sua máquina, abra `solution/app/index.html` com dois cliques: a ferramenta roda inteira no
navegador, sem servidor e sem instalar nada. Prints em
[process-log/screenshots/](process-log/screenshots/README.md) e exemplos de saída
em [docs/exemplos/](docs/exemplos/README.md).

### Abordagem

Separo o que a IA executou do que eu decidi, porque é assim que aconteceu.

1. **Dados antes de tela (IA).** A IA conferiu as quatro tabelas, corrigiu o que
   estava inconsistente (`GTXPro` x `GTX Pro`, `technolgy`) e fixou "hoje" em
   31/12/2017, a última data da base. Usar a data real faria toda negociação
   parecer ter anos.
2. **Medir se existe sinal antes de pontuar (IA).** Vendedor, produto, setor,
   conta, porte da conta, manager e região não mudam a taxa de ganho de forma
   que sirva para ordenar. O que muda é o preço do produto (de $55 a $26.768) e
   o momento da negociação.
3. **Decidir a lógica de negócio com critério de vendas (eu)**, uma decisão por
   vez, e só então construir. As decisões, numeradas e com as minhas falas,
   estão em [process-log/decisoes.md](process-log/decisoes.md).
4. **Mandar auditar o que foi construído (eu pedi, agentes independentes
   executaram)**, com instrução de conferir os números no código em vez de
   confiar no que a própria IA afirmava, e corrigir o que não se sustentou.

### Resultados / Findings

**O que os dados mostraram**

- 81% das negociações em andamento têm mais de 138 dias, o prazo máximo em que
  alguma já foi ganha. Dos $4,97 milhões "em aberto", só 128 negociações têm
  chance real.
- Uma negociação é ganha no trimestre em que começou ou no seguinte: nenhuma das
  4.238 ganhas fechou depois disso (das 2.473 perdidas, uma). Por isso idade
  sozinha engana.
- O escritório Central não tem nenhuma negociação com chance: todas as suas em
  andamento são de julho e agosto. Ele concentra as 500 não iniciadas.
- A entrada de negociações cai de cerca de 780 por mês (agosto a outubro) para 283 em novembro e
  121 em dezembro.
- 68% das negociações abertas não têm a empresa preenchida, e a base não tem
  telefone, e-mail nem registro de contato.

**O que foi construído**

- **A priorização** (`solution/scoring.py`): preço de tabela × chance de ganhar,
  com a chance tirada do mesmo ponto dos trimestres anteriores. Cada negociação
  cai em uma de quatro listas, com ação diferente: ligar, primeiro contato,
  reativar por mensagem, encerrar.
- **O teste histórico** (`solution/backtest.py`), reprodutível com um comando, e
  35 testes automatizados (19 da priorização, 16 do fluxo de contato), incluindo
  um que garante que o cálculo de uma data não usa nada do futuro.
- **A fila do dia do vendedor**, em duas partes. Em cima, a meta do dia:
  retornos combinados e negociações com chance, na ordem testada, com a próxima
  em destaque. Embaixo, "se sobrar tempo": primeiro contato e reativação, que o
  histórico não consegue ordenar, com as que têm empresa cadastrada primeiro. A
  ficha de cada negociação explica o score em dois fatores e traz a empresa, o
  histórico de compras e o roteiro ou a mensagem sugerida.
- **O registro de cada contato**, com confirmação, anotação e retorno automático
  para a fila. É o único jeito de saber o que está esfriando, porque a base não
  tem atividade.
- **A visão do gerente e de operações de receita**: valor esperado das
  negociações com chance (preço × chance), prioritárias sem contato por vendedor, atividade do time e os
  registros de contato em CSV, que são a base do piloto. Filtros por vendedor,
  time e região.
- Em volta disso: três perfis de entrada, exportação em CSV e PDF, lista ou
  kanban, celular e modo escuro. Roda sem backend: é só abrir o arquivo.

**O que o teste histórico mostrou** (24 semanas, 01/07 a 09/12/2017)

| Verificação | Resultado |
|---|---|
| Receita das 10 primeiras de cada vendedor, contra "produto mais caro primeiro, ignorando o que tem mais de 90 dias" (empates de preço desempatados por sorteio) | +9% no 3º trimestre (14 de 14 semanas) e +3% no 4º (5 de 10): vantagem clara no 3º, empate no 4º |
| A mesma regra simples, mas desempatando pela negociação mais nova | +7% no 3º trimestre e −3% no 4º: uma regra simples bem feita chega perto |
| As mesmas negociações que a ferramenta mantém na lista, ordenadas só pelo preço | A ordem preço × chance rende +14% no 3º trimestre e +20% no 4º, em 24 de 24 semanas. Ou seja: não é só ordenar por valor |
| A regra simples com outros cortes de idade (45, 60, 75, 100, 120 e 138 dias) | A ferramenta fica à frente em todos, de +3% (75 dias, 4º trimestre) a +35% (45 dias, 4º trimestre) |
| Negociações tiradas da lista de ligação que foram ganhas depois | 0 de 801 |
| Ganho por faixa de chance | Alta 42,5%, média 21,4%, baixa 2,4% |

### Recomendações

1. **Limpar o pipeline por regra, antes de qualquer ferramenta:** encerrar no CRM
   o que passou de 138 dias. Resolve a maior parte de "tempo em deal que não
   fecha" e corrige a previsão de receita.
2. **Tornar a empresa obrigatória ao iniciar uma negociação.**
3. **Usar a ferramenta como rotina diária e como registro de contato**, que é o
   dado que falta para saber o que está esfriando.
4. **Rodar o piloto de um trimestre** com grupo de controle e decidir com
   critério definido antes: manter, ajustar ou desligar.
5. **Investigar a queda na entrada de negociações** e por que o Central não tem
   pipeline vivo. Se for real, o problema maior é gerar pipeline, não priorizar.

### Limitações

- O teste prova que a ferramenta **aponta** melhor para onde a receita vai cair,
  não que **usá-la** faz cair mais.
- Não há evidência de que os vendedores gastavam tempo nas negociações mortas:
  799 das 801 tiradas da lista nunca foram fechadas por ninguém.
- A lista de hoje não pode ser validada, porque a base termina de um jeito
  diferente do resto do ano.
- **Uma boa regra simples chega perto da ferramenta na ordem.** Contra "o mais
  caro primeiro e, no empate, a negociação mais nova", a ferramenta rende +7% no
  3º trimestre e −3% no 4º. O ganho que não depende de comparação é o corte.
- As 24 semanas do teste se sobrepõem (a mesma negociação aparece em várias):
  "ganhou em 14 de 14" não são 14 provas independentes. Medindo sem repetir
  negociação, a diferença para a regra simples é +10% no 3º trimestre e −5% no 4º.
- Das 128 negociações com chance, 91 não têm a empresa preenchida no CRM. A
  ferramenta avisa na ficha, mas é o vendedor que precisa descobrir quem é.
- O percentual de chance erra (37% previsto contra 7% real numa das faixas), por
  isso a tela mostra faixas.
- "Sem contato" depende do que o vendedor registrar; os registros ficam no
  navegador, sem senha.
- Com 35 vendedores, um piloto não consegue provar +10% de receita.
- A reativação e os prazos de retorno são apostas de negócio, sem dado por trás.

A lista completa está em [solution/README.md](solution/README.md).

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usei |
|---|---|
| Claude Code (app desktop) | Leitura do repositório e dos critérios, análise dos dados, construção do código e das telas, testes no navegador |
| Subagentes do Claude Code | Verificações independentes, com scripts e saídas em [docs/analises/](docs/analises/): duas auditorias, busca de sinais nos dados, advogado do diabo, alternativas, plano de medição e verificação final da lógica. Antes do envio, mais três revisões: o feedback dado a outros candidatos, um avaliador e a aderência ao enunciado. Houve também uma pesquisa de mercado, que ficou só na conversa, sem artefato no repositório |

### Workflow

1. Pedi à IA que lesse o repositório inteiro e procurasse o que não estava
   escrito: ela achou, por exemplo, que o `.gitignore` ignora `submissions/`.
2. A IA começou a construir sozinha. Eu parei: se ela decidisse a lógica, o
   trabalho não seria meu. Passamos a uma decisão de negócio por vez.
3. Defini as regras de reativação, o registro de tudo, os perfis, a confirmação
   e o fluxo de retorno.
4. A tela passou por nove versões: rejeitei seis inteiras e pedi ajustes nas outras até chegar na tabela com resumo do dia (prints
   de v1 a v9 em `process-log/screenshots/`).
5. Pedi uma auditoria contra o enunciado. Ela achou que a chance mostrada estava
   errada e o cálculo foi refeito.
6. Pedi verificações independentes da tese ("resolve ou mascara?") e a IA
   conferiu por conta própria os números de cada relatório.
7. Reposicionei a entrega com o que as verificações mostraram.
8. Antes de enviar, pedi um ensaio do zero (a submissão copiada para uma pasta
   vazia, rodando tudo o que o README promete) e três revisões independentes.
   O ensaio achou scripts de apoio que só rodavam na minha máquina; as revisões
   acharam números desatualizados neste README e uma frase que subestimava a
   própria lógica. Depois, um QA por recálculo mostrou que o teste histórico
   exagerava a vantagem da ferramenta por causa do desempate; refiz o teste e
   reescrevi as afirmações (decisões 39, 40 e 41).
9. Por último, reabri uma decisão minha. Eu tinha mantido a fila do dia inteira
   numa lista só; dois revisores mostraram que, para metade do time, isso
   misturava ligações que valem dinheiro com dezenas de mensagens sem chance
   medida (um vendedor abria com "0 de 169"). Pedi a recomendação da IA e
   separei a fila em meta do dia e "se sobrar tempo" (decisão 42).

**Quem fez o quê.** A análise dos dados, o código e as verificações foram
executados pela IA. As regras de negócio, as rejeições de tela e as perguntas
que mudaram o rumo ("isso não tira a minha parte lógica?", "resolve ou
mascara?", "vamos focar em algo que funcione") foram minhas. O registro de
decisões foi redigido pela IA durante a sessão, com as minhas falas transcritas
como escrevi, erros de digitação incluídos; a conversa está em
`process-log/chat-exports/`.

### Onde a IA errou e como corrigi

| Erro da IA | Como apareceu | Correção |
|---|---|---|
| Começou a decidir a lógica sozinha | Eu questionei: "isso não tira a minha parte lógica?" | Uma decisão por vez, registrada com as minhas palavras |
| Chance calculada só pela idade | Auditoria que eu pedi: previa 33% onde nenhuma de 201 foi ganha | Recalculada pelo mesmo ponto dos trimestres anteriores |
| Teste com comparação fácil e datas favoráveis | Auditoria independente | Refeito em 24 semanas contra uma regra simples justa; a vantagem caiu de "15% a 43%" (número da versão antiga, que não existe mais no código) para 10% a 13% |
| Dava 49% de chance às não iniciadas | Auditoria independente | Ficaram sem chance e sem score |
| Afirmou "0 de 12.886 negociações" | Verificação independente: são 801 distintas | Texto corrigido |
| Ideia de medir "esfriando" por queda em duas semanas | A própria IA testou e não se sustentou | Descartada; substituída por "pode fechar este mês", validada |
| Seis layouts que eu rejeitei inteiros, e ajustes em mais três | Uso da tela | Tabela tipo CRM, escolhida entre três esboços |
| Escreveu que "o preço domina e a chance só acrescenta o corte" | Duas revisões independentes mediram que, dentro do corte, a chance também melhora a ordem | Frase corrigida e a comparação incluída no teste histórico |
| O teste desempatava as regras de comparação pela ordem do arquivo, que põe a negociação mais velha primeiro: o pior caso para a regra simples | QA por recálculo, que pedi antes de enviar; refiz a conta e confirmei | Desempate por sorteio. A vantagem sobre a regra simples caiu de "+13% e +10%" para +9% e +3%, e a comparação "+19% e +41%" para +14% e +20%. O README passou a dizer onde a ferramenta empata |
| Mandava "Ligar" para negociação sem empresa, sem avisar | Revisão independente: 91 das 128 com chance não têm empresa | Aviso na ficha, com o código para localizar no CRM |
| Taxa de resposta de 200%; contador do menu errado; filtro invisível | Testes no navegador e verificação independente | Corrigidos |
| Pôs "pode fechar este mês" no topo da fila, ordem diferente da testada | Advogado do diabo: essa ordem perdia da regra simples (-1,6% na medição dele; a ordem não existe mais no código) | A fila voltou à ordem testada; o aviso ficou só como rótulo |
| Sugeria desconto com base na variação do valor fechado | Advogado do diabo: o valor varia igual para cima e para baixo da tabela | Referência removida |

Nem tudo que os subagentes disseram se confirmou: uma auditoria afirmou que a
ferramenta perdia em 8 de 10 semanas do 4º trimestre, e ao refazer a conta ela
ganhava em 7 de 10.

### O que eu adicionei que a IA sozinha não faria

- **Reativar em vez de descartar.** A IA propunha uma lista de "reativar ou
  encerrar". Eu defini mensagem com condição especial, os mais caros primeiro, e
  só para negociações recentes, porque insistir depois de meses irrita o cliente.
- **Medir tudo.** O registro de contatos, que virou o mecanismo para saber o que
  está esfriando, foi exigência minha.
- **Governança.** Um vendedor não pode ver a carteira do outro.
- **Confirmação e anotação** em cada registro, e o fluxo de "o que acontece
  depois do clique".
- **Não encerrar por telefone mudo.** A IA mandava a negociação para "Encerrar"
  depois de três ligações sem resposta. Eu defini que antes vem uma mensagem
  para confirmar o interesse, e só o silêncio nos dois canais encerra.
- **A pergunta "isso resolve ou mascara?"**, que levou ao reposicionamento.
- **Tratar o caso como um cliente**, e não como uma prova.
- Rejeitei a ideia, que era minha, de usar um modelo de linguagem para
  "enriquecer" os leads, depois de entender que as empresas da base são
  fictícias e ele inventaria os dados.

---

## Evidências

- [x] [process-log/decisoes.md](process-log/decisoes.md): as decisões numeradas, com as minhas falas transcritas e um resumo de cinco minutos no topo
- [x] [process-log/screenshots/](process-log/screenshots/README.md): prints das versões da tela (v1 a v9) e da versão final rodando
- [x] [docs/exemplos/](docs/exemplos/README.md): saídas da solução para conferência
- [x] [process-log/chat-exports/sessao-claude-code.md](process-log/chat-exports/sessao-claude-code.md): a conversa com o Claude Code, gerada por `exportar.py` (o cabeçalho do arquivo diz até que horário ela vai)
- [x] Análises de apoio e scripts de verificação em [docs/analises/](docs/analises/), todos rodando com caminhos relativos
- [x] Plano de adoção e de medição de resultado em [docs/plano-de-piloto-e-adocao.md](docs/plano-de-piloto-e-adocao.md)
- [x] Testes automatizados em [solution/tests/](solution/tests/)

---

**Tempo de trabalho:** três blocos. O primeiro, de construção, das 20h48 de
17/11/2026 à 1h16 de 18/11 (cerca de 4 horas e meia de conversa). O segundo,
entre 11h40 e 13h15 de 18/11, foi a IA executando o QA e as correções que eu
tinha pedido no fim do primeiro bloco (decisão 41). O terceiro, a partir das
18h48 de 18/11, foi a separação da fila de Hoje (decisão 42), com novos testes
e prints, e depois os commits, o envio e a demo (decisão 43). Os horários de cada mensagem estão na conversa exportada.

_Submissão enviada em: 18/11/2026_
