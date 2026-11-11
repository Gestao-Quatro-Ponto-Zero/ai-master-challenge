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

## Revisão de 10/11 (Daniel)
O keep-alive fica **só no n8n**. O fluxo 3 já roda todo dia, e o Daniel não viu necessidade de manter também o cron da Vercel.
- O fluxo 3 (`LpQK8XX5AZJrUCy8`) grava direto em `heartbeat` (`source = 'n8n'`) pelo nó nativo do Supabase, com a credencial `G4 - Supabase`. Ele foi publicado em 10/11, e o teste manual gravou a linha 5.
- Saíram o cron do `vercel.json`, a rota `/api/heartbeat` e o `CRON_SECRET`. A credencial `G4 - Cron da Vercel` deixou de ser necessária.
- Se o banco não aceitar a gravação depois de 3 tentativas, a execução fica com erro no n8n. Com o banco fora do ar, não existe tabela onde gravar um alerta.
- Os itens 1 e 2 da decisão acima ficam como histórico.

## Alternativas descartadas
- **Só `pg_cron` dentro do banco:** atividade interna pode não contar como uso do projeto.
- **GitHub Actions agendado:** workflows ficam em `.github/` na raiz (fora da pasta permitida) e Actions vêm desabilitadas em forks.
- **Edge Function sozinha:** não se agenda sozinha; precisaria de agendador externo de qualquer forma.
