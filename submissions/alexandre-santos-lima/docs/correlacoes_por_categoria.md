# Correlação com churn — por categoria

Gerado por `solution/scripts/02_correlacoes.py`. `q` = p-valor corrigido (Benjamini-Hochberg). **Força** normalizada 0–1: para numéricas `|AUC−0,5|×2`; para categóricas V de Cramér. Referência: < 0,10 desprezível, 0,10–0,20 fraca, 0,20–0,40 moderada.


## Alvo: `churn_flag_conta` (accounts.churn_flag) — 110 de 500 contas (22%)

Variáveis testadas: 49 · sobrevivem à correção: **0**


### perfil

| variável | força | medida | p | q | leitura |
|---|---|---|---|---|---|
| `perfil_dias_desde_signup` | 0.12 | AUC 0.56 | 0.059 | 0.638 | churn 371.67 × retida 329.43 (+13%) |
| `perfil_industry` | 0.13 | V de Cramér 0.13 | 0.066 | 0.638 | maior: DevTools 31% (n=113); menor: Cybersecurity 16% (n=100) |
| `perfil_referral_source` | 0.13 | V de Cramér 0.13 | 0.079 | 0.638 | maior: event 30% (n=96); menor: partner 15% (n=89) |
| `perfil_is_trial` | 0.04 | V de Cramér 0.04 | 0.388 | 0.755 | maior: True 26% (n=97); menor: False 21% (n=403) |
| `perfil_coorte_signup` | 0.11 | V de Cramér 0.11 | 0.563 | 0.835 | maior: 2023Q1 29% (n=55); menor: 2024Q4 15% (n=80) |
| `perfil_country` | 0.09 | V de Cramér 0.09 | 0.659 | 0.921 | maior: DE 32% (n=25); menor: AU 12% (n=32) |
| `perfil_seats` | 0.02 | AUC 0.49 | 0.692 | 0.921 | churn 19.24 × retida 20.93 (-8%) |
| `perfil_plan_tier` | 0.00 | V de Cramér 0.00 | 0.999 | 0.999 | maior: Enterprise 22% (n=154); menor: Pro 22% (n=178) |

### receita

| variável | força | medida | p | q | leitura |
|---|---|---|---|---|---|
| `receita_mrr_medio_assinatura` | 0.09 | AUC 0.46 | 0.154 | 0.638 | churn 2,082.92 × retida 2,315.30 (-10%) |
| `receita_assinaturas_trial` | 0.08 | AUC 0.54 | 0.181 | 0.638 | churn 1.67 × retida 1.52 (+10%) |
| `receita_assinaturas_encerradas` | 0.08 | AUC 0.54 | 0.203 | 0.638 | churn 1.05 × retida 0.95 (+11%) |
| `receita_pct_assin_basic` | 0.07 | AUC 0.53 | 0.271 | 0.737 | churn 0.33 × retida 0.32 (+4%) |
| `receita_assinaturas` | 0.07 | AUC 0.53 | 0.292 | 0.753 | churn 10.29 × retida 9.92 (+4%) |
| `receita_pct_mrr_perdido` | 0.06 | AUC 0.53 | 0.311 | 0.755 | churn 0.11 × retida 0.10 (+21%) |
| `receita_assinaturas_ativas` | 0.05 | AUC 0.53 | 0.395 | 0.755 | churn 9.24 × retida 8.97 (+3%) |
| `receita_mrr_perdido` | 0.05 | AUC 0.52 | 0.411 | 0.755 | churn 2,564.47 × retida 2,300.12 (+11%) |
| `receita_pct_assin_enterprise` | 0.05 | AUC 0.47 | 0.416 | 0.755 | churn 0.34 × retida 0.35 (-3%) |
| `receita_mrr_ativo` | 0.04 | AUC 0.48 | 0.486 | 0.788 | churn 18,846.85 × retida 20,734.50 (-9%) |
| `receita_arr_ativo` | 0.04 | AUC 0.48 | 0.486 | 0.788 | churn 226,162.15 × retida 248,814.00 (-9%) |
| `receita_downgrades` | 0.02 | AUC 0.49 | 0.733 | 0.921 | churn 0.43 × retida 0.44 (-3%) |
| `receita_seats_ativos` | 0.01 | AUC 0.49 | 0.821 | 0.921 | churn 264.25 × retida 271.00 (-2%) |
| `receita_pct_auto_renew` | 0.01 | AUC 0.51 | 0.855 | 0.921 | churn 0.80 × retida 0.80 (+0%) |
| `receita_pct_assin_pro` | 0.01 | AUC 0.51 | 0.862 | 0.921 | churn 0.33 × retida 0.33 (-1%) |
| `receita_pct_anual` | 0.01 | AUC 0.50 | 0.883 | 0.921 | churn 0.49 × retida 0.49 (-1%) |
| `receita_upgrades` | 0.01 | AUC 0.50 | 0.907 | 0.925 | churn 1.05 × retida 1.06 (-0%) |

### uso

| variável | força | medida | p | q | leitura |
|---|---|---|---|---|---|
| `uso_dias_desde_ultimo` | 0.14 | AUC 0.43 | 0.023 | 0.638 | churn 12.27 × retida 17.45 (-30%) |
| `uso_pct_registros_com_erro` | 0.13 | AUC 0.44 | 0.042 | 0.638 | churn 0.30 × retida 0.31 (-4%) |
| `uso_eventos_2024` | 0.10 | AUC 0.55 | 0.106 | 0.638 | churn 264.26 × retida 248.45 (+6%) |
| `uso_taxa_erro` | 0.10 | AUC 0.45 | 0.115 | 0.638 | churn 0.05 × retida 0.06 (-6%) |
| `uso_duracao_h` | 0.08 | AUC 0.54 | 0.203 | 0.638 | churn 43.99 × retida 41.76 (+5%) |
| `uso_eventos` | 0.08 | AUC 0.54 | 0.206 | 0.638 | churn 522.04 × retida 495.13 (+5%) |
| `uso_registros_beta` | 0.08 | AUC 0.54 | 0.214 | 0.638 | churn 5.48 × retida 4.98 (+10%) |
| `uso_features_distintas` | 0.08 | AUC 0.54 | 0.217 | 0.638 | churn 28.34 × retida 27.41 (+3%) |
| `uso_registros` | 0.08 | AUC 0.54 | 0.221 | 0.638 | churn 52.05 × retida 49.42 (+5%) |
| `uso_eventos_2023` | 0.05 | AUC 0.52 | 0.431 | 0.755 | churn 257.77 × retida 246.68 (+4%) |
| `uso_variacao_2024_vs_2023` | 0.04 | AUC 0.52 | 0.499 | 0.788 | churn 0.07 × retida 0.05 (+44%) |
| `uso_registros_com_erro` | 0.03 | AUC 0.51 | 0.645 | 0.921 | churn 15.65 × retida 15.41 (+2%) |
| `uso_duracao_media_min` | 0.02 | AUC 0.49 | 0.787 | 0.921 | churn 50.90 × retida 50.95 (-0%) |
| `uso_erros` | 0.02 | AUC 0.51 | 0.795 | 0.921 | churn 28.15 × retida 28.23 (-0%) |
| `uso_pct_beta` | 0.01 | AUC 0.49 | 0.867 | 0.921 | churn 0.10 × retida 0.10 (-0%) |

### suporte

| variável | força | medida | p | q | leitura |
|---|---|---|---|---|---|
| `suporte_primeira_resposta_media_min` | 0.10 | AUC 0.45 | 0.103 | 0.638 | churn 84.93 × retida 89.58 (-5%) |
| `suporte_pct_urgente_alta` | 0.09 | AUC 0.46 | 0.157 | 0.638 | churn 0.48 × retida 0.53 (-9%) |
| `suporte_tickets` | 0.06 | AUC 0.47 | 0.342 | 0.755 | churn 3.93 × retida 4.02 (-2%) |
| `suporte_pct_escalonados` | 0.04 | AUC 0.52 | 0.391 | 0.755 | churn 0.06 × retida 0.04 (+41%) |
| `suporte_escalonamentos` | 0.04 | AUC 0.52 | 0.399 | 0.755 | churn 0.22 × retida 0.18 (+20%) |
| `suporte_satisfacao_media` | 0.04 | AUC 0.52 | 0.540 | 0.827 | churn 4.00 × retida 3.95 (+1%) |
| `suporte_resolucao_media_h` | 0.02 | AUC 0.49 | 0.717 | 0.921 | churn 35.49 × retida 36.45 (-3%) |
| `suporte_resolucao_max_h` | 0.02 | AUC 0.49 | 0.750 | 0.921 | churn 55.66 × retida 56.68 (-2%) |
| `suporte_pct_sem_nota` | 0.01 | AUC 0.49 | 0.837 | 0.921 | churn 0.40 × retida 0.40 (-2%) |

## Alvo: `churn_tem_evento` (tem evento em churn_events) — 352 de 500 contas (70%)

Variáveis testadas: 49 · sobrevivem à correção: **0**


### perfil

| variável | força | medida | p | q | leitura |
|---|---|---|---|---|---|
| `perfil_referral_source` | 0.12 | V de Cramér 0.12 | 0.143 | 0.977 | maior: partner 75% (n=89); menor: ads 60% (n=98) |
| `perfil_coorte_signup` | 0.13 | V de Cramér 0.13 | 0.276 | 0.977 | maior: 2023Q4 80% (n=65); menor: 2023Q2 57% (n=54) |
| `perfil_seats` | 0.04 | AUC 0.52 | 0.444 | 0.977 | churn 20.67 × retida 20.30 (+2%) |
| `perfil_country` | 0.09 | V de Cramér 0.09 | 0.640 | 0.977 | maior: UK 78% (n=58); menor: DE 56% (n=25) |
| `perfil_plan_tier` | 0.04 | V de Cramér 0.04 | 0.713 | 0.977 | maior: Pro 72% (n=178); menor: Basic 68% (n=168) |
| `perfil_industry` | 0.06 | V de Cramér 0.06 | 0.785 | 0.977 | maior: DevTools 73% (n=113); menor: HealthTech 67% (n=96) |
| `perfil_is_trial` | 0.01 | V de Cramér 0.01 | 0.845 | 0.977 | maior: False 71% (n=403); menor: True 69% (n=97) |
| `perfil_dias_desde_signup` | 0.00 | AUC 0.50 | 0.934 | 0.977 | churn 338.74 × retida 338.69 (+0%) |

### receita

| variável | força | medida | p | q | leitura |
|---|---|---|---|---|---|
| `receita_upgrades` | 0.07 | AUC 0.54 | 0.187 | 0.977 | churn 1.11 × retida 0.95 (+17%) |
| `receita_mrr_perdido` | 0.07 | AUC 0.53 | 0.206 | 0.977 | churn 2,417.94 × retida 2,216.39 (+9%) |
| `receita_pct_mrr_perdido` | 0.06 | AUC 0.53 | 0.303 | 0.977 | churn 0.10 × retida 0.09 (+20%) |
| `receita_downgrades` | 0.05 | AUC 0.52 | 0.311 | 0.977 | churn 0.45 × retida 0.39 (+16%) |
| `receita_assinaturas_encerradas` | 0.05 | AUC 0.53 | 0.338 | 0.977 | churn 1.00 × retida 0.91 (+10%) |
| `receita_seats_ativos` | 0.05 | AUC 0.52 | 0.414 | 0.977 | churn 267.20 × retida 275.01 (-3%) |
| `receita_assinaturas_trial` | 0.04 | AUC 0.48 | 0.434 | 0.977 | churn 1.53 × retida 1.62 (-6%) |
| `receita_mrr_medio_assinatura` | 0.04 | AUC 0.52 | 0.494 | 0.977 | churn 2,285.20 × retida 2,214.17 (+3%) |
| `receita_pct_assin_pro` | 0.03 | AUC 0.51 | 0.620 | 0.977 | churn 0.33 × retida 0.33 (+1%) |
| `receita_mrr_ativo` | 0.03 | AUC 0.51 | 0.625 | 0.977 | churn 20,283.72 × retida 20,403.65 (-1%) |
| `receita_arr_ativo` | 0.03 | AUC 0.51 | 0.625 | 0.977 | churn 243,404.59 × retida 244,843.78 (-1%) |
| `receita_pct_assin_basic` | 0.03 | AUC 0.49 | 0.645 | 0.977 | churn 0.32 × retida 0.32 (-1%) |
| `receita_assinaturas` | 0.02 | AUC 0.51 | 0.703 | 0.977 | churn 10.02 × retida 9.95 (+1%) |
| `receita_pct_auto_renew` | 0.01 | AUC 0.51 | 0.850 | 0.977 | churn 0.80 × retida 0.80 (+1%) |
| `receita_pct_assin_enterprise` | 0.01 | AUC 0.51 | 0.858 | 0.977 | churn 0.35 × retida 0.35 (-1%) |
| `receita_assinaturas_ativas` | 0.00 | AUC 0.50 | 0.960 | 0.977 | churn 9.02 × retida 9.04 (-0%) |
| `receita_pct_anual` | 0.00 | AUC 0.50 | 0.977 | 0.977 | churn 0.49 × retida 0.49 (-0%) |

### uso

| variável | força | medida | p | q | leitura |
|---|---|---|---|---|---|
| `uso_features_distintas` | 0.07 | AUC 0.54 | 0.196 | 0.977 | churn 27.76 × retida 27.27 (+2%) |
| `uso_pct_beta` | 0.06 | AUC 0.47 | 0.270 | 0.977 | churn 0.10 × retida 0.10 (-4%) |
| `uso_registros_beta` | 0.05 | AUC 0.48 | 0.412 | 0.977 | churn 5.04 × retida 5.21 (-3%) |
| `uso_duracao_media_min` | 0.04 | AUC 0.52 | 0.432 | 0.977 | churn 51.01 × retida 50.77 (+0%) |
| `uso_erros` | 0.04 | AUC 0.52 | 0.470 | 0.977 | churn 28.39 × retida 27.79 (+2%) |
| `uso_registros_com_erro` | 0.03 | AUC 0.52 | 0.555 | 0.977 | churn 15.53 × retida 15.31 (+1%) |
| `uso_duracao_h` | 0.03 | AUC 0.52 | 0.569 | 0.977 | churn 42.51 × retida 41.63 (+2%) |
| `uso_eventos_2024` | 0.03 | AUC 0.52 | 0.576 | 0.977 | churn 254.05 × retida 246.89 (+3%) |
| `uso_registros` | 0.03 | AUC 0.51 | 0.657 | 0.977 | churn 50.26 × retida 49.39 (+2%) |
| `uso_eventos` | 0.02 | AUC 0.51 | 0.687 | 0.977 | churn 503.43 × retida 495.38 (+2%) |
| `uso_dias_desde_ultimo` | 0.01 | AUC 0.49 | 0.794 | 0.977 | churn 16.12 × retida 16.76 (-4%) |
| `uso_pct_registros_com_erro` | 0.01 | AUC 0.49 | 0.822 | 0.977 | churn 0.31 × retida 0.31 (-1%) |
| `uso_taxa_erro` | 0.01 | AUC 0.50 | 0.873 | 0.977 | churn 0.06 × retida 0.06 (-1%) |
| `uso_eventos_2023` | 0.01 | AUC 0.50 | 0.908 | 0.977 | churn 249.39 × retida 248.49 (+0%) |
| `uso_variacao_2024_vs_2023` | 0.00 | AUC 0.50 | 0.969 | 0.977 | churn 0.05 × retida 0.07 (-19%) |

### suporte

| variável | força | medida | p | q | leitura |
|---|---|---|---|---|---|
| `suporte_escalonamentos` | 0.05 | AUC 0.52 | 0.216 | 0.977 | churn 0.20 × retida 0.16 (+24%) |
| `suporte_pct_escalonados` | 0.05 | AUC 0.52 | 0.241 | 0.977 | churn 0.05 × retida 0.04 (+10%) |
| `suporte_pct_urgente_alta` | 0.05 | AUC 0.47 | 0.352 | 0.977 | churn 0.51 × retida 0.53 (-3%) |
| `suporte_pct_sem_nota` | 0.04 | AUC 0.52 | 0.535 | 0.977 | churn 0.40 × retida 0.39 (+2%) |
| `suporte_tickets` | 0.03 | AUC 0.49 | 0.625 | 0.977 | churn 3.96 × retida 4.09 (-3%) |
| `suporte_primeira_resposta_media_min` | 0.02 | AUC 0.51 | 0.783 | 0.977 | churn 88.78 × retida 88.04 (+1%) |
| `suporte_satisfacao_media` | 0.01 | AUC 0.51 | 0.828 | 0.977 | churn 3.96 × retida 3.97 (-0%) |
| `suporte_resolucao_media_h` | 0.01 | AUC 0.50 | 0.876 | 0.977 | churn 36.24 × retida 36.25 (-0%) |
| `suporte_resolucao_max_h` | 0.01 | AUC 0.50 | 0.892 | 0.977 | churn 56.59 × retida 56.15 (+1%) |
