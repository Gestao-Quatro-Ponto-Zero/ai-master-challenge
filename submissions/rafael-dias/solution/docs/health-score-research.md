# Estudo — prioridade e saúde comercial v2

Status: proposta para implementação e validação, não um modelo já comprovado. Pesquisa pública e auditoria do código/snapshot em 06/11/2026. Nenhuma regra do aplicativo foi alterada nesta etapa.

## Decisão recomendada

Manter uma fila única de trabalho para o vendedor, calculada a partir de três perguntas distintas:

1. **Potencial:** quanto este negócio pode representar e qual a evidência de adequação?
2. **Saúde:** há sinais atuais de que a compra está avançando?
3. **Urgência:** existe uma ação que precisa acontecer agora?

Valor alto não comprova saúde. Saúde baixa pode exigir resgate urgente. Um negócio saudável pode aguardar o retorno combinado. Por isso, não somar simplesmente os três conceitos numa nota única.

Na tela principal: uma orientação, um motivo e uma ação. O detalhe pode mostrar a composição, a origem e a data dos sinais.

## O que a pesquisa sustenta

| Fonte | Achado e aplicação proposta |
|---|---|
| [HubSpot — ferramenta de scoring](https://knowledge.hubspot.com/scoring/understand-the-lead-scoring-tool) | Separa perfil e engajamento, permite composição e perda de pontos com o tempo. Aplicação: não confundir porte da empresa com intenção atual. |
| [Gong — configurações de alertas](https://help.gong.io/docs/customize-your-deal-warning-settings) | Trata ausência de atividade, ausência de participação do comprador, decisor e estagnação como sinais diferentes. Limiares dependem de ciclo e estágio. Aplicação: alertas específicos e recência contextual. |
| [Salesforce — Opportunity Scoring](https://help.salesforce.com/s/articleView?id=sf.einstein_sales_opportunity_scoring.htm&language=en_US&type=5) | Expõe fatores favoráveis e desfavoráveis ao lado do score. Aplicação: explicar o que está ajudando, o que preocupa e o que fazer. Não importar a interpretação probabilística do produto para nossa heurística. |
| [HubSpot Community — Lead Score Decay](https://community.hubspot.com/t/lead-score-decay/58633) | Discussão de 2022 sobre retirar pontos quando o comportamento sai da janela temporal. Serve como exemplo de necessidade operacional; não como documentação atual do produto. |
| [HubSpot Community — score no Sales Workspace](https://community.hubspot.com/t/scoring-model-for-leads-and-sales-worksplace/126031) | Discussão de 2025 sobre tornar critérios e campos acessíveis no local de trabalho do vendedor. Aplicação: score precisa estar junto da ação, com informação consistente entre objetos. |
| [Fórum r/hubspot](https://www.reddit.com/r/hubspot/comments/1tcukat/how_are_you_actually_using_hubspot_lead_scoring/) | Participantes questionam pesos arbitrários, falta de perfil ideal e transparência. Relatos anedóticos, incluindo autor construindo ferramenta própria; não comprovam aumento de conversão. |
| [AWS — splits e vazamento](https://docs.aws.amazon.com/prescriptive-guidance/latest/ml-operations-planning/splits-leakage.html) | Avaliação precisa separar desenvolvimento/teste e respeitar o que estará disponível na previsão. Aplicação: resultados finais não podem virar sinais de uma oportunidade ainda aberta. |

Essas fontes justificam princípios de desenho. Nenhuma fornece pesos universalmente corretos para este CRM ou comprova efetividade da nossa proposta. Alegações promocionais e relatos de fórum não foram tratados como benchmarks.

## Auditoria do que temos

O snapshot preparado tem 2.089 abertas: 1.589 Engaging e 500 Prospecting. São 1.425 sem conta, aproximadamente 68,2% das abertas. A referência histórica é 31/12/2017; atividades atuais pertencem a outro relógio.

O score v1 gera apenas 21 notas distintas: Engaging varia de 62 a 95; Prospecting de 32 a 45. Portanto, toda negociação supera toda prospecção, independentemente de sinais atuais. Isso é uma consequência das regras, não evidência de que toda prospecção seja pior.

A saúde atual soma 80 por qualificação e 20 por compromisso futuro. Assim, preencher três campos e agendar pode produzir 100, sem distinguir resposta real, tentativa sem retorno ou compromisso aceito pelo comprador. Também não há deterioração por silêncio enquanto existir um retorno futuro. A regra é transparente, mas limitada.

### Como usar cada dado

| Informação | Disponibilidade | Uso defensável |
|---|---|---|
| Nome/ID da conta | Nome ausente em parte das abertas | Identificar, relacionar histórico e evitar duplicação. O texto do nome não ganha pontos. |
| Produto e preço de catálogo | Base original | Aproximação do potencial unitário; não chamar de valor orçado. Sem quantidade, não estimar valor total como preço × quantidade inventada. |
| Valor orçado/proposta vigente | Não existe na base original | Capturar valor, moeda, versão/data e validade da proposta, se informado pelo vendedor. Separar valor discutido de orçamento aprovado. |
| Valor fechado (`close_value`) | Encerramentos históricos | Receita realizada e resultados. Histórico de outras vendas anteriores ao corte pode apoiar referências, com cautela. Nunca usar o fechamento futuro do próprio negócio no score de aberta. |
| Estágio e data de negociação | Base original, com lacunas | Organizar fluxo e sinalizar necessidade de revisão. Sem histórico de transições, não afirmar tempo em cada estágio. |
| Setor, receita, funcionários, localização | Contas identificadas | Contexto e hipóteses de perfil. Empresa grande não significa intenção, orçamento ou boa adequação. Não presumir ICP do G4: o dataset representa outra operação comercial. |
| Histórico da conta | Derivado de encerramentos até o corte | Contexto de relacionamento, separado de interesse atual. Sem histórico não equivale a cliente ruim. |
| Vendedor, gestor, região | Base original | Carteira, filtros e análise de diferenças de distribuição. Não dar bônus por nome ou desempenho bruto do vendedor. |
| Necessidade, decisor e prazo | Registros manuais novos | Evidência declarada de qualificação, a ser atualizada quando o cliente mudar de posição. |
| Última resposta do comprador | Ainda não estruturada | Novo dado crítico. O tipo atual `contact` mistura conversa e tentativa; não inferir resposta apenas por existir um contato. |
| Próximo compromisso | Já existe como tarefa | Acrescentar se foi aceito pelo cliente. Agendamento unilateral não comprova compromisso bilateral. |
| Preço/orçamento/condições aceitos | Ainda não estruturado | Sinal de viabilidade comercial e alerta de bloqueio na fase de proposta. |

## Modelo proposto de saúde

Objetivo: representar evidência comercial atual, não probabilidade de ganho. A unidade é a oportunidade; duas oportunidades da mesma conta podem ter saúde diferente.

Pesos iniciais abaixo são hipóteses versionadas para piloto, não coeficientes estatísticos nem regras oficiais do G4.

| Dimensão | Máximo | Evidência necessária |
|---|---:|---|
| Qualificação | 40 | Necessidade confirmada: 15; decisor/processo de decisão confirmado: 15; prazo ligado a uma decisão real: 10. |
| Participação do comprador | 25 | Resposta/conversa confirmada na janela recente: 15; atualidade dessa interação: até 10. Tentativas, notas e envio unilateral não somam. |
| Próximo avanço | 25 | Próximo passo específico aceito pelo cliente: 15; data ainda válida: 10. Reagendar internamente não renova o aceite. |
| Viabilidade comercial | 10 | Condições financeiras explicitamente compatíveis com a compra; não apenas proposta enviada ou preço alto. |

### Recência e atualização

- Configurar uma janela `T` por estágio/ciclo. Para o primeiro piloto, testar 7 dias corridos como hipótese, com comparação contra janelas alternativas; não alegar que é o prazo ideal.
- Atualidade: 10 pontos até `T`, 5 até `2T`, zero depois; o componente de participação também expira se não houver interação do comprador dentro da janela definida. Envio repetido pelo vendedor não reinicia o relógio.
- Calcular com `occurredAt` (quando aconteceu), mantendo `recordedAt` (quando foi registrado), origem e oportunidade. Validar datas; não premiar lançamento tardio como resposta nova.
- Qualificação e viabilidade precisam registrar a última confirmação e ser invalidadas se surgir contradição. Definir prazo de reconfirmação no piloto; não manter uma necessidade confirmada indefinidamente.
- Quando o cliente não respondeu, isso é evidência observada. Quando o sistema não sabe se houve resposta, isso é informação ausente. Não transformar ausência de dados em rejeição.
- Encerrados saem da fila e não têm saúde ativa. O CRM de 2017 não pode ser apresentado como atividade recente em 2026.

### Confiança e informação ausente

Cada critério tem três estados: confirmado favorável, confirmado desfavorável ou desconhecido. A confiança mede cobertura dos critérios, não chance de venda.

Internamente, registrar `S` (pontos confirmados), `U` (máximo dos critérios desconhecidos) e `coverage` (peso conhecido / 100). O intervalo `[S, S+U]` indica o que ainda não sabemos; evita normalizar dois campos preenchidos para uma falsa nota 100.

Proposta inicial de apresentação:

- Sem interação atual documentada ou cobertura abaixo de 70%: **Em validação**, sem nota precisa. Um risco observado ainda pode ser alertado mesmo com baixa cobertura.
- Com cobertura suficiente: mostrar a pontuação conservadora `S/100`, explicitando se é parcial e o que falta confirmar. Isso mede evidências confirmadas, não estima a parte desconhecida.
- Verde somente com `S >= 80`, cobertura de pelo menos 85%, participação recente, qualificação comercial e compromisso válido, sem bloqueio crítico. Os limiares também precisam de validação.
- Risco crítico observado prevalece sobre uma soma alta: retorno vencido, bloqueio financeiro explícito ou decisão interrompida. Exibir o motivo; não ocultar o alerta atrás de uma nota.
- Pontuação baixa causada por lacunas deve aparecer como validação pendente, sem rotular o cliente como ruim. Uma classificação vermelha por soma só é defensável se mesmo o limite superior continuar baixo; o piloto deve definir o corte.

Os limites de cobertura são política proposta para a primeira versão. Se tornarem o uso pesado ou pouco informativo, simplificar com evidência de uso; não remover a distinção entre desconhecido e negativo.

## Fila de prioridade: política antes da fórmula

Ordenar por classes de ação, não por uma média que permita ao preço compensar um compromisso vencido.

1. **Retorno vencido / compromisso de hoje:** aparece acima das rodadas, independentemente de ter sido selecionado na abertura. Tarefa futura de hoje entra na agenda; não pressionar contato antes da hora combinada sem outro motivo.
2. **Avanço confirmado para agir:** resposta recente, necessidade conhecida, pedido de proposta ou decisão com prazo, com ação ainda pendente.
3. **Resgate de negociação:** silêncio, bloqueio ou estagnação observados; orientar o que validar e não prometer fechamento.
4. **Descoberta e qualificação:** primeiras conversas e prospecção em uma fila própria com espaço deliberado, sem ficar permanentemente atrás de Engaging.
5. **Completar identificação:** conta/contato ausentes; oportunidade continua existindo, mas pede outra ação.

Entre negócios da mesma classe, usar horário/prazo, evidência de avanço e potencial como desempate. Proposta aceita com valor verificado pode preceder uma de menor valor equivalente; catálogo deve ter rótulo de aproximação. Empates finais por ID mantêm estabilidade. Fechados e retornos futuros aguardando o combinado não entram como tarefas de contato imediato.

Rodadas são apenas apresentação da carga de trabalho. Não impedem uma ação urgente nem redefinem o score para forçar a meta.

## Coleta leve para o vendedor

Não criar um formulário de vinte campos. Aproveitar os registros existentes e adicionar controles contextuais:

- Ao registrar contato: **Houve resposta?** (`conversa confirmada`, `sem resposta`, `não informado`). Notas explicam o contexto, mas não substituem o campo estruturado.
- Ao agendar: **Cliente confirmou esse próximo passo?** (`sim`, `não`, `não informado`).
- Ao enviar proposta: valor/moeda vigente se conhecidos e **condições financeiras** (`compatíveis`, `há bloqueio`, `a confirmar`).
- SQL continua com necessidade, decisor e prazo. A nova saúde não altera silenciosamente o contrato de SQL nem torna orçamento um novo requisito obrigatório sem decisão explícita.

Cada evidência informa origem (declaração do vendedor ou CRM integrado), data e oportunidade. Declaração manual não deve aparecer como comprovação externa. IA pode sugerir extração da conversa, se houver autorização e dados, mas não confirmar automaticamente fatos que não foram verificados.

Registros antigos migram com campos novos desconhecidos. Não inferir resposta, orçamento ou aceite a partir do tipo `contact`, de notas ambíguas ou da existência de uma tarefa. Preservar eventos originais e versão do cálculo.

## Leitura rápida desejada

Exemplo fictício de interface, não resultado calculado da base:

> **Retomar agora** · retorno vencido há 1 dia
>
> Conta Alfa · proposta de US$ 8.000 informada pelo vendedor
>
> Saúde: atenção · o cliente respondeu, mas o próximo compromisso venceu.
>
> **Ação:** confirmar a decisão e combinar uma nova data.

Outro negócio pode ter maior valor e saúde melhor, mas retorno combinado só na semana seguinte: ele fica na agenda. A tela não precisa exibir três grandes números; a composição pode continuar no card.

## Como verificar efetividade

### O que podemos fazer agora

1. Criar casos de aceitação: contato sem resposta não melhora saúde; nota não reinicia recência; agendamento unilateral não cria aceite; prazo vencido entra acima das rodadas; registro legado fica desconhecido; venda não usa fechamento futuro como entrada.
2. Comparar composição do top 5/top 20 com preço, idade e regra atual. Medir concentração por produto/estágio, empates e sensibilidade ao variar pesos. Isso avalia comportamento da regra, não acerto de previsão.
3. Revisar uma amostra estratificada com vendedores/gestor, registrando motivo de concordância ou correção. Não selecionar só exemplos em que a proposta parece funcionar.

O dataset não possui respostas, propostas ou snapshots de qualificação históricos. Portanto, não permite provar retrospectivamente que o health score novo prevê ganho. Usar Won/Lost como se fossem estágios conhecidos antes de fechar, ou usar `close_value`, produziria uma validação enganosa.

Histórico de encerramentos pode apoiar análise descritiva e testes exploratórios com disponibilidade temporal explicitada. Atributos de contas sem versionamento e oportunidades ainda abertas exigem cautela; backtest completo continua indisponível.

### Evidência operacional futura

Registrar, antes de cada ação, versão do score, valores/razões, confiança, posição e conjunto de oportunidades elegíveis. Manter resultados posteriores separados. Sem isso, a avaliação pode usar informação futura ou medir apenas os negócios em que o vendedor decidiu trabalhar.

| Indicador | Definição e cuidado |
|---|---|
| Resposta por oportunidade trabalhada | Oportunidades com resposta do comprador / oportunidades com tentativa, no mesmo horizonte; não contar dez envios como dez interesses. |
| Avanço comercial verificado | Oportunidades com avanço confirmado / oportunidades trabalhadas; revisar evidência, não apenas preenchimento do mesmo campo usado no score. |
| Cumprimento dos retornos | Compromissos executados no prazo / compromissos vencendo no período. |
| Ganho no horizonte | Ganhas dentro de H dias / coorte elegível inicial. Negócios ainda em aberto ao final devem ter tratamento temporal explícito. |
| Receita por esforço | Receita realizada da coorte / horas comerciais registradas. Sem registro de esforço, não apresentar como produtividade medida. |
| Utilidade da fila | Concordância do vendedor, correções justificadas e tempo para escolher a próxima ação. Feedback ajuda a revisar, sem garantir causalidade. |

Comparar filas sob desenho de piloto que controle diferença entre vendedores/carteiras, contaminação e oportunidade trabalhada duas vezes. Definir horizonte, capacidade, tamanho de amostra e critério de sucesso antes de avaliar. Uma janela inicial de observação não equivale automaticamente a conclusão estatística; o ciclo mediano histórico geral é 45 dias, e ciclos variam por produto.

Não prometer aumento percentual de vendas antes dessa medição. Também não escolher pesos olhando repetidamente o resultado do mesmo conjunto de teste.

## Implementação sugerida após revisão

1. Introduzir esquema de evidências e compatibilidade de eventos legados.
2. Implementar cálculo puro/versionado de saúde com razões, cobertura e riscos; manter separado do score histórico.
3. Corrigir urgência na seleção da fila antes da lógica de rodadas.
4. Adicionar os controles contextuais e a orientação curta no card.
5. Executar casos automatizados, comparação de filas e revisão humana; ativar primeiro como piloto.

As pastas organizadas na refatoração permitem fazer isso sem reescrever telas ou persistência. Esta proposta ainda não foi ativada no aplicativo.


Auditoria numérica registrada em [health-score-audit.json](health-score-audit.json), com identificação e hash do snapshot. As observações sobre a saúde v1 foram verificadas em `lib/workflow.mjs`; nenhuma regra foi modificada.
