# Contrato da camada de IA: o arquivo de textos

Quem escreve: a camada de IA (`solution/ai/generate.py`, a construir). Quem lê: a interface. A camada de IA lê só `solution/out/score.json` (ver `contrato-score.md`). **A interface funciona com este arquivo ausente**: nesse caso mostra as frases de regra (`factors[].reading`) que já vêm no score.

Princípio: a IA redige; não decide nem calcula. A ordem, o grupo e a jogada vêm do score. Todo número e todo nome num texto é um marcador que o código preenche a partir dos fatos.

## Arquivo

`solution/out/textos.json`, UTF-8, gerado e guardado no repositório (quem avalia não precisa de chave nem de conta).

```json
{
  "meta": {
    "score_reference_date": "2017-12-31",
    "command": "claude -p --model <nome> --setting-sources \"\" --tools \"\" --no-session-persistence --json-schema <schema>",
    "prompt_file": "solution/ai/prompt.md",
    "prompt_sha256": "<hash do prompt usado>"
  },
  "texts": [
    {
      "id": "deal:FZWU2I30:explanation",
      "kind": "deal_explanation",
      "target": {"deal_id": "FZWU2I30"},
      "template": "{product} para {account} está em {group}: aberto há {days_open} dias, dentro do prazo ({deadline}).",
      "facts": {"product": "GTX Plus Pro", "account": "The New York Inquirer", "group": "focar agora",
                "days_open": 21, "deadline": "2018-03-31"},
      "provenance": {"model": "<nome exato do modelo>", "generated_on": "<data do comando date>",
                     "prompt_sha256": "<hash>", "batch": 1}
    }
  ]
}
```

O `template` acima é só ilustração do formato, escrito à mão; nenhum texto foi gerado nesta etapa.

## Tipos de texto e os fatos que cada um pode citar

| `kind` | Alvo | Fatos permitidos (chaves de `facts`) | Dor de `produto.md` |
|---|---|---|---|
| `deal_explanation` | um negócio em `focar agora` ou com a jogada `confirmar_esta_semana` | `seller`, `product`, `account` (se houver), `value`, `group`, `play`, `rank`, `list_size`, `engage_date`, `days_open`, `deadline`, `days_to_deadline`, `reference_date`, `window_days`, `longest_win_days`, `closings_total`, `closings_after_deadline`, `group_test_deals`, `group_test_won`, `group_test_won_value` | explicar a posição |
| `deal_next_step` | o mesmo negócio | os mesmos, mais o rótulo da jogada | próximo passo |
| `seller_briefing` | um vendedor | `seller`, `reference_date`, contagem e valor por grupo, os cinco primeiros (os fatos de cada um, com sufixo `_1` a `_5`), quantos estão em `confirmar_esta_semana`, quantos em `deixar ir` e o valor deles | briefing de segunda |
| `manager_view` | um gestor | `manager`, por vendedor: contagem e valor por grupo | onde orientar |

`docs/fatos-exemplo.json` traz, para cinco negócios reais, os fatos exatos de `deal_explanation` (escrito por `solution/make_example_facts.py`).

O texto não afirma nenhum julgamento além do grupo e da jogada, que entram como marcadores (`{group}`, `{play}`). Nada de "excelente oportunidade", "alta probabilidade", "cliente estratégico".

## Marcadores e a conferência

- Marcador: `{chave}`, onde `chave` existe em `facts` daquele texto. O código formata por tipo (dinheiro, data por extenso, inteiro, nome) e preenche. O modelo nunca escreve um número nem um nome.
- A conferência (`solution/ai/check.py`, roda na geração e nos testes) reprova o texto quando:
  1. um marcador não resolve em `facts`;
  2. sobra qualquer dígito fora de um marcador;
  3. aparece, fora de um marcador, o nome de um vendedor, gestor, conta ou produto do dataset;
  4. um fato usado não está na lista permitida do `kind`, ou seu valor difere do que está em `score.json` para aquele alvo.
- Texto reprovado não entra no arquivo: a interface cai na frase de regra. A geração imprime quantos foram reprovados e por quê.
- A pesquisa (`pesquisa.md`, seção 2) sustenta essa escolha: saída estruturada garante a forma, não a verdade, e citação de fontes falha em boa parte das frases; por isso o número não passa pelo modelo.

## Geração, sem chave de API

- Um script guardado no repositório chama o CLI do Claude Code sem interface, com o modelo nomeado, `--setting-sources ""`, `--tools ""` e `--json-schema`, vários negócios por chamada. O orquestrador mediu essa forma neste laptop em 2026-11-10: cinco itens inventados voltaram como saída estruturada válida em 10 segundos (medição dele, não refeita nesta etapa).
- Entrada de cada chamada: o prompt fixo (`solution/ai/prompt.md`) e uma lista JSON de `{id, kind, facts}`. Saída exigida pelo schema: lista de `{id, template}`.
- Procedência por texto: modelo, data (do `date`), hash do prompt, número do lote; os fatos que entraram ficam no próprio registro.
- Com o Claude Code instalado e logado, um comando regenera tudo (`python solution/ai/generate.py`). Nenhuma chave de API é usada nem aparece em arquivo.
