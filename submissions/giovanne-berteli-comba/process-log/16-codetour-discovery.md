# CodeTour descoberto sem configuração manual — 02/11/2026

O usuário tinha o CodeTour instalado, mas o tour não apareceu. Observou que o
revisor não deveria perder tempo investigando a configuração. A E01 anterior
validara formato/arquivos/âncoras, sem testar descoberta na extensão real; isso
foi insuficiente para validar a experiência de abertura.

## Causa e correção

A extensão instalada (CodeTour 0.0.61) procura tours nos diretórios previstos de
cada pasta do workspace, sem buscar automaticamente todo `.tours` aninhado. O
VS Code estava com a raiz do repositório aberta; o tour estava na submissão.
A implementação foi conferida no código da própria extensão instalada.

Criado `review.sh`: resolve a própria localização, consulta o perfil do VS Code,
instala o CodeTour oficial somente se ausente e abre uma nova janela no workspace
da submissão. O workspace solicita a oferta do tour na primeira visita. O tour
também aparece no Explorer; a janela anterior e as configurações globais são
preservadas. O comando está destacado no README antes do protótipo. Não se editou
`.vscode`/`.tours` da raiz do repositório, pois a entrega só pode alterar a submissão.

O inicializador foi executado para o usuário e abriu o workspace correto com a
extensão já instalada. O Markdown permanece como alternativa, sem ser usado para
disfarçar ausência de descoberta no editor.

## Teste funcional real

Dois hosts de testes VS Code 1.143.1 com perfis isolados e a extensão instalada:

- Workspace da raiz: tour não descoberto, reproduzindo a falha.
- Workspace de revisão: tour descoberto por seu título registrado na extensão;
  navegação efetiva às 11 paradas, conferindo arquivo e seleção de linha pelas APIs
  do editor. Não se alegou screenshot ou validação visual humana.

O [teste preservado](../scripts/codetour-smoke.js) e a
[evidência](../docs/review-evidence/codetour-discovery.json) registram o escopo.
A execução da CLI retorna antes da conclusão do host; o registro aguardou o
resultado produzido após as assertions, sem tratar só o exit code da CLI como
prova de navegação. Os perfis de teste não modificam o perfil pessoal.

Dois testes externos adicionais verificam execução de outra pasta com espaços,
o workspace correto, reuso da extensão existente e instalação do ID oficial se
ausente. A instalação ausente usa fixture isolada de CLI; não foi simulada uma
instalação real que não ocorreu no perfil do usuário. Os 74 testes da suíte passaram.

## Evidência e handoff

Atualizados README, roteiro/guia, verificador e status. A navegação não depende
de mudanças no modelo ou no teste final. Recibos foram revalidados após conferência
de saídas e preservação dos hashes congelados, sem nova previsão final ou treino.

A [captura 20](chat-exports/20-codetour-discovery-chat.md) preserva seis mensagens
novas de quatro turnos retornados, incluindo final E01 e o problema relatado;
hasMore=true. Mensagens posteriores/final da correção ficam para a próxima extração.
Somente usuário/assistente foram arquivados, sem ferramentas ou instruções internas.
P01 segue como próxima etapa. Sem commit, push ou publicação.
