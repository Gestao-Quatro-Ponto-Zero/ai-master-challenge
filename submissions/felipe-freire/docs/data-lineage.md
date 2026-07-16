# Lineage de dados

```text
data/raw/social_media_dataset.csv
  SHA-256 693A...F18E
        │ src/etl/build_dataset.ps1
        │ valida schema, chaves, ranges, datas e patrocínio
        │ minimiza campos e cria features determinísticas
        ▼
data/processed/posts_analytical.csv
        │ tests/data/test_build_dataset.ps1
        ▼
EDA / dataset inferencial mínimo
```

O ZIP original é preservado como evidência de aquisição, mas não participa da transformação. Raw não é sobrescrito. Toda mudança de regra exige nova versão do contrato e invalida gates dependentes.
