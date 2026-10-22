# Onde a IA errou e como foi corrigido

Usei o Claude Code (Opus 5.5) do começo ao fim. Abaixo, cada erro dele que mudou alguma coisa no projeto, quem percebeu e o que foi feito. No final, os erros que foram meus.

| # | O erro | Quem percebeu | Como foi corrigido |
|---|---|---|---|
| E1 | Escreveu os 80 tickets de teste com produtos e canal que não existem no Dataset 1 (geladeira, sofá, vestido, WhatsApp) | Eu, perguntando se aquilo fazia sentido com os dados | Tickets refeitos só com tipos, assuntos, produtos e canais do D1. O script passou a conferir sozinho ([D06](decisoes.md#d06--os-tickets-de-teste-ficam-presos-à-estrutura-do-dataset-1)) |
| E2 | Escreveu na D01 que a ideia de conferir cada achado nos dados tinha sido minha. Foi dela | A própria IA, relendo antes de me entregar | Corrigido nos dois documentos pra ficar fiel a quem decidiu o quê |
| E3 | Sugeriu "resumo pro atendente" pra uma compra de R$ 3.200 que o cliente não fez (B02). Contradizia a própria armadilha que ela escreveu, que tratava o caso como urgente | A comparação entre meu gabarito e as armadilhas | Virou D, e a regra R10 (urgente sem processo vai pra pessoa) |
| E4 | Primeira tela num estilo editorial, de jornal. Diferente, mas confusa pra um atendente | Eu, olhando a tela | Refeita do zero com foco em função ([D08](decisoes.md#d08--uma-tela-que-o-atendente-entende-com-o-inbox-que-eu-já-uso)) |
| E5 | Pus o chat numa gaveta lateral, quando o atendente precisa de um inbox | Eu, mostrando o inbox do meu sistema | Reestruturado em Fila, Conversas e Painel |
| E6 | A trava deixava passar "Posso te dar um desconto" e "a culpa é nossa" | O teste da trava ([`testar_trava.py`](../solution/motor/testar_trava.py)) | Padrões novos, e a trava passou a ignorar negação ("não é normal" passa) |
| E7 | No motor, o T05 ("o iPhone queimou") saiu como resposta automática. O leitor só pegava "queimou meu" | O teste do motor contra o gabarito | Corrigido. Mas corrigido olhando o próprio teste, o que torna o 80 de 80 inútil como prova (ver E8) |
| E8 | O leitor por palavra-chave acertou 80 de 80 nos tickets usados pra escrever as regras, e só 16 de 30 em tickets novos, com 7 erros perigosos. Dois graves: um carregador derretendo e uma compra que o cliente não fez iam receber resposta automática | O teste com tickets que o sistema nunca viu ([D09](decisoes.md#d09--medir-em-tickets-que-o-sistema-nunca-viu)) | Não foi corrigido no código de propósito, pra o número continuar honesto. Mudou a arquitetura proposta: um modelo lê o texto, as regras decidem e a trava confere ([proposta](../solution/04-proposta.md)) |
| E9 | No começo, contou 6 entregas com vídeo. Eram 10, porque faltavam os links do Drive | O script de levantamento, quando rodou de novo | Número corrigido no documento |

## Os erros que foram meus

| O erro | Como percebi |
|---|---|
| Achei que 59% dos tickets estavam como "outros", sem tipo | A IA mostrou que era a tela do Kaggle juntando categorias |
| Marquei a bateria estufada com cheiro de queimado (T04) como "o robô responde" | A comparação com as armadilhas. Virou a regra R9 |
| Em 3 tickets, meu gabarito batia de frente com a lei do consumidor e com os processos (T01, B01, R12) | A base de processos. Decidi que vale a base |

## O que aprendi com isso

O erro mais caro do projeto (E8) não apareceria se eu tivesse parado no 80 de 80. O teste que importa é o que a IA não viu. E os erros que eu peguei olhando (E1, E4, E5) a IA não pegaria sozinha, porque fazem sentido no texto e só ficam errados quando alguém olha com o contexto do usuário.

## Depois do teste: E10

| # | O erro | Quem percebeu | Como foi corrigido |
|---|---|---|---|
| E10 | O motor desobedecia o próprio princípio da política. Quando nenhuma regra disparava, ele respondia sozinho só por causa do tipo do ticket. Foi por esse buraco que passaram o carregador derretendo e a compra não reconhecida | Eu, perguntando se precisava mesmo baixar um modelo | Versão 2 do decisor: só responde sozinho quando reconhece um processo escrito. Na dúvida, pessoa. Nos 30 tickets novos, agora já vistos e portanto **sem valer como teste cego**: 21 de 30 e 1 erro perigoso, contra 16 e 7 no teste cego oficial |
