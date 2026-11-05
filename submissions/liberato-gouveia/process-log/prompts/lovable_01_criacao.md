# Prompt 01 para o Lovable: criação da tela

> **Status:** versão **v3, aprovada pelo Liberato em 04/11/2026 às 21:20** (ele aprovou a v2 e pediu um ajuste na regra de cálculos, que gerou a v3). O texto enviado ao Lovable é exatamente o que está depois da linha `---`.
> Mudança da v3: o app não pode recalcular notas, chances, valores esperados nem classificações, mas pode fazer contagens, somas, filtros e formatações. A v2 está em `versoes/prompt_lovable_01_rascunho_v2.md`.
> Mudança da v2: a data histórica (31/12/2017) agora aparece em destaque e o título deixou de usar "hoje". Isso atende à verificação 5 pedida pelo Liberato em 04/11 às 20:49. A v1 está em `versoes/prompt_lovable_01_rascunho_v1.md`.
> Quando for enviado, este arquivo passa a registrar o texto exato que foi usado.

---

Crie um app web de uma página chamado **"Lead Scorer — Onde focar"**, todo em português do Brasil, para vendedores B2B decidirem em quais oportunidades (deals) trabalhar.

## Regra mais importante
O app **não pode recalcular notas, chances, valores esperados nem classificações** (a lista, a ação e a ordem de cada deal). Tudo isso já vem pronto num arquivo JSON gerado por um motor externo, que foi testado. Use esses valores como vêm, sem alterar os textos do arquivo e sem criar outra ordem para os deals.
O app **pode** fazer contagens, somas, filtros e formatações (de moeda, data e porcentagem) para mostrar os dados corretamente. Por exemplo: contar deals por lista no filtro atual ou somar o `valor_esperado_usd` dos deals filtrados.

## Os dados são históricos: deixe isso evidente
Os dados são de uma base de demonstração e mostram o pipeline **como ele estava em 31/12/2017** (o campo `data_referencia`). **Nunca apresente os dados como atuais.** Não use as palavras "hoje" ou "agora" para falar dos deals. Em toda a tela, a referência é "em {data_referencia}".

## Dados
Ao abrir, carregue (fetch) o JSON desta URL:
`https://raw.githubusercontent.com/libegouv/ai-master-challenge/refs/heads/submission/liberato-gouveia/submissions/liberato-gouveia/solution/motor/saida/deals_priorizados.json`

Mostre "Carregando dados…" durante o carregamento. Se der erro, mostre: "Não foi possível carregar os dados. Tente recarregar a página."

Estrutura do JSON:
- `data_referencia`: texto no formato "2017-12-31". É a data em que o pipeline foi "fotografado".
- `limite_ciclo_dias`: número.
- `parametros`: objeto com `valor_minimo_foco_usd` e `valor_deal_grande_usd`, entre outros.
- `vendedores`: lista de `{vendedor, gerente, regiao}`, com as 35 pessoas da equipe.
- `curva_chance`: lista de `{idade_dias, chance}`, com a chance entre 0 e 1.
- `validacao_volta_no_tempo`: `{data_corte, deals_em_negociacao, top_n, captura_top20_nossa_logica, captura_top20_so_valor}`, com as capturas entre 0 e 1.
- `deals`: um objeto por deal aberto, com `id`, `vendedor`, `gerente`, `regiao`, `empresa` (pode ser null), `setor`, `produto`, `preco_usd`, `etapa` ("Negociação" ou "Prospecção"), `idade_dias` (pode ser null), `chance` (de 0 a 1, ou null), `valor_esperado_usd` (ou null), `nota` (de 0 a 100, ou null), `lista` (um destes valores: "Foco", "Requalificar ou encerrar", "Iniciar contato", "Automatizar"), `ordem_na_lista` (1 é o primeiro), `acao`, `porque`, `nota_texto` e `aviso` (texto ou null).
- Ignore `resumo_por_lista`. Os totais da tela precisam respeitar os filtros, então conte sempre a partir de `deals`.

## Tela
1. **Faixa fixa no topo**, sempre visível e com destaque (fundo âmbar claro, ícone de calendário): "Dados históricos de demonstração: pipeline como estava em {data_referencia em dd/mm/aaaa}. Não são dados atuais."
   **Cabeçalho:** o título "Lead Scorer — Onde focar" e o subtítulo "Situação em {data_referencia em dd/mm/aaaa} · {quantidade de deals no filtro} deals abertos naquela data".
2. **Filtros numa linha:** Região → Gerente → Vendedor, como selects em cascata, cada um com a opção "Todos". Escolher uma região limita os gerentes e vendedores àquela região, e escolher um gerente limita os vendedores àquele gerente. Monte os selects a partir de `vendedores`. Tudo começa em "Todos".
3. **Quatro cartões de resumo**, um por lista, cada um com o nome da lista, a quantidade de deals no filtro atual e uma linha curta:
   - Foco: "Avançar estes deals" e a soma do `valor_esperado_usd` (US$)
   - Requalificar ou encerrar: "Fora do ciclo histórico" e quantos têm a ação "Ligar para requalificar"
   - Iniciar contato: "Primeiro contato, por valor"
   - Automatizar: "Cadência automática"

   Clicar num cartão abre a aba daquela lista.
4. **Abas:** "Foco", "Requalificar ou encerrar", "Iniciar contato" e "Automatizar" (com a quantidade no título de cada aba), mais "Como a nota funciona".
5. **Em cada aba de lista**, mostre os deals do filtro atual em ordem crescente de `ordem_na_lista`. Cada deal é um cartão com:
   - Na aba Foco, um selo grande com a `nota` (de 0 a 100), que vai do cinza (nota baixa) ao azul forte (nota alta). Nas outras abas, um selo neutro com "—".
   - O `produto` e o `preco_usd` (formato "US$ 5.482"), a `empresa` (se for null, escreva "Empresa não cadastrada"), a `etapa`, a idade (por exemplo, "21 dias em negociação em 31/12/2017", usando a data de `data_referencia`; não mostre nada se for null) e o vendedor (só quando o filtro de vendedor estiver em "Todos").
   - A `acao` em destaque, como etiqueta, com estas cores: "Avançar este deal" em azul; "Ligar para requalificar" em laranja; "Encerrar no CRM" em cinza; "Fazer o primeiro contato" em verde; "Incluir na cadência automática (mensagens em lote)" em roxo.
   - O `porque` sempre visível, em texto normal (é a explicação para o vendedor), e logo abaixo o `nota_texto`, em texto menor.
   - Se `aviso` não for null, um alerta amarelo com ícone de atenção e o texto do `aviso`.
   - Na aba Foco, também "Valor esperado: US$ X" e "Chance: Y%". Y é a `chance` × 100, arredondada; se for maior que 0 e menor que 1%, escreva "menos de 1%".
   - Um botão "Mostrar mais", de 25 em 25, porque a lista de requalificação passa de 1.000 itens.
   - Uma busca por ID do deal ou nome da empresa, no topo da lista.
   - Se não houver deals: "Nenhum deal nesta lista para este filtro."
6. **Aba "Como a nota funciona"**, com exatamente estes textos (troque o que está entre chaves pelos valores do JSON):
   - **O que é a nota?** "Para cada deal em negociação, multiplicamos o preço do produto pela chance de ele ser ganho. O resultado é o valor esperado: quanto o deal 'vale' na fila. A nota de 0 a 100 diz qual porcentagem dos outros deals em Foco da empresa tem valor esperado menor. 100 é o maior da empresa."
   - **De onde vem a chance?** "Só da idade do deal (há quantos dias ele está em negociação), medida no histórico da empresa. Deals novos foram ganhos {chance em 0 dias}% das vezes; com 90 dias, {chance em 90 dias}%; com {limite_ciclo_dias} dias ou mais, nenhum deal da história foi ganho."
   - **Por que não usamos produto, setor, região ou vendedor?** "Testamos. As taxas de ganho por esses fatores são praticamente iguais (entre 60% e 65%), e um modelo de machine learning com todos eles acertou só 54% (o chute acerta 50%)."
   - **As 4 listas.** "Foco: deals em negociação dentro do ciclo histórico, com preço a partir de US$ {valor_minimo_foco_usd}. Requalificar ou encerrar: deals em negociação fora do ciclo histórico; a partir de US$ {valor_deal_grande_usd}, vale uma ligação antes de encerrar. Iniciar contato: deals em prospecção, ordenados pelo preço, porque não há histórico para estimar a chance. Automatizar: deals dentro do ciclo, abaixo de US$ {valor_minimo_foco_usd}, para cadência automática."
   - Um **gráfico de linha** da `curva_chance`, com "dias em negociação" no eixo x e "chance de ser ganho (%)" no eixo y.
   - Um bloco **"Teste de volta no tempo"**: "Em {data_corte em dd/mm/aaaa}, os 20% de deals com maior nota nesta lógica concentravam {captura_top20_nossa_logica em %} da receita ganha nos meses seguintes. Ordenando só pelo preço, seriam {captura_top20_so_valor em %}."
   - Uma nota final: "O app não recalcula notas, chances nem listas: tudo vem de um motor testado (12 testes automáticos, incluindo um teste contra o uso de informação do futuro)."

## Estilo
Visual limpo e profissional, com fundo claro e tipografia legível. O app precisa ser responsivo e funcionar no celular. Use os componentes shadcn/ui e os ícones lucide, sem animações exageradas. Não use login, banco de dados nem backend: é um app só de leitura.
