# Process Log — Narrativa: como usei IA no Challenge 002

> Formato: narrativa escrita (aceito pelo guia de submissão), com slots de screenshots/exports nos pontos marcados. Ferramenta principal: **Claude Code** (opencode, modelo GLM), sessões de trabalho em 10–11/11/2026.

---

## 1. Antes de promptar: decompus o problema

Li o README do challenge e transformei as 3 perguntas do Diretor em um plano com entregáveis verificáveis:

1. **Diagnóstico** (Dataset 1): onde trava, o que impacta CSAT, quanto se desperdiça — com números, não narrativa.
2. **Proposta de automação** (Datasets 1+2): o que automatizar, o que NUNCA, e o fluxo ticket-entra-acontece-o-quê.
3. **Protótipo**: algo que rode de verdade sobre dados reais, não 3 exemplos cherry-picked.
4. **Reproduzibilidade**: protocolo de avaliação único (holdout 80/20 estratificado, seed 7) para que qualquer número fosse comparável.

---

## 2. Etapa 1 — Diagnóstico (EDA)

Pedi à IA para carregar o Dataset 1 e validar o grão (1 linha = 1 ticket, `Ticket ID` único). As perguntas que **eu** formulei — não "explore os dados":

- Qual a fração de tickets sem primeira resposta, estratificada por canal, prioridade e tipo (com teste de significância)?
- Os campos `First Response Time` / `Time to Resolution` são internamente consistentes? (contas: resolvido-antes-de-respondido?)
- O CSAT se separa por algum atributo? (testes + modelo com R²)

**A IA respondeu os cálculos; o julgamento foi meu** — por exemplo, interpretar "49,3% dos tickets resolvidos antes de respondidos" como *relógios quebrados do sistema*, e a consequência: nenhum ranking de "combinação mais lenta" seria honesto sobre aqueles timestamps.

Resultado: 33,3% sem primeira resposta, ~33% em todos os estratos (travamento sistêmico), CSAT como sorteio. Relatório narrado em `docs/relatorio_fluxo_atendimento.md`.

📸 *Slot: screenshots da sessão de EDA — `process-log/screenshots/`*

---

## 3. Etapa 2 — Classificador (Dataset 2, 8 tópicos)

Plano de comparação fixo: baseline majoritária → zero-shot (LLM) → TF-IDF (word 1-2g) + LogReg/SVM → fine-tune DistilBERT. Mesmos dados, mesmo split, seed 7.

**Erros da IA que eu percebi e corrigi:**

- **Zero-shot LLM ficou ~32% — praticamente igual ao baseline (28,5%).** A primeira resposta da IA sugeriu incluir o zero-shot na comparação final como opção viável; os números disprovam — descartei e registrei o porquê.
- **DeBERTa: loss NaN no MPS.** A IA tentou treinar a arquitetura maior; o loss explodiu. Correção: voltar ao DistilBERT e registrar a tentativa como limitação honesta (e deixar "DeBERTa em GPU" como próximo passo), em vez de reportar um número falso.
- Hiperparâmetros do DistilBERT (3 epochs, max_length 192, batch 32, lr 2e-5) vieram da IA; o **critério de aceite** (macro-F1 por classe, não só acurácia) foi meu — a classe pior classificada (Administrative rights, F1 0,782) depois virou uma regra de negócio.

Resultado: DistilBERT 87,80% / macro-F1 0,8747 (`solution/artifacts/transformer/`).

📸 *Slot: screenshots do treino/avaliação — `process-log/screenshots/`*

---

## 4. Etapa 3 — Roteador por confiança (a decisão que a IA não teria)

A IA, por padrão, otimiza acurácia. Eu mudei o objetivo: **o que importa é a precisão da fila automática** (cada erro do AUTO custa um ticket na equipe errada — o problema original). Escolha do limiar: o menor com precisão ≥ 0,95 → **0,86** (95,05% precisão, 80,7% cobertura no holdout).

**O erro mais importante da IA — e a minha correção:** a primeira versão do relatório apresentava os 80,7% de cobertura como o resultado. Eu pedi para rodar o roteador sobre o lote de produção cru (`customer_support_tickets.csv`) — e a cobertura desabou para **21,5%** (confiança mediana 0,63 vs 0,95). Causa: treino em corpus pré-processado/balanceado vs texto cru com templates. **Correção:** reescrever a seção para reportar o número real com a explicação, e tornar "recalibrar o limiar com produção" a recomendação nº 2. Esse tipo de leitura honesta não sai de um prompt único.

📸 *Slot: screenshots da escolha do limiar e do lote de produção — `process-log/screenshots/`*

---

## 5. Etapa 4 — Protótipo (dashboard + CLI + Streamlit)

- **Regras de "o que nunca automatizar":** minhas, baseadas nos achados (Administrative rights pelo custo de erro; resposta final ao cliente — a IA só roteia, não escreve; nada guiado por CSAT).
- Dashboard self-contained (`dashboard_g4.html`): fontes/figuras em base64, abrir direto no navegador.
- **Duplicação gerada pela IA:** em iterações de design a IA criou duas templates de dashboard (`dashboard_template.html` e `dashboard_final_template.html`) — o fluxo antigo ficou órfão e confundiria o avaliador. Correção: apontei, mantive só a cadeia viva (`dashboard_final_template.html → dashboard_g4.html → streamlit_template.html`) e removi o script antigo (`build_dashboard.py`).
- App Streamlit 1:1 com o dashboard, com classificador em tempo real (mesmo modelo, mesmo limiar, mesmas regras — paridade validada contra o CLI).

📸 *Slot: screenshots do dashboard/app e da iteração de design — `process-log/screenshots/`*

---

## 6. Etapa 5 — Submissão

Usei IA para mapear os guias (`submission-guide.md`, `CONTRIBUTING.md`, template) contra a pasta: identifiquei `submissions/` ignorado pelo `.gitignore` (exigindo `git add -f`), o `.safetensors` de 267 MB que quebraria o push, e o process-log vazio. Commits incrementais por etapa para que o git history sirva como evidência.

---

## 7. Resumo honesto

- **Ferramentas:** Claude Code (opencode + GLM) para tudo; julgamento, critérios de aceite e as correções de rota acima foram meus.
- **Iterações:** dezenas — em particular o ciclo dashboard (3 gerações de template até a final) e a recalibragem narrativa do distribution shift.
- **Se a IA tivesse trabalhado sozinha:** teria entregado um relatório vendendo 80,7% de cobertura, com um zero-shot que quase empatou com o baseline no meio da tabela, e um template de dashboard duplicado no repo.

📂 Evidências complementares em `screenshots/` e `chat-exports/` (inseridas pelo autor).
