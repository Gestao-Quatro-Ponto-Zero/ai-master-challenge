# Submissão — Gabriel Moreira — Challenge 003 (Lead Scorer)

## Sobre mim

- **Nome:** Gabriel Moreira
- **LinkedIn:** _https://www.linkedin.com/in/gmoreirasantos/_
- **E-mail:** gmoreira1santos@gmail.com
- **Challenge escolhido:** 003 — Lead Scorer (Vendas / RevOps)

---

## Executive Summary

Antes de propor qualquer score, testei se o cadastro sustenta uma previsão de conversão (qui-quadrado, Mann-Whitney, AUC com holdout temporal, testes de permutação) sobre os 6.711 negócios fechados: **nenhum atributo firmográfico prevê ganho ou perda** (AUC 0,49–0,51, p entre 0,26 e 0,97 em vendedor/setor/gerente/conta). A ferramenta não classifica probabilidade de conversão — ela ordena o funil por **valor em risco**: `SCORE = percentil(p̂ × VALOR × URGÊNCIA)`, acompanhado de `CONFIANÇA` (quanto o número está apoiado em dado real) e `ESTADO` (a ação recomendada), com `p̂` calibrado por encolhimento hierárquico (`k` derivado dos dados, sem constantes congeladas) e ajuste por setor (`mult_setor`, ±15%). Entreguei uma API FastAPI + frontend React rodando de ponta a ponta — priorização, filtros, revisão em lote, exportação CSV e alerta de sobrecarga por vendedor com sugestão de redistribuição —, tudo validado por um backtest reprodutível (`make validate`) que também documenta três tentativas de deixar o modelo mais granular que **pioraram** a previsão fora da amostra e foram descartadas, não escondidas.

---

## Solução

### Abordagem

Comecei pela pergunta que a maioria dos guias de lead scoring pula: **os dados sustentam um score de probabilidade de conversão?** Rodei testes estatísticos (qui-quadrado, Mann-Whitney, AUC de modelos preditivos com holdout temporal, testes de permutação) sobre os 6.711 negócios fechados — a resposta foi não, para todo atributo firmográfico testado. Só depois desenhei a alternativa que os dados sustentam: um score de **valor em risco**, calibrado com encolhimento hierárquico (empirical Bayes) e curvas de aging isotônicas.

O trabalho seguiu em ciclos de decisão → implementação → validação → correção:
1. Análise exploratória completa, documentada em [docs/analise-lead-scoring.md](./docs/analise-lead-scoring.md)
2. Sessão de "grilling" (perguntas estruturadas) para validar cada decisão contra os dados
3. Implementação via OpenSpec (proposta → specs → tasks → código)
4. Saneamento de dados (reclassificação de 653 negócios parados ≥200 dias) e análise de carga/fit por vendedor

### Resultados / Findings

**A fórmula final:**

```
p̂          = p̂(produto, idade) × mult_setor(produto, setor)               [encolhimento hierárquico, k derivado; mult_setor ±15%, neutro sem setor conhecido]
PRIORIDADE = p̂ × VALOR(produto, porte) × URGÊNCIA(idade)                   [dólares, auditável — não exibido]
SCORE      = percentil(PRIORIDADE vs. os 4.238 negócios historicamente ganhos) × 100
CONFIANÇA  = min(completude, suporte)                                      [0-100]
ESTADO     = árvore(sem_precedente, SCORE≥95, CONFIANÇA<50)
```

Derivação completa de cada termo em [docs/analise-lead-scoring.md](./docs/analise-lead-scoring.md). Como cada peça se conecta (API, frontend, validação) em [docs/architecture.md](./docs/architecture.md). Validação em [docs/report.md](./docs/report.md).

**Onde está a receita, contra onde está o esforço do time** — a distorção mais cara encontrada na análise:

<svg viewBox="0 0 900 400" xmlns="http://www.w3.org/2000/svg" style="border: 1px solid var(--text-secondary); border-radius: 4px;">
  <defs>
    <style>
      .chart-title { font-size: 16px; font-weight: bold; fill: var(--text-primary); }
      .chart-label { font-size: 12px; fill: var(--text-secondary); }
      .chart-value { font-size: 11px; fill: var(--text-tertiary); }
      .grid-line { stroke: var(--border-default); stroke-width: 0.5; }
      .axis-line { stroke: var(--text-secondary); stroke-width: 1.5; }
      .line-esforco { stroke: #4f46e5; stroke-width: 2.5; fill: none; }
      .line-receita { stroke: #059669; stroke-width: 2.5; fill: none; }
      .dot-esforco { fill: #4f46e5; }
      .dot-receita { fill: #059669; }
      .legend-text { font-size: 12px; fill: var(--text-primary); }
    </style>
  </defs>
  
  <!-- Title -->
  <text x="450" y="25" class="chart-title" text-anchor="middle">Esforço do Time vs Receita por Produto</text>
  
  <!-- Grid lines -->
  <line x1="80" y1="60" x2="80" y2="320" class="axis-line"/>
  <line x1="80" y1="320" x2="870" y2="320" class="axis-line"/>
  
  <!-- Horizontal grid -->
  <line x1="75" y1="220" x2="870" y2="220" class="grid-line"/>
  <line x1="75" y1="170" x2="870" y2="170" class="grid-line"/>
  <line x1="75" y1="120" x2="870" y2="120" class="grid-line"/>
  <line x1="75" y1="70" x2="870" y2="70" class="grid-line"/>
  
  <!-- Y-axis labels and values -->
  <text x="70" y="325" class="chart-label" text-anchor="end">0</text>
  <text x="70" y="225" class="chart-label" text-anchor="end">10</text>
  <text x="70" y="175" class="chart-label" text-anchor="end">20</text>
  <text x="70" y="125" class="chart-label" text-anchor="end">30</text>
  <text x="70" y="75" class="chart-label" text-anchor="end">40</text>
  
  <!-- Y-axis label -->
  <text x="20" y="190" class="chart-label" text-anchor="middle" transform="rotate(-90 20 190)">Percentual (%)</text>
  
  <!-- X-axis labels -->
  <text x="105" y="345" class="chart-label" text-anchor="middle">GTK500</text>
  <text x="195" y="345" class="chart-label" text-anchor="middle">GTXPlus</text>
  <text x="285" y="345" class="chart-label" text-anchor="middle">GTXPro</text>
  <text x="375" y="345" class="chart-label" text-anchor="middle">MG-Adv</text>
  <text x="465" y="345" class="chart-label" text-anchor="middle">GTXBasic+</text>
  <text x="555" y="345" class="chart-label" text-anchor="middle">GTXBasic</text>
  <text x="645" y="345" class="chart-label" text-anchor="middle">MG-Spec</text>
  
  <!-- Data points and lines -->
  <!-- Esforço %: [0.4, 10.7, 16.3, 15.9, 16.1, 22.3, 18.4] -->
  <!-- Receita %: [4.0, 26.3, 35.1, 22.2, 7.1, 5.0, 0.4] -->
  
  <!-- Esforço line -->
  <polyline points="105,317 195,287 285,263 375,265 465,263 555,247 645,259" class="line-esforco"/>
  
  <!-- Receita line -->
  <polyline points="105,304 195,224 285,139 375,211 465,294 555,300 645,318" class="line-receita"/>
  
  <!-- Data points - Esforço -->
  <circle cx="105" cy="317" r="3" class="dot-esforco"/>
  <circle cx="195" cy="287" r="3" class="dot-esforco"/>
  <circle cx="285" cy="263" r="3" class="dot-esforco"/>
  <circle cx="375" cy="265" r="3" class="dot-esforco"/>
  <circle cx="465" cy="263" r="3" class="dot-esforco"/>
  <circle cx="555" cy="247" r="3" class="dot-esforco"/>
  <circle cx="645" cy="259" r="3" class="dot-esforco"/>
  
  <!-- Data points - Receita -->
  <circle cx="105" cy="304" r="3" class="dot-receita"/>
  <circle cx="195" cy="224" r="3" class="dot-receita"/>
  <circle cx="285" cy="139" r="3" class="dot-receita"/>
  <circle cx="375" cy="211" r="3" class="dot-receita"/>
  <circle cx="465" cy="294" r="3" class="dot-receita"/>
  <circle cx="555" cy="300" r="3" class="dot-receita"/>
  <circle cx="645" cy="318" r="3" class="dot-receita"/>
  
  <!-- Legend -->
  <line x1="700" y1="50" x2="730" y2="50" class="line-esforco"/>
  <text x="740" y="55" class="legend-text">Esforço %</text>
  
  <line x1="700" y1="75" x2="730" y2="75" class="line-receita"/>
  <text x="740" y="80" class="legend-text">Receita %</text>
</svg>

MG Special + GTX Basic somam **39,6% dos negócios e 40,6% do esforço do time, para 5,4% da receita** — e MG Special tem a *maior* taxa de conversão da carteira (65%), a armadilha exata que um score de probabilidade de conversão premiaria. Detalhe em [docs/analise-lead-scoring.md §1.2 "Valor é altamente previsível"](./docs/analise-lead-scoring.md).

**Como o funil aberto atual (1.436 oportunidades) se distribui pela recomendação de ação:**

<svg viewBox="0 0 500 350" xmlns="http://www.w3.org/2000/svg" style="border: 1px solid var(--text-secondary); border-radius: 4px;">
  <defs>
    <style>
      .pie-title { font-size: 14px; font-weight: bold; fill: var(--text-primary); }
      .pie-label { font-size: 11px; fill: var(--text-primary); font-weight: 500; }
      .pie-value { font-size: 10px; fill: var(--text-secondary); }
      .legend-text { font-size: 11px; fill: var(--text-primary); }
    </style>
  </defs>
  
  <!-- Title -->
  <text x="250" y="20" class="pie-title" text-anchor="middle">ESTADO - Funil Aberto (1.436 deals)</text>
  
  <!-- Pie chart slices with proper angles -->
  <!-- Qualificar (656) = 45.6% = 0-164.16° -->
  <path d="M 250,180 L 250,80 A 100,100 0 0,1 383.58,134.73 Z" fill="#ef4444" opacity="0.8"/>
  
  <!-- Revisão lote (443) = 30.8% = 164.16-275.04° -->
  <path d="M 250,180 L 383.58,134.73 A 100,100 0 0,1 191.42,124.27 Z" fill="#f97316" opacity="0.8"/>
  
  <!-- Acompanhar (283) = 19.7% = 275.04-345.12° -->
  <path d="M 250,180 L 191.42,124.27 A 100,100 0 0,1 308.06,68.18 Z" fill="#eab308" opacity="0.8"/>
  
  <!-- Priorizar (54) = 3.8% = 345.12-360° -->
  <path d="M 250,180 L 308.06,68.18 A 100,100 0 0,1 250,80 Z" fill="#22c55e" opacity="0.8"/>
  
  <!-- Legend -->
  <g transform="translate(320, 100)">
    <!-- Qualificar -->
    <rect x="0" y="0" width="12" height="12" fill="#ef4444" opacity="0.8"/>
    <text x="18" y="10" class="legend-text">Qualificar (656) 45.6%</text>
    
    <!-- Revisão lote -->
    <rect x="0" y="20" width="12" height="12" fill="#f97316" opacity="0.8"/>
    <text x="18" y="30" class="legend-text">Revisão lote (443) 30.8%</text>
    
    <!-- Acompanhar -->
    <rect x="0" y="40" width="12" height="12" fill="#eab308" opacity="0.8"/>
    <text x="18" y="50" class="legend-text">Acompanhar (283) 19.7%</text>
    
    <!-- Priorizar -->
    <rect x="0" y="60" width="12" height="12" fill="#22c55e" opacity="0.8"/>
    <text x="18" y="70" class="legend-text">Priorizar (54) 3.8%</text>
  </g>
  
  <!-- Note -->
  <text x="250" y="320" class="pie-value" text-anchor="middle">Fila trabalhável: 993 oportunidades (Qualificar + Acompanhar + Priorizar)</text>
</svg>

`Revisão em lote` (sem precedente histórico de fechamento) fica fora da fila ordenada de trabalho — não é "negócio perdido", é passivo de higiene de dados a resolver em lote com o gestor. A fila trabalhável tem 993 oportunidades.

**Sobrecarga de vendedor e sugestão automatizada de redistribuição:**

Além de priorizar cada oportunidade, a ferramenta compara a carteira de cada vendedor com a média do próprio escritório regional em cada ESTADO, e marca como **sobrecarregado** o par (vendedor, ESTADO) que atende simultaneamente `contagem ≥ 1,5× a média do escritório` **e** `contagem ≥ 5` (piso absoluto — sem ele, um vendedor com 1 oportunidade num ESTADO raro apareceria como "10× a média" por puro ruído de amostra pequena). Sobre o funil atual: **12 pares sobrecarregados, 8 vendedores, 227 oportunidades**.

Para cada oportunidade de vendedor sobrecarregado, o sistema sugere um colega **do mesmo escritório**, não sobrecarregado naquele ESTADO, com histórico de negócios fechados — combinando folga de carga com o fit histórico do candidato no produto e no setor da oportunidade (`rank = 0,5×folga + 0,5×fit`, produto pesando 0,6 e setor 0,4). Quando não existe candidato elegível, o sistema reporta isso explicitamente em vez de forçar uma sugestão. **A sugestão é só informativa: nunca reatribui a oportunidade nem altera o dono registrado** — quem decide continua sendo o gestor.

Duas ressalvas importantes, aplicadas por design: (1) o fit por vendedor é **estatisticamente indistinguível de ruído** nesta base (mesmo teste de permutação da Seção 1/2 do backtest) — por isso toda superfície que exibe fit também exibe essa ressalva, e o fit nunca entra em `p̂`, VALOR, URGÊNCIA, SCORE, CONFIANÇA ou ESTADO; (2) o vendedor sugerido só aparece na aba **Sobrecarga** e no painel de detalhe da oportunidade — a listagem geral de Oportunidades recebe apenas um booleano `sobrecarregado`, nunca o nome do candidato. Detalhe técnico completo (fórmulas, encolhimento, endpoints) em [docs/architecture.md §Carga e fit por vendedor](./docs/architecture.md) e na spec formal [openspec/specs/workload-fit/spec.md](./openspec/specs/workload-fit/spec.md). Screenshots do fluxo em [process-log/screenshots/06-sobrecarga.png](./process-log/screenshots/06-sobrecarga.png) e [06b-sobrecarga-detalhe.png](./process-log/screenshots/06b-sobrecarga-detalhe.png).

**Validação:** `make validate` reproduz 9 achados estruturais (ausência de sinal firmográfico, colapso do encolhimento hierárquico, monotonicidade das curvas de aging, concentração de valor no topo da fila) e testa por validação cruzada três hipóteses de tornar o modelo mais granular — as três pioraram a previsão fora da amostra e foram descartadas, não escondidas. Saída completa comentada em [docs/report.md](./docs/report.md).

### Recomendações

1. **Realocar capacidade de MG Special/GTX Basic** para autosserviço ou um time de menor custo — libera ~14 vendedores-equivalentes para produtos que rendem de 10× a 400× mais por dia de esforço.
2. **Instrumentar dado comportamental** (timestamp de mudança de etapa, speed-to-lead, motivo de perda estruturado) — é a lacuna que explica a AUC de 0,50 e o próximo passo de maior retorno. Lista priorizada em [docs/analise-lead-scoring.md §6 "O que não foi implementado"](./docs/analise-lead-scoring.md).
3. Roadmap completo, com esforço e impacto estimados por item, em [docs/roadmap.md](./docs/roadmap.md) — inclui um job de monitoramento de notícias de conta como próximo passo de sinal externo.

### Limitações

- **Sem autenticação** — decisão consciente para um dataset público de demonstração; produção exigiria SSO/OIDC real com escopo por papel.
- **`p̂` varia só entre 0,60 e 0,75** — a ferramenta não prevê quem vai fechar, prioriza por valor e urgência. Isso é o achado central, não um bug a corrigir.
- **Sem persistência** — tudo em memória, recarregado a cada execução; CSV exportado é o artefato durável hoje.
- **Sem sinal comportamental** — nenhum dos 5 CSVs de origem carrega e-mail aberto, ligação atendida, ou visita ao site.

Lista completa e caminho de evolução em [docs/architecture.md §Limitações conhecidas](./docs/architecture.md) e [docs/roadmap.md](./docs/roadmap.md).

---

## Process Log — Como usei IA

Ver narrativa completa e cronológica em [process-log/narrative.md](./process-log/narrative.md).
Log de decisões (registro completo, entrada por entrada) em [process-log/decisions-log.md](./process-log/decisions-log.md).

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| Claude Code | Análise exploratória dos dados (AUC, permutação, encolhimento hierárquico), sessões de "grilling" para stress-testar decisões de design, geração de proposta/specs via OpenSpec, implementação completa (backend, frontend, validação), redesenho de CONFIANÇA/ESTADO, saneamento de dados e análise de carga/fit por vendedor |
| Cursor | Revisão e ajustes pontuais no código já gerado pelo Claude Code (backend/frontend) |

### Workflow

1. Análise exploratória sobre os CSVs brutos, corrigindo qualidade de dados antes de qualquer modelo (typos de setor, produto duplicado)
2. Sessão de perguntas estruturadas (32 perguntas, depois 33 numa segunda rodada) para forçar cada decisão de design contra evidência medida, não contra convenção — cada resposta validada com um script rodado nos dados reais, não estimada
3. Especificação formal via OpenSpec (proposta → design → specs testáveis → tasks) antes de qualquer código de produção
4. Implementação seguindo as tasks, com testes unitários e de contrato de API escritos junto
5. Verificação manual no navegador (não só testes automatizados) — dois bugs reais de UI foram achados dessa forma, não pelos testes
6. Dois ciclos de redesenho movidos por feedback de uso real (remoção de RBAC, redesenho de CONFIANÇA/ESTADO) e um ciclo de saneamento de dados movido pela própria recomendação da análise exploratória

Passo a passo detalhado, com data e o que foi decidido por mim vs. executado pela IA, em [process-log/narrative.md](./process-log/narrative.md).

### Onde a IA errou e como corrigi

- A primeira versão do redesenho de ESTADO fazia ESTADO derivar quase só de CONFIANÇA — eu apontei que eram dois eixos diferentes (quanto sei vs. o que fazer), e a IA corrigiu para uma árvore de decisão cruzando os dois.
- `constants.classificar_porte` só checava `employees is None`, mas o merge preenche ausência com `NaN` — `NaN < limiar` é sempre `False` em Python, então toda oportunidade sem conta caía silenciosamente em "Enterprise". Achado durante a implementação, não previsto no design; corrigido e a distribuição de ESTADO foi recalculada.
- `K_PRODUTO = 4` foi mantido como constante congelada numa calibração em que a recomputação estrita já mostrava colapso — a IA sinalizou a tensão em vez de esconder ou decidir sozinha; a decisão final (manter, depois remover em 2026-08-21 quando os dados mudaram e o nível de produto deixou de colapsar, substituindo por shrinkage derivado dos dados e adicionando `mult_setor`) foi minha, registrada em [process-log/decisions-log.md](./process-log/decisions-log.md).
- Assumir que a diferença em porcentagem de Win do vendedor vs setor e produto não importa, sendo que qualquer acréscimo em conversão pode fazer uma diferença brutal na receita.

### O que eu adicionei que a IA sozinha não faria

- A pergunta inicial de matar a hipótese de probabilidade de conversão antes de aceitar a fórmula pronta — sem isso, o projeto teria implementado um classificador com AUC 0,50 sem perceber.
- Insistir em validar cada resposta de design contra um script rodando nos dados reais, não em aceitar a resposta mais plausível.
- Pedir a segunda rodada de "grilling" depois de ver o sistema em uso real — os problemas de UX (CONFIANÇA forçando "desistir" para 61,8% do funil) só ficaram óbvios rodando a ferramenta, não lendo a spec.
- A decisão de negócio de implementar `mult_setor` mesmo com o resultado de validação cruzada negativo — julgamento de produto, não um resultado que os dados sozinhos indicavam.
- Um score de confiança sobre os dados, assim o time de vendas consegue analisar quais scores são realmente de qualidade.

---

## Evidências

- [x] Chat exports → [process-log/chat-exports/claude.md](./process-log/chat-exports/claude.md)
- [x] Git history (branch [`submission/gabriel-moreira`](https://github.com/ga987123/ai-master-challenge/tree/submission/gabriel-moreira))
- [x] Narrativa escrita → [process-log/narrative.md](./process-log/narrative.md)
- [x] Log de decisões → [process-log/decisions-log.md](./process-log/decisions-log.md)
- [x] Screenshots do produto e do workflow → [process-log/screenshots/](./process-log/screenshots/) (13 imagens: fluxo de oportunidades, filtros, revisão em lote, sobrecarga por vendedor, gestão/rollup, visão mobile)

---

_Submissão enviada em: 2026-08-21 (iniciada em 2026-08-18)_
