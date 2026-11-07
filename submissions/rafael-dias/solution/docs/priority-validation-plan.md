# Comparativos e casos de aceitação — saúde e prioridade

Pesquisa e comparação exploratória em 06/11/2026. A aplicação continua com o comportamento anterior. Este material prepara a implementação; não comprova aumento de vendas.

## O que existe no repositório oficial

A [pasta do Challenge 003](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/tree/main/challenges/build-003-lead-scorer) consultada lista o README. O briefing exige dados reais, prioridade além do valor, explicação e software funcional; não fornece pesos oficiais, casos rotulados ou um benchmark numérico de conversão. O README geral menciona respostas de referência geradas por IA, sem apresentar nessa pasta uma bateria executável para nosso modelo.

Essa conclusão é limitada aos documentos e à pasta oficial consultados; não é uma auditoria de todos os forks, submissões ou PRs de candidatos. Não precisamos copiar soluções de candidatos para construir a comparação.

## Referências práticas encontradas

| Referência | Caso/prática encontrada | Como adaptar |
|---|---|---|
| [Salesforce Admins — uso de Opportunity Scoring](https://admin.salesforce.com/blog/2021/what-you-can-do-with-einstein-opportunity-scoring) | Exemplo ilustrativo de negociação avançada, valor alto e score 19; também discute oportunidade inicial com score alto. | Testar se valor/estágio mascaram risco e se uma compra inicial com evidência pode ganhar atenção. Não adotar os cortes 19/80 como nossos. |
| [HubSpot — testar registros e distribuição](https://knowledge.hubspot.com/scoring/test-records-in-scoring-tools) | Verificação individual dos pontos e prévia da distribuição na base. | Validar cenários de aceitação e, separadamente, composição do top 5/top 20. |
| [Gong — configurações de alertas](https://help.gong.io/docs/customize-your-deal-warning-settings) | Distingue falta de atividade e falta de participação do comprador; alerta também sobre decisor e estagnação. | Diferenciar tentativa de conversa real; testar recência, bloqueios e ausência de decisor. Seus limites são contextuais, não regras oficiais para este dataset. |
| [HubSpot Community — auditar, iterar e visualizar](https://community.hubspot.com/t/contact-engagement-score-audit-iterate-visualize-score/125172) | Participante pede auditoria de registros e contribuição dos fatores; resposta aponta teste individual. | Guardar versão, razões e data do score. É relato comunitário, não estudo de impacto. |
| [Microsoft — desempenho de modelos](https://learn.microsoft.com/en-us/dynamics365/sales/scoring-model-accuracy) | Discute avaliação com resultados conhecidos, incluindo precision/recall/AUC e registros recentes de teste. | Só usar métricas preditivas quando existir população de teste com entradas válidas e resultados posteriores. Não chamar nossa comparação descritiva de acurácia. |

Os cenários abaixo são construídos por nós a partir desses princípios e dos limites do projeto. Não são relatos de clientes reais nem casos rotulados pelo G4.

## Regras de referência

| Regra | Definição | O que testa |
|---|---|---|
| R0 — Score v1 | Ordenar pelo score histórico atual; empate por ID. | Ponto de partida para detectar mudança, sem presumir que esteja correto. |
| R1 — Maior preço | Preço unitário de catálogo decrescente, empate por ID. | Quanto a seleção depende do potencial financeiro aproximado. Não é orçamento ou receita esperada. |
| R2 — Mais antiga | Maior tempo desde `engage_date` até 31/12/2017; datas ausentes por último. | Se uma regra simples vira uma fila de negócios possivelmente parados. Não é FIFO: não há data de criação. |
| R3 — Mais recente | Menor tempo desde `engage_date`; datas ausentes por último. | Se a seleção favorece negociações mais novas e abandona casos antigos recuperáveis. Não é último contato. |
| R4 — Estágio | Engaging antes de Prospecting; empate por ID. | Se o score acrescenta algo ao estágio isolado. |
| R5 — Espaço para descoberta | Reserva experimental `ceil(n/5)` vagas para Prospecting entre `n` selecionados; completa com o score v1. Se faltar prospecção, completa normalmente. | Viabilidade de não deixar toda a prospecção para depois. É hipótese de capacidade, não cota ótima comprovada. |
| R6 — Compromisso primeiro | Ações vencidas primeiro; depois ações já devidas. Compromissos futuros continuam na agenda. | Cumprimento operacional. Depende dos eventos novos, ausentes no snapshot original. |
| R7 — Checklist simples | Contar evidências atuais de necessidade, decisor, prazo, resposta e próximo passo aceito, com limites de recência e desconhecido separado de negativo. | Referência simples para comparar com a saúde ponderada 40/25/25/10 no piloto. Ainda não calculável no histórico. |

R1/R2/R3/R4 são comparadores deliberadamente simples, escolhidos por nós. As fontes fundamentam os sinais e a necessidade de avaliação; não afirmam que essas fórmulas sejam padrão de mercado ou melhores.

## Comparação executada no snapshot

Reprodução: `node scripts/compare-priority.mjs 5` e `node scripts/compare-priority.mjs 20`.

População comum: **664 abertas com conta identificada**, distribuídas em **27 carteiras**. As outras **1.425 abertas** continuam relevantes, mas exigem identificação e não entraram nessa comparação de abordagem. Carteiras, população, capacidade e desempate são iguais entre regras. Não misturamos vendedores nem completamos filas com oportunidades de outra carteira.

Por carteira, selecionar até `k`. No top 5 são **133 selecionadas**, pois uma carteira elegível tem apenas três; no top 20 são **487**, pois nove carteiras têm menos de vinte identificadas. A base original tem 35 vendedores, dos quais oito não têm abertas.

### Top 5 por carteira — composição agregada

| Regra | Prospecção | Preço médio unitário de catálogo (USD) | Acima de dois ciclos históricos | Maior concentração em um produto |
|---|---:|---:|---:|---:|
| R0 Score v1 | 1,5% | 5.031,5 | 77,4% | 26,3% |
| R1 Maior preço | 17,3% | 5.891,4 | 78,9% | 46,6% |
| R2 Mais antiga | 1,5% | 2.484,6 | 98,5% | 21,1% |
| R3 Mais recente | 1,5% | 2.418,4 | 75,9% | 21,8% |
| R4 Estágio | 1,5% | 3.262,7 | 95,5% | 18,8% |
| R5 Descoberta | 8,3% | 5.140,3 | 70,7% | 27,8% |

“Acima de dois ciclos” é um alerta de revisão baseado no tempo desde negociação e na referência histórica do produto. Não significa que a oportunidade foi perdida. O denominador é toda a seleção; idade desconhecida não entra como ciclo excedido. A idade média nos arquivos considera apenas idades conhecidas.

### Leitura dos resultados

- Ordenar pelo maior preço concentra **46,6%** das selecionadas em um único produto, contra **26,3%** no v1. Isso pode ser uma preferência de negócio, mas não comprova propensão de compra.
- A regra mais antiga gera **98,5%** acima de dois ciclos. Serve como comparador de resgate, dificilmente como única fila de abordagem.
- No top 5, o v1 dá **1,5%** de espaço à prospecção. Ela só entra quando faltam negociações identificadas suficientes. Há espaço para experimentar uma fila de descoberta sem alegar que todos os prospects são bons.
- A reserva experimental aumenta esse espaço para **8,3%**, e não 20% globalmente: apenas dez carteiras têm prospecção identificada disponível. A política não fabrica demanda nem transfere leads.
- Ao inverter somente o desempate por ID, a sobreposição média com o top 5 atual é **77,8% por carteira**. Isso evidencia empates na fronteira; não prova erro, mas recomenda explicações e revisão de casos empatados. Não inventar casas decimais para disfarçar a falta de sinais.
- No top 20, a sobreposição média entre preço e score v1 sobe a **90,4%**, em parte porque várias carteiras têm poucos candidatos. Comparar só o top 20 esconderia diferenças relevantes no primeiro bloco de cinco.

Não há aqui comparação da fila completa com rodadas, retornos e contatos reais. É um recorte estático da pontuação inicial, anterior à execução. Tampouco calculamos acurácia ou ganho de vendas: não existem resultados futuros das abertas nem os sinais históricos de saúde necessários.

Arquivos auditáveis: [top 5](priority-comparison-top5.json) e [top 20](priority-comparison-top20.json), com hash do snapshot, critérios, resumo e IDs selecionados por carteira.

## Casos para aceitar a implementação

Relógio controlado nos testes, sem alterar o computador do usuário. Pessoas, propostas e sinais abaixo são fictícios. Os resultados esperados são decisões de produto propostas, ainda a implementar.

| Caso | Situação | Resultado esperado |
|---|---|---|
| C01 | Negócio caro, etapa avançada e comprador sem responder há muito tempo | Exibir risco e ação de resgate; preço não torna a saúde verde. |
| C02 | Negócio menor com resposta recente e compromisso vencido | Entrar antes de um negócio maior que está aguardando retorno futuro. |
| C03 | Dez tentativas sem resposta | Não equivaler a dez sinais de interesse; não renovar data da última resposta. |
| C04 | Cliente respondeu, confirmou necessidade e pediu proposta | Destacar avanço pendente, inclusive se o estágio ainda é inicial. |
| C05 | Vendedor marcou retorno, cliente não confirmou | Tarefa existe; aceite bilateral continua ausente, sem pontos de aceite. |
| C06 | Retorno para daqui a sete dias, sem outro sinal urgente | Permanecer na agenda, sem incentivar contato antecipado. |
| C07 | Retorno vence depois de o plano diário já ter sido criado | Entrar no foco acima das rodadas; rodadas não bloqueiam urgência. |
| C08 | SQL preenchido há muito tempo e silêncio atual | Não manter verde apenas pelo preenchimento; pedir reconfirmação. |
| C09 | Proposta enviada, orçamento/condições explicitamente bloqueados | Risco financeiro visível, mesmo com qualificação e nota bruta altas. |
| C10 | Cadastro incompleto ou evento legado sem resposta estruturada | “Em validação”; não inferir rejeição nem resposta confirmada. |
| C11 | Só acrescentar uma nota interna | Não melhorar participação nem reiniciar recência do comprador. |
| C12 | Mesma evidência importada duas vezes | Não duplicar pontos ou contato real; preservar identidade do evento. |
| C13 | Cliente pede pausa até uma data específica | Respeitar pausa na fila comum; contato imediato só por outro motivo explícito. |
| C14 | Negócio encerrado | Sair da fila ativa e do health score, preservando histórico/resultados. |
| C15 | Alterar `close_value` do próprio negócio em um teste de aberta | Não alterar a prioridade histórica/saúde pré-fechamento. |
| C16 | Falta `engage_date` | Tempo desconhecido, sem idade inventada e sem rótulo de “recente”. |
| C17 | Mesmo negócio, apenas nome da conta ou vendedor diferente | Saúde não muda por nome. A carteira muda de escopo se o responsável mudar. |
| C18 | Duas oportunidades da mesma conta, interações distintas | Calcular evidência por oportunidade; resposta de uma não aquece automaticamente a outra. |
| C19 | Interação antiga lançada hoje | Usar data de ocorrência para recência; manter data de registro para auditoria. |
| C20 | Troca do corte temporal ou leitura de dados futuros | Ignorar evidências posteriores ao corte e guardar versão do cálculo. |

Casos C12, C13 e C20 exigem campos/políticas adicionais: identificador de evidência, pausa explícita e reconstrução no tempo. Não declarar suporte antes de implementar e testar esses contratos. C13 não pode ser inferido apenas de uma nota ambígua. A bateria amplia o estudo anterior com requisitos de idempotência, pausa e auditoria temporal.

## Como comparar as decisões

Além dos casos isolados, usar pares:

- **P1:** C02 contra C06 → cumprir o compromisso vencido primeiro.
- **P2:** C04 contra C01 → avanço real pode preceder alto valor sem resposta, salvo urgência contratual explícita.
- **P3:** C03 contra conversa recente equivalente → participação do comprador diferencia a saúde; volume de tentativas não compensa.
- **P4:** C10 contra rejeição explícita → desconhecido e negativo têm rótulos distintos.
- **P5:** C07 contra o primeiro cliente da rodada → a ação urgente não depende do checkpoint.
- **P6:** duas compras equivalentes em urgência/evidências, valores verificados distintos → potencial pode desempatar, comparando mesma moeda e unidade. Não comparar orçamento total com catálogo unitário como se fossem iguais.

Não precisamos fixar uma nota exata antes de definir todos os detalhes dos pesos e da cobertura. Primeiro validar essas relações e invariantes; depois verificar pontos, faixas e explicações da função escolhida.

## Critérios para avançar

1. Implementar e passar os 20 casos e os seis pares aplicáveis, explicitando os campos ainda sem suporte. Requisito de negócio crítico falhando bloqueia ativação; não fazer média para esconder falha de urgência ou vazamento.
2. Garantir que cada recomendação tenha motivo, origem e ação; dados desconhecidos preservam esse estado.
3. Comparar top 5 e top 20 por vendedor com a mesma capacidade. Separar alterações causadas por dados novos das causadas por fórmula.
4. Fazer revisão humana de uma amostra estratificada (por exemplo, 30 oportunidades e seis pares, como ponto de partida operacional, sem alegar significância estatística). Registrar desacordos e justificativas; não foi realizada nesta pesquisa.
5. Só depois iniciar piloto de resultado com janela/coorte definidas previamente, registrando score antes da ação. Medir resposta real, avanço verificado, cumprimento de retorno e ganho posterior. Se usar ganho em H dias, definir o tratamento dos negócios ainda abertos.

Os números 30, seis pares, a reserva de descoberta e os pesos do estudo anterior são escolhas iniciais a revisar. Uma regra não fica validada só porque satisfaz casos escritos por quem a projetou: esses casos verificam coerência; revisão independente e resultados posteriores verificam utilidade.

## Próxima implementação recomendada

Começar pela urgência e pela coleta estruturada de resposta/aceite. Depois implementar saúde versionada e executar os casos. Valor orçado, pausa, idempotência e auditoria temporal entram com contratos claros e compatibilidade dos eventos antigos, sem reescrever ou apagar o histórico.

O script desta pesquisa não é importado pelo aplicativo e não modifica scoring, dados, atividades do navegador, pesos ou layout.
