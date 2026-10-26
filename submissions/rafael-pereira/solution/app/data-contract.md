# Contrato do `window.LEAD_DATA` (`app/data.js`)

Este arquivo é a especificação entre o motor Python (`python -m scorer.build`, que **gera** o `data.js`) e a interface (`index.html` + `app.js`, que **lê** o `data.js`). A interface foi escrita contra este contrato, usando uma fixture de números falsos (que nunca entra na submissão). O `build.py` tem de produzir exatamente isto; se o motor precisar mudar algo, mude **este arquivo junto** e avise quem cuida da interface.

## 1. Regras gerais

- Arquivo: `app/data.js`, UTF-8, uma única atribuição: `window.LEAD_DATA = {...};` (JSON válido dentro das chaves, `json.dumps(ensure_ascii=False, separators=(",", ":"))`).
- **Nada de `NaN`, `Infinity` ou `NaT`**: ausência é sempre `null`.
- **Inteiros são inteiros** (`n`, `price`, `age`, `score`, dias). Valores monetários em dólares, sem centavos arredondados à mão: a interface arredonda para exibir ("US$ 4.821").
- **Frações são frações** (0 a 1): `p`, `p_fresh`, `pct_ganhos`, AUC e capturas. A interface multiplica por 100 ao exibir.
- **Datas** são strings ISO `AAAA-MM-DD`. A interface converte para `dd/mm/aaaa`.
- **Nenhum número é escrito à mão na interface.** Qualquer texto da tela que contenha número (limiares, datas, contagens de teste, frases de explicação) vem daqui ou é calculado aqui pelo JS a partir daqui. Strings já formatadas (`label`, `how_it_works`, `why`, `headline`) usam o formato PT-BR: "1.291", "63,2%", "US$ 4.821", "31/12/2017".
- Chaves extras são ignoradas pela interface (pode acrescentar campos de diagnóstico sem quebrar nada). Chaves obrigatórias ausentes quebram a tela de propósito.
- Tamanho-alvo: menos de 4 MB.
- Determinismo: sem timestamp; dois builds seguidos geram bytes idênticos.
- **O `data.js` não é commitado em fixture.** Só o `build.py` o gera, a partir dos dados reais.

## 2. Estrutura de cima

```jsonc
window.LEAD_DATA = {
  "meta":      { ... },        // seção 3
  "people":    { ... },        // seção 4
  "snapshots": [ ... ],        // seção 5 (>= 1; o primeiro é o "hoje")
  "backtest":  { ... }         // seção 7
};
```

## 3. `meta`

| Campo | Tipo | Nulo? | Semântica |
|---|---|---|---|
| `reference_date` | string ISO | não | "Hoje" (parâmetro `--reference-date`). Também é a data-limite dos desfechos mostrados no modo teste ("o que aconteceu até 31/12/2017"). |
| `horizon_days` | int | não | Horizonte da chance de ganho (dias). Aparece no texto "chance de ganho nos próximos N dias". |
| `generated_by` | string | não | Comando que gerou o arquivo, p. ex. `python -m scorer.build --reference-date 2017-12-31`. Mostrado no rodapé. |

## 4. `people`

| Campo | Tipo | Semântica |
|---|---|---|
| `agents[]` | lista | **Todos** os 35 vendedores do cadastro, inclusive os 5 sem nenhum deal. Ordem livre (a interface ordena por nome, sem acento). |
| `agents[].name` | string | Nome como está no dataset. É a chave usada em `deals[].agent`. |
| `agents[].manager` | string | Nome do manager. |
| `agents[].region` | string | Escritório regional do time. |
| `agents[].has_deals` | bool | `false` só para quem não aparece em nenhum estágio de `sales_pipeline` (cadastro sem pipeline). Esses vendedores aparecem no seletor com o sufixo "(sem deals no CRM)" e recebem um estado vazio explicativo. |
| `agents[].n_open` | int | Deals abertos (Engaging + Prospecting) na **data de referência**. `has_deals=true` e `n_open=0` = só deals fechados. A interface não lê este campo: o aviso "(sem deals abertos)" sai da contagem de `deals` do snapshot ativo. Ele existe para conferência (`check_app.py` exige `n_open` = deals do snapshot "hoje" por vendedor). |
| `managers[]` | lista de `{name, region}` | Um manager pertence a uma região. Base da cascata dos filtros. |
| `regions[]` | lista de strings | Regiões distintas. |

Invariante: todo `deals[].agent` existe em `agents[].name`; todo `agents[].manager` existe em `managers[].name`.

## 5. `snapshots[]`

Uma "foto" da carteira numa data. **Ordem da lista:** primeiro o snapshot `"hoje"` (a interface abre nele), depois os de teste, do mais recente para o mais antigo.

| Campo | Tipo | Nulo? | Semântica |
|---|---|---|---|
| `date` | string ISO | não | Data da foto. Para `"hoje"` é igual a `meta.reference_date`. Também é a chave do hash (`#modo=2017-09-30`) e casa com `backtest.rows[].cut`. |
| `mode` | `"hoje"` \| `"teste"` | não | `"teste"` = reconstruído no passado, com desfecho real em `deals[].outcome`. |
| `label` | string | não | Texto do seletor de modo: `"Hoje — 31/12/2017"`, `"Teste: 30/09/2017"`. |
| `model` | objeto | não | Parâmetros do modelo **ajustado só com dados até `date`** (curva v2, correção após revisão do Rafael): `knot_days` (int, último dia do Foque: a chance ainda é pelo menos metade da de um deal novo), `p_fresh` (fração, chance de um deal novo), `limpe_after_days` (int, último dia do Reative: depois disso o deal é Limpe), `limpe_rule` (`"chance"` se o Limpe começa porque a chance cai abaixo de `limpe_min_chance`, `"ciclo"` se pelo maior ciclo ganho), `limpe_min_chance` (fração, 0,02), `max_won_cycle_days` (int, maior ciclo já ganho até `date`). Chaves extras de diagnóstico: `version`, `phase`, `halving_days` e `slope_per_30d` (só na v1, nulos na v2), `base_rate`, `train_rows`, `train_snapshots`, `as_of_date`. Usados nas linhas-instrução das abas. |
| `how_it_works` | lista de **5** strings | não | As 5 linhas do `<details>` "Como funciona o score", já com números (vêm de `explain.how_it_works`). Exatamente 5. |
| `summary` | objeto | não | Para as 4 chaves `Foque`, `Reative`, `Limpe`, `Qualifique`: `{n:int, valor_tabela:number, valor_esperado:number\|null}`. `valor_tabela` = soma de `price`; `valor_esperado` = soma de `ev` (`null` em Qualifique). **Em snapshot de teste, `Qualifique` = `{n:0, valor_tabela:0, valor_esperado:null}`.** |
| `outcome_summary` | objeto | **só em `mode="teste"`** (omitir em `"hoje"`) | Para `Foque`, `Reative` e `Limpe` (sem Qualifique): `{n:int, pct_ganhos:fração, receita_ganha:number}`. `pct_ganhos` = ganhos até `meta.reference_date` ÷ `n` (quem ainda está aberto conta como não ganho); `receita_ganha` = soma de `close_value` dos ganhos. É o resumo do snapshot inteiro, **sem filtros**. A interface não o exibe direto: recalcula `n`, ganhos e receita a partir de `deals` filtrados (com um vendedor escolhido, só contagens, sem porcentagem: sem taxa de vitória por vendedor) e a checagem Playwright confere que, sem filtro, o recálculo é igual a este resumo. |
| `deals` | lista | não | Ver seção 6. **Já vem na ordem de exibição; a interface não reordena** (só filtra, preservando a ordem). |

Invariantes (o `build.py` deve garantir com `assert`):

- `summary[cat].n` = número de `deals` com `cat` igual; `valor_tabela` = soma de `price` dessas linhas; `valor_esperado` = soma de `ev` (arredondada só na exibição).
- A interface mostra, sem filtro, exatamente `summary`. A checagem Playwright compara as contagens das abas com `summary`, e `summary` de hoje com `backtest_metrics.json["hoje"]`.
- Em `mode="teste"`: `outcome_summary[cat].n` = `summary[cat].n`; todos os `deals` têm `outcome` (nenhum `null`); nenhum deal `Qualifique`.
- Em `mode="hoje"`: todos os `outcome` são `null`.

### Ordem de exibição dos `deals` (regra do `order_for_list` do plano)

Os deals vêm agrupados por categoria na ordem `Foque`, `Reative`, `Limpe`, `Qualifique`, e **dentro de cada categoria** já na ordem final:

- Foque e Reative: valor esperado decrescente (na v2 a chance cai com a idade, então a ordem não é só o preço) → menos dias até o próximo limiar (`days_to_knot` no Foque, `days_to_limpe` no Reative) → `id`.
- Limpe: `price` decrescente → `age` decrescente.
- Qualifique: `price` decrescente.

Como a interface filtra sem reordenar, a lista filtrada de um vendedor/manager/região é uma subsequência da lista global e mantém essa ordem.

## 6. `deals[]` (um deal de um snapshot)

| Campo | Tipo | Nulo? | Semântica |
|---|---|---|---|
| `id` | string | não | `opportunity_id`. Único dentro do snapshot. |
| `agent` | string | não | Nome do vendedor (casa com `people.agents[].name`). Só contexto, nunca fator de score. |
| `manager` | string | não | Manager do vendedor. |
| `region` | string | não | Região do time. |
| `account` | string | **sim** | Conta. `null` quando o CRM não informa (1.425 deals, todos abertos): a interface escreve "Conta não informada". |
| `product` | string | não | Já normalizado ("GTX Pro", não "GTXPro"). |
| `price` | number | não | Preço de tabela (`sales_price`). **Nunca** `close_value`. |
| `engage_date` | string ISO | **sim** | `null` em Prospecting. |
| `age` | int | **sim** | Dias entre `engage_date` e `snapshot.date`. `null` em Prospecting. |
| `p` | fração | **sim** | Chance de ganho nos próximos `horizon_days` dias. `null` em Qualifique. |
| `ev` | number | **sim** | Valor esperado = `p × price`. `null` em Qualifique. |
| `score` | int 0–100 | **sim** | Score. `null` em Qualifique (a interface mostra "Sem score"). |
| `cat` | string | não | `"Foque"` \| `"Reative"` \| `"Limpe"` \| `"Qualifique"`. |
| `why` | lista de 2 a 4 strings | não | Frases curtas em PT-BR, sem jargão, na ordem em que devem ser lidas. **A 1ª frase aparece sozinha no card** (então precisa fazer sentido sozinha); todas aparecem ao expandir. Se `account` for `null`, uma das frases avisa "Conta não informada no CRM…". |
| `days_to_knot` | int | **sim** | Só em Foque: dias até o fim do Foque (`knot_days - age`, >= 0). `null` nas outras. |
| `days_to_limpe` | int | **sim** | Em Foque e Reative: dias até virar Limpe (`limpe_after_days - age`, >= 0). `null` em Limpe e Qualifique. |
| `outcome` | objeto \| `null` | **sim** | `null` no snapshot `"hoje"`. No de teste: `{status, close_date, close_value}` com `status` = `"Ganho"` (`close_date` e `close_value` preenchidos), `"Perdido"` (`close_date` preenchida, `close_value` pode ser `null` ou `0`), `"Aberto"` (ainda aberto em `meta.reference_date`; `close_date` e `close_value` = `null`). Só entram fechamentos até `meta.reference_date`. |

## 7. `backtest` (painel "Teste no passado")

| Campo | Tipo | Nulo? | Semântica |
|---|---|---|---|
| `headline` | string | não | Frase pronta (uma ou duas sentenças): "Testado em N datas passadas: o top 20% do score capturou X% da receita ganha depois, contra Y% ordenando por valor e Z% pelos mais recentes." Números da média dos cortes. |
| `criterion_text` | string | **sim** | Critério pré-registrado e se passou, em uma frase ("Critério fixado antes do código: ... Resultado: PASSOU."). `null` se não houver. |
| `notes` | lista de strings | não (pode ser `[]`) | Ressalvas honestas mostradas abaixo das tabelas (p. ex. "A recência ganha em AUC nos cortes de fim de trimestre."). |
| `metrics` | lista de `{key, label, kind}` | não | As tabelas do painel, na ordem de exibição: a **1ª é a métrica primária**. `key` é um campo de `rows[]` (`"receita_top20"`, `"ganhos_top20"`, `"auc"`); `label` é o título da tabela, já com números e unidades (ex.: `"Receita ganha capturada pelo top 20% (métrica principal)"`, `"AUC (separa ganhos de perdas; 0,5 = sorteio)"`); `kind` é `"pct"` (fração mostrada como 61,0%) ou `"dec"` (fração mostrada com 2 casas, 0,66). Assim nenhum "20%" fica escrito na interface. |
| `rows` | lista | não | Formato longo: **uma linha por (corte, método)**, na ordem de exibição. Veja abaixo. |

`rows[]`:

| Campo | Tipo | Nulo? | Semântica |
|---|---|---|---|
| `cut` | string | não | Data ISO do corte (`"2017-06-30"`) ou `"media"` para a média dos cortes. A interface agrupa por `cut` na ordem em que aparece e destaca o corte do snapshot ativo (`cut` = `snapshot.date`). |
| `cut_label` | string | não | `"30/06/2017"` ou `"Média dos 4 cortes"`. |
| `method` | string | não | Chave: `"score"` (v2), `"score_v1"` (curva antiga, para comparação), `"valor"`, `"recencia"`, `"aleatorio"`. A interface agrupa as colunas por `method` na ordem em que aparecem no 1º corte. |
| `method_label` | string | não | `"Score v2 (valor esperado, curva por faixas)"`, `"Score v1 (platô, antes da correção)"`, `"Ordenar por valor"`, `"Mais recentes primeiro"`, `"Aleatório (média de sorteios)"`. |
| `auc` | fração | sim | AUC do método no corte. |
| `ganhos_top20` | fração | sim | Fração dos ganhos capturada pelo top 20% do método. |
| `receita_top20` | fração | sim | Fração da receita ganha capturada pelo top 20% (**métrica primária**). |

A interface desenha três tabelas (receita no top 20%, ganhos no top 20%, AUC), cortes nas linhas e métodos nas colunas. Linhas de um mesmo corte devem trazer os mesmos 5 métodos.

## 8. Como a interface usa cada parte (para quem for mudar o build)

- `snapshots[].label` -> seletor de modo; `mode` -> liga a faixa "Modo teste", os selos de desfecho e a indisponibilidade da aba Qualifique.
- `summary` -> KPIs/abas sem filtro; com filtro, a interface recalcula as contagens e os valores a partir de `deals`.
- `deals[].outcome` -> os três blocos `backtest-summary-<Cat>`, recalculados com os filtros: `data-n`, `data-won`, `data-revenue` e `data-pct` (pontos percentuais com uma casa, ex. `"49.3"`; ausente quando há vendedor escolhido ou a lista está vazia).
- `people.agents` -> seletor "Quem é você?" (agrupado por manager), "Carteira do time" e estado vazio.
- `how_it_works` -> `<details data-testid="how-it-works">`, uma `<li>` por linha.
- `backtest` -> `<details data-testid="backtest-panel">`.
- Estado da tela no `location.hash` (`URLSearchParams`): `perfil` (`vendedor`|`manager`|`revops`; sem ele abre a tela de entrada "Quem é você?"), `nome` (o vendedor ou o manager do perfil), `ver` e `pauta` (manager: carteira de um vendedor do time em modo leitura e pauta do 1:1 aberta), `ordem` e `dir` (ordenação do mapa do time), e, na visão completa (`perfil=revops`), `vendedor`, `manager`, `regiao` como filtros; em qualquer perfil, `modo` (data do snapshot) e `aba` (`Foque`|`Reative`|`Limpe`|`Qualifique`). Um endereço antigo com `vendedor=`, `manager=` ou `regiao=` e sem `perfil` abre a visão completa. Nenhum desses vai para o `data.js`.
- `people.agents` e `people.managers` -> tela de entrada (selects de vendedor e de manager), mapa do time (vendedores do manager) e identidade na barra de perfil.
- Marcações do vendedor ("contatei", "agendei", "encerrar no CRM") ficam só no `localStorage` do navegador (chave `leadscorer:acoes:v1`), nunca no `data.js`. O tema escolhido fica em `leadscorer:tema` e o último perfil em `leadscorer:perfil:v1`; todo acesso ao armazenamento tem `try/catch`.
- Nenhum campo novo foi acrescentado ao contrato para as visões por perfil: mapa do time, pauta, progresso e simulador são derivados dos `deals` no navegador. **A separação por perfil é de experiência, não de segurança**: o `data.js` contém todos os deals.

## 9. Desvios em relação ao plano E6 item 3

O plano listou os campos de forma resumida; este contrato os fecha e acrescenta, sem remover nada:

1. `label` por snapshot (texto do seletor), para a interface não montar rótulos com datas à mão.
2. `backtest.rows` em formato longo e `backtest.{headline, criterion_text, notes, metrics}`: o plano pedia só "linhas + headline"; `criterion_text` e `notes` deixam a interface mostrar o critério pré-registrado e as ressalvas (a recência ganha em AUC em fins de trimestre) em vez de esconder; `metrics` leva os títulos das tabelas (com "top 20%") para o `data.js`, para nenhum número ficar escrito à mão na interface.
3. `outcome_summary` omitido (não `null`) em `"hoje"`, e `Qualifique` presente com zeros em `summary` de teste, para a interface não precisar de casos especiais por chave.
4. Frações em vez de porcentagens em todo o arquivo (uma convenção só).
