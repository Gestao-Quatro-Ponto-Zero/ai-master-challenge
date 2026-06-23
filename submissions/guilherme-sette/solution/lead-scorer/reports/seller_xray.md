# Seller X-Ray

Generated from standardized CSVs in `data/processed`.

## Metric Definitions

- `win_rate`: won / closed opportunities.
- `won_value_median` and `won_value_std`: median and sample standard deviation of won deal values.
- `days_to_close_median` and `days_to_close_std`: median and sample standard deviation of lifecycle days for closed opportunities.
- `closed_product_mode`, `closed_sector_mode`, `open_product_mode`, and `open_stage_mode`: categorical modes for historical/current portfolio composition.
- `history_maturity`: `no_history`, `thin_history` (<100 closed), `limited_history` (100-149 closed), or `consolidated` (150+ closed).

## Portfolio Summary

- Active sellers with closed history: 30.
- Sellers on roster with no opportunity history: 5.
- Global closed win rate: 63.2%.
- Open pipeline value across active sellers: US$ 4,966,215.

## Top Historical Performers

| sales_agent | manager | regional_office | closed_opportunities | win_rate | won_revenue_total | won_value_median | days_to_close_median | open_deals | open_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Hayden Neloms | Celia Rouche | West | 152 | 70.4% | US$ 272,111 | US$ 3,197 | 18.5 | 50 | US$ 123,530 |
| Maureen Marcano | Summer Sewald | West | 213 | 70.0% | US$ 350,395 | US$ 1,121 | 57.0 | 72 | US$ 140,225 |
| Cecily Lampkin | Dustin Brinkmann | Central | 160 | 66.9% | US$ 229,800 | US$ 1,168 | 15.0 | 43 | US$ 86,748 |
| Versie Hillebrand | Dustin Brinkmann | Central | 264 | 66.7% | US$ 187,693 | US$ 60 | 34.0 | 97 | US$ 101,409 |
| Moses Frase | Dustin Brinkmann | Central | 195 | 66.2% | US$ 207,182 | US$ 588 | 66.0 | 65 | US$ 108,161 |
| Boris Faz | Rocco Neubert | East | 153 | 66.0% | US$ 261,631 | US$ 1,239 | 19.0 | 57 | US$ 143,456 |
| James Ascencio | Summer Sewald | West | 206 | 65.5% | US$ 413,533 | US$ 3,624 | 51.5 | 61 | US$ 192,216 |
| Corliss Cosme | Cara Losch | East | 229 | 65.5% | US$ 421,036 | US$ 2,918 | 36.0 | 81 | US$ 216,840 |

## Underperforming Historical Conversion

| sales_agent | manager | regional_office | closed_opportunities | win_rate | won_revenue_total | won_value_median | days_to_close_median | open_deals | open_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Lajuana Vencill | Dustin Brinkmann | Central | 231 | 55.0% | US$ 194,632 | US$ 582 | 61.0 | 80 | US$ 116,039 |
| Markita Hansen | Celia Rouche | West | 227 | 57.3% | US$ 328,792 | US$ 1,044 | 49.0 | 79 | US$ 282,756 |
| Donn Cantrell | Rocco Neubert | East | 275 | 57.5% | US$ 445,860 | US$ 3,228 | 51.0 | 0 | US$ 0 |
| Gladys Colclough | Melvin Marxen | Central | 232 | 58.2% | US$ 345,674 | US$ 3,077 | 50.0 | 85 | US$ 192,142 |
| Niesha Huffines | Melvin Marxen | Central | 175 | 60.0% | US$ 176,961 | US$ 1,033 | 49.0 | 64 | US$ 107,745 |
| Daniell Hammack | Rocco Neubert | East | 187 | 61.0% | US$ 364,229 | US$ 3,770 | 30.0 | 72 | US$ 209,320 |
| Zane Levy | Summer Sewald | West | 261 | 61.7% | US$ 430,068 | US$ 1,195 | 27.0 | 88 | US$ 193,348 |
| Anna Snelling | Dustin Brinkmann | Central | 336 | 61.9% | US$ 275,056 | US$ 460 | 55.5 | 112 | US$ 173,259 |

## Current Portfolio Watchlist

| sales_agent | manager | regional_office | win_rate | open_deals | open_value | old_engaging_deals | old_engaging_value | open_account_known_pct | portfolio_risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Darcel Schlecht | Melvin Marxen | Central | 63.1% | 194 | US$ 656,040 | 83 | US$ 273,766 | 30.9% | large_stale_backlog |
| Markita Hansen | Celia Rouche | West | 57.3% | 79 | US$ 282,756 | 69 | US$ 267,800 | 34.2% | high_value_low_conversion |
| Kary Hendrixson | Summer Sewald | West | 62.4% | 103 | US$ 276,517 | 91 | US$ 243,966 | 35.9% | large_stale_backlog |
| Vicki Laflamme | Celia Rouche | West | 63.7% | 104 | US$ 227,326 | 98 | US$ 205,454 | 26.0% | large_stale_backlog |
| Cassey Cress | Rocco Neubert | East | 62.5% | 85 | US$ 220,860 | 79 | US$ 203,489 | 34.1% | large_stale_backlog |
| Daniell Hammack | Rocco Neubert | East | 61.0% | 72 | US$ 209,320 | 65 | US$ 196,172 | 34.7% | high_value_low_conversion |
| Zane Levy | Summer Sewald | West | 61.7% | 88 | US$ 193,348 | 78 | US$ 178,048 | 33.0% | large_stale_backlog |
| Kami Bicknell | Summer Sewald | West | 64.0% | 90 | US$ 190,990 | 80 | US$ 170,873 | 32.2% | large_stale_backlog |

## Largest Open Portfolios

| sales_agent | manager | regional_office | win_rate | open_deals | open_value | old_engaging_deals | open_product_mode | open_product_mode_share | portfolio_risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Darcel Schlecht | Melvin Marxen | Central | 63.1% | 194 | US$ 656,040 | 83 | GTX Pro | 47.9% | large_stale_backlog |
| Markita Hansen | Celia Rouche | West | 57.3% | 79 | US$ 282,756 | 69 | GTX Basic | 22.8% | high_value_low_conversion |
| Kary Hendrixson | Summer Sewald | West | 62.4% | 103 | US$ 276,517 | 91 | GTX Basic | 34.0% | large_stale_backlog |
| Elease Gluck | Celia Rouche | West | 63.5% | 51 | US$ 251,649 | 46 | MG Special | 45.1% | low_data_confidence |
| Marty Freudenburg | Melvin Marxen | Central | 62.9% | 87 | US$ 229,445 | 33 | GTX Plus Basic | 25.3% | low_data_confidence |
| Vicki Laflamme | Celia Rouche | West | 63.7% | 104 | US$ 227,326 | 98 | MG Special | 28.8% | large_stale_backlog |
| Cassey Cress | Rocco Neubert | East | 62.5% | 85 | US$ 220,860 | 79 | GTX Plus Basic | 21.2% | large_stale_backlog |
| Corliss Cosme | Cara Losch | East | 65.5% | 81 | US$ 216,840 | 73 | GTX Basic | 24.7% | low_data_confidence |
| Daniell Hammack | Rocco Neubert | East | 61.0% | 72 | US$ 209,320 | 65 | GTX Plus Basic | 29.2% | high_value_low_conversion |
| Zane Levy | Summer Sewald | West | 61.7% | 88 | US$ 193,348 | 78 | GTX Basic | 39.8% | large_stale_backlog |

## Sellers Requiring Different Interpretation

| sales_agent | manager | regional_office | closed_opportunities | open_deals | open_value | history_maturity | performance_band |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Rosalina Dieter | Celia Rouche | West | 110 | 50 | US$ 119,664 | limited_history | above_average |
| Rosie Papadopoulos | Cara Losch | East | 121 | 39 | US$ 116,685 | limited_history | above_average |
| Elease Gluck | Celia Rouche | West | 126 | 51 | US$ 251,649 | limited_history | around_average |
| Garret Kinder | Cara Losch | East | 123 | 0 | US$ 0 | limited_history | around_average |
| Carl Lin | Summer Sewald | West | 0 | 0 | US$ 0 | no_history | no_history |
| Carol Thompson | Celia Rouche | West | 0 | 0 | US$ 0 | no_history | no_history |
| Elizabeth Anderson | Cara Losch | East | 0 | 0 | US$ 0 | no_history | no_history |
| Mei-Mei Johns | Melvin Marxen | Central | 0 | 0 | US$ 0 | no_history | no_history |
| Natalya Ivanova | Rocco Neubert | East | 0 | 0 | US$ 0 | no_history | no_history |
| Wilburn Farren | Cara Losch | East | 79 | 31 | US$ 82,275 | thin_history | insufficient_sample |

## Full Detail

See `data/processed/seller_xray.csv` for the complete seller-level table.
