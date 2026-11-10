# Contrato do score: o arquivo que o núcleo de scoring emite

Quem escreve: o núcleo de scoring (`solution/score.py`, a construir). Quem lê: a interface e a camada de IA. Os três trabalham ao mesmo tempo a partir deste contrato; nenhum lê o código do outro.

Todo número citado aqui foi impresso por `solution/validate.py` (saída guardada em `docs/validacao-saida.txt`) ou por `solution/audit.py` (`docs/auditoria-saida.txt`).

## Arquivo

`solution/out/score.json`, UTF-8, gerado por um comando (`python solution/score.py`), sem ler o relógio do sistema. "Hoje" é a data de referência: a última data presente nos dados (2017-12-31).

```json
{
  "meta": {
    "reference_date": "2017-12-31",
    "written_by": "solution/score.py",
    "rule": {"window_days": 90, "alive_min": 0.25,
             "focus_expected_value_min": 1000, "cool_days": 30},
    "deadline": {"closings_total": 6711, "closings_after_deadline": 1},
    "longest_win_days": 138,
    "group_evidence": {
      "focar agora":     {"n": 2094, "won": 769,  "lost": 447, "no_outcome": 878,  "won_value": 3609564},
      "manter aquecido": {"n": 2921, "won": 1015, "lost": 592, "no_outcome": 1314, "won_value": 585105},
      "deixar ir":       {"n": 1417, "won": 0,    "lost": 1,   "no_outcome": 1416, "won_value": 0}
    },
    "curve": [{"days_open": 0, "chance": 0.415}, {"days_open": 15, "chance": 0.412}]
  },
  "deals": [ { "...": "um registro por negócio aberto, abaixo" } ]
}
```

## Um registro por negócio aberto (2.089: 1.589 Engaging e 500 Prospecting)

| Campo | Tipo | Significado |
|---|---|---|
| `id` | texto | `opportunity_id` |
| `stage` | `Engaging` ou `Prospecting` | etapa no CRM |
| `seller`, `manager`, `region` | texto | de `sales_teams.csv` (servem aos filtros) |
| `product` | texto | nome do catálogo (`GTXPro` do pipeline vira `GTX Pro`) |
| `account` | texto ou `null` | só para exibir; `null` em 1.425 dos 2.089 abertos. Nunca entra no score |
| `value` | número | preço de tabela do produto: é o único valor que uma linha aberta tem (`close_value` está vazio em 100% dos abertos; nos ganhos, `close_value` / preço tem mediana 1,00) |
| `engage_date`, `days_open` | data, inteiro, ou `null` | dias entre o engajamento e a data de referência. `null` em Prospecting |
| `deadline`, `days_to_deadline` | data, inteiro, ou `null` | fim do trimestre seguinte ao do engajamento; negativo se já passou |
| `chance` | 0 a 1 ou `null` | regra A: de negócios que chegaram abertos a esta idade, a parcela ganha nos 90 dias seguintes, sem contar nada depois do prazo. É um índice de ordenação, **não** uma probabilidade calibrada (ver "Limites") |
| `chance_in_30_days` | 0 a 1 ou `null` | a mesma conta se o negócio seguir aberto por mais 30 dias |
| `dead_reason` | `prazo`, `idade` ou `null` | por que o negócio está em `deixar ir`: o prazo venceu, ou ele está aberto há mais dias que o ganho mais demorado já visto (138) |
| `expected_value` | número ou `null` | `chance` x `value` |
| `group` | texto | `focar agora`, `manter aquecido`, `deixar ir` ou `sem data` |
| `rank`, `list_size` | inteiros | posição dentro da lista do próprio vendedor e tamanho dela |
| `factors` | lista | os fatores do negócio, cada um com a evidência (abaixo) |
| `play` | texto | o próximo passo, escolhido por regra (abaixo) |
| `flags` | lista de texto | `sem_conta` quando `account` é `null` |

### Ordem dentro da lista do vendedor

Primeiro o grupo (`focar agora`, `manter aquecido`, `sem data`, `deixar ir`), depois `expected_value` do maior para o menor, depois `value`, depois `id`. O vendedor é constante dentro da própria lista e por isso não é fator; `seller`, `manager` e `region` só filtram.

### Os grupos e seus limites (medidos em três cortes: 2017-07-01, 2017-08-16, 2017-10-02)

`deixar ir` exige evidência positiva de que o negócio não fecha mais; falta de evidência não basta. A primeira versão usava "chance abaixo de 5%" e errou nos cortes de junho, quando a tabela ainda era curta (114 ganhos em 372 negócios postos em `deixar ir`); foi trocada pela regra abaixo.

| Grupo | Regra | O que aconteceu com os negócios medidos (90 dias) |
|---|---|---|
| `focar agora` | `chance` >= 0,25 e `expected_value` >= 1.000 | 2.094 negócios, 769 ganhos (36,7%), 86,1% de todo o valor ganho |
| `manter aquecido` | vivo que não entra em foco | 2.921 negócios, 1.015 ganhos (34,7%), 13,9% do valor ganho: fecha em proporção parecida, mas vale pouco |
| `deixar ir` | o prazo venceu (`days_to_deadline` <= 0) ou `days_open` > 138 (o ganho mais demorado já visto) | 1.417 negócios, nenhum ganho, 1 perdido; 1.416 seguiam abertos no fim da janela. Em nove cortes: 0 ganhos em 3.192 |
| `sem data` | `stage` = Prospecting | nenhum corte mede: o negócio não tem data nenhuma. A tela diz isso e não promete nada |

Hoje (2017-12-31): 41 em `focar agora`, 74 em `manter aquecido`, 1.474 em `deixar ir`, 500 `sem data`.

### Fatores (`factors`), sempre os mesmos três, na ordem

Cada fator: `{"factor", "reading", "effect", "evidence"}`. `effect` é `a favor`, `contra` ou `neutro`. `reading` é uma frase curta montada por código; `evidence` traz os números que a sustentam.

1. `tempo`: `days_open` contra a curva. Evidência: `{"days_open", "chance", "longest_win_days": 138}`. Nenhum ganho da história levou mais de 138 dias.
2. `prazo`: `days_to_deadline`. Evidência: `{"deadline", "days_to_deadline", "closings_total": 6711, "closings_after_deadline": 1}`.
3. `valor`: `value` e `expected_value`. Evidência: `{"value", "expected_value", "focus_expected_value_min": 1000}`.

Em `sem data` a lista traz só `valor` e um fator `sem_data` com `effect` = `neutro`.

### Jogadas (`play`): a primeira condição verdadeira vale

| `play` | Condição | O que os dados sustentam |
|---|---|---|
| `qualificar` | `stage` = Prospecting | só que o negócio não tem data; nenhum desfecho medido |
| `encerrar_ou_requalificar` | `group` = `deixar ir` | nenhum ganho em 1.417 medidos |
| `confirmar_esta_semana` | vivo hoje e `chance_in_30_days` < 0,25 | **parcial**: no corte de meio de trimestre, 646 negócios, 323 ganhos, 68% deles nos primeiros 30 dias; nos dois cortes de início de trimestre, 265 negócios, 20 ganhos, nenhum nos primeiros 30 dias. Por isso a jogada é confirmar se o negócio está vivo, não "fechar já" |
| `priorizar` | `group` = `focar agora` | 36,7% de ganho e 86,1% do valor |
| `toque_leve` | o resto (`manter aquecido`) | 34,7% de ganho, 13,9% do valor |

Jogadas que os dados **não** sustentam, e que por isso não existem: qualquer uma que dependa de contato, reunião, decisor, concorrente ou desconto (não há registro de atividade nem histórico de etapas); jogadas por produto, setor, porte ou vendedor (taxas de ganho dentro do ruído: auditoria §10.4); jogadas por conta (campo vazio em 68,2% dos abertos e em nenhum fechado).

## Limites que quem consome precisa respeitar

- `chance` ordena, mas superestima: nos três cortes, a faixa prevista entre 40% e 55% teve 44,1%, 22,2% e 33,7% de ganho observado. A tela mostra o grupo e o que aconteceu com o grupo no teste, não uma porcentagem com cara de previsão.
- Campos que nunca entram no score: `close_date`, `close_value`, a etapa final, o tempo até fechar, `account` e tudo o que deriva da conta. `validate.py` prova isso com `assert`.
- O arquivo é o produto completo sem a camada de IA: a interface funciona só com ele.
