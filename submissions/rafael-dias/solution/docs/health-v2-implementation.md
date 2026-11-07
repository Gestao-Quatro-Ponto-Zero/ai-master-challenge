# Saúde comercial v2 — implementação do piloto

Ativação local em 06/11/2026. Versão `health-v2.0`. As regras foram verificadas por cenários e testes, mas ainda não há medição de impacto em conversão. A pesquisa e os comparativos anteriores permanecem como registro do desenho, não como resultados preditivos.

## O que mudou

- Nota da base de 2017 continua como referência histórica, sem recalcular retrospectivamente o dataset.
- Saúde ativa é calculada em `lib/health.mjs`, separada da prioridade operacional de `lib/priority.mjs`.
- Resposta do cliente, aceite do próximo passo e condições financeiras passaram a ter campos próprios. Não se deduzem esses sinais de notas ou eventos antigos.
- Formulário aceita valor total opcional de proposta em USD. Histórico e card distinguem proposta informada de preço unitário do catálogo. O valor fechado continua apenas em Resultados.
- Cliente pode pedir pausa com data futura. O negócio permanece acessível no pipeline, sai da fila de contato e reaparece no vencimento. Conversa confirmada posterior pode encerrar a pausa.
- Eventos mantêm data de ocorrência e registro, origem declarada, versão do esquema e versão da política. A leitura desconsidera evidência futura e efeitos duplicados por identificador, sem apagar os eventos salvos.

## Política ativa

| Componente | Pontos |
|---|---:|
| Necessidade / decisor / prazo | 15 / 15 / 10 |
| Resposta recente / atualidade | 15 / 10 |
| Próximo passo aceito / data válida | 15 / 10 |
| Viabilidade financeira | 10 |

Janela de resposta: sete dias corridos. Atualidade vale dez até sete dias, cinco até quatorze e zero depois. O componente de resposta deixa de somar depois de sete dias. Tentativas não renovam a última conversa. Uma primeira tentativa sem resposta não gera automaticamente alerta de silêncio prolongado; o alerta usa a janela observada desde a tentativa inicial ou desde a última conversa confirmada.

Qualificação perde pontos após trinta dias sem reconfirmação. Compatibilidade financeira perde pontos após trinta dias; bloqueio financeiro não desaparece silenciosamente por envelhecer. As condições conhecidas podem ser atualizadas em outro registro de proposta. Nesta versão, não há revogação granular dos três campos de SQL: reconfirmação e mudança das informações passam pelo registro de qualificação; um bloqueio pode ser descrito e registrado como perda quando cabível.

Só se exibe nota numérica quando há conversa confirmada documentada e pelo menos 70% de cobertura dos critérios. Sem isso, a saúde fica em validação; riscos observados ainda aparecem. Cobertura representa informação disponível, não confiança estatística.

Verde exige ao menos 80 pontos, cobertura de 85%, conversa recente, qualificação atual e próximo passo aceito/válido, sem risco. Um bloqueio financeiro, retorno vencido, silêncio prolongado ou qualificação antiga impede verde mesmo com soma alta. O detalhamento mostra pontos confirmados e critérios desconhecidos; não normaliza poucos campos para 100.

Os pesos e janelas são hipóteses iniciais. Centralizados em `HEALTH_POLICY` para parâmetros temporais/cobertura, e na composição de fatores de `calculateHealth` para pesos. Qualquer alteração exige versão, testes e revisão da explicação ao vendedor.

## Prioridade e rodadas

Ordem operacional: encerrados ficam fora; pausa vigente é respeitada; retorno vencido vem primeiro; resposta recente com avanço pendente vem depois; riscos/revisão precedem descoberta sem sinais atuais. Próximos compromissos futuros ficam na agenda.

Exceção deliberada: um bloqueio financeiro explícito pode entrar como **revisão interna da proposta**, mesmo antes do retorno futuro. O motivo orienta revisar condições sem antecipar contato. Ele não é apresentado como nova resposta do comprador.

Retornos vencidos, avanços atuais e bloqueios financeiros podem entrar no foco fora da rodada e mesmo depois de uma tarefa ter sido concluída. A seleção é limitada a cinco IDs únicos. Quando a rodada só contém casos aguardando/pausados, a tela pode mostrar outros elegíveis; isso não marca artificialmente as tarefas originais como concluídas. Uma pausa não conta como contato ou proposta executada.

Os checkpoints existentes foram preservados. Novas regras não apagam, aumentam ou reiniciam metas antigas. A reserva experimental de 20% para descoberta **não foi ativada**: continua como alternativa de capacidade a validar. A prospecção pode ganhar prioridade por evidência atual, sem depender do estágio histórico.

Valores de proposta desempatam dentro da mesma classe operacional. Propostas em USD formam um grupo explicitamente identificado; quando ambos os negócios têm proposta em USD, compara-se o total. Sem proposta, usa-se a referência histórica como desempate. Não comparar numericamente orçamento total com preço unitário ou moeda diferente.

## Compatibilidade

Envelope e chave `g4-sales-workspace-v2` permanecem. Novos eventos recebem `schemaVersion:3`; antigos não são regravados nem enriquecidos com supostas respostas/aceites. Por isso, uma saúde antiga de 100 pode passar a “Em validação”: o histórico continua lá, mas a regra nova exige evidência estruturada.

Novos campos estão documentados em `lib/contracts.mjs`. A versão original de código/documentação está em `.backups/health-v2-20261106-203448/`; o armazenamento privado do navegador não foi copiado nem apagado.

## Verificação

`tests/health-priority.test.mjs` cobre C01–C20 e P1–P6 do plano de validação, mais validações de entrada, foco de bloqueio financeiro fora da rodada, primeira tentativa sem resposta e corte temporal dos checkpoints. Os testes anteriores foram mantidos; expectativas da antiga saúde 80+20 foram atualizadas para não atribuir resposta a eventos legados.

Conferência de navegador: registro fictício de SQL com resposta e aceite produziu saúde 90/100 e 90% de cobertura; proposta fictícia de USD 1.000 com bloqueio financeiro produziu risco explícito mesmo com 90 pontos. Não houve comunicação ou negociação real. Os registros usados para QA são separados dos registros anteriores da outra origem do navegador.

Ainda faltam revisão independente com vendedores e piloto de resultado. Passar nos cenários mostra coerência das regras, não ganho de vendas comprovado. Publicação, autenticação e persistência compartilhada são etapas separadas.

Fechamento: 58 testes passaram, formatação aprovada e compilação de produção concluída. No navegador, a pausa retirou o negócio do foco e preservou agenda/histórico após recarregar. O histórico abre no topo após salvar. Checkpoints usam a data de ocorrência, com resolução de minuto do formulário, para não creditar lançamento retroativo como trabalho atual.

Revisão responsiva final: a 390 px, o formulário apresentou largura interna de 334 px e rolagem horizontal de 334 px; página com 380 px de conteúdo. Sem transbordamento horizontal. Captura do cenário fictício de risco em docs/screenshots/health-v2-risk.png.
