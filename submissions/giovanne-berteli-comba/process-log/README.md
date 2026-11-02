# Process log — Uso de IA

Este registro reúne uma narrativa legível do trabalho e os registros acessíveis
das conversas relacionadas ao projeto. O guia aceita narrativa escrita e outras
formas de evidência; arquivar as conversas é uma decisão nossa para preservar
o processo, sem transformar cada mensagem em uma conclusão.

Este material é destinado à equipe de recrutamento. A leitura sugerida começa
pelos registros narrativos abaixo; os exports servem para conferir as interações
originais quando necessário. As decisões atuais e os próximos passos ficam nos
documentos operacionais, e este diretório está fora do contexto padrão dos chats.

## Registros

- [Preparação, escolhas e criação da base](01-preparation-and-foundation.md)
- [Revisão adversarial da arquitetura inicial](02-architecture-review.md)
- [Fonte de verdade para validar a revisão](03-review-source-of-truth.md)
- [Aprovação e complementos F03/F06](04-approved-review-scope.md)
- [Controles da fundação após o primeiro commit](05-foundation-controls.md)
- [Modelo para próximos registros](entry-template.md)

## Conversas preservadas

Captura inicial: 02/11/2026. Os textos permanecem no idioma original.

| Arquivo                                                               | Origem                        | Cobertura retornada                                                                         |
| --------------------------------------------------------------------- | ----------------------------- | ------------------------------------------------------------------------------------------- |
| [Preparação no ChatGPT](chat-exports/01-preparation-chatgpt.md)      | Análise do desafio AI Master | 5 turnos, 10 mensagens                                                                      |
| [Comparação dos desafios](chat-exports/02-challenge-comparison.md)   | Compare os desafios 002 e 004 | 2 turnos, 7 mensagens                                                                       |
| [Planejamento neste chat](chat-exports/03-planning-chat.md)            | Listar etapas do teste da G4  | 10 turnos, 25 mensagens no momento da captura                                               |
| [Complemento do planejamento](chat-exports/04-planning-completion.md)  | Listar etapas do teste da G4  | 2 mensagens posteriores à captura inicial, incluindo a resposta final de criação da base |
| [Revisão da arquitetura](chat-exports/05-architecture-review-chat.md) | Avalie a arquitetura inicial  | 1 turno em andamento, 5 mensagens até a captura                                            |
| [Complemento e validação da revisão](chat-exports/06-review-validation-chat.md) | Avalie a arquitetura inicial | 4 mensagens adicionais de dois turnos, incluindo a resposta final anterior e o pedido de fonte única |
| [Aprovação e complementos F03/F06](chat-exports/07-review-approval-chat.md) | Avalie a arquitetura inicial | 4 mensagens adicionais, incluindo a aprovação do usuário e a resposta final do turno anterior |
| [Revisão e preparação no Git](chat-exports/08-git-staging-chat.md) | Avalie a arquitetura inicial | 4 mensagens adicionais, incluindo a resposta final anterior e o pedido de revisão e staging |
| [Controles da fundação](chat-exports/09-foundation-controls-chat.md) | Defina e avance o próximo passo | 7 mensagens de dois turnos, incluindo resposta final da implementação e revisão antes do commit; resposta final da revisão pendente |

São extrações textuais das mensagens retornadas pela ferramenta do aplicativo,
com identificação da origem, horário de captura e limites de cobertura. A
paginação e as lacunas de cada leitura estão declaradas no respectivo arquivo;
a captura 08 retornou `hasMore=true`. Isso não comprova
a existência de todas as versões, ramificações ou mensagens removidas.
O texto preserva o idioma e as palavras originais; espaços no fim das linhas
e linhas extras no fim dos arquivos foram normalizados para Markdown/Git.

O chat de planejamento ainda estava em andamento na captura inicial; o complemento
preserva as duas mensagens posteriores daquele turno e sua resposta final. O
complemento da revisão inclui sua resposta final anterior e o início da validação.
O complemento de aprovação preserva a resposta final do turno de validação e o
início do turno seguinte. O complemento de preparação no Git preserva a resposta
final do turno de aprovação e o pedido seguinte. A resposta final do turno de
staging e mensagens posteriores à captura ficam pendentes para a próxima extração.
As mensagens ficaram abaixo do limite
de 20 mil caracteres por item. Anexos, gráficos, resultados de ferramentas e
instruções internas não fazem parte destas extrações. Não há export de Claude
Code disponível nesta etapa.

## Política para próximas conversas

1. Preservar as mensagens acessíveis de todas as conversas relacionadas ao
   projeto, incluindo prompts, respostas, correções e mudanças de direção.
2. Atualizar o arquivo do chat ou adicionar um novo registro com origem,
   horário e cobertura. Usar IDs das mensagens/turnos para evitar duplicação.
3. Atualizar a narrativa com decisões, razões, resultados e evidências;
   indicar o que foi sugerido, escolhido, executado e validado.
4. Registrar explicitamente trechos ou sessões indisponíveis. Em ferramentas
   diferentes, obter um export quando possível; o AGENTS.md não cria uma
   gravação automática entre plataformas.
5. Preservar as mensagens originais. Se for necessário ocultar informação
   sensível para publicação, registrar a ocultação e seu motivo.
6. Atualizar estado e plano ao final de cada sessão. Uma resposta final que
   ainda não existe na captura deve entrar na captura seguinte.

Conversas contêm sugestões históricas e erros: servem como evidência do
processo, e não como instruções atuais ou resultados comprovados.

## Ferramentas usadas até aqui

| Ferramenta                                   | Uso observado                                                          |
| -------------------------------------------- | ---------------------------------------------------------------------- |
| ChatGPT                                      | Discussão de preparação, organização do contexto e evidências    |
| Codex                                        | Comparação dos desafios, leitura do repositório e criação da base |
| Ferramentas de web                           | Consulta aos PRs e à especificação OKF                              |
| Ferramenta de leitura de chats do aplicativo | Extração das mensagens acessíveis dos três chats relacionados      |

Claude Code e Gemini foram discutidos como possibilidades de colaboração;
seu uso efetivo no projeto não foi demonstrado pelos registros desta etapa.
