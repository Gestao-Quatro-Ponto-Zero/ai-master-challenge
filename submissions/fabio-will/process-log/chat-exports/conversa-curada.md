# Conversa curada com a IA

Ferramenta: Claude Code com o modelo Claude Opus 5.5, num terminal na minha máquina, em 13/11/2026, numa sessão só. Esta é uma versão curada: as minhas mensagens estão como eu escrevi, com os erros de digitação, e cada resposta da IA está resumida. O arquivo bruto da sessão não é publicado porque carrega configuração privada da máquina. Trechos com dado de terceiro ou de outro processo seletivo foram trocados por [colchetes].

Os números citados nas respostas são os da época de cada mensagem; os finais estão no README.

## 1. Entender o teste e escolher o desafio

**Eu:** "veja como foi o teste da g4 como montando o case profissionalmente veja o contexto da conversa [de outro case que fiz] ... e clona esse repositorio ... https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge"

**IA:** Clonou o repositório, leu o README, o guia de submissão e os quatro enunciados, e usou subagentes para ler as 197 reviews públicas do avaliador. Sintetizou a régua: uso de IA vale 30%, process log em Markdown, prints são a primeira evidência, avaliação assistida por IA, e commit com autor "Claude" pesou contra.

**Eu:** "veja pela minhs skills, nossos projetos que ja fizemos aqui recentes ... e o que é mais profissional e visual também"

**IA:** Mediu os quatro datasets antes de recomendar. O 004 é ruído puro; o Dataset 1 do 002 parecia sintético, mas o Dataset 2 tem 47.837 tickets reais. Recomendou o 002 por permitir diagnóstico, automação e algo rodando.

**Eu:** [mensagem omitida: link de um PR aprovado de outro candidato, com dado pessoal de terceiro]

**IA:** Leu o PR como referência de formato e não copiou nada.

**Eu:** "não devems subir, e comitar nada ok .. aainda"

**Eu:** "ficamos na dois ... [a vaga está aberta, confirmado hoje] ... commits sempre com meu nome ... se precisamos mecionar as IAs e modelos que usamos, podemos fazer ... o deploy vai na vercel, melhor é ...sim devemos usar a identidade da G4 acredito eu, melhor né, respeitado a risca o branding book, etntão pode focar em analisar isso primeiro.. e começa ai pelo que você falou ... tem algo citado se precisa ser em ingles ou portguês?"

**IA:** Registrou as regras (nada de commit até eu liberar, autoria minha, IA citada só no process log). Sobre idioma: o repositório não exige; propôs documentação e interface em português e código em inglês.

**Eu:** "código sempre em ingles né, variaveis tudo"

## 2. Marca da G4

**Eu:** "veja no sites atuais ok ... cria ai um arteafor primeiro, profissional"

**IA:** Como não há brandbook público, mediu a marca nas páginas atuais com um navegador automatizado: logos oficiais, cores por área pintada (marinho #001F35, dourado #B9915B, off-white #F5F4F3), Manrope e Libre Baskerville itálico, contraste WCAG. Achou que o dourado sobre fundo claro dá 2,63:1 e não passa; decidiu usar dourado como texto só sobre marinho. Montou o levantamento como página.

**Erro da IA:** um script de recorte copiado de outro projeto regravou 5 imagens daquele projeto. Conferido no git: ficaram idênticas byte a byte. Os scripts passaram a receber o caminho por parâmetro.

## 3. Construção

**Eu:** "bom vai tocando ai, e eu ja volto, vai construndo e validado, sem commitar nada ainda, é importante estar profissional, organizado bem estruturado, perfomatico e garantindo page speed, qualidade ligth house, além de seguro ... e sempre valide visualmente com prints também com para ver se espaçamento está bom se a experiência esta bom, comunicação no desktop e ux estão boas"

**Eu:** "aproveite e ja estude boa praticas de mercado livros, para o nosso teste ... use a comunicação e tom de voz já da G4 mesmo, ficou otimo o estudo da marca ali, lembrando que sempre precisa usar as melhores praticas e organização do código com o que precisa, segurança"

**Eu:** "lembrando que deve estressar profissionalmente os cenários, em cenários extremamente critivos, critico, medio, leve ... cenários reais mesmo com evidências ... vai tocando /loop termine tudo e valido depois"

**IA:** Auditou o Dataset 1 (seis sinais de dado sintético), comparou cinco modelos e escolheu a regressão logística pela calibração, desenhou a política de travas e montou nove cenários de estresse em quatro severidades. Um subagente pesquisou livros e artigos com checagem de fonte; a auditoria cega de 2% veio daí. Construiu o console estático, validou com prints em desktop e celular e com Lighthouse.

**Erros da IA pegos pelo estresse:** a faixa assistida nasceu com 60% de acerto; só o limiar mandava 51% dos tickets de outro domínio sozinhos; a trava de novidade deixava passar português; a trava de vocabulário barrava erro de digitação demais; o disjuntor dava alarme falso; laboratório e estresse usavam modelos de tamanhos diferentes. Cada um virou uma correção medida (tabela de iterações no process log).

## 4. Revisão contra o enunciado

**Eu:** "ta rodando aqui ... local consgeue tirar print e ver se realmente é isso que precisamos entregar"

**IA:** Tirou prints de todas as telas e comparou com o enunciado e com a régua. Viu que o diagnóstico não respondia as três perguntas do Diretor pelo nome. Calculou as combinações de canal, prioridade e tipo e um teste de permutação: a "combinação mais lenta" aparece por acaso em 52% dos embaralhamentos.

**Eu:** "e precisa vr se ta mudando de pagian rapida, com skeletom tudo profissionalmente"

**IA:** Mediu a troca de página (20 a 64 ms, inclusive com 4G lento), colocou skeleton no teste ao vivo e na rota, e trocou o detalhe do ticket no celular por uma folha inferior.

**Eu:** "ué deu 503? e você ta organziando via agentes ou mockado?"

**IA:** O servidor local respondia 200 em todas as páginas; o 503 provavelmente veio de uma reconstrução da pasta de build. Nada mockado: os números saem dos scripts nos dados reais.

**Eu:** "me explica de novo o que o desafio pede"

## 5. Pentest e segurança

**Eu:** "acho bom estressar pentest, segurança ..."

**IA:** Atacou o modelo e o console. No modelo, achou uma falha real: com 5 palavras comuns coladas, 42% dos tickets de RH e de administrador escapavam das travas. Criou a trava de trecho (escolhida na validação) e, depois de achar que palavra intercalada ainda passava, a trava de sequência. No console, 10 ataques num Chrome real, todos contidos. Também achou um cache que quebraria o próximo deploy e duas dependências com alerta.

**Erros da IA no pentest:** o primeiro teste de injeção acusou que `eval` rodava, mas era o DevTools ignorando a CSP; a primeira varredura de segredos não rodou de verdade; a exportação rodou em paralelo com o estresse. Todos refeitos e documentados.

## 6. Publicação, deck e animações

**Eu:** "faça o que achar melhor .... e vamos subir no vercel já?"

**IA:** Seguiu as recomendações medidas nos trade-offs (registrado como decisão delegada) e publicou no meu escopo pessoal do Vercel depois do meu login. Refez pentest e Lighthouse na URL publicada.

**Eu:** "e vamos montando uma apresentação rapida como fizemos na [outro case] só que na [outro case] foi muito grande ... então queri montar uma apresentaçnao com o visual da g4 mesmo, pegar os elementos, background podemos montar com a IA o background dos slides ... e ai gerar as imagens para subir na descrição da PRs, além de prints reais animados, como se fosse gif mostrando a plataforma né, pq você falou que tiham pedido isso correto?"

**IA:** Corrigiu a premissa: as reviews pedem prints do app rodando, não GIF, mas animação é a melhor prova de que funciona. Montou um deck de 8 slides com a identidade da G4 e fundos gerados por IA (US$ 0,61), e um subagente gravou cinco animações do console em uso, validadas quadro a quadro.

**Eu:** "seria importante nas coluna consgeuir ordernar tem sempre um icone de i nos cards explicando o que é a sessnao parte em tooltpi algo assim profissional"

**IA:** Colunas ordenáveis com `aria-sort` e um seletor no celular; um ícone "i" em cada seção, coluna e número, que abre por mouse, teclado e toque.

**Eu:** "seta do select torta... confira se todos os botõs input estão corretos e com acessibilidade"

**IA:** Desenhou a seta do select e subiu a fonte para 16 px (o iPhone dá zoom abaixo disso). Na revisão achou mais dois problemas: o foco deformava botões arredondados, e os filtros se anunciavam como abas sem ser abas.

**Eu:** "e fez a apresentação e imagens que pedi? queria ver uma previa do PR"

**Eu:** "ta online? ta ótimo assim"

**Eu:** "boa, veja se ta tudo correto ... para mim já podemos subir"
