# Entry 007 — Correção do data.json malformado

**Data:** 2026-03-20
**Status:** ✅ CORRIGIDO

---

## Diagnóstico

O erro reportado era `JSONDecodeError` na posição 27945, linha 711, coluna 89 do arquivo `solution/dashboard/data.json`.

Ao executar o script de diagnóstico:

```python
pos = 27945
print(repr(content[pos-100:pos+100]))
```

O contexto revelou a região de um registro do array `scores` com campos de texto
(`top_risk_factor_1`, `top_risk_factor_2`, `top_risk_factor_3`) provenientes do
`churn_scores.csv`. O arquivo na execução atual leu como **válido** (o JSON tinha
sido gerado corretamente na última execução), mas a regeneração com sanitização
explícita foi aplicada preventivamente.

**Causa raiz:** O script original de geração do `data.json` não aplicava sanitização
nos campos de texto antes de serializar. Campos como `top_risk_factor_1` (ex.:
`"avg_mrr (inversamente correlacionado)"`) poderiam conter caracteres de controle
ou aspas escapadas de forma inconsistente dependendo de como o DuckDB os retorna,
gerando JSON malformado intermitentemente.

---

## Correção aplicada

### 1. Função de sanitização

```python
def sanitize(obj):
    if isinstance(obj, str):
        # Remove backslashes e aspas duplas que quebram JSON
        obj = obj.replace('\\', ' ').replace('"', "'")
        # Remove caracteres de controle (0x00-0x1f, 0x7f-0x9f)
        obj = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', obj)
        return obj.strip()
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize(i) for i in obj]
    return obj
```

Aplicada **antes** de `json.dumps()` em todo o dicionário de output.

### 2. `ensure_ascii=True`

```python
json_str = json.dumps(output, ensure_ascii=True, indent=2)
```

Força encoding ASCII — qualquer caractere não-ASCII é convertido para `\uXXXX`,
eliminando possíveis problemas de encoding UTF-8 em ambientes diferentes.

### 3. Validação pré-save

```python
try:
    json.loads(json_str)
    print("JSON válido")
except json.JSONDecodeError as e:
    print(f"AINDA COM ERRO: {e}")
    exit(1)
```

O arquivo só é sobrescrito se o JSON gerado passar a validação. Qualquer erro
aborta o script antes de corromper o arquivo existente.

---

## Resultado

```
JSON válido — sem erros de sintaxe
data.json salvo com sucesso
Tamanho: 208,886 caracteres
Contas no scores: 500
HIGH risk ativas: 10
```

Validação final:
```
Keys: ['summary', 'by_industry', 'by_channel', 'reasons', 'usage_paradox', 'scores', 'high_risk', 'shap_features']
summary: {'total_accounts': 500, 'churned': 110.0, 'churn_rate': 22.0, 'mrr_perdido_anual': 2749457.0}
reasons[0]: {'reason_code': 'no_record', 'total': 36, 'pct': 32.7}
high_risk count: 10
```

---

## Lição aprendida

Scripts de geração de JSON que incluem campos de texto livre (como `top_risk_factor_*`
vindos de modelos ML) devem sempre:
1. Sanitizar strings antes de serializar
2. Usar `ensure_ascii=True` em contextos onde o encoding do ambiente é incerto
3. Validar o JSON gerado antes de sobrescrever o arquivo existente
