# Evoluções planejadas — fora do escopo desta entrega

Estas ideias foram consideradas durante o projeto. A entrega priorizou diagnóstico,
triagem assistida verificável e reprodução. **São caminhos de continuidade que
não foram implementados neste escopo**. A decisão foi concentrar esta versão em
um fluxo verificável e reproduzível.

| Ordem | Evolução pensada | Valor para o negócio | O que falta para implementar e validar |
| --- | --- | --- | --- |
| 1 | Piloto operacional com a equipe (o ensaio local e seus cronômetros já foram implementados) | Medir qualidade e ganho líquido com a operação | Dados representativos, datas/transições, rótulos adjudicados e critérios de avanço acordados antes de observar resultados |
| 2 | IA analista de dados/métricas | Explicar mudanças, sinalizar inconsistências e sugerir investigação com fontes | Cálculos e checks determinísticos, períodos/populações/versões explícitos e avaliação própria das explicações |
| 3 | Google Sheets | Acompanhar fila e revisões no trabalho do time | Conta/acesso configurados, IDs estáveis, deduplicação e reconciliação de eventos; o CSV entregue é o primeiro passo local |
| 4 | Email e Discord/canal interno | Resumos e alertas sobre mudanças acionáveis ou falhas | Destinatários/canal autorizados, entrega observável, controle de repetição e acesso à aplicação |
| 5 | Bot interativo e helpdesk | Consultar casos, atribuir responsável e registrar decisões no fluxo habitual | Autenticação e papéis, auditoria, contrato de eventos e validação da taxonomia/textos disponíveis na abertura |

Fluxo pretendido: dados/eventos → cálculos e verificações → métricas versionadas
→ IA explica com fontes → pessoa revisa → planilha/resumo/alerta → decisão registrada.

A IA analista consumiria métricas verificadas por código. Ela poderia destacar
inconsistências e levantar hipóteses; uma segunda IA concordando não comprova
verdade dos dados, rótulos ou causalidade. Seu uso exigiria avaliar números inventados,
fontes ausentes e confusão entre medição e hipótese. Correções humanas não alimentariam
um retreino automático sem versão e avaliação com novos dados.

O [estudo anterior](pre-submission-review.md#5-o-que-implementar-no-futuro)
registra os caminhos técnicos e fontes primárias de API. Nenhuma conta externa,
credencial, envio ou integração foi configurada. A proposta deve ser adaptada ao
canal que o time realmente usa e às medições do piloto.
