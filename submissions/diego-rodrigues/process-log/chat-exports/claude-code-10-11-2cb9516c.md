# Sessão Claude Code 2cb9516c

- **Período (horário de Brasília):** 10/11 22:55 a 11/11 10:08
- **Modelos:** claude-fable-5-2, claude-opus-5, claude-sonnet-4-6
- **Mensagens do Diego:** 9
- **Como foi gerado:** script `exportar_chats.py` sobre o JSONL local do Claude Code. Resultados de ferramenta, lembretes de sistema e corpo de skills foram omitidos; termos de outros clientes e dados pessoais viraram [removido] (3 remoções). Nenhum texto foi reescrito.

---

### Diego · 10/11 22:55

workspace/g4-challenge-003/02-plano-implementacao.md

Revise este plano seguindo as mais completas e avançadas técnicas de: 
Arquitetura de dados
Software engineer
Business model
Saia dos vieses comuns, não quero que siga algum mental model comum
Tudo dentro do melhor padrão de construção de soluções possível. 
Ao final estruture e melhore esse guia, trazendo um repositório ou modelo ou skill que documente todo o processo e uso de modelos e e IA para estar compliance com as solicitação
Seja extremamente minucioso na entrega e revisão
> ferramenta: `Skill` — superpowers:brainstorming  
> ferramenta: `Read` — workspace/g4-challenge-003/02-plano-implementacao.md  
> ferramenta: `Read` — ~/.claude/projects/-Users-diegorodrigues-AIS-OS/memory/g4-ai-master-challenge.md  
> ferramenta: `Bash` — List the challenge project folder contents  
> ferramenta: `Read` — workspace/g4-challenge-003/01-guia-fde.md  
> ferramenta: `Read` — workspace/g4-challenge-003/README.md  
> ferramenta: `Read` — workspace/README.md  
> ferramenta: `Bash` — Check whether the fork exists, sizes of analysis and data files, and available tools  
> ferramenta: `Bash` — Show the EDA and backtest scripts with their saved outputs  
> ferramenta: `Bash` — List the official challenge repository files (excluding submissions)  
> ferramenta: `Read` — workspace/g4-challenge-004/00-benchmark-prs.md  
> ferramenta: `Bash` — List the official challenge repository files via the GitHub API  
> ferramenta: `Bash` — Download the official challenge rules, submission guide and template for reading  
> ferramenta: `Bash` — Show the first EDA output, check for pandas, and peek at the CSV headers  
> ferramenta: `Bash` — Run a verification script against the dataset to check the plan's pinned numbers and statistical claims  
> ferramenta: `Bash` — Re-run the backtest with censoring-aware probabilities to test whether the plan's core thesis holds  
> ferramenta: `Bash` — Test the time-based expected-value ranking on independent windows with confidence intervals and calibration  
> ferramenta: `Bash` — Inspect calendar patterns in when deals are won and lost  
> ferramenta: `Bash` — Quantify the quarterly calendar effect by deal age and month of quarter  
> ferramenta: `Bash` — Backtest a calendar-aware score against price ordering and the plan's v1 policy, as-of each month  
> ferramenta: `Bash` — Check whether the three top public submissions mention the quarterly calendar pattern  
> ferramenta: `Bash` — Check the capacity formula, per-seller queues, pipeline coverage and remaining candidate signals  
> ferramenta: `Bash` — Read how submission #242 uses the quarter deadline and list its files  
> ferramenta: `Bash` — Compare the calendar-based score against the best public approach and compute the reference-date snapshot under the corr  
> ferramenta: `Bash` — Fix a column-name clash and rerun the remaining sections of the comparison  
> ferramenta: `Bash` — Estimate the statistical power of the plan's pilot experiment design  
> ferramenta: `Skill` — superpowers:writing-plans  
> ferramenta: `Skill` — update-config  
> ferramenta: `Bash` — Check the archive folder, available Python versions, session transcript location and the reference weekday  

**Claude (<synthetic>)**

You've hit your 5-hour limit · resets 12:40am (America/Sao_Paulo)

---

### Diego · 11/11 08:31

status desta solicitação

**Claude (claude-fable-5-2)**

**Status: análise e verificação concluídas; ainda não gravei nada no projeto.** Até aqui li o plano, o guia, as regras oficiais do repositório do G4 e os PRs #240–242, e rodei nove scripts de conferência contra o dataset. Estou começando a escrever os entregáveis agora.

O que a conferência achou muda o plano, então vale você saber antes de eu terminar:

| # | Achado (conferido por script) | Efeito no plano v1 |
|---|---|---|
| 1 | Com `hoje = 2018-01-01` os vencidos são 1.301, não 1.291; só 30 dos 35 vendedores têm deal e 27 têm deal aberto | Testes pinados da Tarefa 2, 3 e 5 falham no primeiro `pytest` |
| 2 | `tabela_chance` usa só deals fechados: mostra "100 em 100 decidem" para deal de 120 dias; com os abertos na conta o real é 16 | O número mais visível da tela sai errado, e pelo viés que o process log diz ter corrigido |
| 3 | Os fechamentos param no fim do trimestre seguinte ao engajamento (6.710 de 6.711). Vivos de verdade: 115 deals e US$ 236 mil, não 298 | O plano está atrás do PR #242 no achado central; os "US$ 3,66 mi / 74%" do guia são dessa regra, não da de 138 dias |
| 4 | "3× o aleatório" é só mistura de preço: o top 5 por preço custa 3,04× a média e acerta o mesmo tanto (39,5% contra 38,9%) | A frase do CFO não se sustenta |
| 5 | Deal lento nunca decide no 1º mês do trimestre: 0 de 3.618 em três trimestres. E 01/01/2018 é uma segunda-feira de 1º mês | A lista "HOJE: ligar e propor data" recomendaria deals com chance histórica zero no mês |
| 6 | Ordenar por valor esperado em 28 dias, aprendido das mesmas datas dos trimestres anteriores, captura 1,26× a melhor regra pública (IC 95%: 1,11 a 1,47) e 1,36× a do v1 | Existe um score de verdade, e ele cumpre o requisito "não é só ordenar por valor" |
| 7 | `submissions/` está no `.gitignore` do repositório oficial | O `git add` da Tarefa 0 não adiciona nada; precisa de `-f` |
| 8 | O piloto "metade da região, +10%" detecta no mínimo +104% com 5 vendedores por braço | O desenho do experimento precisa mudar |

Sigo agora com: scripts de conferência em `analise/`, plano v2, documento de revisão, errata no guia e o kit de registro de processo e uso de IA.
> ferramenta: `Write` — workspace/g4-challenge-003/analise/eda-04-auditoria-plano-v1.p  
> ferramenta: `Write` — workspace/g4-challenge-003/analise/eda-05-relogio-do-trimestre  
> ferramenta: `Bash` — Run the two consolidated verification scripts and save their outputs next to them  
> ferramenta: `Bash` — Prototype the exact scoring specification of the revised plan to pin the golden test values  

**Claude (claude-opus-5)**

O protótipo do motor v2 roda e fecha os números. Vou gravar os entregáveis.
> ferramenta: `Write` — workspace/g4-challenge-003/analise/eda-06-prototipo-motor-v2.p  
> ferramenta: `Bash` — Run the engine prototype and save its output  

**Claude (claude-opus-5)**

Números fixados. Agora os documentos.
> ferramenta: `Write` — workspace/g4-challenge-003/03-revisao-tecnica.md  
> ferramenta: `Write` — workspace/g4-challenge-003/02-plano-implementacao.md  

**Claude (claude-opus-5)**

Preciso arquivar o v1 — ele não estava no Git, então vou regravá-lo a partir do que li.
> ferramenta: `Bash` — Create the archive folder for the previous plan version  
> ferramenta: `Write` — ~/AIS-OS/archives/g4-challenge-003/02-plano-implementacao-v1.md  

**Claude (claude-opus-5)**

Agora o kit de registro de IA, que é o que torna o processo auditável e reutilizável.
> ferramenta: `Write` — ~/AIS-OS/.claude/skills/registro-ia/SKILL.md  
> ferramenta: `Write` — ~/AIS-OS/.claude/skills/registro-ia/template/registrar.py  
> ferramenta: `Write` — ~/AIS-OS/.claude/skills/registro-ia/template/REGISTRO.md  
> ferramenta: `Write` — ~/AIS-OS/.claude/skills/registro-ia/template/MODELOS.md  
> ferramenta: `Write` — ~/AIS-OS/.claude/skills/registro-ia/template/onde-a-ia-errou.md  
> ferramenta: `Write` — ~/AIS-OS/.claude/skills/registro-ia/template/o-que-eu-acrescentei.md  
> ferramenta: `Write` — ~/AIS-OS/.claude/skills/registro-ia/template/verificacao/LEIA.md  
> ferramenta: `Write` — ~/AIS-OS/.claude/skills/registro-ia/template/diario.md  
> ferramenta: `Write` — ~/AIS-OS/.claude/skills/registro-ia/reference/criterios-avaliacao.md  

**Claude (claude-opus-5)**

Vou testar o kit de ponta a ponta antes de considerá-lo entregue.
> ferramenta: `Bash` — Test the AI-registry kit end to end on the system Python  

**Claude (claude-opus-5)**

O kit funciona no Python 3.9 do sistema. Dois ajustes: separar o título do erro do que a IA propôs, e detectar sessão abandonada no meio (não só a última).
> ferramenta: `Edit` — ~/AIS-OS/.claude/skills/registro-ia/template/registrar.py  
> ferramenta: `Edit` — ~/AIS-OS/.claude/skills/registro-ia/template/registrar.py  
> ferramenta: `Edit` — ~/AIS-OS/.claude/skills/registro-ia/template/registrar.py  
> ferramenta: `Edit` — ~/AIS-OS/.claude/skills/registro-ia/template/registrar.py  
> ferramenta: `Edit` — ~/AIS-OS/.claude/skills/registro-ia/template/registrar.py  
> ferramenta: `Bash` — Verify the two fixes to the registry script  
> ferramenta: `Bash` — Rerun the fix verification with proper shell quoting  

**Claude (claude-opus-5)**

Kit validado. Agora a errata no guia e a atualização do índice do projeto.
> ferramenta: `Edit` — workspace/g4-challenge-003/01-guia-fde.md  
> ferramenta: `Edit` — workspace/g4-challenge-003/01-guia-fde.md  
> ferramenta: `Write` — workspace/g4-challenge-003/README.md  
> ferramenta: `Bash` — Check the format of the decisions log before appending  
> ferramenta: `Bash` — Append the new decision to the decisions log  
> ferramenta: `Write` — ~/.claude/projects/-Users-diegorodrigues-AIS-OS/memory/g4-ai-master-challenge.md  
> ferramenta: `Write` — ~/.claude/projects/-Users-diegorodrigues-AIS-OS/memory/registro-ia-kit.md  
> ferramenta: `Edit` — ~/.claude/projects/-Users-diegorodrigues-AIS-OS/memory/MEMORY.md  
> ferramenta: `Edit` — ~/AIS-OS/CLAUDE.md  
> ferramenta: `Bash` — Verify the written files compile, links resolve and list what changed  
> ferramenta: `Bash` — Clean compile caches and confirm the task count  

**Claude (claude-opus-5)**

Pronto. Revisei o plano, achei o que estava errado, achei um sinal que ninguém usou, reescrevi o plano e empacotei o registro de IA como skill.

## O que mudou de fato

**O plano v1 ia falhar na execução.** Seis dos números pinados nos testes não fecham com o dataset: são 30 vendedores com deal e 27 com deal aberto, não 35; os vencidos são 1.301, não 1.291, porque o EDA mediu idade contra 31/12 e o produto usa 01/01; a fila que seria a tela principal tem mediana zero por vendedor; e o `git add` da Tarefa 0 não adicionava nada, porque `submissions/` está no `.gitignore` do repositório oficial.

**A tabela de probabilidade tinha o viés que o process log dizia ter corrigido.** A fórmula do v1 contava só deals fechados no denominador, então a chance de decidir subia para 100% aos 120 dias. Com os deals ainda abertos em risco e a janela censurada, o real é 15,6%. Esse número aparece no cartão "por quê" de cada deal — era o número mais visível da submissão.

**Faltava metade da regra, e o guia já usava a metade que faltava sem dizer.** Os fechamentos param no fim do trimestre seguinte ao engajamento (6.710 de 6.711). Os "US$ 3,66 mi vencidos, 74%" que o guia cita só saem com essa regra aplicada, que o texto não descrevia. São 173 deals e US$ 429 mil que o motor do v1 mandaria o vendedor trabalhar.

**A métrica de sucesso media mistura de preço.** O top 5 por preço de tabela acerta 36,8% contra 35,7% do sorteio, e seu preço médio é 2,87× a média dos abertos. "3× o aleatório" era a razão entre preços disfarçada de resultado — e era a frase do CFO.

## O achado novo

Nenhum deal com mais de 30 dias fechou no primeiro mês de um trimestre: zero em 3.618 observações. O PR público #240 viu o efeito de calendário e descartou como artefato, e está certo para a pergunta que ele fez — "quem ganha" não se responde com a data do fechamento, que só se conhece depois. Mas a altura do trimestre em que hoje cai é conhecida hoje, e ela prevê **quando decide**, que é exatamente o que a lista de segunda-feira precisa saber.

Ordenar por valor esperado nessa leitura captura 1,30× o que a melhor regra pública captura (IC 95% de 1,13 a 1,52, bootstrap por vendedor) e acerta 22,7% contra 15,4%. O limiar não é escrito à mão: sai da tabela aprendida das mesmas datas dos trimestres anteriores, e o protótipo prova isso mostrando duas respostas diferentes para a mesma regra em duas alturas do trimestre.

Isso também muda o argumento do produto. Em 01/01/2018 — primeira segunda-feira de um trimestre — sobram 7 deals com chance medida de decidir, e os 500 em Prospecting valem US$ 1,07 mi, 4,5× todo o pipeline vivo. A recomendação honesta para a semana é começá-los, não resgatar os velhos.

## Entregas

| Arquivo | O quê |
|---|---|
| [03-revisao-tecnica.md](workspace/g4-challenge-003/03-revisao-tecnica.md) | a revisão: cada achado com o script que o conferiu, e onde a correção entrou |
| [02-plano-implementacao.md](workspace/g4-challenge-003/02-plano-implementacao.md) | plano v2, 14 tarefas, valores de ouro vindos do protótipo |
| [analise/eda-04](workspace/g4-challenge-003/analise/eda-04-auditoria-plano-v1.py), [eda-05](workspace/g4-challenge-003/analise/eda-05-relogio-do-trimestre.py), [eda-06](workspace/g4-challenge-003/analise/eda-06-prototipo-motor-v2.py) | auditoria, o achado com IC, e o protótipo do motor rodando |
| [01-guia-fde.md](workspace/g4-challenge-003/01-guia-fde.md) | errata de 12 pontos no fim, com o porquê de cada um |
| [.claude/skills/registro-ia/](.claude/skills/registro-ia/) | o kit de compliance |

O plano v1 está em [archives/g4-challenge-003/](archives/g4-challenge-003/02-plano-implementacao-v1.md) — o process log da submissão vai citar o que mudou.

## O kit `/registro-ia`

É a parte de compliance: `registrar.py` (só stdlib, testado no Python 3.9 do macOS) mais `diario.md`, `REGISTRO.md`, `MODELOS.md` com coluna de dado sensível, `onde-a-ia-errou.md`, `o-que-eu-acrescentei.md` e o protocolo de verificação independente. Três regras ficam impostas pelo desenho: o registro é gravado na hora, o modelo é citado com a versão exata, e **erro da IA sem o mecanismo que o pegou o comando recusa gravar** — porque "a IA errou e eu corrigi" é afirmação, não evidência. `--conferir` lista pendências e sai com código 1 quando o registro está incompleto. Testei o ciclo inteiro, incluindo a recusa e a detecção de sessão abandonada no meio do diário.

Registrei a decisão em `decisions/log.md` e atualizei a memória do projeto.

Duas coisas para você decidir antes da Tarefa 0: o relógio do trimestre pode ser artefato do gerador do dataset — eu declararia isso em `limitacoes.md` e deixaria o `drift.py` como resposta, mas é um risco real de um avaliador chamar de overfitting; e adotar a regra do trimestre significa creditar o PR #242 em uma linha no README, o que eu acho que fortalece e você pode achar que enfraquece.

---

### Diego · 11/11 08:33

[comando: /model]
            
            claude-opus-5

---

### Diego · 11/11 09:51

<ide_opened_file>The user opened the file workspace/g4-challenge-003/02-plano-implementacao.md in the IDE. This may or may not be related to the current task.</ide_opened_file>

---

### Diego · 11/11 09:51

Revisei todo o material, ficou excelente. 
Agora, antes de iniciar, eu tive uma ideia: 

Adicione ao seu plano de implementação uma etapa de discovery que envolve entrevistas com 4 personas sintéticas da área de vendas da empresa G4 que foram criadas a partir de um estudo de perfis e arquétipos com toda a cultura de vendas da empresa. 
Foi criado um agente no copilot com todo o aprendizado da base de dados do Kaggle para ser entrevistado. Adicione a etapa de perguntas, com as perguntas que eu devo fazer a cada uma das 4 personas (vc tem essas pessoas descritas no documento em anexo. 
Implemente de maneira que isso depois entre na documentação final e faça parte do processo de FDE e gere mais valor ao case.

**Claude (claude-opus-5)**

Boa ideia, e ela cai exatamente em cima do ponto mais frágil da submissão. Mas tem uma armadilha no enunciado que precisa ser resolvida antes de a primeira pergunta ser feita, então deixo isso explícito no protocolo.
> ferramenta: `Write` — workspace/g4-challenge-003/04-discovery-personas.md  

**Claude (claude-opus-5)**

Agora a etapa entra no plano, como tarefa própria, e os documentos finais passam a consumi-la.
> ferramenta: `Edit` — workspace/g4-challenge-003/02-plano-implementacao.md  
> ferramenta: `Edit` — workspace/g4-challenge-003/02-plano-implementacao.md  
> ferramenta: `Edit` — workspace/g4-challenge-003/02-plano-implementacao.md  
> ferramenta: `Edit` — workspace/g4-challenge-003/02-plano-implementacao.md  
> ferramenta: `Edit` — workspace/g4-challenge-003/02-plano-implementacao.md  
> ferramenta: `Edit` — workspace/g4-challenge-003/02-plano-implementacao.md  
> ferramenta: `Edit` — workspace/g4-challenge-003/02-plano-implementacao.md  
> ferramenta: `Edit` — workspace/g4-challenge-003/02-plano-implementacao.md  
> ferramenta: `Edit` — ~/AIS-OS/.claude/skills/registro-ia/template/MODELOS.md  
> ferramenta: `Edit` — workspace/g4-challenge-003/README.md  
> ferramenta: `Edit` — workspace/g4-challenge-003/README.md  
> ferramenta: `Bash` — Record the discovery decision in the log  
> ferramenta: `Edit` — ~/.claude/projects/-Users-diegorodrigues-AIS-OS/memory/g4-ai-master-challenge.md  
> ferramenta: `Bash` — Verify the plan structure, the question counts and that links resolve  

**Claude (claude-opus-5)**

Etapa adicionada. O roteiro está em [04-discovery-personas.md](workspace/g4-challenge-003/04-discovery-personas.md), e virou a **Tarefa 0B** do plano — numerada assim de propósito, para não renumerar as tarefas que a revisão técnica já referencia.

## A armadilha que eu resolvi antes de escrever a primeira pergunta

O agente foi montado com o aprendizado da base do Kaggle. Isso contamina a persona como informante: ela vai te devolver o que o dado diz vestido de experiência vivida, e você vai achar que encontrou confirmação independente. É validação circular com cara de entrevista — e um avaliador que perceba isso derruba a etapa inteira junto com a credibilidade do resto.

A correção é separar em dois modos, **em conversas distintas**. Modo A é a persona como vendedor: processo, incentivo, reação, adoção — isso entra no produto como premissa. Modo B é o agente respondendo sobre a base, e serve **só para calibração**: medir se ele inventa. Nada do Modo B entra no produto.

As perguntas de calibração têm gabarito que eu já calculei: mediana de 2 negócios vivos numa carteira de ~70 abertos, nenhum produto ou setor separa ganho de perda, ciclo máximo de 138 dias, mediana de 79 abertos por vendedor. Se a persona responder com confiança e errar, **esse é o melhor item do process log** — deixa de ser "a IA errou uma conta" e vira "usei informante sintético e medi a confiabilidade dele antes de acreditar". É alfabetização em IA aplicada, que é literalmente o que a vaga descreve.

## As quatro perguntas que decidem o produto

De 42 perguntas no roteiro, quatro podem matar a ferramenta e nenhuma delas tem resposta no dado:

- **Caçador B6** — a ferramenta diz "não há nada seu para fechar esta semana, abra os 55 parados". Primeira reação. Se um vendedor de meta rejeitar isso, o estado vazio honesto é um problema de adoção, não uma virtude.
- **Caçador B7** — marcar "não está vivo" faria o negócio sumir do número que o seu gerente apresenta. Você marcaria? Se a resposta for não, a fila de encerrar precisa de meta e patrocínio, não de botão.
- **Embaixador B5** — se o gerente passar a ver quantos cada um marcou como feito, o que acontece com esse número na semana seguinte? Se todo mundo marcar tudo, a métrica de adoção nasce morta e o override vira a única medida difícil de falsear.
- **Líder L2** — se o seu pipeline encolher 70% porque alguém limpou o que não fecha, o que acontece com você? Essa é do outro lado da mesa, e é por isso que acrescentei uma quinta persona.

## Duas coisas que eu acrescentei sem você pedir

**A quinta persona, o líder.** O sponsor map é um diferencial declarado da submissão, e a anti-meta — o gestor usar a tela para cobrar indivíduo — só pode ser confirmada ou derrubada por ele. Perguntar isso ao vendedor é perguntar ao lado errado da mesa. São seis perguntas, dez minutos, e a resposta de L4 decide uma coisa concreta: se a Tela 2 mostra indivíduo por padrão ou só agregado.

**O pré-registro commitado antes da primeira pergunta.** Os avaliadores do repositório pediram em público para ver quais hipóteses você formulou *antes* de pedir à IA. Um commit datado é a única forma de provar isso, e sem ele toda resposta vira "eu já sabia".

## Por que isso fortalece o case

O relógio do trimestre é a tese do produto e o maior risco declarado dela é ser artefato do gerador de dados. Uma operação de meta mensal, com ritual de fechamento e uniforme preto no último dia do mês, é exatamente o mecanismo que explicaria o padrão. Se as personas descreverem essa concentração, o achado ganha causa. **E se descreverem fechamento uniforme, eu declaro isso e o case fica mais forte, não mais fraco** — porque mostra um teste que poderia ter dado errado e não foi escondido.

Também ajustei o que consome a etapa: a Tarefa 12 não reescreve mais o `discovery.md`, o operating map e o sponsor map passam a citar as palavras das personas, a onda 1 do rollout passa a ser por perfil em vez de por região, e as `limitacoes.md` ganham o parágrafo de que o discovery foi ensaiado, não vivido — nunca escrever "entrevistei vendedores". O kit `/registro-ia` ganhou uma seção sobre informantes sintéticos, então a regra vale para qualquer entregável seu daqui em diante, não só para este.

Registrei a decisão em `decisions/log.md` e atualizei a memória.

Uma coisa de calendário: hoje é 11/11 e o PR era para sair hoje. A etapa custa 75 minutos, ou 40 na versão curta da seção 9, que cobre as dez perguntas que decidem produto. Eu rodaria a versão curta antes do build e deixaria as entrevistas completas para depois do PR, como atualização na mesma branch — o repositório aceita push na mesma branch. Se você preferir o roteiro completo agora, o corte natural é a Tarefa 9 virar só template.

---

### Diego · 11/11 10:04

[comando: /model]
            
            claude-sonnet-4-6

---

### Diego · 11/11 10:05

<ide_opened_file>The user opened the file workspace/documentacao-stepbystep-ongoing.md in the IDE. This may or may not be related to the current task.</ide_opened_file>

---

### Diego · 11/11 10:05

Agora escreva aqui no chat: 

1 - o passo a passo que eu devo seguir para a implementação e criação do que está no plano de implementação. 
2 - Qual modelo eu posso utilizar aqui para cada etapa, evitando assim um modelo caro para uma ação simples. 
3 - O resultado que eu devo esperar de cada etapa antes de avançar para a próxima.

---

### Diego · 11/11 10:07

This session is being continued from a previous conversation that ran out of context. The summary below covers the earlier portion of the conversation.


Summary:
1. **Primary Request and Intent:**

   **Request 1 (opening):** Revise `workspace/g4-challenge-003/02-plano-implementacao.md` following "as mais completas e avançadas técnicas de: Arquitetura de dados, Software engineer, Business model". Explicitly: "Saia dos vieses comuns, não quero que siga algum mental model comum. Tudo dentro do melhor padrão de construção de soluções possível." And: "Ao final estruture e melhore esse guia, trazendo um repositório ou modelo ou skill que documente todo o processo e uso de modelos e e IA para estar compliance com as solicitação. Seja extremamente minucioso na entrega e revisão."

   **Request 2 (after approving the result):** "Revisei todo o material, ficou excelente." Then: add to the implementation plan a discovery stage involving interviews with **4 synthetic personas** from G4's sales area, created from a study of profiles and archetypes with the company's whole sales culture (supplied as an attached Perplexity PDF). An agent was created in Copilot with all the learning from the Kaggle database to be interviewed. Add the question stage, **with the questions he should ask each of the 4 personas**. Implement it so that it later enters the final documentation, becomes part of the FDE process, and generates more value for the case.

   Context: this is the G4 Educação AI Master job challenge 003 (Lead Scorer). Target: PR `[Submission] Diego Rodrigues — Challenge 003` on 11/11/2026, aiming to place first.

2. **Key Technical Concepts:**
   - Point-in-time / as-of backtesting; temporal leakage prevention via a single `recortar(dados, hoje)` entry point used identically in production and evaluation
   - Survivorship bias and censored life tables (deals still open must be in the denominator)
   - The "quarter clock": decision timing depends on deal age **and** position within the quarter; learned from analogous dates of prior quarters, not hand-written thresholds
   - Quarter deadline rule: closings stop at end of the quarter following engagement (6710/6711)
   - Bootstrap confidence intervals clustered **by seller** (not by deal) — seller is the unit of independence
   - Three honest metrics replacing "3× random": ratio vs best honest alternative, hit rate (immune to price mixing), fraction of oracle ceiling
   - Statistical power: CV, ICC (0.031), MDE; within-seller deal-level randomization instead of seller-level
   - Permutation tests, stratified by month-of-quarter
   - TDD with golden values generated by a spec prototype
   - Deterministic builds with SHA-256 hash of JSON (excluding `gerado_em`)
   - Drift detection (`drift.py`) for learned parameters
   - LLM with structured output + deterministic validator + template fallback; cost logging
   - Mom Test interviewing; pre-registration of hypotheses; synthetic-informant calibration against known ground truth
   - Superpowers skills: `brainstorming`, `writing-plans`, `subagent-driven-development`
   - Python 3.9-compatible stdlib-only tooling (the evaluator may have system Python)

3. **Files and Code Sections:**

   - **`workspace/g4-challenge-003/02-plano-implementacao.md`** (681 lines, rewritten as v2, then amended)
     - The central deliverable. Now 15 task headings: Tarefa 0, **0B**, 1–13.
     - Global Constraints include: `git add -f` (because `submissions/` is in upstream `.gitignore`); no hand-written phase thresholds; `config.json` holds only operational choices (`horizonte_dias: 28`, `foco_por_vendedor: 5`, `p_decide_min: 0.05`, `bordas_faixa: [15,30,45,60,75,90,105,120]`, `n_min_faixa: 30`, `tolerancia_prazo_trimestre: 0.001`, `min_fechamentos_para_prazo: 500`, `semente: 7`, `hoje: null`); `hoje` is a mandatory parameter; every number from `numeros.py` with IC for ratios.
     - Review Focus (5 items): future-closing deals; thin age bands; sellers with zero deals; unknown products; briefing hallucination + POST /acao validation.
     - Golden test values pinned from the prototype, e.g.:
       ```python
       def test_filas_em_2018_01_01(s):
           assert s.fila.value_counts().to_dict() == {
               "encerrar": 1474, "iniciar": 500, "preparar": 108, "fechar": 7}
           assert len(s) == 2089 and s.vendedor.nunique() == 27
       def test_valor_esperado_total(s):
           assert round(s.ve_trimestre.sum(), 2) == 65482.05
           assert round(s.ve_28.sum(), 2) == 2699.05
       def test_relogio_bate_a_melhor_alternativa_honesta(dados, config):
           razao, lo, hi = razao_com_ic(backtest(dados, config, detalhado=True), "relogio", "preco_prazo")
           assert round(razao, 2) == 1.30 and lo > 1.0
           assert (round(lo, 2), round(hi, 2)) == (1.13, 1.52)
       ```
     - **Tarefa 0B (new, turn 2):** "Discovery ensaiado com personas sintéticas", 75 min (or 40 short). Explicitly numbered 0B "para não renumerar as tarefas já referenciadas em Review Focus e na revisão técnica". 8 steps: pre-registration + commit; register the persona agent in MODELOS.md; 4 Mode-A interviews in separate conversations; 5th leader interview; Mode-B calibration in a separate conversation; write `docs/discovery.md`; apply what changed (opening pendings in Tasks 9, 11, 12); commit. Includes the `registrar.py --erro` invocation for caught confabulations.
     - **Tarefa 12** retitled "Operating map, sponsor map, design, deploy e experimento" — no longer creates `discovery.md`, consumes it; sponsor/operating map use persona wording; deploy wave 1 by profile not region.
     - **Tarefa 13** Step 4 adds "o discovery foi ensaiado com personas sintéticas, não vivido — nunca escrever 'entrevistei vendedores'"; Step 5 adds the persona-calibration item as a distinct category of AI error.

   - **`workspace/g4-challenge-003/04-discovery-personas.md`** (233 lines, NEW in turn 2)
     - The main turn-2 deliverable: full interview protocol and paste-ready questions.
     - §1 the contamination trap and the Modo A / Modo B table; §2 eight conduct rules plus the framing prompt to paste (includes giving the persona permission to contradict); §3 pre-registration table P1–P12; §4–§7 the four personas (10, 9, 9, 8 questions each, three columns: Pergunta | Premissa | O que muda); §8 Persona 5 "Líder de tropa de elite" (6 questions, recommended addition); §9 short 40-min version with 10 starred questions; §10 outputs + synthesis table; §11 six ways it generates value; §12 risks and treatment.
     - Calibration ground truths embedded: median **2** live deals in a ~70-deal book; **no** product/sector separates win from loss; max cycle **138** days; median **79** open deals per seller.
     - Killer questions include Caçador B7 ("Se marcar 'não está vivo' fizesse o negócio sumir do seu pipeline **e do número que o seu gerente apresenta**, você marcaria?") and Embaixador B5 ("Se o gerente passar a ver quantos negócios cada um marcou como feito, o que acontece com esse número na semana seguinte?") and Líder L2 ("Se o seu pipeline aberto encolhesse 70% numa semana porque alguém limpou o que não fecha, o que acontece com você?").

   - **`workspace/g4-challenge-003/03-revisao-tecnica.md`** (243 lines, NEW turn 1)
     - 11 sections: verdict; execution-breaking errors (table of 9); the survivorship bias table; the missing quarter rule; the wrong success metric; the quarter clock finding with IC; business model (pilot power, ROI, the 500 Prospecting deals); architecture changes (7.1–7.10); what v1 got right; v2 risks; a checklist of every claim verified with its script.

   - **`analise/eda-04-auditoria-plano-v1.py`** + `.saida.txt` — audits each pinned v1 number (sections A–G).
   - **`analise/eda-05-relogio-do-trimestre.py`** + `.saida.txt` — the quarter clock, backtest with IC, permutation stratified by month-of-quarter (sections A–L).
   - **`analise/eda-06-prototipo-motor-v2.py`** + `.saida.txt` — the v2 engine prototype; defines `carregar`, `recortar`, `aprender`, `pontuar`, `replay`, `ic`; produces all golden values. Key signature shapes:
     ```python
     def recortar(full, ref):  # apaga o futuro
     def aprender(con, ref) -> dict(ciclo_max, n_fechamentos, apos_prazo, usa_prazo_tri, analogas, tabela, carga, razao_fechado_tabela, semana_tri)
     def pontuar(con, ap, ref) -> DataFrame  # estado, fila, chave, posicao, em_foco, indice
     ```

   - **`archives/g4-challenge-003/02-plano-implementacao-v1.md`** — v1 reconstructed verbatim (it was untracked in git and I had overwritten it).

   - **`.claude/skills/registro-ia/`** (NEW turn 1, amended turn 2) — the compliance kit:
     - `SKILL.md` — usage, the 6 output files table, 5 rules, sensitive-data rule.
     - `reference/criterios-avaliacao.md` — maps each kit file to what evaluators ask; notes "O uso de IA pesa 30% da nota"; notes `submissions/` gitignore finding.
     - `template/registrar.py` — stdlib-only, Python 3.9 tested. Commands: `--inicio`, `--pedi/--veio/--mudei`, `--erro [--propos] --pego-por --teste --ficou`, `--nota`, `--fim`, `--conferir`. Refuses to record an AI error without a catching mechanism. `sessoes_abertas()` returns a list so abandoned mid-diary sessions are flagged.
     - `template/MODELOS.md` — amended turn 2 with an "Informantes sintéticos" section: table (Agente | Papel | Construído a partir de | É fonte de fato? | Como a confiabilidade foi medida) and 4 rules (separate modes; pre-register; no answer becomes fact; label honestly).
     - `template/{diario.md, REGISTRO.md, onde-a-ia-errou.md, o-que-eu-acrescentei.md, verificacao/LEIA.md}`.

   - **`01-guia-fde.md`** — header warning + 12-row errata table appended before "Fontes usadas neste guia".
   - **`README.md`** (project folder) — rewritten; now lists 04-discovery-personas.md and Tarefa 0B in status.
   - **`decisions/log.md`** — two entries appended (the v2 technical decisions; the discovery decision with guardrails).
   - **Memory:** `g4-ai-master-challenge.md` rewritten + discovery paragraph added; `registro-ia-kit.md` created; `MEMORY.md` index updated; `CLAUDE.md` gained `/registro-ia`.

4. **Errors and fixes:**
   - `gh api 'repos/.../git/trees/main?recursive=1'` failed in zsh with "no matches found" (glob expansion of `?`) — fixed by running from the scratchpad directory with the URL quoted.
   - `v8.py`: `pd.cut(R2.sem, [0,4,9,14], ...)` raised "Input array must be 1 dimensional" because `.sem` resolved to a DataFrame method, not the column — fixed with `pd.cut(R2["sem"], ...)`.
   - Kit test: `R="/usr/bin/python3 process-log/registrar.py"; $R --conferir` failed in zsh ("no such file or directory") because zsh does not word-split unquoted variables — fixed by defining a shell function `R() { /usr/bin/python3 process-log/registrar.py "$@"; }`.
   - After end-to-end testing the kit, two design defects found and fixed: (a) `--erro` duplicated the title into "O que a IA propôs" — added `--propos`; (b) only the most recent unclosed session was detected — replaced `sessao_aberta()` with `sessoes_abertas()` returning a list, and `--conferir` now reports each.
   - I overwrote plan v1 before archiving it, and it was untracked in git (git status showed `?? workspace/`). Recovered by reconstructing it verbatim from my earlier full read into `archives/g4-challenge-003/`.
   - `py_compile` left `__pycache__` directories; cleaned them.
   - No user corrections to my work were received; the user's only feedback was "Revisei todo o material, ficou excelente."

5. **Problem Solving:**
   - Converted a desk review into an empirical audit: every claim in the v1 plan and the FDE guide was recomputed against the dataset rather than reasoned about.
   - Found that the v1 plan's own tests would fail on first run (6 pinned numbers wrong), that its probability table carried the exact survivorship bias its process log claimed to have fixed, and that its headline metric measured price mixing rather than prediction.
   - Discovered a genuinely new signal (the quarter clock) by asking a different question than the public PR #240 asked — "when does it decide" (knowable today) vs "who wins" (only knowable after).
   - Resolved the task-numbering risk by inserting the discovery as **Tarefa 0B** rather than renumbering 13 tasks referenced elsewhere.
   - Resolved the circular-validation risk of a persona agent built on the same dataset via the Modo A / Modo B split plus calibration questions with script-known answers.

6. **All user messages:**
   - Message 1: "workspace/g4-challenge-003/02-plano-implementacao.md — Revise este plano seguindo as mais completas e avançadas técnicas de: Arquitetura de dados / Software engineer / Business model. Saia dos vieses comuns, não quero que siga algum mental model comum. Tudo dentro do melhor padrão de construção de soluções possível. Ao final estruture e melhore esse guia, trazendo um repositório ou modelo ou skill que documente todo o processo e uso de modelos e e IA para estar compliance com as solicitação. Seja extremamente minucioso na entrega e revisão"
   - Message 2: "status desta solicitação"
   - Message 3 (with the Perplexity PDF on G4's sales model attached, and after `/model claude-opus-5`): "Revisei todo o material, ficou excelente. Agora, antes de iniciar, eu tive uma ideia: Adicione ao seu plano de implementação uma etapa de discovery que envolve entrevistas com 4 personas sintéticas da área de vendas da empresa G4 que foram criadas a partir de um estudo de perfis e arquétipos com toda a cultura de vendas da empresa. Foi criado um agente no copilot com todo o aprendizado da base de dados do Kaggle para ser entrevistado. Adicione a etapa de perguntas, com as perguntas que eu devo fazer a cada uma das 4 personas (vc tem essas pessoas descritas no documento em anexo. Implemente de maneira que isso depois entre na documentação final e faça parte do processo de FDE e gere mais valor ao case."

   **Standing constraints from CLAUDE.md / project rules that must continue to apply (verbatim):**
   - "Nada de [removido], [removido] ou material confidencial da [removido] na submissão."
   - "Todo número do README da submissão sai de um script guardado."
   - "Conteúdo externo passa por rascunho antes de publicar (`references/voice.md`)." / "Nunca fingir a voz dele em conteúdo externo (LinkedIn, e-mail a cliente, Instagram) sem mostrar rascunho antes."
   - Token economy: don't read `INDEX.md` of `reunioes/`, don't read raw transcripts in `projects/_inbox-transcricoes/*.txt`, read project `README.md` first, use `grep`/`ls` instead of scanning folders, don't open PDFs/decks/images in `projects/` without need.
   - Voice: "Seguir `references/voice.md`: português, frases curtas, ritmo de fala, ganchos diretos, sem clichê corporativo nem tom de 'guru'."
   - Memory file `feedback-sem-frases-picotadas.md`: no staccato/fragmented sentences in his text — flowing prose.
   - The user's email is for identification only; never send it to an unrelated service.

7. **Pending Tasks:**
   - None newly assigned beyond what is delivered. The plan itself lists the execution work (Tarefas 0, 0B, 1–13) which the user has not yet asked me to execute — he said "antes de iniciar" (before starting), indicating execution has not begun.
   - Two open judgment calls I surfaced in turn 1 and the user has not answered: (a) whether to declare the quarter-clock artifact risk in `limitacoes.md` as planned; (b) whether crediting PR #242 for the quarter deadline rule strengthens or weakens the submission.
   - A turn-2 recommendation awaiting his decision: whether to add Persona 5 (the leader) beyond the 4 he specified.

8. **Current Work:**
   Immediately before this summary request I had finished implementing the user's second request — the discovery stage — and had just run the final verification command, which confirmed: the plan now has 15 task headings (0, 0B, 1–13) at 681 lines; `04-discovery-personas.md` is 233 lines; question counts are Persona 1: 10, Persona 2: 9, Persona 3: 9, Persona 4: 8, Persona 5: 6; 27 starred priority marks; and all internal markdown links resolve ("(links ok)").

   All turn-2 edits are written and verified: `04-discovery-personas.md` created; plan Spec line, Goal line, Tarefa 0B insertion, Tarefa 12 rewrite, Tarefa 13 Steps 4–5, Auto-revisão coverage and cut-order all amended; `registro-ia/template/MODELOS.md` gained the "Informantes sintéticos" section; project `README.md` gained the new file row and two status lines; `decisions/log.md` gained the discovery decision; memory `g4-ai-master-challenge.md` gained the discovery paragraph.

   I had **not yet written my prose reply to the user** explaining the turn-2 work.

9. **Optional Next Step:**
   Write the reply to the user for turn 2: explain the discovery stage as delivered, lead with the methodological trap I resolved (the Copilot agent was built on the same Kaggle dataset, so Modo A / Modo B separation plus calibration questions prevent circular validation), point to `04-discovery-personas.md` and Tarefa 0B, state the time cost (75 min, or 40 in the short version) against the 11/11 PR deadline, and surface the two judgment calls for his decision: adding Persona 5 (the leader) beyond the 4 he specified — justified because "o sponsor map é um dos diferenciais declarados da submissão, e ele tem um patrocinador e uma anti-meta que **só o gestor pode confirmar ou derrubar**: a premissa P12 ... e a P8" — and keeping the honest label "discovery ensaiado com personas sintéticas", never "entrevistei vendedores". No further file changes should be made without his confirmation, since he said "antes de iniciar" and has not yet asked me to execute the plan.

If you need specific details from before compaction (like exact code snippets, error messages, or content you generated), read the full transcript at: ~/.claude/projects/-Users-diegorodrigues-AIS-OS/2cb9516c-4406-49e6-bfcf-c3bec086338b.jsonl
Continue the conversation from where it left off without asking the user any further questions. Resume directly — do not acknowledge the summary, do not recap what was happening, do not preface with "I'll continue" or similar. Pick up the last task as if the break never happened.

The messages after this summary are the most recent messages from before compaction, kept verbatim. The summary was written without seeing them, so something it says has not happened yet may already have happened in them.
> ferramenta: `Read` — workspace/g4-challenge-003/02-plano-implementacao.md  

**Claude (claude-sonnet-4-6)**

---

## Guia de execução: Tarefa por tarefa

Pré-condição: você está no fork `~/Documents/ai-master-challenge`, branch `submission/diego-rodrigues`, pasta `submissions/diego-rodrigues/`.

---

### Tarefa 0 · Estrutura e registro de IA
**Modelo:** Haiku 5.5 — são só comandos bash, cópias e boilerplate.\
**O que fazer:** fork, branch, `mkdir`, venv, `pip install`, `shasum`, copiar o kit `/registro-ia` para `process-log/`.\
**Resultado esperado antes de avançar:**
- `git status` mostra só arquivos dentro de `submissions/diego-rodrigues/`
- `python3 process-log/registrar.py --inicio "Tarefa 0"` não dá erro
- `diario.md` tem uma entrada com data e modelo
- `data/SHA256SUMS` existe e casa com os quatro CSVs

---

### Tarefa 0B · Discovery com as 4 personas
**Modelo:** as entrevistas são você + o agente Copilot, nenhum modelo meu. Para escrever `discovery.md` depois: Sonnet.\
**O que fazer:** pré-registro commitado ANTES de abrir a primeira conversa → quatro entrevistas Modo A em conversas separadas → uma entrevista do líder → Modo B de calibração → síntese → `discovery.md`.\
**Resultado esperado antes de avançar:**
- Commit do pré-registro tem timestamp anterior ao das transcrições (isso é a prova que importa)
- Cada transcrição tem pelo menos uma resposta de discordância ou "não sei" — se nenhuma tem, a entrevista foi cordial demais: repita a última pergunta na forma "me dá a versão em que isso dá errado"
- `discovery.md` tem as 12 premissas P1–P12, cada uma com status e **o teste real que a derrubaria**
- Respostas de calibração incorretas da persona estão em `onde-a-ia-errou.md` via `registrar.py --erro`

> Se o prazo apertar: versão curta de 40 minutos da seção 9 do roteiro. Mas não cortar para zero — P5, P7, P8 e P12 testam premissas que podem matar a adoção do produto.

---

### Tarefa 1 · `motor/carregar.py`
**Modelo:** Sonnet 4.6 (você já está aqui) ou Sonnet 5.5.\
**O que fazer:** escrever os 5 testes primeiro → rodar para ver falhar → implementar `carregar` e `recortar` → rodar para ver passar.\
**Resultado esperado antes de avançar:**
```
5 passed
```
Especialmente: `test_recortar_nao_vaza_futuro` passa — é a garantia de que o backtest não pode divergir do produto. Se falhar, não avançar.

---

### Tarefa 2 · `motor/janela.py`
**Modelo:** Sonnet 4.6 ou Sonnet 5.5.\
**O que fazer:** 5 testes → falhar → implementar → passar. A parte que engana: fim do trimestre seguinte ao engajamento é `QuarterBegin(2) − 1 dia`, não 90 dias fixos.\
**Resultado esperado antes de avançar:**
```
5 passed
```
Especialmente: `j.usa_prazo_trimestre is True` e `j.ciclo_max == 138` na data de referência. Se `ciclo_max` vier diferente, conferir se `recortar` está sendo chamado antes de `aprender_janela`.

---

### Tarefa 3 · `motor/aprender.py` (o relógio do trimestre)
**Modelo:** Sonnet 5.5 — essa é a lógica central e a mais sutil. Não usar Haiku aqui.\
**O que fazer:** 7 testes → falhar → implementar. Ponto crítico: cada data análoga alimenta o denominador com os deals **abertos** naquela data, não só os que fecharam — isso é o que corrige o viés de sobrevivência do v1.\
**Resultado esperado antes de avançar:**
```
7 passed
```
Especialmente: `test_nao_ha_vies_de_sobrevivencia` — `p_decide` para faixas 106–138 dias deve ser < 0,05. Se der ~1,0, o denominador está errado (só fechados em vez de todos os abertos).

---

### Tarefa 4 · `motor/pontuar.py`
**Modelo:** Sonnet 5.5.\
**O que fazer:** 9 testes → falhar → implementar. Pontos de atenção: a ordem dentro do vendedor tem 4 chaves (`fila_ordem`, `chave` desc, `dias_restantes` asc, `opportunity_id`); `indice` deve ser monótono.\
**Resultado esperado antes de avançar:**
```
9 passed
```
Especialmente:
- `test_filas_em_2018_01_01`: `{"encerrar": 1474, "iniciar": 500, "preparar": 108, "fechar": 7}`
- `test_valor_esperado_total`: `ve_trimestre.sum() == 65482.05`

Se qualquer um falhar, conferir `eda-06-prototipo-motor-v2.saida.txt` seção C — os valores de ouro vêm de lá.

---

### Tarefa 5 · `motor/explicar.py`
**Modelo:** Sonnet 4.6.\
**O que fazer:** testes do cartão de momento, da frase de estado vazio de Carl Lin e do `nao_sabe` com 4 itens quando conta é nula → implementar.\
**Resultado esperado antes de avançar:**
- `resumo_vendedor("Carl Lin")` não lança exceção e devolve zeros com carga de referência
- Texto do `momento` para deal em `preparar` contém "até o fim" e NÃO contém "quatro semanas seguintes" como promessa

---

### Tarefa 6 · `build.py`
**Modelo:** Sonnet 4.6.\
**O que fazer:** 2 testes → falhar → implementar → passar. `json.dump` com `sort_keys=True` e sem `gerado_em` para garantir hash determinístico.\
**Resultado esperado antes de avançar:**
```
2 passed
```
Especialmente: `test_build_e_deterministico` — rodar duas vezes e obter o mesmo `hash.txt`. Se o hash mudar, tem campo com timestamp ou ordem não determinística.

---

### Tarefa 7 · `avaliacao/` (backtest e IC)
**Modelo:** Sonnet 5.5 — lógica de bootstrap por vendedor e permutação estratificada.\
**O que fazer:** 6 testes → falhar → implementar → passar. A métrica que importa é a taxa de acerto (imune à mistura de preço), não o valor. Bootstrap por vendedor (não por deal).\
**Resultado esperado antes de avançar:**
```
6 passed
```
Especialmente:
- `razao == 1.30`, `lo > 1.0`, `(lo, hi) == (1.13, 1.52)`
- `test_a_vantagem_nao_e_mistura_de_preco`: `acerto_relogio.mean() == 0.227`
- `test_nenhum_vencido_ganhou`: todos zeros

Depois: rodar `python -m avaliacao.numeros > ../docs/numeros-saida.txt` — essa saída alimenta o README e a Tela 3.

---

### Tarefa 8 · `drift.py`
**Modelo:** Haiku 5.5 — lógica simples de comparação.\
**O que fazer:** 3 testes → implementar → passar.\
**Resultado esperado antes de avançar:**
- Contra os CSVs originais: código 0, sem mensagem
- Com deal plantado além de 138 dias: código 1, mensagem em português nomeando `ciclo_max`

---

### Tarefa 9 · `ia/` (briefing + validador)
**Modelo:** Sonnet 5.5 para escrever o código. Para gerar os briefings em produção: `claude-sonnet-5-5` (já hardcoded no plano).\
**O que fazer:** 7 testes do validador → falhar → implementar → passar sem chamar a API → depois rodar `python -m ia.briefing` com a chave real.\
**Resultado esperado antes de avançar:**
```
7 passed
```
Depois da chamada real: anotar quantos briefings vieram de IA vs template e o custo estimado. Dois exemplos recusados pelo validador vão para `onde-a-ia-errou.md`.

> Se o prazo apertar: `--sem-ia` e todos vêm de template — a Tarefa 9 é cortável sem perder o score.

---

### Tarefa 10 · `run.py`
**Modelo:** Sonnet 4.6.\
**O que fazer:** 5 testes (servidor em thread) → implementar → passar → teste manual num clone limpo.\
**Resultado esperado antes de avançar:**
- `python run.py` imprime `hoje = 2018-01-01 (semana 1 do trimestre)` e abre em < 1 minuto
- `POST /acao` com id inexistente responde 400 e não grava nada

---

### Tarefa 11 · `app/` (três telas)
**Modelo:** Sonnet 5.5 — o CSS mobile-first e os estados vazios são trabalhosos.\
**O que fazer:** escrever as três telas → servir local → conferir 6 casos → gerar prints (Playwright, 1366 e 390 px).\
**Resultado esperado antes de avançar:**
- Boris Faz: 1 em `fechar`, 4 em `preparar`
- Carl Lin: estado vazio com carga de referência, sem erro
- Tela 3 mostra 6 linhas de backtest e os IC
- 6 prints salvos em `process-log/screenshots/`

---

### Tarefa 12 · Docs estratégicos (operating map, sponsor map, design, deploy, experimento)
**Modelo:** Sonnet 5.5 — precisa de vocabulário das personas.\
**O que fazer:** escrever os 5 documentos consumindo `discovery.md` → conferir `wc -w docs/*.md` (250–700 palavras cada).\
**Resultado esperado antes de avançar:**
- `sponsor-map.md` cita palavras das transcrições das personas
- `design.md` tem a abordagem rejeitada com o número: "ordenar por preço rende 0,77× o relógio"
- `experimento.md` tem "1.100 deals por braço" e explica por que valor ganho **não pode** ser critério de aceite
- Toda premissa `contrariada` em `discovery.md` tem consequência visível em pelo menos um desses arquivos

---

### Tarefa 13 · Deploy, process log e PR
**Modelo:** Opus 5.5 para o `resumo-executivo.md` e `limitacoes.md` — são os dois documentos que um avaliador lê primeiro. Haiku para o deploy e os comandos git.\
**O que fazer (em ordem):**
1. `vercel --prod` → URL pública com faixa de demo visível
2. Escrever `resumo-executivo.md`, `limitacoes.md` e fechar o README com números de `numeros-saida.txt`
3. Fechar o process log — diário, tabela de modelos, `onde-a-ia-errou.md` com os 6 itens da revisão + os da calibração de personas
4. Verificação independente: subagente em Sonnet (modelo diferente do que implementou) recalcula os números do README do zero — só leitura, gravar em `process-log/verificacao/`
5. `git diff --stat upstream/main` deve listar **só** `submissions/diego-rodrigues/`
6. Push e PR

**Resultado esperado antes de enviar o PR:**
- URL da Vercel abre no celular: três telas, faixa de demo visível, nenhum erro de console
- `git diff --stat upstream/main` lista zero arquivos fora de `submissions/diego-rodrigues/`
- `process-log/verificacao/relatorio.md` diz que nenhum número divergiu e nenhum vazamento temporal foi encontrado
- O PR title é exatamente `[Submission] Diego Rodrigues — Challenge 003`

---

## Resumo de modelos por tipo de trabalho

| Tipo de trabalho | Modelo |
|---|---|
| Bash, cópias, boilerplate, git | `claude-haiku-5-5` |
| Implementar módulos Python, testes, HTML/JS | `claude-sonnet-4-6` ou `claude-sonnet-5-5` |
| Lógica sutil (tabela de destino, backtest, IC, briefing) | `claude-sonnet-5-5` |
| Documentos estratégicos (resumo executivo, limitações) | `claude-opus-5-5` |
| Verificação independente (subagente revisor) | `claude-sonnet-5-5` em contexto limpo |
| Geração de briefings de CRM em produção | `claude-sonnet-5-5` (hardcoded no código) |

**Regra de ouro:** se um teste falhar e o número estiver errado, conferir `analise/eda-06-prototipo-motor-v2.saida.txt` antes de desconfiar do plano. Os valores de ouro vêm do protótipo — se divergir, a implementação está diferente da especificação.
