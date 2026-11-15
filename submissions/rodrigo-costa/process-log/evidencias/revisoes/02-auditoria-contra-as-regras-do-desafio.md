# Auditoria do plano contra as regras do desafio

> Dois revisores independentes conferiram o plano e o estudo de UX contra os termos de entrega do desafio 003. Saída bruta de agentes de IA, sem edição além da remoção de caminhos locais.


## checklist

- **resumo:** Li os cinco arquivos na íntegra e vi as telas 01 a 04 no Paper, só para leitura. O plano cobre bem o mérito do desafio: o score tem lógica própria, não é só ordenar por valor; cada deal mostra o porquê com números; a tela é pensada para a segunda de manhã; há prova contra o baseline, o process log é forte e há verificação por script. O problema é que quase tudo o que é obrigatório ainda não existe. A exigência número 1 do challenge 003 é software que RODA com os dados reais ("não é mockup, wireframe ou PowerPoint"), e hoje só há pranchas no Paper e um protótipo de análise. Os riscos de rejeição ou desclassificação são cinco. (1) Arquivos fora de submissions/<nome>/: a configuração do Railway (Procfile, railway.json, nixpacks) não pode ir para a raiz do fork. (2) Process log ausente ou fraco. (3) Título do PR fora do formato. (4) Mais de um PR. (5) README sem o bloco "Process Log", que o template diz ser obrigatório sob pena de desclassificação. Os riscos de nota baixa são dois. Primeiro, o excesso de escopo: Kanban, Clientes com painel lateral e Configurações com CRMs fictícios esticam um prazo que já passou bastante das 4 a 6 horas ("40 horas não recebem pontos extras") e podem soar como "foco em parecer inteligente". A tela de Configurações é a mais arriscada, porque mostra integração que não existe; vale ligá-la à seção Limitações/escalar. Segundo, o +42% ainda não foi conferido de forma independente; é preciso conferir e garantir que a máquina do tempo não usa informação do futuro. Pequenas inconsistências nas telas: "30 vendedores" contra 35 no enunciado (explicar que 5 não têm deals) e o nome do dataset ("CRM Sales Opportunities" contra "CRM Sales Predictive Analytics"). Ordem sugerida: app rodando com os CSVs dentro da pasta e link no Railway, depois o README no template com Setup, Lógica e Limitações, depois o process log. Pipeline com filtro de cliente, Transparência e Qualidade dos dados ficam em seguida. Kanban, Clientes e Configurações, só se sobrar tempo.

### itens


#### 1. item 1

- **exigencia:** Solução funcional que RODA (não mockup, wireframe ou PowerPoint)
- **fonte:** challenges/build-003-lead-scorer/README.md L64: "Precisa rodar (não é mockup, wireframe ou PowerPoint)"; L17 "O deliverable principal é software funcionando"
- **tipo:** obrigatorio
- **situacao:** ainda_nao_existe
- **falta:** Construir o app (servidor Python + página) que implementa as telas 01 a 04 com cálculo real. As pranchas do Paper NÃO contam como solução: em docs/, apresentá-las como estudo de UX, não como entrega.

#### 2. item 2

- **exigencia:** Usar os dados reais do dataset
- **fonte:** build-003 README L65: "Precisa usar os dados reais do dataset"
- **tipo:** obrigatorio
- **situacao:** parcial
- **falta:** A análise já usa os dados; o app ainda não. Incluir os 4 CSVs (licença CC0) dentro de submissions/<nome>/solution/data para o app rodar sem download, citar a fonte e a licença no README e corrigir o nome do dataset na tela de acesso (aparece "CRM Sales Opportunities"; o enunciado chama de "CRM Sales Predictive Analytics").

#### 3. item 3

- **exigencia:** Lógica de scoring/priorização que não seja só ordenar por valor
- **fonte:** build-003 README L66: "não é só ordenar por valor"
- **tipo:** obrigatorio
- **situacao:** atende
- **falta:** No plano, atende: a chance vem da idade do deal e do ponto do trimestre, e a prioridade = chance × preço. Risco: como só existem 7 produtos, o preço pode dominar a ordem. Mostrar, na Transparência e na máquina do tempo, que a ordem difere da ordenação por valor (o comparativo com "Por valor" já faz isso).

#### 4. item 4

- **exigencia:** Vendedor entende POR QUE o deal tem score alto ou baixo
- **fonte:** build-003 README L67; Dicas L98: "Explainability ganha"
- **tipo:** obrigatorio
- **situacao:** parcial
- **falta:** O design atende: o bloco "Por que 98 / De onde vem a chance / O que não entra" está na tela 02. Falta implementar, gerando o texto a partir dos números reais de cada deal, inclusive para os deals frios e os sem desfecho (por que o score é baixo).

#### 5. item 5

- **exigencia:** Documentação: Setup (dependências, comandos, URL)
- **fonte:** build-003 README L71; CONTRIBUTING L36: "Se construí código, incluí instruções de setup"
- **tipo:** obrigatorio
- **situacao:** ainda_nao_existe
- **falta:** No README: versão do Python, "nenhuma dependência", o comando único (ex.: python solution/app.py), a porta, o link público do Railway e como rodar o script de conferência. Testar o passo a passo num clone limpo.

#### 6. item 6

- **exigencia:** Documentação: Lógica (critérios de scoring e por quê)
- **fonte:** build-003 README L72
- **tipo:** obrigatorio
- **situacao:** parcial
- **falta:** Os achados existem, mas falta a seção escrita. Explicar a fórmula (chance em 30 dias por idade × ponto do trimestre; prioridade = posição por chance × preço), o corte de 138 dias e por que produto, setor, regional, gestor, porte, histórico, vendedor e conta ficaram de fora (testados e sem efeito). A tela Transparência deve repetir isso.

#### 7. item 7

- **exigencia:** Documentação: Limitações e o que precisaria para escalar
- **fonte:** build-003 README L73; submission-guide L59; template L41-43
- **tipo:** obrigatorio
- **situacao:** ainda_nao_existe
- **falta:** Listar: dados só até 31/12/2017; sem fechamentos antes de 01/03/2017; campo de cliente vazio em 68% dos abertos; acesso simulado sem login; nenhuma integração; +42% medido no passado da própria base. Para escalar: integração com o CRM (aqui a tela de Configurações vira argumento), recálculo periódico e validação fora da amostra.

#### 8. item 8

- **exigencia:** Process log com evidências de uso de IA (sem ele = desclassificado)
- **fonte:** README raiz L37-38: "Sem evidência de processo = desclassificado"; submission-guide L18-20; build-003 L75-79; template L49-51
- **tipo:** rejeicao
- **situacao:** parcial
- **falta:** Planejado (conversa exportada + commits + documento de contribuição), mas ainda não montado. Colocar em process-log/chat-exports e process-log/screenshots, revisar a exportação removendo dados pessoais e de outros projetos, e mostrar a primeira versão descartada (20 min) como evidência de iteração.

#### 9. item 9

- **exigencia:** Process log mostra: ferramentas e por quê; decomposição antes de promptar; onde a IA errou; o que você adicionou; quantas iterações
- **fonte:** submission-guide L33-39
- **tipo:** qualidade
- **situacao:** parcial
- **falta:** O conteúdo existe (CRM vivido, hipóteses descartadas, erros corrigidos: tabela com viés, ranking de vendedores que era efeito do time, porte do cliente). Falta escrever e dizer explicitamente o NÚMERO de iterações e o motivo de cada ferramenta (Claude Code, Paper/MCP, Railway etc.).

#### 10. item 10

- **exigencia:** README da pasta segue o template de submissão
- **fonte:** README raiz L88; submission-guide L47; CONTRIBUTING L19 e L35
- **tipo:** obrigatorio
- **situacao:** ainda_nao_existe
- **falta:** Criar submissions/<nome>/README.md com exatamente estas seções: Sobre mim, Executive Summary, Solução (Abordagem, Resultados/Findings, Recomendações, Limitações), Process Log (Ferramentas usadas em tabela, Workflow numerado, Onde a IA errou e como corrigi, O que eu adicionei que a IA sozinha não faria), Evidências (checklist) e a data de envio.

#### 11. item 11

- **exigencia:** Título do README: "Submissão — [Seu Nome] — Challenge [XXX]"
- **fonte:** templates/submission-template.md L1
- **tipo:** obrigatorio
- **situacao:** ainda_nao_existe
- **falta:** Usar "Submissão — Rodrigo ... — Challenge 003".

#### 12. item 12

- **exigencia:** Campos Sobre mim: Nome, LinkedIn, Challenge escolhido
- **fonte:** templates/submission-template.md L5-7
- **tipo:** obrigatorio
- **situacao:** ainda_nao_existe
- **falta:** Preencher os três campos, incluindo a URL do LinkedIn e "003 — Lead Scorer".

#### 13. item 13

- **exigencia:** Executive Summary em 3 a 5 frases (o que fez, o que encontrou, principal recomendação)
- **fonte:** template L13; submission-guide L55
- **tipo:** obrigatorio
- **situacao:** ainda_nao_existe
- **falta:** Escrever: pipeline declarado de US$ 3,9 mi contra US$ 0,7 mi ainda vivo; score por idade × trimestre; +42% contra ordenar por valor (só depois de conferido); recomendação principal (ex.: decidir os deals com mais de 138 dias).

#### 14. item 14

- **exigencia:** Recomendações priorizadas para a empresa
- **fonte:** template L35-37 "Priorize"; submission-guide L58
- **tipo:** obrigatorio
- **situacao:** ainda_nao_existe
- **falta:** Lista ordenada: 1) política de encerrar ou confirmar deals com mais de 138 dias; 2) usar o foco da semana e a mensagem para quem não abre o sistema; 3) tornar o campo de cliente obrigatório; 4) acompanhar a taxa de ganho real contra a oficial.

#### 15. item 15

- **exigencia:** Resultados/Findings com dados, screenshots e links
- **fonte:** template L29-31
- **tipo:** obrigatorio
- **situacao:** parcial
- **falta:** Os achados já estão levantados. Colocar no README os screenshots do APP RODANDO (não só do Paper), o link do Railway e os números principais com referência ao script de conferência.

#### 16. item 16

- **exigencia:** Seção Evidências com checklist marcado (screenshots, gravação, chat exports, git history, outro)
- **fonte:** template L85-93
- **tipo:** obrigatorio
- **situacao:** ainda_nao_existe
- **falta:** Marcar o que foi entregue e linkar cada item. Uma gravação curta (Loom) do workflow ou do app ajuda; o template a lista como opção.

#### 17. item 17

- **exigencia:** Rodapé com data de envio
- **fonte:** template L97: "Submissão enviada em: [data]"
- **tipo:** obrigatorio
- **situacao:** ainda_nao_existe
- **falta:** Preencher a data.

#### 18. item 18

- **exigencia:** Estrutura de pastas: README.md, solution/, process-log/ (screenshots/, chat-exports/), docs/
- **fonte:** CONTRIBUTING L17-28
- **tipo:** regra_pr
- **situacao:** parcial
- **falta:** O plano prevê docs/ e process-log/. Garantir que o código, os dados e o script de conferência fiquem em solution/; as pranchas do Paper e o documento de contribuição em docs/; as exportações em process-log/chat-exports e os prints em process-log/screenshots.

#### 19. item 19

- **exigencia:** Fork, branch submission/seu-nome, pasta submissions/seu-nome/
- **fonte:** README raiz L26-31 e L87; CONTRIBUTING L7-11
- **tipo:** regra_pr
- **situacao:** ainda_nao_existe
- **falta:** Criar o fork e a branch submission/<nome> e commitar só dentro de submissions/<nome>/.

#### 20. item 20

- **exigencia:** Só modificar arquivos dentro de submissions/seu-nome/ (senão o PR é rejeitado)
- **fonte:** CONTRIBUTING L41: "PRs que alteram outros arquivos serão rejeitados"; checklist L37
- **tipo:** rejeicao
- **situacao:** nao_atende
- **falta:** Risco concreto com o Railway: Procfile, railway.json, nixpacks.toml, .python-version, .gitignore e workflows NÃO podem ir para a raiz. Colocar dentro da pasta e configurar o Root Directory do serviço no Railway como submissions/<nome>/solution. Conferir com git diff --stat main antes de abrir o PR.

#### 21. item 21

- **exigencia:** Título do PR: "[Submission] Nome — Challenge XXX", PR para main
- **fonte:** CONTRIBUTING L13 e L43
- **tipo:** regra_pr
- **situacao:** ainda_nao_existe
- **falta:** Usar exatamente "[Submission] Rodrigo ... — Challenge 003" (com travessão), base main do repositório original.

#### 22. item 22

- **exigencia:** Um PR por pessoa; atualizações por push na mesma branch
- **fonte:** CONTRIBUTING L42
- **tipo:** rejeicao
- **situacao:** ainda_nao_existe
- **falta:** Abrir um único PR e não abrir outro para correções.

#### 23. item 23

- **exigencia:** Checklist antes do PR (challenge escolhido e lido, pasta certa, process log, template, setup, nada fora da pasta)
- **fonte:** CONTRIBUTING L30-37
- **tipo:** regra_pr
- **situacao:** ainda_nao_existe
- **falta:** Copiar o checklist na descrição do PR e marcar cada item só depois de conferir.

#### 24. item 24

- **exigencia:** Submissão exclusivamente via Pull Request
- **fonte:** README raiz L85; submission-guide L45
- **tipo:** regra_pr
- **situacao:** ainda_nao_existe
- **falta:** O link do Railway é complemento; a entrega oficial é o PR, com tudo o que é necessário para rodar localmente.

#### 25. item 25

- **exigencia:** Escolher UM desafio (preferem um bem feito)
- **fonte:** README raiz L27 e L98-99
- **tipo:** regra_pr
- **situacao:** atende
- **falta:** Nada; só o 003.

#### 26. item 26

- **exigencia:** Superar substancialmente o baseline das IAs (profundidade, julgamento, execução, criatividade)
- **fonte:** README raiz L40-46; FAQ L104-105
- **tipo:** qualidade
- **situacao:** atende
- **falta:** Os diferenciais são claros: pipeline declarado contra o vivo, corte de 138 dias, ritmo do trimestre, máquina do tempo sem olhar o futuro, mensagem para quem não abre o sistema. Explicitar no README o que a primeira versão autônoma (o baseline) fazia e por que foi descartada.

#### 27. item 27

- **exigencia:** Evitar 'zero evidência de verificação (a IA disse, o candidato acreditou)'
- **fonte:** submission-guide L74
- **tipo:** qualidade
- **situacao:** parcial
- **falta:** O script de conferência está planejado. O +42% (22 datas, 659 listas) ainda não tem conferência independente: conferir antes de publicar, garantir que a máquina do tempo use só deals e fechamentos conhecidos até a data (inclusive taxas e corte de 138 dias calculados com o passado) e registrar o resultado no process log.

#### 28. item 28

- **exigencia:** A solução funciona de verdade seguindo as instruções
- **fonte:** build-003 README L85
- **tipo:** qualidade
- **situacao:** ainda_nao_existe
- **falta:** Depois de pronto, clonar o fork numa pasta limpa, seguir o README à risca e testar o link do Railway numa aba anônima.

#### 29. item 29

- **exigencia:** Scoring faz sentido, usa as features certas e vai além do óbvio
- **fonte:** build-003 README L86; Dicas L96
- **tipo:** qualidade
- **situacao:** atende
- **falta:** Ponto forte: mostrar no README e na Transparência a tabela das features óbvias testadas e descartadas (produto, setor, regional, gestor, porte, vendedor, conta), com o tamanho do efeito.

#### 30. item 30

- **exigencia:** Vendedor não técnico consegue usar e entender
- **fonte:** build-003 README L87; submission-guide L69
- **tipo:** qualidade
- **situacao:** parcial
- **falta:** O design usa linguagem simples. No app, evitar jargão ("coorte", "janela" sem explicação) e testar com alguém de vendas, se possível.

#### 31. item 31

- **exigencia:** A interface ajuda a decidir, não só mostra dados
- **fonte:** build-003 README L88; Dica L99 (segunda-feira de manhã)
- **tipo:** qualidade
- **situacao:** atende
- **falta:** Design atende (Foco da semana, Insights, Pauta da Gabi, Deals para decidir, mensagem pronta). Implementar com ações claras (confirmar ou encerrar).

#### 32. item 32

- **exigencia:** Código limpo para outro dev manter
- **fonte:** build-003 README L89
- **tipo:** qualidade
- **situacao:** ainda_nao_existe
- **falta:** Separar cálculo do score, servidor e página; funções nomeadas, com comentários sobre as regras; constantes (138 dias, janela de 30 dias) num só lugar; o script de conferência reutilizando o mesmo módulo de cálculo.

#### 33. item 33

- **exigencia:** Comece simples, itere; regras + heurísticas bem apresentadas valem mais que ML sem interface
- **fonte:** build-003 Dicas L95 e L97
- **tipo:** qualidade
- **situacao:** atende
- **falta:** Manter o modelo simples. Não acrescentar ML para impressionar.

#### 34. item 34

- **exigencia:** Bônus: filtro por vendedor, manager e região
- **fonte:** build-003 README L100
- **tipo:** bonus
- **situacao:** parcial
- **falta:** Vendedor (pela pessoa escolhida) e manager (visão do gestor) já existem. Não há filtro explícito por regional: adicionar filtros vendedor/manager/regional no Pipeline/Kanban e na máquina do tempo.

#### 35. item 35

- **exigencia:** Time budget de 4 a 6 h; 40 h não ganham pontos; inteligência no uso do tempo
- **fonte:** README raiz L75-79; build-003 L5
- **tipo:** qualidade
- **situacao:** nao_atende
- **falta:** Já passou bastante do prazo. Cortar escopo: Kanban, Clientes com painel lateral e Configurações com CRMs são opcionais e pesam contra. Se forem feitos, que sejam leves e reaproveitem os mesmos dados. Declarar o tempo gasto e justificá-lo no process log (o que levou mais tempo e por quê).

#### 36. item 36

- **exigencia:** Entrega solução funcional, não apresentação bonita; evitar 'foco em parecer inteligente' e '40 páginas onde 5 resolveriam'
- **fonte:** README raiz L17; submission-guide L76-77
- **tipo:** qualidade
- **situacao:** parcial
- **falta:** Risco com as telas novas. A tela de Configurações lista CRMs para integração que não existe: manter o aviso e apresentá-la no README como "o que precisaria para escalar", não como funcionalidade. O Kanban precisa trazer o score e o filtro com cliente / sem cliente para justificar a existência. Manter o README enxuto e mandar os detalhes para docs/.

#### 37. item 37

- **exigencia:** Saber o que automatizar e o que não automatizar
- **fonte:** README raiz L18
- **tipo:** qualidade
- **situacao:** atende
- **falta:** A mensagem para quem não abre o sistema é copiada pelo gestor, não enviada sozinha. Dizer isso explicitamente no README como decisão.

#### 38. item 38

- **exigencia:** Output acionável e específico (não genérico)
- **fonte:** submission-guide L67 e L73
- **tipo:** qualidade
- **situacao:** atende
- **falta:** Os achados são específicos da base. Manter números reais em todas as telas.

#### 39. item 39

- **exigencia:** Consistência com o enunciado (35 vendedores, ~85 contas, ~8.800 oportunidades)
- **fonte:** build-003 README L11 e L27-32
- **tipo:** qualidade
- **situacao:** parcial
- **falta:** A tela de acesso diz "30 vendedores em 3 regionais". Explicar na tela ou no README que 5 dos 35 não têm deals, para não parecer erro de leitura dos dados.

#### 40. item 40

- **exigencia:** Telas pedidas hoje: Pipeline/Kanban com filtro com cliente / sem cliente, Clientes, Configurações, Transparência, Qualidade dos dados
- **fonte:** Não exigidas pelos termos; ligadas a build-003 L88 (decidir), L98 (explicabilidade) e template (Limitações)
- **tipo:** qualidade
- **situacao:** ainda_nao_existe
- **falta:** Prioridade: Transparência (sustenta "por quê" e Lógica) e Qualidade dos dados (sustenta Limitações: 68% sem cliente, 21,7% sem desfecho, corte em 01/03/2017) agregam nota. O filtro de cliente é barato e útil. Kanban, Clientes e Configurações vêm por último. A Transparência deve separar "o que a pessoa trouxe" de "o que a IA fez", alinhada ao template.

#### 41. item 41

- **exigencia:** Selo de conceito e aviso de que não é produto oficial do G4
- **fonte:** Não exigido; boa prática ligada à clareza (submission-guide L69)
- **tipo:** qualidade
- **situacao:** atende
- **falta:** Já está na tela de acesso. Repetir no README e no rodapé do app publicado.

## banca

- **veredito:** A ideia vence o baseline, mas o plano de entrega pode atrapalhar. O que diferencia a submissão é o julgamento sobre os dados: features óbvias que não discriminam, deals "zumbis" de mais de 138 dias, viés antes de 01/03/2017, ritmo de trimestre, um score que é uma probabilidade por coorte e não uma soma de pesos, e a máquina do tempo como prova. Uma IA sozinha com o enunciado entrega pesos para stage, valor, setor e porte. Essa submissão mostra com números que esses pesos são ruído. Isso responde direto a "vai além do óbvio" e "usar as features certas" (challenges/build-003-lead-scorer/README.md, Critérios de qualidade). A máquina do tempo responde a "zero evidência de verificação" (submission-guide.md, O que torna uma submissão fraca).
  
  O escopo atual, porém, empurra a entrega para o que os termos punem. São 10 telas, conceito de produto do G4 com selo, CRMs de integração que não integram, uma tela de Configurações que é cenário, um Pipeline em kanban que repete o Foco da semana, e um tempo bem acima das 4 a 6 horas. Os termos dizem que "soluções que levaram 40 horas não recebem pontos extras" (README.md, Time budget) e citam "Foco em parecer inteligente em vez de resolver o problema" (submission-guide.md). O README do desafio diz: "O deliverable principal é software funcionando — não um documento" e "Pode ser simples, mas precisa funcionar".
  
  Recomendação: entregar um núcleo pequeno e profundo. Manter Acesso, Foco da semana do vendedor, Meu time do gestor, Máquina do tempo e um Transparência curto que absorva Qualidade dos dados. Cortar Configurações/CRMs e o conceito "módulo do G4 OS". Fazer Clientes e kanban só se sobrar tempo, e mesmo assim enxutos. Pôr a energia no que o avaliador confere: rodar com um comando, link vivo, números que o script recalcula, frases de "por quê" corretas, e um process log curto que mostre as correções feitas na IA.
  
  Ponto em aberto: o +42% "ainda sem conferência independente" é hoje o número mais exposto da submissão. Se o script de conferência não chegar ao mesmo valor, ele precisa sair do README.

### por_criterio


#### 1. item 1

- **criterio:** Funciona de verdade? Dá pra rodar seguindo as instruções? (build-003 README, Critérios; 'Precisa rodar (não é mockup, wireframe ou PowerPoint)')
- **ganha:** Servidor Python sem dependências mais um comando local mais um link no Railway: é o setup com menos atrito possível. Ter link vivo e execução local juntos cobre a hipótese de o Railway cair.
- **perde:** Tudo o que ainda é só desenho no Paper não conta como entrega. Se uma tela parecer clicável mas não funcionar (Configurações com CRMs, botão 'conectar'), o avaliador lê como mockup. O risco cresce se o Railway dormir ou cair no dia da avaliação, ou se os dados forem carregados de um caminho absoluto.

#### 2. item 2

- **criterio:** O scoring faz sentido? Usa as features certas? Vai além do óbvio? ('não é só ordenar por valor')
- **ganha:** É o ponto mais forte. Os achados de que produto, setor, regional, gestor, porte e histórico não mudam a taxa de ganho, o limite de 138 dias, o ritmo de trimestre, o viés antes de 01/03/2017 e os 21,7% sem desfecho respondem direto à dica 'O que mais importa? Olhe os dados'. Chance × preço de tabela não é ordenar por valor, e a comparação com 'ordenar por valor' mostra o ganho.
- **perde:** Se a prioridade final ficar parecida demais com o valor (chance quase igual entre deals da mesma coorte), o avaliador pode achar que 'no fundo é valor'. Mostrar exemplos em que um deal barato passa à frente de um caro ajuda. Coortes pequenas por idade × ponto do trimestre podem dar chances instáveis, e sem um mínimo de amostra visível isso vira crítica. Usar o preço de tabela em vez do close_value precisa de uma frase de justificativa.

#### 3. item 3

- **criterio:** O vendedor (não-técnico) consegue usar e entender? Explainability ('se o vendedor entender POR QUE o deal tem score 85')
- **ganha:** Uma frase com números por deal é exatamente o que a dica pede. O perfil vendedor/gestor mais a escolha da pessoa cumprem o bônus de filtro por vendedor/manager.
- **perde:** Termos como 'coorte', 'receita esperada' e 'ponto do trimestre' assustam quem não é técnico. Se a frase usar estatística ('IC', 'p-valor', 'taxa base'), perde. O excesso de telas também dilui a navegação: o vendedor da segunda-feira precisa de uma tela, não de dez.

#### 4. item 4

- **criterio:** A interface ajuda a tomar decisão ou só mostra dados?
- **ganha:** O Foco da semana (lista curta e ordenada com o porquê) e a recomendação de limpar zumbis (mais de 138 dias) são decisão. Para o gestor, apontar deals que o time deixa abertos para não marcar perda é contexto de CRM real que o baseline não tem.
- **perde:** Kanban, Clientes com abas, Configurações e Qualidade dos dados como telas soltas são telas de mostrar dados. Para um avaliador cético, cada tela que não termina em ação ('o que faço agora') pesa contra.

#### 5. item 5

- **criterio:** O código é limpo o suficiente pra outro dev dar manutenção?
- **ganha:** Python sem dependências, lógica de score separada e um script de conferência que recalcula os números são sinais fortes de manutenibilidade e de verificação.
- **perde:** Uma página única gigante com HTML/JS inline e a lógica de score duplicada entre o front e o Python é o padrão comum de 'vibe code'. Quanto mais telas, maior esse risco no orçamento de tempo.

#### 6. item 6

- **criterio:** Documentação mínima: Setup, Lógica, Limitações (build-003 README, item 2) e formato do template (templates/submission-template.md)
- **ganha:** O README no formato do template mais o script de conferência cobrem bem. Limitações honestas (cliente vazio em 68%, viés antes de 03/2017, ausência de conferência independente do +42%) mostram julgamento.
- **perde:** O guia avisa: 'Documento de 40 páginas onde 5 resolveriam'. Uma tela de Transparência longa, mais um doc de contribuição, mais as pranchas de UX exportadas, mais o process log extenso viram volume. O avaliador quer achar Setup, Lógica e Limitações em menos de 2 minutos.

#### 7. item 7

- **criterio:** Process log: ferramentas, decomposição, onde a IA errou, o que você adicionou, iterações (submission-guide.md); 'Sem evidência de processo = desclassificado' (README.md, Regras)
- **ganha:** Tem as melhores evidências possíveis: a versão autônoma de 20 minutos descartada, o inventário dos dados antes da análise, as hipóteses testadas e descartadas, os erros corrigidos (tabela com viés, ranking de vendedor que era efeito de time, falso sinal de porte) e a vivência de CRM. Isso responde item por item ao que o guia pede e à frase do README: 'saber o que pedir, quando desconfiar, o que ajustar'.
- **perde:** Um export bruto e enorme da conversa sem um índice curto ('os 5 momentos em que corrigi a IA', com link para o trecho) faz o avaliador não achar as provas. A versão descartada só ajuda se aparecer lado a lado com a atual, mostrando o que mudou e por quê.

#### 8. item 8

- **criterio:** Superar o baseline / 'O que só um humano com contexto consegue fazer' (README.md, Sobre o baseline)
- **ganha:** A máquina do tempo (backtest legível) e o diagnóstico de que as features 'óbvias' não discriminam são exatamente o que o baseline não faz. O baseline normalmente monta pesos arbitrários para stage, valor, setor e porte, sem validar.
- **perde:** A identidade de 'módulo do G4 OS' e a grande quantidade de telas genéricas de CRM (kanban, clientes, integrações) são o que o baseline também gera com facilidade. Elas puxam a percepção para 'parecido com o baseline' e escondem o diferencial.

### riscos


#### 1. item 1

- **risco:** Número de resultado não reproduzível: o +42% em 30 dias contra ordenar por valor está 'ainda sem conferência independente'. Se o avaliador rodar o script e der outro valor, ou achar vazamento de futuro na máquina do tempo (stage atual, close_date ou dados posteriores à data usados na reconstrução), a credibilidade de toda a submissão cai. Isso cai na fraqueza 'a IA disse, o candidato acreditou'.
- **gravidade:** alta
- **mitigacao:** Antes de qualquer tela nova, fechar o script de conferência e fazê-lo imprimir o +42% e cada número citado no README a partir dos CSVs. Listar no README as regras anti-vazamento da máquina do tempo (só deals com engage_date até a data, stage reconstruído como 'aberto' naquela data, fechamentos posteriores invisíveis). Mostrar a distribuição nas 22 datas (mediana, pior data), não só a média. Se não der para conferir, rebaixar para 'resultado preliminar' ou tirar o número.

#### 2. item 2

- **risco:** Escopo contra o orçamento de 4 a 6 horas: 5 telas desenhadas mais 5 pedidas hoje, deploy, script, process log e export de pranchas, com o tempo já 'bem além'. Os termos dizem que 40 horas não ganham pontos extras e valorizam 'inteligência no uso do tempo'. O efeito prático é chegar com 10 telas meio funcionando em vez de 4 sólidas, e as meio funcionando parecem mockup.
- **gravidade:** alta
- **mitigacao:** Congelar o escopo no núcleo (Acesso, Foco da semana, Meu time, Máquina do tempo, Transparência curta). Admitir no README, em uma frase, que o tempo passou do sugerido e onde ele foi gasto (análise e validação, não telas). Tudo o que não for construído sai também do Paper exportado, ou vai para 'Próximos passos', sem aparecer como tela.

#### 3. item 3

- **risco:** 'Não é mockup': a tela de Configurações com lista de CRMs que não integram e tem aviso de 'apenas referência' é, por definição, um mockup dentro do software. O próprio aviso confessa isso. Um avaliador cético vê cenário e conclui que o candidato gastou tempo em aparência.
- **gravidade:** alta
- **mitigacao:** Cortar a tela. Trocar por uma linha no rodapé ou na Transparência, como 'Fonte dos dados: CRM Sales Predictive Analytics (Kaggle, CC0), carregado em <data>; N deals, M contas', com o horário de carga real. Em 'Limitações e como escalar', descrever em 3 linhas o que uma integração exigiria (mapeamento de campos: stage, engage_date, close_date, conta, produto) sem mostrar logos.

#### 4. item 4

- **risco:** Identidade de produto do G4 ('módulo do G4 OS' com selo 'Conceito'): pode parecer bajulação ou 'foco em parecer inteligente', e usa marca de terceiros mesmo com aviso. O avaliador do G4 conhece o próprio produto, e qualquer divergência de identidade, nome ou visual pesa contra. O desafio pede uma ferramenta para a Head de RevOps de um time de 35 vendedores, não um pitch de produto para o G4.
- **gravidade:** media
- **mitigacao:** Tirar o enquadramento G4 OS e a identidade visual que remete ao G4. Dar um nome neutro e descritivo (por exemplo 'Foco de Pipeline'). Se quiser manter a visão de produto, deixar uma frase em Recomendações ('isto poderia virar um módulo...'), nunca no app.

#### 5. item 5

- **risco:** 'Documento de 40 páginas onde 5 resolveriam': README completo, tela de Transparência longa ('como chegamos', 'o que cada um contribuiu'), doc de contribuição, chat export integral, pranchas de UX e Qualidade dos dados. O conjunto pode afogar o avaliador e esconder Setup, Lógica e Limitações.
- **gravidade:** media
- **mitigacao:** README com no máximo 2 telas de rolagem: executive summary de 3 a 5 frases, link e comando, Lógica em 5 bullets com números, Limitações em 5 bullets, process log resumido com os 5 erros da IA corrigidos e o que você adicionou. O resto vai para process-log/ e docs/ com um índice. Na Transparência do app, só o necessário para o vendedor confiar no score. A história do processo fica no README e no process log, não no app.

#### 6. item 6

- **risco:** Coortes pequenas e chance instável: a probabilidade por idade × ponto do trimestre pode virar 0% ou 100% com poucos casos, o que gera frases estranhas ('chance de 100%') e prioridades que mudam de forma brusca. O avaliador testa deals extremos.
- **gravidade:** media
- **mitigacao:** Definir um mínimo de amostra por célula e suavização (juntar células vizinhas, ou encolher para a taxa geral da faixa de idade). Mostrar o 'n' na frase de por quê ('em 214 deals parecidos, 31% fecharam em 30 dias'). Cobrir isso no script de conferência.

#### 7. item 7

- **risco:** Achados negativos ('nada discrimina') lidos como modelo pobre: um avaliador apressado pode ver 'só idade e trimestre' e concluir que o score é simplório ou que o candidato não usou as features pedidas (produto, conta, vendedor).
- **gravidade:** media
- **mitigacao:** Na Transparência e no README, mostrar em uma tabela pequena cada feature óbvia testada, a taxa de ganho por categoria e o veredito 'não muda a decisão'. Assim, ignorar a feature vira prova de julgamento. A dica do desafio pergunta explicitamente 'O que mais importa? Olhe os dados'.

#### 8. item 8

- **risco:** Deploy frágil: o Railway dormindo, caindo ou expirando no dia da avaliação, ou um link quebrado no README.
- **gravidade:** media
- **mitigacao:** Execução local com um comando (python3 app.py) sem dependências e com os CSVs incluídos ou com instrução clara de download. Prints ou GIF curto do app no README como garantia. Testar o link de um navegador anônimo e de outra rede antes de abrir o PR.

#### 9. item 9

- **risco:** Regras de PR: alterar arquivo fora de submissions/seu-nome/, título fora do formato, mais de um PR. Os termos dizem que 'PRs que alteram outros arquivos serão rejeitados' (CONTRIBUTING.md).
- **gravidade:** baixa
- **mitigacao:** Branch submission/seu-nome, tudo dentro de submissions/seu-nome/ (solution/, process-log/, docs/), título '[Submission] Nome — Challenge 003', conferir com git diff --stat contra main antes de abrir. Atualizar sempre com push na mesma branch.

#### 10. item 10

- **risco:** Kanban e Clientes diluem o diferencial e parecem CRM genérico, que o baseline também produz. Também consomem horas de front.
- **gravidade:** baixa
- **mitigacao:** Ver a recomendação por tela: se forem feitos, que cada um termine numa decisão ligada ao score (zumbis na coluna, prioridade no card) e que fiquem depois do núcleo pronto e conferido.

### telas_pedidas_hoje


#### 1. item 1

- **tela:** Configurações com lista de CRMs para integração (só referência, com aviso)
- **recomendacao:** cortar
- **motivo:** É o caso mais direto de 'mockup dentro do software' e de 'parecer inteligente em vez de resolver'. O aviso 'apenas para referência' confessa que a tela não faz nada. Não atende nenhum critério declarado. A necessidade real (deixar claro de onde vêm os dados) cabe numa linha 'Fonte dos dados' no rodapé ou na Transparência, com nome do dataset, licença, contagens e data de carga. O caminho para integração vai em 'Limitações / como escalar' no README, em texto.

#### 2. item 2

- **tela:** Transparência (como o score funciona, como chegamos a ele, o que cada um contribuiu: pessoa e IA)
- **recomendacao:** enxugar
- **motivo:** A parte 'como o score funciona' é o diferencial e atende direto à explainability. Manter, em linguagem de vendedor: o que entra (idade do deal, ponto do trimestre, preço), o que testamos e não entra (tabela curta com produto, setor, regional, gestor, porte, histórico), as regras de higiene (mais de 138 dias, sem desfecho) e o link para a máquina do tempo. A parte 'como chegamos' e 'quem contribuiu com o quê' é process log: pertence ao README e a process-log/, não ao app que o vendedor abre na segunda-feira. No app, no máximo um bloco de 3 a 4 linhas com link para o README. Colocar a narrativa do processo no produto soa autopromoção.

#### 3. item 3

- **tela:** Qualidade dos dados
- **recomendacao:** enxugar
- **motivo:** Os achados (cliente vazio em 68%, 21,7% sem desfecho, 81% dos negociando com mais de 138 dias, nada fechado antes de 01/03/2017) são fortes e dão credibilidade, mas como tela própria viram dashboard de dados. Fundir na Transparência, como seção 'O que os dados não permitem' com 4 números. Os mais acionáveis viram ação na tela do gestor: 'X deals do seu time passaram de 138 dias: fechar ou justificar'. Isso conecta direto com a sua vivência de deals deixados abertos para não marcar perda.

#### 4. item 4

- **tela:** Pipeline em kanban (fases e oportunidades, filtro com cliente / sem cliente)
- **recomendacao:** enxugar
- **motivo:** O dataset tem só 2 fases abertas (Prospecting, Engaging) mais Won/Lost, então um kanban fica com 2 colunas úteis e não acrescenta decisão ao Foco da semana, que já ordena. Se fizer, que seja uma visão alternativa da mesma lista do vendedor: cards ordenados pela prioridade dentro de cada coluna, com selo de zumbi (mais de 138 dias), uma coluna ou faixa de 'para limpar', e sem drag-and-drop (mover card sem gravar parece funcional e não é). O filtro com/sem cliente é útil e barato como filtro global, ligado ao achado de 68% vazio e ao fato de que, no resto, o campo se comporta como sorteado. Fazer só depois do núcleo pronto e conferido.

#### 5. item 5

- **tela:** Clientes (lista e painel lateral com abas: dados, oportunidades abertas, oportunidades fechadas)
- **recomendacao:** enxugar
- **motivo:** É o tipo de tela de CRM que o baseline gera e que, pelos seus próprios achados, não muda a decisão (conta e porte não discriminam, e o cliente está vazio em 68% dos abertos). Três abas é escopo de produto, não de desafio. Se fizer, uma versão mínima: lista de contas com contagem de abertos e soma de prioridade, e um painel com as abertas já com score e porquê, mais as fechadas em uma lista simples. Sem aba de 'dados do cliente' elaborada. Prioridade baixa. Se o tempo apertar, cortar.
- **primeiro_minuto:** Meta: em 60 segundos o avaliador vê que roda com dados reais, que o score não é ordenar por valor, que cada deal se explica e que existe prova.
  
  0 a 10 s: o link abre direto, sem cadastro e sem tela de conceito ou marca. O acesso simulado já vem com uma pessoa pré-selecionada ('Entrar como vendedor: <nome real do dataset>') e um botão secundário 'ver como gestor'. Uma linha discreta de fonte: 'Dados: CRM Sales Predictive Analytics, 8.800 deals, carga real'.
  
  10 a 30 s: Foco da semana. Topo com uma frase de decisão ('Esta semana, foque nestes 5 deals: receita esperada R$ X'). Lista curta ordenada, cada linha com prioridade 0 a 100, chance em 30 dias, valor e a frase do porquê com números e amostra (ex.: 'Deals com 20 a 30 dias no último mês do trimestre fecharam em 41% dos 180 casos; valor de tabela 5.482'). Pelo menos um caso visível de deal mais barato acima de um mais caro, para mostrar que não é ordenação por valor. Um bloco separado: 'N deals seus passaram de 138 dias: nenhum deal nessa idade fechou; marque perda ou justifique'.
  
  30 a 50 s: um clique em 'Isto funciona?' leva à Máquina do tempo já posicionada numa segunda-feira passada com resultado claro: lado a lado 'o que o score indicou' × 'ordenar por valor' × 'o que aconteceu nos 30 dias', com receita de cada lista e o agregado (+42% em 22 datas, com mediana e pior caso), reproduzível pelo script citado no rodapé.
  
  50 a 60 s: troca para gestor e vê o time numa tela: deals zumbis por vendedor, receita esperada da semana e quem precisa de ajuda, com a ressalva honesta de que as diferenças entre vendedores estão dentro do acaso.
  
  O que não pode aparecer no primeiro minuto: tela de integrações, selo de produto G4, texto longo sobre o processo, termos estatísticos, telas vazias ou botões que não fazem nada.
