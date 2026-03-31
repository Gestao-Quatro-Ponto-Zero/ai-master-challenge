# Submissão — Pedro Henrique Sonda — Challenge 003

## Sobre mim

- **Nome:** Pedro Henrique Sonda
- **LinkedIn:** https://www.linkedin.com/in/pedro-henrique-sonda-30ab35163/
- **Challenge escolhido:** 003 — Lead Scorer (Vendas / RevOps)

---

## Executive Summary

Construí uma ferramenta funcional em Streamlit que calcula um score de probabilidade (0-100) para cada deal aberto no pipeline, ajudando 35 vendedores a priorizarem onde focar seu tempo. O scoring é baseado em 4 fatores validados estatisticamente nos dados históricos (8.800 oportunidades) + bônus de recorrência para clientes que já compraram. A principal descoberta foi que nenhum deal na história do CRM fechou após 138 dias — o que permitiu identificar ~700 deals provavelmente mortos no pipeline atual. A ferramenta inclui Top 5 dinâmico com checklist de status, explicação detalhada de cada score, e alerta automático para deals na zona limite.

---

## Solução

### Abordagem

Segui um processo de 7 etapas antes de escrever uma linha de código:

1. **Compreensão do problema** — Documentei hipóteses sobre o que faz um deal fechar ANTES de ver os dados. Isso está em `process-log/hipoteses-iniciais.md`.

2. **Exploração dos dados** — Testei 13 hipóteses contra os dados reais. Várias caíram (tamanho da empresa é irrelevante, subsidiárias não importam). Outras se confirmaram com surpresas (deals Won levam mais tempo que Lost, não menos). Documentado em `process-log/exploracao-dados.md`.

3. **Definição da lógica** — Desenhei a fórmula no papel antes de codificar, passando por 6 versões. Cada versão corrigiu problemas da anterior (scores empatados → adicionei histórico da conta; stage penalizava Prospecting → removi do score; valor distorcia ranking → separei do score; tempo no pipeline estava desalinhado → recalibrei com cicle time real). Documentado em `docs/logica-scoring.md`.

4. **Construção iterativa** — 11 iterações de desenvolvimento (CONTEXT1 a CONTEXT11), cada uma com objetivo claro, problemas identificados, e soluções implementadas.

5. **Decisões de design de produto** — Excluí o vendedor do score (ferramenta é para ele, não sobre ele). Excluí o stage (score mede potencial, não progresso). Separei valor do score (naturezas diferentes). Cada decisão está justificada nos documentos de processo.

### Resultados

**A ferramenta (Streamlit):**
- Score de probabilidade 0-100 para cada deal aberto (2.089 deals)
- 4 fatores de scoring + boost de recorrência, todos validados com dados
- Top 5 dinâmico: deals saem quando o vendedor marca status (contatado/em negociação/concluído)
- Pontuação detalhada por fator para cada deal (transparência total)
- Filtros: faixa de valor, escritório, manager, vendedor, stage
- Ordenação: por probabilidade ou por valor (vendedor escolhe)
- Alerta automático para deals na zona limite (120-140 dias)
- KPIs do vendedor: taxa de conversão, ciclo médio, ticket médio
- Checklist de status persistente (salva em CSV)
- Explicação didática de como o score funciona
- Design visual inspirado na identidade do G4

**Principais insights dos dados:**
- Sazonalidade trimestral é universal: TODOS os setores e produtos convertem ~80% no fechamento de trimestre vs ~49% nos outros meses
- Nenhum deal fechou após 138 dias na história — ~700 deals abertos estão provavelmente mortos
- A combinação setor+produto é mais preditiva que cada um isolado (20pp de variação)
- O vendedor impacta 15pp na conversão, mas foi excluído do score por decisão de design
- 31.5% dos deals abertos são de clientes recorrentes (mesmo produto, mesma conta)

### Recomendações

**Para implementação imediata:**
1. Incluir campo `lead_source` no CRM — a origem do lead (recomendação, anúncio, outbound) mudaria significativamente a priorização
2. Revisar os ~700 deals com 140+ dias no pipeline — provavelmente estão mortos e poluem o funil
3. Usar a ferramenta como base para reuniões semanais de pipeline review

**Para evolução futura:**
1. Visão de gestor com fator vendedor incluído, para realocar esforço do time
2. Autenticação SSO integrada ao CRM para cada vendedor ver automaticamente seus deals
3. Validação retroativa: aplicar scoring nos deals históricos e medir acurácia
4. Modelo de ML quando houver mais features (lead source, interações, emails)

### Limitações

- Os dados são de 2016-2017 — a ferramenta usa data de referência calculada, não datetime.now()
- Sem campo de lead source, o scoring perde uma dimensão importante
- O close_value real varia -34% a +34% do preço de tabela, mas para deals abertos usamos o preço de tabela
- A sazonalidade pode ser artefato do período dos dados — precisaria de mais anos para confirmar
- O boost de recorrência usa normalização por 115 que, embora protegida pelo max(), adiciona complexidade

---

## Process Log — Como usei IA

> **Este bloco é obrigatório.** Sem ele, a submissão é desclassificada.

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| Claude (claude.ai) | Advisor estratégico: planejamento, análise de dados, definição de lógica de scoring, revisão de decisões, produção de documentação |
| Claude Code | Construção da aplicação Streamlit via vibe coding, com 11 iterações (CONTEXT1 a CONTEXT11) |

### Workflow

1. **Planejamento estratégico** — Usei o Claude como mentor para montar um plano de 7 etapas antes de tocar em código. Definimos juntos a postura de "consultor resolvendo problema real" vs "candidato fazendo prova".

2. **Hipóteses antes dos dados** — Escrevi minhas hipóteses sobre o que influencia o fechamento de deals ANTES de qualquer análise. O Claude me orientou a documentar isso como evidência de processo.

3. **Exploração de dados** — O Claude rodou análises nos CSVs e eu confrontei cada resultado com minhas hipóteses. Onde discordei (ex: tempo no pipeline), questionei e iteramos até chegar numa conclusão fundamentada.

4. **Lógica de scoring** — Desenhei a fórmula iterativamente. O Claude propôs, eu questionei (viés de sobrevivência no tempo, vendedor no score, valor esperado), e corrigimos juntos. A fórmula passou por 6 versões.

5. **Construção com Claude Code** — Cada iteração foi um CONTEXT.md com problema identificado, solução proposta, e checklist. O Claude Code gerou o código, eu testei, identifiquei problemas, e iteramos.

6. **Documentação** — O Claude organizou os documentos, mas o conteúdo (decisões, questionamentos, insights) é meu. Cada documento foi revisado e editado por mim.

### Onde a IA errou e como corrigi

1. **Faixas de tempo no pipeline (CONTEXT2):** A IA propôs penalizar deals com 90+ dias. Os dados mostraram o contrário (71.3% de conversão). Quase aceitei a inversão da IA, mas questionei: "isso não é viés de sobrevivência?" A IA concordou. Tornamos neutro. Depois, quando analisei o cicle time real (nenhum Won após 138 dias), recalibrei as faixas com dados concretos.

2. **Valor esperado (CONTEXT5):** A IA propôs Score Final = Probabilidade × Valor (valor esperado). Testamos e o ranking ficou dominado pelo GTK 500. Tentamos log, mas os scores ficaram artificialmente próximos. Eu questionei: "isso não faz sentido com dados reais de valor." Descartamos e separamos probabilidade de valor.

3. **Normalização do boost (CONTEXT8):** A IA aplicou divisão por 115 em TODOS os deals, incluindo os sem boost. Isso penalizava deals sem recorrência (score 84.9 virava 73.8). Identifiquei o erro e corrigimos para normalização condicional.

4. **Stage no score (CONTEXT4):** Inicialmente o stage era fator do scoring (Prospecting = 40pts, Engaging = 75pts). Eu questionei: "um deal com mesmo potencial não deveria ter score diferente só porque ainda não foi contatado." Removemos stage do score e transformamos em badge visual.

### O que eu adicionei que a IA sozinha não faria

1. **Visão de produto:** A decisão de excluir o vendedor do score veio da pergunta "como fica a questão do score se a ferramenta é para o vendedor usar e não o gestor?" — a IA não teria feito essa pergunta.

2. **Questionamento do viés de sobrevivência:** Quando os dados mostraram que deals antigos convertem mais, eu não aceitei de cara. Perguntei "isso não é porque os ruins já caíram antes?" — raciocínio que exige contexto de negócio.

3. **Separação de valor e probabilidade:** Após testar 3 fórmulas que não funcionavam, eu disse "a conta de valor esperado não faz sentido com dados reais." A IA estava tentando forçar uma solução matemática. Eu propus: deixa o vendedor escolher como ordenar.

4. **Insight do cicle time de 138 dias:** A IA não teria destacado espontaneamente que zero deals fecharam após 138 dias. Esse dado mudou completamente as faixas de tempo e identificou ~700 deals provavelmente mortos.

5. **Recorrência como boost, não fator:** Quando analisamos que contas compram o mesmo produto repetidamente, eu defini: "não quero penalizar quem não tem recorrência, quero bonificar quem tem." Isso moldou o design do boost aditivo.

---

## Evidências

- [x] Git history — commits mostrando evolução do projeto
- [x] Chat exports — esta conversa com Claude (advisory) + Claude Code (construção)
- [x] Process log narrativo — hipoteses-iniciais.md, exploracao-dados.md, logica-scoring.md
- [x] Documentação dos 11 contexts de iteração (CONTEXT1 a CONTEXT11)
- [x] Código funcional com instruções de setup

---

*Submissão enviada em: 30/03/2026*
