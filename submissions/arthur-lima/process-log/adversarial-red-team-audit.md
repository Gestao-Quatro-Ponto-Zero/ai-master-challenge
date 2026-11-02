# Registro de revisão adversarial e correções — Challenge 003

## Fluxo e atribuição

Conforme esclarecimento de Arthur, o trabalho partiu de **esboço de especificação no Antigravity**, passou por **revisão adversarial no DeepSeek** e seguiu para **auditoria e implementação no Codex**, com **revisão e ajustes de Arthur em cada etapa**.

Este arquivo reúne a síntese retrospectiva dos problemas e correções. Não é export de chat nem transcrição literal do DeepSeek. As versões anteriores traziam atribuições incorretas de ferramentas e uma divisão de papéis que não deve ser usada como evidência do processo. O fluxo acima substitui essas atribuições, sem inferir modelos específicos ou atribuir a uma única revisão todos os achados posteriores.

## 1. Especificação e revisão adversarial

O esboço no Antigravity foi submetido à revisão adversarial do DeepSeek, sob revisão de Arthur, antes da etapa de auditoria e implementação no Codex. A finalidade dessa passagem foi questionar as premissas e ajustar o direcionamento da solução.

A discussão técnica registrada no projeto inclui dispersão de preços, idade no funil e separação de Prospecting e Engaging. A ausência de vitórias observadas após 138 dias não prova impossibilidade de ganhar nem estabelece, sozinha, que a causa seja censura à direita. O export também não permite comprovar abandono ou quando o vínculo de conta foi preenchido. Essas limitações foram incorporadas à interpretação final.

## 2. Auditoria e implementação no Codex, revistas por Arthur

| Problema identificado nas versões anteriores | Correção implementada e revista durante o fluxo |
|---|---|
| Idade no teste usava data futura de fechamento. | `cycle_days` no instante de decisão; eventos de treino limitados ao corte; mutação de dados futuros nos testes. |
| Baselines e rótulos estavam em ordens diferentes. | Avaliação alinhada por oportunidade e desempate determinístico. |
| Histórico sem ganhos quebrava o estimador de ticket. | Fallback de catálogo com schema consistente. |
| Muitos multiplicadores e dias restantes manuais sem validação suficiente. | Simplificação para EV_90d, curva empírica em snapshots históricos completos e ablação de idade versus idade + vendedor. |
| Falta de conta recebia penalidade arbitrária. | Higiene cadastral separada de P_90d; sem inferir quando o vínculo foi preenchido. |
| Tabela descritiva era chamada de Kaplan-Meier e heurísticas eram apresentadas como calibradas. | Terminologia corrigida, Prospecting explicitamente não probabilístico e curva de calibração publicada para avaliação. |
| População avaliada excluía negócios ainda abertos. | Fila completa em +90 dias e diagnóstico condicional dos resolvidos publicados separadamente. |
| Testes verificavam filtros ou positividade sem detectar os defeitos. | Mutação, permutação, paridade lote/simulador, testes de persistência e interação via AppTest. |
| Override apenas gravava JSON e o simulador duplicava fórmulas. | Override funcional na fila, preservando estimativas; simulador usa scorer canônico. |
| Compatibilidade Python, horizontes aceitos e narrativa excediam a validação. | Python 3.12, launchers corrigidos, limites explícitos de backtest e reconhecimento de janelas sobrepostas e resultados observacionais. |

Arthur revisou e ajustou a condução dessas correções. A auditoria, a implementação e as verificações foram feitas no Codex; isso não transforma cada achado em descoberta exclusivamente humana. O [mapa H1–H5](../PROCESS_LOG.md#decisoes-humanas) mostra decisões e pontos de verificação.

## 3. Resultados e limites preservados

O ranking reúne 60,1%–63,7% da receita histórica observada no Top 20% nos três cortes móveis publicados, com janelas sobrepostas. O diagnóstico dos 970 resolvidos tem AUC ~0,49–0,51 nas estratégias avaliadas. Esses resultados não demonstram impacto causal nem teto universal de desempenho.

Os 19 testes passaram na rechecagem. O launcher Windows foi executado em cópia limpa com instalação, `pip check` e testes aprovados; o servidor respondeu HTTP 200 ao health check. O relatório foi reproduzido a partir do código. O launcher macOS/Linux não foi executado.

## 4. Correção da narrativa de autoria

Arthur identificou que a documentação atribuía contribuição a uma ferramenta que não participou. O Codex havia reproduzido essa atribuição sem confirmação. A documentação e os comentários foram corrigidos para o fluxo explicitamente informado pelo candidato. As anotações de decisão são retrospectivas; não substituem transcrições originais e não conferem autoria exclusiva a propostas cuja origem individual não foi confirmada.
