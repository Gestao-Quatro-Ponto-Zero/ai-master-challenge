# Legibilidade, dois públicos e interpretação da qualidade — 03/11/2026

O candidato apontou rótulos verticais/truncados no gráfico, sugeriu separar a visão
da empresa da explicação ao instrutor, encontrou ausência do CodeTour no start-here
e questionou como avaliar se a entrega foi boa. O agente implementou M06 a partir
desse feedback de uso real; a submissão/PR seguem em P01.

## Mudanças

- Grupos e filas agora usam barras horizontais com nomes completos. O gráfico IT
  também apresenta as três contagens numa tabela. Na conferência visual, os valores
  inicialmente tinham contraste insuficiente; foram movidos para dentro das barras,
  com cor de fundo/texto explícitas. Não se alterou nenhum número ou classificação.
- Empresa é a visão inicial em ambos os entry points: diagnóstico de atendimento,
  ações e capacidade. Sem material de recrutamento, benchmark de outro domínio ou
  inicialização do modelo/banco pela interface. Premissas aparecem como tabela legível.
- Instrutor adiciona guia de autoria, roteiro, evidências, benchmark, demonstração
  no modo completo e ideias futuras. O modo de consulta explica como abrir a demo.
  O seletor muda a apresentação, não autentica papéis nem muda histórico/modelo.
- start-here e Guia do instrutor mostram comando, pré-requisito, 11 paradas e
  alternativa em Markdown do CodeTour.
- A avaliação da entrega ficou explícita: execução e melhora no benchmark são
  verificáveis; duração/causas/desperdício real têm resposta parcial e dependem
  de dados melhores. Benefício operacional requer piloto. Não se atribuiu nota
  de seleção nem comparação com o baseline privado da empresa.

## Verificação

81 testes passaram, incluindo dois novos de comportamento por público e troca de
visão nos dois entry points. Os testes de triagem existentes passaram selecionando
Instrutor. A visão Empresa foi testada com model-loader bloqueado e caminho de banco
temporário inexistente; não criou o banco. A demonstração continua usando treino
ou fixtures, sem acessar exemplos finais para ajustar o modelo.

No navegador, verificadas a seleção inicial Empresa, suas duas abas, a troca para
Instrutor e as seis abas da aplicação completa. O gráfico mostra Confirmação padrão,
Especialista e Triagem por inteiro, com contagens reconciliadas. Screenshots e
registros estão na [evidência M06](../docs/review-evidence/audience-delivery-checks.json).
O CodeTour atual percorreu as 11 âncoras em host VS Code isolado. Fontes/modelos/
política/referência/resultado congelados continuam idênticos; não houve fit ou
nova inferência final. Testes de software não são validação de ganho de negócio.

## Evidência humana e limite

A [captura 24](chat-exports/24-audience-feedback-chat.md) preserva nove mensagens
novas de quatro turnos retornados, hasMore=true, incluindo discussão anterior e
feedback atual. A imagem fornecida foi inspecionada; seu binário não integra a
extração textual. Anexos, ferramentas, instruções internas e raciocínio privado
ficam fora do chat export. Texto original e IDs foram preservados, sem duplicação
dos IDs já arquivados. Mensagens após o corte e o final atual permanecem pendentes.

O papel humano foi identificar fricção, propor públicos e cobrar uma leitura clara
de qualidade; o agente implementou e verificou as alterações. Não houve commit,
push, publicação ou integração externa.
