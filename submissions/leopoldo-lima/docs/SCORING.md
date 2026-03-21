# Motor de scoring (v0 → v2)

## Objetivo
Disponibilizar um baseline de score determinístico e explicável para oportunidades do pipeline.

## Implementação
- Código: `src/scoring/engine.py`
- Regras versionadas: `config/scoring-rules.json` (**`version`: 2** — ver **`docs/SCORING_V2.md`**)
- Testes: `tests/test_scoring_engine.py`, `tests/test_scoring_v2_features.py`

## Entradas mínimas esperadas
- `deal_stage`
- `close_value`
- `account` (pode estar vazio no snapshot atual; gera penalidade e risco)

## Como o score é calculado
1. Inicia em `base_score`.
2. Soma peso por `deal_stage`.
3. Soma bônus por faixa de `close_value`.
4. Aplica penalidade quando `account` está ausente.
5. Faz clamp final para faixa `0..100`.

## Explicabilidade retornada
O resultado inclui:
- `score`
- `positives`
- `negatives`
- `risks`
- `next_best_action`

Isso permite justificar por que um lead subiu ou desceu no ranking sem depender de lógica na UI.

## Exemplo resumido
Entrada:
- `deal_stage=Engaging`
- `close_value=12000`
- `account=Acme Corp`

Saída esperada (aproximada, dependendo das regras versionadas):
- score alto
- positivos de estágio e valor
- sem risco de account ausente
- ação de prioridade alta

## Execução e validação

```powershell
python .\scripts\tasks.py test
python .\scripts\tasks.py build
```

Ou diretamente:

```powershell
python -m pytest -q
```

## Limitações
- Regras são heurísticas e **não** calibradas com performance histórica (v2 aumenta sinais, não precisão validada).
- A UI consome score agregado via API; o detalhe JSON inclui `scoreExplanation` com fatores textuais.
