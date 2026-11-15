# Revisão independente do motor e da API (4 revisores, 36 achados)

> Depois que o motor e a API passaram nos testes, quatro revisores independentes os examinaram: recontagem às cegas a partir dos CSVs, busca por uso de informação do futuro, robustez do servidor e conferência de números e textos. Um quinto agente reproduziu e corrigiu os achados. Um achado pode ter gerado mais de uma correção, por isso corrigidos e mantidos somam mais que o total de achados. Saída bruta de agentes de IA, sem edição além da remoção de caminhos locais.


## Revisor: recontagem

**Resumo do revisor.** Fiz a recontagem às cegas: escrevi um motor do zero, a partir dos CSVs e da especificação, sem abrir engine/, server.py, tests/ nem a pasta de análise. Foram 33.507 comparações automáticas contra a API na porta 8811 e 33.505 bateram.

As 2 que não bateram são de nome, não de conta: os campos auc.score e auc.age_only de /api/proof medem coisas diferentes do que o nome indica.

Fiz também cerca de 25 conferências manuais, todas certas:
- window.chance em 7 datas;
- a tabela de /api/score-model (chance, n, y e nível por faixa) em 7 datas;
- semana e mês do trimestre;
- os números citados nos textos de insights, agenda do time e data-quality.

O que foi conferido, por rota:
- **/api/seller e /api/pipeline**: 5 vendedores × 4 datas (2017-07-03, 09-11, 10-02, 12-04), com 23.164 comparações sem nenhuma diferença. Entraram contagens, valores declarado, vivo, sem desfecho e esperado, live_share, a janela, as faixas de score com e sem cliente e as taxas oficial e com os sem desfecho. Também a ordem completa dos deals, e por deal: idade, faixa, score, chance, receita esperada, n, y, nível e share_above. No pipeline, as colunas de prospecção (preço, depois id), em negociação, sem desfecho, ganhos e perdidos (fechados em [d-30, d)).
- **/api/team**: Rocco Neubert, Summer Sewald, Central e empresa inteira, nas 4 datas (2.808 comparações, todas certas). As linhas vêm por valor declarado decrescente, com desempate por nome.
- **/api/accounts e /api/account**: East e todas, mais Mathtouch, Kan-code, Hottechi, Sonron, Condax e Zathunicon, nas 4 datas (6.043 comparações, todas certas).
- **/api/proof**: tudo bateu, salvo os dois campos de AUC. Isso inclui n_lists 659, as somas e razões das 6 regras, as 22 datas, dates_won, by_period, peak e a sensibilidade top 5 e top 20. Implementei a expectativa exata (grupos de chave igual; o grupo que não cabe entra pela fração vagas/tamanho).
- **/api/time-machine**: 3 vendedores × 3 datas (528 comparações, todas certas): as duas listas, os desfechos, a janela cortada em 31 dez e a comparação justa.
- **/api/data-quality e /api/login**: 4 datas (696 comparações, todas certas).

O "3.438" do ritmo de trimestre é a soma, em 1 abr, 1 jul e 1 out, dos deals abertos com mais de 30 dias. Inclui os sem desfecho e conta pares deal–mês (são 2.616 deals distintos).

Fora as diferenças de AUC, achei duas inconsistências de apresentação, listadas abaixo. A API cumpre a regra de ouro em todas as contas que refiz: nada usa desfecho, data nem valor de fechamento a partir da data. O campo account nunca entra em chance, score nem ordenação.

O servidor foi encerrado e conferi que o processo morreu e a porta 8811 ficou livre. Os scripts estão em <pasta temporária>/wf/backend/recontagem (model.py, cmp.py e audit_*.py).

**Achados: 4**

### 1. [medio] auc.score não mede o score: mede a chance

- **onde:** /api/proof → auc.score e auc.age_only
- **detalhe:** Valores da API: auc.score = 0,78026 e auc.age_only = 0,69343. Os meus, recalculados sobre os mesmos 50.138 pares deal–data (5.982 positivos): AUC da chance completa (idade + semana do trimestre) = 0,78026; AUC da chance só por faixa de idade = 0,69343; AUC do score de verdade (receita esperada = chance × preço) = 0,70568; AUC do score inteiro 0–100 = 0,67359. Ou seja, o campo 'score' guarda a AUC da chance, e não a da ordem que o app usa. A conta da API está certa; o problema é o nome. Hoje nenhum texto da API cita AUC, então o risco é só a tela, ou a documentação, apresentar 0,78 como 'AUC do score'. Sugestão: renomear para chance e age_band_chance, ou acrescentar a AUC da receita esperada (0,7057).
- **como reproduzir:** Para cada uma das 22 segundas, de 2017-07-03 a 2017-11-27: pegar todos os deals abertos (com idade), rótulo y = Won com close_date < d + 30; calcular a AUC com empates contando 0,5. Com a chave chance r['chance'] sai 0,78026 (igual a auc.score); com round(chance × preço, 2) sai 0,70568.

### 2. [baixo] Desempate do id muda de sentido entre as telas

- **onde:** /api/account → closed.deals (comparado com /api/pipeline → columns won/lost)
- **detalhe:** Em /api/account, closed.deals vem em close_date decrescente e, no empate, id decrescente: em 131 empates conferidos, todos seguem (close_date, id) invertidos. Já em /api/pipeline, as colunas Ganhos e Perdidos vêm em close_date decrescente com id crescente. As duas ordens são determinísticas, mas incoerentes entre si.
- **como reproduzir:** /api/account?name=Condax&date=2017-12-04: em 2017-12-0x aparece X7DYUDEB antes de P3HO0L6P e antes de 1IY7Y42E (ids decrescentes). No pipeline de qualquer vendedor, os empates de close_date vêm com ids crescentes.

### 3. [baixo] "3.438" conta pares deal–mês, inclusive deals sem desfecho

- **onde:** /api/data-quality → items.quarter_rhythm.number ("0 de 3.438")
- **detalhe:** O número bate com a soma, em 2017-04-01, 2017-07-01 e 2017-10-01, dos deals abertos com mais de 30 dias. Mas esse total conta o mesmo deal várias vezes (são 2.616 deals distintos) e inclui os que já passaram de 138 dias, que não fechariam em mês nenhum. A afirmação '0' está certa: nenhum fechamento com ciclo acima de 30 dias caiu no primeiro mês de um trimestre, entre 3.548 fechamentos assim. Só que o denominador não é óbvio para quem confere. Um denominador mais direto seria '0 de 3.548 fechamentos com mais de 30 dias', ou deixar explícito no texto que são deals em aberto no início do mês.
- **como reproduzir:** sum(len([x for x in open_at(t) if (t - engage).days > 30]) for t in (2017-04-01, 2017-07-01, 2017-10-01)) = 3438; conjunto de ids distintos = 2616; fechamentos com ciclo > 30 = 3548, sendo 0 no mês 0 do trimestre.

### 4. [baixo] A regional de casa de um cliente muda com a data

- **onde:** /api/accounts e /api/account → home_region
- **detalhe:** home_region é a moda das regionais dos fechados antes da data. Isso está correto pela regra de ouro, e minha recontagem com essa definição bateu 100%. Mesmo assim, 4 clientes divididos quase meio a meio trocam de lista conforme a data: Kan-code fica em West em 07-03, East em 09-11 e 10-02 e West em 12-04; Hottechi fica em West até 10-02 e Central em 12-04; Condax é Central; Konex é West. Por isso a lista East tem 27 clientes em 07-03, e não 28. Os textos de aviso tratam bem esse caso: só dizem 'nunca fecharam negócio' quando é verdade e acertam o plural de 'outras regionais'. Não é erro de conta. Fica como ponto que o avaliador pode estranhar, e uma nota curta na tela resolveria.
- **como reproduzir:** GET /api/account?name=Kan-code&date=2017-07-03 devolve home_region West (fechados antes de 3 jul: West 36, East 31). Na data 2017-09-11 devolve East (East 57, West 55).


## Revisor: vazamento

**Resumo do revisor.** Não achei vazamento de informação do futuro que mude deals, scores, chances, ordenações ou números das telas de trabalho. Conferi todas as funções que recebem a data d em engine/ e server.py, e o teste empírico deu respostas idênticas.

Leitura do código:
(c) O modelo da data d usa só segundas m com m + 30 dias <= d (core.py:198), e o rótulo y exige close_date < m + 30, logo antes de d (core.py:120).
(d) O maior ciclo conhecido pega só fechamentos com close_date < d (bisect_left em core.py:82).
(e) A regional de casa e o histórico do cliente vêm de closed_before(d, account=...) (accounts.py:27-36).
(f) win_record e as colunas Ganhos/Perdidos do pipeline usam closed_before(d) (core.py:330, seller.py:383).
(a) O campo account só aparece em contagens de exibição: não entra em priority_key, stale_key, Snapshot, score nem proof._rule_keys.
(b) A máquina do tempo não devolve account: varri o JSON das 26 datas x 30 vendedores e não há chave "account" nem nome de cliente. As listas dela saem de snap.by_seller e o desfecho é anexado depois.
Usos da base inteira ficam só nas exceções permitidas: proof, data_quality (_item_account_leak e _item_max_cycle, que dizem "até o fim da base"), tested_signals, sources e meta.

Teste empírico. Script em <pasta temporária>/wf/backend/vazamento/compare.py. Bases truncadas em <pasta temporária>/wf/backend/vazamento/<data>/.
Nas datas 2017-07-03, 2017-10-02 e 2017-12-04, comparei 26 chamadas por data:
- focus e pipeline de 6 vendedores;
- team de 2 gestores, da regional Oeste e da empresa;
- listing geral e da Oeste;
- detail de 5 clientes;
- score_model com viewer vendedor e com viewer gestor, sem signals e proof;
- login sem os stats da prova.
Os deals abertos foram os mesmos nas duas bases (1.714, 2.434 e 2.078). A única diferença foi panel.stats[0].value do login (ver achado 1).

Fiz também uma extensão em <pasta temporária>/wf/backend/vazamento/extended.py. Ela cobre as 26 datas, os 30 vendedores, os 6 gestores, as 3 regionais, 5 clientes por data e a ordem das listas da máquina do tempo (sem o desfecho), num total de 110 comparações por data. Resultado: 0 diferenças, com os stats do login retirados.

O fim da base não aparece em nenhum rótulo das telas comparadas. Ele só aparece na máquina do tempo (proof._window), que é exceção permitida.

A suíte unittest passa: 161 testes OK. Nada foi corrigido.

**Achados: 3**

### 1. [baixo] Login conta deals que só entram depois da data

- **onde:** engine/quality.py:247 (_login_panel, stats[0])
- **detalhe:** O card "oportunidades na base" usa len(ds.deals) = 8.800, que inclui deals com engage_date >= d. Na base truncada o valor muda: 4.935 em 2017-07-03, 7.672 em 2017-10-02 e 8.691 em 2017-12-04. É a única diferença do teste empírico. O rótulo diz "na base", então dá para defender como descrição da base inteira. Mas está no painel de uma tela datada, logo ao lado de números da data, e um avaliador cético pode ler como vazamento. Saída possível: trocar por uma contagem conhecida em d (deals com engage_date < d mais os em prospecção) ou mudar o rótulo para deixar claro que é a base inteira.
- **como reproduzir:** quality.login(full, date(2017,7,3))['panel']['stats'][0]['value'] dá '8.800'. Na base truncada em 2017-07-03 dá '4.935'.

### 2. [baixo] Lista de vendedores com deals vem da base inteira (latente)

- **onde:** engine/team.py:30, team.py:76-77, team.py:93; engine/quality.py:84, quality.py:124, quality.py:174
- **detalhe:** team.team, team._scope (erro "não tem deals na base"), team._options, quality.login e quality.meta filtram vendedores por ds.deals_by_seller / _base['sellers_with_deals'], montados com a base inteira. Se um vendedor só tivesse deals depois de d, ele apareceria em d com carteira vazia e entraria nas contagens de vendedores (seller_count, team_size, "N vendedores"). Hoje não há efeito: o primeiro deal mais tardio de um vendedor é de 2016-12-02 (Jonathan Berthelot), e o teste nas 26 datas não achou diferença. Só vira problema com outra base.
- **como reproduzir:** Sem reprodução nesta base: o extended.py mostra 'sellers sem deal antes de d: []' nas 26 datas.

### 3. [baixo] Datas aceitas dependem do fim da base (latente)

- **onde:** engine/core.py:171 (available_dates) e core.py:184 (parse_date)
- **detalhe:** available_dates usa min(LAST_DATE, ds.end_date), e end_date é a maior close_date da base inteira. Isso não muda nenhum número nem texto das telas, porque com estes dados o limite é sempre LAST_DATE. Mas o seletor de datas é definido com informação de depois de d. Na base truncada, parse_date recusaria a própria data d (por isso o script de comparação passa objetos date direto, sem parse). Para o avaliador não tem efeito. Fica registrado como acoplamento.
- **como reproduzir:** core.parse_date(base_truncada_em_2017_12_04, '2017-12-04') levanta ValueError 'Data fora do período', porque end_date vira 2017-12-03 ou antes.


## Revisor: robustez

**Resumo do revisor.** Revisão de robustez de solution (server.py, engine/, API.md). Não alterei nada. O servidor de teste (porta 8813) já foi encerrado.

O que passou:
- A suíte roda em Python 3.9.6: 161 testes OK em 3,3 s, sem avisos com -X dev. Python 3.12 não está instalado na máquina, então a parte de 3.12 foi só leitura de código.
- 20 requisições simultâneas logo após subir o servidor, com rotas e datas diferentes e o aquecimento ainda rodando: todas deram 200. Os corpos ficaram byte a byte iguais aos das chamadas sequenciais num servidor novo. Não achei condição de corrida.
- Varri a engine inteira: 26 datas × 30 vendedores × foco/pipeline/máquina do tempo/team/score-model, cada gestor e regional, as 85 contas na primeira, na última e na data padrão, além de proof/meta/sources. Resultado: zero exceções, zero NaN/Infinity, zero "None" em frase, zero %s sobrando, zero plural errado. Conferi que o detector acusa defeitos plantados.
- Datas mal formadas ou fora da lista, nomes inexistentes e combinações impossíveis de gestor/regional/vendedor dão 400 com mensagem em português. Caixa, espaços e acentos no nome são tolerados.
- Path traversal está bloqueado: ../, %2e%2e, %252e, barras duplas, caminho absoluto, \, %00, link simbólico para fora e o truque de prefixo web2. Erro 500 não vaza stack trace.
- Vendedor com menos de 10 abertos (Garret Kinder em 04/12, Reed Clapper em 25/12) e as datas 03/07 e 25/12 dão respostas coerentes. Não há vendedor com carteira zerada em nenhuma data.

Desempenho:
- Carga dos CSVs: 137 ms. Prova: 0,5 s, feita uma vez no aquecimento. Snapshot de uma data nova: cerca de 5 ms.
- /health responde em 22 ms logo após subir.
- A frio, depois do aquecimento: de 0,6 a 8 ms por rota (/api/login 8 ms, /api/seller 7 ms). A quente: de 0,3 a 1 ms.
- 780 requisições de vendedor × data: 2,0 s no total, máximo de 9 ms.
- Memória do processo: cerca de 50 MB depois do aquecimento e 74 MB com o cache cheio.
- /api/seller chega a 176 KB sem gzip (cerca de 8 KB com gzip), porque o mesmo texto fixo de "excluídos" se repete em cada deal.

Abaixo, os defeitos com o passo que reproduz cada um.

**Achados: 16**

### 1. [alto] A interface não existe: abrir o navegador dá 404

- **onde:** web/ (pasta vazia); server.py _static
- **detalhe:** A pasta web/ está vazia. Por isso, GET / e qualquer caminho fora da API devolvem 404 com a página 'Interface não encontrada'. O roteiro de validação ('python3 server.py e abrir o navegador') falha hoje. Se o front vem numa etapa posterior, falta só ele. Se não vem, é o defeito que derruba a entrega.
- **como reproduzir:** cd solution && PORT=8813 python3 server.py & curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8813/   -> 404

### 2. [medio] /api/account com viewer gestor nunca marca is_viewer

- **onde:** engine/accounts.py:210-253 (_viewer_name / detail)
- **detalhe:** O API.md diz que viewer pode ser 'vendedor ou gestor' e marca is_viewer nos deals dele. Mas detail() compara s.deal.seller == who, e who é o nome do gestor. O nome de um gestor nunca aparece como vendedor de um deal, então tudo sai False. O model_page já trata o gestor como 'o time dele' (_viewer_scope); aqui falta essa expansão.
- **como reproduzir:** curl -s 'http://127.0.0.1:8813/api/account?name=Acme%20Corporation&viewer=Melvin%20Marxen' -> viewer='Melvin Marxen', is_viewer verdadeiro em 0 abertos e 0 fechados. Os deals da conta são de vendedores do time dele, por exemplo Daniell Hammack e Reed Clapper.

### 3. [medio] Validação de data muda entre Python 3.9 e 3.12

- **onde:** engine/core.py:180 (parse_date) e :37 (_date)
- **detalhe:** A partir do 3.11, date.fromisoformat aceita o formato ISO compacto ('20171204') e semanas ISO ('2017-W49-1'). No 3.9 local, esses textos dão 400 'Data inválida'. No deploy (Dockerfile python:3.12-slim), passam a dar 200, o que contradiz o API.md ('formato AAAA-MM-DD'). Também viram entradas separadas no cache. O teste test_core.test_parse_date só cobre '04/12/2017' e não pega a diferença.
- **como reproduzir:** Python 3.9: curl 'http://127.0.0.1:8813/api/seller?name=Darcel%20Schlecht&date=20171204' -> 400. Em 3.12: python3.12 -c "import datetime; print(datetime.date.fromisoformat('20171204'), datetime.date.fromisoformat('2017-W49-1'))" -> 2017-12-04 duas vezes, logo a rota devolve 200.

### 4. [medio] Telas de trabalho em data passada expõem o cliente dos deals abertos, que adianta o desfecho

- **onde:** engine/shapes.py:58 (open_deal_dict.account); seller.py:312-323 (_band_groups with/without_account), :390 (counts.with_account); accounts.py:237-245 (abertos da ficha)
- **detalhe:** O próprio app diz que esse campo vaza o desfecho: o texto do time machine fala em 'Mostrar o cliente numa data passada adiantaria o desfecho', e o data-quality e o model_page dizem 'Fora, por vazamento'. Mesmo assim, foco, pipeline e ficha do cliente devolvem account em cada deal aberto, contagens com/sem cliente e a lista de abertos 'com' a conta, em qualquer data passada. Em 03/07/2017 há 397 deals vivos sem cliente e nenhum deles fechou depois. Dos 1.159 com cliente, 614 foram ganhos. Quem vê 'sem cliente' numa data passada sabe que o deal não fecha. Isso contradiz a convenção 'Só o que se sabia na data' do API.md, que só cita estágio, data e valor. Um avaliador cético pega a incoerência entre a máquina do tempo e as outras telas.
- **como reproduzir:** python3 -c "from engine import core; from datetime import date; ds=core.get_dataset(); s=core.snapshot(ds,date(2017,7,3)); wo=[x for x in s.live if not x.deal.account]; print(len(wo), sum(x.deal.close_date is not None for x in wo))" -> 397 0. Depois: curl '.../api/seller?name=Darcel%20Schlecht&date=2017-07-03' e ver deals[].account e bands[].with_account.

### 5. [medio] O 405 não lê o corpo da requisição e dessincroniza a conexão keep-alive

- **onde:** server.py:143-147 (_not_allowed)
- **detalhe:** Com protocol_version HTTP/1.1, um POST/PUT com corpo recebe 405, mas o corpo continua no socket. O servidor então lê os bytes do corpo como o início da próxima requisição. Resultado: um GET legítimo na mesma conexão vira '501 Unsupported method (xxxxxxxxxxxxxxxxxxxxGET)' em HTML. Isso afeta clientes e proxies que reaproveitam a conexão.
- **como reproduzir:** python3 -c "import socket,time; s=socket.create_connection(('127.0.0.1',8813)); s.sendall(b'POST /api/meta HTTP/1.1\r\nHost: x\r\nContent-Length: 20\r\n\r\n'+b'x'*20+b'GET /health HTTP/1.1\r\nHost: x\r\n\r\n'); time.sleep(.5); print(s.recv(65536).decode())" -> 405 seguido de 501 "Unsupported method ('xxxxxxxxxxxxxxxxxxxxGET')"

### 6. [baixo] Qualquer ValueError interno vira 400 com a mensagem crua do Python

- **onde:** server.py:174-177 (except ValueError)
- **detalhe:** O servidor trata todo ValueError como erro do usuário. Um defeito futuro na engine, como max() de sequência vazia, int() de texto ou o ValueError de closed_deal_dict, sairia como 400 com mensagem interna em inglês, em vez de 500 genérico. Hoje nenhuma entrada dispara isso, porque a varredura não teve exceções. O risco é latente. Uma exceção de domínio própria resolveria.
- **como reproduzir:** python3 -c "import threading,http.client,server; s=server.LeadScorerServer(('127.0.0.1',0),quiet=True); threading.Thread(target=s.serve_forever,daemon=True).start(); server.ROUTES['/api/sources']=((),lambda ds,p: max([])); c=http.client.HTTPConnection('127.0.0.1',s.server_address[1]); c.request('GET','/api/sources'); r=c.getresponse(); print(r.status,r.read())" -> 400 {"error":"max() arg is an empty sequence"}

### 7. [baixo] Erros da biblioteca padrão saem em HTML inglês e o header Server expõe a versão do Python

- **onde:** server.py Handler (send_error herdado); API.md 'Outros métodos devolvem 405'
- **detalhe:** Métodos fora da lista (TRACE, CONNECT, qualquer verbo inventado) dão 501 em HTML inglês, não o 405 que o API.md promete. Linha de requisição inválida dá 400 HTML, e URI acima de 64 KB dá 414 HTML. Toda resposta traz 'Server: LeadScorer/1.0 Python/3.9.6'. Não é stack trace, mas foge do contrato 'erro = JSON em português'.
- **como reproduzir:** curl -s -i -X TRACE http://127.0.0.1:8813/api/meta | head -3 -> 'HTTP/1.1 501 Unsupported method' e 'Server: LeadScorer/1.0 Python/3.9.6'. Também: printf 'GARBAGE\r\n\r\n' | nc 127.0.0.1 8813 -> 400 HTML 'Bad request syntax'.

### 8. [baixo] Parâmetro repetido vale o último (sem documentação) e o erro devolve a entrada inteira, sem limite

- **onde:** server.py:168 (params) e mensagens de erro em core._resolve / _api
- **detalhe:** Em ?name=A&name=B vale B, e isso não está no API.md. As mensagens de erro repetem o texto recebido sem cortar: um nome de 60.000 caracteres gera um 400 de 60 KB, e a rota 404 repete o caminho inteiro. A resposta é JSON com nosniff, então não há XSS direto, mas o front precisa escapar a mensagem, porque ela traz <script> do jeito que chegou.
- **como reproduzir:** curl '.../api/seller?name=Fulano&name=Darcel%20Schlecht' -> 200; curl '.../api/seller?name=Darcel%20Schlecht&name=Fulano' -> 400. Nome com 'A'*60000 -> 400 com 60.043 bytes. ?name=%3Cscript%3E... -> o erro contém <script>alert(1)</script>.

### 9. [baixo] Conexão ociosa prende uma thread para sempre e o servidor escuta em todas as interfaces

- **onde:** server.py Handler/LeadScorerServer (sem timeout); main() bind 0.0.0.0
- **detalhe:** StreamRequestHandler.timeout fica None. Cada conexão keep-alive ociosa ou lenta segura uma thread sem limite, o que abre espaço para slowloris no deploy público. Localmente, o servidor escuta em 0.0.0.0 e expõe a porta na rede, mas a mensagem fala em localhost.
- **como reproduzir:** Abrir N sockets em 127.0.0.1:8813 sem enviar nada: cada um fica com uma thread viva até o cliente fechar. Ver também: grep -n timeout server.py -> nenhuma ocorrência.

### 10. [baixo] Vendedor cadastrado sem deals: 200 em /api/seller e 400 em /api/team

- **onde:** engine/seller.py focus/pipeline vs engine/team.py:76-77
- **detalhe:** Carl Lin, Mei-Mei Johns e outros três só estão no cadastro. /api/seller, /api/pipeline, /api/time-machine e score-model com viewer respondem 200 com 'Você não tem deal em negociação nesta data', como se fosse algo daquela data. Já /api/team?seller=Carl%20Lin dá 400 'não tem deals na base', e o /api/meta nem lista esses vendedores. Falta uma regra só.
- **como reproduzir:** curl '.../api/seller?name=Carl%20Lin' -> 200 com a frase 'nesta data'; curl '.../api/team?seller=Carl%20Lin' -> 400.

### 11. [baixo] Coluna Prospecção usa o estado final da base em qualquer data

- **onde:** engine/seller.py:381 (prospects) e 356-370
- **detalhe:** Os 500 deals em Prospecting são o estado de 31/12/2017, mas aparecem iguais em 03/07. Deals que naquela data ainda nem tinham entrado em negociação (engage_date > d) não aparecem em lugar nenhum. A coluna é anacrônica em data passada. Não vaza desfecho, mas destoa do 'só o que se sabia na data'.
- **como reproduzir:** curl '.../api/pipeline?name=Darcel%20Schlecht&date=2017-07-03' e '...&date=2017-12-25': columns[0].count dá 111 nas duas.

### 12. [baixo] Arquivo estático que falta volta como index.html com 200 e text/html

- **onde:** server.py:189-219 (_static, fallback SPA)
- **detalhe:** Um asset ausente, como /app.js ou /favicon.ico, recebe o index.html com status 200. O navegador tenta interpretar HTML como JS e o erro vira 'Unexpected token <' em vez de 404. '/index.html/' também resolve. Vale devolver 404 para caminhos com extensão.
- **como reproduzir:** Com web/index.html presente: curl -i http://127.0.0.1:8813/nao-existe.js -> 200 text/html (coberto, sem querer, por tests/test_api.py test_spa_fallback).

### 13. [baixo] Código morto e um comentário enganoso

- **onde:** engine/rules.py:206 display_key, :33 STAGE_LABELS, :24 LEVELS, :31 SCORE_BANDS, :106 Deal.outcome_at; engine/core.py:49 Dataset.by_id, :54-55 deals_by_manager/deals_by_region, :85-92 filtros manager/region de closed_before, :279 Snapshot.by_id; engine/fmt.py:38 money_short; engine/quality.py:160-167 e 231-232 _proof_stats/fallback; team.py:26 e proof.py:403 isinstance(d,str)
- **detalhe:** Nenhum desses símbolos é usado pelo servidor ou pelas telas. Alguns só aparecem nos testes: outcome_at, Snapshot.by_id e money_short. O docstring de Deal manda 'use outcome_at(d) nas telas', mas nenhuma tela usa. Em _proof_stats, o try/except ImportError e o fallback 'if mondays is None' nunca executam. Os ramos isinstance(d, str) em team() e time_machine() também nunca executam, porque o servidor sempre passa date.
- **como reproduzir:** for s in display_key STAGE_LABELS LEVELS SCORE_BANDS deals_by_manager deals_by_region money_short outcome_at; do grep -rnw $s engine server.py; done -> só a definição e o reexport.

### 14. [baixo] Funções duplicadas e nomes iguais com significados diferentes

- **onde:** accounts._home_region, model_page._home_regions, quality._base['home']; team._share vs quality._share; proof._period_label vs quality._period_label; rules.stale_key vs seller.top_by_price vs proof.time_machine by_value; model_page._rate vs core.win_rate; team.PHASE_TITLES vs seller.MOMENT_TITLES
- **detalhe:** A regional de casa do cliente é calculada em três lugares. _share devolve 0.0 em team e None em quality para o mesmo caso. _period_label existe em proof e em quality com significados diferentes. A ordenação (-preço, -idade, id) aparece três vezes, e stale_key já é exatamente ela. _rate repete win_rate. Os títulos de fase do trimestre aparecem em dois dicionários quase iguais.
- **como reproduzir:** grep -n "def _home_region\|def _home_regions\|home = {a" engine/*.py; grep -n "def _share\|def _period_label" engine/*.py; grep -n "-s.deal.price, -s.age_days, s.deal.id" engine/*.py

### 15. [baixo] quality.py passa do limite de cerca de 450 linhas

- **onde:** engine/quality.py (492 linhas); model_page.py 435; proof.py 420
- **detalhe:** quality.py junta meta, login, qualidade dos dados e fontes num arquivo só, com 492 linhas. model_page.py e proof.py estão no limite.
- **como reproduzir:** wc -l engine/*.py

### 16. [baixo] Testes que não testam o que dizem

- **onde:** tests/test_quality.py:22, tests/test_proof.py:96, tests/test_core.py:94
- **detalhe:** test_serializable só chama json.dumps(page) com allow_nan padrão (True), então um NaN passaria, embora o servidor use allow_nan=False. test_cached_and_thread_safe chama proof() com o cache já cheio pelo setUpClass, então não exercita corrida nenhuma. test_parse_date não cobre os formatos que o 3.12 passou a aceitar ('20171204', '2017-W49-1'). Nenhum teste cobre viewer=gestor em /api/account, e por isso o defeito do is_viewer passou.
- **como reproduzir:** Em test_quality.py, trocar json.dumps(self.page) por json.dumps(self.page, allow_nan=False) para o teste ter efeito. Em test_proof.py, o setUpClass já calcula self.p = proof.proof(DS) antes das threads.


## Revisor: referencia-e-textos

**Resumo do revisor.** I ran the server on port 8814 and stopped it at the end; exit code 144 is from that pkill, so it is expected. I ran mock.py for 2017-12-04, 2017-09-11 and 2017-10-02, once for the company and once each for 6 sellers (Daniell Hammack, Darcel Schlecht, Reed Clapper, Cassey Cress, Vicki Laflamme, Wilburn Farren). I also ran mock2.py, tm.py, leak.py, cal.py and check2.py. I compared their output with the API.

NUMBERS: every reference number matches the API. That covers the company at the 3 dates and all 30 rows of /api/team. It also covers counts, bands, values, expected revenue, win rates and the score, chance, n and level of each deal for the 6 sellers. The remaining checks also match:
- Daniell's top 10 in priority order, and his open deals by product.
- The time machine for Daniell: 5 sales, US$ 25.687; value-only list 0; 3, 6 and 4,3 sales for the three tie rules.
- Rocco Neubert's team row by row and the totals per region.
- The East client list, Mathtouch in full, data quality, the login panel, AUC, top 5 and top 20, and the peak date.
- The proof differs by less than 0,5% in the sums (6,99 vs 7,01 million; 5,72 vs 5,71; 4,93 vs 4,91).

The only differences are: rounding by 1 real (Markita 26.634 vs 26.635, Donn 9.752 vs 9.751); the order inside ties, where the reference does not put the oldest first and the API correctly does; and the order of deals with no outcome, where the API correctly uses price.

The golden rule held. The won and lost pipeline columns, which I checked against the CSV for 3 sellers on 3 dates, the client history and the seller win rates only use deals closed before the date.

TEXTS: I read 121 calls (about 92 thousand strings, deduplicated into templates). I also scanned the seller texts (summary, context and insight cards) for the 30 sellers on all 26 dates, plus the company team texts on all 26 dates. That scan found no "1 deals", no None or null inside a sentence, no number in English format and no missing accent.

The problems found are listed below. Nothing was fixed.

**Achados: 13**

### 1. [medio] Tag "Maior carteira" for Darcel Schlecht is false on some dates

- **onde:** /api/login?date=2017-07-03 and date=2017-12-25 (suggestions[2].tag)
- **detalhe:** Darcel always gets the tag "Maior carteira". On 2017-07-03 Markita Hansen is ahead on declared value (373.939 vs 292.987) and on live value (338.020 vs 292.987), and Kary (120) and Vicki (113) have more open deals than Darcel (84). On 2017-12-25 Markita's declared value (297.164) is above Darcel's (291.081), and the same card says "Central · 76 sem desfecho". Darcel only has the highest live value from 2017-07-31 on. Even on 2017-12-04 he does not have the most open deals (Vicki 134, Darcel 118); the tag is only true there for declared and live value.
- **como reproduzir:** GET /api/login?date=2017-07-03 and compare with GET /api/team?date=2017-07-03 (rows: declared_value, live_value, open_count).

### 2. [medio] "é o ritmo de fim de trimestre" stated even when the data does not show it

- **onde:** /api/account?name=Acme%20Corporation&date=2017-12-04 (closed.month_sentence); also Umbrella Corporation
- **detalhe:** The text is: "Março, junho e setembro somam 11 das 30 vendas: é o ritmo de fim de trimestre." 11/30 = 37%, about the 33% expected if sales were spread evenly over 9 months. The biggest month for Acme is May (7 sales); June has 6 and March 3. For Umbrella Corporation it is 17 of 44 (39%), and the biggest month is November (9). The sentence is built without checking whether the quarter-end months really stand out.
- **como reproduzir:** GET /api/account?name=Acme%20Corporation&date=2017-12-04: by_month mar 3, abr 2, mai 7, jun 6, jul 2, ago 3, set 2, out 2, nov 3.

### 3. [medio] Action asks to confirm whether a 15-day deal "segue de pé" and calls a deal with the same chance "já passou da faixa"

- **onde:** /api/seller (deals[].why.action and summary_text) on first-month dates: 2017-07-03, 2017-07-10, 2017-10-02, 2017-10-09
- **detalhe:** On 2017-07-03, every live deal aged 15 to 107 days gets: "o deal já passou da faixa que mais fecha agora (0 a 14 dias). Confirme com o cliente se segue de pé." Two problems. (1) Asking whether a 15-day deal "segue de pé" suggests it has gone cold, but it was just opened. (2) For #6R6S91WE (Daniell, 100 days, score 92) the chance is 17% (30 of 180), almost the same as the window's 18%, because the 91–105 band is 17%. The data does not support "já passou da faixa" with that doubtful tone. On 2017-10-02 the 15–107 band is at 0–3%, so there the problem is mainly (1).
- **como reproduzir:** GET /api/seller?name=Daniell%20Hammack&date=2017-07-03, deal 6R6S91WE: why.action plus chance 0.17 against window.chance 0.18.

### 4. [baixo] "É mês de fechar" and "Proponha o fechamento ainda em dezembro" with 6 days left and the best chance at 19–22%

- **onde:** /api/seller and /api/team?date=2017-12-25 (also 2017-09-25): insights[0].title, agenda[2].title, messages[].text, why.action
- **detalhe:** On 2017-12-25 the best chance in the table is 22% (76–90 days), against 50% on 2017-12-04. Even so, the seller card says "É mês de fechar.", the context sentence says "quando os deals maduros desta base mais fecham", the message reads "Dezembro é mês de fechar.", and deals in the window get "Proponha o fechamento ainda em dezembro". December has 6 days left and the base ends on the 31st. The title comes only from the quarter phase and ignores how low the chance is. The 2017-09-25 cards say the same ("É mês de fechar") with the window at 21%; its action says "ainda em setembro" (not checked deal by deal).
- **como reproduzir:** GET /api/seller?name=Cassey%20Cress&date=2017-12-25: window.chance 0.19, insights[0] "É mês de fechar."; GET /api/score-model?date=2017-12-25: peak 22%.

### 5. [baixo] Team expected revenue rounds to US$ 153.815, but the rows add up to 153.814 and the reference says 153.814

- **onde:** /api/team?manager=Rocco%20Neubert&date=2017-12-04 (agenda[2].body)
- **detalhe:** "A receita esperada em 30 dias é US$ 153.815." The total 153.814,92 is rounded on its own, while the 5 rows shown add up to 43.450 + 42.162 + 25.431 + 25.869 + 16.902 = 153.814. A reviewer adding up the table will find 1 real of difference.
- **como reproduzir:** GET /api/team?manager=Rocco%20Neubert&date=2017-12-04: summary.expected_30d 153814.92; rows[].expected_30d.

### 6. [baixo] "+10% em outubro e novembro" vs reference 1,11; "dá empate" covers a small loss

- **onde:** /api/proof (sentences.limits[1].body)
- **detalhe:** by_period out-nov gain_vs_value_no_stale = 0,104, so the text shows "+10%" while the reference gives 1,11 (+11%). This comes from using the exact expected value instead of a random draw, but it is the one place where the rounded label changes. Also, "Se a regra simples puser o deal mais novo na frente, nesses dois meses dá empate.": the API value is -1,1% (reference 0,99), so the score loses slightly. "Empate" is defensible, but it softens a loss.
- **como reproduzir:** GET /api/proof: by_period[1].gain_vs_value_no_stale 0.104, gain_vs_value_no_stale_newest -0.0106.

### 7. [baixo] Dates outside the "4 dez 2017" format

- **onde:** /api/score-model (training.sentence), /api/proof (period_label, sentences.method), /api/score-model proof.sentence, /api/login (panel.sentence)
- **detalhe:** Mixed date formats: "(3 abr de 2017)", "(6 mar, 5 jun e 4 set de 2017)", "de 3 jul a 27 nov de 2017" and, in the login panel, "Em 3 de julho de 2017" / "Em 4 de dezembro de 2017". The rest of the app uses "3 abr 2017". Seen on every date tested.
- **como reproduzir:** GET /api/score-model?date=2017-12-04 -> training.sentence; GET /api/login?date=2017-10-02 -> panel.sentence.

### 8. [baixo] Wrong article: "vendedores da Leste" / "da Oeste"

- **onde:** /api/account?name=Mathtouch&date=2017-12-04 (history.sellers_label); engine/accounts.py:228
- **detalhe:** sellers_label is built as "%s da %s" with the region label, which gives "vendedores da Leste" (should be "do Leste" or "da regional Leste"). The same happens for every client served by Leste or Oeste.
- **como reproduzir:** GET /api/account?name=Mathtouch&date=2017-12-04 -> history.sellers_label = "vendedores da Leste".

### 9. [baixo] Region reason stops holding near the end of the base

- **onde:** /api/data-quality?date=2017-12-04 and date=2017-12-25 (regions.sentence)
- **detalhe:** On 2017-12-04: "A Central só tem deals abertos recentes...". All Central deals entered in Jul–Aug 2017, and on 12-04 the oldest is exactly 138 days. By 12-25, 361 of the 467 Central open deals are past 138 days, and the sentence changes to "A parte dos abertos que está sem desfecho vai de 67% (Leste) a 77% (Central)... Por isso o app não compara vendedores...". If the shares are that close, the "Por isso" no longer follows.
- **como reproduzir:** GET /api/data-quality?date=2017-12-25 -> regions.sentence; Central 467 open, 361 with no outcome.

### 10. [baixo] Statistical jargon and cohort not stated

- **onde:** /api/score-model (signals: Vendedor, Histórico de compras) and /api/accounts (note)
- **detalhe:** (a) Vendedor: "Só 2 passam do limite de distância da média que o acaso ultrapassa 5 vezes em 100. Só pelo acaso, já se esperariam 1 ou 2." This is a significance test in disguise, hard to read. Also "cabem no acaso". (b) /api/accounts note: "A taxa de ganho varia entre clientes dentro do acaso". (c) Histórico: "Entre os fechados, a taxa de ganho é 59,5% com venda anterior (2.305 deals) e 60,9% sem (729 deals)". This is the cohort that entered from 1 abr to 14 ago, not all 6.711 closed deals, and the sentence does not say so (both rates are also below the company's 63,2%, which confuses the reader).
- **como reproduzir:** GET /api/score-model?date=2017-12-04 -> signals; GET /api/accounts?date=2017-12-04&region=East -> note.

### 11. [baixo] "42 dos seus 49 maiores deals": the top list is inflated by price ties

- **onde:** /api/seller?name=Darcel%20Schlecht&date=2017-12-25 (insights[1].title)
- **detalhe:** top_by_price takes the top 10 and keeps going while the price is tied, so it becomes "49 maiores" (all GTX Plus Pro). The same pattern shows "12", "15", "16" or "20 maiores" for other sellers. A reader expects about 10 deals.
- **como reproduzir:** GET /api/seller?name=Darcel%20Schlecht&date=2017-12-25 -> insights[1].title.

### 12. [baixo] "deal antigo quase não fecha" vs "nenhum deal com mais de 30 dias fechou"

- **onde:** /api/seller?date=2017-10-02 (date.context_sentence) vs /api/data-quality (quarter_rhythm.body)
- **detalhe:** On 2017-10-02 the context says "nesta base, deal antigo quase não fecha agora", while data quality states that in the first month of the quarter no deal over 30 days closed (0 of 3.438, which the CSV confirms). Same fact, two strengths. Also, 2017-10-09 (same window, 0–14) uses a different phrase ("os deals novos, de até 14 dias, são os que mais fecham agora").
- **como reproduzir:** GET /api/seller?name=Reed%20Clapper&date=2017-10-02 and date=2017-10-09 -> date.context_sentence.

### 13. [baixo] Wording and mixed terms

- **onde:** /api/sources (alert); /api/login (stats[2].label); /api/team (agenda bodies)
- **detalhe:** (a) "Tela apenas para referência, os dados vêm da base fornecida para o desafio e não de alguma integração.": comma splice, and "de alguma integração" should be "de uma integração". (b) The same concept is called "sem desfecho", "parados" (login: "sem os deals parados"; team: "Sem deals parados", "Sua carteira não tem deal parado") and "sem resposta" ("A taxa oficial esconde 779 deals sem resposta"). Three names for one thing confuse a skeptical reader.
- **como reproduzir:** GET /api/sources; GET /api/login?date=2017-12-04; GET /api/team?manager=Melvin%20Marxen&date=2017-12-04.


## O que foi feito com os achados

**Testes ao final.** python3 -m unittest discover -s tests -t . rodou 184 testes e todos passaram (eram 161) no Python 3.9.6. Nenhum Python 3.11+ estava disponível na máquina; a diferença do 3.12 é coberta pelo regex e pelos testes com '20171204' e '2017-W49-1'. Os números de referência (empresa, Daniell, Darcel, Reed, Rocco, regionais, prova, máquina do tempo, Mathtouch, qualidade e login) continuam conferidos pelos testes. Um teste novo mostra que a base cortada em 4 dez dá exatamente o mesmo retrato da base inteira nessa data.

### Corrigidos (32)

1. **auc.score não mede o score: mede a chance**: engine/proof.py _auc_block: a chave virou auc.chance (0,780). Entraram auc.expected_value (0,7057, a ordem que o app usa, com a receita esperada em 2 casas), age_only e price. Docstring diz o que cada uma mede. Testes em test_proof e test_api; API.md atualizado.
2. **/api/account com viewer gestor nunca marca is_viewer**: Nova função shapes.viewer_scope (gestor = time dele), usada por accounts.detail e model_page (fim do _viewer_scope duplicado). Testes com Rocco Neubert na Mathtouch e na Acme. O exemplo do revisor, Melvin Marxen, não tem deals na Acme: os vendedores citados são do time do Rocco.
3. **Validação de data muda entre Python 3.9 e 3.12**: core.parse_date exige o regex ^\d{4}-\d{2}-\d{2}$ antes do fromisoformat. Testes com '20171204', '2017-W49-1', '2017-12-4' e '2017-12-04T00:00' em test_core e test_api.
4. **405 não lê o corpo e dessincroniza o keep-alive**: server._not_allowed marca close_connection e manda Connection: close. Teste com socket cru (POST com corpo seguido de GET): sai só o 405 e nenhum 501.
5. **Tag 'Maior carteira' falsa em algumas datas**: engine/access.login: a tag 'Maior carteira' só sai para quem tem o maior valor declarado na data. Os outros recebem 'Carteira em dia' ou 'Carteira com deals sem desfecho'. O teste confere as 26 datas (em 3 jul e 25 dez, Darcel não recebe a tag).
6. **'é o ritmo de fim de trimestre' afirmado sem base**: accounts._month_sentence: a frase do ritmo só sai se a média dos meses de fim de trimestre for pelo menos 1,5x a dos outros meses (QUARTER_END_LIFT). Se for só um pouco maior, sai 'vendem só um pouco mais'. Acme e Umbrella não dizem mais 'ritmo'; Mathtouch continua dizendo.
7. **Ação 'segue de pé' para deal de 15 dias e 'já passou da faixa' com a mesma chance**: seller._action no caso 'tarde': (1) se a chance da faixa do deal for >= ao limite da janela, o texto diz que ela fecha quase tanto quanto a melhor; (2) perto de 138 dias, o texto de antes; (3) nos demais, um texto neutro com a janela e a chance da faixa, sem 'segue de pé'. Teste com 6R6S91WE em 3 jul (17% contra 18%).
8. **'É mês de fechar' / 'ainda em dezembro' com 6 dias e chance de 19-22%**: Entraram core.phase_title, closing_is_strong (pico >= 30%) e days_to_quarter_end. Em 25 set e 25 dez o título é 'Fim de trimestre' e a mensagem diz 'Dezembro fecha o trimestre.'. A frase dos 'deals maduros' só sai com pico forte. 'ainda em <mês>' só sai com 14 dias ou mais até o fim do trimestre. PHASE_TITLES ficou num lugar só (rules).
9. **Desempate do id muda de sentido entre telas**: accounts.detail ordena os fechados por close_date decrescente e id crescente, igual ao pipeline. Teste com Condax.
10. **'3.438' conta pares deal-mês**: O número continua o da referência, mas o texto do item quarter_rhythm agora mostra os três dias, as parcelas 673, 1.015 e 1.750 e avisa que o mesmo deal pode contar mais de uma vez.
11. **Regional de casa muda com a data**: Nota fixa home_region_note em /api/accounts e /api/account. A regra ficou numa função só, core.home_region, que substitui as três cópias (accounts, model_page e quality). Teste com Kan-code: West em 3 jul, East em 11 set.
12. **Login conta deals que só entram depois da data**: O rótulo do card agora diz 'oportunidades na base inteira, até 31 dez 2017'. O valor 8.800 da referência ficou.
13. **Datas aceitas dependem do fim da base (latente)**: available_dates usa só FIRST_DATE e LAST_DATE. Novo teste com a base cortada em 4 dez: parse_date aceita a data e o retrato é idêntico ao da base inteira, o que também testa que não há vazamento.
14. **Qualquer ValueError interno vira 400**: Nova rules.InputError(ValueError) para erros de entrada (nomes, datas, filtros, parâmetro obrigatório). O servidor só devolve 400 para InputError; outro ValueError vira 500 genérico. Teste com max([]).
15. **Erros da biblioteca em HTML inglês e header Server com versão do Python**: Handler.send_error responde em JSON em português. O 501 de método desconhecido (TRACE, inventado) vira 405 JSON. version_string devolve só 'LeadScorer/1.0'. Testes para 414, versão HTTP inválida, TRACE e cabeçalho Server.
16. **Parâmetro repetido sem documentação e erro ecoando entrada sem limite**: Nova core.echo corta a entrada em 60 caracteres em todas as mensagens (nomes, data, regional, rota 404). API.md documenta que vale o último parâmetro e que a mensagem é texto puro, a escapar no front. Testes com nome de 20 mil caracteres e rota de 5 mil.
17. **Conexão ociosa sem timeout e bind em 0.0.0.0**: Handler.timeout = 30 s. O bind vem de HOST (padrão 127.0.0.1) e o Dockerfile define HOST=0.0.0.0 para o deploy.
18. **Vendedor só no cadastro: 200 em /api/seller e 400 em /api/team**: Uma regra só: core.resolve_working_seller, usada em focus, pipeline, time_machine, team e viewer (score-model e account). Todas devolvem 400 'X só está no cadastro: não tem deals na base.'
19. **Arquivo estático ausente volta como index.html**: Caminho com extensão que não existe dá 404 JSON, e caminho de arquivo com barra no fim não é servido. O fallback SPA segue para rotas sem extensão.
20. **Código morto e comentário enganoso**: Removidos display_key, STAGE_LABELS, LEVELS, SCORE_BANDS, Deal.outcome_at (e o docstring que mandava usá-lo), Dataset.by_id, deals_by_manager/region, os filtros manager/region de closed_before, Snapshot.by_id, o try/except e o fallback de _proof_stats e os ramos isinstance(d, str) de team e time_machine. Os testes que os usavam passaram a usar alternativas.
21. **Funções duplicadas e nomes iguais com sentidos diferentes**: Uma função de regional de casa (core.home_region). quality._share virou facts.share_or_none e team._share virou _fraction. Os dois _period_label viraram facts.base_period_label e proof._dates_label. top_by_price e time_machine usam stale_key. model_page._rate usa win_rate. Os títulos de fase ficaram unificados.
22. **quality.py passa de 450 linhas**: Dividido em engine/facts.py (fatos da base inteira), engine/access.py (meta e login, reexportados por quality) e quality.py (271 linhas). O arquivo maior agora tem 431 linhas.
23. **Testes que não testam o que dizem**: test_serializable usa allow_nan=False. O teste de threads da prova usa uma base nova, com o cache vazio. test_parse_date cobre os formatos aceitos no 3.11+. Entraram testes de viewer gestor, InputError contra 500 e outros.
24. **'dá empate' cobre uma pequena perda**: proof._sentences: 'empate' só quando arredonda a 0%. Com -1,1%, o texto diz 'quase empata: o score fica 1% abaixo.'
25. **Datas fora do formato '4 dez 2017'**: Os rótulos de data dos textos seguiram o formato do app: _days_list ('6 mar, 5 jun e 4 set 2017'), _dates_label ('de 3 jul a 27 nov 2017') e o painel do login ('Em 4 dez 2017').
26. **Artigo errado: 'vendedores da Leste'**: sellers_label agora sai 'vendedores da regional Leste'.
27. **Motivo por regional deixa de valer perto do fim da base**: _regions_sentence: o 'Por isso' só sai no caso da Central sem nenhum deal sem desfecho. No outro caso a regra vem como frase própria, sem nexo causal. Teste nas 26 datas.
28. **Jargão estatístico e grupo não informado**: O texto do sinal Vendedor foi reescrito ('Só 2 vendedores ficam longe da média... o acaso sozinho já daria 1 ou 2 casos assim'). A nota da lista de clientes saiu do 'dentro do acaso'. O texto do histórico agora diz que as taxas são 'dos que fecharam desse mesmo grupo'.
29. **'42 dos seus 49 maiores deals' inflado por empates**: _pipeline_card: quando o empate estica o top 10, o grupo vira 'seus N deals de <produto>' (um produto só) ou 'seus N deals de maior preço'. Daniell: '10 dos seus 12 deals de GTX Plus Pro'; Darcel em 25 dez: '42 dos seus 49 deals de maior preço'.
30. **'deal antigo quase não fecha' contra 'nenhum fechou'**: A frase de contexto agora diz 'deal com mais de 60 dias quase não vira venda nos 30 dias seguintes' (é o horizonte do modelo, diferente do 'no mês' da qualidade). Quando a chance é exatamente zero, diz 'nenhum'. Teste confere as duas variantes contra a tabela.
31. **Redação e termos misturados**: O alerta de fontes foi corrigido. 'sem resposta' e 'parado' viraram 'sem desfecho' no time e no login: 'N deals sem desfecho esperam uma decisão', 'A taxa oficial deixa de fora N deals sem desfecho', 'Você não tem deal sem desfecho', 'já tirando os sem desfecho'. Teste proíbe 'parad' e 'sem resposta' nos textos do time.
32. **Coluna Prospecção usa o estado final da base**: Só ajuste de texto: a nota da coluna diz que a lista é a do fim da base e que não dá para saber desde quando cada deal está ali. O MODELO manda mostrar os Prospecting sem data na coluna, e Darcel precisa ter 111 em qualquer data, então a regra não mudou. API.md registra isso.

### Mantidos como estavam, com justificativa (6)

1. **A interface não existe: abrir o navegador dá 404 (web/ vazia)**: Não corrigido nesta etapa e continua sendo o maior risco da entrega. Reproduz: web/ está vazia e GET / dá a página 'Interface não encontrada' com 404. Esta etapa corrige achados da API; construir o front inteiro (várias telas) é outra entrega do workflow, e o servidor já serve web/index.html quando ela existir. Até lá, 'python3 server.py e abrir o navegador' falha.
2. **Telas de trabalho expõem o cliente dos deals abertos**: Reproduz (397 vivos sem cliente em 3 jul, nenhum fechou), mas o MODELO diz que account é mostrado como está na base e nunca entra em chance, score, ordem ou prova. Os números de referência exigem as contagens com e sem cliente (Daniell 21/17, Mathtouch 13 abertos com o cliente no campo). Por isso não removi. API.md agora diz isso nas convenções, e a qualidade dos dados já explica o vazamento.
3. **Lista de vendedores com deals vem da base inteira (latente)**: Não reproduz nesta base: o primeiro deal mais tardio de um vendedor é de dez 2016, e não há diferença nas 26 datas. Mudar a definição de 'vendedor com deals' mexeria em contagens de referência (30 vendedores, tamanhos de time) sem efeito real. Agora há uma regra só (resolve_working_seller) para quem não tem nenhum deal.
4. **Receita esperada do time 153.815 contra a soma das linhas 153.814**: Não há uma regra que bata com as duas referências. Arredondar o total exato dá a referência da empresa (929.174); somar as linhas arredondadas daria 929.170. O 153.814 do time é a soma das linhas, como o teste já registra. Mantive uma regra só (arredondar o total exato) para não contradizer a referência da empresa.
5. **'+10%' em outubro e novembro contra a referência 1,11**: O número está certo: o MODELO pede a expectativa exata no desempate, que dá 0,104, e a referência diz 'cerca de'. Corrigi só a palavra 'empate', que escondia uma perda de 1%.
6. **money_short marcado como código morto**: O formato curto 'US$ 7,0 mi' é exigido na FORMATAÇÃO de engine/fmt.py, para uso do front, e tem teste. Mantido. O resto do código morto foi removido.

### Notas de quem corrigiu

A interface continua faltando: web/ está vazia, então 'python3 server.py e abrir o navegador' ainda dá 404. É o achado alto que ficou sem correção; o front é outra entrega do workflow. Comandos git não foram usados. O git status mostra arquivos antigos apagados (leadscorer/, static/, app.py, analysis/, docs/) que já estavam assim antes deste trabalho; não mexi neles.

Mudanças que quebram o contrato da API (o front precisa seguir):
- auc.score virou auc.chance e entrou auc.expected_value.
- Vendedor que só está no cadastro agora dá 400 também em /api/seller, /api/pipeline, /api/time-machine e no viewer.
- Os títulos de fase podem ser 'Fim de trimestre'.
- Os títulos do time agora falam em 'sem desfecho'.
- Arquivo com extensão inexistente em web/ dá 404.
- O servidor escuta em HOST (padrão 127.0.0.1; o Dockerfile usa 0.0.0.0).

Arquivos novos (todos em solution):
- engine/facts.py
- engine/access.py

Arquivos alterados (no mesmo diretório):
- engine/core.py, rules.py, shapes.py, accounts.py, seller.py, team.py, proof.py, model_page.py, quality.py
- server.py, Dockerfile, API.md
- tests/test_core.py, test_accounts.py, test_seller.py, test_team.py, test_proof.py, test_quality.py, test_model_page.py, test_shapes.py, test_api.py
