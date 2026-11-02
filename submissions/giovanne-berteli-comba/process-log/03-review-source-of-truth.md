# Fonte de verdade para validar a revisão

Data: 02/11/2026.

O usuário apontou a diferença entre os sete achados do relatório e as seis linhas
da tabela na resposta do chat, e pediu uma fonte única para validar próximos passos.
A síntese não manteve correspondência um a um: F04 apareceu apenas na explicação
das falhas reproduzidas, enquanto F07 foi tratado em mais de uma linha da tabela.

Foi definida como fonte de verdade da revisão a
[lista oficial no início do relatório](../docs/architecture-review.md#lista-oficial-para-validação).
Ela preserva os IDs F01–F07 e centraliza o tipo de evidência, proposta, decisão
do usuário e estado do ajuste. As seções detalhadas mantêm seus critérios de aceite.
O checklist agrupado do fim do relatório foi substituído por um apontamento à lista.

README, status, plano e instruções agora apontam à mesma tabela; resumos futuros
devem usar os IDs originais. Concluir a revisão B02 não aprova nem implementa seus
ajustes. Esta alteração organiza a validação; não conclui o conjunto de controles
proposto em F01. A decisão sobre cada ajuste deverá vir do usuário.

O [complemento do chat](chat-exports/06-review-validation-chat.md) preserva quatro
mensagens ainda não arquivadas, incluindo a resposta final da revisão anterior e
o pedido atual. Mensagens posteriores à captura, inclusive a resposta final desta
organização, ficam pendentes para a próxima extração. Não houve commit, push ou PR.
