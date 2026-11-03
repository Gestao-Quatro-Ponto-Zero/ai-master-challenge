# Controles da fundação — 02/11/2026

## Contexto e objetivo

Depois do commit `cab8373`, o usuário pediu para identificar e executar o próximo
passo. O status e a sequência aprovada da revisão indicavam concluir os controles
da fundação antes de D01/D02. Esta entrega fecha B03; a aplicação segue pendente.

## Colaboração com IA

Codex consultou o commit, as instruções locais e os documentos operacionais.
A [captura desta conversa](chat-exports/09-foundation-controls-chat.md) preserva
o pedido e as mensagens disponíveis até o horário indicado no arquivo.

## Decisões e correções

- A sequência foi escolhida pelo agente com base no plano e nas aprovações já
  registradas, sem criar uma decisão humana sobre arquitetura ou dados.
- Foi usado Python 3.12 com biblioteca padrão: suficiente para contratos
  explícitos e hashes, sem introduzir dependências para a fundação.
- A leitura inicial de `git show HEAD` foi ampla demais e retornou também
  arquivos históricos de conversa. As leituras seguintes para execução foram
  delimitadas aos documentos operacionais; os arquivos de evidência só foram
  consultados para atualização do próprio registro. Os testes não usam texto
  dos exports como instrução ou dado de decisão.
- Uma tentativa de patch foi rejeitada porque o trecho esperado de um arquivo
  tinha uma quebra de linha diferente. O patch foi corrigido e reaplicado.

## Execução e evidências

- [Controles e comandos](../docs/foundation-controls.md): autoridade do desafio
  no contexto, comparação de declarações, links locais, cabeçalhos mínimos OKF,
  tabela F01–F07, ordem V00/I01 e recibos de SHA-256.
- [Testes](../tests/test_foundation.py): mutações em cópias temporárias,
  incluindo a contradição original 002→004, mudanças em regra/dado/modelo,
  dependência nova ou ausente, recibo inválido, link quebrado, exclusão dos
  arquivos históricos e execução da CLI fora da pasta da submissão.
- [Saída executada](../docs/review-evidence/foundation-tests.txt): 11 testes.
  As amostras de dado/modelo são fixtures artificiais para testar invalidação;
  não são datasets do desafio nem avaliação de IA.
- [Recibo atual](../docs/review-evidence/foundation-current.json): versão dos
  arquivos checados. O snapshot anterior foi preservado como evidência histórica.
- A entrada explícita nesta nova sessão encontrou instruções, desafio e próximo
  passo. A busca automática na raiz continua sujeita ao `.gitignore`.
  Não foi feito benchmark de agentes nem teste em Claude/Gemini.
- Verificação final: 11 testes aprovados, 12 documentos operacionais e 47 links
  locais, hashes atuais e diff sem erros de whitespace. Os sete arquivos novos
  foram registrados com intenção de adição (`git add -N -f`) para aparecerem no
  diff, sem preparar o conteúdo para commit. O índice somente leitura do sandbox
  exigiu repetição elevada, aprovada automaticamente.

O controle detecta contratos declarados e versões, não toda contradição possível
em prosa. Dependências futuras de resultados devem ser registradas explicitamente;
um hash atualizado não substitui regenerar e validar o resultado afetado.
Nenhuma revisão humana de resultados foi inferida ou marcada como `verified`.

## Estado e próxima ação

Estado dos ajustes apenas na [tabela oficial](../docs/architecture-review.md#lista-oficial-para-validação).
Andamento geral no [plano](../execution/plan.md). Próxima tarefa: D01 — adquirir e
auditar ambos os datasets, com fontes, versões, hashes, schemas e unidades reais.
Não houve download, auditoria de dados, avaliação de modelo, commit ou publicação
nesta etapa.

## Cobertura das conversas

Captura 09: um turno em andamento, quatro mensagens retornadas, sem outra página.
A resposta final desta etapa e qualquer mensagem posterior à captura ainda não
existiam no snapshot e ficam para a próxima extração. A lacuna anterior do fim do
staging permanece declarada no índice; não foi reconstruída como citação.

Na revisão antes do commit, o suplemento da captura 09 preservou mais três
mensagens: a resposta final da implementação, a pergunta do usuário e a atualização
inicial da revisão. A captura totaliza sete mensagens em dois turnos. A checagem
dos contratos e hashes e `git diff --check` passaram; não houve mudança de código.
O índice continua sem conteúdo preparado para commit, apenas intenção de adição
dos arquivos novos. A resposta final desta revisão fica para a próxima captura.
