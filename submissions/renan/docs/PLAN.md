# Plano e registro de tempo

O G4 recomenda 4–6 h e diz que horas extras não valem pontos. Meta: **≤ 6 h**, registrando o tempo real de cada fase.

| # | Fase | Time-box | Entregável | Tempo real |
|---|---|---|---|---|
| 0 | Escolha do desafio, skills, arquitetura e docs | 0:30 | Este conjunto de docs | ~0:45 |
| 1 | Dados: download, scaffold, `build-data`, checagens de qualidade | 0:30 | `dataset.json` + achados H4 | ~0:30 |
| 2 | Exploração + motor de score + backtest | 1:15 | `analyze.ts`, `SCORING.md` e `FINDINGS.md`, testes | ~1:15 |
| 3 | Direção visual (propostas → escolha → tokens) | 0:30 | `DESIGN.md` seções 3–4 | ~0:50 |
| 4 | UI: hoje, pipeline, painel do deal, time, metodologia (+ refação como sistema) | 2:15 | App rodando | ~2:45 |
| 4c | Agente Gestor, Radar e Configurações (decisão minha, fora do plano original) | — | Agente + testes | ~1:30 |
| 5 | Auditoria de design e acessibilidade, ajustes | 0:20 | Correções (feitas ao longo das fases) | ~0:15 |
| 6 | Deploy, README final, process log, PR | 0:40 | URL pública + PR aberto | ~0:30 |
| | **Total** | **6:00** | | **~8:30** |

## Regra de corte

Se uma fase estourar o time-box em mais de 50%, corto escopo na ordem: `/time` → deals parecidos no painel → modo escuro. Nunca corto: explicação do score, filtros por vendedor/manager/região e o backtest.
