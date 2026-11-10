# 0006 — Evitar pausa do Supabase free por inatividade

- **Status:** Aceita
- **Data:** 2026-11-09
- **Origem:** Daniel (requisito: rotina diária para o projeto não cair) · IA (mecanismo)

## Contexto
Projetos free do Supabase são pausados após um período sem atividade (a página de billing atual não informa o número de dias; historicamente ~7). A avaliação do G4 pode acontecer semanas depois do envio.

## Decisão
Duas rotinas independentes, ambas versionadas na pasta da submissão:
1. **Vercel Cron (principal):** `vercel.json` com cron diário chamando `/api/heartbeat`, que faz uma leitura/escrita real no Supabase (tabela `heartbeat`). Confirmado na doc da Vercel (consultada em 2026-11-09): o plano **Hobby (grátis)** permite cron jobs com intervalo mínimo de **1 vez por dia** e precisão de ±59 min — suficiente.
2. **n8n Schedule (redundância):** workflow diário na VPS que chama a mesma rota.

O dashboard exibe "último heartbeat" — indicador de saúde para quem avaliar.

## Alternativas descartadas
- **Só `pg_cron` dentro do banco:** atividade interna pode não contar como uso do projeto.
- **GitHub Actions agendado:** workflows ficam em `.github/` na raiz (fora da pasta permitida) e Actions vêm desabilitadas em forks.
- **Edge Function sozinha:** não se agenda sozinha; precisaria de agendador externo de qualquer forma.
