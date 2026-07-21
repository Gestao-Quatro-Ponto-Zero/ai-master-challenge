# Submissão — Rafael Antunes Sanches — Challenge 002

## Sobre mim

- **Nome:** Rafael Antunes Sanches
- **LinkedIn:** https://www.linkedin.com/in/sanchesarafael/
- **Challenge escolhido:** 002 — Redesign de Suporte

---

## Executive Summary

Diagnostiquei a operação de suporte, propus uma automação com IA e construí um protótipo funcional. O achado que reorienta tudo: **os dados operacionais do Dataset 1 não enxergam o problema** — 49% das "durações" de atendimento são negativas (impossível), nenhuma variável capturada explica a satisfação (R²=0,003), e não há gargalo concentrado. O diagnóstico honesto, então, não é "achei a causa-raiz" — é *"o sistema foi feito para operar, não para diagnosticar; antes de otimizar, é preciso instrumentar"*. Mas o **texto** dos tickets é uma matéria-prima rica: construí um classificador que roteia tickets com **86,5% de acurácia**, a custo zero e em milissegundos, com um **gate de confiança** que automatiza 74% dos tickets e manda os 26% mais incertos para um humano. Recomendação central: automatizar a triagem por texto (74% dos tickets sem toque humano; ~900 h/ano poupadas num exemplo ajustável), instrumentar os dados operacionais, e **não** automatizar o que exige julgamento (reembolsos, casos críticos insatisfeitos).

---

## Solução

> **Nota sobre os dois datasets:** eles são **complementares, não combináveis** — Dataset 1 é suporte a produto de consumo, Dataset 2 é service desk de TI interno; domínios e taxonomias diferentes, sem chave comum. Um "join" produziria lixo. Usei cada um para sua força, exatamente como as dicas do desafio sugerem: **D1 para o diagnóstico operacional, D2 para o classificador**. Reconhecer isso — em vez de forçar um cruzamento inexistente — é parte da solução.

### Abordagem

Plano de 4 fases com verificação em cada uma: **(0)** auditoria de integridade dos dados → **(1)** diagnóstico → **(2)** protótipo + benchmark supervisionado vs. LLM → **(3)** síntese. Comecei duvidando dos dados antes de analisá-los — o que mudou o rumo de toda a solução (ver Process Log).

### Resultados / Findings

- **Diagnóstico** → [`solution/DIAGNOSIS.md`](solution/DIAGNOSIS.md). As três perguntas do Diretor testadas estatisticamente; o fato sólido: só **32,7% dos tickets chegam a "Resolvido"**. Gráficos em [`solution/figures/`](solution/figures/).
- **Proposta de automação** → [`solution/AUTOMATION.md`](solution/AUTOMATION.md). O que automatizar (classificação+roteamento), o que **não** (com base nos dados), o fluxo, e o ROI.
- **Protótipo funcional** → [`solution/prototype/`](solution/prototype/). App Streamlit: cola o ticket → categoria + confiança + roteamento + explicação; modo lote; slider de limiar ao vivo. Roda local, com dados reais.
- **Benchmark** → provamos que o supervisionado (88,6%) supera o LLM zero-shot mesmo com prompt caprichado (Opus 55,8%), a 1/1000 do custo e da latência.

### Recomendações (priorizadas)

1. **Automatizar a triagem por texto** com o classificador + gate de confiança — **74% dos tickets** roteados sem toque humano (~900 h/ano poupadas num exemplo ajustável, premissa em AUTOMATION.md), a custo marginal ~US$0.
2. **Instrumentar os dados operacionais** (capturar `created_at`, validar ordem dos timestamps, amarrar CSAT ao ticket/agente, padronizar o campo de resolução) — sem isso, nenhuma métrica de eficiência é confiável.
3. **Não automatizar** o que exige julgamento humano (reembolsos/cobrança, Critical+CSAT baixo) nem o que os dados não sustentam (sugestão de resposta, triagem de prioridade).

### Limitações

O diagnóstico do desperdício *atual* em horas/custo **não é possível** com estes dados (durações corrompidas) — por isso o ROI é uma projeção da automação, não uma medida do estado atual. O classificador aprendeu a taxonomia do dataset público; um deploy real precisa retreinar nos tickets e na taxonomia da própria empresa, em texto cru, com calibração e monitoramento. O protótipo é prova de capacidade, não sistema pronto (ver `solution/prototype/README.md`).

---

## Process Log — Como usei IA

> **Bloco obrigatório.** Versão completa em [`process-log/PROCESS_LOG.md`](process-log/PROCESS_LOG.md).

Usei o **Claude Code** como copiloto para fazer a análise e o código, e **dirigi** o processo — escolhi o desafio, impus um protocolo fase-a-fase (discutir antes de executar), e fiz o controle de qualidade. Meu valor esteve em *como* dirigi. Destaques dos ciclos de verificação:

- **Exigi validar o brief contra a fonte:** pedi ao Claude conferir os dados; ele pegou que o enunciado diz "~30.000 registros", mas o arquivo tem **8.469**.
- **Mandei validar os dados antes de construir:** o Claude descobriu que `Resolution` é sintético e 49% das durações são negativas — matou uma feature planejada e reescreveu o diagnóstico.
- **Deixei o dado corrigir a hipótese:** o LLM errou mais em Hardware, não nas categorias previstas; revisei a explicação em vez de forçá-la.
- **Uma revisão crítica que pedi** pegou um número enganoso (96% numa amostra pequena) — exigi contexto honesto (86,5% de referência).
- **Forcei um teste justo:** mandei benchmarkar três modelos de LLM, não só o mais fraco.

O que meu julgamento acrescentou: **ceticismo como método** (a IA sozinha teria analisado dado sintético como real), o enquadramento estratégico, e saber onde parar de automatizar.

---

## Evidências

- [x] **Narrativa escrita** → `process-log/PROCESS_LOG.md`
- [x] **Git history** → commits mostrando a evolução fase-a-fase
- [x] **Código comentado** → scripts de análise em `solution/analysis/` + protótipo em `solution/prototype/`
- [x] **Figuras da análise** → `solution/figures/` (backlog, CSAT, duração corrompida, matriz de confusão, curva precisão×cobertura)
- [x] **Protótipo executável** → `solution/prototype/` (roda com `streamlit run app.py`)

---

*Submissão enviada em: [preencher na data do push]*
