# Exploracao inicial — Lead Scorer

## Shapes
- accounts: 85 linhas x 7 colunas — colunas: ['account', 'sector', 'year_established', 'revenue', 'employees', 'office_location', 'subsidiary_of']
- products: 7 linhas x 3 colunas — colunas: ['product', 'series', 'sales_price']
- sales_teams: 35 linhas x 3 colunas — colunas: ['sales_agent', 'manager', 'regional_office']
- sales_pipeline: 8800 linhas x 8 colunas — colunas: ['opportunity_id', 'sales_agent', 'product', 'account', 'deal_stage', 'engage_date', 'close_date', 'close_value']

## Nulos por coluna
- **accounts**: subsidiary_of=70
- **products**: sem nulos
- **sales_teams**: sem nulos
- **sales_pipeline**: account=1425, engage_date=500, close_date=2089, close_value=2089

## Validacao de joins (mismatches)
- sales_pipeline.account sem match em accounts.account: 0 valores -> []
- sales_pipeline.product sem match em products.product: 1 valores -> ['GTXPro']
- sales_pipeline.sales_agent sem match em sales_teams.sales_agent: 0 valores -> []

## Distribuicao de deal_stage
- Won: 4238 (48.2%)
- Lost: 2473 (28.1%)
- Engaging: 1589 (18.1%)
- Prospecting: 500 (5.7%)

## Win rate global (entre deals fechados, Won+Lost)
- 63.2% (6711 deals fechados)

## Win rate por produto (min 5 deals fechados)
- MG Special: 64.8% (n=1223)
- GTX Plus Pro: 64.3% (n=745)
- GTX Basic: 63.7% (n=1436)
- GTXPro: 63.6% (n=1147)
- GTX Plus Basic: 62.1% (n=1051)
- MG Advanced: 60.3% (n=1084)
- GTK 500: 60.0% (n=25)

## Win rate por setor da conta (min 5 deals fechados)
- marketing: 64.8% (n=623)
- entertainment: 64.7% (n=402)
- software: 63.9% (n=704)
- technolgy: 63.4% (n=1058)
- services: 63.4% (n=352)
- retail: 63.1% (n=1267)
- employment: 62.6% (n=286)
- telecommunications: 62.5% (n=456)
- medical: 62.3% (n=950)
- finance: 61.2% (n=613)

## Win rate por escritorio regional (min 5 deals fechados)
- West: 63.9% (n=2249)
- East: 63.0% (n=1858)
- Central: 62.6% (n=2604)

## Win rate por vendedor (top 10 e bottom 10, min 10 deals fechados)
Top 10:
- Hayden Neloms: 70.4% (n=152)
- Maureen Marcano: 70.0% (n=213)
- Wilburn Farren: 69.6% (n=79)
- Cecily Lampkin: 66.9% (n=160)
- Versie Hillebrand: 66.7% (n=264)
- Moses Frase: 66.2% (n=195)
- Boris Faz: 66.0% (n=153)
- James Ascencio: 65.5% (n=206)
- Corliss Cosme: 65.5% (n=229)
- Rosalina Dieter: 65.5% (n=110)
Bottom 10:
- Kary Hendrixson: 62.4% (n=335)
- Anna Snelling: 61.9% (n=336)
- Zane Levy: 61.7% (n=261)
- Garret Kinder: 61.0% (n=123)
- Daniell Hammack: 61.0% (n=187)
- Niesha Huffines: 60.0% (n=175)
- Gladys Colclough: 58.2% (n=232)
- Donn Cantrell: 57.5% (n=275)
- Markita Hansen: 57.3% (n=227)
- Lajuana Vencill: 55.0% (n=231)

## Tempo no pipeline (dias entre engage_date e close_date, deals fechados)
- Won: media=51.8 dias, mediana=57.0
- Lost: media=41.5 dias, mediana=14.0

## Deals abertos (referencia: data mais recente no dataset = 2017-12-31)
- Total abertos: 2089 ({'Engaging': 1589, 'Prospecting': 500})
- Idade media: 198.8 dias, mediana: 165.0
- Percentis de idade (dias): p50=165, p75=263, p90=319, p95=353

## close_value (deals Won)
- media=2361, mediana=1117, min=38, max=30288

## sales_price por produto (products.csv)
- GTX Basic (GTX): 550
- GTX Pro (GTX): 4821
- MG Special (MG): 55
- MG Advanced (MG): 3393
- GTX Plus Pro (GTX): 5482
- GTX Plus Basic (GTX): 1096
- GTK 500 (GTK): 26768

## Achados sobre mismatch de produto: 'GTXPro' vs 'GTX Pro'
- sales_pipeline usa o literal 'GTXPro' (sem espaco) em 1480 registros (incluindo deals abertos).
- products.csv define o produto como 'GTX Pro' (com espaco) — mismatch de nomenclatura, nao produto novo.
- Correcao necessaria antes de qualquer join por produto: normalizar 'GTXPro' -> 'GTX Pro'.

## Achados sobre account nulo no pipeline (1425 registros)
- Ocorre **somente** em deals abertos: Engaging=1088, Prospecting=337
- Nenhum deal Won ou Lost tem account nulo — 100% dos deals fechados tem conta associada.
- Implicacao pro scoring: ~1425 deals abertos nao terao features de conta (setor/revenue/employees) disponiveis; precisa de fallback.

## Achados sobre engage_date nulo (500 registros)
- Coincide exatamente com os 500 deals em estagio 'Prospecting' (100%): Prospecting=500
- Padrao esperado, nao e problema de dados: Prospecting = ainda nao engajado, logo sem engage_date.
- Implicacao pro scoring: 'dias no pipeline' nao pode ser calculado para Prospecting; usar outra logica de recencia (ex.: data de criacao do opportunity_id, se existir, ou tratar como grupo separado).

## Outras checagens de consistencia (todas OK)
- opportunity_id duplicado: 0
- Won sem close_date: 0
- Won sem close_value: 0
- Lost com close_value>0: 0
- Prospecting/Engaging com close_date preenchido: 0
