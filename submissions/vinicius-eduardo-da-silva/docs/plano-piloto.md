# Plano de piloto: o Foco da Semana aumenta as vendas?

**Para:** Head de Revenue Operations
**Decisão pedida:** aprovar um teste de um trimestre, com grupo de controle, antes de levar a ferramenta a todo o time.

## Por que testar

O replay mostrou que a lista aponta melhor os deals que iam fechar: 42% mais receita que ordenar por valor. Isso não prova que a atenção do vendedor muda o resultado, já que muitos desses deals talvez fechassem de qualquer forma. Só um teste responde a isso.

## O desenho

| Item | Proposta |
|---|---|
| **Quem** | Os 30 vendedores com deals, sorteados dentro de cada manager |
| **Grupo com a ferramenta** | Cerca de 15 vendedores usam a lista de Foco toda segunda |
| **Grupo de controle** | Cerca de 15 vendedores seguem como hoje, sem acesso à lista |
| **Duração** | Um trimestre completo |
| **Métrica principal** | Deals ganhos por vendedor, comparados com o trimestre anterior da mesma pessoa |
| **Métrica secundária** | Receita ganha por vendedor |
| **Métricas de proteção** | Tempo até fechar, deals novos em Engaging e deals que passam de 138 dias |

**Antes de começar:** todos os vendedores limpam a fila Decidir. Assim, o teste mede a priorização, e não o efeito da limpeza.

**Por que um trimestre:** o win rate varia de cerca de 50% a 80% conforme o mês do trimestre. Um mês só mediria esse ciclo, e não a ferramenta.

## O que o teste consegue detectar

Simulamos 5.000 divisões falsas dos vendedores em períodos em que nada foi testado, para medir o ruído natural. Os números são o menor ganho com 80% de chance de ser detectado, a 5% de significância:

| Duração | Em deals ganhos | Em receita |
|---|---:|---:|
| Um mês | 42% | 61% |
| **Um trimestre** | **17%** | **29%** |

**Isso limita o que se pode concluir.** Com 30 vendedores, um ganho real de 10% provavelmente não apareceria como resultado claro. Esses valores vêm de um único trimestre por período e são uma aproximação.

## Como decidir no fim

Definir isso antes evita interpretar o resultado conforme a conveniência.

| Resultado em deals ganhos | Decisão |
|---|---|
| Ganho claro, de cerca de 17% ou mais, sem piora nas métricas de proteção | Levar a todo o time |
| Ganho menor ou inconclusivo | Manter a fila Decidir e repetir o teste por mais um trimestre |
| Piora clara | Rever o score antes de qualquer expansão |

## Riscos

| Risco | O que fazer |
|---|---|
| **Baixa adoção:** o grupo não usa a lista | Acompanhar o uso desde a 1ª semana; sem uso, o teste não mede a ferramenta |
| **Contaminação:** vendedores do controle veem a lista | Acesso individual e combinado claro com os managers |
| **Região Central:** hoje não tem deal vivo | Confirmar o que aconteceu em julho de 2017 antes de sortear |
| **Efeito de trimestre** é efeito do dataset | Confirmar com RevOps, pois isso afeta o score |

## Sinais que aparecem antes do fim

Não servem para concluir sobre vendas, mas mostram cedo se vale continuar:

- Semana 2: fila Decidir limpa e vendedores abrindo a lista
- Semana 4: queda de deals acima de 138 dias
- Semana 6: os vendedores dizem que a lista mudou o que fizeram na semana
