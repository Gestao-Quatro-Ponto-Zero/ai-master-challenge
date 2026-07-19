# Plano mestre do projeto

Este documento torna o process log autocontido. Ele reproduz, de forma organizada, a instrução mestra definida por Thales antes da execução e registra as adaptações aprovadas ao longo do trabalho.

## Papel e objetivo

Atuar como Senior AI Master, Data Scientist, Analytics Engineer, Machine Learning Engineer, AI Engineer, Product Manager e consultor de operações para resolver o **Challenge 002 — Redesign de Suporte**.

O problema de negócio parte de uma operação com aproximadamente 30 mil tickets/ano e três perguntas centrais:

1. Onde estamos perdendo tempo?
2. O que pode ser automatizado com IA?
3. É possível mostrar algo funcionando?

A entrega deveria incluir diagnóstico operacional, proposta de automação, protótipo funcional, ROI e process log.

## Regras de execução definidas pelo humano

- trabalhar em fases e não pular etapas;
- ao fim de cada fase, salvar artefatos, documentar decisões, validar resultados e registrar limitações;
- não sustentar conclusões em achismos;
- comprovar afirmações quantitativas com os dados e explicitar premissas;
- manter gates humanos entre fases;
- entregar uma solução reproduzível e pronta para submissão no GitHub.

## FASE 0 — Descoberta do repositório

Ler recursivamente o projeto e identificar README principal, briefing do Challenge 002, guia de contribuição, guia de submissão, templates, datasets, notebooks, estrutura e dependências.

**Saída esperada:** `solution/docs/project_discovery.md`, com requisitos, perguntas obrigatórias, entregáveis e lacunas.

## FASE 1 — Auditoria dos dados

Auditar todos os datasets: dimensões, schema, tipos, nulos, duplicados, cardinalidade, estatísticas, outliers, inconsistências e distribuições.

Investigar especialmente `First Response Time` e `Time to Resolution`, testando se o segundo representa tempo total ou tempo após primeira resposta. Verificar negativos, coerência, percentis e relação entre campos; documentar ambiguidades.

**Saídas esperadas:** `solution/docs/data_audit.md`, notebook executado e gráficos.

## FASE 2 — Preparação dos dados

Criar variáveis derivadas úteis, como status, criticidade, volume e proxies de esforço; definir fórmula, origem e justificativa de cada feature.

Quando uma feature solicitada não puder ser calculada honestamente, registrar como não disponível e indicar a instrumentação necessária, em vez de inventar valores.

**Saídas esperadas:** módulo de preparação, testes, dados processados regeneráveis, notebook e `solution/docs/feature_engineering.md`.

## FASE 3 — Responder o desafio

### Pergunta 1 — Onde o fluxo trava?

Investigar canal, tipo, prioridade e seus cruzamentos; produzir medidas robustas, tabelas e heatmaps; identificar gargalos e quantificar impacto operacional em horas.

### Pergunta 2 — O que impacta a satisfação?

Usar apenas tickets válidos. Avaliar tempos quando semanticamente válidos, tipo, canal e prioridade com correlação de Spearman, ANOVA, regressão e Random Forest; comunicar tamanho de efeito e limitações.

### Pergunta 3 — Quanto estamos desperdiçando?

Calcular horas/ano, FTE, custo operacional e economia potencial. O ROI deve declarar premissas, fórmulas, cenários, sensibilidade e limitações.

**Decisão humana posterior e vigente:** implementação interna pelo AI Master, com custo incremental de implantação **R$ 0**. O modelo econômico varia desempenho e custo recorrente, não investimento externo.

## FASE 4 — Automação com IA

Usar ambos os datasets para decidir o que automatizar, assistir ou nunca automatizar, considerando repetitividade, previsibilidade, risco, criticidade e necessidade de julgamento humano.

**Saída esperada:** `solution/docs/automation_strategy.md`, matriz de automação e regras explícitas de veto.

## FASE 5 — Machine Learning

Com o Dataset 2, construir e comparar classificadores com TF-IDF e embeddings; avaliar accuracy, precision, recall, macro-F1 e F1 por classe; escolher a abordagem com critério declarado.

Construir também busca semântica sobre tickets similares, usando FAISS ou solução equivalente, e definir gates de confiança para escalonamento humano.

## FASE 6 — Protótipo funcional

Demonstrar Dashboard Executivo, visão operacional, AI Support Copilot e simulador de ROI. O Copilot deve receber texto e devolver categoria, prioridade, confiança, recomendação, equipe, similares e resposta sugerida.

**Evolução aprovada:** o primeiro protótipo em Streamlit foi substituído na entrega vigente por FastAPI + front-end web próprio. A mudança preservou o core analítico e ampliou a demonstração com portal do cliente, perfis, fila e loop de aprendizado. A stack não altera os requisitos funcionais.

## FASE 7 — Documentação

Produzir README seguindo o template oficial e cobrindo: resumo executivo, problema, metodologia, diagnóstico, solução, automação, protótipo, ROI, limitações e próximos passos.

## FASE 8 — Process log

Manter `ai-usage.md`, `decisions.md`, `iterations.md`, `prompts.md` e evidências complementares. Registrar ferramentas de IA, prompts relevantes, hipóteses, erros, correções, mudanças, validações e pontos de julgamento humano.

## Estrutura final esperada

```text
submissions/thales-barbosa/
├── README.md
├── solution/
│   ├── app.py
│   ├── bootstrap.py
│   ├── requirements.txt
│   ├── data/raw/
│   ├── docs/
│   ├── notebooks/
│   ├── src/
│   ├── tests/
│   └── web/
└── process-log/
    ├── project-plan.md
    ├── ai-usage.md
    ├── decisions.md
    ├── iterations.md
    └── prompts.md
```

## Critérios de aceite

- responder às três perguntas do challenge;
- usar os dois datasets e separar dado observado de premissa;
- demonstrar automação com guardrails;
- apresentar ROI reproduzível com implantação interna a R$ 0;
- possuir aplicação funcional e código testado;
- conter documentação, limitações e process log completos;
- permitir reconstrução por um avaliador a partir da submissão.
