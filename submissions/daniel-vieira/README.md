# Submissão — Daniel Vieira — Challenge 003

## Sobre mim

- **Nome:** Daniel Vieira
- **LinkedIn:** https://linkedin.com/in/daniel-vieira-r
- **Challenge escolhido:** 003 - Lead Scorer

---

## Como executar

A solução é executável em um único comando, a partir de um clone deste repositório. O único
pré-requisito é Docker ou Podman com o respectivo plugin de compose; o dataset acompanha o
pacote (fonte normalizada versionada), de modo que nenhuma credencial externa é necessária.

```bash
# a partir da raiz deste repositório (o fork do desafio)
cd submissions/daniel-vieira/solution
./scripts/quickstart
```

O script prepara o ambiente na primeira execução (gera a senha do banco e escolhe uma porta de
host livre), provisiona o banco (migração e seed idempotentes) e sobe as duas aplicações web. A
imagem é compilada apenas na primeira execução. Encerre com Ctrl-C. As aplicações ficam em:

- Aplicação do agente: http://127.0.0.1:8081/login
- Aplicação do gerente: http://127.0.0.1:8082/login

O login é sem senha nesta versão de demonstração: a tela lista os usuários semeados; basta
selecionar um agente ou um gerente. Instruções completas, arquitetura e base de conhecimento
estão no README do produto, em `solution/README.md`.

---

## Executive Summary

Construí um MVP funcional que ranqueia e prioriza oportunidades de venda por um indicador
composto de potencial, personalizado por agente comercial, entregue como aplicação web que
gerencia o ciclo de engajamento de cada oportunidade. A análise exploratória mostrou que a
probabilidade de ganho não é aprendível a partir deste dataset — a conversão é praticamente
plana e o win rate do agente é ruído —, de modo que substituí deliberadamente a propensão por
duas alavancas robustas: o momentum (timing) e a especialização demonstrada do agente, num
composto do tipo RFM estendido pelo eixo do agente, agregado por uma média geométrica não
compensatória. A recomendação principal é usar o instrumento como apoio de priorização da
região de topo, com um laço de realimentação em produção para calibrar pesos e curvas a partir
dos desfechos realizados. A limitação central é o próprio dataset, sintético e raso, que
sustenta o enquadramento de demonstração de método, não de acurácia preditiva.

---

## Solução

### Abordagem

Comecei pela compreensão do problema e dos dados antes de qualquer modelagem. O trabalho foi
decomposto em três fases, cada uma desdobrada em tarefas atômicas mantidas em um backlog
unificado:

1. Análise exploratória (EDA) dos dados brutos do CRM, para descobrir que sinal existe;
2. Construção do modelo de ranqueamento a partir do que a EDA sustentou;
3. Desenvolvimento da aplicação MVP para gestão de oportunidades.

A EDA foi determinante e mudou o rumo do modelo. Ela mostrou que porte, setor e geografia não
distinguem a conversão, que o valor fechado acompanha de perto o preço de tabela e que o win
rate individual é ruído. Diante disso, abandonei a ideia inicial de um modelo preditivo de
probabilidade de ganho — que ajustaria ruído — e de uma heurística separada de distribuição de
leads. Em seu lugar, a capacidade do agente virou uma dimensão do próprio indicador, produzindo
um ranqueamento personalizado por agente (decisão registrada no ADR B7Q3).

O modelo é um substituto transparente do valor esperado (probabilidade de ganho vezes valor).
Como a probabilidade não é aprendível aqui, ela é substituída pelo momentum e pela
especialização. As dimensões correspondem ao modelo canônico RFM, estendido pelo eixo do
agente. A agregação combina um portão de elegibilidade não compensatório com uma média
geométrica ponderada, que penaliza o desequilíbrio: um momentum baixo arrasta o índice
independentemente das demais dimensões. Os pesos são arbitrados e documentados, não aprendidos,
porque não há alvo discriminativo do qual aprendê-los.

O desenvolvimento seguiu desenvolvimento orientado a testes, segurança desde a concepção e um
pipeline assistido por LLM que registra o trabalho diário (worklogs), vincula-o às sessões
físicas (transcrições) e registra as decisões de arquitetura (ADR) tempestivamente. Cada fase
foi sucedida por uma sessão de code-review, e cada sessão que produziu código passou por uma
auditoria independente, realizada por um agente com contexto deliberadamente cortado (recebe só
os critérios de aceitação e o diff, nunca o raciocínio do autor).

### Resultados / Findings

A entrega é uma aplicação funcional que expõe duas listas de decisão sobre a tripla
produto-empresa-agente:

- Potenciais: pares conta-produto conhecidos e ainda não engajados, ordenados pelo indicador
  personalizado por agente, com filtro de corte na interface;
- Iniciadas: as oportunidades que o agente engajou, ordenadas pelo decaimento do potencial
  restante, até expirarem por idade ou serem marcadas como Won ou Lost.

A classificação é autoexplicativa: cada oportunidade traz o seu indicador e a decomposição das
dimensões em uma visualização em teia, para que o agente leia o porquê da posição.

![Oportunidades engajadas na aplicação do agente](solution/.claude/assets/examples/example-app-agente-oportunidades-engajadas-dark.png)

![Painel de desempenho do agente](solution/.claude/assets/examples/example-app-agente-desempenho-dark.png)

A metodologia formal do indicador, com as cautelas de literatura (OECD/JRC Handbook on
Constructing Composite Indicators; Kaplan-Meier para a curva de decaimento; Pareto/NBD e BG/NBD
para cadência e churn), está em `solution/docs/metodologia-scoring.md`. A EDA está em
`solution/docs/analise-exploratoria.md` e a validação de robustez em
`solution/docs/validacao-scoring.md`.

### Recomendações

- Ler o instrumento como apoio de priorização da região de topo, e não como uma ordem total
  precisa: a estrutura primária regida pelo momentum é robusta, mas a ordenação fina entre pares
  maduros depende dos pesos arbitrados, cuja sensibilidade está reportada na validação;
- Fechar um laço de realimentação em produção, capturando os desfechos realizados para
  recalibrar pesos e curvas; nesse momento, as dimensões hoje inertes (diligência e atividade do
  cliente) e a regra de cross ou up-sell tornam-se calibráveis;
- Não investir, com este perfil de dado, em um modelo preditivo de probabilidade de ganho: a EDA
  mostra que o sinal é fraco e que aprender pesos ajustaria ruído;
- Em produção, reintroduzir uma dimensão de fit de conta (perfil de cliente ideal), padrão na
  prática, que aqui foi omitida por ser inerte neste dataset.

### Limitações

- O dataset é insuficiente em largura e profundidade e traz marcas de dado sintético (conversão
  invariante, contas todas quentes, preços colados à lista, ciclo travado no corte de
  expiração), o que desencoraja a modelagem preditiva e sustenta o enquadramento de demonstração
  do método;
- O braço descendente da curva de momentum é uma suposição documentada, na ausência de contas
  inativas para ajustá-lo;
- O modelo é estático por escolha de MVP;
- Do registro do processo, 8 das 27 sessões de trabalho não têm a transcrição `.jsonl`
  correspondente; como a forma bruta não é retida por política de segurança, essas transcrições
  provavelmente não são recuperáveis. As 19 transcrições higienizadas disponíveis, somadas aos
  27 worklogs e aos 17 ADRs, cobrem o processo de forma ampla.

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| Claude Code (Opus) | Todo o ciclo: análise exploratória (SQL), formalização do modelo, construção da aplicação em Common Lisp, revisões de código, auditorias independentes e a redação da documentação |
| PostgreSQL / psql | Execução das consultas de EDA e de verificação do seed sob condução do agente |
| Docker / Podman compose | Verificação ponta a ponta da execução em um passo, na perspectiva do avaliador |

O trabalho todo correu sobre um único pipeline assistido por LLM, projetado e configurado por
mim e utilizado em projetos profissionais. Ele não é um uso de prompt único: é um processo com 
backlog, worklog por sessão, ADRs, code-review por fase e auditoria independente.

### Workflow

1. **Concepção e EDA.** Enquadrei o problema e conduzi a EDA para descobrir que sinal os dados
   sustentam. O achado de que a propensão não é aprendível redirecionou toda a modelagem;
2. **Modelo de scoring.** Formalizei o indicador composto (dimensões, normalização por
   percentil, portão de elegibilidade e média geométrica ponderada), confrontando cada escolha
   com a literatura estabelecida e registrando as cautelas;
3. **Validação.** Como não há verdade-fundamental a prever, validei robustez, não acurácia:
   comparação com baselines por correlação de Spearman, análise de sensibilidade à normalização,
   à forma de agregação e aos pesos, e validade de face;
4. **Aplicação.** Construí a aplicação web (Common Lisp, HTMX, PostgreSQL) sob desenvolvimento
   orientado a testes, cobrindo o ciclo de engajamento mínimo necessário ao ranqueamento;
5. **Empacotamento.** Consolidei a execução em um passo em container único (Docker/Podman) e
   validei a experiência do avaliador a partir de um clone limpo;
6. **Controle de qualidade.** A cada fase, uma sessão de code-review; a cada sessão com código,
   uma auditoria independente com contexto cortado, cujo relatório é insumo da decisão humana.

### Onde a IA errou e como corrigi

- **Referência temporal à frente dos dados.** Ao computar o momentum e o decaimento, que
  dependem da idade desde o evento, a IA ia adotar a data de sistema real como o "agora". Como
  o dataset é histórico, essa referência ficava muito à frente da janela dos dados: toda
  oportunidade ultrapassaria a cadência e o corte de expiração, zerando o sinal e inviabilizando
  um teste real com o dataset válido. Identifiquei o problema, e a referência de "agora" foi
  ancorada no marco temporal do próprio dataset;
- **Forma de agregação.** A primeira formulação era uma base aditiva multiplicada por um fator
  de momentum. A validação que exigi (Fase 5) revelou que essa forma tornava o momentum
  dominante por um artefato de escala, não por decisão de peso. Substituí pela média geométrica
  ponderada, empiricamente mais robusta (ADR C4X9);
- **Recompilação no arranque do container.** O diagnóstico inicial presumiu data de arquivo.
  Medindo os stamps de compilação, a causa real era o auto-upgrade do ASDF divergindo do uiop
  fixado. A correção foi distribuir a aplicação como imagem de core do SBCL, com guarda que
  impede a recompilação (ADR K6M2);
- **Auditoria independente.** A auditoria da fase de empacotamento apontou oito achados, entre
  eles dados não versionados que quebrariam um clone limpo, imagens por nome não qualificado que
  quebram o Podman não interativo e publicação de portas em 0.0.0.0 contra o menor privilégio.
  Todos foram remediados antes da entrega;
- **Escopo, nesta própria sessão de entrega.** O agente criou uma tarefa nova para um objetivo
  que já possuía tarefa-pai (a tarefa de empacotamento e entrega). O erro foi corrigido ao ler o
  registro de decisão e o backlog, reatribuindo a sessão à tarefa correta.

### O que eu adicionei que a IA sozinha não faria

- **A concepção das dimensões de ranqueamento.** A escolha de quais vetores do contexto de
  decisão de venda compõem o potencial — retorno econômico, momentum, afinidade e a
  especialização demonstrada do agente — foi ideação minha, um trabalho de raciocínio sobre o
  que efetivamente move o fechamento de uma venda, não uma derivação que a IA faria sozinha. A
  IA formalizou, normalizou e agregou essas dimensões; a proposição de que são essas as
  dimensões certas, e o seu significado de negócio, partiu de mim;
- A decisão epistêmica de **não** treinar um modelo preditivo nem aprender os pesos dos dados —
  contra o instinto default — porque a EDA mostra que não há alvo discriminativo e que aprender
  ajustaria ruído;
- O enquadramento do objetivo como demonstração de método e apoio à decisão do agente, não como
  acurácia preditiva sobre uma base fraca;
- Segurança desde a concepção como restrição dura, com segregação entre dados expostos e
  sensíveis e segredos fora da base de código;
- A disciplina de auditoria independente com contexto deliberadamente cortado, que assegura que
  a revisão não herde o raciocínio do autor;
- As decisões de escopo (a distribuição de leads como dimensão do indicador, não como modelo
  separado) e a curadoria das fontes de literatura que sustentam cada escolha de técnica.

---

## Evidências

A evidência integral do trabalho assistido por IA acompanha esta submissão em
`solution/.claude/`, com um guia de leitura em `process-log/README.md`. Em resumo:

- **Worklogs** (`solution/.claude/worklog/`): 27 registros de sessão com a conduta, as
  motivações e o raciocínio de cada dia de trabalho, além do resumo histórico;
- **Transcrições** (`solution/.claude/sessions/`): 19 transcrições higienizadas das sessões,
  como chat exports do processo real;
- **Decisões** (`solution/.claude/decisions/`): 17 ADRs registrando as escolhas consequentes;
- **Backlog** (`solution/.claude/backlog/`): as tarefas atômicas do projeto;
- **Git history**: o histórico de commits do projeto, em `solution/`, evidencia o
  desenvolvimento incremental orientado a testes.

Checklist de formatos:

- [x] Chat exports (transcrições higienizadas em `solution/.claude/sessions/`)
- [x] Git history (histórico de commits em `solution/`)
- [x] Written narrative (worklogs e ADRs em `solution/.claude/`)
- [x] Screenshots (capturas da aplicação em `solution/.claude/assets/examples/`)

---

_Submissão enviada em: 2026-07-21_
