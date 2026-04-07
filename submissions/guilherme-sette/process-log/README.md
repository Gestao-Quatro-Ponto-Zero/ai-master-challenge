# Process Log

## Resumo do processo

O desenvolvimento começou por exploração dos CSVs para entender onde havia sinal real de negócio e onde havia só ruído operacional. A partir disso, a solução foi estruturada em duas camadas:

1. `Deal Forecast`
2. `Seller Fit`

Depois da primeira versão funcional, o trabalho concentrou-se em:

- clareza operacional da aba vendedor
- visão gerencial da aba head
- bugs de visualização e consistência de labels
- ajuste da responsabilidade de movimentação de owner para a liderança

## Ferramentas usadas

| Ferramenta | Uso principal |
|------------|---------------|
| Codex | Exploração, implementação, debugging e refinamento da dashboard |
| Python + pandas | Leitura, agregação e validação dos dados |
| Streamlit | Interface funcional da solução |
| Plotly | Gráficos da visão gerencial |

## Como o problema foi decomposto

Antes de construir a interface, o problema foi quebrado em perguntas menores:

1. O que define um bom deal com os dados disponíveis?
2. O que define aderência contextual de um vendedor?
3. O que é ação do vendedor e o que é decisão da liderança?
4. Como manter a solução explicável para um usuário não técnico?

Essa decomposição guiou a solução final:

- `Deal Forecast`: qualidade do deal
- `Seller Fit`: aderência contextual do vendedor
- `VENDEDOR`: operação
- `HEAD`: gestão

## Principais iterações

- análise inicial de produto, ticket, time e cadência
- decisão de evitar ML opaco e usar heurística explicável
- criação da dashboard funcional
- refino da lógica de realocação para não sacrificar resultado
- refino de UX para separar venda de higiene de CRM
- correções finais de bugs de forecast, plotly e renderização

## Onde a IA errou e como foi corrigida

- Escopo inicial foi além do pedido do usuário.
  - Correção: reorientação para foco estrito no que foi solicitado.
- Em versões intermediárias, a aba do vendedor ficou confusa e excessivamente “dashboard”.
  - Correção: simplificação da fila principal e separação entre venda e higiene de CRM.
- A ação de transferência de owner apareceu na mão do vendedor.
  - Correção: mover essa responsabilidade para a visão `HEAD`.
- Houve bugs técnicos:
  - coluna de forecast com escala inconsistente
  - gráfico usando nome de coluna errado
  - HTML renderizado como texto
  - warning de Plotly por API deprecated
  - Correção: iterações específicas de debugging e validação local

## O que foi julgamento humano

- Definir que a solução deveria ser útil para adoção real, não só “sofisticada”.
- Escolher explainability em vez de ML opaco.
- Interpretar que o principal gargalo do pipeline aberto era higiene e concentração, não apenas score.
- Definir que movimentação de owner é decisão de liderança e não ação operacional do vendedor.

## Evidências a anexar

- screenshots das conversas
- eventuais exports de chat
- screenshots da interface final
- histórico de commits

## Evidências já representadas nesta submissão

- narrativa escrita do processo neste arquivo
- estrutura da solução organizada dentro de `submissions/guilherme-sette/`
- código funcional da solução

## Artefatos complementares nesta pasta

- `timeline.md`: linha do tempo resumida das iterações
- `bugs-and-fixes.md`: principais erros encontrados e como foram corrigidos
- `artifacts-inventory.md`: inventário do que a submissão contém
- `manual-evidence-checklist.md`: checklist do que ainda vale anexar manualmente
