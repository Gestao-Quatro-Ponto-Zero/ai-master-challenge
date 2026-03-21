# CRP-REAL-01 — Baseline do runtime real e eliminação do caminho demo dominante

## Objetivo
Trocar o foco do produto principal para o dataset real, sem apagar ainda os artefatos demo. Este CRP serve para identificar e reconfigurar o caminho dominante do runtime.

## Problema que resolve
Hoje o projeto prova que sabe ler os CSVs reais, mas o caminho principal do produto ainda parece servir dados sintéticos/demo. Isso enfraquece a aderência ao challenge.

## Tarefas
1. Identificar exatamente quais módulos, endpoints, scripts e telas ainda dependem de `demo-opportunities.json` ou equivalentes.
2. Mapear o runtime principal atual:
   - fonte de dados
   - pipeline de transformação
   - endpoints
   - UI
3. Introduzir uma configuração explícita de source mode:
   - `real_dataset`
   - `demo_dataset` (apenas para fallback ou desenvolvimento local controlado)
4. Tornar `real_dataset` o modo padrão.
5. Documentar a decisão no repositório.

## Entregáveis
- `docs/RUNTIME_DATA_FLOW.md`
- atualização de `README.md`
- atualização de configuração/env
- atualização de `LOG.md`
- atualização de `PROCESS_LOG.md`

## Impacto na Submissão
- move a solução para aderência real ao dataset oficial
- reduz risco de avaliador entender que a demo é sintética
- fortalece a narrativa de software funcional com dados reais

## Evidências obrigatórias
- diff mostrando `real_dataset` como default
- print/log da aplicação subindo em modo real
- captura de endpoint/UI servindo dados do dataset real
- nota curta listando arquivos que ainda usam demo e por quê

## Atualizações obrigatórias de process log
Registrar:
- como foi identificado o caminho demo dominante
- que ferramentas de IA ajudaram no diagnóstico
- onde a IA errou ou simplificou demais
- quais decisões humanas foram tomadas para preservar ou rebaixar o caminho demo

## Atualizações obrigatórias de README/Submission
- adicionar seção “Data Source”
- deixar explícito que o modo padrão de execução usa os CSVs oficiais

## Definition of Done
- `real_dataset` é o caminho padrão do produto
- o runtime principal não depende mais de dataset demo para funcionar
- README, LOG e PROCESS_LOG atualizados
- evidências salvas
