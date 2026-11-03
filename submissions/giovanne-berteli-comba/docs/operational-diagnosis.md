# Diagnóstico operacional — A01

> Registro da etapa indicada no título; suas referências a etapas seguintes são históricas.
> Para a versão atual e a demonstração, siga o [resumo da entrega](start-here.md).

**A primeira investigação deve olhar os registros não encerrados e a instrumentação
da operação, sem eleger um canal como causa do atraso.** Há 5.700 não encerrados
em 8.469 tickets (67,30%), incluindo 1.403 marcados como Critical. As notas dos
encerrados têm média 2,99/5, mas as comparações marginais por canal, prioridade e
tipo não apontam uma explicação convincente. O potencial de esforço recuperável
depende de um piloto: o cenário de referência simula 29,75 h/mês, não economia medida.

## Evidências e perguntas respondidas

Análise em 02/11/2026, sobre o CSV de atendimento versão 1 com SHA-256 fixado no
[manifesto](../data/manifest.json). O código verifica esse hash antes de ler.
Todos os registros originais são preservados; não removemos descrições repetidas,
não corrigimos rótulos e não preenchemos notas ou timestamps.

| Pergunta do briefing | Resposta sustentada |
| --- | --- |
| Onde o fluxo trava? | O retrato contém 2.819 Open e 2.881 Pending Customer Response. Todos os Open estão sem registro de primeira resposta. Isso justifica investigar a fila, mas não comprova que nunca houve resposta, sua idade ou onde ocorre atraso. |
| Quais segmentos merecem investigação? | Critical tem 1.403 não encerrados de 2.129; canais têm proporções próximas. Há extremos em combinações menores, expostos abaixo com seus denominadores. |
| O que impacta satisfação? | Foram examinadas associações marginais com três campos, não causas. Entre os 2.769 encerrados, não detectamos diferenças convincentes nesses testes exploratórios. |
| Quanto se desperdiça em horas? | Não é identificável no arquivo: não há esforço ativo ou início do ticket. Os cenários variam de −26,67 a +74,75 h/mês; os parâmetros são hipóteses, não estimativas aprendidas dos dados. |

As fontes dos números são o [JSON do diagnóstico](../data/diagnosis.json) e o
[CSV completo de segmentos](../data/diagnosis-segments.csv), gerados por
[diagnose_support.py](../solution/diagnose_support.py). As convenções e os cenários
estão em [configuração versionada](../data/diagnosis-assumptions.json), declarada
antes de inspecionar os resultados por grupo.

## 1. Composição da fila

Não encerrado significa `Open` ou `Pending Customer Response`. Cada percentual
abaixo divide a contagem pelo total do próprio grupo; não é uma taxa de fechamento
no tempo. A base não fornece um período de observação para calcular throughput.

| Canal | Tickets | Não encerrados | % do canal | Encerrados com nota | Média da nota |
| --- | ---: | ---: | ---: | ---: | ---: |
| Chat | 2.073 | 1.399 | 67,49% | 674 | 3,08 |
| Email | 2.143 | 1.423 | 66,40% | 720 | 2,96 |
| Phone | 2.132 | 1.441 | 67,59% | 691 | 2,95 |
| Social media | 2.121 | 1.437 | 67,75% | 684 | 2,97 |

O intervalo entre as proporções dos canais é de apenas 1,35 ponto percentual.
Não há aqui fundamento para afirmar que um canal é o gargalo temporal ou deve
receber sozinho o investimento. É necessário conhecer entradas, transições e idade.

| Prioridade registrada | Tickets | Não encerrados | % do grupo | Encerrados com nota | Média da nota |
| --- | ---: | ---: | ---: | ---: | ---: |
| Critical | 2.129 | 1.403 | 65,90% | 726 | 2,96 |
| High | 2.085 | 1.380 | 66,19% | 705 | 2,98 |
| Medium | 2.192 | 1.498 | 68,34% | 694 | 2,98 |
| Low | 2.063 | 1.419 | 68,78% | 644 | 3,05 |

Verificar os 1.403 Critical e 1.380 High não encerrados é uma hipótese operacional
de priorização a validar com o responsável. Esses números não demonstram que a
prioridade foi ignorada, que o risco é real ou que esses tickets são os mais antigos.

| Tipo registrado | Tickets | Não encerrados | % do grupo | Encerrados com nota | Média da nota |
| --- | ---: | ---: | ---: | ---: | ---: |
| Billing inquiry | 1.634 | 1.090 | 66,71% | 544 | 3,03 |
| Cancellation request | 1.695 | 1.179 | 69,56% | 516 | 3,03 |
| Product inquiry | 1.641 | 1.108 | 67,52% | 533 | 3,02 |
| Refund request | 1.752 | 1.156 | 65,98% | 596 | 2,93 |
| Technical issue | 1.747 | 1.167 | 66,80% | 580 | 2,96 |

Esses tipos são rótulos originais. A D01 identificou 446 linhas em grupos de
descrições iguais após normalização com tipos conflitantes. O CSV publica essa
contagem em cada segmento para evitar tratar o rótulo como referência validada.

## 2. Combinações: pistas para verificar, não vencedores comprovados

Foram geradas todas as partições simples, duplas e triplas: 150 linhas agregadas
incluindo o total. Cada partição descreve a mesma base; não se deve somar os totais
entre partições diferentes. As 80 combinações canal × prioridade × tipo têm 85–136 tickets
e 20–49 notas por grupo. Nenhum segmento foi excluído do CSV, inclusive grupos
vazios se existissem. A exibição de extremos exige ≥50 tickets e ≥20 notas para
comparar médias; são convenções de leitura, não garantias estatísticas.

| Combinação | Não encerrados / tickets | Proporção |
| --- | ---: | ---: |
| Phone · Low · Cancellation request | 87/108 | 80,56% |
| Social media · High · Cancellation request | 79/99 | 79,80% |
| Email · Medium · Product inquiry | 80/101 | 79,21% |

A menor média de satisfação observada entre esses grupos foi em Phone · High ·
Refund request: 2,29, com 31 notas em 108 tickets; 19/31 notas foram 1 ou 2.
São extremos escolhidos entre 80 grupos. Não fizemos um teste independente de
seus rankings; seleção de extremos, suporte pequeno, conteúdo repetido e rótulos
conflitantes impedem apresentá-los como causas ou prioridades definitivas.

## 3. Satisfação: cobertura e associações exploratórias

Há notas em 2.769/8.469 registros (32,70%), todos encerrados. A cobertura dentro
dos encerrados é 100%. Os 5.700 demais não têm nota; não os tratamos como nota zero.
Distribuição observada: 553 notas 1, 549 notas 2, 580 notas 3, 543 notas 4 e
544 notas 5. Notas 1–2 correspondem a 1.102/2.769 (39,80%), por convenção descritiva.

| Campo examinado separadamente | Fração da variação numérica das notas entre médias dos grupos | p por permutação | p ajustado para as três comparações |
| --- | ---: | ---: | ---: |
| Canal | 0,139% | 0,306 | 0,918 |
| Prioridade | 0,062% | 0,622 | 1,000 |
| Tipo | 0,079% | 0,703 | 1,000 |

O cálculo usa soma de quadrados entre grupos / soma de quadrados total, tratando
as notas 1–5 como espaçadas igualmente. São 999 permutações das notas dos
encerrados entre grupos fixos, com sementes registradas, e correção de Holm para
as três comparações predefinidas. O p Monte Carlo é `(excedências + 1)/(999 + 1)`.

A interpretação depende de permutabilidade dos registros; a proveniência incerta
e conteúdo repetido limitam essa hipótese. As notas são ordinais e a média é uma
descrição, não um modelo causal. **Não detectar essas associações não prova que
nada influencia satisfação**, não exclui interações e não generaliza aos não
encerrados. Não foi testado um efeito causal do tempo: esse tempo não é identificável.

## 4. Esforço e custo: cenários explícitos

Nenhuma hora de desperdício foi medida. Para explorar uma assistência à triagem,
assumimos **2.500 tickets/mês**, apenas os 30 mil/ano do contexto divididos por 12.
O CSV de 8.469 registros não foi anualizado. Em todos os exemplos há revisão humana
adicional em 100% dos casos assistidos; os minutos assistidos não incluem essa revisão.

`C = volume × elegibilidade × cobertura assistida`

`horas líquidas = [C × (minutos manuais − assistidos − revisão × minutos de revisão − retrabalho × minutos de retrabalho) − minutos fixos]/60`

Casos sem assistência mantêm o trabalho manual; não geram ganho. Custos fixos de
preparação/monitoramento são subtraídos mesmo com cobertura zero. As frações e os
tempos são hipóteses do agente, não dados medidos nem desempenho transferido do IT.

| Premissa ou resultado mensal | Desfavorável | Conservador | Referência | Otimista |
| --- | ---: | ---: | ---: | ---: |
| Elegibilidade | 40% | 40% | 60% | 80% |
| Cobertura entre elegíveis | 50% | 50% | 60% | 75% |
| Casos assistidos | 500 | 500 | 900 | 1.500 |
| Minutos manuais por caso | 4 | 4 | 4 | 4 |
| Minutos assistidos, sem revisão | 3 | 2 | 1 | 0,5 |
| Revisão adicional por caso assistido | 1 min | 0,75 min | 0,5 min | 0,25 min |
| Casos com retrabalho adicional | 20% | 10% | 5% | 2% |
| Minutos por retrabalho | 10 | 5 | 5 | 5 |
| Esforço fixo no mês | 600 min | 240 min | 240 min | 240 min |
| **Capacidade líquida hipotética** | **−26,67 h** | **2,25 h** | **29,75 h** | **74,75 h** |
| Equivalente a R$ 60/h, também hipotético | −R$ 1.600 | R$ 135 | R$ 1.785 | R$ 4.485 |

Na referência, 45 h brutas menos 7,5 h de revisão, 3,75 h de retrabalho e 4 h
fixas resultam em 29,75 h. O ponto de equilíbrio é aproximadamente 2,02 minutos de
trabalho manual por caso assistido, mantendo as demais premissas. Valores negativos
permanecem visíveis. Nenhum cenário recebe probabilidade de ocorrência.

O equivalente monetário valora capacidade, não é economia de caixa, salário
pesquisado ou ROI financeiro. Não foram estimados custos de infraestrutura/modelo,
implantação inicial ou conversão dessa capacidade em benefício realizado.

## 5. Próximas ações propostas

1. **Com o responsável pelo suporte:** conferir status e prioridades, começando
   pelos Critical/High não encerrados e pelos Open sem resposta registrada. Validar
   se são tickets ativos ou artefatos da base; não reordenar clientes reais com
   rótulos ainda não verificados.
2. **Instrumentar uma operação/piloto representativo:** abertura, respostas,
   transições, encerramento, esforço ativo por tarefa, reabertura, motivo da nota e
   população convidada a avaliar. Isso permitiria medir SLA, retrabalho e horas.
3. **Em S01:** delimitar uma triagem assistida, com saída útil, revisão humana e
   anomalias registradas/filtráveis. O benchmark IT demonstra classificação em seu
   domínio; não valida os parâmetros da simulação de atendimento.
4. **No piloto futuro:** medir os componentes da fórmula e a carga de revisão
   antes de alegar economia. A alternativa sem ganho é um resultado possível.

## Como reproduzir e verificar

Na pasta da submissão, Python 3.12.3 e biblioteca padrão:

```bash
python3 -I solution/acquire_data.py
python3 -I solution/diagnose_support.py
python3 -I -m unittest discover -s tests -v
python3 -I scripts/check_foundation.py --receipt docs/review-evidence/diagnosis-current.json
```

O [registro de verificação](review-evidence/diagnosis-checks.json) identifica
reprodução byte a byte, reconciliações e testes. O recibo registra dependências,
sem implicar revisão humana. A01 está concluída como diagnóstico da base e
cenários de esforço; S01 é a próxima etapa, e nenhuma automação foi avaliada aqui.
