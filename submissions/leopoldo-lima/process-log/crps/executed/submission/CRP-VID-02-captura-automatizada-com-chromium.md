# CRP-VID-02 — Captura automatizada com Chromium

## Objetivo
Preparar a execução da demo no navegador escolhido, com estado previsível e gravação repetível.

## Decisão técnica
Usar **Chromium** com automação via Playwright ou script equivalente. Se houver gravação externa, o navegador continua sendo Chromium; se houver gravação via ferramenta do SO, documentar isso no runbook.

## Tarefas
1. Criar `scripts/record_demo_chromium.*` ou equivalente.
2. Garantir pré-condições:
   - servidor em pé
   - porta correta
   - dataset real carregado
   - estado inicial limpo
3. Automatizar:
   - abrir app
   - aguardar KPIs
   - aplicar ao menos um filtro
   - abrir detalhe
   - demonstrar combobox/gestor
4. Criar `docs/VIDEO_RUNBOOK.md`.
5. Atualizar `LOG.md` e `PROCESS_LOG.md`.

## Entregáveis
- script de gravação/navegação
- runbook do vídeo
- logs atualizados

## Impacto na Submissão
Tira o vídeo do improviso e garante que a prova visual seja reproduzível.

## Evidências obrigatórias
- script versionado
- comando de execução
- captura de uma execução bem-sucedida
- nota sobre ferramenta efetiva de gravação

## Definition of Done
- fluxo automatizado ou semi-automatizado documentado
- Chromium definido como navegador oficial da demo
- runbook publicado
- logs atualizados
