# Mapa de evidências do processo

Este índice liga cada pergunta que a banca faz (README do repositório e `submission-guide.md`) ao arquivo que a responde. Tudo aqui foi gerado durante o trabalho, nada foi reconstruído depois.

## As perguntas do G4 e onde estão as respostas

| Pergunta da banca | Evidência | Arquivo |
|---|---|---|
| **Você entendeu o problema antes de sair executando?** | Exploração dos dados antes de qualquer código. Pivot do "score por atributos" para o frescor quando os dados derrubaram a hipótese. Escopo com as dores da Head de RevOps traduzidas em métrica. | [`00_fase0_exploracao.md`](00_fase0_exploracao.md), [`../docs/briefing.md`](../docs/briefing.md), [`../docs/SCOPE.md`](../docs/SCOPE.md) |
| **Usou IA de forma inteligente ou só deu copy-paste?** | Antes de delegar, escrevi um kit de regras: 7 decisões fechadas, um prompt por bloco com checkpoints, guia de armadilhas e um prompt de operação com regras de honestidade. A execução tem planejador, executores e revisor separados, e cada um tem a sua função. | [`../CLAUDE.md`](../CLAUDE.md), [`../PROMPTS.md`](../PROMPTS.md), [`../GUIA.md`](../GUIA.md), [`../PROMPT_AUTONOMO.md`](../PROMPT_AUTONOMO.md), [`plano_execucao_opus.md`](plano_execucao_opus.md) |
| **Como decompôs o problema antes de promptar?** | Oito blocos sequenciais (escopo → dados → score → produto → docs → revisão → PR), cada um com entregável e critério de pronto. | [`../PROMPTS.md`](../PROMPTS.md), [`plano_execucao_opus.md`](plano_execucao_opus.md) |
| **Onde a IA errou e como você corrigiu?** | Três episódios da fase 0 corrigidos por mim, onze da execução delegada pegos pelos controles que exigi, e um que os controles não pegaram: a curva de chance em patamar, que eu vi ao usar a ferramenta como vendedor ([`07_correcao-curva.md`](07_correcao-curva.md)). | [`../README.md`](../README.md) (seção "Onde a IA errou"), logs `NN_bloco-N.md` (seção "O que deu errado") |
| **O que você adicionou que a IA sozinha não faria?** | Problema, tese, regra de justiça (vendedor fora do score), controles de governança, decisão de não ajustar o modelo depois do resultado e publicação reservada a mim. | [`../README.md`](../README.md) (seção "O que eu adicionei"), [`07_revisao-do-rafael.md`](07_revisao-do-rafael.md) |
| **Quantas iterações?** | Um commit por bloco. Cada log registra testes que falharam, hipóteses descartadas e versões refeitas. Há duas rodadas de revisão independente com correções entre elas, e 3 atritos de interface com antes e depois. | histórico git, `NN_bloco-N.md`, [`06_revisao-independente.md`](06_revisao-independente.md), [`screenshots/`](screenshots/) |
| **Houve verificação, ou "a IA disse e o candidato acreditou"?** | O critério de sucesso foi registrado antes do backtest. Um teste de mutação do futuro protege contra vazamento. Outro teste confere cada número da prosa. A página foi aberta de verdade (Playwright) e o build é determinístico. | [`../docs/SCORING.md`](../docs/SCORING.md), [`../solution/tests/`](../solution/tests/), [`../solution/tools/check_app.py`](../solution/tools/check_app.py) |
| **O resultado resolve o problema? Alguém consegue agir?** | Ferramenta funcionando, um brief de segunda-feira por vendedor e recomendações priorizadas para a Head de RevOps. | [`../solution/app/index.html`](../solution/app/index.html), [`../solution/briefs/`](../solution/briefs/README.md), [`../README.md`](../README.md) |

## Onde eu intervim (e onde não)

| Momento | Quem decidiu | Registro |
|---|---|---|
| Fase 0: escolha do desafio, leitura do problema, pivot para o frescor, regras do projeto | Rafael, conversando com o Claude | [`00_fase0_exploracao.md`](00_fase0_exploracao.md) |
| Kit de regras e prompt de operação | Rafael, redigido com o Claude | [`../CLAUDE.md`](../CLAUDE.md), [`../PROMPT_AUTONOMO.md`](../PROMPT_AUTONOMO.md) |
| Blocos 0 a 6: decisões técnicas dentro das regras | Claude, marcadas "decisão autônoma do Claude", uma por linha | [`../docs/DECISIONS.md`](../docs/DECISIONS.md) |
| Durante a execução: paralelizar, retomar depois da cota, ajustar modelo e esforço | Rafael | [`chat-exports/sessao-orquestracao-claude-code.md`](chat-exports/sessao-orquestracao-claude-code.md) (linha do tempo no topo) |
| Revisão final da narrativa e das evidências, publicação | Rafael | [`07_revisao-do-rafael.md`](07_revisao-do-rafael.md) |
| Uso da página publicada como vendedor, detecção da curva em patamar e pedido de correção | Rafael (a implementação foi delegada) | [`07_correcao-curva.md`](07_correcao-curva.md), screenshots `antes-correcao-*` e `depois-correcao-*` |
| Visões por perfil, escolha da opção A com a limitação declarada, opção B mapeada e direção visual | Rafael, por especificação escrita (a execução foi delegada) | [`../PROMPT_VISOES_E_DESIGN.md`](../PROMPT_VISOES_E_DESIGN.md), [`08_visoes-e-design.md`](08_visoes-e-design.md), [`../docs/ARQUITETURA_PRODUCAO.md`](../docs/ARQUITETURA_PRODUCAO.md) |
| Uso da página publicada como vendedor e pedido de correção da curva de chance (mudança pós-backtest) | Rafael pediu; execução pelo Claude Sonnet (subagente executor) | [`07_correcao-curva.md`](07_correcao-curva.md) |

O registro separa as duas coisas de propósito. Não atribuí a mim nenhuma decisão que a IA tomou, nem o contrário.

## Os arquivos, por tipo

- **Narrativa por bloco:** [`00_fase0_exploracao.md`](00_fase0_exploracao.md), [`00_bloco-0.md`](00_bloco-0.md), [`01_bloco-1.md`](01_bloco-1.md), [`02_bloco-2.md`](02_bloco-2.md), [`03_bloco-3.md`](03_bloco-3.md), [`04_bloco-4.md`](04_bloco-4.md), [`05_bloco-5.md`](05_bloco-5.md), [`06_bloco-6.md`](06_bloco-6.md), [`07_revisao-do-rafael.md`](07_revisao-do-rafael.md), [`07_correcao-curva.md`](07_correcao-curva.md).
- **Plano (equivalente ao Plan Mode):** [`plano_execucao_opus.md`](plano_execucao_opus.md), salvo sem edição.
- **Revisões independentes:** [`06_revisao-independente.md`](06_revisao-independente.md), com dois relatórios integrais, triagem e correções.
- **Conversa:** [`chat-exports/`](chat-exports/LEIA-ME.md).
- **Screenshots:** [`screenshots/`](screenshots/). Os prefixos são `antes_`, `depois_` (3 atritos corrigidos) e `final_`, em 390 px e 1280 px, mais `antes-correcao-rosalina-` e `depois-correcao-rosalina-` (correção da curva). As visões por perfil e o design têm o [`08_visoes-e-design.md`](08_visoes-e-design.md), as três rodadas de screenshots em `screenshots/design-r1/`, `design-r2/` e `design-r3/` e o conjunto final `final-*.png`.
- **Reprodução da fase 0:** [`scripts/`](scripts/eda.py) e [`outputs/`](outputs/).
- **Decisões:** [`../docs/DECISIONS.md`](../docs/DECISIONS.md), com uma linha por decisão, a alternativa descartada e o motivo.
- **Git:** um commit por bloco na branch `submission/rafael-pereira`.
