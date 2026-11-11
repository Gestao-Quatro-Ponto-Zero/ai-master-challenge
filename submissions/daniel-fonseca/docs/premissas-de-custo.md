# Premissas do modelo de custo

> O DS1 não tem tempo de manuseio, data de abertura do ticket nem custo (ADR-0003). Estas premissas preenchem a lacuna **com fonte**, ficam editáveis no dashboard e são lidas de [`solution/analysis/cost_premises.json`](../solution/analysis/cost_premises.json).
> Pesquisa feita pela IA em 2026-11-09, a pedido do Daniel ("benchmarks com fonte"). Fontes lidas diretamente quando o acesso permitiu; o grau de verificação está indicado.

## Premissas usadas no cálculo

| Premissa | Valor padrão | Fonte | Verificação |
|---|---|---|---|
| Volume anual | 30.000 tickets | Brief do challenge 002 | primária |
| Tempo de manuseio humano | **8,6 min/ticket** | MetricNet via HDI — [Rumburg, *Ticket Handle Time*, 2019](https://thinkhdi.com/library/supportworld/2019/metric-of-month-ticket-handle-time) | lida |
| Alternativa telefone | 7,1 min (424 s) | [SQM Group — operational data findings](https://sqmgroup.com/resources/library/blog/call-center-operational-data-findings), América do Norte, estudo de 2021 | lida |
| Custo do atendente | **R$ 3.508/mês** (salário médio R$ 2.063,79 + encargos) | [Salario.com.br / Novo CAGED — Operador de Suporte Técnico, CBO 4223-20](https://www.salario.com.br/profissao/operador-de-suporte-tecnico-telemarketing-cbo-422320), 12 meses até 09/2026 | lida |
| Jornada | 38 h/semana → 164,7 h/mês | mesma fonte | lida |
| Custo por hora | **R$ 21,30** | cálculo: 3.508 / 164,7 | — |
| Produtividade | ~400 tickets/atendente/mês (10 min) · ~270 (15 min) | MetricNet via HDI, 2019 | lida |
| Follow-up por ticket "aguardando cliente" | 1 contato extra | **sem fonte** — premissa conservadora | — |

**Ordem de grandeza (padrões acima):** 30.000 × 8,6 min ≈ **4.300 h/ano ≈ R$ 91,6 mil/ano** em mão de obra direta; ~2.500 tickets/mês ≈ **6,2 atendentes**. O custo direto por ticket fica em R$ 3,05.

## Referências de contexto (não entram no cálculo)

| Referência | Por que não entra |
|---|---|
| Gartner: mediana de **US$ 13,50** por contato assistido × **US$ 1,84** em autoatendimento ([resumo 5164231](https://www.gartner.com/en/documents/5164231)) | Só o resumo é público; a data não foi confirmada. Inclui overhead (infra, gestão), por isso fica bem acima do custo direto. Serve para mostrar que **o nosso cálculo é conservador**. |
| Gartner 2019: US$ 8,01 por contato ao vivo × US$ 0,10 em autoatendimento; só 9% resolvem tudo sozinhos | Pesquisa antiga, média (não mediana), lida só via fontes secundárias. |

## Decisões de modelagem

- **Tempo na fila não entra no custo.** O cliente esperando não consome hora de atendente: custa **satisfação**, não mão de obra. Fica como indicador de SLA, com a recomendação de instrumentar a data de abertura (hoje inexistente). Não foi encontrado benchmark confiável para ele, e não inventamos um.
- **Custo só de mão de obra direta.** Sem overhead, licenças e gestão → a economia estimada tende a ser **subestimada**. É uma escolha conservadora e explícita.
- **Moeda:** R$ para mão de obra (operação no Brasil); referências internacionais em US$, sem conversão no cálculo.
- **Limitações:** benchmarks norte-americanos de tempo aplicados a custo brasileiro; o tempo de manuseio varia por tipo de ticket e o padrão é único (editável por tipo no dashboard).
