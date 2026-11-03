# Aquisição e auditoria dos datasets — 02/11/2026

## Contexto e objetivo

O usuário pediu para avançar à próxima etapa depois do commit `b094b64`.
A D01 exigia adquirir e auditar ambos os datasets antes de escolher seus papéis
e a arquitetura da aplicação. O andamento geral fica no plano; os estados de
F01–F07 continuam apenas na tabela oficial da revisão.

## Colaboração com IA

Codex leu instruções, status, plano, conhecimento relevante e briefing. Consultou
as páginas oficiais e a API pública do Kaggle, escreveu scripts em Python com
biblioteca padrão e executou a auditoria. A
[captura 10](chat-exports/10-data-audit-chat.md) preserva as mensagens acessíveis,
incluindo a resposta final anterior que estava pendente.

## Decisões e correções

- Fixar a versão 1 de ambas as fontes e preservar bytes dos CSVs e ZIPs, com
  hashes independentes. Downloads e dados brutos ficam fora do Git.
- A primeira tentativa de rede no sandbox falhou por resolução de nomes.
  A execução elevada para consulta/download público foi aprovada e funcionou;
  não foram usados token, conta ou credenciais de Kaggle.
- Rejeitar a interpretação literal dos campos temporais como durações: são
  timestamps sem abertura do ticket, e 1.365 pares encerrados são negativos.
  Não corrigir datas silenciosamente nem converter esses intervalos em economia.
- Preservar ausências, duplicatas e conflitos de rótulo, identificando suas
  populações. O agente não decidiu qual rótulo deveria substituir outro.
- Não afirmar que todos os registros são reais ou sintéticos. Placeholders,
  emails de exemplo e descrições repetidas limitam a interpretação do briefing;
  a proveniência operacional não foi estabelecida de forma independente.
- Na revisão do script de aquisição foi encontrada a possibilidade de manifesto
  incompleto deixar uma fonte sem hash esperado. A validação foi reforçada antes
  do download e recebeu um teste adicional. Por isso a suíte passou de 18 para
  19 testes; a reprodução limpa foi repetida na versão final dos scripts.

## Execução e evidências

- [Manifesto](../data/manifest.json): URLs oficiais, versão, licença declarada,
  atualização da fonte, nomes dentro dos ZIPs, tamanhos e SHA-256.
- [Aquisição](../solution/acquire_data.py): download anônimo, versão fixada,
  validação de ZIP/membro, hashes e preservação de arquivos brutos existentes.
- [Auditoria](../solution/audit_data.py) e [JSON agregado](../data/audit.json):
  schemas, parsing, ausências, categorias, cobertura por status, cronologia,
  duplicatas e conflitos de rótulo. Nenhum texto de ticket ou nome/email individual
  foi incluído no artefato agregado.
- [Relatório](../docs/data-audit.md): 8.469 tickets operacionais e 47.837 textos
  IT; cobertura de satisfação de 32,70%; 49 grupos de descrições com rótulos
  conflitantes; limites para qualquer diagnóstico de duração e esforço.
- [Testes](../tests/test_data_audit.py) e saída
  `docs/review-evidence/data-audit-tests.txt`: 19 testes aprovados na suíte completa,
  incluindo os 11 da fundação e oito de aquisição/auditoria.
- [Reprodução limpa](../docs/review-evidence/data-reproduction.json): somente
  scripts e manifesto copiados, novos downloads e auditoria idêntica byte a byte.
  Hashes de scripts/manifesto e versão do Python identificam a execução final.
- Revisão final: 122 destinos locais resolvidos, recibos atuais e diff sem erros
  de whitespace. Os 23 caminhos alterados pertencem à submissão; arquivos brutos
  e caches não aparecem no diff. Os 13 arquivos novos foram registrados apenas
  com intenção de adição para ficarem visíveis, sem preparar conteúdo para commit.
- A orientação de leitura/auditoria da skill de planilhas foi consultada na
  conferência de unidades, fontes e ausências. A entrega solicitada é código e
  evidência de auditoria; nenhum workbook foi criado ou alterado.
- Recibo dependente das entradas em `docs/review-evidence/data-audit-current.json`;
  recibo da fundação revalidado após atualizar seus documentos operacionais.

Não houve treino, ajuste de prompt, avaliação de IA, criação de split, diagnóstico
operacional final, medição de economia, decisão de stack, commit ou publicação.

## Estado e próxima ação

D01 concluída com os arquivos efetivos, não apenas com a descrição do Kaggle.
D02 deverá definir papéis complementares e métricas válidas, sem um join artificial
ou transferência não validada da taxonomia IT. V00 continua obrigatório antes de
implementar e selecionar modelos/limiares.

## Cobertura das conversas

Captura 10: seis mensagens adicionais de dois turnos retornados; `hasMore=true`
para histórico anterior fora da página. Inclui o final da revisão antes do commit
e as mensagens disponíveis da D01. A resposta final desta etapa e mensagens
posteriores à captura continuam pendentes, sem reconstrução como citação.
