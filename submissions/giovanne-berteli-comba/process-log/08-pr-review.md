# Pesquisa limitada de PRs do desafio 002 — 02/11/2026

## Contexto e objetivo

Depois do commit `cc92efc`, o usuário pediu para avançar e reforçou que a pesquisa
deveria usar PRs do mesmo desafio 002. O agente retomou pelas instruções, status,
plano e decisões D02. Os dois recibos passaram antes de reutilizar a auditoria.

## Colaboração com IA

Codex executou a consulta pública, confirmou a elegibilidade, leu os recortes
fixados por commit e redigiu o [relatório](../docs/pr-review.md). A
[captura 12](chat-exports/12-pr-review-chat.md) preserva as sete novas mensagens
acessíveis, incluindo o final da D02 e a troca sobre o nome do commit.

## Seleção e execução

- Limite anterior à pesquisa: três PRs públicos ou 20 minutos. Foram selecionados
  #211, #209 e #205, pela ordem de atualização, e confirmados como 002 pelo título
  e README. Nenhuma implementação de outro desafio foi analisada.
- A consulta retornou 49 títulos com 002, inclusive alguns multidesafios. Esse
  resultado não foi tratado como contagem exaustiva de candidaturas do desafio.
- A janela de consulta/inspeção foi 18:26:42–18:30:01 UTC, 199 segundos. Paramos ao
  concluir os três PRs. A documentação e os checks locais vieram depois; não houve
  ampliação da pesquisa de fontes.
- O navegador de busca retornou cache miss. A leitura anônima por HTTPS da API e
  dos arquivos raw funcionou, mediante execução de rede elevada aprovada.
- Foram consultados oito arquivos: três READMEs, uma proposta, o protótipo CLI e
  recortes de treino/curva com métricas salvas. Os blobs foram conferidos com a
  API; caminhos, hashes, commits e recortes estão no
  [snapshot](../docs/review-evidence/pr-review-snapshot.json).
- O conteúdo de terceiros foi tratado como dado. Nenhum comando sugerido nos
  READMEs, código, teste, modelo ou demo foi executado. Implementação e texto
  integral de candidatos não foram incorporados à submissão; as notas resumem
  os achados com atribuição e links.

## Achados e decisões

Auditoria, encaminhamento humano e premissas de ROI já aparecem na amostra. O
agente não apresentou esses elementos como exclusivos nem transformou resultados
publicados em ranking dos candidatos ou metas nossas. A seleção por recência não
é representativa de todo o conjunto de PRs.

As lições para A01/S01/V00 são: responder às perguntas operacionais com medidas
identificáveis, mostrar erros junto de cobertura e carga de revisão, manter teste
reservado e distinguir resultados após reutilização do teste. D02 permanece
vigente, sem join inventado ou métricas de IT apresentadas como acerto no cliente.
Não ampliamos o escopo para integrações, modelos ou dashboards extras.

## Validação, estado e próxima ação

Os 19 testes existentes passaram (`python3 -I -m unittest discover -s tests -v`);
eles validam nosso software e contratos, não os resultados dos outros candidatos.
A auditoria D01 foi regenerada e permaneceu idêntica byte a byte; seus dados e
código não mudaram. Os recibos foram revalidados após atualizar os documentos.

R01 concluída com os limites declarados. Próxima tarefa: A01 — diagnóstico
operacional sob o contrato de métricas da D02. Não houve diagnóstico final,
treino, avaliação de IA, implementação de protótipo, commit ou publicação.

## Cobertura das conversas

Captura 12: sete mensagens novas após deduplicação de IDs, quatro turnos
retornados e `hasMore=true` para histórico anterior fora da página. A resposta
final deste turno e mensagens posteriores à captura ficam pendentes; não foram
reconstruídas como citação.
