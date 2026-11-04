# F4 — Política e fluxo (spec para o Claude Code)

- **Teto:** 25 min. Ao chegar a 30 min (120%), pare e proponha o corte no report.
- **Leia antes:** `CLAUDE.md`; `planning/F0-escopo.md`; `planning/F3-report.md`; a seção "Portão F3" de `process-log/process-log.md`.
- **Decisões já tomadas (portão F3):** clássico com 3 faixas; LLM fora do caminho de decisão; *e*_Q2 = 3,82% (quase-duplicados).
- **Objetivo:** a política "IA decide / IA sugere / humano decide" **por tipo de ticket**, apoiada em números e em exemplos reais sorteados (não escolhidos a dedo), e o fluxo da entrada à resolução, incluindo o que acontece quando algo falha.

## Premissa de transferência (escrever no topo de `docs/politica.md`)

A política tem duas camadas, porque os datasets não se encaixam (F0-escopo, seção 2):
1. **Roteamento** (para qual fila vai): medido no DS2, com as 8 categorias e as faixas da F3.
2. **Ação** (o que pode ser feito sem humano): definida pelos 5 tipos do DS1. É **regra de negócio declarada**, não resultado de modelo, porque o texto do DS1 é inutilizável (T2).

## Passo 1 — `solution/f4_politica.py` (≤ 10 min)

Entradas: `f3_probs_holdout_grupo.csv`, `f3_faixas.json` (limiares e metas), `f3_classico.json` (F1 por classe e confusões).

Para cada uma das 8 categorias do DS2, calcule no holdout por grupo:
- n; % em cada faixa; precisão na faixa "IA decide", com IC de Wilson 95%; F1; as 2 confusões mais frequentes.

Grave em `solution/outputs/f4_politica_por_categoria.csv`.

**Regra por categoria** (fixada antes de ver o resultado):
- se o limite inferior da precisão da categoria na faixa "IA decide" for ≥ 1 − *e*_inferior, a categoria fica em **IA decide**;
- se só for ≥ 1 − *e*_superior, ela é **rebaixada para IA sugere**, mesmo com `p_max` ≥ 0,74;
- abaixo disso, **humano decide**.

Grave a coluna `politica` e o motivo numérico. **Não ajuste os limiares.**

## Passo 2 — Exemplos reais (≤ 5 min)

- Para cada categoria × política resultante: 1 ticket sorteado (seed 42) do holdout por grupo, dentro da faixa correspondente.
- Para "humano decide": 3 tickets sorteados (seed 42) da faixa humana; mais 3 tickets marcados `ambíguo` na `revisao_rotulos_adjudicada.csv`, também sorteados.
- Em `docs/politica.md`, cada exemplo aparece como `id` + trecho de **no máximo 120 caracteres** do texto + rótulo + `p_max`. (Exceção aprovada à regra de texto no repositório: o brief exige exemplos dos dados, e o DS2 é CC0. Nada além disso.)
- DS1: para cada um dos 5 tipos, 1 ticket sorteado (seed 42) mostrando só `Ticket Type`, `Ticket Subject`, `Ticket Channel` e `Ticket Priority`. **Nunca** nome, e-mail nem descrição.

## Passo 3 — `docs/politica.md` (≤ 5 min)

Tabela única: tipo | camada (roteamento / ação) | IA decide / IA sugere / humano decide | motivo (com número e arquivo de origem, ou "regra de negócio") | exemplo real.

- **Roteamento:** as 8 categorias, conforme o passo 1.
- **Ação:**
  - `Refund request` e `Cancellation request`: **humano decide**, sempre. Motivo: regra de negócio (movimenta dinheiro e é difícil de reverter). Escreva que **não** é resultado medido.
  - `Billing inquiry`, `Technical issue` e `Product inquiry`: a IA roteia conforme a camada 1 e o humano responde. Não existe resposta automática ao cliente nesta proposta.
- Uma linha com a cobertura total esperada: % IA decide / % IA sugere / % humano, com origem.
- Uma linha: "o que IA sugere significa na tela do atendente": a categoria mais provável e a segunda, com as probabilidades, e um botão para confirmar ou corrigir. A correção é registrada.

## Passo 4 — `docs/fluxo.md` (≤ 5 min)

Diagrama em Mermaid (`flowchart TD`) mais uma tabela de falhas, da entrada à resolução:

1. **Entrada:** chave de idempotência = `event_id`; sem ele, hash do texto normalizado + canal + janela de tempo. Evento duplicado é descartado e registrado.
2. **Validação:** texto vazio ou com menos de 3 palavras vai direto para humano decide (o DS2 tem 14 tickets assim; cite `f1_ds2_auditoria.json`).
3. **Mascaramento** de dado pessoal antes de gravar o log.
4. **Classificação:** categoria + `p_max` + motivo (os termos de maior peso do TF-IDF para a classe prevista).
5. **Faixa:** a política do passo 1, por categoria.
6. **Regra de ação** do DS1 (reembolso e cancelamento sempre com humano), aplicada **depois** do roteamento.
7. **Resolução** pelo atendente; correção da sugestão → log → conjunto de avaliação.

Tabela de falhas: falha | como detecta | o que o sistema faz | quem é avisado. Cubra pelo menos: evento duplicado, texto vazio ou curto, erro do classificador ou modelo não carregado (→ fila humana), injeção no texto (o clássico não executa instruções; a taxa de troca de rótulo é medida na F5), categoria nova ou drift (→ queda da cobertura na faixa IA decide como alerta), dado pessoal no texto.

## Passo 5 — Report

`planning/F4-report.md` (formato da seção 8 do `CLAUDE.md`). Linha da F4 no process log, com "Decisão minha" vazia.

## Critérios de aceite

- `python solution/f4_politica.py` e `pytest solution/tests -q` passam. Acrescente um teste da regra por categoria com valores sintéticos (um caso para cada uma das 3 políticas).
- Todo número de `docs/politica.md` e `docs/fluxo.md` tem um arquivo de origem.
- Exemplos só sorteados com seed; nenhum escolhido a mão.
- Nenhum nome, e-mail ou descrição do DS1 no repositório; trechos do DS2 com no máximo 120 caracteres.
- `f1_splits.csv` com o mesmo hash. Nenhum commit.

## Não faça

- Mudar limiares, faixas ou modelo.
- Usar LLM.
- Construir o protótipo (é F5).
- Escrever sobre a experiência do Gustavo.
