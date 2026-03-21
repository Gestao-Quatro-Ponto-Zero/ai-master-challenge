# Data Health Report — social_media_dataset.csv
*Gerado em: 2026-03-21 09:18*

## Score de Confiabilidade

```
  [░░░░░░░░░░░░░░░░░░░░] 0/100
  Veredito: SINTETICO/COMPROMETIDO
```

**Dataset muito provavelmente é sintético ou tem problemas graves.**

## Resumo do Dataset

| Métrica | Valor |
|---------|-------|
| Registros | 52,214 |
| Colunas | 27 |
| Colunas numéricas | 7 |
| Colunas texto | 18 |
| Valores nulos (total) | 17,431 (1.2%) |
| Linhas duplicadas | 0 |

## Problemas Críticos

- **[VARIANCIA]** Coluna "views": CV=0.0099 (muito baixo). Média=10100.28, Std=100.03, Range=875.00. Em 52214 registros, a variação é suspeitamente pequena.

- **[VARIANCIA]** Coluna "likes": CV=0.0258 (muito baixo). Média=1510.27, Std=38.92, Range=314.00. Em 52214 registros, a variação é suspeitamente pequena.

- **[CORRELACAO]** Métricas de engajamento com correlação ~0: views x likes = 0.0008; views x shares = 0.0074; views x comments_count = 0.0050; views x follower_count = 0.0050; likes x shares = 0.0053. Em dados reais, views e likes tipicamente correlacionam >0.5.

- **[CORRELACAO_GERAL]** Correlação média entre TODAS as variáveis numéricas: 0.0035. Isso é estatisticamente improvável em dados reais com 52214 registros.

- **[FAKER]** Coluna "sponsor_name": 87/500 valores contêm padrões típicos de Faker (LLC, Ltd, PLC, Inc, etc.). Alta probabilidade de dados gerados por biblioteca.

## Alertas

- **[OUTLIERS]** Coluna "id": ZERO outliers em 52214 registros. Dados reais quase sempre têm outliers.

- **[OUTLIERS]** Coluna "content_length": ZERO outliers em 52214 registros. Dados reais quase sempre têm outliers.

- **[RANGE]** Coluna "views": Range de apenas 875.00 para média de 10100.28 (8.7% da média). Dados reais costumam ter range muito maior.

- **[OUTLIERS]** Coluna "follower_count": ZERO outliers em 52214 registros. Dados reais quase sempre têm outliers.

- **[UNIFORMIDADE]** Coluna "platform": 5 categorias com distribuição quase perfeita (desvio máximo: 0.0030). Valores: Bilibili: 0.2030, YouTube: 0.2010, Instagram: 0.1996, RedNote: 0.1992, TikTok: 0.1972. Dados reais raramente são tão uniformes.

- **[UNIFORMIDADE]** Coluna "audience_location": 8 categorias com distribuição quase perfeita (desvio máximo: 0.0023). Valores: China: 0.1273, UK: 0.1258, Japan: 0.1255, Brazil: 0.1246, USA: 0.1244, Germany: 0.1244, India: 0.1242, Russia: 0.1237. Dados reais raramente são tão uniformes.

- **[TEMPORAL]** Coluna "post_date": distribuição por dia da semana é quase perfeitamente uniforme (desvio máximo: 0.0022). Dados reais mostram padrões de dias úteis vs fins de semana.

- **[TEMPORAL_HORA]** Coluna "post_date": distribuição por hora uniforme demais. Dados reais têm picos e vales claros.

## Informações

- **[IDS]** Coluna "creator_id" parece ser ID mas tem apenas 5000/52214 valores únicos.

## Recomendação

**NÃO prossiga com análise sem investigar.** Os dados apresentam sinais consistentes de geração sintética. Qualquer insight extraído será baseado em ruído estatístico, não em padrões reais. Recomendação: validar a origem dos dados antes de investir tempo em análise.
