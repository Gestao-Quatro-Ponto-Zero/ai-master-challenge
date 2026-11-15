# Revisão independente da interface (3 revisores, 38 achados)

> Depois de integrada, a interface foi lida por três revisores independentes: contrato com a API e erros de execução, segurança e acessibilidade, e fidelidade ao estudo de UX. Saída bruta de agentes de IA, sem edição além da remoção de caminhos locais.


## Revisor: contrato-e-execucao

**Resumo do revisor.** Li todos os 19 módulos de assets/js (app.js, core/*, views/*, views/foco/rows.js). Todos passam no checkModuleSyntax do jsc, e não há console.log, eval nem innerHTML fora de dom.js. Conferi o contrato com a API viva, que está em 127.0.0.1:8077. Varri /api/seller, /api/pipeline e /api/time-machine para os 30 vendedores nas 26 segundas (de 2017-07-03 a 2017-12-25). Varri /api/team nas 26 datas com a empresa inteira, as 3 regionais, os 6 gestores, os 30 vendedores sozinhos e cada vendedor com o seu gestor. Varri /api/score-model nas 26 datas, tendo como viewer cada um dos 30 vendedores e dos 6 gestores. Varri /api/accounts com as 4 regiões em 4 datas, e /api/account para os 85 clientes em 2017-07-03 e 2017-12-25, tendo como viewer um vendedor e um gestor. Li também /api/login, /api/proof, /api/sources e /api/data-quality. Foram usados casos de borda reais: vendedor sem deal sem desfecho (Reed Clapper, a Central em julho), vendedor com poucos deals (Garret Kinder em 27 nov, com 7 abertos), a Central com prospecção (Anna Snelling, Darcel Schlecht) e "Gekko & Co" com & e espaço. Resultado: todo campo que o front lê existe com o nome e o tipo esperados. Nas varreduras, window, fair, example, why, summary, bands, insights, agenda e messages nunca vieram nulos ou vazios. Os máximos e as larguras de barra estão protegidos contra lista vazia, os únicos reduce sem valor inicial têm guarda de tamanho, e o front não acessa [0] de lista vazia sem proteção. Os parâmetros são codificados com URLSearchParams: o servidor aceita "Gekko+%26+Co" (resposta 200) e os seletores usam CSS.escape. O createScope impede que uma resposta antiga sobrescreva a nova, e os ouvintes em root são removidos na limpeza quando o motivo é 'params'. Nenhum percentual recalculado no front diverge do da API: em 472 frases de resumo do Foco, o arredondamento do front bate com o número da frase. Não encontrei erro de execução que quebre uma tela. Os achados abaixo são um link de pauta que não leva ao que o rótulo promete, textos e rótulos que o front recompõe em vez de usar o campo pronto da API, e estado que não reinicia ao trocar de pessoa.

**Achados: 13**

### 1. [medio] O link da Pauta da Gabi promete o time inteiro e abre só um vendedor

- **onde:** Meu time · solution/web/assets/js/views/time.js:290-308 (topTeamSeller/agendaLink), usado em 315
- **detalhe:** A API manda, em agenda[].link_label, rótulos como "Ver os 153 deals" (link_target 'sem_desfecho') e "Ver os 42" (link_target 'quentes') para o time inteiro. Exemplo real: Cara Losch em 2017-12-04. O front transforma esse link em #/foco?vendedor=<quem mais tem>&aba=sem_desfecho|quente. O gestor clica em "Ver os 153 deals" e cai na lista de Corliss Cosme, que tem 60 sem desfecho. Clica em "Ver os 42" e vê os 15 quentes de Corliss. Para um avaliador cético, parece número inventado.
- **correção sugerida:** Uma saída é levar a uma visão que de fato mostre os 153: a própria tabela do Meu time com destaque, ou um filtro. Outra é trocar só o texto do link no front (por exemplo "Ver os de Corliss"), mantendo o destino. A terceira é pedir à API um link_label/link_target por vendedor. A frase da API não deve ser reescrita: o ajuste vale só para o texto do link.

### 2. [baixo] Data de fechamento reformatada no front em vez de usar close_label

- **onde:** Pipeline · solution/web/assets/js/views/pipeline.js:43-48 (shortDate) e 84-92 (closedCard)
- **detalhe:** Os deals fechados de /api/pipeline já trazem close_label ("3 dez 2017"). O front ignora esse campo, pega close_date e monta o próprio rótulo, tirando o ano ("3 dez"). Esse rótulo recalculado diverge do usado em Clientes › Fechadas, que mostra deal.close_label com o ano: o mesmo deal aparece com duas datas diferentes.
- **correção sugerida:** Usar deal.close_label como vem, nas duas telas, e apagar shortDate.

### 3. [baixo] O limite de dias é extraído por regex de uma frase da API

- **onde:** Pipeline · solution/web/assets/js/views/pipeline.js:50-55 (staleDays), 110-113 e 176
- **detalhe:** O subtítulo ("A coluna tracejada separa o que passou de 138 dias") e o texto de coluna vazia tiram o número do hint da coluna stale ("US$ 146.909 · mais de 138 dias") com /(\d[\d.]*)\s*dias/. Hoje funciona nas 780 combinações, mas qualquer mudança no texto da API apaga a frase sem aviso. Pior: um hint como "mais de 1.380 dias" seria capturado com o ponto.
- **correção sugerida:** Ler o número de um campo cru: max_cycle de /api/score-model, ou window.max_days de /api/seller. Outra opção é pedir à API um campo stale_days na coluna.

### 4. [baixo] "Mais de 138 dias" fixo no código

- **onde:** Clientes, painel › Em aberto · solution/web/assets/js/views/clientes.js:250
- **detalhe:** O rótulo do grupo Sem desfecho é um literal. Hoje max_cycle vale 138 em todas as datas, mas o número não vem da API, ao contrário de Foco e Meu time, que leem da resposta. Se o motor mudar o limite, o painel mostra um número errado sem nenhum erro.
- **correção sugerida:** Usar um campo da API (bands.stale.rule de /api/score-model, ou pedir open.stale_rule em /api/account) em vez do literal.

### 5. [baixo] "Até <véspera>" recalculado no front

- **onde:** Clientes, painel › Dados · solution/web/assets/js/views/clientes.js:40-45 (dayBefore) e 155
- **detalhe:** O front calcula a véspera da data simulada com Date e formata com fmt.dateLabel. A API já entrega esse corte pronto: closed.value_label diz "em vendas, até 3 dez 2017" e note/home_region_note falam da véspera. O resultado bate hoje, mas é uma regra de negócio (até onde vai o histórico) duplicada no front.
- **correção sugerida:** Pedir à API um history.until_label, ou reaproveitar o rótulo já enviado. Depois, apagar dayBefore.

### 6. [baixo] Frases dos passos 1 e 3 compostas no front, duplicando example.steps

- **onde:** Como o score funciona · solution/web/assets/js/views/score.js:6-12
- **detalhe:** O front escreve "Se 196 de 391 viraram venda, a chance é 50%" e "Score 98 quer dizer: receita esperada igual ou maior que a de 98% dos deals vivos". A API já manda essas frases em example.steps, e a segunda vem mais precisa: "98% dos 1.299 deals vivos da empresa". Hoje os números coincidem, mas a frase é uma reescrita no front de algo que a API entrega pronto.
- **correção sugerida:** Usar example.steps nos cards (ou pedir à API os textos dos passos) e manter no front só os títulos fixos.

### 7. [baixo] Dinheiro em "US$ 7,0 mi" e médias fracionárias mostradas como inteiras

- **onde:** Máquina do tempo · solution/web/assets/js/views/maquina.js:34-36 (millions) e 157-160 (pairText)
- **detalhe:** millions() formata a receita das regras como "US$ 7,0 mi", fora do padrão de dinheiro do projeto ("US$ 5.482"). Em pairText, as vendas por data vêm fracionárias da API, porque são médias de desempate (score.wins 41,45; value_only.wins 17,81). O front arredonda para "41 vendas pelo score e 18 só por valor" sem dizer que é média, e o leitor pode somar e não chegar ao total.
- **correção sugerida:** Formatar a receita com fmt.money ou pedir um rótulo pronto à API, por exemplo rules[k].revenue_label. Em pairText, usar 1 casa ("41,5") ou o texto "em média", ou pedir o rótulo pronto por data.

### 8. [baixo] Chip "Todos" não conta a coluna Prospecção

- **onde:** Pipeline · solution/web/assets/js/views/pipeline.js:144-154
- **detalhe:** counts.all da API soma só Em negociação e Sem desfecho. Para vendedores da Central, por exemplo Anna Snelling em 2017-07-03, o chip mostra "Todos 52", mas o quadro tem mais 55 cartões em Prospecção. Isso vem do contrato da API, mas o rótulo "Todos" sugere tudo o que está na tela.
- **correção sugerida:** Trocar o rótulo do chip para algo como "Todos os abertos com data", ou explicar no rodapé que o filtro vale só para Em negociação e Sem desfecho. Também dá para pedir à API um rótulo pronto.

### 9. [baixo] A busca de cliente não reinicia ao trocar de pessoa ou de data

- **onde:** Clientes · solution/web/assets/js/views/clientes.js:16 e 516
- **detalhe:** view é variável de módulo, e search: view?.search ?? '' carrega o termo para a nova tela mesmo quando o motivo é 'user' ou 'date'. Quem sai e entra como outra pessoa encontra a tabela já filtrada pela busca da pessoa anterior.
- **correção sugerida:** Carregar a busca só quando ctx.reason === 'params'. Nos outros motivos, começar com ''.

### 10. [baixo] Ao trocar de vendedor, ?aba= do anterior continua

- **onde:** Moldura, seletor de vendedor do gestor · solution/web/assets/js/app.js:338
- **detalhe:** openSellerPicker limpa o parâmetro deal, mas mantém aba. Quando o gestor chega ao Foco pela pauta (aba=sem_desfecho) e troca de vendedor, o novo vendedor abre direto na aba Sem desfecho em vez da primeira faixa com deals.
- **correção sugerida:** Na troca de vendedor, limpar também aba (aba: undefined), como já é feito com deal.

### 11. [baixo] Erro em /api/login deixa o painel escuro vazio

- **onde:** Acesso simulado · solution/web/assets/js/views/login.js:224 (com o painel em 37 e 102)
- **detalhe:** ui.load mostra o erro e o botão "Tentar de novo" só em [data-body]. O painel lateral [data-panel] continua vazio e sem esqueleto, e a metade direita da tela fica em branco enquanto carrega ou quando dá erro.
- **correção sugerida:** Mostrar um esqueleto e uma frase de erro também no painel, ou desenhar o painel com um estado neutro até os dados chegarem.

### 12. [baixo] focusAfterDate pode sobrar e mover o foco mais tarde

- **onde:** Máquina do tempo · solution/web/assets/js/views/maquina.js:15 e 294-301
- **detalhe:** Ao clicar numa barra do gráfico, focusAfterDate fica com pair:true e só é limpo quando o gráfico aparece. Se /api/proof falhar, a variável de módulo continua preenchida. Numa volta posterior à tela, depois do proof carregar, o foco pula para uma barra sem o usuário pedir.
- **correção sugerida:** Limpar focusAfterDate no erro da prova e na limpeza da tela (a função devolvida por render).

### 13. [baixo] Ícones sem uso (código morto)

- **onde:** solution/web/assets/js/core/icons.js:33-34
- **detalhe:** checkCircle e circle estão definidos em PATHS e não são usados em nenhum módulo.
- **correção sugerida:** Remover os dois.


## Revisor: seguranca-e-acessibilidade

**Resumo do revisor.** Revisão (só leitura) dos 34 arquivos de solution/web: 19 JS e 15 CSS. Também testei no navegador, em http://127.0.0.1:8077, com ?cliente=<img src=x onerror=alert(1)>, &aba=">..., localStorage corrompido e larguras de 1440, 1280, 1024 e 390 px. Não achei nenhum problema crítico de segurança. Todo HTML passa pelo template html`` de core/dom.js, que escapa tudo, e os atributos passam por ui.attrs. Não há eval, Function, javascript: nem handler inline. Há uma CSP restritiva em index.html (script-src 'self'). O ?cliente= malicioso aparece escapado no título do painel e na mensagem de erro da API, sem criar nenhum <img>. Nos seletores, os valores de URL e de dados passam por CSS.escape, com a exceção de pipeline.js. O localStorage é lido com try/catch, e usuário, data, decisões, tratados e prefs são validados; o JSON corrompido foi testado e o app abriu normalmente. A cópia tem fallback e avisa a falha. O fetch trata erro de rede, status diferente de 2xx e corpo não JSON, e cancela pedidos antigos. Na acessibilidade a base é boa: lang pt-BR, título por rota, foco vai para o h1 ao trocar de tela, abas e segmentados com role e setas, painel lateral com role=dialog, aria-modal, foco preso, Esc e devolução do foco, :focus-visible global e prefers-reduced-motion. Os achados são pontuais: contraste de dois textos pequenos com --color-text-subtle, menu de gaveta abaixo de 900 px sem comportamento modal, abas do Foco que rolam de lado em 1280 px (o que fere a regra de 1280 px), requisição sem tempo limite e pequenos ajustes de robustez e limpeza. Em 390 e 1024 px nada estourou a largura da página; as rolagens internas (pipeline, linha do tempo) ficam dentro do próprio bloco. Durante o teste mudei chaves leadscorer: no localStorage do navegador do painel: removi as chaves de teste, mas a última chave leadscorer:usuario gravada no teste (Daniell Hammack, vendedor) continua lá. A janela voltou ao tamanho padrão.

**Achados: 12**

### 1. [medio] Texto de 12 px em --color-text-subtle abaixo do contraste AA

- **onde:** solution/web/assets/css/views/maquina.css:184-188 (.tm-compare__saved) e solution/web/assets/css/views/qualidade.css:92-96 (.dq-item__scope)
- **detalhe:** #8B95A1 sobre #FFFFFF dá 3,04:1, sobre --color-chrome 2,76:1 e sobre --color-fill 2,57:1. O AA pede 4,5:1 para texto pequeno. Os dois casos são texto informativo de 12 px: o aviso 'Sua escolha fica salva só neste navegador.' (que a regra exige que a tela mostre) e o escopo do número em Qualidade dos dados. Para comparar: --color-text-muted dá 5,86 sobre branco e 5,33 sobre chrome; --color-window dá 4,39 sobre branco, ainda abaixo de 4,5. Win sobre win-soft (4,59) e loss sobre loss-soft (4,53) passam, mas por pouco. Os símbolos × e = de .score-op (score.css:120, 20 px normal, 3,04:1) também não são texto grande e ficam abaixo de 4,5 (estão com aria-hidden, mas a regra vale para o visual).
- **correção sugerida:** Use --color-text-muted em .tm-compare__saved e .dq-item__scope, e em .score-op se ela não for só decorativa. Reserve --color-text-subtle para bordas, ícones decorativos e estados desabilitados.

### 2. [medio] Menu de gaveta abaixo de 900 px não é modal: o Tab sai para o conteúdo atrás do fundo escuro

- **onde:** solution/web/assets/js/app.js:290-300 (setDrawer) e solution/web/index.html:41-45
- **detalhe:** Ao abrir o menu, só entram a classe is-open, o fundo (backdrop) e aria-expanded. O <main> continua focável e lido pelo leitor de tela, sem inert, sem foco preso e sem role=dialog. Quem navega pelo teclado sai do último item do menu direto para o conteúdo coberto pelo fundo escuro. O Esc e o clique no fundo fecham corretamente, e o foco volta para o botão.
- **correção sugerida:** Com o menu aberto, ponha inert em #conteudo e no restante da barra superior (menos o botão do menu) e tire ao fechar. Outra opção é reaproveitar o foco preso de ui.openPanel. Feche também ao passar de 900 px (matchMedia change) para não deixar inert para trás.

### 3. [medio] Em 1280 px as abas do Foco da semana rolam de lado e escondem parte de 'Sem desfecho'

- **onde:** solution/web/assets/css/components.css:236 (.tabs overflow-x: auto) e solution/web/assets/css/views/foco.css (coluna principal com --aside-width)
- **detalhe:** Medido no navegador em 1280×900: .tabs com scrollWidth 638 e clientWidth 546 (vendedor) e 636/546 (gestor vendo Boris Faz). A aba ativa mostra a dica ('· score 80 ou mais') e a de Sem desfecho sempre mostra '47 · mais de 138 dias', então a última aba fica cortada e nada indica que dá para rolar. Isso fere a regra 'de 1280 px para cima tudo cabe sem rolagem horizontal'. No mesmo tamanho, .score-chart__scroll de Como o score funciona rola 18 px (520/502, por causa de min-width 520px em score.css:200) e .table-wrap de Meu time com ?gestor=todos rola 7 px (593/586). Em 1440 px nada rola.
- **correção sugerida:** Abaixo de 1360 px: mostre a dica só na aba ativa (ou passe a dica de Sem desfecho para a linha de introdução), reduza o padding das abas ou deixe o .tabs quebrar linha (flex-wrap). Baixe o min-width do gráfico de score para cerca de 480 px e ajuste a largura das colunas da tabela do time (time.css:149-158) na faixa de 1280 a 1439 px.

### 4. [medio] fetch sem tempo limite: com o servidor travado, o esqueleto fica para sempre

- **onde:** solution/web/assets/js/core/api.js:60-67 (startFetch)
- **detalhe:** Erro de rede, status diferente de 2xx e JSON inválido são tratados. Mas se o servidor aceitar a conexão e não responder, a Promise nunca termina: a tela fica no esqueleto, sem mensagem e sem 'Tentar de novo'. Isso vale também para o boot (/api/meta), que fica em 'Carregando o app…'.
- **correção sugerida:** Junte ao controller um tempo limite (por exemplo setTimeout(() => controller.abort(new DOMException('tempo', 'TimeoutError')), 15000), limpo no finally) e transforme TimeoutError em ApiError('O servidor demorou para responder. Tente de novo.', 0). Separe de AbortError para não cair no cancelamento silencioso de ui.load.

### 5. [baixo] Resposta de /api/meta com formato inesperado deixa a página em branco

- **onde:** solution/web/assets/js/app.js:548-569 (boot) e 158-191
- **detalhe:** O boot só confere se a resposta é JSON. Se meta vier sem dates, sellers ou managers (por exemplo, numa versão da API fora de sincronia), currentDate, currentUser ou renderShell lançam TypeError fora de qualquer try. O #boot já foi escondido e #shell e #login-root seguem hidden, então a tela fica em branco. Isso fere a regra 'nunca deixe a tela em branco'.
- **correção sugerida:** Logo depois do request, valide o formato mínimo (Array.isArray(meta.dates) && meta.dates.length && Array.isArray(meta.sellers) && Array.isArray(meta.managers)) e chame showBootError se falhar. Envolva também o handleRoute inicial num try/catch que mostre o erro de boot.

### 6. [baixo] Seletor montado com a chave de coluna da API sem CSS.escape

- **onde:** solution/web/assets/js/views/pipeline.js:166 e 211
- **detalhe:** dom.qs(`[data-col="${key}"]`, body) usa column.key, que vem da API e do dataset do botão 'Mais'. Uma chave com aspas ou barra invertida faz o querySelector lançar SyntaxError dentro do ouvinte de clique: o botão para de funcionar e não aparece mensagem. Não é XSS (o seletor não vira HTML), mas o resto do código usa CSS.escape de forma consistente.
- **correção sugerida:** Use `[data-col="${CSS.escape(key)}"]`. Em redrawColumn, o alternativo é buscar por qsa('[data-col]').find((el) => el.dataset.col === key).

### 7. [baixo] Botões 'Conectar' só explicam por que não funcionam pelo atributo title

- **onde:** solution/web/assets/js/views/fontes.js:39-43
- **detalhe:** Os botões têm aria-disabled=true e continuam focáveis, mas o motivo ('Somente referência: nenhuma integração existe neste conceito') está só em title. O title não aparece no toque nem de forma confiável no foco pelo teclado, e alguns leitores de tela não o anunciam. O clique não faz nada e não dá retorno.
- **correção sugerida:** Ligue o botão a um texto visível ou sr-only com aria-describedby (o mesmo id para todos), ou mostre um ui.toast(CONNECT_HINT) no clique.

### 8. [baixo] Toasts disparados com o painel lateral aberto podem não ser anunciados

- **onde:** solution/web/assets/js/core/ui.js:308-316 (toast) com ui.js:348-428 (openPanel)
- **detalhe:** A região role=status do toast fica em document.body, fora do painel com aria-modal=true. O VoiceOver e outros leitores tratam o que está fora de um diálogo aria-modal como inerte e podem não ler a região viva. Isso afeta a cópia com fallback e qualquer aviso feito com o painel aberto.
- **correção sugerida:** Com o painel aberto, use uma região de status dentro do próprio painel (por exemplo um <p role=status class=sr-only> no side-panel__body), ou mova toastRegion para dentro do painel enquanto ele existir.

### 9. [baixo] aria-labelledby aponta para um id que ainda não existe

- **onde:** solution/web/assets/js/views/login.js:37 e 64
- **detalhe:** A section .login__panel nasce com aria-labelledby="login-panel-title", mas o <p id="login-panel-title"> só aparece depois que /api/login responde. Durante o carregamento, e para sempre se o pedido falhar, a região fica sem nome acessível. Além disso, se der erro, ui.load mostra o erro no corpo do formulário e o painel escuro fica vazio.
- **correção sugerida:** Ponha o rótulo fixo no layout (ou use aria-label até os dados chegarem) e, no erro, mostre também um estado vazio no painel.

### 10. [baixo] Regiões vivas aninhadas no boot

- **onde:** solution/web/index.html:35 com solution/web/assets/js/core/ui.js:241-247
- **detalhe:** #boot tem role=status e o skeleton() que entra nele traz outro <p role="status">Carregando…</p>. Status dentro de status pode ser anunciado duas vezes ou ignorado, conforme o leitor de tela.
- **correção sugerida:** Tire o role=status de #boot, ou passe uma opção para skeleton() não incluir o parágrafo de status quando ele for usado dentro do boot.

### 11. [baixo] Faixa de acentos escrita com caracteres combinantes literais

- **onde:** solution/web/assets/js/views/clientes.js:35 e solution/web/assets/js/views/login.js:12
- **detalhe:** O regex /[̀-ͯ]/g usa os caracteres U+0300 e U+036F direto no código, invisíveis no editor. Funciona, mas é frágil: um editor ou formatador pode normalizar e quebrar a busca sem acento. A mesma função normalize está duplicada nas duas telas.
- **correção sugerida:** Escreva /[̀-ͯ]/g e mova normalize para core/fmt.js (ou core/dom.js) para as duas telas usarem a mesma.

### 12. [baixo] Dois comentários colados numa só linha

- **onde:** solution/web/assets/js/views/foco/rows.js:1
- **detalhe:** A linha 1 termina em '...e o bloco aberto.// Tudo usa os textos e números da API...'. É sintaxe válida (tudo vira um comentário só), mas falta a quebra de linha; no estilo do resto do código são duas linhas.
- **correção sugerida:** Quebre a linha antes do segundo '//'.


## Revisor: fidelidade-ao-estudo

**Resumo do revisor.** Comparei as 11 telas do Paper (get_jsx de 18U-0, 1-0, D0-0, U4-0, 1Q8-0, 1XH-0, 25P-0, 2C1-0, 2K0-0, 2SR-0, 2ZE-0, mais o PNG da 09) com os módulos e o CSS em solution/web. A estrutura e a ordem dos blocos, os rótulos fixos, os tokens de cor, os ícones do menu e do trilho (conferi os traços SVG um por um), o estado ativo do menu e das abas e as larguras de coluna (Foco 52/1fr/204/92/68, Time 264/104/148, Fontes 156/120, Score 230/150, Qualidade 170/1fr/300 e 150/1fr, painel 440, Gabi 300 com respiro de 36) batem com o estudo em quase tudo. Achei um defeito visual real: o painel do cliente (06/06b) perde todo o espaçamento interno, porque a classe que o CSS espera nunca entra no painel. Conferi isso no navegador: o tabpanel fica com display block e gap normal. As demais diferenças seguem um padrão. O estudo usa tamanhos fora da escala de tokens (30, 15, 18, 22, 26, 34, 24, 11 px e espaçamento de letra 0.08em), e o código arredonda tudo para a escala 12/13/14/16/20/28/40/56 e para 0.06em. Isso dá diferenças de 1 a 6 px que um designer nota, sobretudo nos títulos de tela, nos números grandes e nos rótulos da Gabi. Há também duas divergências de texto fixo na tela 09 (uma muda um fato), o sexto item pedido em "Onde a IA errou" não existe no código, e há frases do estudo cortadas no Acesso e no Foco. Os acréscimos ao estudo, na maioria, ajudam: busca e regionais em Clientes, escolha da mensagem por vendedor, conta passo a passo, leitura do gráfico, avisos de "salvo só neste navegador". Dois deles usam text-subtle em 12 px e não passam no contraste AA.

**Achados: 13**

### 1. [alto] Painel do cliente sem espaçamento interno: a classe clientes-painel nunca é aplicada

- **onde:** solution/web/assets/css/views/clientes.css:117-133 (seletores .side-panel.clientes-painel); solution/web/assets/js/views/clientes.js:401 (openPanel sem classe); solution/web/assets/js/core/ui.js:354 (o painel só recebe class 'side-panel')
- **detalhe:** Todas as regras de clientes.css que deveriam espaçar o painel começam com .side-panel.clientes-painel, mas nenhum JS adiciona essa classe (grep sem resultado; no navegador o painel tem className 'side-panel', o tabpanel tem display:block e gap:normal). Efeito, comparado com 06 (1XH-0) e 06b (25P-0), onde o corpo do painel tem gap 20 entre blocos: na aba Dados, o fio de 'O que mais compra' e o de 'Cadastro' encostam no bloco de cima, e a nota cinza cola no Cadastro; na aba Em aberto, o alerta dourado, 'Em negociação' e 'Sem desfecho' ficam sem respiro; na aba Fechadas, os números, 'Vendas por mês' e 'Mais recentes' também. Também deixam de valer o alinhamento do ícone do alerta pelo topo (o estudo usa align start para o texto de duas linhas) e o overflow-wrap do título.
- **correção sugerida:** Passar uma classe ao openPanel (por exemplo um parâmetro className) ou trocar os seletores para escopo próprio (.side-panel [data-panel-body] .tabpanel { display:flex; flex-direction:column; gap:20px }) e conferir as três abas.

### 2. [medio] Escala tipográfica arredondada: títulos, números e rótulos ficam 1 a 6 px fora do estudo

- **onde:** solution/web/assets/css/components.css:4-11, 39-50, 615-695, 717-727, 474-487; shell.css:164-173; views/*.css (lista no detalhe)
- **detalhe:** O estudo usa tamanhos fora da escala de tokens e o código arredonda. Diferenças que um designer nota: título de tela 30/36 no estudo e 28/34 no código (.screen-title); subtítulo de tela 15/22 e 16/22 (.screen-sub); rótulo da tela nas pranchas 01 a 04, 0.08em e 0.06em (.eyebrow); título do menu lateral 15/20 e 16/20 (shell.css:170); iniciais do avatar 11 e 12 (components.css:483); Gabi: título do cabeçalho 15 e 16, rótulo do cartão 11 px/0.08em e 12/0.06em, título do cartão destacado 18/24 e 20/26, título do cartão comum 15/21 e 16/22 (components.css:634-695); Foco: score da linha 22 e 20 (foco.css:200), chance 15 e 16 (foco.css:283); Meu time: KPIs laterais 22/30 e 20/30 (time.css:68), títulos de seção 18/24 e 20/26 (time.css:111), cabeçalho da tabela 11 px/0.08em e 12/0.06em; Máquina: data atual 18/24 e 20/26 (maquina.css:42), frase da prova 15 e 16 (maquina.css:401), títulos dos limites 15/21 e 16/22 (maquina.css:596); Clientes: título do painel 26/32 e 28/32 (components.css:813), valor principal 34/40 e 40/48 (clientes.css:154), mini-números 18/24 e 20/26 (clientes.css:197), números das Fechadas 24/30 e 28/34 (clientes.css:205), score da linha 18/24 e 20/24 (clientes.css:363), rótulos dos meses 11 e 12 (clientes.css:477); Score: termos do exemplo e selo 26/32 e 28/32 (score.css:105), × e = 22 e 20 (score.css:122), nome do exemplo 15 e 16, faixas dt 15/20 e 16/20 (score.css:306), título da chamada final 18/24 e 20/26 (score.css:423), contagens do eixo 11 e 12; Qualidade: números grandes 26/32 e 28/34 (qualidade.css:31, 85), título do item 15/21 e 16/22 (qualidade.css:108); Como chegamos aqui: título da etapa 15/20 e 16/20 (chegamos.css:37); Acesso: título 30/36 e 28/34, botão 15 e 16 (components.css:137), selo Conceito 11 px em pílula e 12, manchete 60/66 e 56/62 (login.css:260), números 22 e 20 (login.css:295), frase do painel #C6CED8 e on-ink-muted #A9B4C0. O próprio estudo é incoerente (0.08em de 01 a 04, 0.06em de 05 a 10).
- **correção sugerida:** Decidir uma vez: ou o estudo ganha a escala de tokens (atualizar o Paper), ou entram tokens extras (15, 18, 22, 26, 30 e o rótulo de 11 px) e o código passa a usá-los. Do jeito que está, cada tela fica um pouco maior que o desenho.

### 3. [medio] Tela 09: texto do último erro da IA muda um fato em relação ao estudo

- **onde:** solution/web/assets/js/views/chegamos.js:101-103
- **detalhe:** Estudo (2SR-0 e PNG): "No fim da base, um em cada três tem. O erro estava em duas telas e foi pego quando o app recalculou cada frase a partir do dado." Código: "Na verdade um em cada três tem. O erro estava em três telas e foi pego quando o app recalculou cada frase a partir do dado." Muda a quantidade de telas (duas para três) e tira o recorte temporal "No fim da base", que importa porque a tela 10 mede isso no fim da base. É texto fixo, não vem da API.
- **correção sugerida:** Confirmar qual versão está certa e alinhar estudo e código; se 'três telas' estiver certo, atualizar o Paper e manter 'No fim da base'.

### 4. [medio] Tela 09: o sexto item pedido em "Onde a IA errou" não está no código

- **onde:** solution/web/assets/js/views/chegamos.js:78-104
- **detalhe:** O briefing diz que o sexto item de "Onde a IA errou" é um acréscimo pedido (e por isso não deveria aparecer como divergência), mas o código tem só 5 itens: Tempo de fechamento inflado, Ranking de vendedores, "Cliente pequeno fecha menos", +42% contra um adversário fraco e "Deal aberto quase nunca tem cliente". O estudo também tem 5, então o acréscimo não foi feito em nenhum dos dois. O outro acréscimo, "Inventário e limpeza", está presente.
- **correção sugerida:** Acrescentar o sexto item combinado (título e texto) em COLUMNS[2].items, ou confirmar com quem pediu se ele foi abandonado.

### 5. [baixo] Tela 09: "Design e ideia de entrega" foi reescrito em relação ao estudo

- **onde:** solution/web/assets/js/views/chegamos.js:43-46
- **detalhe:** Estudo: "Design e idéia de entrega" / "A idéia de utilizar o design do G4OS e simular como se fosse um modulo do G40S para que sirva de idéia futura como serviço a ser entregue na plataforma". Código: "Design e ideia de entrega" / "A ideia de utilizar o design do G4 OS e simular o app como se fosse um módulo do G4 OS, para que sirva de ideia futura de serviço a ser entregue na plataforma." A mudança corrige ortografia (idéia, G40S, modulo) e é melhor que o original, mas o texto diverge.
- **correção sugerida:** Manter o código e corrigir o Paper, para estudo e app ficarem iguais.

### 6. [baixo] Acesso simulado: a dica sob a lista perde a indicação do gestor sugerido

- **onde:** solution/web/assets/js/views/login.js:160
- **detalhe:** Estudo (18U-0): "São 3 sugestões entre os 30. Para ver um time inteiro, troque o perfil para Gestor e escolha Rocco Neubert, da Leste." Código: "...troque o perfil para <strong>Gestor</strong>." O trecho "e escolha Rocco Neubert, da Leste" sumiu, e é ele que leva o avaliador ao gestor certo (o código até pré-seleciona DEFAULT_MANAGER = 'Rocco Neubert'). Também diverge: o placeholder da busca usa text-muted no código e text-subtle no estudo (login.css:112). Essa troca melhora o contraste e pode ficar.
- **correção sugerida:** Repor o final da frase, usando o nome e a regional do gestor padrão vindos de data.managers.

### 7. [baixo] Foco: nota do rodapé cortada e link "Ver os N deals" com ícone que o estudo não tem

- **onde:** solution/web/assets/js/views/foco.js:237; foco.js:229
- **detalhe:** Estudo (1-0): "O cliente não entra na conta: está vazio em 68% dos deals abertos e, nesta base, só é confiável depois que o deal fecha. O filtro Com cliente serve para navegar. Ver qualidade dos dados." Código: "O cliente não entra na conta: nesta base ele só é confiável depois que o deal fecha..." Falta o dado dos 68%, que é o argumento mais concreto da frase; se ele deve vir da API, hoje não vem. O link "Ver os 16 deals" no estudo é texto em negrito 13 px sem ícone; o código usa link-arrow com chevron. O código também acrescenta um contador "x de N tratados" sob "Por score. No empate, o mais antigo primeiro." (ajuda, mas empilha duas linhas cinzas onde o estudo tem uma).
- **correção sugerida:** Trazer o percentual de cliente vazio da API (data-quality ou seller) e repor o trecho; avaliar tirar o chevron.

### 8. [baixo] Painel do cliente (06b): coluna de data larga demais e detalhes de forma diferentes

- **onde:** solution/web/assets/css/views/clientes.css:488-495, 363, 370-372, 263-274, 463-467; solution/web/assets/js/views/clientes.js:218; components.css:272-276
- **detalhe:** Fechadas: a coluna de data tem 84 px no código (flex 0 0 84px) e 44 px no estudo; isso aperta o título do deal num painel de 440 px. Em aberto: o traço de sem score é "—" (travessão) no código e "–" (meia-risca) no estudo. Barras de produto e de mês: raio 999 e 6 no código, 3 no estudo. Abas: a contagem da aba ativa no estudo é 12 px na cor text (13 e 75 em Em aberto e Fechadas); no código .tab__count é sempre 13 px em text-muted.
- **correção sugerida:** Usar flex 0 0 44px na data, raio 3 nas barras e uma variante de contagem 12 px que fica text quando a aba está selecionada (só no painel; no Foco o estudo usa 13 px).

### 9. [baixo] Meu time: tracejado da barra grossa e posição da legenda diferentes

- **onde:** solution/web/assets/css/components.css:548-557 (.dualbar__rest e .dualbar--thick); time.css:267-276
- **detalhe:** No estudo (D0-0), a barra de 10 px do time tem tracejado de 1.5 px; o código herda 2px de .dualbar__rest (o tracejado de 2 px é o da barra fina do Foco). Legenda da tabela: no estudo, as chaves Vivo / Declarado ficam à esquerda e a nota "Taxa de ganho: a oficial e..." à direita na mesma linha (justify space-between); no código a nota desce para baixo das chaves.
- **correção sugerida:** .dualbar--thick .dualbar__rest { border-width: 1.5px } e .time-legend em linha com space-between de 1180 px para cima.

### 10. [baixo] Máquina do tempo: rótulos de mês, ponto passado, barras da prova e legenda do gráfico

- **onde:** solution/web/assets/css/views/maquina.css:3, 87-93, 441-446, 462-469, 559-568
- **detalhe:** Rótulos dos meses na linha do tempo e no eixo: 11 px/600/0.08em no estudo (U4-0); 12 px/0.02em (linha do tempo) e 12/0.06em (eixo) no código. Pontos passados: #B8C0CA no estudo, uma mistura de text-subtle com surface no código. É quase igual, e o hex do estudo nem é token. Barras das três regras: raio 4 px no estudo, pílula no código. Legenda do gráfico: no estudo as chaves ficam numa linha e "Vendas nos 10 primeiros, por data · barra mais alta: 108 em 30 listas" na linha de baixo; no código a frase entra na mesma linha das chaves, e há uma linha nova de leitura ao passar o mouse (acréscimo útil).
- **correção sugerida:** Ajustar o rótulo dos meses para 11 px/0.08em, se o token de 11 px for aceito, e o raio das barras para 4; manter a leitura no hover.

### 11. [baixo] Raios de 14 px do estudo viraram 12 px, e há pequenos desvios de respiro

- **onde:** solution/web/assets/css/views/fontes.css:6, 47; score.css:56, 409; components.css:395-410
- **detalhe:** Fontes (2C1-0): as caixas "Fonte em uso" e "Integrações de CRM" têm raio 14 px no estudo e 12 no código. Score (2K0-0): a faixa do exemplo e a chamada escura também têm 14 no estudo e 12 no código. Fontes: o estudo usa gap 24 entre cabeçalho, alerta e colunas; o código usa 28 (gap do painel e de .fontes-body). Pipeline (1Q8-0): os botões Segue/Encerrar do estudo têm ~26 px de altura e padding 4/9; o .decide do código tem 28 px e padding 10.
- **correção sugerida:** Decidir se 14 entra como token de raio; se não, atualizar o Paper. Respiro e botão de decisão são ajuste fino.

### 12. [baixo] Acréscimos em text-subtle de 12 px não passam no contraste AA

- **onde:** solution/web/assets/css/views/maquina.css:184-188 (.tm-compare__saved); qualidade.css:92-97 (.dq-item__scope)
- **detalhe:** Duas peças que não existem no estudo usam --color-text-subtle (#8B95A1) sobre branco em 12 px, cerca de 3:1, abaixo dos 4,5:1 do AA: "Sua escolha fica salva só neste navegador.", sob o botão Revelar/Esconder da Máquina do tempo, e o escopo do número em cada particularidade da Qualidade dos dados ("de 4 dez 2017" e afins). O estudo reserva text-subtle para separadores e ícones (o × e o = do Score, o número das etapas da 09, que no código já virou text-muted).
- **correção sugerida:** Trocar as duas por --color-text-muted.

### 13. [baixo] Peças que não estão no estudo: em geral ajudam

- **onde:** clientes.js:463-470; time.js:248-258; score.js:62-65; maquina.js:192, 381; pipeline.js:212-214; foco.js:195-197
- **detalhe:** Ajudam: chips de regional e busca em Clientes (o estudo não tem como trocar de regional); chips para escolher de qual vendedor é a mensagem em Meu time (o estudo mostra uma só, com "Há uma para cada vendedor"); "Ver a conta passo a passo" no exemplo do Score; leitura por data ao passar sobre o gráfico da Máquina; faixa "Você está vendo..." e seletor de vendedor para o gestor no Foco, no Pipeline e na Máquina; avisos "fica salvo só neste navegador", que as regras exigem. Discutíveis: toasts a cada clique em Segue/Encerrar e em Revelar/Esconder (redundantes com o estado do botão, que já muda); contador "x de N tratados" empilhado sob a frase de ordenação no Foco. Peças do estudo não implementadas: nenhuma relevante.
- **correção sugerida:** Manter os acréscimos; considerar tirar os toasts de Revelar/Esconder e o contador duplicado. Registrar os acréscimos no Paper para o estudo continuar sendo a fonte de verdade.


## O que foi feito com os achados

### Corrigidos (31)

1. **Painel do cliente sem espaçamento interno (classe clientes-painel nunca aplicada)**: ui.openPanel aceita um novo parâmetro className e clientes.js passa 'clientes-painel'. No navegador, o painel aparece com class 'side-panel clientes-painel' e o tabpanel com gap de 20 px. Com isso voltam a valer o gap, o alinhamento do alerta pelo topo e o overflow-wrap do título.
2. **Link da Pauta da Gabi promete o time inteiro e abre só um vendedor**: time.js: a frase da API continua igual; só o texto do link muda para o vendedor e a contagem dele, que vem crua da API (stale_count ou hot_count). Exemplo real com Cara Losch: 'Ver os 60 de Corliss Cosme' leva a aba=sem_desfecho e 'Ver os 15 de Corliss Cosme' leva a aba=quente.
3. **Fetch sem tempo limite**: api.js: um tempo limite de 15 s aborta com DOMException 'TimeoutError', separado do AbortError, e o timer é limpo no finally. Tempo esgotado, inclusive com o corpo parado no meio, vira ApiError('O servidor demorou para responder. Tente de novo.', 0), com o botão 'Tentar de novo'.
4. **Menu de gaveta abaixo de 900 px não era modal**: app.js setDrawer põe inert em #conteudo enquanto a gaveta está aberta e tira ao fechar. Um listener de matchMedia('(max-width: 899px)') fecha a gaveta quando a tela passa de 900 px. Conferido em 375 px: com a gaveta aberta, inert=true; depois do Esc, inert=false.
5. **Abas do Foco rolavam de lado em 1280 px (e gráfico do Score, tabela do time)**: Nas abas, ui.tabs passou a pôr a dica num span .tab__hint (novo helper ui.tabCount, usado também no syncTabs do Foco). Abaixo de 1360 px, só a aba ativa mostra a dica. No Score, o min-width do gráfico caiu para 480 px. Na tabela do Meu time, abaixo de 1440 px o cabeçalho pode quebrar linha. Medido em 1280 px: abas 546/546, gráfico 502/502 e tabela com ?gestor=todos 586/586.
6. **Texto de 12 px em text-subtle abaixo do AA (achado de dois revisores)**: .tm-compare__saved, .dq-item__scope e .score-op passaram a usar --color-text-muted.
7. **Tela 09: último erro da IA mudava um fato**: chegamos.js agora diz 'No fim da base, um em cada três tem. O erro estava em duas telas...', igual ao estudo. O process-log/README.md confirma: 'Corrigido nas duas telas'.
8. **Data de fechamento recalculada no Pipeline**: Os cartões usam deal.close_label da API ('3 dez 2017'), igual a Clientes › Fechadas. A função shortDate foi apagada.
9. **Limite de dias extraído por regex no Pipeline**: pipeline.js busca /api/score-model junto com /api/pipeline e usa o número cru max_cycle. staleDays não usa mais regex.
10. **'Mais de 138 dias' fixo no painel do cliente**: loadPanel busca /api/score-model em paralelo, e o grupo Sem desfecho mostra bands.stale.rule ('Mais de 138 dias').
11. **'Até <véspera>' recalculado no front**: dayBefore foi apagado. O título passou a 'Histórico fechado · antes de {data.date.label}': o rótulo vem pronto da API, no mesmo estilo da frase da API 'Antes de 4 dez 2017...'.
12. **Passos 1 e 3 do Score compostos no front**: Os cards usam example.steps[1] e example.steps[3] da API, depois de um texto fixo curto, e não repetem a frase. O teste do motor garante que as 4 frases estão sempre nessa ordem. O card 3 mostra '98% dos 1.299 deals vivos da empresa: score 98'.
13. **Dinheiro em 'US$ 7,0 mi' e médias mostradas como inteiras na Máquina**: millions() foi apagada e a receita das regras usa fmt.money ('US$ 6.994.434'). pairText e a legenda da barra mais alta usam 1 casa decimal ('41,5', '107,5'), com um comentário explicando que são médias de empate.
14. **Chip 'Todos' não contava Prospecção**: O rodapé do Pipeline agora diz que o filtro (Todos, Com cliente, Sem cliente) vale para Em negociação e Sem desfecho. O número continua o de counts.all, que vem da API.
15. **Busca de cliente sobrevivia à troca de pessoa ou de data**: O termo da busca só é mantido quando ctx.reason === 'params'. Nos outros motivos, a busca começa vazia.
16. **?aba= do vendedor anterior continuava**: openSellerPicker limpa aba junto com deal. Conferido: indo de Corliss na aba sem_desfecho para Garret, a URL fica #/foco?vendedor=Garret+Kinder e a tela abre na aba quente.
17. **Erro em /api/login deixava o painel escuro vazio, e aria-labelledby apontava para um id inexistente**: O painel nasce com aria-label 'Resumo da base' e mostra um esqueleto escuro (.login__panel-wait). Se a chamada falhar, mostra uma frase de erro. Quando os dados chegam, passa a usar aria-labelledby='login-panel-title'.
18. **focusAfterDate podia sobrar**: Ao carregar a prova, a Máquina guarda o pedido de foco que está pendente. Se o load não devolver dados (erro ou saída da tela) e o pedido ainda for o mesmo, ele é limpo. Um novo goTo não é apagado por engano.
19. **Resposta de /api/meta fora do formato deixava a tela em branco**: validMeta confere dates (não vazio), sellers, managers e dataset; se falhar, mostra o erro de boot. handleRoute agora devolve a promise do mount, e a primeira rota roda num try/catch que reexibe o erro de boot.
20. **Seletor com chave da API sem CSS.escape**: redrawColumn usa CSS.escape(key).
21. **Botões 'Conectar' explicavam o motivo só no title**: Os botões ganharam aria-describedby apontando para um <p class=sr-only> com o motivo, e o clique mostra ui.toast(CONNECT_HINT). O ouvinte é removido na limpeza da tela.
22. **Toasts com o painel aberto podiam não ser anunciados**: O painel ganhou uma região <p role=status class=sr-only> própria. Com o painel aberto, toast() escreve a mensagem também nela.
23. **Regiões vivas aninhadas no boot**: role=status foi removido de #boot no index.html. O esqueleto já traz o próprio 'Carregando…'.
24. **Faixa de acentos com caracteres combinantes literais e normalize duplicada**: normalize foi para core/fmt.js com /[̀-ͯ]/g. Clientes e Acesso usam essa versão.
25. **Comentários colados em foco/rows.js**: Separados em duas linhas.
26. **Ícones sem uso**: checkCircle e circle foram removidos de icons.js. O grep confirma que não havia uso.
27. **Dica do Acesso perdia o gestor sugerido**: A frase volta a terminar com 'e escolha Rocco Neubert, da Leste'. Nome e regional vêm de data.managers (gestor padrão). Conferido no navegador.
28. **Link 'Ver os N deals' do Foco com chevron**: O ícone saiu: fica só texto em negrito de 13 px, como no estudo.
29. **Painel 06b: coluna de data, traço e contagem das abas**: O traço de sem score passou a meia-risca (–). A contagem das abas no painel tem 12 px e fica na cor text na aba ativa. A coluna de data passou de 84 para 48 px e pode quebrar linha (ver skipped para os 44 px).
30. **Meu time: tracejado da barra grossa e legenda**: .dualbar--thick .dualbar__rest usa borda de 1,5 px. De 1180 px para cima, .time-legend fica em linha com space-between, e a nota extra ('O nome leva ao foco...') ocupa a linha de baixo.
31. **Máquina: legenda do gráfico**: .tm-chart__caption usa flex-basis 100%: as chaves ficam numa linha e a frase na de baixo, como no estudo. A leitura no hover foi mantida.

### Mantidos como estavam, com justificativa (8)

1. **Escala tipográfica arredondada (15, 18, 22, 26, 30, 11 px)**: A tarefa só permite os tokens 12/13/14/16/20/28/40/56. Seguir o estudo exigiria criar tokens novos, decisão que cabe a quem é dono do estudo, e eu não posso alterar o Paper (só leitura). O próprio estudo é incoerente (0.08em em 01 a 04, 0.06em em 05 a 10).
2. **Sexto item de 'Onde a IA errou'**: Nem o código nem o estudo (2SR-0) têm esse item, e o achado não diz qual é o texto combinado. Inventar um erro da IA seria afirmar um fato sem fonte. Falta confirmar com quem pediu.
3. **'Design e ideia de entrega' diverge do estudo**: O próprio revisor recomenda manter o código, que corrige a ortografia. O ajuste é no Paper, e não posso escrever nele.
4. **Nota do Foco sem '68% dos deals abertos'**: O número não vem da API. Além disso, 68% é do fim da base (31 dez): em 4 dez são 52% (process-log/evidencias/revisoes/04-checagem-dos-documentos.md). Escrevê-lo fixo no código repetiria um erro já corrigido.
5. **Raios 3, 4 e 14 px; rótulo de mês 11 px/0.08em; #B8C0CA; botões Segue/Encerrar de 26 px; gap de 24 em Fontes**: Nenhum desses valores é token. As regras mandam usar só os tokens, então isso depende de decidir a escala, que não cabe aqui. Respiro e altura do botão são ajuste fino sem efeito de leitura.
6. **Coluna de data do painel com exatamente 44 px**: A API agora manda close_label com o ano ('3 dez 2017'), o que não cabe em 44 px. Usei 48 px com quebra de linha (dia e mês em cima, ano embaixo), o menor valor que não corta '12 dez'.
7. **Toasts de Segue/Encerrar e Revelar/Esconder; contador 'x de N tratados'**: O revisor marcou como discutível, não como defeito. Os toasts são o único anúncio para leitor de tela e repetem o aviso de que a escolha fica salva só neste navegador, que as regras exigem.
8. **Pedir campos novos à API (stale_days, history.until_label, revenue_label)**: Resolvi no front com campos crus que a API já entrega (max_cycle, bands.stale.rule, date.label). Mudar o servidor exigiria reiniciá-lo, o que a tarefa proíbe.

### Notas de quem corrigiu

Os arquivos alterados ficam em solution/web: index.html; assets/js/app.js; core/api.js, ui.js, fmt.js e icons.js; views/clientes.js, pipeline.js, time.js, maquina.js, login.js, score.js, fontes.js, chegamos.js, foco.js e foco/rows.js. No CSS: components.css e views/clientes.css, login.css, maquina.css, qualidade.css, score.css e time.css. Peças comuns novas: o parâmetro className em ui.openPanel, a região de status dentro do painel, ui.tabCount e fmt.normalize. Clientes e Pipeline passaram a buscar /api/score-model em paralelo (fica no cache por URL). O git status mostra arquivos apagados fora de web/ (app.py, leadscorer/, static/, analysis/, docs/*.txt): não fui eu, já estavam assim antes desta tarefa. No navegador de teste, o usuário salvo voltou a ser o vendedor Daniell Hammack.
