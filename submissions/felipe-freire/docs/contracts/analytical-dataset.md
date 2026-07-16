# Contrato do dataset analítico

## Artefato

`data/processed/posts_analytical.csv`, produzido por `src/etl/build_dataset.ps1` a partir do arquivo fonte imutável.

- Linhas: 52.214
- Colunas: 34
- SHA-256: `410E2D8101CA5206BAFB2825DE4417F33AB5922EA85B2DE2ACB0C5FC0EE649F0`
- Decimais: representação invariável com ponto

## Grão e população

Uma linha por post. Nenhuma linha fonte é excluída no DQ. O dataset deve conter exatamente 52.214 linhas e chaves `id`/`content_id` únicas.

## Transformações

- `post_date` → ISO sem timezone, componentes de ano/mês/dia da semana/hora;
- `is_sponsored` → 0/1;
- faixas de seguidores: `<10k`, `10k–50k`, `50k–100k`, `100k–500k`, `500k+`;
- contagem de hashtags por separação em vírgula;
- `engagement_total = likes + shares + comments_count`;
- taxas por view e `views_per_follower`, sem divisão por zero;
- remoção do dataset analítico de nome/URL/descrições/comentários e sponsor name, por minimização e falta de necessidade analítica.

`follower_count` e `creator_size` são atributos do registro/post. Eles não devem ser interpretados como características estáveis de `creator_id`, pois variam quase linha a linha dentro do mesmo creator.

## Invariantes

- métricas e seguidores nos ranges do contrato fonte;
- `0 < engagement_rate_views ≤ 1`;
- flag patrocinado em `{0,1}` e coerente com disclosure/categoria;
- nenhuma alteração dos valores-base de performance;
- contagem de linhas reconciliada à fonte.

## Uso permitido

EDA e preparação de dataset mínimo para inferência. Não autoriza alegação causal, ROI, identificação individual ou uso de `creator_name`.

## Validação executada

`tests/data/test_build_dataset.ps1` passou com 52.214 linhas e 34 colunas, validando chaves, campos derivados, flag de patrocínio, datas e reconciliação de engagement.
