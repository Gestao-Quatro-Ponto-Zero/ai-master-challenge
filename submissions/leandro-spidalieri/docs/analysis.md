# Diagnóstico e decisão de operação

**Decisão proposta ao diretor de operações.** Instrumentar o trabalho de triagem e testar sugestões de fila em um piloto controlado, com confirmação do atendente. A base de suporte mostra onde há volume para observar o processo. O corpus de TI mostra que a classificação temática funciona sob condições de teste e que ainda produz erros relevantes para a operação.

## Onde investigar a carga

O snapshot do Kaggle tem **8.469 tickets**, um por ID após a auditoria. O estoque na fotografia é de **5.700 (67,3%)**, dos quais 2.819 estão abertos e 2.881 aguardam o cliente. Faltam idade do ticket e SLA, portanto o status não mede atraso. O volume anual de 30.000 pertence ao cenário do desafio. [Manifesto](../solution/artifacts/manifest.json) · [Cubo de diagnóstico](../solution/artifacts/diagnosis.json).

| Corte | Maior volume | Tickets | % do snapshot |
|---|---|---:|---:|
| Canal | Email | 2.143 | 25,3% |
| Prioridade | Medium | 2.192 | 25,9% |
| Tipo | Refund request | 1.752 | 20,7% |
| Canal × prioridade | Phone × Medium | 595 | 7,0% |
| Canal × tipo | Social media × Technical issue | 465 | 5,5% |

Os canais variam de 2.073 a 2.143 tickets. A carga é distribuída. Em **Social media × Technical issue**, 313 dos 465 tickets estão abertos ou aguardando o cliente. Isso torna o recorte adequado para observar a triagem e verificar o que chega por esse canal. A intensidade de esforço e a fila mais lenta continuam desconhecidas. As participações dividem as contagens do corte pelo total de 8.469 tickets. [`diagnosis.json`, campos `cubo` e `cortes`](../solution/artifacts/diagnosis.json).

### Tempos e desperdício

O CSV contém timestamps sem fuso em `First Response Time` (5.650 preenchidos) e `Time to Resolution` (2.769 preenchidos). Não há evento de abertura. Dos **2.769 pares completos, 1.365 (49,3%)** têm o segundo timestamp anterior ao primeiro e 2 são iguais. A data de compra é um evento distinto. Sem semântica temporal validada, FRT, TTR, intervalo parcial, tendência e horas desperdiçadas ficam indisponíveis. O cálculo de auditoria compara os dois campos como timestamps, sem usar a diferença como métrica de desempenho. [`diagnosis.json`, `qualidade.tempo`](../solution/artifacts/diagnosis.json).

O texto também exige cautela. Todas as 8.469 descrições têm placeholder entre chaves, há 403 repetições excedentes após normalizar caixa e espaço e um mesmo prefixo de 80 caracteres aparece 189 vezes. Há 16 assuntos distintos e 2.769 resoluções preenchidas, das quais 18 têm menos de 15 caracteres. São sinais de uso de templates. A autoria, a representatividade e a validade das resoluções como política operacional seguem sem confirmação. A auditoria de padrões encontrou e-mails, URLs e sequências numéricas em descrições e reteve apenas contagens. [`diagnosis.json`, `qualidade.texto`](../solution/artifacts/diagnosis.json).

## O que a satisfação permite comparar

Existem **2.769 notas válidas (32,7% dos tickets)**, todas de tickets fechados. Entre elas, **1.087 (39,3%)** são 4 ou 5. A mediana ordinal é 3 e a distribuição é 553, 549, 580, 543 e 544 nas notas 1 a 5. Entre os fechados, a cobertura é de 100% no arquivo. Entre abertos e pendentes, é zero. O resultado se refere aos fechados e o mecanismo de geração dessas notas é desconhecido.

| Corte | Menor % de notas 4–5 | Maior % de notas 4–5 |
|---|---|---|
| Canal | Social media, 256/684 (37,4%) | Chat, 280/674 (41,5%) |
| Prioridade | Medium, 258/694 (37,2%) | Low, 274/644 (42,5%) |
| Tipo | Technical issue, 215/580 (37,1%) | Billing inquiry, 227/544 (41,7%) |

A mediana é 3 em todos os grupos unidimensionais desses três cortes. O recorte Social media × Technical issue tem 46/152 notas 4–5 (30,3%). É um ponto de investigação entre várias comparações. Composição dos fechados, cobertura no total e seleção dos grupos podem explicar diferenças. A associação com resposta não é estimável e os dados não permitem atribuir causalidade. Na interface, grupos com menos de 30 notas são sinalizados. [`diagnosis.json`, `cortes` e `satisfacao_por_status`](../solution/artifacts/diagnosis.json).

## Três frentes, em ordem de execução

| Evidência | Ação | Risco e medida necessária |
|---|---|---|
| 5.700 fora de Closed e 1.365 pares invertidos | Instrumentar abertura, primeira resposta, mudança de fila, espera e fechamento | Confirmar a origem dos eventos e registrar tempo ativo separado da espera. Medir cobertura, inversões e idade por fila. |
| 465 chamados técnicos em redes sociais e concentração fraca entre canais | Observar o recorte e depois testar sugestão temática com taxonomia local | Corpus de TI é outro domínio. Rotular tickets na entrada e medir cobertura, taxa de fila incorreta e minutos ativos. |
| 1.752 pedidos de estorno e 1.695 de cancelamento | Separar tema, risco e autorização no processo | Benefício dessas ações não é mensurável. Manter verificação de política, identidade e decisão com responsável humano. |

A ligação entre os arquivos é operacional. O Dataset 1 delimita volume e risco para escolher o que medir. O Dataset 2 demonstra uma capacidade de classificação fora do treino em TI. Para transferi-la ao suporte ao consumidor, é preciso um conjunto rotulado na taxonomia local e avaliação reservada nesse domínio. As classes, populações e chaves diferem, e a cobertura experimental de 83,9% não entra no simulador operacional. [Avaliação de TI](../solution/artifacts/evaluation.json).

## Fluxo proposto e autoridade

O fluxo atual do case foi descrito em nível de canais e estados. A sequência interna de ações do agente é desconhecida. No piloto, validar a entrada, minimizar dados pessoais, registrar domínio e preservar a prioridade de origem. Aplicar as guardas antes da sugestão. Exibir a categoria e o motivo ao atendente, que escolhe a fila final. Registrar categoria sugerida, fila confirmada, correção, tempos ativos e desfecho. Revisar os erros por lote e aprovar mudanças de regra antes de reaplicar. O protótipo executa classificação e guardas localmente, sem integração nem gravação do histórico de operação.

| Ação | Evidência e condição | Responsável e fallback | Controle |
|---|---|---|---|
| Sugerir tema e fila | Domínio validado no piloto, vocabulário compatível e score acima do limiar com guardas satisfeitas | Atendente confirma ou corrige. Sem evidência suficiente, usa fila manual. | Cobertura, acerto por classe e reencaminhamento |
| Priorizar crítico e tratar incidentes | Prioridade de origem crítica ou sinal de incidente | Responsável de plantão. A prioridade informada é preservada. | Tempo até revisão e falsos negativos de risco |
| Conceder acesso, estornar ou cancelar | Direitos, identidade, política vigente e autorização verificável | Responsável autorizado decide e executa. Encaminhar para verificação humana. | Erros por classe sensível, aprovações e incidentes |
| Enviar resposta ao cliente | Base aprovada, resposta rastreável e revisão conforme risco | Atendente redige e valida. | Correções, reincidência e satisfação |

Exemplos do Dataset 1 por ID, com atributos estruturados apenas. O ticket 8 é um pedido de estorno crítico em Social media, aberto. O 11 é um pedido de cancelamento de prioridade alta por telefone, fechado. O status não documenta autorização ou execução. No teste de TI, **46 de 246** registros rotulados `Administrative rights` receberam sugestão para outros temas, incluindo o ID derivado `028b4da669f61fb2f695` previsto como Hardware. Regras de palavras e categoria prevista deixam passar parte dos casos sensíveis. Isso fundamenta a confirmação humana de todas as sugestões durante o piloto. [CSV de origem e hash](../solution/artifacts/manifest.json) · [Casos e métricas de TI](../solution/artifacts/evaluation.json).

## Impacto projetado

| Cenário hipotético | Triagens assistidas/mês | Horas líquidas/mês | Valor líquido da capacidade/mês | Caixa líquido/mês |
|---|---:|---:|---:|---:|
| Conservador | 210 | 3,15 h | R$ 39,00 | −R$ 150,00 |
| Base | 600 | 18,00 h | R$ 930,00 | −R$ 150,00 |
| Otimista | 1.096,9 | 38,03 h | R$ 2.131,50 | −R$ 150,00 |

Leandro confirmou a apresentação do cenário base de 18 h/mês ao lado do conservador de 3,15 h/mês, ambos como hipóteses, com 0% de conversão em caixa. O volume de 2.500/mês assume os 30.000 tickets/ano do case distribuídos uniformemente. Elegibilidade é a parcela do volume na triagem em teste. Cobertura é a fração dos elegíveis que recebe sugestão. Adesão é a fração das sugestões usadas. O cenário base usa 50%, 60% e 80%, respectivamente. Os parâmetros são premissas para medir no piloto. [Premissas e resultados completos](../solution/artifacts/impact.json).

Horas líquidas são as triagens assistidas multiplicadas por minutos antes menos minutos depois, revisão e retrabalho esperado, divididas por 60. O cálculo atribui a tickets fora do fluxo assistido o custo ativo do processo manual. Se houver sobrecusto de manuseio de abstinência ou de sugestões descartadas, medir separadamente antes de usar a projeção. Os custos de IA configuráveis abrangem todas as chamadas cobradas, inclusive rejeições e repetições. O P0 local não faz chamadas cobradas. O cenário soma um único ganho de triagem, sem sobrepor roteamento e resolução.

No cenário base são 600 × (4 − 1,5 − 0,5 − 0,05 × 4) ÷ 60 = 18 h/mês. A 50% e 70% de cobertura, com o resto fixo, são 15 e 21 h/mês. A R$ 60/h, o valor de capacidade é R$ 1.080/mês. Deduzidos R$ 150/mês recorrentes, restam R$ 930/mês de valor de capacidade. Caixa tem conversão inicial de 0%. Só preencher uma fração positiva se houver um mecanismo defensável, como evitar hora extra comprovada. Com R$ 1.500 de implantação, o caixa hipotético em 12 meses é −R$ 3.300 no cenário base. ROI de 12 meses divide caixa líquido anual pelo custo anual recorrente mais implantação. Payback divide implantação pelo caixa líquido mensal e só é exibido quando este é positivo. [Código do simulador](../solution/src/supportops/impact.py).

## Protocolo de piloto

**Decisão.** Leandro propõe testar a coleta em chamados técnicos de redes sociais e comparar os quatro canais antes de intervir. Antes do piloto, a liderança de suporte define janela, amostra por recorte, cobertura mínima dos registros, ganho mínimo de tempo e limites de erro de fila e segurança.

| Fase | O que fazer | Quando avançar |
|---|---|---|
| **1. Testar a coleta** | Em Social media × Technical issue, confira a ordem dos eventos e os intervalos ativos observando uma amostra de atendimentos. | Corrija faltas e inversões e repita a coleta até atingir a cobertura acordada. |
| **2. Comparar canais** | Use a mesma janela em Email, Chat, Phone e Social media. Entre tickets de tipo e prioridade semelhantes, compare volume, tempo ativo, espera e reencaminhamentos. Informe tamanho e cobertura por recorte. | Escolha a fila onde a carga e o esforço ativo medido justificam testar a intervenção. Com amostra insuficiente, amplie a medição. |
| **3. Avaliar em modo sombra** | Gere sugestões ocultas dos atendentes e compare com a fila validada por um revisor que desconhece a previsão. Audite os críticos e sensíveis identificados por pessoas e uma amostra aleatória de sugestões e abstinências. | Passe à assistência se a qualidade atingir os limites acordados e a revisão humana cobrir os riscos identificados. Se um caso sensível escapar dessa revisão, ajuste a regra e reteste em nova amostra. |
| **4. Comparar assistência com rotina manual** | Sorteie tickets elegíveis entre triagem manual e assistida dentro de canal e prioridade. Se houver influência entre atendentes, sorteie e analise equipes ou blocos de turno. O atendente confirma cada sugestão. | Amplie se a redução de tempo atingir o ganho mínimo e o reencaminhamento ficar dentro da margem acordada. Pause e investigue casos críticos sem revisão ou ações sensíveis sem autorização. |

**Registro mínimo por ticket.** Guarde ID pseudonimizado, canal, tipo, prioridade na entrada e grupo de teste. Use carimbo com fuso padronizado para abertura, primeira resposta, troca de fila, fechamento e início, pausa, retomada e fim do trabalho ativo. Registre filas sugerida e escolhida e motivos de correção.

**Leitura do piloto.** Some os minutos ativos de triagem, revisão e retrabalho e divida pelos tickets com medição válida de cada grupo. Inclua abstinências e sugestões descartadas. Informe a cobertura sobre todos os tickets alocados. Entre os tickets com rota rastreável, calcule a proporção com correção de fila na janela. Compare espera separadamente. Com cobertura desigual ou resultado inconclusivo, amplie a coleta.

**Validação das horas.** Subtraia a média assistida da média manual, multiplique pelo volume mensal observado de elegíveis e divida por 60. As **18 h/mês** e **3,15 h/mês** continuam hipóteses até essa medição. A conversão em caixa parte de **0%**.
