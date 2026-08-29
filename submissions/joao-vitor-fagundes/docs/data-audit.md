# Auditoria inicial dos dados

## Escopo e proveniência

- **Dataset:** CRM Sales Predictive Analytics
- **Fonte:** https://www.kaggle.com/datasets/agungpambudi/crm-sales-predictive-analytics
- **Licença declarada:** CC0
- **Data do download:** 28/08/2026
- **Snapshot temporal inferido pelos dados:** 31/12/2017
- **Arquivo original:** ZIP com SHA-256 `74d535826330b616758ebb6bb393abf701a5126364a72fbe71003cb6a7a87a9c`

O diretório `solution/data/raw/` preserva os arquivos como foram baixados. Correções devem acontecer em uma camada processada, nunca sobrescrevendo a fonte.

## Inventário

| Tabela | Linhas | Colunas | Chave | Duplicidades da chave |
|---|---:|---:|---|---:|
| `accounts.csv` | 85 | 7 | `account` | 0 |
| `products.csv` | 7 | 3 | `product` | 0 |
| `sales_teams.csv` | 35 | 3 | `sales_agent` | 0 |
| `sales_pipeline.csv` | 8.800 | 8 | `opportunity_id` | 0 |
| `metadata.csv` | 21 | 3 | catálogo de campos | 0 linhas duplicadas |

As chaves principais estão completas e não há linhas inteiras duplicadas.

## Estado do pipeline

| Estágio | Oportunidades | Participação |
|---|---:|---:|
| Won | 4.238 | 48,2% |
| Lost | 2.473 | 28,1% |
| Engaging | 1.589 | 18,1% |
| Prospecting | 500 | 5,7% |

- **Histórico fechado:** 6.711 oportunidades.
- **Win rate histórico:** 63,15%.
- **Pipeline ativo:** 2.089 oportunidades.
- **Valor de catálogo do pipeline ativo:** US$ 4.966.215.
- **Vendedores com oportunidades no pipeline completo:** 30 dos 35 cadastrados.
- **Vendedores cadastrados sem nenhuma oportunidade:** Carl Lin, Carol Thompson, Elizabeth Anderson, Mei-Mei Johns e Natalya Ivanova.

## Qualidade e relacionamentos

### Integridade referencial

- Todos os vendedores usados no pipeline existem em `sales_teams.csv`.
- Todas as contas não nulas do pipeline existem em `accounts.csv`.
- Todas as empresas-mãe não nulas existem na própria tabela de contas.
- `GTXPro` aparece em 1.480 oportunidades, enquanto o catálogo usa `GTX Pro`. A diferença é resolvível por normalização controlada.

### Cobertura dos dados ativos

- Apenas 664 das 2.089 oportunidades ativas possuem conta identificada: **31,8%**.
- Todas as 500 oportunidades em `Prospecting` não possuem `engage_date`, coerente com a interpretação de que ainda não foram engajadas.
- As 1.589 oportunidades em `Engaging` possuem `engage_date`.
- O preço de catálogo fica disponível para 100% das oportunidades depois da correção de `GTXPro`.
- `technolgy` aparece como setor em 12 contas e deve ser normalizado para `technology`.
- `Philipines` aparece como localização de uma conta e deve ser normalizado para `Philippines`.

Ausência de conta ou data não deve ser tratada apenas como sujeira. No pipeline ativo, ela também representa estágio e qualidade de qualificação.

## Evidência de pipeline estagnado

Entre oportunidades fechadas:

- Mediana do ciclo Won: **57 dias**.
- Mediana do ciclo Lost: **14 dias**.
- Maior ciclo fechado observado: **138 dias**.

Entre as oportunidades ainda em `Engaging`:

- Idade mediana: **165 dias**.
- Percentil 90: **319 dias**.
- Máximo: **423 dias**.
- 1.301 oportunidades estão abertas há mais de 138 dias, duração superior ao maior ciclo fechado observado.

Isso indica que o problema de negócio não é apenas “qual deal tem maior chance de ganhar”. Há um componente forte de higiene do pipeline: oportunidades antigas podem precisar de requalificação, próxima ação ou encerramento, e não de uma prioridade artificialmente alta por estarem abertas há mais tempo.

## Guardrails contra leakage

1. `close_date` e `close_value` são conhecidos somente após o resultado e não podem entrar como features de previsão.
2. `deal_stage` é Won/Lost nas linhas históricas e Prospecting/Engaging nas ativas. Usá-lo simultaneamente como alvo e feature produziria uma modelagem inválida.
3. Histórico de vendedor, conta ou produto deve ser calculado apenas dentro do conjunto de treino ou com passado temporal. Calcular taxas usando toda a base vazaria o resultado da própria oportunidade.
4. O snapshot contém oportunidades recentes e antigas ainda abertas. Uma validação aleatória pode misturar futuro e passado; a avaliação deve respeitar o tempo ou declarar claramente sua limitação.
5. O valor potencial de uma oportunidade ativa deve partir de `sales_price` ou de outra estimativa disponível antes do fechamento. `close_value` não existe nesse momento.

## Limite informacional

O dataset permite trabalhar com vendedor, produto, preço, conta, firmografia, região, manager e tempo desde o engajamento. Ele não oferece:

- histórico de mudança de estágio;
- última atividade ou próximo passo;
- chamadas, emails e reuniões;
- origem do lead;
- valor previsto informado pelo vendedor;
- contato e quantidade de stakeholders;
- motivos de perda;
- data de criação para oportunidades ainda em Prospecting.

Por isso, um modelo de probabilidade pode ser útil, mas terá um teto informacional baixo. Uma solução responsável deve mostrar confiança, cobertura dos dados e explicações, combinando evidência histórica com regras operacionais transparentes.

## Conclusão da auditoria

O dataset é suficiente para construir uma ferramenta funcional de priorização, desde que a entrega não confunda:

1. probabilidade de fechamento;
2. valor potencial;
3. urgência ou staleness;
4. qualidade dos dados;
5. próxima decisão operacional.

O relatório completo em JSON está em [`data-audit.json`](./data-audit.json), e a auditoria é reproduzível pelo script `solution/scripts/audit_data.py`.
