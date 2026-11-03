# Listar etapas do teste da G4

Source: codex chat `01a19a53-9f3a-71a3-86b6-c248212d7e55`.
Captured: 2026-11-02 06:03:44 UTC.
Method: user/assistant message extraction from the app's read_thread response.
Coverage: 10 returned turns; hasMore=false.
Original message languages and wording are preserved. Formatting normalization:
trailing whitespace is removed and the file ends with one newline. This is a text snapshot,
not a native platform export. Tool calls/results, internal reasoning, system
instructions, attachments, and graphical content are not included. Platform
citation markers may be preserved without their original interactive rendering.
The source API limits each message item to 20,000 characters; no returned
message reached that limit. This snapshot alone cannot prove that the service
returned all historical branches or deleted/edited messages.
This capture includes the current turn only up to the messages available at capture time; its later messages and final response require a subsequent capture.

---

Turn: `01a19a54-0161-70a1-93ac-dc14acf3601d` | started: 2026-11-02T03:35:59.000Z

## User

quero que lembre o que conversamos sobre o teste da g4, e faça uma lista de etapas para cumprir o requisito


## Assistant (commentary)

Vou revisar o contexto disponível neste chat e os arquivos do projeto para identificar qual requisito do teste da G4 estamos tratando e organizar as etapas para cumpri-lo.

## Assistant (final_answer)

Não vejo uma conversa anterior sobre o teste neste chat. Pelo material do projeto, o teste da G4 pede que você escolha **um desafio**, entregue a solução correspondente e mostre **como usou IA**. Sem o process log, a submissão pode ser desclassificada.

### Etapas para cumprir o requisito

1. **Escolha um desafio** entre os quatro do repositório: Churn, Redesign de Suporte, Lead Scorer ou Estratégia de Social Media.
2. **Leia o briefing completo** do desafio escolhido e anote cada entrega obrigatória e critério de avaliação.
3. **Obtenha e entenda os dados** indicados no briefing. Confira colunas, volume, qualidade e limitações antes de tirar conclusões.
4. **Defina o resultado que vai entregar** e divida o trabalho em etapas. O prazo recomendado é de 4 a 6 horas.
5. **Analise o problema com evidências**: use os dados reais, registre números e diferencie achados de hipóteses.
6. **Construa a solução exigida pelo desafio**. Por exemplo, no Lead Scorer é obrigatório criar uma ferramenta funcional; no Churn, o deliverable principal é um diagnóstico.
7. **Documente a lógica e as recomendações**: explique o que fez, por que fez, o que a empresa deveria priorizar e quais são as limitações.
8. **Mantenha o process log durante o trabalho**: registre as ferramentas de IA usadas, prompts e iterações, erros da IA e como você os corrigiu, além das decisões que dependeram do seu julgamento.
9. **Monte a submissão** na pasta `submissions/seu-nome/`, usando o template do repositório. Inclua a solução e as evidências do processo.
10. **Envie por Pull Request**, seguindo as instruções de contribuição.

O ponto central é entregar algo **acionável e sustentado por dados**, não apenas uma resposta gerada por IA. Para fechar a lista específica — com dados, entregáveis e critérios do desafio — falta identificar qual dos quatro você escolheu.

---

Turn: `01a19a54-867d-76b3-833c-5d6846ec69a6` | started: 2026-11-02T03:36:33.000Z

## User

tu n tem acesso ao chat do chatgpt?


## Assistant (final_answer)

Não automaticamente. Eu consigo ver as mensagens deste chat e os arquivos do projeto, mas não tenho acesso aos seus outros chats do ChatGPT. Se você colar aqui a conversa sobre o teste da G4, eu uso esse contexto para montar as etapas específicas.

---

Turn: `01a19a54-fa98-79e2-a362-5e2e660820d9` | started: 2026-11-02T03:37:02.000Z

## User

[https://chatgpt.com/share/6ae80554-9530-83e9-acbd-9e30b3a6788b](https://chatgpt.com/share/6ae80554-9530-83e9-acbd-9e30b3a6788b)


## Assistant (commentary)

Vou tentar abrir o link compartilhado. A primeira leitura direta falhou, então vou verificar se o conteúdo está acessível pelo navegador; se o compartilhamento exigir login ou não estiver público, te aviso.

## Assistant (final_answer)

Agora sim — consegui ler o chat compartilhado. A conversa era sobre **como preparar o workspace e conduzir o teste da G4**, com foco em usar IA com critério, preservar seu raciocínio e produzir uma entrega que vá além de uma resposta genérica. Eu resumiria o plano assim:

### Etapas para cumprir o requisito

1. **Preparar o ambiente de forma enxuta.** Criar o workspace e as instruções centrais (`AGENTS.md` e `CLAUDE.md`), além de um índice inicial de conhecimento. Limitar essa preparação a cerca de 8% do esforço; a entrega do desafio precisa continuar sendo o foco.

2. **Entender o repositório da G4 antes de escolher.** Ler os READMEs dos desafios, as instruções de submissão e os materiais disponíveis. Comparar os desafios por aderência à sua experiência, dados, esforço, impacto e potencial de diferenciação.

3. **Escolher e justificar um desafio.** Registrar por que ele é a melhor opção e quais critérios do briefing a solução precisará atender. A decisão final é sua; a IA ajuda a comparar.

4. **Definir o problema antes de construir.** Identificar usuário, problema concreto, hipóteses, resultado de negócio desejado e como medir sucesso. Registrar o escopo e o que ficará de fora.

5. **Pesquisar e analisar com foco.** Examinar os dados e buscar referências relevantes para o problema. Guardar fontes, achados e limitações; separar fatos, hipóteses e recomendações.

6. **Planejar a solução e comparar alternativas.** Definir uma abordagem viável, critérios de aceite e tarefas pequenas. Usar o Claude Code principalmente para explorar e implementar; usar o ChatGPT para questionar hipóteses, decisões e pontos cegos. Recorrer a outra IA só quando uma segunda opinião puder ajudar.

7. **Implementar em ciclos curtos.** Para cada parte: construir, validar, revisar o resultado e registrar o que mudou. Não tratar uma sugestão da IA como concluída até que tenha sido verificada.

8. **Manter o process log desde o começo.** Uma estrutura possível é `process-log/` com registros de preparação, entendimento do problema, pesquisa, desenho da solução, implementação, validação e decisões finais. Para cada etapa, guardar o contexto, o que a IA sugeriu, o que você aproveitou ou rejeitou, seu motivo e a evidência correspondente.

   A conversa compartilhada pode ser registrada como **preparação anterior à análise detalhada do desafio**. Separe as sugestões da IA das decisões que você tomou depois; não descreva como feito algo que ainda não aconteceu.

9. **Validar a solução e buscar diferenciação.** Verificar casos extremos, dados inconsistentes, limitações e erros da IA. Comparar com as respostas baseline mencionadas pela G4 e mostrar, com evidências, onde sua solução agrega valor.

10. **Preparar a submissão.** Incluir solução, documentação, limitações, histórico de uso de IA e evidências. Abrir o Pull Request conforme as instruções do repositório.

11. **Adicionar o CodeTour quando a solução estiver estável.** O tour pode guiar o avaliador pelo problema, estrutura, fluxo principal, decisões, validação e execução. É um complemento para explicar a aplicação; não substitui README nem process log.

A regra prática que amarra tudo é: **cada etapa importante deve gerar um entregável e uma evidência do processo**. O process log não precisa registrar cada interação trivial; deve mostrar as conversas e decisões que influenciaram a solução, inclusive erros corrigidos e ideias descartadas.

---

Turn: `01a19a95-b13d-7490-989a-cb03c1cd7c78` | started: 2026-11-02T04:47:43.000Z

## User

1- faz sentido deixar so 8% do foco? pensei em focar nisso agr pra evitar uso excessivo de token
2- ok, me mande um resumo de cada desafio
3- pensei em pegar o desafio mais complexo para me provar e colocar o meu uso junto a IA em teste
4- sim
5- daria pra gente olhar outras pull requests ne?
6- ok
7- concordo e cada parte tem que ter o check no md
8- sim
9, 10 e 11- ok

coisas a mais a se pensar:

sempre fazer em ingles e seguir regras de programaçao e git
vamos fazer testes unitarios e integraçao? se precisar podemos fazer um pequeno dashboard interno para analise e consulta de resultados, desde o q passou nos testes e o q n passou, ate para testes avançados e simulaçoes
se precisar podemos fazer uma area que funciona como backlog, mostrando componentes criados e funçoes criadas para visualizaçao separada, como se fosse um "design system" onde a pessoa pode analisar, faz sentido?


## Assistant (final_answer)

Sim — com o contexto do outro chat, ajustaria o plano assim:

### 1. Preparar o ambiente agora

Faz sentido cuidar disso antes do desafio para evitar repetir contexto e gastar tokens depois. Eu trataria os **8% como referência, não como limite rígido**. Vamos preparar só o que reduz retrabalho: instruções em inglês, estrutura mínima de contexto e registro do trabalho. Se começarmos a criar muitas skills, dashboards e ferramentas antes de escolher o desafio, a preparação vira o próprio projeto.

### 2. Resumo dos desafios

| Desafio | O que você precisa resolver | O que mais exige |
|---|---|---|
| **001 — Diagnóstico de Churn** | Cruzar cinco tabelas de uma empresa SaaS para encontrar causas e segmentos de risco, estimar impacto e recomendar ações. | Análise de dados, cuidado com correlação e recomendações para executivos. |
| **002 — Redesign de Suporte** | Analisar métricas e textos de tickets, apontar gargalos, propor o que automatizar e construir um protótipo funcional. | Combina análise, desenho de processo, IA e implementação; exige justificar onde manter intervenção humana. |
| **003 — Lead Scorer** | Criar uma ferramenta funcional que priorize oportunidades de vendas usando dados reais e explique o score para o vendedor. | Construção de software utilizável, lógica explicável e uma interface prática. |
| **004 — Estratégia Social Media** | Analisar 52 mil posts, comparar desempenho entre plataformas e patrocínios e recomendar uma estratégia baseada em dados. | Análise segmentada, comparação justa e comunicação executiva clara. |

### 3. Sobre escolher o mais complexo

“Mais complexo” pode significar coisas diferentes. O **002 é o mais abrangente**, pois junta diagnóstico, automação e protótipo. O **003 concentra a prova em construir uma aplicação funcional**. O **001 e o 004 pesam mais em análise de dados**, com o 004 trazendo um conjunto maior e uma comparação de patrocínios mais delicada.

Pelo que você quer testar — seu trabalho junto com IA, além da capacidade de construir — eu colocaria **002 e 003 como finalistas**. Minha recomendação inicial seria o **002** para provar amplitude; o **003** se sua prioridade for demonstrar execução de software.

### 4. Pull Requests anteriores

Sim, faz sentido olhar PRs de outros candidatos, se estiverem acessíveis. Podemos observar como organizaram a solução, quais formatos de evidência usaram e o que parece faltar — sem copiar a abordagem. Isso também pode ajudar a entender o padrão de avaliação. Eu faria essa pesquisa depois de mapear o repositório e antes de fechar a escolha do desafio.

### 5. Regras de idioma e Git

Combinado: documentação do projeto, código, comentários técnicos, nomes de branches, commits e PRs em **inglês**, seguindo convenções de programação e Git. Podemos conversar estrategicamente em português e registrar as decisões do trabalho em inglês.

### 6. Testes e checks no plano

Sim: cada etapa terá um item verificável no Markdown, com objetivo, resultado esperado, critério de aceite, testes necessários e status — por exemplo, `Proposed`, `Approved` e `Validated`.

Vamos usar testes unitários e de integração **quando fizerem sentido para a solução**. Para um protótipo, os testes devem cobrir os fluxos e riscos importantes, sem criar uma infraestrutura de testes maior que o produto. Os resultados, inclusive falhas e correções, entram no registro.

### 7. Dashboard interno e catálogo de componentes

As duas ideias fazem sentido como ferramentas de apoio, mas eu não as construiria antes de haver uma necessidade concreta:

- **Dashboard de análise e testes:** pode ser útil se houver muitos cenários, simulações ou resultados difíceis de acompanhar. Para começar, relatórios de teste e um Markdown com resultados podem bastar.
- **Catálogo visual de componentes:** vale considerar se a aplicação tiver vários componentes de interface ou se o avaliador precisar explorá-los separadamente. Se for pequena, uma galeria simples ou um CodeTour pode cumprir esse papel.

Assim mantemos o preparo enxuto, mas já deixamos essas possibilidades no plano, com critérios para decidir se entram.

---

Turn: `01a19aaa-4938-7880-9743-f77dd2c4fd46` | started: 2026-11-02T05:10:13.000Z

## User

3- seria bom escolher um projeto que n foi tao escolhido por outras pessoas?
4- pull requests: [https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pulls](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pulls) (pode usar pra ver qual projeto foi menos escolhido, se for uma boa ideia)
5- mas e para os revisores? seria interessante estar em pt?


## Assistant (commentary)

Vou olhar os PRs abertos e fechados para ver se o desafio aparece neles e se há algum padrão de participação. Também vou separar essa evidência da decisão de idioma: pouca submissão pode ser um sinal útil, mas não prova sozinha que o desafio foi menos escolhido.

## Assistant (final_answer)

**3. Vale escolher o desafio menos escolhido?** Pode ajudar a diferenciar sua submissão, mas eu não usaria popularidade como critério principal. O que mais importa é combinar um desafio que você consiga executar bem com uma solução forte.

Na primeira página dos PRs, que lista submissões recentes, vi **um PR identificado como Challenge 004**, quatro como 002, seis como 001 e doze como 003. Isso sugere que o **004 pode estar menos escolhido**, mas é só uma amostra da página — não uma contagem completa de todos os PRs. Há 193 PRs abertos no repositório, e alguns títulos não identificam o desafio. [Lista de PRs da G4](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pulls)

Então eu não concluiria ainda que o 004 é o menos escolhido no total. Mas vale investigá-lo: pode ser uma boa combinação de diferenciação e análise complexa. A decisão deve considerar também seus dados, seu interesse e o tipo de trabalho que quer demonstrar.

**5. Idioma para os revisores:** sim, eu faria a entrega voltada aos revisores em **português**. O briefing e o guia da G4 estão em português, então isso facilita a leitura e avaliação. Ajustaria a regra anterior assim:

- **Português:** README da submissão, análise, recomendações e explicações dirigidas ao avaliador.
- **Inglês:** código, nomes de variáveis, comentários técnicos, branches, commits e PR.

Se quiser maximizar a acessibilidade, o resumo executivo pode ter uma versão curta em inglês também, mas eu manteria o português como idioma principal da avaliação.

---

Turn: `01a19aad-9d79-7dc2-8af3-a8cc8a578138` | started: 2026-11-02T05:13:51.000Z

## User

001: 45
002: 42
003: 95
004: 21

pegando por tipo e quantidade de pessoas criando projetos, qual tu escolheria? quero me destacar e parece q escolher o com menos poderia abrir essa porta, mas fico na duvida pq foi tao pouco escolhido


## Assistant (final_answer)

Com esses números, **eu escolheria o 004 — Estratégia de Social Media**, dado que você quer se destacar e está considerando a quantidade de pessoas em cada desafio.

Ele teve **21 participantes**, contra 42 no 002, 45 no 001 e 95 no 003. Isso não garante uma avaliação mais fácil nem uma vantagem automática, mas sugere menos concorrência direta. E o 004 ainda permite um trabalho bem robusto: analisar 52 mil posts, comparar patrocínio e conteúdo orgânico com controles justos e transformar os achados em decisões práticas.

Eu não sei por que menos pessoas o escolheram. Pode ser preferência por desafios mais técnicos, perfil dos candidatos ou outros motivos; o número, sozinho, não revela isso. Também não significa que o desafio seja simples.

Minha recomendação é escolher o **004** e buscar diferenciação pela qualidade da análise: comparar posts patrocinados e orgânicos levando em conta plataforma, tamanho do creator e categoria; explicitar limites dos dados; e entregar recomendações que o time de marketing consiga usar. Um dashboard ou ferramenta de acompanhamento pode entrar se ajudar a tornar essas decisões recorrentes — sem virar trabalho extra só para parecer mais técnico.

O **002** seria minha escolha se a prioridade principal fosse testar a amplitude técnica, já que combina diagnóstico, proposta de automação e protótipo. Mas, pesando **chance de se destacar pela escolha** junto com um desafio ainda exigente, eu iria de **004**.

---

Turn: `01a19ab2-6be4-7621-848a-4abc1cc7fe96` | started: 2026-11-02T05:19:06.000Z

## User

usando o sol no high pra pensar e extra high pra executar, acha que consigo terminar bem a tarefa? vou perguntar pra ele decidir entre o segundo e o quarto projeto


## Assistant (final_answer)

Sim, acho que você consegue fazer uma entrega forte — **desde que mantenha o escopo controlado**. O High pode ajudar a comparar e planejar; o Extra High pode ser útil em decisões difíceis e revisões críticas. Mas o nível de raciocínio, sozinho, não garante qualidade: o que vai pesar é validar dados, resultados e decisões, e registrar o processo.

Os dois desafios cabem no tempo recomendado de 4–6 horas, mas exigem trabalhos diferentes:

- **002:** diagnóstico operacional, proposta de automação e protótipo. É mais amplo; precisa limitar o protótipo a um fluxo útil.
- **004:** análise de conteúdo e patrocínios, com recomendações. Tem menos participantes pelos números que você trouxe, mas exige comparar grupos de forma justa e não confundir correlação com causa.

Eu pediria ao Sol uma **recomendação justificada**, não que decida por você. Pode usar este prompt:

> Compare os desafios 002 e 004 para mim. Quero me destacar, produzir uma entrega de alta qualidade no tempo recomendado de 4–6 horas e demonstrar bom julgamento usando IA. Considere minhas experiências com agentes, automações, integrações e arquitetura. Para cada desafio, avalie: aderência às minhas habilidades, dificuldade real, riscos de dados e escopo, possibilidade de diferenciação, entregáveis obrigatórios e o que caberia no tempo. Separe fatos do briefing de hipóteses. Termine recomendando um deles e explique o principal trade-off. Não escolha apenas porque há menos submissões.

Depois, compare a recomendação com a sua motivação principal: **se for testar amplitude entre análise e construção, o 002; se for aproveitar a menor quantidade de participantes e se destacar pela qualidade analítica, o 004**.

---

Turn: `01a19ab3-20e8-7512-b820-0c5a1b3da433` | started: 2026-11-02T05:19:53.000Z

## User

falo pra ele levar em conta a quantidade de pr aberta pro 2?


## Assistant (final_answer)

Sim. Passe os números de PR explicitamente e peça que ele considere popularidade **como critério secundário**: pode indicar menos concorrência, mas não prova que será mais fácil se destacar.

Você pode acrescentar ao prompt:

> Considere também estes números de participantes/submissões: Challenge 002: 42; Challenge 004: 21. Use isso como um sinal de possível concorrência, não como prova de dificuldade ou chance de aprovação. Diga se essa diferença mudaria sua recomendação e por quê.

---

Turn: `01a19ad3-cee5-72b1-97e8-b609301eea97` | started: 2026-11-02T05:55:34.000Z

## User

vou selecionar o projeto 2, levando em conta tudo q falamos e as decisoes tomadas, pense tambem se é bom usarmos o protocolo OKF da google para fazer a inteligencia da IA ([https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md))


## Assistant (commentary)

Vou revisar a especificação do OKF e o estado do repositório para definir uma estrutura enxuta de contexto, planejamento e evidências para o desafio 002, considerando as decisões que já tomamos.

## Assistant (final_answer)

**Fechamos o desafio 002 — Redesign de Suporte. Eu usaria OKF para organizar o contexto compartilhado entre as IAs**, começando com poucos documentos e expandindo conforme o trabalho produzir conhecimento.

Li a especificação: o OKF v0.2 é um formato de conhecimento em Markdown com metadados YAML. Ele permite registrar fontes, autoria, verificações e estado dos documentos, com índices para consultar o conteúdo aos poucos. Isso combina com nosso objetivo de manter contexto portátil entre ferramentas. [Especificação oficial do OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)

O benefício para tokens depende de **como os agentes consultam os arquivos**. Minha proposta é que cada sessão leia as instruções, o estado atual e o índice; depois abra somente os documentos relacionados à tarefa. Carregar toda a base em cada interação eliminaria boa parte dessa vantagem.

Para o projeto, eu adotaria esta organização:

| Parte | Responsabilidade |
|---|---|
| `AGENTS.md` e `CLAUDE.md` | Regras de trabalho e instruções para encontrar o contexto |
| `knowledge/` em OKF | Requisitos, definições dos dados, hipóteses, achados e decisões |
| `execution/plan.md` | Etapas com checkboxes, critérios de aceite e evidências de conclusão |
| `process-log/` | Registro das interações com IA, correções e decisões humanas |
| Código, dados e resultados | Implementação e artefatos que sustentam as conclusões |

**Cada informação importante terá uma origem rastreável.** Um achado analítico deverá apontar para o dataset, script e resultado que o sustentam. Uma hipótese continuará identificada como hipótese. O campo `verified` só será preenchido depois de uma verificação real, e revisão humana só será registrada quando você efetivamente revisar. Os estados do OKF (`draft`, `stable`, `deprecated`) terão sua função documental; o andamento das tarefas ficará nos checkboxes do plano.

Também encontrei uma restrição importante: o G4 exige que o PR altere **somente arquivos dentro de `submissions/seu-nome/`**. Portanto, vamos planejar a organização para respeitar esse limite e manter qualquer configuração exclusiva do ambiente fora do diff final. [Instruções de contribuição](/media/hethus/bk/Projetos/g4/ai-master-challenge/CONTRIBUTING.md)

Considerando tudo que decidimos, eu seguiria esta sequência:

1. **Preparar o contexto mínimo:** regras, índice OKF, decisões já tomadas, plano com checkboxes e primeiro registro do processo.
2. **Mapear os requisitos e revisar algumas submissões do 002:** identificar abordagens frequentes, lacunas e oportunidades de diferenciação.
3. **Auditar os dois datasets:** conferir volume, origem, qualidade, campos de tempo, categorias e limitações antes de propor a solução.
4. **Produzir o diagnóstico:** gargalos, relação com satisfação e estimativas de desperdício com premissas explícitas.
5. **Escolher uma automação principal:** candidata inicial — triagem assistida com classificação, encaminhamento e revisão humana quando necessário. A escolha dependerá dos dados.
6. **Construir e validar em entregas pequenas:** testes unitários para regras e cálculos; integração para o fluxo completo; avaliação separada da qualidade da IA.
7. **Consolidar resultados e evidências:** documentação para os revisores, process log, limitações e CodeTour após estabilizar o código.
8. **Preparar a submissão e o PR.**

Há dois cuidados analíticos que podem diferenciar bastante nossa entrega: os datasets representam contextos distintos, então precisamos justificar como serão usados em conjunto; e **tempo até resolução inclui espera**, portanto sua redução não equivale automaticamente a horas de trabalho economizadas.

Mantemos código, Git e documentação técnica interna em inglês; material executivo e explicações ao avaliador em português. O dashboard interno e o catálogo de componentes continuam como possibilidades, entrando quando houver utilidade concreta. No briefing, o protótipo é um diferencial; incluí-lo será uma escolha nossa para demonstrar a automação funcionando. [Briefing do desafio 002](/media/hethus/bk/Projetos/g4/ai-master-challenge/challenges/process-002-support/README.md)

Minha recomendação é **adotar OKF agora como uma base pequena de contexto**, e definir a arquitetura da aplicação depois da auditoria dos dados.

---

Turn: `01a19ad7-70ee-7463-836e-150f78a9c9c5` | started: 2026-11-02T05:59:32.000Z

## User

podemos montar a base e decidir na proxima etapa como os datasets serao usados juntos ne? se sim, ja faça

alem disso, todas as conversas que tivemos ate agora e futuras devem ser colocadas no process log, certo?


## Assistant (commentary)

Sim. Vou montar a base agora e deixar a combinação dos datasets como decisão pendente da próxima etapa. Também vou registrar as conversas disponíveis e definir como preservar as futuras: o process log terá uma narrativa das decisões, ligada aos registros das conversas, com indicação de qualquer trecho indisponível.

## Assistant (commentary)

Encontrei os três chats relevantes disponíveis no aplicativo: a preparação no ChatGPT, a comparação dos desafios e esta conversa. Vou preservar as mensagens retornadas pela ferramenta, com a origem e os limites de cobertura. A branch já está em `submission/giovanne-berteli-comba`; vou usá-la e concentrar os arquivos nessa pasta de submissão.
