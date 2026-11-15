# Revisão final da entrega (5 revisores e 1 verificador, 31 achados, 26 confirmados)

> Com o app, os documentos e as evidências prontos, cinco revisores independentes leram a entrega, cada um por uma lente: regras do desafio, fatos e números, instalação do zero, avaliador cético no navegador, e privacidade e texto. Um sexto agente tentou refutar cada achado. Saída bruta de agentes de IA, sem edição além da remoção de caminhos locais. Cada achado guarda o número com que saiu dos revisores (#0 a #30); a lista de confirmados está em ordem de gravidade. No fim de cada um, o que foi feito.

## Revisor: regras-do-desafio

**Resumo do revisor.** A entrega cumpre as exigências duras do desafio. O app roda e usa os CSVs reais (copiados em solution/data). O score não é só valor: é chance × preço, e cada deal mostra o porquê. Há filtro por vendedor, gestor e regional (bônus). O README traz setup, lógica, limitações e o que falta para escalar, e o process log é extenso. Conferi rodando numa cópia em pasta temporária: 189 testes OK, verify.py com 189 de 189. A API em :8077 bate com o README (#LFI3BGEE na posição 1, 85 abertos, 47 sem desfecho, US$ 146.909; prova com +22,2% e +41,8%, 659 listas; Máquina do tempo com 5 vendas e US$ 25.687). O README segue as seções e a ordem do template; o único acréscimo é a subseção "Para ver em um minuto", que ajuda. A branch é submission/rodrigo-costa e nada fora da pasta foi alterado (git status sem mudanças fora de submissions/). A entrega não depende de nada fora da pasta: o caminho ../../../solution/data dos scripts aponta para dentro dela. Os problemas estão na evidência do processo e no tamanho dos textos. Faltam as respostas da IA, embora "Chat exports" esteja marcado. A frase "na íntegra" não bate com o arquivo de mensagens. O tempo gasto não aparece, num escopo muito acima de 4 a 6 horas. O README tem 3.548 palavras, com o process log repetido. Lembrete fora dos arquivos: o PR ainda precisa ter o título "[Submission] Rodrigo Costa — Challenge 003".

**Achados: 7**

## Revisor: fatos-e-numeros

**Resumo do revisor.** Conferi os números e as afirmações de fato dos quatro documentos (README.md, process-log/README.md, docs/contribuicao-do-rodrigo.md e docs/README.md). Usei a API viva em 8077 (proof, seller, team com e sem gestor, data-quality, score-model, time-machine, login, meta, sources e account Mathtouch), o verify.py (189 de 189; com --json, total 189 e ok 189) e o unittest (Ran 189 tests, OK; test_web.py tem 5, os outros 184). Também recalculei direto dos CSVs com python3 -I e rodei hyp.py, regmatch.py, trunc.py, leak.py e mock.py. Quase tudo bate. As quatro linhas da tabela da prova batem: 6.994.434, 5.822.827, 5.723.131 e 4.932.579, com 1.437,6, 1.069,3, 1.053,1 e 879,7 vendas e 659 listas. Também batem +22%, +42%, +30% e +10%, o -1%, 20 de 22 (30 out e 6 nov) e o teto de 13.039.226. Na tabela "O que a base esconde" batem 1.185, 1.425 de 2.089 (68%), 1.078 de 2.078 (52%), 31,8% e 94,6% de regional, 549/0 e 750/404, 673+1.015+1.750=3.438, 81% e 52%, 138 dias, e 779 de 2.078 (37%). Daniell bate: 85 abertos, 47 sem desfecho, US$ 146.909 de 253.368, 103/70 = 59,5% e 46,8%, #LFI3BGEE score 98, 391/196, US$ 2.748, 2%. Rocco bate: 824.840, 438.104, 53%. A Máquina do tempo bate: 27 dias, 5 vendas e US$ 25.687 contra 0, 3/6/4,3. A tabela de chance bate (17%, 6%, 50%, janela de 61 a 105 dias). Medianas: 39 a 52 dias, GTK 500 com 69 dias e 9 vendas; 47,5 vira 48, arredondamento coerente. Os terços de faturamento (63,2/63,0/63,2) e os quartis do hyp.py (64,4/61,2/64,6/62,5) batem. Também batem 22,3% e 3,6%, 59,5% e 60,9%, a conferência independente (4.924.037, 1,421 e 1,225, +11%, 20 repetições, diferença abaixo de 0,3%) e o controle negativo (35 diferenças). Nas revisões, as contagens batem com os arquivos: 03 tem 36 achados (4+3+16+13), 32 corrigidos e 6 mantidos; 04 tem 37 (11+14+12); 05 tem 38 (13+12+13), 31 corrigidos e 8 mantidos. A recontagem às cegas deu 33.505 de 33.507. Todos os caminhos citados existem: 10 capturas em docs/app, 12 PNG e o PDF em docs/ux, os 16 scripts de análise, e no código a classe Snapshot, rate_with_stale, sources() com "manter a redação", messages e signals. As citações do candidato batem com prompts-do-rodrigo.md, e no alerta só o acento de "vêm" mudou. O git log mostra os 4 commits citados, de 069da76 a ab211ef. Não achei contradição de número entre os quatro documentos. Sobraram só dois exageros pequenos de redação sobre o processo.

**Achados: 2**

## Revisor: instalacao-do-zero

**Resumo do revisor.** Seguindo o README ao pé da letra, tudo funciona de primeira na cópia limpa. Testei com Python 3.9.6, o único disponível na máquina. Não havia 3.12, então essa versão foi checada só por varredura de código. O servidor sobe com "Lead Scorer rodando em http://localhost:8131 (Ctrl+C para encerrar)". A raiz responde 200 text/html. Também funciona com outro diretório de trabalho: subi por engano um servidor na 8000 a partir de /tmp, e /api/meta respondeu 200; esse processo já foi encerrado. /health e as 12 rotas do API.md respondem 200 com JSON válido, em 1 a 6 ms depois do warm-up. Os casos de erro batem com o documentado: nome inexistente dá 400, data 2017-12-05 ou "xx" dá 400, combinação gestor e regional impossível dá 400, rota desconhecida dá 404, POST dá 405 com Allow e Connection: close, e linha inválida dá 400 em JSON. Os caminhos com ../ e %2e%2e voltam 404, e arquivo oculto não é servido. O index.html carrega 14 CSS e 8 módulos JS. Os 10 views mais o foco/rows.js são carregados por import dinâmico. Todos respondem 200 com content-type certo, e nenhum import aponta para arquivo ausente. No navegador, /#/foco?como=Daniell Hammack, /#/time?como=Rocco Neubert e /#/maquina-do-tempo?desfecho=revelado renderizam sem nenhuma mensagem no console. verify.py deu "189 conferências, 189 bateram" em 2,2 s. unittest rodou 189 testes, OK, em 6,3 s (8,4 s de parede). Com -W error -X dev não houve aviso, nem com POST com corpo nem com linha inválida. Na varredura de compatibilidade não achei match/case, X | Y avaliado em runtime, datetime.UTC, tomllib, zip(strict=), utcnow, cgi nem distutils. As anotações list[str] e dict[...] de tests/test_web.py ficam sob from __future__ import annotations. No Docker, o COPY leva data/ e web/. tests/ fica de fora de propósito, e __pycache__ e .DS_Store também. HOST=0.0.0.0 e PORT vêm do ambiente, e SIGTERM é tratado. O healthcheck /health existe e não depende da base. Os arquivos chegam com permissão 644 e o processo não escreve em disco, então o usuário app consegue ler tudo. Sem internet, a fonte cai para system-ui pelo --font-sans. A CSP é coerente: script só de 'self', estilo de 'self' e googleapis, fonte de gstatic, imagem de 'self' e data: (favicon), e não há handler inline nem eval. O único problema sério é o .gitignore da raiz, que ignora toda a pasta submissions/. Matei só as portas 8131 e 8132 e a 8000 que abri por engano; a 8077 segue no ar. Apaguei a cópia limpa.

**Achados: 3**

## Revisor: avaliador-cetico

**Resumo do revisor.** Fiz o roteiro completo no navegador em 127.0.0.1:8077, com localStorage limpo para simular um avaliador novo. Passos: login como Daniell Hammack; deal #LFI3BGEE (score 98, 50%, 196 de 391), marcar como tratado (1 de 16), copiar resumo (aviso "Resumo copiado"); abas Mornos (17), Frios (5) e Sem desfecho (47), onde marquei Encerrar (1 de 47, refletido no Pipeline). Depois Pipeline, Clientes (Mathtouch, três abas), Máquina do tempo (revelado: score com 5 vendas e US$ 25.687, valor com 0; semana anterior funciona), Como o score funciona, Como chegamos aqui, Qualidade dos dados e Fontes de dados (botões Conectar com aria-disabled). Em seguida, Rocco Neubert: filtros Regional Oeste, Gestor Celia Rouche e Vendedor Vicki; três leituras; mensagem pronta; links da pauta. Troquei a data para 25 dez e 3 jul. Testei os atalhos ?como= e a largura de 375px: não há rolagem horizontal em nenhuma tela. Console sem nenhuma mensagem e todas as chamadas /api com 200. Conferi contra o CSV: 31,8%/94,6% de regional, 2.078 = 1.299 + 779, somas do time (824.840 e 438.104) e os 189 de 189 do verify. Tudo bate.

Nada quebrou, travou ou ficou vazio. Os números são coerentes entre as telas e o README. O vendedor entende o porquê: chance, base de casos e o que fazer, em cada deal. Os problemas são de acabamento: links que prometem mais do que entregam, conta de pontos que não fecha na tela e um rótulo "Quente" que pode enganar.

Primeira crítica na banca: "Quente" e score 100 são posição relativa, não chance. Em 3 jul, o score 100 tem 18% de chance e o time tem "72 deals quentes" para US$ 48 mil esperados. O preço domina a fila.

Nota franca: 8/10. É software de verdade, explicável e verificado, acima do que o desafio pede. Perde pontos pela densidade de texto, por alguns toques de enfeite (toggle de leituras) e pelas pequenas inconsistências abaixo.

Observações de processo:
- Outro agente estava usando o painel do navegador: a aba tab-7 foi levada para 127.0.0.1:8131 no meio do teste. Continuei numa aba própria (tab-8).
- O localStorage do 8077 é compartilhado entre as abas. Ele já trazia estado de outra sessão: data 4 set e "revelado". Ao terminar, restaurei os 4 valores originais.
- Nenhum arquivo da entrega foi alterado.

**Achados: 11**

## Revisor: privacidade-e-texto

**Resumo do revisor.** Privacidade está limpa. Rodei grep -rI na pasta inteira, sem __pycache__ e sem os CSVs, e não achei e-mail, telefone, caminho /Users, /private ou C:\, nome do empregador, chave, token nem nome de outro candidato. As saídas brutas em process-log/evidencias/revisoes/ também não trazem caminho local. O único identificador é a URL do fork público (github.com/rodrigopiffer/...) citada literalmente em prompts-do-rodrigo.md:9, e isso é aceitável.

Links e caminhos estão bons. Todo link relativo e todo arquivo citado em README.md, process-log/README.md, prompts-do-rodrigo.md, docs/*.md e solution/API.md existe. As 3 imagens do README existem e têm entre 326 e 356 KB. Não há .DS_Store, __pycache__ nem arquivo temporário. O único arquivo vazio é solution/tests/__init__.py, que é normal. Acima de 500 KB só aparecem docs/ux/estudo-de-ux.pdf (2,6 MB) e solution/data/sales_pipeline.csv (623 KB). Tamanhos (du -sh): total 11M, docs 9,4M, solution 1,4M, process-log 472K.

Markdown está bem formado. Tabelas têm colunas consistentes, blocos de código fecham e os títulos seguem a hierarquia.

Acentuação está correta nos documentos, no front e no motor. Os erros de grafia que aparecem estão só nas citações literais do candidato.

O achado mais grave está fora do texto: o .gitignore da raiz do desafio ignora submissions/. Todos os arquivos novos desta entrega estão marcados como ignorados (!!). Um git add comum não leva nada para o commit nem para o deploy.

O resto são inconsistências de texto pequenas, listadas abaixo.

**Achados: 8**

## Verificador

Conferi os 31 achados nos arquivos, no git (só leitura), na API viva em 127.0.0.1:8077 e numa subida do server.py com a porta ocupada (não sobrou __pycache__). O mais grave é o #9: o .gitignore da raiz ignora submissions/, então um git add sem -f grava só as exclusões da tentativa antiga. O #23 repete o #9. Também confirmei: links "Ver a conta" que levam a uma tela sem a conta (#12), diferença de pontos que não bate com as taxas arredondadas (#13), "mesmos números" na Máquina do tempo contra "muito próximos" no README (#16; o #24 repete), link "Ver os 47" num card que fala de 10 (#18) e atalhos do README sem &data= (#22), entre outros de texto. Refutei o #19: a nota fica dentro da coluna Prospecção e já diz que a lista é a do fim da base. Refutei o #20: o texto é do próprio candidato, escrito no estudo do Paper (revisão 05:203). Duplicados: #23 (do #9), #24 (do #16) e #26 (do #5). Nenhum achado caiu nas pendências já conhecidas.

## Achados confirmados (26) e o que foi feito

### #9 [critico] Todos os arquivos novos da entrega estão ignorados pelo .gitignore do repositório

- **revisor:** instalacao-do-zero
- **onde:** .gitignore:16 (regra "submissions/")
- **detalhe:** O .gitignore da raiz do desafio tem a linha "submissions/". Rodei `git check-ignore -v` em server.py, engine/core.py, web/index.html, web/assets/js/core/api.js e .dockerignore. Todos voltaram ".gitignore:16:submissions/". `git status --short --ignored submissions/rodrigo-costa` marca com "!!" (ignorado) o README.md, docs/, process-log/, server.py, engine/, web/, tests/, verify.py, API.md, Dockerfile e railway.json. Hoje o git só rastreia os arquivos da tentativa descartada (app.py, leadscorer/, static/ e os outros), que aparecem como "D", e os CSVs de data/. Um `git add .` ou `git add submissions/rodrigo-costa` sem -f grava só as exclusões. A PR iria sem o app, e o avaliador que clonar não teria nada para rodar. Os CSVs já rastreados continuam no índice.
- **prova do verificador:** O .gitignore da raiz tem 'submissions/' na linha 16. 'git check-ignore -v' em README.md e solution/server.py devolve '.gitignore:16:submissions/'. 'git status --short --ignored' mostra '!!' em README.md, docs/ etc. e ' D' nos arquivos da tentativa antiga. 'git ls-files submissions/rodrigo-costa | wc -l' = 20.
- **o que foi feito:** Sem mudança de arquivo. O commit da entrega precisa de `git add -f`; fica registrado para a hora do commit, que depende do candidato.

### #0 [alto] Chat exports marcado, mas só há as mensagens do candidato

- **revisor:** regras-do-desafio
- **onde:** README.md:213; process-log/README.md:10; process-log/prompts-do-rodrigo.md:3
- **detalhe:** O README marca [x] Chat exports e aponta para prompts-do-rodrigo.md. O próprio arquivo diz: "As respostas da IA não estão aqui"; o process-log/README.md:10 diz o mesmo da conversa principal. O guia descreve Screenshots como "seus prompts e as respostas" e Chat export como "Export da conversa". Screenshots, gravação e git history ainda estão pendentes. Assim, nenhuma resposta da IA na conversa principal pode ser vista em primeira mão. As saídas brutas dos revisores existem, mas cobrem só as revisões. O avaliador lê um resumo feito pela própria IA, que é a forma mais fraca de evidência.
- **prova do verificador:** README.md:213 marca '[x] Chat exports: minhas mensagens na íntegra'. prompts-do-rodrigo.md:3 diz 'As respostas da IA não estão aqui'. process-log/README.md:10 diz 'As respostas da IA na conversa principal não foram anexadas'. Não há export da conversa com as respostas da IA.
- **o que foi feito:** O README passou a dizer que o export tem só as mensagens do candidato e que as respostas da IA estão resumidas, não exportadas. Exportar a conversa inteira fica para o candidato decidir.

### #1 [medio] "Na íntegra" não bate: a lista para no início do desenvolvimento

- **revisor:** regras-do-desafio
- **onde:** README.md:158 e 213; process-log/README.md:106; process-log/prompts-do-rodrigo.md (última mensagem)
- **detalhe:** A última mensagem do arquivo é "Pode iniciar o desenvolvimento". O próprio log descreve etapas posteriores: fluxo da interface, três revisores, teste final no Chrome, checagem dos documentos (revisoes/04 e 05), deploy preparado e ajustes de texto. Nenhuma instrução dessas etapas aparece. Se o candidato mandou mensagens depois do início do desenvolvimento, "na íntegra" é falso, e é fácil de contestar quando o export ou o git aparecerem. Não consegui confirmar se houve mensagens depois; vale conferir.
- **prova do verificador:** A última mensagem de prompts-do-rodrigo.md é '> Pode iniciar o desenvolvimento' (14 nov). As linhas 10 e 11 da tabela do process-log não têm pedido do candidato ('—'). Mas houve trabalho depois a pedido dele: a revisão 04 dos documentos, o teste no Chrome e esta própria rodada de revisão. Esses pedidos não aparecem no arquivo, então 'na íntegra' (README.md:158 e :213, process-log/README.md:106) não se sustenta.
- **o que foi feito:** A mensagem enviada depois do início do desenvolvimento ("terminou?") foi acrescentada a `process-log/prompts-do-rodrigo.md`. Não houve outras.

### #2 [medio] Tempo gasto não declarado, num escopo muito acima de 4 a 6 h

- **revisor:** regras-do-desafio
- **onde:** README.md (Process Log) e process-log/README.md:5
- **detalhe:** O desafio diz "Time budget: 4-6 horas". O README do repositório diz que soluções de 40 horas não ganham pontos extras e que contam a "inteligência no uso do tempo". A entrega tem dois dias de trabalho, 10 telas, 12 pranchas, fluxo de 13 agentes, cinco rodadas de revisão (38.397 palavras de saída bruta) e 189 testes. Busquei "hora" e "horas" e não há menção ao tempo de mão de obra do candidato. Sem esse número, o avaliador tende a supor que o tempo estourou muito.
- **prova do verificador:** grep -i 'horas' no README.md e no process-log/README.md: nenhuma menção ao tempo de trabalho do candidato. Só aparece 'tempo de fechamento'. A auditoria 02 já alertava para o estouro das 4 a 6 h.
- **o que foi feito:** O README ganhou a linha de tempo gasto, com o número de horas para o candidato preencher (a IA não sabe esse número).

### #3 [medio] README longo e repetido (3.548 palavras)

- **revisor:** regras-do-desafio
- **onde:** README.md:156-205 (Process Log), 59-129 (Resultados), 141-152 (Limitações), 215 (Evidências)
- **detalhe:** O guia penaliza "Documento de 40 páginas onde 5 resolveriam". Contagem por seção (wc): Process Log no README com cerca de 960 palavras, quase cópia do process-log/README.md. "O que eu adicionei" aparece três vezes: README, process-log e docs/contribuicao. A prova tem 390 palavras e o score 338. A armadilha do cliente aparece 4 vezes (linhas 64-65, 136, 147 e na tabela). "Mede a ordem, não o efeito" aparece 3 vezes (103, 138, 145). A linha 215 tem um parágrafo inteiro dentro de um checkbox.
- **prova do verificador:** wc -w README.md = 3548. 'Mede a ordem' aparece em README.md:103 e de novo em :145. A linha 215 é um parágrafo inteiro dentro de um checkbox. O Workflow (:170-181) repete o process-log/README.md.
- **o que foi feito:** O bloco de process log do README foi encurtado (workflow em 6 passos, erros e contribuições resumidos, evidências em lista) e as repetições das limitações saíram. O README continua com cerca de 3.400 palavras: o que sobrou é setup, lógica, prova e limites.

### #12 [medio] "Ver a conta" da taxa de ganho abre uma tela que não tem essa conta

- **revisor:** avaliador-cetico
- **onde:** Foco da semana (Insights da Gabi, card INDICADOR) e Meu time (Pauta da Gabi, INDICADOR); solution/engine/seller.py:322 e solution/engine/team.py:198
- **detalhe:** Os dois cards falam da taxa oficial contra a real ("Hoje o CRM mostra 59,5%... fica em 46,8%"). O link "Ver a conta" aponta para #/como-funciona. Essa tela explica só a chance x preço e as faixas do score. Não traz nenhuma conta de taxa de ganho com os sem desfecho. É o mesmo tipo de "link que promete e não entrega" que o process log diz ter corrigido.
- **prova do verificador:** engine/seller.py:322 e engine/team.py:198 apontam 'Ver a conta' para 'como-funciona'. Na API /api/score-model, não há conta de taxa oficial contra real: '59,5' aparece só num sinal sobre cliente. Nenhuma outra tela (quality.py) traz essa conta.
- **o que foi feito:** O cartão do vendedor passou a trazer a conta no próprio texto ("103 ganhos em 173 deals fechados... são 103 em 220, ou 46,8%") e ficou sem link. O do gestor aponta para a coluna Taxa de ganho da tabela, na mesma tela, também sem link.

### #13 [medio] Diferença de pontos não bate com as taxas exibidas

- **revisor:** avaliador-cetico
- **onde:** Meu time, coluna TAXA DE GANHO; solution/web/assets/js/views/time.js:166-171
- **detalhe:** A diferença é calculada sobre os valores sem arredondar e as taxas aparecem arredondadas. No time do Rocco: Cassey "62,0% → 50,8%" com "11,1 pontos a menos" (a conta na tela dá 11,2); Boris "63,2% → 49,1%" com "14,0" (dá 14,1). Na regional Oeste: Kary 61,0→48,9 "12,0" (dá 12,1), Elease 61,5→47,7 "13,9" (dá 13,8), Vicki 61,4→50,7 "10,8" (dá 10,7), Rosalina 63,7→48,9 "14,9" (dá 14,8). O avaliador que faz a conta de cabeça vê erro.
- **prova do verificador:** /api/team?manager=Rocco%20Neubert: Cassey 62,0→50,8 com delta 11,1 (a conta na tela dá 11,2); Boris 63,2→49,1 com delta 14,0 (dá 14,1). Na regional Oeste: Kary 12,0 contra 12,1, Elease 13,9 contra 13,8, Vicki 10,8 contra 10,7. time.js:167 usa row.rate_delta_points sem arredondar.
- **o que foi feito:** A diferença em pontos passou a sair das duas taxas já arredondadas, para bater com o que está na tela.

### #14 [medio] "Quente" e score 100 não indicam chance alta

- **revisor:** avaliador-cetico
- **onde:** Foco da semana em 3 jul 2017 (deal #S9N98QU9); Meu time em 3 jul (MOMENTO); Frios em 4 dez
- **detalhe:** Em 3 jul, o deal #S9N98QU9 tem "Score 100" e "18% em 30 dias". A pauta diz "Começo de trimestre: 72 deals quentes no time" com só US$ 48.485 esperados. Em 4 dez, um MG Special com 35% de chance aparece em Frios (score 13). Como o score é posição relativa da receita esperada, o preço domina. Na mensagem pronta de Markita (4 dez), o primeiro deal é um GTK 500 com 134 dias, a 4 dias de virar sem desfecho. O README explica isso, mas na tela o vendedor lê "quente" como "vai fechar".
- **prova do verificador:** /api/seller?name=Daniell%20Hammack&date=2017-07-03: S9N98QU9 tem band 'quente', score 100 e chance 0,1838. O motivo explica a receita esperada, mas a faixa (engine/seller.py:329) diz só 'score 80 ou mais'.
- **o que foi feito:** A nota acima da lista do Foco passou a dizer "Ordem: receita esperada (chance × preço)". O README ganhou a frase que explica que quente não quer dizer "vai fechar", com o exemplo de 3 jul 2017 (score 100, 18% de chance).

### #25 [medio] README chama de '3.438 deals' uma soma em que o mesmo deal conta mais de uma vez

- **revisor:** privacidade-e-texto
- **onde:** README.md:66 (tabela 'O que a base esconde')
- **detalhe:** O README diz '3.438 deals abertos há mais de 30 dias (somando os dias); 0 fecharam naquele mês'. A própria API (/api/data-quality) explica '673, 1.015 e 1.750 ... (3.438 somando os dias; o mesmo deal pode contar mais de uma vez)'. A revisão 03, achado 3, apontou isso. No README, 'somando os dias' não deixa claro que não são 3.438 deals distintos.
- **prova do verificador:** README.md:66 diz '3.438 deals abertos há mais de 30 dias (somando os dias)'. A API /api/data-quality explica '673, 1.015 e 1.750... o mesmo deal pode contar mais de uma vez'.
- **o que foi feito:** Frase do README trocada pelos três números (673, 1.015 e 1.750), com o aviso de que o mesmo deal pode contar em mais de uma data.

### #4 [baixo] Executive Summary com 7 frases; o template pede 3 a 5

- **revisor:** regras-do-desafio
- **onde:** README.md:15
- **detalhe:** O template diz "Em 3-5 frases: o que você fez, o que encontrou, e qual a principal recomendação". O parágrafo tem 7 frases: Construí / O score é / A base esconde / Nenhum deal fechou / E o cliente / Em 22 segundas / A principal recomendação. É o primeiro bloco que o avaliador lê.
- **prova do verificador:** README.md:15 tem 7 frases. Começam assim: 'Construí', 'O score é', 'A base esconde', 'Nenhum deal fechou', 'E o cliente', 'Em 22 segundas', 'A principal recomendação'. O template pede de 3 a 5.
- **o que foi feito:** Executive Summary reescrito em 5 frases.

### #5 [baixo] Conta que não fecha no Workflow do README (38 achados = 31 + 8)

- **revisor:** regras-do-desafio
- **onde:** README.md:181
- **detalhe:** "três revisores independentes registraram 38 achados (31 correções, 8 itens mantidos com justificativa)": 31 + 8 = 39. O process-log/README.md:45 explica que há achado repetido e achado corrigido só em parte, mas o README não diz isso. Para um avaliador que confere números, parece erro.
- **prova do verificador:** README.md:181 diz '38 achados (31 correções, 8 itens mantidos com justificativa)', e 31 + 8 = 39. A explicação só está em process-log/README.md:45.
- **o que foi feito:** O README passou a dar só o total de achados por frente; a conta detalhada, com a explicação da soma, ficou no process log.

### #6 [baixo] Tabela de ferramentas diz "para quê", mas não "por quê"

- **revisor:** regras-do-desafio
- **onde:** README.md:162-168; process-log/README.md:14-20
- **detalhe:** O guia pede "Quais ferramentas de IA você usou e por quê". A tabela segue a coluna do template ("Para que usou"), mas não diz por que escolheu cada ferramenta. Exemplos: Paper via MCP para desenhar antes de codar; subagentes Opus para revisão independente; só biblioteca padrão para rodar com um comando, pedido no item 3 das respostas do candidato.
- **prova do verificador:** README.md:162-168: a coluna 'Para que usou' descreve só o uso. Nenhuma linha diz por que a ferramenta foi escolhida.
- **o que foi feito:** A tabela de ferramentas ganhou o porquê onde ele é fato: agentes separados para a revisão ser independente, Paper para discutir as telas antes do código, biblioteca padrão para rodar com um comando.

### #7 [baixo] Teste de vazamento descrito como 'respostas idênticas', mas a evidência registra uma diferença

- **revisor:** fatos-e-numeros
- **onde:** process-log/README.md:86 e :45 (linha 9 da tabela); README.md:180 (passo 9 do Workflow)
- **detalhe:** Os documentos dizem que o motor rodado em bases cortadas 'deu as mesmas respostas' e que 'as respostas foram idênticas'. Em process-log/evidencias/revisoes/03-revisao-do-motor-e-da-api.md (cerca da linha 76), o revisor diz: 'A única diferença foi panel.stats[0].value do login (ver achado 1)'. A extensão do teste deu 0 diferenças 'com os stats do login retirados'. A diferença virou o achado 1 e foi tratada só no rótulo (correção 12: o card agora diz que o número é da base inteira). Ou seja, havia uma diferença conhecida. Ela foi explicada e não afeta score, ordem nem prova. Comando: grep -n 'idêntic\|única diferença' na evidência 03.
- **prova do verificador:** process-log/README.md:86 diz 'as respostas foram idênticas'. A evidência 03, linha 80, diz 'A única diferença foi panel.stats[0].value do login'. A linha 82 diz '0 diferenças, com os stats do login retirados'.
- **o que foi feito:** O process log passou a registrar a única diferença do teste de vazamento (o total de 8.800 da tela de acesso).

### #8 [baixo] README diz que as 12 pranchas foram revisadas por IA, mas as revisões viram as primeiras telas

- **revisor:** fatos-e-numeros
- **onde:** README.md:53 (Abordagem, passo 5)
- **detalhe:** O README diz '12 pranchas no Paper, revisadas por IA (usabilidade e regras do desafio) antes de construir'. A evidência mostra outra coisa. Na 01-critica-das-telas.md, os três revisores 'criticaram as primeiras telas do estudo'. Na 02-auditoria-contra-as-regras-do-desafio.md, o resumo diz que o revisor 'vi as telas 01 a 04 no Paper'. O process-log/README.md:41-42 confirma: a revisão foi sobre as 5 telas, e só depois o estudo passou a 12 pranchas. Nenhum arquivo em evidencias/revisoes cobre a versão de 12 pranchas. O docs/README.md:11 é mais cuidadoso, mas também não diz que a revisão foi da primeira versão.
- **prova do verificador:** README.md:53 diz '12 pranchas no Paper, revisadas por IA'. Mas a revisão 01 cobre 'as primeiras telas do estudo' e a 02 diz 'vi as telas 01 a 04 no Paper'. Nenhum arquivo em evidencias/revisoes revisa as 12 pranchas: a 05 compara o código com o estudo.
- **o que foi feito:** README corrigido: a crítica por IA foi das 5 primeiras telas; depois o estudo passou a 12 pranchas.

### #10 [baixo] Porta ocupada derruba o servidor com traceback cru

- **revisor:** instalacao-do-zero
- **onde:** solution/server.py:302-304 (main: int(PORT) e LeadScorerServer((host, port)))
- **detalhe:** Com a 8131 já em uso, rodei `PORT=8131 python3 server.py`. A saída termina em "socketserver.py, line 466, in server_bind ... OSError: [Errno 48] Address already in use", com o traceback inteiro. A porta padrão do README é 8000, que costuma estar ocupada na máquina de quem avalia. `PORT=abc python3 server.py` também dá traceback: "ValueError: invalid literal for int() with base 10: 'abc'". O resto da experiência de subir o app é bem cuidado, e esse caso destoa.
- **prova do verificador:** Em solution/, rodei 'PORT=8077 python3 server.py' com a porta já ocupada. A saída termina em 'OSError: [Errno 48] Address already in use', com o traceback inteiro. server.py:320 faz 'int(os.environ.get("PORT") or 8000)' sem tratar erro.
- **o que foi feito:** O servidor passou a sair com uma frase (porta ocupada ou PORT inválida) e a sugestão de outra porta, sem traceback.

### #11 [baixo] Deploy no Railway depende de apontar o Root Directory para solution/, e isso não está escrito

- **revisor:** instalacao-do-zero
- **onde:** solution/railway.json e README.md:150 ("Dockerfile e railway.json estão prontos em solution/")
- **detalhe:** O Dockerfile, o .dockerignore e o railway.json estão em submissions/rodrigo-costa/solution/, dentro de um repositório com várias entregas. Sem o Root Directory do serviço configurado para essa pasta, o Railway procura o Dockerfile e o railway.json na raiz do repositório e não os acha. Aí o build falha ou cai no detector automático, e o healthcheck /health não é aplicado. Fora isso, a configuração está certa. COPY . . leva data/ e web/. CMD ["python","server.py"] com HOST=0.0.0.0 usa a PORT injetada. /health responde 200 sem depender da base. O usuário app (uid 1000) lê os arquivos com permissão 644.
- **prova do verificador:** README.md:150 diz só 'Dockerfile e `railway.json` estão prontos em `solution/`'. grep -n 'Root Directory\|root' no README, no Dockerfile e no railway.json não acha nada. O repositório tem várias entregas na raiz.
- **o que foi feito:** O README passou a dizer o Root Directory e o caminho do arquivo de configuração no Railway.

### #15 [baixo] Botões Lado a lado / Declarado / Real só mudam a cor da barra

- **revisor:** avaliador-cetico
- **onde:** Meu time, "As duas leituras, por vendedor"; solution/web/assets/js/views/time.js:227 e solution/web/assets/css/views/time.css:229-235
- **detalhe:** Alternei os três modos e o texto da tabela ficou idêntico. O cabeçalho continua "Vivo dentro do declarado" e os valores continuam "US$ 121.303 de US$ 263.367". Muda só o preenchimento da barra. Para um avaliador cético, parece enfeite: o título promete duas leituras, mas o controle não troca o número nem a coluna.
- **prova do verificador:** time.js:227: o segmented tem só aria-label 'Barra de cada vendedor', sem rótulo visível. time.css:229-235 só esconde ou recolore partes da barra. O texto e as colunas não mudam.
- **o que foi feito:** Cada leitura (Lado a lado, Declarado, Real) passou a trocar também o número e o cabeçalho da coluna, não só a barra.

### #16 [baixo] Máquina do tempo diz "mesmos números"; README diz diferença abaixo de 0,3%

- **revisor:** avaliador-cetico
- **onde:** Máquina do tempo, card "Conferida duas vezes"; solution/engine/proof.py:233
- **detalhe:** A tela diz "Uma segunda implementação... chegou aos mesmos números". O README (seção 3, Limites) diz "chegou a números muito próximos: diferença abaixo de 0,3% nos totais, porque ela desempata por sorteio". O avaliador que lê os dois vê exagero na tela.
- **prova do verificador:** engine/proof.py:233 diz 'chegou aos mesmos números'. README.md:105 diz 'chegou a números muito próximos: diferença abaixo de 0,3%'. process-log:84 dá os totais 4.924.037 contra 4.932.579.
- **o que foi feito:** Texto da tela alinhado ao README: "números muito próximos (diferença abaixo de 0,3%, por causa do desempate)", mais a menção ao script de conferência, que bate exatamente.

### #17 [baixo] "O que não entra" inclui produto, mas o preço do produto entra

- **revisor:** avaliador-cetico
- **onde:** Foco da semana, bloco expandido "O QUE NÃO ENTRA"; solution/engine/seller.py:16
- **detalhe:** O Foco diz "Cliente, setor, produto e vendedor. Foram testados nesta base e não mudam a chance." Em Como o score funciona, a linha Produto tem decisão "Entra só pelo preço", e o próprio card ao lado diz "50% de chance vezes US$ 5.482". Lido rápido, parece contradição.
- **prova do verificador:** engine/seller.py:16 EXCLUDED_TEXT = 'Cliente, setor, produto e vendedor. Foram testados nesta base e não mudam a chance.'. É exibido em foco/rows.js:93 sob o rótulo 'O que não entra'. O preço do produto entra no score.
- **o que foi feito:** Texto trocado para "Cliente, setor e vendedor: foram testados nesta base e não mudam a chance. O produto entra só pelo preço."

### #18 [baixo] Insight de GTX Plus Pro abre os 47 deals, não os 10

- **revisor:** avaliador-cetico
- **onde:** Foco da semana, Insights da Gabi, card PIPELINE
- **detalhe:** O card diz "10 dos seus 12 deals de GTX Plus Pro passaram de 138 dias." O link é "Ver os 47 deals" e abre a aba Sem desfecho inteira. O número do link não é o do título, e o filtro por produto não é aplicado.
- **prova do verificador:** Na API, para Daniell em 4 dez: o título é '10 dos seus 12 deals de GTX Plus Pro passaram de 138 dias.' e o link é 'Ver os 47 deals', com destino sem_desfecho. O número vem de _see(n) em seller.py:239, e não há filtro por produto.
- **o que foi feito:** Quando o título fala de menos deals do que o link abre, o rótulo passou a ser "Ver todos os N sem desfecho".

### #21 [baixo] "10 vendedores da regional Leste" na ficha do cliente é ambíguo

- **revisor:** avaliador-cetico
- **onde:** Clientes, ficha da Mathtouch, aba Dados
- **detalhe:** Entre os números do cliente (US$ 152.556, ticket médio, última venda) aparece "10 / vendedores da regional Leste". Não fica claro se são os vendedores que venderam para o cliente ou só o tamanho da regional.
- **prova do verificador:** clientes.js:158 mostra seller_count com o rótulo sellers_label. engine/accounts.py:224 monta '%s da regional %s' a partir dos vendedores dos deals fechados com o cliente. Na tela fica '10 / vendedores da regional Leste', sem dizer que são os vendedores que negociaram com o cliente.
- **o que foi feito:** Rótulo trocado para "vendedores com deal fechado, da regional Leste" (ou "de N regionais").

### #22 [baixo] Data simulada fica salva e os números do roteiro mudam

- **revisor:** avaliador-cetico
- **onde:** Atalhos #/foco?como=... e #/time?como=...; README, "Para ver em um minuto"
- **detalhe:** A data fica no localStorage. Ao abrir o atalho #/time?como=Rocco%20Neubert depois de trocar a data, a tela abriu em 3 jul 2017 e não em 4 dez. Também vi a tela de acesso mostrar "Em 4 set 2017, 429 dos 2.273..." com estado anterior. O roteiro do README cita números de 4 dez (score 98, 27 dias). O avaliador que mexeu na data e volta pelo atalho não encontra esses números.
- **prova do verificador:** app.js:576-590: o atalho só muda a data se vier ?data=. Fora isso, vale a data salva em localStorage (state.js:60). README.md:36 dá os atalhos sem &data=, e o roteiro cita números de 4 dez.
- **o que foi feito:** Os dois atalhos do README passaram a levar `&data=2017-12-04`.

### #27 [baixo] A mesma regra de comparação aparece com dois nomes: 'sem os parados' e 'sem os sem desfecho'

- **revisor:** privacidade-e-texto
- **onde:** README.md:97; process-log/README.md:50 e :84
- **detalhe:** O app (maquina.js:9 'Por valor, sem os sem desfecho') e a tabela do README.md:91-92 usam 'sem os sem desfecho'. Já o README.md:97 diz 'vem só de tirar os parados da frente'. O process-log/README.md:50 diz 'ordenar por valor já sem os parados' e 'sem os parados, o mais novo primeiro', e a linha 84 diz 'contra valor sem os parados'. O avaliador pode achar que são dois grupos diferentes.
- **prova do verificador:** README.md:97 diz 'tirar os parados da frente'. process-log/README.md:50 diz 'já sem os parados' e 'sem os parados, o mais novo primeiro', e a :84 diz 'contra valor sem os parados'. No app e no README.md:91-92 o nome é 'sem desfecho'.
- **o que foi feito:** "Sem os parados" virou "sem os sem desfecho" no README e no process log.

### #28 [baixo] README chama de 'agenda' o que o app chama de 'Pauta da Gabi'

- **revisor:** privacidade-e-texto
- **onde:** README.md:113 (tabela 'O que o app tem', linha Meu time)
- **detalhe:** O README diz '... taxa oficial e real por vendedor, agenda e mensagem pronta por vendedor'. Na tela, o bloco se chama 'Pauta da Gabi' (time.js:318 e :379), e a contribuição usa 'pauta do Meu time' (docs/contribuicao-do-rodrigo.md:46). 'agenda' é o nome do campo na API e vazou para o texto.
- **prova do verificador:** README.md:113 diz 'agenda e mensagem pronta por vendedor'. Na tela, time.js:318 e :379 usam 'Pauta da Gabi'.
- **o que foi feito:** "agenda" virou "Pauta da Gabi" no README.

### #29 [baixo] Número sem unidade no roteiro de validação

- **revisor:** privacidade-e-texto
- **onde:** README.md:33
- **detalhe:** O texto diz '... aparece o que aconteceu nos 30 dias seguintes (27 em 4 dez, porque a base acaba em 31 dez)'. Sem a palavra 'dias', '27 em 4 dez' parece uma data ou uma contagem de deals.
- **prova do verificador:** README.md:33 diz '(27 em 4 dez, porque a base acaba em 31 dez)', sem a unidade.
- **o que foi feito:** Frase trocada para "27 dias a partir de 4 dez".

### #30 [baixo] Frases sem verbo e com repetição na tela Como chegamos aqui

- **revisor:** privacidade-e-texto
- **onde:** solution/web/assets/js/views/chegamos.js:45 e :8
- **detalhe:** A linha 45 diz: 'A ideia de utilizar o design do G4 OS e simular o app como se fosse um módulo do G4 OS, para que sirva de ideia futura de serviço a ser entregue na plataforma.' A frase não tem verbo principal, repete 'ideia' e 'G4 OS' e destoa das outras frases curtas da tela. A linha 8 diz 'Desenho das telas e revisão por três revisores de IA.', que é redundante. Se a linha 45 for redação do candidato, como o alerta de Fontes, ignore só esse trecho.
- **prova do verificador:** Só vale para a linha 8 de chegamos.js: 'Desenho das telas e revisão por três revisores de IA.' é redundante. A linha 45 é texto do candidato (ver #20) e fica fora.
- **o que foi feito:** A linha 8 foi trocada ("crítica de três revisores de IA"). A frase "Design e ideia de entrega" é redação do candidato e ficou como está.

## Achados descartados (5)

- **#19 Nota da coluna Prospecção contradiz o README** (avaliador-cetico): refutado. engine/seller.py:372-388: a nota é exibida dentro da coluna Prospecção do kanban, então 'lista' é a própria coluna. Isso combina com o README.md:74, que diz que esses deals aparecem só no kanban. Para quem tem prospecção, o texto já diz 'A lista é a do fim da base, em ordem de valor', o que cobre a data simulada.
- **#20 Frase sem verbo em "Design e ideia de entrega"** (avaliador-cetico): refutado. chegamos.js:45 é texto do candidato. process-log/evidencias/revisoes/05-revisao-da-interface.md:203 mostra o original dele no estudo ('A idéia de utilizar o design do G4OS... G40S'), só com a ortografia corrigida. O próprio revisor deixa a decisão com o candidato.
- **#23 Arquivos novos da entrega estão ignorados pelo git e não entram no commit** (privacidade-e-texto): duplicado. É o mesmo problema do #9 (.gitignore:16 'submissions/', arquivos com '!!').
- **#24 App diz que a conferência chegou aos 'mesmos números'; o README diz 'muito próximos'** (privacidade-e-texto): duplicado. É a mesma frase de engine/proof.py:233 do #16.
- **#26 Conta de achados da interface não fecha no README** (privacidade-e-texto): duplicado. É o mesmo achado do #5 (README.md:181, 31 + 8 = 39).

## Conferência das correções (3 agentes)

> Depois das correções, três agentes independentes, só com leitura, conferiram se cada uma entrou e se alguma criou problema novo. Abaixo, o resumo de cada um e os achados, sem edição além da remoção de caminhos locais, e o que foi feito.

### Agente: correcoes

Conferi as 26 correções uma a uma. Todas entraram. Achei uma contradição nova, baixa, e uma sobra de código.
- seller.py: o cartão INDICADOR não tem link e traz a conta no texto. Rodei /api/seller para os 30 vendedores em 2017-07-03, 2017-09-04, 2017-12-04 e 2017-12-25. Nenhuma conta deixou de fechar: ganhos/fechados dá a taxa oficial, ganhos/(fechados + sem desfecho) dá a outra, e os números batem com rates. Não há link_label sem link_target. Singular e plural estão certos ("1 ganho em 1 deal fechado. Com o deal sem desfecho contado como não ganho"), conferido também com WinRecord sintético. O cartão PIPELINE diz "Ver todos os N sem desfecho" quando o título cita menos deals, e N = stale_count. EXCLUDED_TEXT foi trocado.
- O front não deixa botão vazio: gabiCard só desenha a ação se houver link_label e (href ou linkAttrs).
- team.py: o INDICADOR não tem link. A frase fica no singular no escopo de um vendedor ("A conta está na coluna Taxa de ganho."). Em time.js não sobrou código que espere 'como-funciona'.
- time.js/time.css: os três modos trocam o número e o cabeçalho (data-mode-text). A diferença sai das taxas arredondadas. Conferi Rocco e a regional Oeste em 2017-12-04: Cassey 11,2, Boris 14,1, Kary 12,1, Elease 13,8, Vicki 10,7, Rosalina 14,8. "não muda" vale para Reed e Donn. O sinal é sempre "a menos".
- accounts.py: Mathtouch mostra "vendedores com deal fechado, da regional Leste". proof.py: "Conferida duas vezes" agora diz "números muito próximos (diferença abaixo de 0,3%...)".
- server.py: com PORT=8077 (ocupada), abc, 0, 70000, ' 8001' e -1, a saída é uma frase e exit 1, sem traceback. O servidor da 8077 continuou no ar.
- README, process-log/README e prompts-do-rodrigo: todas as trocas registradas estão no texto, e o Executive Summary tem 5 frases.
- Testes: 189 OK. verify.py: 189/189. Os testes cobrem os textos novos de seller, team e accounts. Não cobrem o singular do INDICADOR do vendedor, a frase nova da prova nem as mensagens de subida do server.py. É lacuna de teste, não erro.
- API.md não ficou errado. Ele não diz que link_label e link_target podem vir null, mas isso já era possível antes.
Nada foi alterado na entrega. A pasta temporária conferencia-final foi apagado e não sobrou __pycache__.

### Agente: fatos

Achei dois problemas reais, os dois de severidade baixa. O resto bate com a API, com o verify.py, com os testes e com os CSVs.

O que conferi:
- **README:** tem 3.368 palavras (wc -w). O Executive Summary agora tem 5 frases.
- **Números do Executive Summary:** batem. 138 dias; 779 de 2.078 (37,5%, "mais de um terço"); 22 segundas; +22,2%; +10% em outubro e novembro.
- **Frase do score em 3 jul:** /api/seller?name=Daniell%20Hammack&date=2017-07-03 devolve como primeiro deal S9N98QU9, score 100, chance 0,1838, faixa quente. O trimestre está na fase "abre".
- **673, 1.015 e 1.750:** recalculei dos CSVs com python3 -I. São os deals abertos há mais de 30 dias em 1 abr, 1 jul e 1 out, e 0 fecharam em cada mês. A /api/data-quality diz o mesmo.
- **Testes e verify.py (numa cópia na pasta temporária, já apagada):** verify.py deu 189 de 189. A suíte rodou 189 testes, OK. Somei os arquivos: 184 de motor e API e 5 de test_web.py.
- **Revisões:** são 6 arquivos em revisoes/. As contagens batem: 03 com 36 achados (4+3+16+13), 04 com 37, 05 com 38, e 06 com 31 (7+2+3+11+8), dos quais 26 confirmados. Bate também "cinco revisores e um sexto".
- **Process log (linhas 10 a 12 e "Como a IA foi verificada"):** batem. Conferência independente: 4.924.037, C/A 1,421, C/B 1,225, REPS=20, top 5 e top 20, sementes, retirada de um vendedor ou de uma data. No app: 1,418 e 1,222. Diferença abaixo de 0,3%. Recontagem às cegas: 33.505 de 33.507. Teste de vazamento: a única diferença é o total de 8.800. Controle negativo: 35 diferenças. Rocco: US$ 438.104 e 824.840. Máquina do tempo: 5 vendas e US$ 25.687 em 27 dias.
- **Caminhos citados:** todos existem. São os 16 scripts, os 4 arquivos da conferência e saida-verify.txt.
- **Atalhos com &data=2017-12-04:** batem com "Endereços do app" do API.md e com applyEntryLink em app.js (como, perfil, data).
- **Capturas:** são 10 em docs/app. As 3 citadas no README existem. Em docs/ux há 12 PNG e o PDF.
- **Markdown:** blocos de código fechados (4 cercas no README, 2 no process log). As tabelas têm o mesmo número de colunas em todas as linhas. A sublista do checkbox está bem formada.
- **Correções conferidas no código:** "Ordem: receita esperada" em foco.js:207 e "muito próximos (diferença abaixo de 0,3%" em proof.py:234.

Não alterei nada na pasta da entrega e apaguei o temporário.

### Agente: regressao

Achei duas regressões pequenas. O resto passou.

O que rodei na cópia (porta 8141):
- 189 testes OK.
- verify.py: 189 de 189 bateram.
- Varredura da API: 4.184 chamadas, sem 500 e sem JSON inválido. Cobriu seller, pipeline e time-machine (26 datas × 30 vendedores); team (sem filtro, 6 gestores, 3 regionais e alguns vendedores); accounts; account (85 clientes × 3 datas × viewers); login, score-model, data-quality, proof e sources.
- Nenhum cartão tem só um dos dois campos de link.
- Nenhum texto com None, nan, %s, %d, { ou espaço duplo. Os únicos textos sem ponto final são os subtítulos de setor, que são rótulos.
- O cartão INDICADOR do vendedor fecha com rates e stale_count em todos os casos. A única divergência foi 66,25%: meu script arredondou para 66,2 e o servidor para 66,3. O servidor está certo.
- O sellers_label nunca fica vazio nem repete número (85 clientes × 26 datas), e o plural confere.
- A ordem do Foco confere com a nota "chance × preço, no empate o mais antigo": 41.127 pares, 0 fora.
- Os 19 módulos JS passam no jsc.
- time.css: as três regras de [data-mode-text] escondem os dois textos não escolhidos, inclusive no cabeçalho da tabela, que fica dentro de [data-time-mode]. Nenhuma outra tela usa data-mode-text.
- Taxa nula: não ocorre em /api/team em nenhuma data nem escopo. Se ocorresse, rateHtml cairia em "não muda".
- Restos de código: applyEntryLink, as variáveis e os seletores estão certos. O modo da tabela persiste de propósito.

As duas regressões estão nos achados: a do cartão INDICADOR do gestor eu reproduzi na API; a do ?desfecho=revelado, pela leitura do código.

Limpeza:
- A pasta conferencia-final sumiu do disco no meio da conferência. Depois disso li os JS e o CSS do original, só para leitura.
- Matei só o PID 69958 (porta 8141). O servidor da 8077 segue no ar.
- A pasta temporária não existe mais e não sobrou __pycache__ na entrega.

### Achados da conferência (6) e o que foi feito

- **[baixo] Pauta do gestor arredonda os pontos da diferença bruta; a tabela usa as taxas arredondadas** (correcoes; solution/engine/team.py:210). A correção #7 mudou só o front (time.js:172): ele calcula a diferença a partir das taxas arredondadas. O cartão INDICADOR da Pauta da Gabi continua arredondando rate_delta_points, que é a diferença sem arredondar. Varri /api/team nas 26 datas, por gestor, por regional e no escopo geral: há 66 linhas em que o inteiro do cartão diverge do arredondamento do número da tabela. Exemplo em /api/team?seller=Elease%20Gluck&date=2017-12-25: o cartão diz 'Elease perde 14 pontos de taxa de ganho...'. Na tabela, 62,9% → 48,4% aparece como '14,5 pontos a menos', e rate_delta_points = 14.46. Em /api/team?manager=Summer%20Sewald&date=2017-12-25, o cartão diz 'de 12 a 13 pontos', mas Maureen aparece na tabela com 13,5 (68,8 → 55,3). O próprio cartão manda conferir 'na coluna Taxa de ganho'. **O que foi feito:** Corrigido: o cartão passou a usar a mesma conta da tabela (diferença das duas taxas já arredondadas), também para escolher quem é citado. Ganhou teste de regressão (Elease Gluck em 25 dez 2017: 15 pontos).

- **[baixo] foco.js ainda trata link_target 'como-funciona', que nenhum cartão emite** (correcoes; solution/web/assets/js/views/foco.js:85). Depois da correção #6, o cartão INDICADOR vem com link_label e link_target nulos. grep -rn "como-funciona" solution/engine não acha nenhum link_target com esse valor; os únicos são 'janela' e 'sem_desfecho'. A linha 85 de foco.js virou código morto. Não muda o comportamento, mas sugere um link que não existe mais. **O que foi feito:** Linha apagada.

- **[baixo] Contribuição ainda diz que todo cartão da Gabi tem link para a conta, mas a correção 6 tirou esse link** (fatos; docs/contribuicao-do-rodrigo.md:46). A correção 6 da evidência 06 tirou o link 'Ver a conta' dos cartões INDICADOR do vendedor e do gestor. A API confirma. Comando: curl -s 'http://127.0.0.1:8077/api/seller?name=Daniell%20Hammack&date=2017-12-04' e leitura de insights. O cartão INDICADOR volta com "link_label": null e "link_target": null. Em /api/team?date=2017-12-04&manager=Rocco%20Neubert, o INDICADOR da agenda também volta com link_label null. Mesmo assim, a tabela da contribuição ainda diz que cada cartão traz 'o número, a ação e o link para a conta'. Os outros cartões têm link para a lista de deals ('Ver os 18 deals', 'Ver todos os 47 sem desfecho'), não para uma conta. **O que foi feito:** Frase trocada: "cada um traz o número e a ação; o de taxa de ganho mostra a conta no próprio texto".

- **[baixo] Evidência 06 cita achados por números que não batem com a lista numerada de 1 a 26** (fatos; process-log/evidencias/revisoes/06-revisao-final-da-entrega.md:58, 267, 274-276). Na seção Verificador (linha 58) e em 'Achados descartados' (linhas 274-276), os números com # seguem a numeração bruta dos 31 achados. A seção 'Achados confirmados (26)' foi renumerada de 1 a 26. Comparei os títulos. O .gitignore aparece como '#9' na linha 58 e na 274, mas é o achado 1 da lista; o achado 9 da lista é o dos '3.438 deals'. 'Ver a conta (#12)' é o 6. 'Diferença de pontos (#13)' é o 7. 'mesmos números (#16)' (linhas 58 e 275) é o 18. 'Ver os 47 (#18)' é o 20. 'Duplicado do #5 (README.md:181, 31 + 8 = 39)' (linha 276) é o 11; o 5 da lista é o do 'README longo'. A linha 267 (achado 26) diz '(ver #20)', mas o 20 da lista é o do GTX Plus Pro; o '#20' bruto é um achado descartado. Quem segue um '#' cai no achado errado. **O que foi feito:** Este arquivo foi gerado de novo com o número original (#) no título de cada achado.

- **[medio] Correção #7 entrou pela metade: o cartão INDICADOR do gestor ainda usa a diferença sem arredondar e contradiz a coluna Taxa de ganho** (regressao; solution/engine/team.py:207 e solution/engine/team.py:210 (a tabela em solution/web/assets/js/views/time.js:172 já usa as taxas arredondadas)). A tabela passou a mostrar a diferença das duas taxas já arredondadas. O cartão da pauta continua arredondando rate_delta_points, que é a diferença crua. O próprio cartão manda o leitor conferir na coluna. Comando: curl -s 'http://127.0.0.1:8141/api/team?date=2017-07-03&seller=Markita%20Hansen'. Saída: rate_official 0.6364, rate_with_stale 0.5714, rate_delta_points 6.49, e o cartão diz 'Markita perde 6 pontos de taxa de ganho quando esses deals entram na conta. A conta está na coluna Taxa de ganho.' A tabela mostra '63,6% → 57,1%' e '6,5 pontos a menos', que arredonda para 7. Numa varredura de 26 datas × (sem filtro, 6 gestores, 3 regionais, 30 vendedores), 53 respostas têm essa divergência. Exemplos: 2017-07-10 sem filtro, Kami com '10' no cartão e 10,5 na tabela; 2017-07-31 Summer Sewald, Maureen com '11' no cartão e 11,5 na tabela. A ordem dos citados também segue a diferença crua. **O que foi feito:** É o mesmo ponto do primeiro achado desta lista; corrigido junto.

- **[baixo] ?desfecho=revelado volta a revelar o desfecho a cada troca de semana, mesmo depois de o usuário esconder** (regressao; solution/web/assets/js/views/maquina.js:337). Achei por leitura do código. Não abri navegador. O comentário em maquina.js:336 promete 'abre já revelado ... até o primeiro clique no botão'. Mas revealedByLink é recalculado a cada render a partir de ctx.params. O parâmetro desfecho nunca sai do endereço: applyEntryLink, em app.js:577-595, só tira como, perfil e data. Os botões de semana e a linha do tempo chamam ctx.setDate. Isso dispara handleRoute('date') (app.js:631), que relê o hash com ?desfecho=revelado. Então o render roda de novo com revealedByLink = true. O mesmo acontece quando o gestor troca o vendedor, porque app.js:342 repassa ...ctx.params. Resultado: o usuário clica em 'Esconder o desfecho' (o store grava 'escondido'), troca de semana, e as listas voltam reveladas. Evidência: grep -n "revealedByLink\|desfecho" solution/web/assets/js/views/maquina.js mostra a linha 337 'let revealedByLink = ctx.params.desfecho === 'revelado';' dentro de render(). E grep -n "const { como, perfil, data, ...rest }" solution/web/assets/js/app.js mostra que desfecho fica em rest. **O que foi feito:** Corrigido: o link vale até o primeiro clique no botão, mesmo que a tela seja redesenhada.
