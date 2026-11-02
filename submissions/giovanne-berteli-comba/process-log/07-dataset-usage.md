# Decisão de uso dos datasets — 02/11/2026

## Contexto e objetivo

O usuário pediu para avançar depois do commit `26dc6d3`. A D02 precisava definir
o papel de cada arquivo, a existência ou ausência de mapeamento válido e os limites
de avaliação. O agente retomou a partir dos documentos operacionais e dos recibos
atuais, sem usar conversas históricas para decidir.

## Colaboração com IA

Codex usou a auditoria D01 para redigir a
[decisão operacional](../knowledge/dataset-usage.md). A
[captura 11](chat-exports/11-dataset-usage-chat.md) preserva as novas mensagens
acessíveis, incluindo o final da D01 e a troca sobre o nome do commit.

## Decisões e alternativas

- **Escolha do agente no escopo autorizado:** atendimento para diagnóstico
  descritivo; IT para benchmark de classificação em suas oito categorias.
  São papéis complementares; não foi criado join nem mapeamento de taxonomias.
  Essa decisão não é apresentada como aprovação humana adicional.
- **Alternativas rejeitadas:** misturar rótulos dos arquivos, inventar uma
  correspondência por semelhança de nomes, tratar `Resolution` como biblioteca
  confiável ou corrigir datas para produzir métricas aparentes de duração.
- **Conflitos de rótulo:** preservar os registros originais e sinalizar seus
  grupos. Não escolher automaticamente um rótulo majoritário; os rótulos de
  atendimento não serão alvos supervisionados do protótipo IT.
- **Métricas:** explicitar populações para volume, status e satisfação; distinguir
  proporção de encerrados de taxa de fechamento ao longo do tempo. Tempo total e
  esforço ativo continuam indisponíveis; horas/custo só em cenários identificados.
- **Avaliação:** separar domínios e dados de ajuste/teste; não reportar acurácia
  em atendimento a partir de resultado IT. Um eventual teste sem rótulos no outro
  domínio não prova detecção de casos fora da taxonomia. `Document` processado
  também não garante que todo conteúdo existia na chegada do ticket.
- **Escopo seguinte:** R01 fica previamente limitado a três PRs públicos ou
  20 minutos, com critérios de seleção no plano. A pesquisa ainda não ocorreu.

## Execução e evidências

Atualizados instruções, status, plano, contexto, índice, donos da informação,
README, estratégia de validação e tabela oficial F01–F07. O registro D02 é a
autoridade para essas escolhas; V00 continua pendente para membership, candidatos,
metas e limiares. Stack e contrato final da automação permanecem para S01/V00.

Os [19 testes existentes](../docs/review-evidence/dataset-usage-tests.txt) passaram.
Não foram criados testes que apenas espelham o texto da decisão. Os testes cobrem
os contratos documentais e as regras de software existentes, não a eficácia da
futura automação ou a aceitação humana das escolhas.

A auditoria foi regenerada a partir dos dados com hashes verificados; o JSON
permaneceu idêntico (`fd9319894962f9117f5a7d35c536f9cf197869647365f90704203fd1b1a5868f`).
Os recibos da fundação e da D01 foram revalidados após atualizar seus documentos
dependentes. Não houve mudança de dados, código de aplicação ou resultados de IA.

## Estado e próxima ação

D02 concluída. R01 é a próxima tarefa, seguida de A01 sob o contrato de métricas.
Não houve pesquisa de PRs, implementação de split, treino, avaliação de modelo,
protótipo, commit ou publicação nesta etapa.

## Cobertura das conversas

Captura 11: oito mensagens adicionais extraídas de quatro turnos retornados;
`hasMore=true` indica histórico anterior fora da página. IDs já preservados foram
excluídos. Inclui o final da D01 e a troca sobre o nome do commit; o final desta
D02 e qualquer mensagem posterior à captura ficam para a próxima extração.
