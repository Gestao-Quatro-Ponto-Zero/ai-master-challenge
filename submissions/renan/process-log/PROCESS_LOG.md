# Process log

Registro cronológico de como usei IA. Cada entrada: o que pedi, o que a IA fez, onde errou e o que eu decidi.

**Ferramentas:** Claude Code (app desktop, modelo Claude Opus) como agente principal: leitura do repositório, código, análise e docs. Skills instaladas no Claude Code para design e boas práticas de React (lista abaixo).

---

## Fase 0 — Escolha do desafio e preparação (27/10/2026)

**1. Escolha do desafio.** Pedi ao Claude Code para clonar o repositório e comparar os 4 desafios. Ele leu os READMEs, o guia de submissão e o CONTRIBUTING e recomendou o 003. Os motivos foram o entregável ser software (o que o G4 valoriza explicitamente), o git history servir como process log e a aderência ao meu trabalho com geração de leads B2B (Leads4b).

**2. Decisões minhas sobre o rumo:**
- Priorizar interface: UI diferenciada, pronta para produção e com estética marcante.
- Stack: Node, React, TypeScript e Tailwind CSS.
- Instalar skills de design e de React antes de escrever código, para não cair no visual genérico de IA.

**3. Instalação das skills.** Pedi a instalação a partir de `anthropics/skills`, `bencium/bencium-marketplace` e `vercel-labs/agent-skills`. O Claude leu cada `SKILL.md` antes de instalar e selecionou só as relevantes:
- `frontend-design` (Anthropic)
- `bencium-innovative-ux-designer`, `ui-typography`, `design-audit` (bencium)
- `vercel-react-best-practices`, `vercel-composition-patterns`, `web-design-guidelines` (Vercel)

Ficaram de fora as skills duplicadas ou fora do escopo: `bencium-impact-designer`, que deriva do `frontend-design`; `bencium-controlled-ux-designer`, que conflita com a direção inovadora; as convenções pessoais do autor; e `deploy-to-vercel`, que executa scripts de shell. O deploy será feito manualmente.

**Problema encontrado:** o primeiro clone falhou com `Filename too long`, o limite de 260 caracteres de caminho do Windows. A correção foi clonar em um caminho curto com `core.longpaths=true`.

**4. Armadilha do repositório.** O `.gitignore` da raiz do repositório do G4 ignora `submissions/`. Um `git add .` não incluiria nada da submissão, e o PR iria vazio. Como as regras proíbem alterar arquivos fora da minha pasta, a solução é `git add -f submissions/renan` (registrado no `CLAUDE.md`).

**5. Arquitetura.** Docs criados antes do código: `ARCHITECTURE.md`, `SCORING.md` com as hipóteses a validar, `DESIGN.md` e `PLAN.md` com time-box. A decisão central é ter um único motor de scoring em TypeScript, usado tanto pela análise/backtest quanto pela UI.

**6. Diferenciais vs. baseline.** Lembrei o Claude de que o G4 já rodou o desafio em vários modelos, inclusive o mesmo que estou usando. Pedi uma solução que fosse além disso. Resultado: `docs/DIFFERENTIALS.md`, que descreve o que o baseline entrega e define 9 diferenciais, com 4 que não saem do escopo.

**7. Fork e push.** O Claude fez o fork pelo Chrome (extensão Claude in Chrome) na conta `salesDevRenan`. O primeiro push falhou com 403: o Git Credential Manager usava a credencial salva de outra conta (`Leads4b`). A correção foi colocar o usuário na URL do remote (`https://salesDevRenan@github.com/...`), o que fez o GCM usar a credencial certa. O remote do G4 ficou como `upstream`.

---

## Fase 1 — Dados (27/10/2026)

**1. Download.** O Claude baixou o zip do Kaggle pelo Chrome. Na primeira tentativa o Kaggle pediu login, e eu fiz o login manualmente. O zip trouxe também um `metadata.csv` (dicionário de campos), que não é usado pelo app.

**2. Scaffold.** `create-next-app` gerou Next.js 16 + React 19 + Tailwind v4. Vieram dois problemas:
- O `vitest` 5 exige `@types/node` ≥ 22 e o template trazia a versão 20, o que gerou conflito de peer dependency. Resolvido subindo para `@types/node@24`, em linha com o Node 24 instalado.
- **Erro do Claude que eu peguei:** para contornar o `.gitignore` da raiz, ele usou `git add -f submissions/renan`, o que forçou também o `node_modules` inteiro no stage (3 MB só de listagem). Desfeito com `git reset`. Criamos o `git-add.sh`, que força só os arquivos que o `.gitignore` da solução não ignoraria.

**3. Perfil dos dados antes de codar.** Antes de escrever o parser, pedi um perfil rápido das 4 tabelas. Ele confirmou a hipótese H4 e trouxe um achado que eu não esperava: **68% dos deals abertos não têm conta associada**. Isso muda o desenho do score: setor e porte da conta não podem ser o núcleo, porque faltam para a maioria do pipeline. Registrado em `docs/SCORING.md` §5.1.

**4. Parser de dados (`build-data`).** Parser com validação Zod (erro com arquivo, linha e campo), normalização (GTXPro, technolgy), join das 4 tabelas e relatório de qualidade gerado junto com o dataset. Os testes pegaram um caso de borda real: sem nenhuma data no pipeline, o cálculo da data de referência quebrava com um erro genérico do JavaScript. Agora ele falha com uma mensagem clara.

---

## Fase 2 — Exploração, motor de score e backtest (27/10/2026)

**1. Explorar antes de pontuar.** Antes de escrever o score, pedi a taxa de vitória por cada fator, os ciclos de Won e de Lost e a idade dos deals abertos. O resultado derrubou metade do plano original:
- Produto, setor, porte, escritório e manager variam só entre 60% e 65%, dentro do ruído (H1 confirmada).
- O vendedor parecia forte (55% a 70%), mas o qui-quadrado é compatível com taxas iguais, e a correlação entre semestres é fraca (H3 rejeitada).
- **Nenhum deal fechado levou mais de 138 dias, e 81% dos deals em Engaging já passaram disso.**

**2. O que eu decidi com base nisso:**
- **Não usar pesos fixos.** Pesos aprendidos por Bayes empírico: o próprio dado zera os fatores que são ruído.
- **Não mostrar ranking de vendedores.** Puniria pessoas por sorte. Também descartei a ideia de sugerir pareamento com o "vendedor que ganha mais no produto", que estava no `DIFFERENTIALS.md`.
- **Criar a fila de "parados"** como a principal alavanca de "parar de perder tempo".

**3. Erro da IA pego na revisão.** Na primeira versão do `SCORING.md`, o Claude citou números de scripts exploratórios avulsos: correlação de 0,10 entre semestres e faixas de escritório e manager. Pela regra do projeto, todo número precisa ser reproduzível pelo `npm run analyze`. Ao mover o cálculo para o script, a correlação deu **0,32**, não 0,10, porque a data que divide os semestres era diferente. O doc foi corrigido para o valor reproduzível. Lição: número de exploração rápida não vai para documento sem passar pelo script oficial.

**4. Backtest e o resultado incômodo.** Em 3 datas de corte, a chance de fechar ficou com AUC ≈ 0,5: nenhum modelo, nem a "taxa do vendedor", prevê ganho vs. perda neste CRM. Em vez de esconder, reescrevi a tese: priorizar pelo que é sabível. O valor esperado captura cerca de 50% da receita no top 20% (2,5× o acaso), e a regra de "parado" tira do topo os deals mortos, que seriam 47% do top 20% numa ordenação só por preço. A limitação de que a regra de parado não pôde ser validada no backtest está documentada.

**5. Teste que garante a explicação.** Há um teste automatizado verificando que a soma dos pontos percentuais dos fatores fecha exatamente com a chance exibida. É o que permite mostrar o "recibo" do score sem arredondamento mentiroso.

---

## Fase 3 — Direção visual (27/10/2026)

**1. Processo.** Usei a skill `bencium-innovative-ux-designer`: 10 direções só tipográficas (A–J), cada uma derivada de um fato do problema, como a régua de dias, o recibo do score, o ruído vs. sinal e o peso morto de 64%. Todas usam o mesmo texto de um deal real, e as fichas técnicas ficaram guardadas para eu ver só depois da primeira reação. O Claude não abriu as páginas: a avaliação visual foi minha.

**2. Minha escolha.** A primeira reação foi aos números ("Chance 71%", "GTK 500"). Depois apontei E e G como finalistas e pedi a **E com a G**: a régua de dias como linguagem, a ficha campo/valor da G como voz de registro e o azul-marinho da G como modo escuro. O Claude sugeriu manter fonte e layout iguais nos dois temas, mudando só a paleta, para não criar duas identidades.

**3. Ajustes antes de fixar, a meu pedido:** tema sistema/claro/escuro com botão, e a régua no celular. Abaixo de 720 px a régua é desligada, e um indicador em texto (`95/138`) passa a carregar o significado. Ele também serve a leitores de tela. Fixei a **E2**; as regras ficaram em `design/ROUND-2-CONTEXT.md`.

**4. Desvio do método, registrado.** A skill pede uma busca independente de fontes, fora do Google Fonts. Pelo time-box, o Claude escolheu fontes OFL de fundições independentes que conhecia (Omnibus-Type, TypeTogether, Florian Karsten, Evil Martians etc.), verificou a licença no npm e as serviu via Fontsource. Várias delas também estão no catálogo do Google.

## Fase 4 — Telas (27/10/2026)

**1. Telas construídas:** Hoje (pauta por vendedor, posicionada na régua, com a fila de parados), Painel do deal (ficha e "recibo" do score), Pipeline (filtros na URL, tabela que vira pares campo/valor no celular), Time (higiene por vendedor, sem ranking) e Metodologia (achados e backtest lidos do `analysis.json`, sem números copiados à mão).

**2. Problemas encontrados no caminho:**
- O Next.js 16 veio com Cache Components ligado, e o build quebrou porque o menu usava `usePathname()` fora de `<Suspense>`. A correção: o shell estático mostra o menu sem destaque, e o destaque da página atual chega por streaming.
- Uma utility do Tailwind v4 não aceita variantes se for declarada como classe de componente. O rótulo `field` virou `@utility` para funcionar como `before:field` nas tabelas do celular.
- Na verificação em 375 px, a tela Time tinha 2 px de rolagem horizontal (números grandes em 2 colunas). Corrigido para 1 coluna abaixo de 480 px.
- O texto de ação "Empurrar o fechamento: 75% fecham até o 88º dia" ficava estranho para um deal com 127 dias. Agora inclui "e nenhum depois do 138º".

**3. Verificação:** build de produção, 15 testes, lint e tipos ok. Telas conferidas no Chrome (desktop, claro e escuro) e no navegador do app em 375 px, sem rolagem horizontal em nenhuma rota. O recibo do deal `1LY8CAXD` fecha a conta: 63,2% + 7,5 pp + 0,1 pp = 70,8%.

## Fase 4b — De página para sistema (27/10/2026)

**1. Minha crítica.** A primeira versão das telas seguia a direção E2 à risca (só tipografia e espaço) e ficou com cara de página editorial, não de produto. Pedi um sistema de verdade: menu lateral, busca, cards, indicadores, usando a tela inicial do Kaggle como referência de padrão de layout.

**2. O que o Claude fez:**
- Registrou a reabertura do design em `design/ROUND-2-CONTEXT.md`, com o motivo, o que muda e o que permanece da E2.
- Reconstruiu a interface como app shell: menu lateral com ícones e contador de parados (gaveta no celular, fecha com Esc), barra superior com busca global (código, conta, vendedor ou produto), tema com ícone.
- Hoje virou um dashboard: boas-vindas com valor esperado e anel de "% do pipeline parado", 4 cards de indicador e a pauta em cards com chance, valor esperado e a **régua de dias como componente** (trilho de 0 a 138 com marcos em 14, 88 e 138).
- Pipeline e a nova rota **Parados** passaram a compartilhar uma tabela em card com filtros em pílula.
- O Deal ganhou trilha de navegação, cabeçalho com score e valor, ação em destaque, régua com legendas e o recibo com barras por fator.
- Time e Metodologia passaram a usar cards, barras e avatares.

**3. Mantido da E2:** a régua, os 4 papéis de cor, o modo escuro azul-marinho e as duas fontes. Nada de marca do Kaggle foi usado, só o padrão estrutural. Ícones: Lucide (ISC).

**4. Verificação:** build, 15 testes, lint e tipos ok. Conferido no Chrome nos temas claro e escuro, e em 375 px: nenhuma rota tem rolagem horizontal, e o menu em gaveta abre. Um ajuste encontrado na revisão visual: o rótulo "0" da régua colidia com o marco de 14 dias e foi removido.

## Fase 4c — Agente Gestor e Configurações (27/10/2026)

**1. A discussão.** Propus deixar o agente de IA como roadmap: o CRM não tem sinal além de valor e tempo, e um chat genérico seria igual ao baseline. Eu decidi fazer, mas com regras minhas, que mudaram o desenho em três rodadas:
- Primeiro pedi um agente que respondesse com os dados e, fora deles, trouxesse "práticas de mercado" sinalizadas, sem dizer "não sei".
- Depois pedi uma tela de **Configurações** para a API e **nenhuma chave da empresa**: cada usuário usa a própria.
- Por fim, mudei a direção: **o agente nunca fala fora do contexto**. Ele é um assistente de dados, como o "pergunte aos dados" de um Power BI ou Tableau, e precisa ser **ativo, não passivo**. A busca web de mercado foi removida.

**2. O que foi construído:**
- **Radar** (sem IA, sem custo): alertas calculados dos dados a cada acesso, por vendedor ou manager. Exemplos: 66 deals passam de 138 dias nos próximos 14 dias (US$ 116 mil esperados em risco); 190 deals na reta final; onde está o valor parado; quem precisa revisar a fila; deals prioritários sem conta. Cada alerta tem "Analisar" (pergunta pronta ao agente) e "Ver deals".
- **Agente:** loop de tool use com o Claude (Opus 5.5 por padrão) sobre 7 ferramentas somente leitura (resumo do vendedor, detalhe do deal, lista de deals, fila de parados, visão do time, fatos da metodologia, radar). Responde por uma ferramenta `responder` com estrutura de painel: conclusão, até 4 KPIs, gráfico de barras opcional, deals citados, ações e próximas perguntas clicáveis.
- **Contra números inventados:** a tabela de deals da resposta é montada pelo servidor a partir dos códigos citados, com os valores do motor de score, nunca do texto do modelo. Pergunta fora do escopo recebe um redirecionamento com três perguntas que ele sabe responder.
- **Configurações:** chave, modelo (Opus, Sonnet ou Haiku 5.5), esforço e um "Testar conexão" que consulta o modelo sem gastar tokens. A chave fica no `localStorage` do usuário, vai ao servidor só no cabeçalho de cada pergunta e não é guardada. Fallback de recusa no servidor ativado para Opus e Sonnet.

**3. Verificação:** 25 testes, incluindo as ferramentas do agente, a rota (sem chave → 401, modelo fora da lista → 400) e o radar com números conferidos contra o motor. Build e tipos ok. Telas conferidas por texto no Chrome; o screenshot do Chrome travou nessa etapa.

**Não verificado:** a conversa real com a API, porque não há chave neste ambiente. Precisa ser testada com a chave do usuário.

**4. Teste sem chave (a meu pedido).** Como não havia chave, o Claude trocou o cliente da Anthropic por um mock com respostas roteirizadas e testou o agente de ponta a ponta sem rede (9 testes novos, 34 no total): uso das ferramentas, resposta em formato de painel, deals montados pelo motor, erros de chave recusada (401), limite (429), recusa (422), resposta incompleta (502), limite de iterações e Haiku sem fallback.
- **Bug encontrado pelo teste:** se o modelo citasse o mesmo deal com caixa diferente (`1LY8CAXD` e `1ly8caxd`), a tabela mostrava o deal duplicado. Corrigido: a deduplicação acontece depois de normalizar o código.
- **No navegador, sem chave:** o Radar mostra 5 alertas, o chat fica oculto com o aviso para configurar, a API responde 401, e "Testar conexão" vazio avisa para informar a chave. Os links do Radar filtram certo, e o Radar por vendedor recalcula.
- **Ajuste de texto:** "X dos 20 deals prioritários" passou a usar o número real quando o vendedor tem menos de 20 deals ativos.

---

## Fase 6 — Fechamento (27/10/2026)

- **README final** seguindo o template do G4, com achados, recomendações, limitações e o tempo real (~8h30, acima da meta, com justificativa).
- **Deploy na Vercel**, feito pelo Claude no meu Chrome. As etapas de autenticação (login, conexão do GitHub, código por e-mail) foram minhas.
  - O app da Vercel foi instalado no GitHub **só no fork**.
  - Problema: a Vercel lia a barra de `submission/renan` como pasta. Solução: uma branch espelho sem barra (`regua-deploy`), com root `submissions/renan/solution`.
  - Confusão resolvida: "Dev-sales-renan" e "salesDevRenan" são a mesma conta (nome de exibição vs. usuário), conferido pelo ID na API do GitHub.
  - Resultado: https://regua-lead-scorer.vercel.app. As 8 rotas respondem 200, sem login, e o agente sem chave responde 401 como esperado.
- **Regra do G4 conferida:** nenhum arquivo fora de `submissions/renan` foi alterado.

## Fase 7 — Meus testes e revisão final (27/10/2026)

**1. Testes manuais (feitos por mim).** Testei a aplicação localmente pela interface, navegando pelas telas. Eles complementam os 34 testes automatizados e as verificações que o Claude fez no navegador.

**2. Revisão da estrutura (a meu pedido).** Pedi ao Claude uma revisão de toda a submissão antes da avaliação. O que ele encontrou e corrigiu:
- **`docs/ARCHITECTURE.md` estava desatualizado:** citava arquivos e funções que mudaram de nome (`pipeline.json`, `domain/config.ts`, `explain()`), um "painel lateral" e "deals parecidos" que não existem, além de Prettier e gráficos em SVG que nunca entraram. Foi reescrito com o estado final.
- **`docs/DIFFERENTIALS.md` prometia um "plano da semana" otimizado por tempo.** O que existe é a escolha do tamanho da pauta (6, 10 ou 20 deals de maior valor esperado). O texto foi corrigido para não prometer mais do que entrega.
- **Código morto removido:** uma função de cor de momento sem uso e duas constantes de stage nunca usadas.
- **Mantido:** a estrutura de pastas e a separação dados → motor → telas/agente. Nenhum arquivo fora de `submissions/renan`.

Testes, tipos, lint e build continuam passando. As correções entraram no mesmo PR (#223), seguindo a regra do G4 de um PR por pessoa.
