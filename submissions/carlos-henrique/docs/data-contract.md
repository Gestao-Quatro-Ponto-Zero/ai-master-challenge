# Contrato de dados — estrutura pendente

> **Status geral:** nenhum dataset foi inspecionado. Todo schema permanece **A CONFIRMAR NA FASE 1**.

Este documento registra as fontes esperadas e o protocolo de validação sem transformar a descrição pública do challenge em um schema definitivo.

## Inventário pendente

| Tabela esperada | Arquivo esperado | Chave candidata | Granularidade esperada | Campos temporais | Relacionamentos | Riscos principais | Status da validação |
|---|---|---|---|---|---|---|---|
| Contas | `ravenstack_accounts.csv` | A CONFIRMAR NA FASE 1 | A CONFIRMAR NA FASE 1 | A CONFIRMAR NA FASE 1 | A CONFIRMAR NA FASE 1 | duplicidade, atributos mutáveis, missingness | A CONFIRMAR NA FASE 1 |
| Assinaturas | `ravenstack_subscriptions.csv` | A CONFIRMAR NA FASE 1 | A CONFIRMAR NA FASE 1 | A CONFIRMAR NA FASE 1 | A CONFIRMAR NA FASE 1 | múltiplas assinaturas, períodos sobrepostos, valores inconsistentes | A CONFIRMAR NA FASE 1 |
| Uso de funcionalidades | `ravenstack_feature_usage.csv` | A CONFIRMAR NA FASE 1 | A CONFIRMAR NA FASE 1 | A CONFIRMAR NA FASE 1 | A CONFIRMAR NA FASE 1 | alta cardinalidade, timezone, dias sem evento, inflação de joins | A CONFIRMAR NA FASE 1 |
| Tickets de suporte | `ravenstack_support_tickets.csv` | A CONFIRMAR NA FASE 1 | A CONFIRMAR NA FASE 1 | A CONFIRMAR NA FASE 1 | A CONFIRMAR NA FASE 1 | múltiplos tickets, tempos negativos, texto livre, dados pessoais | A CONFIRMAR NA FASE 1 |
| Eventos de churn | `ravenstack_churn_events.csv` | A CONFIRMAR NA FASE 1 | A CONFIRMAR NA FASE 1 | A CONFIRMAR NA FASE 1 | A CONFIRMAR NA FASE 1 | eventos recorrentes, reativação, leakage, definição do desfecho | A CONFIRMAR NA FASE 1 |

## Campos e tipos

Nomes de colunas, tipos, domínios, nulabilidade, unidades, moedas, timezone e semântica de valores estão **A CONFIRMAR NA FASE 1**. A documentação oficial do challenge serve apenas como orientação inicial; o contrato será atualizado com evidência obtida diretamente dos cinco arquivos.

## Testes futuros obrigatórios

1. **Unicidade:** validar as chaves candidatas e documentar exceções.
2. **Integridade referencial:** verificar vínculos entre as cinco fontes e órfãos.
3. **Missingness:** medir ausência por campo, segmento e tempo.
4. **Duplicidade:** distinguir duplicata exata, reprocessamento e evento legítimo repetido.
5. **Cardinalidade:** caracterizar relações um-para-um, um-para-muitos e muitos-para-muitos.
6. **Datas:** validar parsing, timezone, limites e valores impossíveis.
7. **Ordem temporal:** impedir sequências incompatíveis com o ciclo de vida observado.
8. **Inflação de joins:** reconciliar contagens e valores antes e depois de cada junção.
9. **Leakage:** excluir atributos indisponíveis no instante de decisão.
10. **Churn recorrente:** identificar mais de um evento por entidade e definir sua interpretação.
11. **Reativação:** verificar retorno após churn e seus efeitos sobre coortes e censura.

## Gate para efetivação do contrato

O contrato só passará de pendente para validado após: presença dos cinco arquivos oficiais; leitura bem-sucedida; inventário de schema; perfil de qualidade; validação de chaves e cardinalidades; reconciliação de contagens; documentação de riscos de privacidade; e aprovação explícita para prosseguir.
