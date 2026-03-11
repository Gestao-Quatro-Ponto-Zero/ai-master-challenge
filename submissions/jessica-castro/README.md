# DealSignal — Jessica Castro
## Challenge: build-003-lead-scorer

---

## Solução

**DealSignal** é um AI-powered deal rating engine que prioriza oportunidades de vendas por probabilidade de fechamento e impacto financeiro esperado.

**Stack**: Python · Logistic Regression · WoE/IV · Streamlit · APIs externas com fallback mock

### Como rodar

```bash
cd solution/dealsignal
pip install -r requirements.txt

# Treinar modelo e gerar scores
python run_pipeline.py

# Abrir interface
streamlit run app/streamlit_app.py
```

### Arquitetura

```
CSVs → Enrichment (BrasilAPI/BuiltWith/Similarweb) → Feature Engineering
     → WoE Transform → IV Selection → Logistic Regression → Rating Engine → Streamlit
```

- **Modelo**: Regressão Logística com WoE (inspirado em scoring de crédito bancário)
- **Rating**: AAA → CCC baseado em win probability
- **Expected Revenue**: win_probability × deal_value
- **Explainability**: top fatores positivos/negativos por deal (WoE × coeficiente)

---

## Process Log

Ver pasta `process-log/` com:

- `racional.md` — ideia inicial e abordagem
- `prompt - gerado ChatGTP.md` — prompt técnico gerado com ajuda de ChatGPT
- `plan - claudecode.md` — plano de implementação gerado pelo Claude Code

**Ferramentas usadas**: ChatGPT (design da metodologia + geração do prompt técnico) → Claude Code (planejamento + implementação completa)
