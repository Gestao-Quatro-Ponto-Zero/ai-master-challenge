# CRP-REAL-08 — Elevar testes para o caminho principal com dataset real

## Objetivo
Garantir que a suíte de testes proteja o fluxo que realmente importa para o challenge.

## Problema que resolve
Se os testes só cobrem mocks/demos, a submissão continua vulnerável no que mais interessa.

## Tarefas
1. Criar/ajustar testes de integração e smoke para:
   - carga dos CSVs reais
   - ranking principal
   - detalhe da oportunidade
   - filtros
   - explainability
2. Usar amostras reais do dataset ou fixtures derivados dele.
3. Manter testes rápidos, pequenos e confiáveis.
4. Atualizar estratégia de testes.

## Entregáveis
- testes reais do caminho principal
- `docs/TEST_STRATEGY_REAL_DATA.md`
- atualização de `LOG.md`
- atualização de `PROCESS_LOG.md`

## Impacto na Submissão
- prova verificabilidade
- reduz risco de “a IA disse, o candidato acreditou”

## Evidências obrigatórias
- output de testes passando
- evidência de teste exercitando CSV real
- resumo do que está coberto e do que ainda não está

## Atualizações obrigatórias de process log
- registrar gaps antigos de teste
- prompts usados para gerar casos e correções
- validação humana dos cenários críticos

## Atualizações obrigatórias de README/Submission
- atualizar instruções de teste e validação

## Definition of Done
- suíte cobre o fluxo principal em modo real
- testes passam localmente/CI
- docs, LOG e PROCESS_LOG atualizados
