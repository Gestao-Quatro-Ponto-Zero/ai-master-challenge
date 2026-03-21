# Raw schema summary

## accounts.csv
- source_of_truth: True
- rows: 85
- notes: Nao renomear colunas na ingestao raw.

| coluna | tipo inferido | nulavel | nulos | cardinalidade aprox | sample |
|---|---|---|---:|---:|---|
| account | string | False | 0 | 85 | Acme Corporation, Betasoloin, Betatech |
| sector | string | False | 0 | 10 | technolgy, medical, medical |
| year_established | int | False | 0 | 35 | 1996, 1999, 1986 |
| revenue | float | False | 0 | 85 | 1100.04, 251.41, 647.18 |
| employees | int | False | 0 | 85 | 2822, 495, 1185 |
| office_location | string | False | 0 | 15 | United States, United States, Kenya |
| subsidiary_of | string | True | 70 | 7 | Acme Corporation, Massive Dynamic, Acme Corporation |

## products.csv
- source_of_truth: True
- rows: 7
- notes: Nao renomear colunas na ingestao raw.

| coluna | tipo inferido | nulavel | nulos | cardinalidade aprox | sample |
|---|---|---|---:|---:|---|
| product | string | False | 0 | 7 | GTX Basic, GTX Pro, MG Special |
| series | string | False | 0 | 3 | GTX, GTX, MG |
| sales_price | int | False | 0 | 7 | 550, 4821, 55 |

## sales_teams.csv
- source_of_truth: True
- rows: 35
- notes: Nao renomear colunas na ingestao raw.

| coluna | tipo inferido | nulavel | nulos | cardinalidade aprox | sample |
|---|---|---|---:|---:|---|
| sales_agent | string | False | 0 | 35 | Anna Snelling, Cecily Lampkin, Versie Hillebrand |
| manager | string | False | 0 | 6 | Dustin Brinkmann, Dustin Brinkmann, Dustin Brinkmann |
| regional_office | string | False | 0 | 3 | Central, Central, Central |

## sales_pipeline.csv
- source_of_truth: True
- rows: 8800
- notes: Nao renomear colunas na ingestao raw.

| coluna | tipo inferido | nulavel | nulos | cardinalidade aprox | sample |
|---|---|---|---:|---:|---|
| opportunity_id | string | False | 0 | 8800 | 1C1I7A6R, Z063OYW0, EC4QE1BX |
| sales_agent | string | False | 0 | 30 | Moses Frase, Darcel Schlecht, Darcel Schlecht |
| product | string | False | 0 | 7 | GTX Plus Basic, GTXPro, MG Special |
| account | string | True | 1425 | 85 | Cancity, Isdom, Cancity |
| deal_stage | string | False | 0 | 4 | Won, Won, Won |
| engage_date | string | True | 500 | 421 | 2016-10-20, 2016-10-25, 2016-10-25 |
| close_date | string | True | 2089 | 306 | 2017-03-01, 2017-03-11, 2017-03-07 |
| close_value | int | True | 2089 | 2051 | 1054, 4514, 50 |

## metadata.csv
- source_of_truth: True
- rows: 21
- notes: Nao renomear colunas na ingestao raw.

| coluna | tipo inferido | nulavel | nulos | cardinalidade aprox | sample |
|---|---|---|---:|---:|---|
| Table | string | False | 0 | 4 | accounts, accounts, accounts |
| Field | string | False | 0 | 18 | account, sector, year_established |
| Description | string | False | 0 | 18 | Company name, Industry, Year Established |
