# CRP-REAL-03 — Alinhar domínio em runtime aos estágios e semântica do challenge

## Objetivo
Eliminar qualquer divergência entre o domínio runtime do produto e o domínio oficial do dataset/challenge.

## Problema que resolve
Há risco de o produto ainda carregar nomenclaturas ou convenções herdadas de protótipos anteriores, como estágios não previstos no dataset oficial.

## Tarefas
1. Encontrar e corrigir todas as ocorrências de estágios/nomenclaturas divergentes.
2. Padronizar o domínio de runtime para:
   - `Prospecting`
   - `Engaging`
   - `Won`
   - `Lost`
3. Corrigir labels, enums, filtros, payloads e testes.
4. Revisar a UI para que textos, badges e explicações reflitam a semântica oficial.

## Entregáveis
- ajustes de domínio em código
- `docs/DOMAIN_ALIGNMENT.md`
- atualização de `LOG.md`
- atualização de `PROCESS_LOG.md`

## Impacto na Submissão
- reduz inconsistência semântica
- melhora credibilidade do produto perante o avaliador

## Evidências obrigatórias
- grep/lista de arquivos corrigidos
- screenshot da UI com stages corretos
- payload de API com `deal_stage` alinhado
- teste cobrindo enum oficial

## Atualizações obrigatórias de process log
- registrar onde o domínio estava desalinhado
- anotar como a IA ajudou a encontrar resíduos
- registrar revisão humana dos labels finais

## Atualizações obrigatórias de README/Submission
- atualizar a seção de domínio/dados se necessário

## Definition of Done
- não há estágios espúrios no fluxo principal
- UI, API e testes usam a semântica oficial
- evidências e logs atualizados
