# Lead Scorer — Plano de Projeto e Design da Solução
### Challenge 003 · Vendas / RevOps · Oficina Martech

> Documento de design escrito **antes da construção**, fundamentado em análise exploratória dos dados reais. Objetivo: deixar explícito o raciocínio de produto e de engenharia por trás de cada decisão, para que a solução seja avaliada como um sistema deliberado — não um protótipo improvisado.

---

## 1. O problema (na linguagem da Head de RevOps)

35 vendedores, ~8.800 oportunidades históricas, **2.089 deals abertos agora**. A priorização é "no feeling": cada vendedor decide no instinto onde focar. O custo disso é duplo e mensurável:

- **Esforço em deal que não fecha** — tempo gasto em oportunidades de baixa probabilidade.
- **Boa oportunidade esfriando** — deals com chance real que perdem o timing por falta de atenção.

A Head foi explícita: *"não quero um modelo no Jupyter que ninguém usa. Quero uma ferramenta que o vendedor abra na segunda de manhã, veja o pipeline e saiba onde focar."* O deliverable é **software que roda e gera decisão**, com o vendedor entendendo **por que** cada deal tem o score que tem.

## 2. Tese da solução (resumo executivo)

Construímos o **Foco do Dia** — uma aplicação que lê o pipeline do CRM e devolve, para cada vendedor, a **lista priorizada de deals abertos** com **score 0-100, motivo explícito e ação recomendada**. O score combina três sinais que a análise provou relevantes — probabilidade de fechamento, valor esperado e urgência (deal esfriando) — e **descarta deliberadamente** os sinais que a análise provou irrelevantes. Cada número é defensável célula a célula com dados históricos, e a interface é desenhada para **decisão**, não para exibição.

O diferencial central não é o algoritmo — é o **julgamento**: medimos o que tem sinal, rejeitamos o que é ruído, derivamos os thresholds dos dados reais, e tornamos tudo auditável e explicável. É exatamente o que a IA "colando o brief" não faz.

## 3. Descobertas que fundamentam o design (EDA)

Antes de desenhar o scoring, exploramos os 4 CSVs cruzados (evidência em `../process-log/execucoes/eda-output.txt`, decisões em `decisoes.md`). Achados que moldaram cada escolha:

| # | Descoberta | Número | Implicação de design |
|---|-----------|--------|----------------------|
| 1 | Sinal preditivo está **quase todo no vendedor** | win-rate por vendedor **55–70%** (spread 15pp) | Probabilidade = win-rate histórico do vendedor (suavizado) |
| 2 | Produto/setor/região/valor **não diferenciam** | todos **<5pp** de spread (≈63%) | **Descartados** como features de probabilidade — não inflar com ruído |
| 3 | Ciclo de fechamento real | Won: mediana **57d**, p75 **88d**, máx **138d** | Urgência data-driven em curva sino: pico em 57–88d, decai até 138d, piso além (não chutado) |
| 4 | Deals perdidos morrem rápido | Lost mediana **14d** | Aging só penaliza deals que passaram do ciclo *vencedor* |
| 5 | Valor não muda probabilidade | win-rate flat por faixa de preço | Priorizar por **valor esperado** (prob × valor), não valor bruto |
| 6 | Buracos de CRM | **1.425 deals sem conta = 68% dos abertos** (16% do total); 500 Prospecting sem `engage_date`; `GTXPro`≠`GTX Pro` | Tratar join, renormalizar pesos, **reportar a higiene como insight de RevOps** |

> Este é o ponto que separa a entrega do baseline: a maioria das soluções pesa todas as features igualmente porque a IA assume que "mais features = melhor". Os dados dizem o contrário. **Rejeitar produto/setor/região com evidência é a decisão mais valiosa do projeto.**

## 4. Princípios de design

1. **Explainability primeiro.** Todo score vem com breakdown por fator (feature, peso, pontos, porquê) em linguagem de vendedor. Um número sem motivo não entra no app.
2. **Honesto > sofisticado.** Sinal fraco (63% base) não justifica ML opaco. Scoring por regras + estatística defensável, calibrado nos dados, vale mais e é manutenível.
3. **Orientado à decisão.** A tela responde "o que eu faço hoje?", não "como está o pipeline?". Foco do dia, ação por deal, filtros por vendedor/manager/região.
4. **Reprodutível e auditável.** Toda a lógica versionada no repo, calculada dos CSVs reais em runtime — **nada pré-computado, nada em ferramenta externa**.
5. **Testado.** O motor de scoring tem testes unitários; roda do zero seguindo o README.

## 5. Arquitetura

```
                 ┌──────────────────────────────────────────┐
   CSVs (CRM)──▶ │  scoring/  (Python puro, sem UI)          │
                 │  ├─ data.py     load + join + fix higiene │
                 │  ├─ features.py win-rate smoothed, aging  │
                 │  ├─ model.py    score + breakdown por deal│
                 │  └─ config.py   PESOS e thresholds (const)│
                 └───────────────┬──────────────────────────┘
                                 │ importado por
                 ┌───────────────▼──────────┐   ┌───────────────┐
                 │  app/  (Streamlit)        │   │ tests/ (pytest)│
                 │  Foco do Dia · filtros ·  │   │ scoring puro   │
                 │  detalhe+porquê · manager │   └───────────────┘
                 │  theme.py (tokens de marca)│
                 └───────────────────────────┘
   .streamlit/config.toml  → tema (cores da marca, ver branding/)
```

- **Núcleo desacoplado da UI:** o motor é um módulo puro testável — outro dev mantém, e dá para expor via API/CLI/bot sem reescrever (extensibilidade real).
- **Stack:** Python + Streamlit (sobe em 3 comandos, sem API key). Simples por decisão, não por limitação.

### 5.1 Persistência: migrations + seed (instala em qualquer lugar)

Para o avaliador instalar e validar 100% sem fricção, a solução tem **camada de banco portável** (`db/`):
- **SQLite** (stdlib do Python — sem servidor, sem Docker, sem credencial: roda em qualquer máquina).
- **Migrations versionadas** (`migrations/0001_init.sql`, `0002_views.sql`) com runner idempotente que rastreia o que já aplicou (`schema_migrations`).
- **Seed dos dados reais** (`seed.py`): carrega os 4 CSVs, aplica a limpeza da EDA (`GTXPro→GTX Pro`, vazios→NULL) e **valida as contagens** (7/85/35/8800) — o banco já nasce correto e testável.
- **Views auditáveis** (deals abertos, win-rate por vendedor, saúde do pipeline) para conferência direta no banco.

Instalação completa: `make setup` (= install + migrate + seed) → `make run`. Detalhes em `db/README.md`. *Validado: migrate + seed rodam limpos e idempotentes.*

## 6. Modelo de scoring (a lógica, justificada)

Para cada deal aberto, três componentes:

**(A) Probabilidade de fechamento** — `P`
- **Exclusivamente o win-rate histórico do vendedor**, suavizado por Bayes: `P = (wins + k·p0) / (n + k)`, com `p0 = 0,632` (base global) e `k = 8`. Justificativa: win-rate cru em célula pequena é instável; o smoothing puxa vendedores com pouco histórico para a média até haver evidência.
- **Produto, setor, região e manager não entram** — a EDA mostrou spread <5pp nessas dimensões (ruído, não sinal).

**(B) Tamanho do deal** — percentil do `sales_price` na população aberta. Decisão deliberada: o componente de valor usa o **tamanho puro**, não `P × valor` — a probabilidade já tem componente próprio, e usá-la também no valor a contaria duas vezes, distorcendo os pesos declarados. O **valor esperado** (`EV = P × sales_price`) é calculado como métrica **informativa** para monetizar risco nas visões de manager e RevOps ("R$ X em risco"), mas fica fora do score.

**(C) Urgência (aging)** — só para deals **Engaging** (têm `engage_date`). É uma **curva sino** ancorada no ciclo dos Won, **não** monotônica: a chance de fechar sobe até a janela produtiva e **decai** depois (deal velho provavelmente morreu — nenhum Won passou de 138d). Um deal de 300d tem urgência **baixa** (piso), não máxima.
- `0 → 57d` (até a mediana Won): **esquentando** — subscore sobe 0→100.
- `57 → 88d` (mediana→p75): **janela ideal** — platô em 100, é onde a maioria fecha.
- `88 → 138d` (p75→Won mais velho): **janela fechando** — decai 100→10 (severidade `alerta`).
- `> 138d`: **além do ciclo histórico** — piso 10 (severidade `critico`) e marcado `is_stale` (sai do foco).
- **Prospecting** (sem `engage_date`): componente de aging removido e **pesos renormalizados** — não penalizamos por falta de dado.

**Score final (0-100):** combinação normalizada ponderada de A/B/C, com **pesos declarados em `config.py`** (constante com `assert` de soma = 1) e justificados aqui. Tiers operacionais: **Foco Agora / Trabalhar / Baixa Prioridade** por faixa de score, calibrados para não jogar metade do pipeline numa categoria genérica.

> Cada deal carrega `breakdown = [{feature, valor, peso, pontos, porquê}]` — é isso que vira a explicação na tela.

## 7. Explainability (o que o vendedor vê)

Para o deal de score 84:
> **Score 84 · Foco Agora** 🔥
> • Vendedor fecha 70% historicamente — top 15% do time (+) — *seu maior trunfo neste deal*
> • Tamanho do deal R$ 3.150 — top 20% do pipeline (+)
> • Aberto há 64 dias — janela ideal de fechamento (57–88d) (urgência no pico)
> **Ação:** priorizar contato hoje; está na janela em que mais deals fecham.

> O percentil ("top 15% do time") é mostrado ao lado do "fecha 70%" porque os **pontos** do score derivam do percentil de P na população (rank robusto), não do % absoluto — display e mecanismo precisam bater.

Linguagem de negócio, fator a fator, com a ação. O vendedor entende e age — não interpreta um número solto.

## 8. Experiência, marca e UX

O produto tem identidade própria — **Foco** ("O que fechar primeiro.") — e um design system definido **antes do código**, para ser uma ferramenta com a qual o vendedor *quer* trabalhar, não um Streamlit cru. Especificação completa em `branding/BRANDING.md` (marca, paleta semântica de prioridade, tipografia, voz, tema do Streamlit) e `branding/UI-UX.md` (wireframes, componentes, estados, dicas in-app, acessibilidade AA).

- **Foco do Dia:** top 5-7 deals do vendedor por score, agrupados por tier (🔥 Foco Agora / ⭐ Trabalhar / ⏳ Baixa), com score grande, motivo em 1 linha e ação. Lista curta e priorizada, não tabela de 2.089 linhas.
- **Filtros:** vendedor · manager · regional (bônus do brief) — manager vê o time, RevOps vê tudo.
- **Detalhe do deal:** breakdown do score fator a fator (o "porquê") em linguagem de vendedor.
- **Painel de saúde (RevOps):** os 68% dos deals abertos sem conta e o ciclo médio — higiene de dados virando insight acionável.
- **Princípios:** decisão em 3 segundos · cor semântica (sempre com ícone+texto) · dicas/tooltips de onboarding · todos os estados (vazio/carregando/sem dado) tratados.

## 9. Plano de execução por fases (com evidência)

| Fase | Entrega | Evidência capturada | Status |
|------|---------|---------------------|--------|
| 1. Entender | hipóteses escritas antes dos dados | `process-log.md` (G1) | ✅ |
| 2. EDA | sinal medido, features validadas/rejeitadas | `eda-output.txt`, `decisoes.md` | ✅ |
| 3. Núcleo `scoring/` | motor puro + breakdown | git + testes | ▶ próximo |
| 4. Testes | pytest do scoring | `tests/` | |
| 5. App | Foco do Dia + filtros + detalhe | screenshots | |
| 6. Revisão de qualidade | auto-revisão contra os critérios, corrigir gaps | checklist interno | |
| 7. README + process log | narrativa final + evidências | submissão | |
| 8. PR | abrir no repo do G4 | git | |

## 10. Qualidade e testes

- Motor puro testável: testes de win-rate suavizado (célula cheia vs vazia), de renormalização de pesos (Prospecting), de monotonicidade (mais prob/valor ⇒ mais score), de tratamento do join `GTXPro`.
- Código: lógica separada da UI, pesos/thresholds em constantes nomeadas, type hints, sem duplicação.
- Roda do zero: `pip install -r requirements.txt && streamlit run app/...` documentado.

## 11. Métricas de sucesso (como a RevOps mede valor)

- **Adoção:** vendedor abre na segunda e age a partir da lista.
- **Precisão de priorização:** dos deals marcados "Foco Agora", quantos fecham vs a base de 63%.
- **Tempo economizado:** menos horas em deals de baixa probabilidade.
- **Higiene:** redução dos 68% de deals abertos sem conta após o report.

## 12. Limitações (honestidade explícita)

- **Dataset histórico/possivelmente sintético:** o sinal é fraco (63% base, features chapadas). Reportamos isso em vez de fabricar precisão. Em produção, a maior alavanca seria registrar **interações reais** (última atividade), hoje ausente — `engage_date` é um proxy fraco.
- **Sem histórico de transição de estágio:** Prospecting vs Engaging não tem trilha temporal rica; aging só é confiável para Engaging.
- **Win-rate do vendedor é histórico:** vendedor novo cai na base global até acumular dados (o smoothing já trata isso).

## 13. Como isto supera o baseline da IA

| O que a IA sozinha faz | O que entregamos |
|------------------------|------------------|
| Pesa todas as features (produto, setor, região) | **Mede e rejeita** as que são ruído, com evidência |
| Threshold de aging arbitrário | Derivado do **ciclo real** (57/88d) |
| Score solto | **Breakdown por fator** em linguagem de vendedor |
| Ignora higiene de dados | Detecta join quebrado e **68% dos abertos sem conta** como insight |
| Notebook/dashboard que mostra dados | Ferramenta que **decide** (Foco do Dia + ação) |
| Lógica em ferramenta externa | Tudo **versionado, testado, reprodutível** |

## 14. Roadmap de produção (se virar real)

1. Tabela de **interações** (última atividade real) → substitui `engage_date` como proxy; maior ganho de precisão.
2. Feedback loop: marcar deals "Foco Agora" e medir conversão para recalibrar pesos.
3. Integração CRM (webhook) + entrega por Slack/WhatsApp do Foco do Dia.
4. Correção da higiene na origem (campo conta obrigatório).

---

*Próxima ação: construir a Fase 3 (núcleo `scoring/` + testes) conforme este design, com process log ao vivo.*
