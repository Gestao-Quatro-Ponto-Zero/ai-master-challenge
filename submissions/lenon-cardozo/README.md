# Submissão — Lenon Cardozo — Challenge 004

## Sobre mim

- **Nome:** Lenon Cardozo
- **LinkedIn:** https://www.linkedin.com/in/lenon-cardozo-681273200/
- **Challenge escolhido:** 004 — Estratégia Social Media

---

## Executive Summary

Analisei 52.214 posts para responder três perguntas: o que gera engajamento real, quando patrocínio funciona e qual estratégia aplicar no dia a dia. O principal achado foi simples: patrocínio no agregado é quase neutro. Ele só funciona bem em segmentos específicos. Por isso, a recomendação é operar por células de performance, com decisão semanal de escalar, manter, pausar ou testar.

Leitura visual rápida:
- Apresentação ao vivo: https://skill-deploy-nof601wqs3-codex-agent-deploys.vercel.app

---

## Solução

Entreguei a solução em três arquivos na pasta `solution`:
- `/solution/analysis.md`
- `/solution/recomendations.md`
- `/solution/strategy.md`

### Abordagem

1. Leitura do README do challenge para garantir aderência total às perguntas obrigatórias.
2. QA dos dados e criação das métricas derivadas (`ERR`, `share_rate`, `reach_per_follower`).
3. Segmentação por plataforma, período, categoria e tamanho de creator.
4. Comparação justa de orgânico vs patrocinado por estrato.
5. Tradução dos achados em recomendações operacionais e estratégia de execução.

### Resultados / Findings

- Respondi objetivamente:
  - o que gera engajamento,
  - quando patrocínio funciona,
  - qual perfil de audiência performa melhor,
  - o que não funciona.
- Mostrei as evidências numéricas por segmento no arquivo de análise.
- Estruturei recomendações com formato, audiência, categoria, frequência, delta esperado e evidência.
- Estruturei uma estratégia completa de operação de influenciadores no `strategy.md`.

### Recomendações

As recomendações priorizadas estão em:
- `/solution/recomendations.md`

Resumo executivo:
- Escalar células com lift comprovado.
- Pausar células com queda recorrente.
- Tratar patrocínio como tático, não como padrão.
- Rodar um ritual semanal com dashboard simples.

### Limitações

- O dataset não tem métricas de negócio (Lead/MQL/SQL/CAC).
- `engagement_rate` precisou ser derivado dos campos da base.
- O sinal entre segmentos é pequeno em vários recortes, então foi aplicada cautela nas conclusões.

---

## Process Log — Como usei IA

> **Este bloco é obrigatório.** Sem ele, a submissão é desclassificada.

### Ferramentas usadas

GPT-5.3-Codex: Leitura do repositório, planejamento da abordagem, análise do dataset, organização da resposta e revisão final.

### Workflow

1. Usei a IA para mapear hipóteses e cortes possíveis, mas persegui só as análises que respondiam ao brief: plataforma, período, categoria, creator band e comparação patrocinado vs. orgânico por estrato.
2. Quando surgiram caminhos mais amplos, escolhi o pacote `Operating System + Dashboard` e descartei uma entrega mais preditiva para manter profundidade, clareza e utilidade prática.
3. Depois da análise, reescrevi os outputs para leitura executiva e mantive no README apenas o que era decisivo para aprovação.

### Onde a IA errou e como corrigi

A IA partiu do pressuposto de que existia `engagement_rate`, mas no CSV real essa coluna não existia. Interrompi a linha de análise, derivei a métrica a partir de `likes + shares + comments_count / views` e documentei a limitação. Também recusei conclusões fortes em grupos frágeis: os insights principais ficaram restritos a células com `n >= 80`.

### O que eu adicionei que a IA sozinha não faria

A decisão de comparar patrocinado vs. orgânico apenas dentro de estratos equivalentes foi minha, para evitar conclusões agregadas enganosas. Também descartei claims de ROI de negócio porque o dataset não tinha Lead/MQL/SQL/CAC e transformei essa lacuna em recomendação de instrumentação no dashboard. Por fim, a adaptação da minha estratégia `Rede de Influenciadores` para um operating model conectado aos dados foi contribuição minha, não texto aceito automaticamente da IA.

---

## Evidências

_Anexe ou linke as evidências do processo:_

- [ ] Screenshots das conversas com IA
- [ ] Screen recording do workflow
- [x] Chat exports
- [x] Git history (se construiu código)
- [x] Outro: documentação de suporte em `docs/`

---

_Submissão enviada em: 2026-03-03_
