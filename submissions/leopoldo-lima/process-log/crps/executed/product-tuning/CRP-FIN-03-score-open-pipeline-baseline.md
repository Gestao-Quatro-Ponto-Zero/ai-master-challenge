# CRP-FIN-03 — Recalibrar score: baseline para oportunidades abertas

## Objetivo
Parar de privilegiar excessivamente oportunidades já ganhas no topo do ranking e reposicionar o score para **priorização operacional de oportunidades abertas**.

## Fazer
- revisar pesos atuais
- reduzir o prêmio estrutural de `Won` no ranking principal
- separar:
  - score operacional para foco comercial
  - sinal de fechamento histórico, se ainda fizer sentido
- garantir que `Prospecting` e `Engaging` competitivos possam subir no ranking

## Impacto na submissão
Ataca um dos principais riscos de produto: o ranking parecer correto tecnicamente, mas inútil operacionalmente.

## Evidências obrigatórias
- diff de pesos/regras
- comparação antes/depois do top 20
- evidência de oportunidades abertas subindo no ranking com justificativa plausível

## Atualizações obrigatórias de process log
Registrar:
- problema detectado no ranking antigo
- hipótese de recalibração
- efeito observado após ajuste

## Definition of Done
- top do ranking não é dominado artificialmente por `Won`
- oportunidades abertas relevantes aparecem no topo
- rationale dos pesos ficou documentado
