# Instrumentação: 5 eventos

O DS1 não permite medir onde o fluxo trava. A 1ª resposta e a resolução estão invertidas em 49,3% dos tickets fechados (T3). Não existe data de abertura (T4). O status "Pending" mistura a espera do cliente com a espera do atendente (T7). E nada registra transferência entre filas. Estes 5 eventos cobrem essas lacunas.

**Campos comuns a todos os eventos:**
- `event_id`: único; serve de chave de idempotência, e um evento repetido com o mesmo `event_id` é descartado;
- `ticket_id`;
- `timestamp_utc`;
- `ator`: `cliente`, `agente` ou `sistema`.

| Evento | Quando dispara | Campos mínimos (além dos comuns) | O que permite calcular | Pergunta do brief que responde |
|---|---|---|---|---|
| `ticket_criado` | Cliente abre o ticket, em qualquer canal | `canal`, `prioridade`, `tipo`, `fila_inicial` | Início do relógio. Volume real por semana e por segmento. Tempo até a 1ª resposta (com `resposta_agente`) | Onde estamos perdendo tempo |
| `resposta_agente` | Agente envia mensagem ao cliente | `agente_id`, `primeira` (s/n) | Tempo até a 1ª resposta. Nº de interações por ticket | Onde estamos perdendo tempo |
| `status_mudou` | Qualquer troca de status | `status_de`, `status_para` (inclui `aguardando cliente`, `resolvido`, `reaberto`) | Tempo de resolução **líquido** (descontado o tempo em `aguardando cliente`). Taxa de reabertura | Onde estamos perdendo tempo; quanto se desperdiça |
| `reatribuido` | O ticket muda de fila ou de agente responsável | `fila_de`, `fila_para`, `motivo` | Reatribuições por ticket. Custo do roteamento errado: é o ganho do cenário B, hoje não calculável | O que pode ser automatizado (triagem/roteamento) |
| `csat_respondido` | Cliente responde à pesquisa | `nota` (1–5), ligada ao `ticket_id` | CSAT por ticket cruzado com as métricas acima | O que impacta a satisfação |

**Métricas derivadas mínimas:**
- **Tempo até a 1ª resposta** = 1º `resposta_agente` − `ticket_criado`.
- **Tempo de resolução líquido** = `status_mudou` → `resolvido` − `ticket_criado` − tempo total em `aguardando cliente`.
- **Taxa de reabertura** = tickets com `status_para = reaberto` ÷ tickets resolvidos.
- **Reatribuições por ticket** = nº de `reatribuido` ÷ nº de `ticket_criado`.
- **CSAT por ticket** = `csat_respondido.nota` cruzada com as quatro métricas anteriores, com o mesmo segmento (canal, prioridade, tipo).

**Prazo** (premissas: volume de ~30 mil tickets/ano, segundo o brief; desvio padrão do DS1 como premissa de variância), com o MDE de 2 h:

| Granularidade do diagnóstico | Semanas até poder detectar 2 h de diferença | Arquivo |
|---|---|---|
| Por prioridade | 0,9 | `solution/outputs/f2_mde.csv` |
| Por canal × prioridade | 3,6 | `solution/outputs/f2_mde.csv` |
| Por canal × prioridade × tipo | 21,2 | `solution/outputs/f2_mde.csv` |
