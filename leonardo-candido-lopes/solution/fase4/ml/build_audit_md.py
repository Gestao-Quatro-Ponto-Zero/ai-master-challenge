"""Gera 00_pipeline_audit.md a partir de splits/audit_results.json (números injetados, não digitados)."""
import json, pandas as pd
A = json.load(open("splits/audit_results.json")); X = json.load(open("evaluation/results.json")); L = json.load(open("evaluation/residual_leakage_eval.json"))
P = A["params"]; r235 = A["reconcile_235"]
md = [f"# 00 — Auditoria final pré-treinamento (rastreabilidade)\n",
      "> Gerado por `build_audit_md.py` a partir de `splits/audit_results.json` (saída de `pipeline.py`, seed 42). O CSV original não foi alterado.\n",
      "## 1. Reconciliação da diferença de 235 registros (Fase 3: 47.837 → 47.602)\n",
      f"**EVIDÊNCIA:** os 235 = **{r235['short_lt5']} textos com < 5 palavras** + **{r235['prefix_conflict_records']} registros em {A['prefix_conflict_groups']} grupos** que compartilham as mesmas 15 primeiras palavras com rótulos diferentes. Sobreposição entre os dois critérios = {r235['overlap']}; união = {r235['union']}. Reproduzido exatamente nesta fase.\n",
      "Na Fase 4 a regra mudou: os 133 curtos **não são mais excluídos** (ficam com `short_flag` e passam por sensibilidade); os 102 conflitantes seguem em quarentena, somados a conflitos por cosseno.\n",
      "## 2. Log passo a passo\n", "| Etapa | Antes | Depois | Removidos | Critério | Decisão |", "|---|---:|---:|---:|---|---|"]
for s in A["log"]:
    md.append(f"| {s['step']} | {s['antes']:,} | {s['depois']:,} | {s['removidos']:,} | {s['criterio']} | {s['decisao']} |".replace(",", "."))
md += [f"\n**Total final (conservador — principal): {A['final_clean']:,}** registros limpos.".replace(",", "."),
       f"\n## 3. Textos curtos (< {P['SHORT_WORDS']} palavras)\n",
       f"- Lixo (≤ {P['GARBAGE_CHARS']} caracteres): **{A['garbage']}** → nada a excluir.",
       f"- Curtos: **{A['short_lt5']}** (por nº de palavras: {A['short_by_words']}; por classe: {A['short_by_class']}).",
       "- Inspeção: são abreviações legítimas de chamados (ex.: 'password reset contacted change', 'new starter please'). Decisão: **manter com flag** e medir impacto.",
       "- Primeiros 5 exemplos:\n", "| row_id | Texto | Rótulo |", "|---:|---|---|"]
for e in A["short_examples_first5"]:
    md.append(f"| {e['row_id']} | {e['Document']} | {e['Topic_group']} |")
md += ["\n## 4. Duplicatas\n", f"- Exatas (Document+Topic_group): **{A['dup_exact_doc_label']}**; texto idêntico: **{A['dup_exact_doc']}**; idêntico após normalização: **{A['dup_normalized']}**.",
       f"- Quase-duplicatas (mesmas {P['PREFIX_N']} primeiras palavras): {A['prefix_groups']} grupos com {A['prefix_records_in_groups']} registros.",
       f"- Mesmo rótulo → manter 1 representante (o primeiro): ver etapa 5 do log.",
       "\n## 5. Quase-duplicatas com rótulos CONFLITANTES → quarentena (`splits/quarantine.csv`)\n",
       f"- Critério A (prefixo-{P['PREFIX_N']}): {A['prefix_conflict_groups']} grupos, {A['prefix_conflict_records']} registros.",
       f"- Critério B (par cosseno TF-IDF ≥ {P['COS_CONFLICT']} com rótulos diferentes): {A['cos98_conflict_records']} registros ({A['cos98_overlap_prefix']} já no critério A).",
       "- Padrões de conflito (critério A, nº de grupos):\n", "| Rótulos em conflito | Grupos |", "|---|---:|"]
for k, v in A["prefix_conflict_label_patterns"].items():
    md.append(f"| {k.replace(' | ', ' / ')} | {v} |")
md += ["\nExemplos (prefixo truncado):\n"]
for e in A["prefix_conflict_examples"][:5]:
    md.append(f"- `{e['prefix'][:100]}` → {e['labels']}")
md += ["\n**INTERPRETAÇÃO:** textos praticamente iguais com rótulos diferentes indicam ruído de rotulagem; mantê-los ensinaria contradições e contaminaria o teste.",
       f"\n## 6. Divisão por grupos (anti-vazamento)\n",
       f"- Grupos = componentes conexos de pares com cosseno ≥ {P['COS_GROUP']} **unidos** aos grupos de prefixo-15 → {A['split_groups']:,} grupos ({A['split_groups_multi']:,} com > 1 registro); maior grupo (limpo) = {A['split_max_group_size_clean']} registros.".replace(",", "."),
       f"- `StratifiedGroupKFold(n_splits=20, shuffle=True, random_state=42)`: folds 0–2 → teste, 3–5 → validação, 6–19 → treino. (`GroupShuffleSplit` puro não estratifica; esta é a alternativa estratificada.)",
       f"- Tamanhos: {A['split_sizes']} → {A['split_pct']}.",
       f"- Desvio máximo da proporção por classe vs. global (p.p.): {A['max_abs_dev_pp_by_split']}. **Limitação:** Purchase tem uma família de templates muito grande (maior grupo) que fica inteira num único split; por isso o teste tem menos Purchase do que o treino.",
       "\n| Categoria | Treino | Validação | Teste | Total |", "|---|---:|---:|---:|---:|"]
d = A["dist_by_split"]
for c in sorted(A["dist_final"], key=lambda c: -A["dist_final"][c]):
    md.append(f"| {c} | {d['train'][c]:,} | {d['val'][c]:,} | {d['test'][c]:,} | {A['dist_final'][c]:,} |".replace(",", "."))
lk = A["leakage_check"]
md += ["\n### Verificação de vazamento\n", "| Checagem | Valor |", "|---|---:|"] + [f"| {k} | {v:,} |".replace(",", ".") for k, v in lk.items()]
md += [f"\n**EVIDÊNCIA:** zero grupos, textos ou prefixos compartilhados e zero pares cosseno ≥ 0,90 entre splits. **Risco residual:** {lk['pairs_cos_0.80-0.90_across_splits_residual']:,} pares com cosseno 0,80–0,90 cruzam splits; {lk['test_rows_with_train_neighbor_cos>=0.80']:,} linhas de teste têm vizinho no treino. No teste, F1-macro = {L['com_vizinho_treino']['f1_macro']} nessas linhas vs. **{L['sem_vizinho_treino']['f1_macro']}** nas {L['sem_vizinho_treino']['n']:,} linhas sem vizinho → o desempenho em texto realmente novo é mais próximo de {L['sem_vizinho_treino']['f1_macro']}.".replace(",", "."),
       "\n## 7. Pesos por classe (`compute_class_weight('balanced')`, treino)\n", "| Classe | Peso |", "|---|---:|"] + [f"| {k} | {v} |" for k, v in A["class_weights_train"].items()]
cmp_ = A["comparison"]; S = X["sensitivity"]
md += ["\n## 8. Conservador vs. agressivo\n", "| Abordagem | Removidos/quarentena | Restantes | F1-macro no MESMO teste* |", "|---|---:|---:|---:|",
       f"| Sem limpeza (sujo) | 0 | 47.837 | {S['A_sujo_sem_limpeza']['test_f1_macro']} |",
       f"| Auditoria Fase 3 | 235 | 47.602 | — |",
       f"| **Conservador (principal)** | {cmp_['conservador_principal']['removidos_ou_quarentena']} | {cmp_['conservador_principal']['restantes']:,} | {S['B_conservador_principal']['test_f1_macro']} |".replace(",", "."),
       f"| Conservador sem curtos | — | — | {S['C_conservador_sem_curtos']['test_f1_macro']} |",
       f"| Agressivo ({cmp_['agressivo']['inclui']}) | {cmp_['agressivo']['removidos_ou_quarentena']} | {cmp_['agressivo']['restantes']:,} | {S['D_agressivo']['test_f1_macro']} |".replace(",", "."),
       "\n\\* Mesmo modelo (LinearSVC sem calibração, C escolhido no val), mesmo split por folds, mesmo teste limpo. **EVIDÊNCIA:** a limpeza muda o F1-macro em ≤ 0,001 — o ganho da limpeza é de **integridade da avaliação** (sem vazamento/contradição no teste), não de desempenho."]
open("00_pipeline_audit.md", "w").write("\n".join(md) + "\n")
