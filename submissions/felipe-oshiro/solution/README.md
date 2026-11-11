# Solução — Triagem inteligente de tickets (G4 Educação)

**O problema:** 67% do fluxo de atendimento está parado e 33,3% dos tickets (2.819 de 8.469) nunca recebem uma primeira resposta — o gargalo é o começo do processo, não a execução.
**A solução:** um classificador DistilBERT fine-tuned (87,8% de acurácia, macro-F1 0,875 em 8 tópicos) alimenta um roteador por confiança que atinge **95,05% de precisão na fila automática** com 80,7% de cobertura no holdout, empacotado num dashboard executivo.
**Navegação:** diagnóstico em `docs/relatorio_fluxo_atendimento.md` · protótipo em `solution/scripts/` · números em `solution/artifacts/` · produto final em `solution/dashboard/dashboard_g4.html`.

---

## 1. O que automatizar (e por quê, com base nos dados)

### 1.1 Classificação automática de tópico

O classificador atribui automaticamente 1 de 8 tópicos a cada ticket (Access, Administrative rights, HR Support, Hardware, Internal Project, Miscellaneous, Purchase, Storage), eliminando a triagem manual — origem nº 4 do desperdício do relatório ("tickets encaminhados à equipe errada morrem sem resposta").

| Modelo | Acurácia (holdout) | Observação |
| --- | --- | --- |
| Baseline majoritária | 28,5% | classe mais frequente do holdout |
| Zero-shot (LLM) | ~32% | descartado: próximo do baseline |
| TF-IDF (word 1-2g) + LogReg | 86,78% | `solution/artifacts/step1_results.json` |
| **DistilBERT fine-tuned** | **87,80% / macro-F1 0,8747** | `solution/artifacts/transformer/step2_results.json` |

Protocolo único: holdout estratificado 80/20, seed 7, mesmos dados e split para todos os modelos. Por classe, o transformer destaca-se em Purchase (F1 0,938) e Access (F1 0,909); o pior é Administrative rights (F1 0,782) — ver `solution/artifacts/transformer/classification_report.txt`.

### 1.2 Roteamento por confiança (AUTO vs HUMANO)

A automação não é binária por tópico: ela roteia **só quando o modelo tem certeza**. Varrendo o limiar na curva precisão × cobertura (`solution/scripts/pick_threshold.py`), escolhemos o **menor limiar com precisão ≥ 0,95**:

- **Limiar 0,86** → precisão na fila automática **95,05%**, cobertura **80,7%** no holdout (`solution/artifacts/router_threshold.json`).

Em outras palavras: a cada 20 tickets despachados sem humano, no máximo 1 vai para a equipe errada — dentro da fila automática, não no fluxo todo.

### 1.3 Impacto real medido no lote de produção (8.469 tickets)

Rodando o roteador sobre o CSV de produção (`solution/artifacts/routed_tickets.csv`, derivado de `solution/datasources/customer_support_tickets.csv` — [Dataset 1 do Kaggle](https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset)):

| Métrica | Valor |
| --- | --- |
| AUTO (despachado direto) | **1.821 (21,5%)** |
| HUMANO (triagem com motivo) | **6.648 (78,5%)** |
| — motivo `low_confidence` | 5.703 (67,3%) |
| — motivo `sensitive_class` | 945 (11,2%) |
| Confiança mediana do lote | **0,63** |

**Leitura honesta (distribution shift):** o corpus de treino é pré-processado e balanceado por tópico; o texto de produção é cru, com templates e ruído. Resultado: a confiança despenca (mediana 0,63 vs 0,95 nos AUTO do holdout) e a cobertura AUTO cai de 80,7% para 21,5%. No lote de produção os tópicos previstos concentram-se em Purchase (48%) e Access (21%) — outro sinal do descolamento. **O modelo não está pronto para 80% de cobertura em produção: recomenda-se recalibrar o limiar com dados de produção reais antes de ligar o AUTO em escala.** O pipeline já é defensável ao contrário: errar para o lado humano não bloqueia nada.

---

## 2. O que NÃO automatizar (com justificativa dos dados)

Os 4 cards da seção "Quatro portas que ficam sempre com uma pessoa" do dashboard:

1. **Administrative rights → sempre humano.** Classe com pior F1 (0,782) e trata permissões/acessos de conta: erro caro, recall baixo (0,756) e a regra dispara no lote real — 945 tickets (11,2%) foram para triagem humana exatamente por isso.
2. **Confiança < limiar (0,86) → triagem humana.** Quando o modelo não tem certeza, alguém decide: no lote de produção, 67,3% dos encaminhamentos vieram da baixa confiança — a regra fez o trabalho dela.
3. **Resposta final ao cliente → sempre revisão humana.** A automação só roteia e prioriza: o roteador decide o **destino** do ticket, nunca a **mensagem**. Nenhuma resposta sai sem revisão de uma pessoa.
4. **Nenhuma decisão guiada pelo CSAT atual.** A nota se comporta como sorteio (~20% em cada nota, p>0,25 para tempo/canal/tipo, R²=2% com todos os atributos) — evidência completa em `docs/relatorio_fluxo_atendimento.md` (Pergunta 2). Nenhum investimento, fila ou prioridade é definido por ela até a medição ser reconstruída.

---

## 3. Como funciona na prática (fluxo)

1. **Ticket entra** (e-mail, chat, telefone, redes sociais) — coluna `Ticket Description`.
2. **Padronização de texto** — mesmo pré-processamento do treino; em produção recomenda-se ingestão do texto cru com dicionário de templates.
3. **Classificador (IA)** — DistilBERT retorna tópico previsto + confiança (max softmax). *É o único ponto onde a IA decide.*
4. **Regras de roteamento (determinísticas)**, nesta ordem:
   - tópico == "Administrative rights" → **HUMANO**, motivo `sensitive_class`;
   - confiança < 0,86 → **HUMANO**, motivo `low_confidence`;
   - caso contrário → **AUTO**, motivo `ok`.
5. **Destino:** AUTO vai direto para a fila da equipe do tópico; HUMANO entra na triagem com o motivo visível.
6. **Métricas diárias (humano no controle):** precisão da fila automática (amostragem de auditoria), cobertura AUTO, volume e motivos da fila humana, % de tickets sem primeira resposta. O humano audita o AUTO; nunca o contrário.

---

## 4. Protótipo funcional

### 4.1 CLI de roteamento — `solution/scripts/route_tickets.py`

```bash
solution/.venv/bin/python solution/scripts/route_tickets.py --text "my laptop will not turn on"
# → Access | 0.9701 | AUTO→equipe(Access)

solution/.venv/bin/python solution/scripts/route_tickets.py --text "request admin permissions for my account"
# → Administrative rights | 0.8812 | HUMANO→triagem(sensitive_class)

# Lote completo (modo --batch; lê a coluna 'Ticket Description' e salva
# solution/artifacts/routed_tickets.csv com predicted_topic/confidence/decision/reason):
solution/.venv/bin/python solution/scripts/route_tickets.py --batch solution/datasources/customer_support_tickets.csv
```

> O resultado do lote de produção já está pré-computado em `solution/artifacts/routed_tickets.csv` — o `--batch` só é necessário para reproduzir.

### 4.2 Dashboard executivo

**`solution/dashboard/dashboard_g4.html`** — abrir direto no navegador (arquivo único, sem dependências externas: fontes e imagens em base64). 6 seções: diagnóstico do fluxo, classificador, roteamento, o que não automatizamos e decisões.

### 4.3 Demo web interativa — Streamlit

O mesmo dashboard, replicado 1:1 num app Streamlit (`solution/dashboard/streamlit_app.py`), com o classificador **em tempo real** no fim da seção 2 ("A solução — classificador"): cole o texto do ticket, clique em "Classificar ticket" e receba tópico, confiança, decisão AUTO/HUMANO e top-3 probabilidades — mesma lógica do CLI (mesmo modelo, mesmo limiar 0,86, mesmas regras; paridade validada).

```bash
python3.12 -m venv solution/.venv                     # Python ≥ 3.10
solution/.venv/bin/pip install -r solution/requirements.txt
solution/.venv/bin/streamlit run solution/dashboard/streamlit_app.py
# → abre em http://localhost:8501
```

Detalhes: o modelo carrega uma única vez por sessão (`@st.cache_resource`, ~15 s na abertura; cada classificação é instantânea); a página é gerada de `solution/dashboard/streamlit_template.html`, que por sua vez é regenerado a partir do `dashboard_g4.html` com `solution/.venv/bin/python solution/scripts/build_streamlit_template.py` — edite sempre o dashboard original, nunca o template.

### 4.4 Reprodutibilidade

Split fixo: holdout estratificado 80/20, `random_state=7`, seed 7 em tudo que é estocástico. Comandos na ordem:

```bash
# passo 0: baixar os datasets do Kaggle para solution/datasources/
# Dataset 1 (métricas): https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset → customer_support_tickets.csv
# Dataset 2 (texto):    https://www.kaggle.com/datasets/adisongoh/it-service-ticket-classification-dataset → all_tickets_processed_improved_v3.csv

solution/.venv/bin/python solution/scripts/train_classic.py        # passo 1: baselines TF-IDF → artifacts/step1_results.json + model_best.joblib
solution/.venv/bin/python solution/scripts/train_transformer.py    # passo 2: fine-tune DistilBERT → artifacts/transformer/ (modelo + test_predictions.npy)
solution/.venv/bin/python solution/scripts/evaluate.py             # passo 3: relatório por classe + curva precisão × cobertura
solution/.venv/bin/python solution/scripts/pick_threshold.py       # passo 4: limiar com precisão ≥ 0,95 → artifacts/router_threshold.json
solution/.venv/bin/python solution/scripts/route_tickets.py --batch solution/datasources/customer_support_tickets.csv  # passo 5: impacto no lote → routed_tickets.csv
solution/.venv/bin/python solution/scripts/build_dashboard_final.py # passo 6: dashboard → solution/dashboard/dashboard_g4.html
solution/.venv/bin/python solution/scripts/build_streamlit_template.py # passo 7 (opcional): template do app Streamlit → solution/dashboard/streamlit_template.html
```

**Nota sobre os binários de modelo:** os pesos (`artifacts/transformer/model.safetensors`, 267 MB) e o `model_best.joblib` não são versionados (limite de tamanho do GitHub). Todos são regenerados pelos passos 1–2 — **rode o passo 2 antes do CLI (`route_tickets.py`) e do app Streamlit**, que carregam o modelo treinado. Os resultados das métricas (`artifacts/*.json`, CSVs, PNGs) estão commitados e não dependem de reexecução.

---

## 5. Limitações e próximos passos

**Sendo honestos:**

- **Alvo de 90% de acurácia não foi atingido** — o transformer saturou (87,8%; TF-IDF+LogReg fica a 1 pp). DeBERTa foi tentada e descartada: loss NaN no MPS.
- **Cobertura AUTO baixa em texto cru** — 21,5% no lote de produção vs 80,7% no holdout (distribution shift documentado na seção 1.3).
- **Sem prioridade automática** — o dataset não tem sinal de prioridade real que o modelo possa aprender (segmentos uniformes, relógios quebrados).
- **CSAT inutilizável** — nota com comportamento de sorteio; nada pode ser guiado por ela.

**Próximos passos:**

1. **DeBERTa em GPU** — testar arquitetura maior fora do MPS para tentar superar os 90%.
2. **Recalibração com produção** — reescolher o limiar com confianças medidas sobre texto cru (o caminho para elevar os 21,5% de AUTO com segurança).
3. **Coleta dos 3 timestamps** (`created_at`, `first_response_at`, `resolved_at`) — destrava SLA, priorização e medição real de satisfação, pré-condição para automatizar qualquer coisa além da triagem.
