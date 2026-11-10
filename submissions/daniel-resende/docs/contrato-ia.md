# Contrato da camada de IA: o arquivo de textos

Segunda versão, para a forma que o Daniel decidiu (vivos, fila, limpar). Quem escreve: `solution/ai/`. Quem lê: a interface. A camada de IA lê só os arquivos do score (`contrato-score.md`), da segunda padrão (2018-01-01).

**A interface funciona com o arquivo ausente**: ela o busca ao carregar e, se não vier, mostra as frases de regra que já estão no score. A IA redige; não decide nem calcula. O bloco, a ordem e o próximo passo vêm do score.

## Arquivo: `solution/ai/textos.json` (guardado no git, com a procedência)

```json
{
  "meta": {"monday": "2018-01-01", "score_file": "score-2018-01-01.json",
           "prompt_file": "solution/ai/prompt.md", "prompt_sha256": "<hash>",
           "command": "claude -p --setting-sources \"\" --tools \"\" --no-session-persistence --model <nome> --json-schema <schema> --output-format json"},
  "texts": [
    {"id": "deal:FZWU2I30", "kind": "deal",
     "target": {"deal_id": "FZWU2I30", "seller": "Zane Levy"},
     "parts": {"reason":    {"template": "...{days_open}...", "text": "...21..."},
               "next_step": {"template": "...", "text": "..."}},
     "facts": {"product": "GTX Plus Pro", "days_open": 21},
     "provenance": {"model": "<nome exato>", "generated_on": "<data do comando date>",
                    "prompt_sha256": "<hash>", "batch": 1}}
  ]
}
```

`template` é o que o modelo escreveu, com marcadores; `text` é o mesmo texto com os marcadores preenchidos pelo código. A interface mostra `text`.

## Três tipos de texto

| `kind` | `id` | `target` | `parts` | Dor de `produto.md` |
|---|---|---|---|---|
| `deal` | `deal:<id>` | `deal_id`, `seller` | `reason` (por que este negócio está onde está, uma ou duas frases) e `next_step` (o próximo passo, uma frase) | explicar e indicar o passo. Um por negócio **vivo** |
| `briefing` | `briefing:<vendedor>` | `seller` | `body` (o briefing de segunda, três a cinco frases, montado dos três blocos) | o briefing. Um por vendedor que tenha algum negócio |
| `manager` | `manager:<gestor>` | `manager` | `body` (o resumo do gestor, três a cinco frases, só fatos) | a saúde do pipeline. Um por gestor |

## Os fatos que cada texto pode citar (chaves de `facts`)

Uma chave só existe quando o fato existe: sem conta, não há `account`; sem tabela na data, não há as chaves `band_*`.

As contagens com substantivo vêm prontas, como frases montadas pelo código com o singular, o plural e o zero certos (`*_phrase`): o modelo não flexiona nada. A frase da tabela do tempo vem inteira do score (`time_sentence`) e o modelo a coloca sem mudar uma palavra, ou a deixa de fora.

- `deal`: `seller`, `product`, `account`, `value`, `engage_date`, `days_open`, `days_open_phrase`, `days_left`, `days_left_phrase`, `window_end`, `block` (sempre `vivo`), `play_label` (o rótulo do próximo passo, do score), `cooling_label` (`esfriando`, só se `cooling`), `rank`, `alive_count`, `longest_win_days`, `time_sentence`, `monday`.
- `briefing`: `seller`, `monday`, `alive`, `alive_value`, `cooling`, `queue`, `queue_value`, `clean`, `clean_value`, `longest_win_days`, `evidence_deals`, `evidence_won`, `evidence_phrase`, `alive_phrase`, `queue_phrase`, `clean_phrase`, `cooling_phrase`, e para os até três primeiros vivos `product_1`, `account_1`, `value_1`, `days_left_1`, `days_left_phrase_1` (e `_2`, `_3`).
- `manager`: `manager`, `region`, `monday`, `sellers`, `sellers_without_alive`, `without_alive_phrase`, `names_without_alive` (lista), `alive`, `alive_value`, `cooling`, `queue`, `queue_value`, `clean`, `clean_value`, `alive_phrase`, `queue_phrase`, `clean_phrase`, `cooling_phrase`, `evidence_deals`, `evidence_won`, `evidence_phrase`.

`docs/fatos-exemplo.json` traz os fatos exatos de cinco alvos reais (três negócios vivos, um deles esfriando e um sem conta; um vendedor; um gestor), escritos por `python solution/ai/facts.py --examples`.

## Marcadores e a conferência (`solution/ai/check.py`, um comando)

- Marcador: `{chave}`, com `chave` em `facts` daquele texto. O código formata pelo tipo (dinheiro "US$ 5.482", data "31/03/2018", inteiro, lista "A, B e C") e preenche. O modelo nunca escreve número nem nome.
- O único julgamento permitido é o que vem nos fatos: o bloco, o rótulo do próximo passo e a marca "esfriando", sempre por marcador.
- A conferência reprova um texto quando:
  1. um marcador não existe em `facts`;
  2. sobra um dígito fora de um marcador;
  3. aparece fora de marcador o nome de um vendedor, gestor, conta ou produto do dataset;
  4. aparece um julgamento que não está nos fatos: porcentagem, "chance", "probabilidade", "provável", "garantido", "promissor", "quente", "excelente" e afins (lista no código, com o limite dito: uma lista de palavras não pega tudo);
  5. `text` não é o `template` preenchido com `facts`, ou falta procedência (inclusive se o `prompt.md` mudou depois da geração);
  6. um fato difere do que está no arquivo do score para aquele alvo;
  7. português quebrado que já apareceu: "tem nenhum", ou a mesma sequência de três palavras digitada duas vezes no modelo do texto.
- Uma frase pronta que começa uma frase ganha a maiúscula no preenchimento; a conferência usa o mesmo preenchedor.
- A procedência traz também `model_requested` (o nome pedido ao CLI); `model` é o que o envelope da resposta registrou.
- Texto reprovado não entra no arquivo. A geração imprime quantos foram reprovados e por quê.
- Por que assim (`pesquisa.md`, seção 2): saída estruturada garante a forma, não a verdade; por isso o número não passa pelo modelo.

## Geração, sem chave de API

`python solution/ai/generate.py` chama o CLI do Claude Code sem interface, de um diretório vazio de nome neutro, na forma medida neste laptop: `claude -p --setting-sources "" --tools "" --no-session-persistence --model <nome> --json-schema <schema> --output-format json`, com vários itens por chamada; a resposta vem no campo `structured_output` do envelope. Entrada de cada chamada: o prompt fixo (`solution/ai/prompt.md`) e uma lista de `{id, kind, facts}`. Saída exigida: lista de `{id, parts}` com os `template`. Cinco itens primeiro, lidos pelo construtor; depois todos. Se o plano limitar o uso ou atrasar, a geração para e o produto sai sem os textos.
