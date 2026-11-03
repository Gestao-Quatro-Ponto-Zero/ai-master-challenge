# Cobertura das conversas preservadas

Este inventário descreve os arquivos locais disponíveis para recrutamento; não é
prova de completude da plataforma. Há **24 capturas**, **181 ocorrências
de mensagens** e **139 IDs explícitos distintos**, sem duplicação desses IDs.
As 42 ocorrências sem ID continuam sem deduplicação global comprovada.
Contagens de turnos abaixo são os representados no arquivo após deduplicação,
não o número de turnos retornados pela API; cada cabeçalho declara sua cobertura.

| Captura | Mensagens | IDs explícitos | Turnos representados | hasMore no cabeçalho |
| --- | ---: | ---: | ---: | --- |
| [01-preparation-chatgpt.md](../process-log/chat-exports/01-preparation-chatgpt.md) | 10 | 0 | 5 | false |
| [02-challenge-comparison.md](../process-log/chat-exports/02-challenge-comparison.md) | 7 | 0 | 2 | false |
| [03-planning-chat.md](../process-log/chat-exports/03-planning-chat.md) | 25 | 0 | 10 | false |
| [04-planning-completion.md](../process-log/chat-exports/04-planning-completion.md) | 2 | 2 | 1 | true |
| [05-architecture-review-chat.md](../process-log/chat-exports/05-architecture-review-chat.md) | 5 | 5 | 1 | false |
| [06-review-validation-chat.md](../process-log/chat-exports/06-review-validation-chat.md) | 4 | 4 | 2 | false |
| [07-review-approval-chat.md](../process-log/chat-exports/07-review-approval-chat.md) | 4 | 4 | 2 | false |
| [08-git-staging-chat.md](../process-log/chat-exports/08-git-staging-chat.md) | 4 | 4 | 2 | true |
| [09-foundation-controls-chat.md](../process-log/chat-exports/09-foundation-controls-chat.md) | 7 | 7 | 2 | false |
| [10-data-audit-chat.md](../process-log/chat-exports/10-data-audit-chat.md) | 6 | 6 | 2 | true |
| [11-dataset-usage-chat.md](../process-log/chat-exports/11-dataset-usage-chat.md) | 8 | 8 | 3 | true |
| [12-pr-review-chat.md](../process-log/chat-exports/12-pr-review-chat.md) | 7 | 7 | 3 | true |
| [13-operational-diagnosis-chat.md](../process-log/chat-exports/13-operational-diagnosis-chat.md) | 8 | 8 | 3 | true |
| [14-automation-scope-chat.md](../process-log/chat-exports/14-automation-scope-chat.md) | 8 | 8 | 3 | true |
| [15-evaluation-protocol-chat.md](../process-log/chat-exports/15-evaluation-protocol-chat.md) | 9 | 9 | 3 | true |
| [16-prototype-chat.md](../process-log/chat-exports/16-prototype-chat.md) | 9 | 9 | 3 | true |
| [17-setup-fix-chat.md](../process-log/chat-exports/17-setup-fix-chat.md) | 8 | 8 | 3 | true |
| [18-final-evaluation-chat.md](../process-log/chat-exports/18-final-evaluation-chat.md) | 8 | 8 | 3 | true |
| [19-reviewer-evidence-chat.md](../process-log/chat-exports/19-reviewer-evidence-chat.md) | 8 | 8 | 3 | true |
| [20-codetour-discovery-chat.md](../process-log/chat-exports/20-codetour-discovery-chat.md) | 6 | 6 | 2 | true |
| [21-codetour-completion-chat.md](../process-log/chat-exports/21-codetour-completion-chat.md) | 4 | 4 | 2 | true |
| [22-pre-submission-review-chat.md](../process-log/chat-exports/22-pre-submission-review-chat.md) | 5 | 5 | 3 | false |
| [23-management-delivery-chat.md](../process-log/chat-exports/23-management-delivery-chat.md) | 10 | 10 | 5 | true |
| [24-audience-feedback-chat.md](../process-log/chat-exports/24-audience-feedback-chat.md) | 9 | 9 | 3 | true |

As três primeiras capturas não registram IDs por mensagem. `hasMore=false` não
comprova mensagens excluídas, editadas, ramificações ou anexos recuperados;
`hasMore=true` indica paginação anterior fora daquela leitura. As extrações
retêm usuário/assistente no idioma original; não são exports nativos completos.
Ferramentas, raciocínio privado, instruções internas, imagens e gravações não
integram essas capturas. Não há export de Claude Code ou Gemini para alegar uso.

O arquivo mais recente declara seu corte e suas lacunas: mensagens
posteriores, inclusive a resposta final ainda inexistente na captura, ficam para
próxima extração. Não foram reconstruídas como citação. Um scan de padrões comuns
de credenciais não encontrou correspondências; isso é um check limitado, não uma
certificação de privacidade ou de revisão humana. Veja o [process log](../process-log/README.md).

O process log é evidência histórica, fora do contexto operacional padrão. Decisões
atuais continuam nos donos indicados em [status](../PROJECT_STATUS.md) e
[conhecimento](../knowledge/index.md).
