# Contrato do score: os arquivos que o núcleo emite

Segunda versão, reescrita a partir do `PRODUTO.md` que o Daniel decidiu depois da auditoria. A primeira (focar agora, manter aquecido, deixar ir) está no histórico do git.

Quem escreve: `solution/build.py`. Quem lê: a interface (`solution/web/`) e a camada de IA (`solution/ai/`). Ninguém lê o código do outro; `solution/check_contract.py` sai com 0 só se todo arquivo emitido obedece a este texto.

## A afirmação que o produto sustenta

Um negócio em andamento está **vivo** ou é **para limpar**. A fronteira é a janela da regra congelada (`solution/validate.py`, função `is_dead`, intocada: o arquivo tem sha256 `336760fdcc511cde2ad5d28e9437dd0b061a222b18f2f5f03e2a38164abca212`):

- nenhum negócio foi ganho depois de 138 dias aberto (o ganho mais demorado conhecido na data);
- os fechamentos acontecem até o fim do trimestre seguinte ao do engajamento (o prazo).

Passou de um dos dois, é para limpar. Evidência: nenhum ganho em 717 negócios distintos postos fora da janela nos doze cortes medidos (`docs/confirmacao-saida.txt`). A ordem entre os vivos é secundária e não foi confirmada em datas novas.

## Datas

Um arquivo por segunda-feira. A segunda padrão é **2018-01-01**, com os dados fechados no domingo 2017-12-31. Segundas do passado, fixas: 2017-06-05, 2017-07-03, 2017-08-07, 2017-09-04 e 2017-10-02 (cada uma tem 90 dias de dados depois dela).

Como uma segunda-feira se liga à regra congelada, sem tocar nela:

- **corte = a segunda menos um dia** (o fechamento dos dados, um domingo). O núcleo chama `validate.world_at(deals, corte)`, que apaga tudo o que aconteceu depois, e pontua só com isso.
- Em `validate.py` um negócio está fora da janela quando `(prazo - corte).days <= 0`. Com o corte no domingo, o negócio está vivo exatamente quando o prazo é a própria segunda ou depois: **o dia do prazo conta como vivo**, como o Daniel decidiu. Nenhuma das seis datas é o último dia de um trimestre.
- **As idades são contadas na data de fechamento dos dados** (o corte), não na segunda.
- `days_left` (a contagem regressiva) = o menor entre `138 - days_open` e `(prazo - segunda).days`. Zero quer dizer "hoje é o último dia". É sempre >= 0 num negócio vivo.

## Arquivos em `solution/out/` (gerados, nunca vão para o git)

### `index.json`

```json
{
  "written_by": "solution/build.py",
  "default_monday": "2018-01-01",
  "default_seller": "<o vendedor com mais vivos na segunda padrão>",
  "mondays": [
    {"monday": "2018-01-01", "data_closed": "2017-12-31", "file": "score-2018-01-01.json", "past": false},
    {"monday": "2017-10-02", "data_closed": "2017-10-01", "file": "score-2017-10-02.json", "past": true}
  ],
  "sellers": [{"seller": "...", "manager": "...", "region": "..."}],
  "evidence": {"cuts": 12, "distinct_deals_past_window": 717, "won_after": 0, "lost_after": 1,
               "still_open_at_data_end": 716, "source": "docs/confirmacao-saida.txt"},
  "value_note": {"list_prices": 7, "closed_without_value_on_open_rows": true}
}
```

`sellers` traz os 35 de `sales_teams.csv`, em ordem alfabética. `mondays` vem da mais recente para a mais antiga.

### `score-AAAA-MM-DD.json`

```json
{
  "meta": {
    "monday": "2018-01-01", "data_closed": "2017-12-31", "past": false,
    "window": {"longest_win_days": 138, "deadline_applied": true,
               "closings_known": 6711, "closings_after_deadline": 1},
    "cooling_after_days": 90,
    "time_table": {
      "exists": true, "counted_on": "2017-12-31", "settled_until": "2017-08-14", "deals": 4767,
      "rows": [{"reached_days": 0, "deals": 4767, "won_after": 2256, "lost_after": 1433,
                "never_closed": 1078, "won_per_100": 47}]
    },
    "outcomes_until": null
  },
  "sellers": [
    {"seller": "...", "manager": "...", "region": "...",
     "headline": {"alive": 10, "alive_value": 15300.0, "cooling": 0,
                  "queue": 0, "queue_value": 0.0, "clean": 78, "clean_value": 178048.0},
     "alive": [ {"...": "negócio"} ], "queue": [], "clean": [],
     "after": null}
  ],
  "team": {
    "by_seller":  [{"seller": "...", "manager": "...", "region": "...", "sellers": 1, "sellers_without_alive": 0,
                    "alive": 0, "alive_value": 0.0, "cooling": 0, "queue": 0, "queue_value": 0.0,
                    "clean": 0, "clean_value": 0.0}],
    "by_manager": [{"manager": "...", "region": "...", "sellers": 6, "sellers_without_alive": 2, "...": "os mesmos sete números"}],
    "by_region":  [{"region": "...", "sellers": 12, "sellers_without_alive": 4, "...": "os mesmos sete números"}],
    "total": {"sellers": 35, "sellers_without_alive": 18, "...": "os mesmos sete números"}
  }
}
```

- `sellers` traz os 35, em ordem alfabética, também os que não têm negócio nenhum (listas vazias).
- `time_table`: quem chegou aberto a cada idade (0, 30, 60, 90, 120, 138 dias) e o que aconteceu depois, **como se sabia no corte**. Só entram negócios engajados desde o primeiro fechamento registrado e há mais dias que o ganho mais demorado (`settled_until`), escolhidos pela data de engajamento e nunca pelo desfecho. Quando nenhum negócio teve esse tempo, `exists` é `false` e `rows` é `[]`. Os números da data de referência conferem com `docs/confirmacao-saida.txt` (M3, tabela b).
- Na segunda padrão nenhum vendedor tem os três blocos: a regional Central tem toda a fila (500) e nenhum vivo; East e West têm os vivos (45 e 70) e nenhuma fila. A tela precisa estar certa para os dois casos e para quem não tem nada.
- `team`: os agregados do gestor, só fatos. Numa segunda do passado os números de fila são 0 em `team` (a fila não existe no passado). "Os sete números" são `alive`, `alive_value`, `cooling`, `queue`, `queue_value`, `clean`, `clean_value`. `sellers_without_alive` conta vendedores sem nenhum vivo.

### Um negócio

| Campo | Tipo | Significado |
|---|---|---|
| `id` | texto | `opportunity_id` |
| `block` | `vivo`, `fila` ou `limpar` | o bloco. `fila` = etapa Prospecting (sem data nenhuma); `limpar` = fora da janela; `vivo` = o resto |
| `rank` | inteiro | posição dentro do bloco, na lista do vendedor, a partir de 1 |
| `product` | texto | nome do catálogo (`GTXPro` do pipeline vira `GTX Pro`) |
| `account` | texto ou `null` | só para exibir. `null` em 1.425 dos 2.089 abertos: nenhuma tela e nenhum texto pode supor que existe. É o único campo de `validate.LEAK_FIELDS` que aparece num negócio, e nunca entra na regra |
| `value` | número | **o preço de tabela do produto**: um negócio aberto não tem valor de fechamento (`close_value` vazio em 100% dos abertos). Na tela: "valor de tabela" |
| `engage_date` | data ou `null` | `null` na fila |
| `days_open` | inteiro ou `null` | dias entre o engajamento e o fechamento dos dados |
| `deadline` | data ou `null` | fim do trimestre seguinte ao do engajamento |
| `days_left` | inteiro ou `null` | a contagem regressiva (definição acima). Só nos vivos |
| `window_end` | data ou `null` | a segunda mais `days_left`: o último dia do negócio dentro da janela. Só nos vivos |
| `cooling` | booleano | `true` num vivo com `days_open` > 90: aparece como "esfriando". **Informa, não reordena** |
| `time_sentence` | texto ou `null` | a frase da tabela para a faixa de idade do negócio (a maior idade da tabela que ele já alcançou), montada pelo código: "Cerca de 39 em cada 100 negócios que chegaram abertos aos 60 dias foram ganhos depois (conta de 31/12/2017)." Na faixa de 0 dias: "Cerca de 47 em cada 100 negócios foram ganhos depois de engajados (conta de 31/12/2017)." Sem tabela na data: "Sem histórico suficiente nesta data." Só nos vivos; `null` na fila e em limpar |
| `clean_fact` | `prazo`, `idade` ou `null` | só em `limpar`: qual lado da janela o negócio passou. É um fato de calendário, não o motivo de ele estar parado, que os dados não dizem |
| `play` | texto | o próximo passo, por regra (abaixo) |
| `flags` | lista | `sem_conta` quando `account` é `null` |
| `after` | objeto ou `null` | só nas segundas do passado e nunca na fila: `{"result": "ganho" \| "perdido" \| "aberto", "close_date", "close_value", "days_after"}`, com o que aconteceu até o fim dos dados (2017-12-31); `days_after` conta a partir do corte (o fechamento dos dados). `null` na segunda padrão |

Numa segunda do passado, `sellers[].after` resume o que aconteceu: `{"alive_won", "alive_lost", "alive_open", "alive_won_value", "clean_won", "clean_lost", "clean_open"}`, e `meta.outcomes_until` é `2017-12-31`.

**A fila no passado não existe.** O CRM não guarda a data em que um negócio entrou em Prospecting, então numa segunda do passado `queue` é `[]`, `headline.queue` é `null` e a tela diz que a fila não pode ser reconstruída.

### Ordem

- `alive`: `value` do maior para o menor; empate: mais `days_left` primeiro; depois `id`. A contagem regressiva e a marca "esfriando" nunca reordenam. Com sete preços de tabela, ordenar por valor é quase ordenar por produto, e o desempate decide muitas vezes: a tela e o README dizem isso.
- `queue`: `value` do maior para o menor, depois `id`. Nada mais nos dados ordena a fila, e a tela diz isso.
- `clean`: `value` do maior para o menor, depois `days_open` do maior para o menor, depois `id`.

### Próximo passo (`play`), por regra

| `play` | Condição | Na tela |
|---|---|---|
| `trabalhar` | `block` = `vivo` e não `cooling` | "Trabalhar esta semana" |
| `confirmar` | `block` = `vivo` e `cooling` | "Confirmar esta semana se segue de pé" |
| `engajar` | `block` = `fila` | "Engajar e registrar a data" |
| `encerrar` | `block` = `limpar` | "Encerrar no CRM e tirar da segunda-feira" |

Jogadas que os dados não sustentam e que por isso não existem: as que dependem de contato, reunião, decisor, concorrente ou desconto (não há registro de atividade); as por produto, setor, porte ou vendedor (ruído, `docs/auditoria-saida.txt` §10.4).

## O que nunca aparece

- Nenhuma porcentagem por negócio, e nada que sugira que um negócio vivo fecha mais que outro. A frase da tabela fala de uma faixa de idade, com "cerca de" e a data da conta.
- Campos que nunca entram na regra: `close_date`, `close_value`, a etapa final, o tempo até fechar, `account` e o que deriva da conta. Numa segunda do passado, `after` é o único lugar em que o futuro aparece, e ele é lido depois de os blocos estarem decididos.
- Os arquivos são o produto completo sem a camada de IA.
