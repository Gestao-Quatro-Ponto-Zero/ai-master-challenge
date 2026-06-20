# Submissão — Oficina Martech — Challenge 003 (Lead Scorer)

> Folha de submissão formal (segue `templates/submission-template.md`).
> Para **rodar** e entender o produto em detalhe, comece pelo [`docs/GUIA-DO-PRODUTO.md`](docs/GUIA-DO-PRODUTO.md).
> Design completo: [`docs/PLANO-DO-PROJETO.md`](docs/PLANO-DO-PROJETO.md) · decisões e verificações: [`docs/decisoes.md`](docs/decisoes.md) · redesenho de processo: [`docs/REDESENHO-DE-PROCESSO.md`](docs/REDESENHO-DE-PROCESSO.md) · processo ao vivo: [`process-log/process-log.md`](process-log/process-log.md) · código: [`solution/`](solution/).

## Sobre mim

- **Nome:** Kehlween Zascha Nienow Wirmond
- **LinkedIn:** https://pt.linkedin.com/in/kehlween
- **Challenge escolhido:** 003 — Lead Scorer · Vendas / RevOps
- **Demo ao vivo:** https://ai-master-challenge-whltkcmfjkn7qsrufhr3es.streamlit.app/ (Streamlit Cloud)
- **Como rodar local:** 3 comandos (`make setup && make run`) — SQLite + Streamlit, sem API key nem Docker. Passo a passo em [`docs/GUIA-DO-PRODUTO.md`](docs/GUIA-DO-PRODUTO.md).

---

## Executive Summary

Construí o **Foco** — uma aplicação (Streamlit + SQLite) que lê o pipeline real do CRM (~8.800 oportunidades, 35 vendedores, **2.089 deals abertos**) e devolve, por vendedor, a **lista priorizada de deals abertos** com **score 0-100, o porquê fator a fator, e a ação recomendada**. O achado que define o projeto: **o sinal preditivo está quase todo no vendedor** (win-rate com spread de 15pp), enquanto produto, setor, região e valor são ruído (<5pp) — então **medi e rejeitei essas features com evidência**, em vez de empilhá-las como faria uma IA "colando o brief". A recomendação central para a RevOps: adotar o Foco do Dia como rotina de segunda-feira e atacar a higiene de CRM (68% dos deals abertos sem conta), que hoje é a maior alavanca de precisão.

---

## Solução

O **Foco** ("O que fechar primeiro.") tem três telas, uma por papel:

| Tela | Para quem | O que entrega |
|------|-----------|---------------|
| **Foco do Dia** | Vendedor | Top deals por tier (🔥 Foco Agora / ⭐ Trabalhar), brief executivo do dia, breakdown do score por deal, seção 🩺 Revisar/Descartar — e **ação por deal** (✓ Contatado · ✕ Descartar · ↩ Reativar), persistida e auditável |
| **Time** | Manager | Foco Agora por vendedor, pipeline esperado e **receita em risco em R$**, deals a descartar, **export CSV "CRM-ready"** |
| **Saúde** | RevOps | 68% dos deals abertos sem conta (R$ quantificado), receita esfriando, ciclo médio, **log de auditoria** das ações |

**Stack:** Python + Streamlit + SQLite — roda em 3 comandos, sem API key, sem Docker, sem credencial. Núcleo de scoring (`scoring/`) é módulo puro e testável, desacoplado da UI.

### Abordagem

Comecei pelo **problema de negócio**, não pela ferramenta. Escrevi hipóteses **antes** de olhar os dados (`process-log/process-log.md`, Fase 1), rodei uma EDA cruzando os 4 CSVs para **medir o sinal de cada dimensão** (`process-log/execucoes/eda-output.txt`) e só então desenhei o scoring — documentado **antes do código** em `docs/PLANO-DO-PROJETO.md`. Princípio condutor: **explainability primeiro e honesto > sofisticado** — sinal fraco (base 63%) não justifica ML opaco; regras + estatística defensável, calibradas nos dados reais, valem mais e são manuteníveis.

Modelo: `score = 45% probabilidade + 35% tamanho do deal + 20% urgência`.
- **Probabilidade** = win-rate histórico do vendedor com smoothing bayesiano (`k=8`, prior `p0=0,632`) — única dimensão com sinal real.
- **Tamanho** = percentil do `sales_price` na população aberta (valor puro; `EV = P × valor` fica fora do score para não contar P duas vezes, e vira métrica de risco em R$).
- **Urgência** = dias abertos vs ciclo real de fechamento (mediana 57d / p75 88d, medidos nos Won), só para deals Engaging; Prospecting não é penalizado (pesos renormalizam).
- Deals "mortos" (`days_open > 138d` = o Won mais velho da história; nenhum fechou além disso) saem do foco e viram insight de pipeline inflado — **61,8% dos abertos**.

### Resultados / Findings

Achados da EDA que fundamentaram cada decisão (evidência em `process-log/execucoes/eda-output.txt`):

| Descoberta | Número | Implicação |
|-----------|--------|------------|
| Sinal está **no vendedor** | win-rate 55–70% (spread **15pp**) | Probabilidade = win-rate do vendedor (suavizado) |
| Produto/setor/região/valor **não diferenciam** | todos **<5pp** (~63%) | **Descartados** — não inflar com ruído |
| Ciclo de fechamento real | Won: mediana **57d**, p75 **88d** | Urgência data-driven (não chutada) |
| Buracos de CRM | **1.425 deals (68% dos abertos) sem conta**; `GTXPro`≠`GTX Pro` | Tratar join, **reportar higiene como insight** |

Produto entregue: app rodando, 3 telas, 31 testes (pytest), seed que valida contagens 7/85/35/8800. Screenshots das telas em `process-log/screenshots/`.

### Recomendações

1. **Adotar o Foco do Dia como rotina** — vendedor abre na segunda, age pela lista priorizada em vez do feeling.
2. **Atacar a higiene de CRM** — **68% dos deals abertos** sem conta (1.425 de 2.089; 16% do pipeline total) são o maior bloqueio de precisão; corrigir na origem (campo conta obrigatório).
3. **Registrar interações reais** (última atividade por deal) — hoje `engage_date` é proxy fraco; essa é a maior alavanca de ganho preditivo em produção.
4. **Fechar o loop de feedback** — marcar deals "Foco Agora" e medir conversão vs a base de 63% para recalibrar pesos.

### Limitações

- **Dataset histórico (snapshot ~2017) e possivelmente sintético:** sinal preditivo fraco (base 63%, features chapadas). Reportei isso em vez de fabricar precisão que os dados não suportam.
- **`engage_date` é proxy fraco de atividade** — sem histórico de interações reais, a urgência só é confiável para Engaging.
- **Sem trilha de transição de estágio** — Prospecting vs Engaging não tem timeline rica.
- **Win-rate do vendedor é histórico** — vendedor novo cai na base global até acumular dados (o smoothing já trata).

---

## Process Log — Como usei IA

> Detalhe completo e ao vivo em [`process-log/process-log.md`](process-log/process-log.md). Resumo abaixo.

### Ferramentas usadas

| Ferramenta | Para que usei |
|------------|---------------|
| **Claude Code Opus 4.8 (High)** | **Mapeamento inicial do projeto**: leitura do contexto, entendimento do desafio, análise exploratória dos 4 CSVs (EDA), design do modelo de scoring, código do núcleo (`scoring/`), app Streamlit, testes, e geração do tema/UI da marca — escolhido por captar melhor comportamento por perfil (ex.: comercial). "Vibe coding" + análise no mesmo loop |
| **Codex 5.5 (High, app Codex)** | Polish visual direto no app rodando em `localhost:8501`: removeu `st.code` escuro do brief (substituído por painel claro de prioridades acionáveis), ajustou tokens ink remanescentes, estilizou o segmented control Lista/Kanban |
| **OpenCode + GLM 5.2** | Análise independente dos dados e **revisão de cálculos do modelo**: identificou que a urgência estava calibrada na distribuição dos Won (mediana 57d) enquanto os deals abertos têm mediana 165d — distribuições incompatíveis. Propôs e aplicou: recalibração da urgência nos abertos, clamp do win-rate em [0,1], rebaixamento de tier para deals stale |
| **Python (pandas)** | Exploração dos dados e protótipo do scoring |
| **Streamlit + SQLite** | App e persistência portável (roda em qualquer máquina) |

A IA foi a alavanca de execução; meu papel foi **decidir o que medir, desconfiar dos resultados e cortar o que não tinha sinal**.

### Workflow

1. **Mapeamento e contexto (Claude Code Opus 4.8 High)** — leitura do brief, entendimento do desafio, análise das 4 tabelas, escrita das 5 hipóteses (H1–H5) antes de abrir os dados.
2. **EDA para medir sinal (Opus 4.8 High)** — cruzei os 4 CSVs e medi o spread de win-rate por dimensão; rejeição empírica de features.
3. **Design antes do código** — `PLANO-DO-PROJETO.md` com pesos e thresholds justificados pelos dados.
4. **Núcleo puro + testes** — `scoring/` desacoplado da UI, 31 testes (pytest).
5. **App de decisão + tema da marca** — 3 telas (vendedor/manager/RevOps) + camada de ação persistida; tema/UI gerado com Claude Opus 4.8 a partir de comportamento por perfil (ex.: comercial).
6. **Revisão de cálculos e bugs (GLM 5.2 via OpenCode)** — calibração de urgência, fix do filtro regional em Saúde, auditoria das métricas do pipeline completo.
7. **Polish visual (Codex 5.5 High)** — refinamento visual direto no app rodando em `localhost:8501`.

### Onde a IA errou e como corrigi

- **Pesar features iguais (H2 refutada):** apostei que produto/setor/região diferenciariam — a EDA mostrou <5pp. **Descartei com evidência.** A IA "colando o brief" pesaria tudo igual; o valor foi **testar e rejeitar**.
- **Bug do `days_open`:** `julianday('now')` num dataset de ~2017 marcava todo deal com 3.000+ dias e saturava a urgência. Corrigi ancorando à última data do dataset (`MAX(close_date)`).
- **P contando duas vezes:** o componente de valor usava `P × sales_price`. Corrigi para tamanho puro; criei teste de regressão `test_value_independe_de_P`.
- **Limiar de "deal morto" mal calibrado:** o primeiro (p90 = 106d) marcava 69% do pipeline como morto. Recalibrei para `WON_MAX_DAYS = 138d` (nenhum deal Won na história passou disso — além é, por dados, morto) e reportei como insight de pipeline inflado.
- **Breakdown divergindo do score:** passei a derivar o score da soma das parcelas do breakdown — invariante "soma == score" por construção.
- **UI gerada por IA veio não-finalizada (Codex/refino visual):** a nova interface entregue **não subia** — `breakdown_html` estava sem o `def` (corpo órfão após `kanban_head_html`) e o `main.py` importava essa função → `ImportError` no boot. O `.streamlit/config.toml` também ficou com a paleta do tema antigo (roxo `#8B5CF6`) em vez do indigo da marca (`#4F46E5`), e telas do corpo comercial além do "Foco do Dia" não estavam finalizadas no padrão visual novo. Corrigi o import, alinhei o tema ao `BRANDING.md`, validei o **boot real (HTTP 200) + a suíte de testes** e finalizei as telas faltantes. **Lição:** UI gerada por IA exige verificação de import/boot e **cobertura de todas as telas** — não só da tela "hero" que a IA caprichou.

### O que eu adicionei que a IA sozinha não faria

Rejeição **empírica** de features óbvias (spread medido, não assumido); thresholds de aging derivados do **ciclo real** (57/88d); detecção do join quebrado (`GTXPro`) e do buraco de RevOps (**68% dos abertos sem conta**) **antes** de modelar; e a transformação de "app que mostra dados" em **ferramenta que decide** (brief do dia, receita em risco, ação persistida).

---

## Evidências

- [x] **Demo ao vivo (Streamlit Cloud)** — https://ai-master-challenge-whltkcmfjkn7qsrufhr3es.streamlit.app/
- [x] **Como rodar local** — 3 comandos (`make setup && make run`), sem API key nem Docker; banco auto-inicializa no primeiro boot
- [x] **Git history** — evolução do código com desenvolvimento assistido por IA
- [x] **Narrativa escrita** — [`process-log/process-log.md`](process-log/process-log.md) + [`docs/decisoes.md`](docs/decisoes.md)
- [x] **Chat exports / conversas com IA** — `process-log/chat-exports/`: sessão Claude Code Opus 4.8 + sessão OpenCode GLM 5.2
- [x] **Execuções** — `process-log/execucoes/`: `eda-output.txt`, `pytest.txt`, `install-migrate-seed.txt`, `score-distribuicao.txt`, `app-smoke-test.txt`
- [x] **Screenshots das telas do produto** (em `process-log/screenshots/`)
  - `tela-foco-lista.png` — Foco do Dia · Lista (cards com badge ⚠ sem conta, ação por deal)
  - `tela-foco-kanban.png` — Foco do Dia · Kanban (3 colunas por tier: 🔥 Foco Agora / ⭐ Trabalhar / ⏳ Baixa)
  - `tela-foco-brief.png` — Brief do dia expandido (must-acts numerados, cada um liderado pelo **motivo opinativo** — driver dominante: ticket / win-rate / janela — + ação por linha e badge de tier; mesma fonte do brief `.txt`)
  - `tela-foco-breakdown.png` — "Por que esse score?" expandido (fator a fator com percentil **"· top 75% / top 6%"** — display = mecanismo — e badge ⚠ **sem conta** no card)
  - `tela-time.png` — Visão Time (Cara Losch, 4 vendedores, R$ 54.467 em risco, rep cards + botão "Ver deals →")
  - `tela-time-tabela.png` — Time · tabela completa por vendedor (Foco Agora / pipeline / em risco 88–138d / revisar)
  - `tela-saude.png` — Saúde · Higiene no topo (2.089 abertos, **68% sem conta**, R$ 302.340 em risco, breakdown sem conta por vendedor)
  - `tela-saude-scoreboard.png` — Saúde · scoreboard histórico (conversão 63,2%, R$ 10 mi, funil Won/Lost/Aberto, por produto/regional, ranking)
- [x] **Screenshots de processo** (ferramentas usadas, em `process-log/screenshots/`)
  - `claude-design-interface.png` — Claude Opus 4.8 prototipando a interface Foco
  - `opencode-glm52-validacao.png` — OpenCode+GLM 5.2 validando boot + fixes
  - `glm52-analise-calculos.png` — GLM 5.2 revisando calibração da urgência
  - `glm52-auditoria-pipeline.png` — GLM 5.2 auditoria das métricas (8.800 registros)
  - `glm52-fix-regional-saude.png` — GLM 5.2 corrigindo filtro Regional em Saúde
  - `glm52-tasklist-bugs.png` — GLM 5.2 task list de red flags (stale 138d, denominador 68%)
  - `codex55-polish-visual.png` — Codex 5.5 High aplicando polish visual
- [x] **Screen recording do workflow** — [assistir no Jam](https://jam.dev/c/e1166361-6d96-4d22-b02e-510df2ba12ff)

---

_Submissão enviada em: 2026-06-20_
