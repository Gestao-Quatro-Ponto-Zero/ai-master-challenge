# Submissão — Diego Rodrigues — Challenge 003

## Sobre mim

- **Nome:** Diego Rodrigues
- **LinkedIn:** https://www.linkedin.com/in/diegoaorodrigues/
- **Challenge escolhido:** 003 · Lead Scorer

---

## Executive Summary

Três quartos do pipeline aberto (US$ 3,66 mi dos US$ 4,97 mi, 73,6%) não tem nenhuma chance histórica de fechar: dos 734 negócios distintos classificados como vencidos nos seis cortes do backtest, nenhum foi ganho em momento algum do export. O que sobra vivo são 115 negócios, em 17 dos 35 vendedores. Priorizar esses negócios pela janela de decisão do trimestre — aprendida do histórico, não escrita à mão — rende 1,30 vez o valor da melhor alternativa honesta (ordenar por preço e prazo), com intervalo de confiança de 95% que não cruza 1 (1,13 a 1,52). Nenhum atributo do negócio prevê quem ganha; a recomendação não é "quem vai fechar", é "quando este negócio costuma decidir". Resumo completo, com a conta de horas como premissa declarada: [`docs/resumo-executivo.md`](docs/resumo-executivo.md).

---

## Solução

**Demo pública:** https://lead-scorer-diego.vercel.app (dados fictícios, CC0; ações não são gravadas na demo)

### Abordagem

O motor é um pipeline determinístico em três fronteiras: `recortar` (única porta de entrada — apaga o futuro, usada igual em produção e no backtest), `aprender` (histórico conhecido → janela de validade + tabela de destino por faixa de idade) e `pontuar` (tabela + deals abertos → fila, ordem, índice). Comecei pela procedência do dado (Tarefa 1) porque um merge ingênuo de produto já derrubaria 1.480 linhas de pipeline; segui tarefa por tarefa do plano em `projects/pessoal/transicao-carreira-ia/g4-challenge-003/02-plano-implementacao.md`, com TDD em cada módulo do motor e verificação contra os dados reais antes de cada commit — não só contra os testes escritos.

O discovery (`docs/discovery.md`) foi ensaiado com quatro personas sintéticas e um líder, não entrevistas reais: protocolo, pré-registro e calibração contra números já medidos, para separar o que a persona podia me dizer do que não podia.

### Resultados / Findings

- **Motor:** `solution/motor/` (carregar, janela, aprender, pontuar, explicar), 59 testes, TDD tarefa a tarefa.
- **Avaliação:** `solution/avaliacao/` — backtest as-of com 3 métricas e IC por bootstrap de vendedor, permutação para descartar atributos como sinal. Único erro de método que encontrei sozinho: o campo de conta só é preenchido após o desfecho (0 de 6.711 fechados sem conta, 1.425 de 2.089 abertos sem conta), e isso vazava sinal falso para "vendedor" no primeiro teste — corrigido em `docs/logica.md`.
- **Produto:** `solution/app/` (3 telas, mobile-first, estado vazio como primeira classe), `solution/run.py` (um comando, servidor local, ações gravadas), `solution/ia/` (briefing com validador determinístico; nesta versão, só por template — a chamada à API da Anthropic não foi implementada, por decisão do Diego).
- **Prints:** `process-log/screenshots/` (desktop 1366px e mobile 390px).

### Recomendações

A frase de negócio, com a conta por trás em [`docs/resumo-executivo.md`](docs/resumo-executivo.md): priorizar pelo relógio do trimestre em vez de por valor, medir o ganho num piloto com grupo de controle antes de expandir (`docs/experimento.md`), e tratar os 500 deals em Prospecting sem data (US$ 1,07 mi) como a maior lacuna sobre a qual a ferramenta não opina.

### Limitações

Lista completa e honesta em [`docs/limitacoes.md`](docs/limitacoes.md).

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| Claude Code — `claude-sonnet-5-5`, `claude-sonnet-5`, `claude-sonnet-4-6`, `claude-opus-5`, `claude-haiku-5-5`, `claude-haiku-4-5-20251001` | Implementação do motor (TDD), backtest, avaliação, as três telas, o deploy, os cinco documentos da Tarefa 12 e este README. Modelo trocado por tipo de trabalho: Opus para documentos lidos primeiro pelo avaliador, Haiku para deploy e comandos mecânicos, Sonnet para implementação. |
| Microsoft 365 Copilot (Premium), GPT Sol 6.1 | Agente de persona do discovery (Tarefa 0B) — informante sintético, nunca fonte de fato. |
| Nemotron-3.5-lightning (via OpenRouter), Gemini 3.1, ChatGPT 6.1 Sol | Baseline sem ferramentas (Tarefa 0), para medir o que um modelo propõe sem o dado na mão. |

Inventário completo, com versão exata e papel: [`process-log/MODELOS.md`](process-log/MODELOS.md).

### Workflow

1. Procedência do dado e recorte temporal sem vazamento (Tarefa 1), com TDD: testes escritos e vistos falhar antes do código.
2. Janela de validade e tabela de destino aprendidas do histórico, nunca com limiar escrito à mão (Tarefas 2–3).
3. Fila, ordem e explicação por deal (Tarefas 4–5), cada uma verificada contra os valores de ouro do protótipo (`analise/eda-06-prototipo-motor-v2.saida.txt`) antes do commit.
4. Build do contrato JSON e relatório de desvio (Tarefas 6 e 8).
5. Backtest com três políticas e IC, permutação de atributos (Tarefa 7) — onde encontrei e corrigi o vazamento do campo de conta.
6. Briefing por template com validador determinístico (Tarefa 9, sem chamada de API nesta versão), servidor local (Tarefa 10), três telas (Tarefa 11) — corrigidas depois de olhar os próprios prints, não só os testes.
7. Operating map, sponsor map, design, deploy e experimento citando as transcrições do discovery (Tarefa 12).
8. Deploy, resumo executivo, limitações e este README (Tarefa 13).

### Onde a IA errou e como corrigi

Lista completa, com o teste ou a verificação que pegou cada erro: [`process-log/onde-a-ia-errou.md`](process-log/onde-a-ia-errou.md). Destaques:

- A fórmula ingênua de chance de decidir dava 100% aos 120 dias por contar só fechados; corrigida com a tabela censurada (`test_nao_ha_vies_de_sobrevivencia`).
- O campo de conta vazava sinal falso para "vendedor" no teste de permutação (0,012 virou 0,141 ao filtrar deals sem conta).
- Uma frase do plano ("o que sobra vivo cabe numa lista de cinco por vendedor") não se sustentava: 11 dos 17 vendedores com deal vivo têm mais de cinco; corrigida no resumo executivo com o número medido.
- "Intervalo de confiança que não cruza zero", também do plano, estava errado para uma razão: o intervalo não cruza **um**.

### O que eu adicionei que a IA sozinha não faria

Lista completa: [`process-log/o-que-eu-acrescentei.md`](process-log/o-que-eu-acrescentei.md).

---

## Evidências

- [x] Prints das três telas, desktop e mobile: `process-log/screenshots/`
- [x] Diário de sessões, na hora: `process-log/diario.md`
- [x] Git history: este repositório, branch `submission/diego-rodrigues`
- [ ] Relatório de verificação independente: `process-log/verificacao/` (etapa seguinte desta tarefa)
- [ ] Screen recording do workflow

---

_Submissão enviada em: 11/11/2026_
