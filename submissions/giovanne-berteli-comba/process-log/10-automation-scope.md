# Escopo da triagem assistida — 02/11/2026

## Contexto e objetivo

O usuário pediu para avançar após o commit `b1ba3b6`. A S01 precisava escolher uma
automação e especificar o fluxo, saídas, handoff, falhas, anomalias e medidas de
sucesso, antes da V00 e da implementação. Os três recibos existentes passaram no
início; o diagnóstico e as decisões D02 foram o contexto da escolha.

## Colaboração com IA

Codex redigiu o [contrato técnico](../knowledge/solution-scope.md) e a
[proposta com fluxo](../docs/automation-proposal.md). Consultou documentação primária
de scikit-learn, Streamlit e sqlite3 para embasar a escolha. A
[captura 14](chat-exports/14-automation-scope-chat.md) preserva oito mensagens novas,
inclusive as mensagens pendentes da A01 e a troca sobre o nome do commit.

## Decisões do agente no escopo autorizado

- Uma triagem IT assistida: categoria/destino/motivo como sugestão, com confirmação
  humana obrigatória. Sem resposta automática ao cliente, ação comercial, alteração
  de acesso ou integração externa. O papel diagnóstico da base de clientes permanece.
- Python 3.12, scikit-learn Pipeline, interface local Streamlit e SQLite. O primeiro
  candidato aprendido é TF-IDF com regressão logística; ele não é um vencedor
  selecionado. A V00 ainda definirá candidatos, critérios e ambiente exato testado.
- Dois fluxos de tela: Triagem e Revisão/anomalias. O armazenamento durável será
  SQLite; session state da UI não servirá como histórico ou aprovação persistente.
- Três saídas: suggested, review_needed e failed. Entradas inválidas, contexto não
  suportado, falta de prontidão, nenhum vocabulário conhecido, score baixo,
  timeout/saída inválida e gravação malsucedida têm comportamento especificado.
- Anomalias de score/tamanho normalizado comparadas por domínio/categoria/versão.
  Quantis serão ajustados só na validação sob protocolo congelado. Menos de 100
  referências compatíveis produz não avaliado; não se inventa faixa normal.
- Persistir original, execução, duas avaliações de métrica e eventos de revisão;
  filtros combinados por direção/motivo/estado, sem duplicar totais de casos.
  Correção humana não sobrescreve valores originais ou alimenta treino/teste.
- O limite de 10 mil caracteres, timeout de 5 segundos, mínimo de referência e
  encaminhamento especializado são convenções de desenho, não resultados de
  desempenho ou políticas confirmadas por uma operação real.

As escolhas não foram rotuladas como aprovação humana adicional. O app local não
terá autenticação de papéis empresariais; operadores serão declarados e fixtures
serão identificadas como testes. O contrato não infere revisão humana verificada
a partir de um rótulo ou de um agente interagindo com a interface.

## Alternativas e revisão da especificação

Foram descartados LLM remoto/respostas geradas, API separada, dashboard e
integração de helpdesk nesta etapa: não são necessários para testar a classificação
com revisão e anomalias. O texto dos tickets continua dado, não instrução executável.

A revisão encontrou uma inconsistência de enumeração: o texto permitia adiar a
avaliação de uma anomalia, mas a lista de estados não incluía deferred. A lista
foi corrigida. Também ficou explícito que contexto fora de IT pode aceitar/adiar
handoff sem forçar uma categoria IT. Uma tentativa de patch foi rejeitada por um
trecho não correspondente; o patch corrigido foi aplicado sem alteração parcial.

## Evidências e limites

O [registro de checagens](../docs/review-evidence/solution-scope-checks.json) identifica
fontes consultadas, cobertura da revisão e comandos executados. Os 29 testes
existentes passaram: são testes dos cálculos/software anteriores, não dos fluxos
S01 ainda inexistentes. Não foram adicionados testes que apenas espelham a redação.

Auditoria, JSON de diagnóstico e CSV de segmentos foram regenerados e permaneceram
idênticos. Donos operacionais, plano, status e fonte oficial F02/F03 foram atualizados;
recibos revalidados. Os caminhos futuros de banco/modelos foram adicionados ao
ignore local; não houve criação de banco, modelo ou interface.

## Estado e próxima ação

S01 concluída como especificação. V00 deve congelar membership, riscos de
duplicatas, limitações de entrada, custos dos erros, candidatos, critérios de
escolha/aceite e procedimento de referência, além de preparar dependências exatas.
I01 implementará e ajustará parâmetros em desenvolvimento/validação; V01 usará o
teste reservado. Não houve instalação de dependências, treino, validação da nova
automação, medição de latência, deploy, commit ou publicação.

## Cobertura das conversas

Captura 14: oito mensagens novas extraídas de quatro turnos retornados após
deduplicação; `hasMore=true` para histórico anterior fora da página. Mensagens
posteriores e a resposta final desta S01 permanecem pendentes, sem reconstrução.
