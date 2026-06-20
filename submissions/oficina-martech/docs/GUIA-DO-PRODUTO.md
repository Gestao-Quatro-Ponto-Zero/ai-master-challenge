# 🎯 Foco — O que fechar primeiro.

> 📄 **Submissão formal (segue `templates/submission-template.md`):** [`../README.md`](../README.md) — Sobre mim, Executive Summary, Process Log e Evidências.
> Este é o guia do produto (diagnóstico, como rodar, como o score funciona). O código está em [`../solution/`](../solution/).

Lead scorer para o Challenge 003 (Vendas/RevOps). Lê o pipeline do CRM (~8.800 oportunidades, 35 vendedores) e devolve, para cada vendedor, a **lista priorizada dos deals abertos** — com score 0-100, o **porquê** de cada score (fator a fator) e a ação recomendada. O vendedor abre na segunda de manhã e sabe onde focar.

> 🔗 **Demo ao vivo (Streamlit Cloud):** https://ai-master-challenge-whltkcmfjkn7qsrufhr3es.streamlit.app/ — ou rode local em 3 comandos (abaixo), SQLite + Streamlit, sem API key, sem Docker.

## Diagnóstico de negócio

A priorização hoje é "no feeling": cada vendedor decide no instinto onde focar, e ninguém limpa o que já morreu. O pipeline incha — e quanto mais entulho, mais difícil enxergar o que vale, o que empurra o vendedor de volta pro feeling. É um ciclo que se realimenta. Os nossos dados mostram o tamanho do entulho: **61,8% dos deals abertos (1.291 de 2.089) já passaram do ciclo de qualquer venda fechada na história** (>138 dias — nenhum negócio ganho levou mais que isso), e **68% (1.425 de 2.089) estão sem conta atribuída no CRM**.

A raiz é que "priorizar" virou uma nota só, quando na verdade são **duas perguntas separadas**:

| Pergunta | O que responde | Como o Foco trata |
|----------|----------------|-------------------|
| **"Vale a pena?"** | O potencial do deal | **Score 0-100** = win-rate do vendedor + tamanho do deal + urgência |
| **"Dá pra trabalhar?"** | A viabilidade real | Um deal pode ter score alto e ainda ser **inviável**: passou do ponto de fechar (**stale, >138d**) ou não dá nem pra agir porque está **sem conta** atribuída |

O Foco cruza esses dois eixos **de propósito**. É por isso que um deal de score alto mas morto cai para "Baixa Prioridade" (sai da lista de ataque) e um deal sem conta sai do brief do dia (não dá pra cobrar um cliente que o vendedor não consegue identificar). Não é acaso nem efeito colateral das regras de tier — é **decisão de design**: separar o que é *trabalhável* do que é *ruído* é o que quebra o ciclo de inchaço e devolve o foco ao vendedor.

## Rodar (3 comandos)

O código fica em `solution/` — rode de lá:

```bash
cd solution
pip install -r requirements.txt
make setup     # migrations + seed dos dados reais (valida contagens: 7/85/35/8800)
make run       # abre o app em http://localhost:8501
```

> Sem API key, sem Docker, sem credencial — SQLite + Streamlit. `make test` roda os 31 testes.
>
> 🔁 **`make evidence`** regenera num comando só os `.txt` de evidência em `../process-log/execucoes/` (`pytest.txt`, `score-distribuicao.txt`, `install-migrate-seed.txt`) a partir do código atual — assim a evidência nunca fica defasada do scoring. (`app-smoke-test.txt` é narrativa interativa das telas, atualizada à mão quando a UI muda.)

📸 *Screenshots das telas e vídeo de demo: ver `../process-log/` (screenshots + chat-exports).*

## O que tem dentro

| Tela | Para quem | O que entrega |
|------|-----------|---------------|
| **Foco do Dia** | Vendedor | Top deals por tier (🔥 Foco Agora / ⭐ Trabalhar), brief executivo do dia (com download), breakdown do score por deal, seção 🩺 Revisar/Descartar — e **ação por deal**: ✓ Contatado hoje · ✕ Descartar · ↩ Reativar (persistido, auditável) |
| **Time** | Manager | Foco Agora por vendedor, pipeline esperado e **receita em risco em R$**, deals a descartar, **export CSV "CRM-ready"** do Foco Agora |
| **Saúde** | RevOps | 68% dos deals abertos sem conta (R$ quantificado), receita esfriando, ciclo médio, **log de auditoria** das ações dos vendedores |

## Como o score funciona (resumo)

`score = 45% probabilidade + 35% tamanho do deal + 20% urgência` — cada deal carrega o breakdown auditável (a soma das parcelas **é** o score).

- **Probabilidade** = win-rate histórico do vendedor com smoothing bayesiano (k=8, prior=63,2%). Única dimensão com sinal real nos dados (spread 15pp); produto/setor/região foram **medidos e descartados** (<5pp).
- **Urgência** = curva sino ancorada no ciclo real dos Won (sobe até a janela ideal 57→88d, satura e decai após), **não** na distribuição dos abertos — usar o p90 dos abertos (319d) era viés de sobrevivência (marcava tudo como "ainda no prazo").
- **Deals "mortos"** (`days_open > 138d` = o Won mais velho da história; nenhum fechou além disso) saem do foco e vão para "Revisar/Descartar" — **61,8% dos abertos**, reportado como insight de pipeline inflado.
- Prospecting (sem data de engajamento) não é penalizado: os pesos renormalizam sem o fator de urgência.

Lógica completa e justificativas: [`PLANO-DO-PROJETO.md`](PLANO-DO-PROJETO.md) · decisões e verificações: [`decisoes.md`](decisoes.md).

## Estrutura

```
submissions/oficina-martech/
├── README.md              submissão formal (segue o template do challenge)
├── solution/              o produto (roda daqui)
│   ├── scoring/             núcleo do score (puro, testável): config · data · features · model
│   ├── app/                 Streamlit: main.py (orquestração) · views.py (1 função/tela) · theme/ (tokens · styles · components)
│   ├── db/                  migrations versionadas + seed (SQLite) — ver db/README.md
│   ├── data/                4 CSVs do CRM (dataset oficial do challenge)
│   ├── tests/               31 testes (pytest)
│   ├── notebooks/           EDA que fundamentou o modelo
│   ├── Makefile · requirements.txt · pytest.ini
├── process-log/           como foi construído (evidência de uso de IA)
│   ├── process-log.md        narrativa ao vivo
│   ├── execucoes/            saídas reais (pytest, EDA, seed, smoke test, distribuição)
│   ├── screenshots/          telas do produto + screenshots das ferramentas de IA
│   └── chat-exports/         transcrições das sessões (Codex, OpenCode/GLM)
└── docs/                  documentação de apoio
    ├── GUIA-DO-PRODUTO.md    este guia
    ├── decisoes.md           decisões com alternativas descartadas + verificações numéricas
    └── PLANO-DO-PROJETO.md   design completo da solução
```

## Limitações

- Dataset histórico (snapshot ~2017) e possivelmente sintético — sinal preditivo fraco (base 63%) e concentrado no vendedor; não fabricamos precisão que os dados não suportam.
- `engage_date` é proxy fraco de atividade. Em produção, a maior alavanca é registrar **interações reais** (última atividade por deal).
- Sem histórico de transição de estágio — urgência só é confiável para Engaging.
