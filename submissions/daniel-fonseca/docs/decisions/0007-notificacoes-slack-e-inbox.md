# 0007 — Notificações do nível 3: Slack (n8n) + caixa de mensagens no painel

- **Status:** Aceita
- **Data:** 2026-11-09
- **Origem:** Daniel

## Contexto
O plano inicial era WhatsApp via WAHA. Para o avaliador do G4, WhatsApp exige número próprio e sessão pareada; Slack é mais provável na stack do G4 e não depende de telefone.

## Decisão
- O workflow n8n do nível 3 termina num **nó Slack** (mensagem para o canal do time de suporte).
- Toda notificação também é gravada no Supabase e aparece na **caixa de mensagens do painel**, mostrando a mensagem exatamente como seria enviada a partir do teste feito, mais uma explicação de como funciona no caso real (envio pelo nó Slack do n8n).
- WhatsApp (WAHA ou Evolution API) fica documentado como alternativa — é só trocar o nó final.

## Consequências
- A demo funciona mesmo sem Slack configurado (a caixa no painel é sempre a fonte de verdade).
- O formato da mensagem é o mesmo nos dois destinos.
