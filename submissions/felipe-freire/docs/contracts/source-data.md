# Contrato do dado fonte

## Identificação

- Arquivo: `data/raw/social_media_dataset.csv`
- Fonte declarada: Kaggle, `omenkj/social-media-sponsorship-and-engagement-dataset`
- Licença declarada no desafio: MIT
- SHA-256: `693A2DF6E609D1C099F3430D9A5B894B224FE12B2420C0D93E6DEFE90D15F18E`
- Linhas: 52.214
- Colunas: 27
- Grão pretendido: um post por linha
- Chaves observadas únicas: `id`, `content_id`
- Período observado: 2023-05-29 00:15 a 2025-05-28 11:08

## Schema

| Grupo | Colunas | Tipo esperado/regra |
|---|---|---|
| Identidade | `id`, `content_id`, `creator_id` | não vazias; `id` e `content_id` únicos |
| Identificadores descritivos | `creator_name`, `content_url` | não usar como chave; `creator_name` é inconsistente |
| Conteúdo | `content_type`, `content_category`, `language`, `content_length`, textos/hashtags | categorias controladas; length positivo |
| Tempo | `post_date` | data parseável; timezone não fornecido |
| Performance | `views`, `likes`, `shares`, `comments_count` | inteiros não negativos; views positivo; interação ≤ views |
| Creator | `follower_count` | inteiro positivo |
| Patrocínio | `is_sponsored`, disclosure e sponsor | flag coerente com metadados |
| Audiência | idade, gênero, localização | categorias agregadas; não representam indivíduos |

## Missingness permitido

Somente `hashtags` e `comments_text` apresentaram vazios, respectivamente 8.743 e 8.688 linhas. Ausência é preservada; não há imputação semântica.

## Limitações da fonte

- A origem/geração precisa ser confirmada no material do Kaggle; os padrões são compatíveis com dataset sintético.
- `creator_name` não é estável: todas as 5.000 IDs aparecem com múltiplos nomes.
- `follower_count` também não é estável por creator: a média de valores distintos por `creator_id` é aproximadamente igual à média de posts por creator, e a dispersão intra-creator é próxima à dispersão populacional. Trate-o como atributo observado do post, não cadastro fixo do creator.
- Métricas de performance são excessivamente concentradas e não contêm zeros, limitando validade externa e análise de sobrevivência.
- Não há custo, receita, timezone, frequência planejada ou exposição de mídia; ROI e causalidade não são identificáveis.
