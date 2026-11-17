# Como rodar

Pré-requisito: os dois CSVs do Kaggle na pasta `datasets/` da raiz do repositório:
- `datasets/customer_support_tickets.csv`
- `datasets/all_tickets_processed_improved_v3.csv`

Na raiz do repositório:

```
python -m pip install -r submissions/adson-valeriano/solution/requirements.txt
cd submissions/adson-valeriano/solution
python diagnostico.py      # diagnóstico do dataset de suporte -> resultados_diagnostico.md
python avaliar.py          # treina e avalia o classificador   -> resultados_avaliacao.md
streamlit run app.py       # abre o protótipo no navegador
```

Na primeira execução o modelo é treinado (~30 s a 1 min) e salvo em `modelo_triagem.joblib`.
