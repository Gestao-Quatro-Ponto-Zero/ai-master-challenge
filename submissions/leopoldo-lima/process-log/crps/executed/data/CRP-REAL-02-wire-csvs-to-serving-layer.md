# CRP-REAL-02 — Conectar CSVs reais à camada de serving

## Objetivo
Plugar os CSVs reais ao fluxo de API/serving que alimenta o produto.

## Problema que resolve
Mesmo com ingestão e contrato de dados prontos, o produto ainda pode não estar servindo oportunidades reais no endpoint principal.

## Tarefas
1. Construir/adaptar o pipeline de leitura de:
   - `accounts.csv`
   - `products.csv`
   - `sales_teams.csv`
   - `sales_pipeline.csv`
   - `metadata.csv`
2. Garantir joins, normalização e integridade referencial antes do serving.
3. Gerar modelos canônicos de oportunidade para uso pela API.
4. Expor endpoints principais usando dados reais:
   - listagem ranqueada
   - detalhe da oportunidade
   - filtros
5. Manter fallback demo opcional, mas fora do caminho principal.

## Entregáveis
- código de serving ligado ao dataset real
- `docs/SERVING_REAL_DATA.md`
- atualização de `LOG.md`
- atualização de `PROCESS_LOG.md`

## Impacto na Submissão
- fecha o requisito mais crítico: uso real do dataset
- transforma a aplicação de demo controlada em protótipo aderente ao challenge

## Evidências obrigatórias
- resposta real de endpoint com `opportunity_id` oriundo do CSV
- print da UI mostrando registros do dataset real
- teste de integração ou smoke usando os CSVs reais

## Atualizações obrigatórias de process log
- decomposição do problema de serving real
- prompts usados para wiring e transformação
- bugs de join/normalização encontrados
- correções humanas aplicadas

## Atualizações obrigatórias de README/Submission
- documentar onde os CSVs devem ficar
- documentar o caminho de execução com dataset real

## Definition of Done
- endpoints principais usam o dataset real
- UI consegue consumir listagem e detalhe reais
- smoke test passa em modo real
- README, LOG e PROCESS_LOG atualizados
