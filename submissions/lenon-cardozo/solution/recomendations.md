# Recomendations — Action Plan

## Recommendation Framework
Cada recomendação abaixo está no formato exigido: **formato, audiência, categoria, frequência, delta esperado e evidência**.

| ID | Prioridade | Plataforma | Formato | Audiência / Creator | Categoria | Frequência | Política de patrocínio | Delta esperado | Evidência |
|---|---|---|---|---|---|---|---|---|---|
| REC-01 | Alta | YouTube | Vídeo 120s+ | Creators 50k–200k, audiência 19–35 | Beauty | 3 posts/semana | Orgânico padrão; patrocínio só se estrato estiver em whitelist | `ERR +0,54%`, `share +0,30%`, `reach/follower +45,4%` vs baseline YouTube | EVID-01 |
| REC-02 | Alta | Instagram | Vídeo 120s+ | Creators 50k–200k, audiência 19–35 | Lifestyle | 3 posts/semana | Orgânico padrão; patrocínio apenas com teste A/B | `share +0,01%` e `reach/follower +46,7%` com ERR estável | EVID-02 |
| REC-03 | Alta | TikTok | Vídeo 120s+ | Creators 50k–200k, audiência 26–35 | Beauty | 4 posts/semana em Q4; 2 no restante | Primeiro orgânico; depois patrocínio só em célula com lift > 1.003 | Em Q4: `share +1,85%`, `ERR +0,07%` vs baseline TikTok | EVID-03 |
| REC-04 | Média | YouTube | Vídeo 120s+ | Creators 200k–500k | Lifestyle | 3 posts/semana + 1 experimento/semana | Patrocínio limitado a 20% do volume da célula | `share +1,10% a +1,20%`, `ERR +0,11% a +0,23%` | EVID-04 |
| REC-05 | Alta | YouTube + Instagram | Vídeo 120s+ | Creators 500k+ | Beauty / Lifestyle | 2 ativações patrocinadas/mês por estrato | Somente estratos High-confidence positivos | `ERR +0,50% a +0,59%`, `share +1,07% a +1,32%` | EVID-05 |
| REC-06 | Alta (corte) | TikTok + YouTube | Vídeo/Image 60s+ | Creators 500k+ | Beauty / Lifestyle | Reduzir 30% do volume por 6 semanas | Pausar patrocínio até lift voltar > 1.000 | Evitar perda de `ERR -0,55% a -0,79%` e `share -0,97% a -1,00%` | EVID-06 |
| REC-07 | Alta (governança) | Todas | Todos | Todos | Todos | Reunião semanal de 30–45 min | “Escalar/Manter/Pausar/Testar” por célula | Realocar 10–15% do volume fora do quartil inferior em 8 semanas | EVID-07 / EVID-08 |

## O que parar de fazer
1. Parar patrocínio horizontal por plataforma sem estratificação.
2. Parar alocação automática em creators `500k+` sem evidência de lift por célula.
3. Parar decisões por média agregada sem mediana/quartis.

## Quick Wins (esta semana)
1. Criar whitelist de patrocínio só com estratos High-confidence positivos.
2. Aplicar regra de pausa automática após 2 semanas abaixo de `ERR_rel < 0,995` ou `share_rel < 0,995`.
3. Rebalancear calendário para aumentar células `50k–200k + video 120s+`.
4. Publicar dashboard mínimo com abas: `Resumo`, `Segmentos`, `Patrocínio vs Orgânico`, `Ações da Semana`.

## Evidence Keys
- EVID-01 a EVID-08 em: `/docs/evidence_register.md`
