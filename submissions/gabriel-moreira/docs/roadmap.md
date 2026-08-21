# Roadmap — Lead Scorer

## O que foi construído

Ferramenta de triagem de pipeline por **valor em risco**, não por probabilidade categórica de
conversão. A evidência que sustenta essa escolha: em 6.711 negócios fechados, nenhum atributo
firmográfico isolado (vendedor, conta, setor, escritório) prevê ganho/perda — AUC ≈ 0,50, testes
de permutação com p entre 0,26 e 0,98 (ver [solution/report.md](./solution/report.md) e
[docs/architecture.md](./docs/architecture.md)).

```
PRIORIDADE = P̂ganho(produto, idade) × VALOR(produto, porte) × URGÊNCIA(idade)   [dólares, auditável]
SCORE      = percentil(PRIORIDADE contra os 4.238 negócios historicamente ganhos)   [0-100, número exposto]
CONFIANÇA  = min(completude, suporte)                                            [0-100, veracidade do dado]
ESTADO     = árvore(sem_precedente, SCORE≥95, CONFIANÇA<50)  →  Priorizar / Acompanhar / Qualificar / Revisão em lote
```

Entregue: API FastAPI + frontend React, sem autenticação (dataset público de demonstração — vendedor,
gerente e escritório são filtros ordinários, não escopo de sessão), validação reprodutível
(`make validate`, 9 seções incluindo três resultados negativos de refinamento testados e descartados)
e suíte de testes (unitário + e2e). Stack e detalhes completos em
[docs/architecture.md](./docs/architecture.md); decisões e porquês em
[docs/decisions-log.md](./docs/decisions-log.md).

**Limitação central, já documentada:** o modelo diferencia por valor e urgência, não por
probabilidade real — `p̂` varia só entre 0,60 e 0,75 porque não existe dado comportamental nos 5
arquivos de origem. É a lacuna que os itens abaixo endereçam.

---

## Próximos passos selecionados

### 1. Saneamento em lote do funil congelado — ✅ feito (2026-08-21)

A mediana de idade dos 2.089 negócios abertos era 165 dias — mais velha que o negócio mais longo
que já fechou na história (138 dias). Executado: oportunidades abertas há ≥200 dias (política,
distinta dos 138 dias observados) são reclassificadas como `Lost` na carga — 653 negócios,
funil aberto caindo de 2.089 para 1.436. O que resta em **Revisão em lote** (443, idade 154–199
dias) é passivo real de higiene de dados, não mais um depósito de quase dois terços do funil.
Detalhes em [docs/architecture.md](./docs/architecture.md) e
[docs/decisions-log.md](./docs/decisions-log.md) (entrada 2026-08-21).

### 2. Persistir histórico de score

Tudo roda in-memory hoje, recalculado a cada carga — não existe série temporal por negócio.

- **Ação:** banco gerenciado (ex.: Supabase) guardando SCORE/ESTADO/CONFIANÇA por negócio a cada
  execução do pipeline.
- **Esforço:** baixo-médio — schema simples, sem mudança na lógica de scoring.
- **Impacto de negócio:** habilita trajetória ("este negócio está piorando há 3 semanas", que a
  foto do dia não mostra), auditoria de decisão, e é pré-requisito técnico direto dos itens 6, 8
  e 9 abaixo — sem histórico, nenhum deles pode ser medido ou construído.

### 3. A/B do próprio score

Metade dos vendedores prioriza pela ferramenta, metade continua no processo atual; medir receita
por trimestre entre os dois grupos.

- **Esforço:** baixo em engenharia, médio em processo (requer coordenação com liderança de
  vendas e período de espera para significância estatística).
- **Impacto de negócio:** é a evidência que compra orçamento para a fase seguinte (instrumentação
  comportamental, modelo real) e defende a ferramenta com dado quando alguém perguntar se ela
  vale o custo. Sem isso, o valor de tudo o resto fica em opinião, não em número.

### 4. Forecast probabilístico (commit vs. upside)

Somar `p̂ × valor` com intervalo de confiança, agregado por escritório e trimestre.

- **Esforço:** médio — a fórmula unitária já existe; o novo trabalho é agregação, intervalo de
  confiança e visualização por período/escritório.
- **Impacto de negócio:** muda quem compra a ferramenta internamente. Sai de "ferramenta de
  priorização do vendedor" para "instrumento de forecast do CFO/head de vendas" — patrocínio
  mais alto, orçamento maior, e uma segunda razão de existir além da fila individual.

### 5. Modelo de sobrevivência para time-to-close

As curvas de aging atuais (`risco(t)`, `p_ganho(t)`) já são metade de um modelo de sobrevivência;
falta tratar censura formalmente (hoje é um corte fixo em 138 dias) e responder diretamente
"este negócio fecha neste trimestre ou no próximo".

- **Esforço:** médio-alto — requer troca do encolhimento em degraus atual por um modelo de
  sobrevivência real (ex.: Cox, Kaplan-Meier com covariáveis) e nova validação.
- **Impacto de negócio:** responde a pergunta que gestor de vendas mais faz — alocação de esforço
  dentro do trimestre corrente — com mais precisão do que o corte binário de hoje, e melhora a
  acurácia do próprio forecast do item 4.

### 6. Job de sinal externo: notícias da conta

Nenhum dos 5 CSVs de origem carrega sinal comportamental ou de contexto de mercado (ver
[docs/analise-lead-scoring.md §6](./docs/analise-lead-scoring.md)) — hoje a ferramenta só reage
ao que já está no CRM. Um gatilho de mercado (rodada de investimento, expansão, troca de
liderança, notícia negativa) é o tipo de evento que justifica contato imediato e que nenhuma
curva de aging consegue prever.

- **Ação:** job agendado (diário) que busca notícias recentes por conta vinculada (nome da conta
  + domínio/setor, via API de notícias ou busca), filtra por relevância comercial (funding,
  expansão, aquisição, mudança de C-level, sinais negativos) e, quando encontra algo relevante,
  notifica o vendedor responsável pela conta — no canal que já usa (e-mail/Slack), não numa aba
  nova a ser checada.
- **Esforço:** médio — a parte nova é o pipeline de ingestão/filtro de notícias e a integração de
  notificação; o roteamento "conta → vendedor responsável" já existe via `sales_teams.csv`.
- **Impacto de negócio:** é o primeiro sinal de **intenção externa** que a ferramenta passaria a
  ter — hoje ela só prioriza por valor e urgência de funil, nunca por "por que agora". Fecha parte
  da lacuna comportamental apontada em `analise-lead-scoring.md` §6 sem exigir instrumentação do
  CRM, que depende de terceiros para começar a coletar.

---
