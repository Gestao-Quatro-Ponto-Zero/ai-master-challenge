# Registro de métricas

| Métrica | Fórmula | Unidade/denominador | Uso | Limitação |
|---|---|---|---|---|
| `engagement_total` | likes + shares + comments | interações/post | volume descritivo | ações têm pesos iguais |
| `engagement_rate_views` | engagement_total / views | interações/view | métrica primária proposta | views não são usuários únicos |
| `like_rate_views` | likes / views | likes/view | diagnóstico | plataforma pode contar ações diferente |
| `share_rate_views` | shares / views | shares/view | intenção de distribuição | sem valor econômico direto |
| `comment_rate_views` | comments / views | comentários/view | profundidade aproximada | qualidade não avaliada |
| `views_per_follower` | views / follower_count | views/seguidor | alcance relativo | seguidores podem não representar audiência disponível |

Nenhuma métrica representa ROI. Fórmulas são derivadas pelo projeto, não fornecidas pela fonte. A métrica primária requer aprovação humana antes de recomendação final.
