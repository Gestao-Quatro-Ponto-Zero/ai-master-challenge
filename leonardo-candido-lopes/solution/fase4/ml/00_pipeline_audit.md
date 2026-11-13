# 00 — Auditoria final pré-treinamento (rastreabilidade)

> Gerado por `build_audit_md.py` a partir de `splits/audit_results.json` (saída de `pipeline.py`, seed 42). O CSV original não foi alterado.

## 1. Reconciliação da diferença de 235 registros (Fase 3: 47.837 → 47.602)

**EVIDÊNCIA:** os 235 = **133 textos com < 5 palavras** + **102 registros em 38 grupos** que compartilham as mesmas 15 primeiras palavras com rótulos diferentes. Sobreposição entre os dois critérios = 0; união = 235. Reproduzido exatamente nesta fase.

Na Fase 4 a regra mudou: os 133 curtos **não são mais excluídos** (ficam com `short_flag` e passam por sensibilidade); os 102 conflitantes seguem em quarentena, somados a conflitos por cosseno.

## 2. Log passo a passo

| Etapa | Antes | Depois | Removidos | Critério | Decisão |
|---|---:|---:|---:|---|---|
| 1_nulos | 47.837 | 47.837 | 0 | Document ou Topic_group nulo | excluir (nenhum encontrado) |
| 2_lixo | 47.837 | 47.837 | 0 | <= 2 caracteres alfanuméricos | excluir |
| 2b_curtos | 47.837 | 47.837 | 0 | < 5 palavras | manter com flag short_flag; sensibilidade com/sem |
| 3_dup_exatas | 47.837 | 47.837 | 0 | Document+Topic_group idênticos (e texto normalizado idêntico) | manter 1 (nenhuma encontrada) |
| 4_conflitantes | 47.837 | 47.559 | 278 | grupo prefixo-15 com >1 rótulo OU par cosseno>=0.98 com rótulos diferentes | quarentena (fora de treino/val/teste) |
| 5_quase_dup_mesmo_rotulo | 47.559 | 46.993 | 566 | mesmo prefixo-15 e mesmo rótulo | manter 1 representante |

**Total final (conservador — principal): 46.993** registros limpos.

## 3. Textos curtos (< 5 palavras)

- Lixo (≤ 2 caracteres): **0** → nada a excluir.
- Curtos: **133** (por nº de palavras: {'2': 14, '3': 35, '4': 84}; por classe: {'Hardware': 40, 'Access': 37, 'HR Support': 35, 'Miscellaneous': 13, 'Administrative rights': 4, 'Purchase': 3, 'Internal Project': 1}).
- Inspeção: são abreviações legítimas de chamados (ex.: 'password reset contacted change', 'new starter please'). Decisão: **manter com flag** e medir impacto.
- Primeiros 5 exemplos:

| row_id | Texto | Rótulo |
|---:|---|---|
| 439 | annual leave se ca | HR Support |
| 526 | access hi please thank | HR Support |
| 561 | new starter please | HR Support |
| 754 | access dear browse thank | HR Support |
| 759 | reactivate access card va | Access |

## 4. Duplicatas

- Exatas (Document+Topic_group): **0**; texto idêntico: **0**; idêntico após normalização: **0**.
- Quase-duplicatas (mesmas 15 primeiras palavras): 365 grupos com 1011 registros.
- Mesmo rótulo → manter 1 representante (o primeiro): ver etapa 5 do log.

## 5. Quase-duplicatas com rótulos CONFLITANTES → quarentena (`splits/quarantine.csv`)

- Critério A (prefixo-15): 38 grupos, 102 registros.
- Critério B (par cosseno TF-IDF ≥ 0.98 com rótulos diferentes): 211 registros (35 já no critério A).
- Padrões de conflito (critério A, nº de grupos):

| Rótulos em conflito | Grupos |
|---|---:|
| HR Support / Hardware | 8 |
| Hardware / Miscellaneous | 7 |
| Hardware / Storage | 6 |
| HR Support / Miscellaneous | 6 |
| Hardware / Miscellaneous / Storage | 2 |
| Administrative rights / Miscellaneous | 2 |
| Access / Miscellaneous | 2 |
| Access / Administrative rights | 1 |
| Access / Internal Project | 1 |
| HR Support / Hardware / Miscellaneous | 1 |
| Access / Hardware | 1 |
| Access / Hardware / Purchase | 1 |

Exemplos (prefixo truncado):

- `access request for a list or library library requesting library links library manage setting library` → {'Hardware': 5, 'Storage': 3, 'Miscellaneous': 1}
- `access request for a list or library november library requesting library links library manage settin` → {'Hardware': 1, 'Storage': 1}
- `access request for a list or library october pm library requesting library links library manage` → {'Hardware': 1, 'Storage': 1}
- `access request for a list or library pm library requesting library links library manage setting` → {'Storage': 1, 'Hardware': 1}
- `access request for a list or library thursday pm library requesting library links library manage` → {'Storage': 3, 'Hardware': 2, 'Miscellaneous': 2}

**INTERPRETAÇÃO:** textos praticamente iguais com rótulos diferentes indicam ruído de rotulagem; mantê-los ensinaria contradições e contaminaria o teste.

## 6. Divisão por grupos (anti-vazamento)

- Grupos = componentes conexos de pares com cosseno ≥ 0.9 **unidos** aos grupos de prefixo-15 → 42.163 grupos (1.639 com > 1 registro); maior grupo (limpo) = 612 registros.
- `StratifiedGroupKFold(n_splits=20, shuffle=True, random_state=42)`: folds 0–2 → teste, 3–5 → validação, 6–19 → treino. (`GroupShuffleSplit` puro não estratifica; esta é a alternativa estratificada.)
- Tamanhos: {'train': 33237, 'val': 6990, 'test': 6766} → {'train': 0.7073, 'val': 0.1487, 'test': 0.144}.
- Desvio máximo da proporção por classe vs. global (p.p.): {'train': 0.52, 'val': 0.91, 'test': 1.61}. **Limitação:** Purchase tem uma família de templates muito grande (maior grupo) que fica inteira num único split; por isso o teste tem menos Purchase do que o treino.

| Categoria | Treino | Validação | Teste | Total |
|---|---:|---:|---:|---:|
| Hardware | 9.460 | 2.028 | 1.934 | 13.422 |
| HR Support | 7.555 | 1.604 | 1.551 | 10.710 |
| Access | 4.959 | 1.061 | 1.057 | 7.077 |
| Miscellaneous | 4.865 | 1.050 | 1.043 | 6.958 |
| Storage | 1.939 | 414 | 389 | 2.742 |
| Purchase | 1.759 | 270 | 214 | 2.243 |
| Internal Project | 1.473 | 308 | 315 | 2.096 |
| Administrative rights | 1.227 | 255 | 263 | 1.745 |

### Verificação de vazamento

| Checagem | Valor |
|---|---:|
| train_val_groups | 0 |
| train_val_norm_text | 0 |
| train_val_prefix15 | 0 |
| train_test_groups | 0 |
| train_test_norm_text | 0 |
| train_test_prefix15 | 0 |
| val_test_groups | 0 |
| val_test_norm_text | 0 |
| val_test_prefix15 | 0 |
| pairs_cos>=0.90_across_splits | 0 |
| pairs_cos_0.80-0.90_across_splits_residual | 13.751 |
| test_rows_with_train_neighbor_cos>=0.80 | 1.026 |

**EVIDÊNCIA:** zero grupos. textos ou prefixos compartilhados e zero pares cosseno ≥ 0.90 entre splits. **Risco residual:** 13.751 pares com cosseno 0.80–0.90 cruzam splits; 1.026 linhas de teste têm vizinho no treino. No teste. F1-macro = 0.9211 nessas linhas vs. **0.8204** nas 5.740 linhas sem vizinho → o desempenho em texto realmente novo é mais próximo de 0.8204.

## 7. Pesos por classe (`compute_class_weight('balanced')`, treino)

| Classe | Peso |
|---|---:|
| Access | 0.8378 |
| Administrative rights | 3.386 |
| HR Support | 0.5499 |
| Hardware | 0.4392 |
| Internal Project | 2.8205 |
| Miscellaneous | 0.854 |
| Purchase | 2.3619 |
| Storage | 2.1427 |

## 8. Conservador vs. agressivo

| Abordagem | Removidos/quarentena | Restantes | F1-macro no MESMO teste* |
|---|---:|---:|---:|
| Sem limpeza (sujo) | 0 | 47.837 | 0.8362 |
| Auditoria Fase 3 | 235 | 47.602 | — |
| **Conservador (principal)** | 844 | 46.993 | 0.8363 |
| Conservador sem curtos | — | — | 0.8362 |
| Agressivo (lixo + conflitos prefixo + conflitos cosseno>=0.90 + curtos<5 palavras + quase-dup mesmo rótulo) | 1520 | 46.317 | 0.8364 |

\* Mesmo modelo (LinearSVC sem calibração, C escolhido no val), mesmo split por folds, mesmo teste limpo. **EVIDÊNCIA:** a limpeza muda o F1-macro em ≤ 0,001 — o ganho da limpeza é de **integridade da avaliação** (sem vazamento/contradição no teste), não de desempenho.
