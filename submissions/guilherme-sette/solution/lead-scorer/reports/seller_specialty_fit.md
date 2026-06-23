# Seller Specialty Fit

Generated from standardized CSVs in `data/processed`.

## Method

- Historical fit uses only closed opportunities.
- Open deal matching uses product, ticket band, sector, revenue band, employee band, and account when available.
- Seller-segment win rates are smoothed against the segment baseline to reduce overfitting.
- Sellers need at least 100 closed opportunities to be considered specialist candidates.
- Results are associative, not causal.

## Strongest Apparent Specialties

| sales_agent | dimension | segment_value | seller_segment_closed | seller_segment_win_rate | segment_win_rate | uplift_vs_segment | specialty_score | fit_strength |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Markita Hansen | sector | entertainment | 21 | 90.5% | 64.7% | 11.8% | 13.3 | strong_fit |
| Lajuana Vencill | account | Rangreen | 13 | 92.3% | 75.0% | 5.9% | 11.4 | strong_fit |
| Moses Frase | product | GTX Basic | 59 | 79.7% | 63.7% | 11.2% | 10.5 | strong_fit |
| Cassey Cress | account | Plussunin | 14 | 92.9% | 60.4% | 11.6% | 10.2 | strong_fit |
| Corliss Cosme | employee_band | 500_to_2k | 34 | 82.4% | 61.9% | 11.8% | 9.8 | strong_fit |
| Jonathan Berthelot | account | Rangreen | 11 | 100.0% | 75.0% | 7.6% | 9.3 | strong_fit |
| Rosalina Dieter | sector | retail | 24 | 83.3% | 63.1% | 9.9% | 9.2 | strong_fit |
| Rosie Papadopoulos | product | GTX Pro | 31 | 80.6% | 63.6% | 9.5% | 9.2 | strong_fit |
| Hayden Neloms | product | MG Advanced | 77 | 76.6% | 60.3% | 12.3% | 9.1 | strong_fit |
| Gladys Colclough | account | Inity | 14 | 85.7% | 68.0% | 6.4% | 9.0 | strong_fit |
| Maureen Marcano | ticket_band | high_ticket_4k_to_10k | 62 | 79.0% | 63.8% | 10.8% | 8.9 | strong_fit |
| Vicki Laflamme | account | Goodsilron | 16 | 87.5% | 73.9% | 5.3% | 8.9 | strong_fit |

## High-Value Open Deals Where Suggested Specialist Differs

| opportunity_id | deal_stage | product | ticket_band | estimated_deal_value | current_sales_agent | recommended_sales_agent | match_score | match_confidence | match_band | match_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ZK4S74FD | engaging | GTX Plus Pro | high_ticket_4k_to_10k | US$ 5,482 | Vicki Laflamme | Maureen Marcano | 77.9 | 97.1% | specialist_match | product=GTX Plus Pro (strong_fit, n=32); ticket_band=high_ticket_4k_to_10k (strong_fit, n=62); sector=retail (strong_fit, n=39) |
| 6OD1J7MW | engaging | GTX Plus Pro | high_ticket_4k_to_10k | US$ 5,482 | Elease Gluck | Maureen Marcano | 77.6 | 90.0% | specialist_match | product=GTX Plus Pro (strong_fit, n=32); ticket_band=high_ticket_4k_to_10k (strong_fit, n=62); sector=retail (strong_fit, n=39) |
| 059K86LU | engaging | GTX Plus Pro | high_ticket_4k_to_10k | US$ 5,482 | Kami Bicknell | Maureen Marcano | 77.2 | 87.8% | specialist_match | product=GTX Plus Pro (strong_fit, n=32); ticket_band=high_ticket_4k_to_10k (strong_fit, n=62); sector=medical (strong_fit, n=19) |
| 1FEHFRKX | engaging | GTX Plus Pro | high_ticket_4k_to_10k | US$ 5,482 | Anna Snelling | Maureen Marcano | 77.2 | 87.8% | specialist_match | product=GTX Plus Pro (strong_fit, n=32); ticket_band=high_ticket_4k_to_10k (strong_fit, n=62); sector=medical (strong_fit, n=19) |
| B26TNOGQ | prospecting | GTX Plus Pro | high_ticket_4k_to_10k | US$ 5,482 | Jonathan Berthelot | Maureen Marcano | 77.2 | 87.8% | specialist_match | product=GTX Plus Pro (strong_fit, n=32); ticket_band=high_ticket_4k_to_10k (strong_fit, n=62); sector=medical (strong_fit, n=19) |
| CBQRKYZP | engaging | GTX Plus Pro | high_ticket_4k_to_10k | US$ 5,482 | Marty Freudenburg | Maureen Marcano | 77.2 | 87.8% | specialist_match | product=GTX Plus Pro (strong_fit, n=32); ticket_band=high_ticket_4k_to_10k (strong_fit, n=62); sector=medical (strong_fit, n=19) |
| KJHM27ZM | engaging | GTX Plus Pro | high_ticket_4k_to_10k | US$ 5,482 | Daniell Hammack | Maureen Marcano | 77.2 | 87.8% | specialist_match | product=GTX Plus Pro (strong_fit, n=32); ticket_band=high_ticket_4k_to_10k (strong_fit, n=62); sector=medical (strong_fit, n=19) |
| WZN26QZQ | engaging | GTX Plus Pro | high_ticket_4k_to_10k | US$ 5,482 | Corliss Cosme | Maureen Marcano | 77.2 | 87.8% | specialist_match | product=GTX Plus Pro (strong_fit, n=32); ticket_band=high_ticket_4k_to_10k (strong_fit, n=62); sector=medical (strong_fit, n=19) |
| 49T7VKA7 | prospecting | GTX Plus Pro | high_ticket_4k_to_10k | US$ 5,482 | Gladys Colclough | Maureen Marcano | 77.1 | 88.7% | specialist_match | product=GTX Plus Pro (strong_fit, n=32); ticket_band=high_ticket_4k_to_10k (strong_fit, n=62); sector=retail (strong_fit, n=39) |
| 7A3R2M9T | engaging | GTX Plus Pro | high_ticket_4k_to_10k | US$ 5,482 | Vicki Laflamme | Maureen Marcano | 76.9 | 86.8% | specialist_match | product=GTX Plus Pro (strong_fit, n=32); ticket_band=high_ticket_4k_to_10k (strong_fit, n=62); sector=telecommunications (possible_fit, n=17) |
| I3KQNE9V | engaging | GTX Plus Pro | high_ticket_4k_to_10k | US$ 5,482 | Darcel Schlecht | Maureen Marcano | 76.8 | 87.8% | specialist_match | product=GTX Plus Pro (strong_fit, n=32); ticket_band=high_ticket_4k_to_10k (strong_fit, n=62); sector=medical (strong_fit, n=19) |
| HF74MC9F | engaging | GTX Plus Pro | high_ticket_4k_to_10k | US$ 5,482 | Corliss Cosme | Maureen Marcano | 76.6 | 90.0% | specialist_match | product=GTX Plus Pro (strong_fit, n=32); ticket_band=high_ticket_4k_to_10k (strong_fit, n=62); sector=retail (strong_fit, n=39) |
| 4SOUOUKH | engaging | GTX Plus Pro | high_ticket_4k_to_10k | US$ 5,482 | Vicki Laflamme | Maureen Marcano | 76.5 | 86.8% | specialist_match | product=GTX Plus Pro (strong_fit, n=32); ticket_band=high_ticket_4k_to_10k (strong_fit, n=62); sector=telecommunications (possible_fit, n=17) |
| 9E8A7MQ8 | engaging | GTX Plus Pro | high_ticket_4k_to_10k | US$ 5,482 | Kary Hendrixson | Maureen Marcano | 76.4 | 96.4% | specialist_match | product=GTX Plus Pro (strong_fit, n=32); ticket_band=high_ticket_4k_to_10k (strong_fit, n=62); sector=retail (strong_fit, n=39) |
| BBOWBQA6 | engaging | GTX Plus Pro | high_ticket_4k_to_10k | US$ 5,482 | Niesha Huffines | Maureen Marcano | 76.4 | 96.4% | specialist_match | product=GTX Plus Pro (strong_fit, n=32); ticket_band=high_ticket_4k_to_10k (strong_fit, n=62); sector=retail (strong_fit, n=39) |

## Best Current Deals Inside Seller Specialty

| current_sales_agent | opportunity_id | deal_stage | product | ticket_band | estimated_deal_value | current_match_score | current_match_confidence | current_match_band | recommended_sales_agent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Maureen Marcano | MV227O65 | engaging | GTX Plus Pro | high_ticket_4k_to_10k | US$ 5,482 | 76.9 | 86.8% | specialist_match | Maureen Marcano |
| Hayden Neloms | 3N46WQVI | engaging | MG Advanced | mid_ticket_1k_to_4k | US$ 3,393 | 75.8 | 85.8% | specialist_match | Hayden Neloms |
| Maureen Marcano | R1K16RZO | engaging | GTX Plus Pro | high_ticket_4k_to_10k | US$ 5,482 | 74.3 | 50.0% | specialist_match | Maureen Marcano |
| Maureen Marcano | D62905BC | engaging | GTX Plus Pro | high_ticket_4k_to_10k | US$ 5,482 | 74.3 | 50.0% | specialist_match | Maureen Marcano |
| Maureen Marcano | 1GIP77EP | engaging | GTX Plus Pro | high_ticket_4k_to_10k | US$ 5,482 | 74.3 | 50.0% | specialist_match | Maureen Marcano |
| Maureen Marcano | DYNHHN6P | engaging | GTX Pro | high_ticket_4k_to_10k | US$ 4,821 | 73.9 | 87.2% | specialist_match | Maureen Marcano |
| Hayden Neloms | WRUG19FZ | engaging | MG Advanced | mid_ticket_1k_to_4k | US$ 3,393 | 74.6 | 67.5% | specialist_match | Hayden Neloms |
| Maureen Marcano | 54OH0061 | engaging | GTX Pro | high_ticket_4k_to_10k | US$ 4,821 | 73.5 | 50.0% | specialist_match | Maureen Marcano |
| Maureen Marcano | 03VCDZEE | engaging | GTX Pro | high_ticket_4k_to_10k | US$ 4,821 | 73.5 | 50.0% | specialist_match | Maureen Marcano |
| Maureen Marcano | GQ2W1DXM | engaging | GTX Pro | high_ticket_4k_to_10k | US$ 4,821 | 73.5 | 50.0% | specialist_match | Maureen Marcano |
| Maureen Marcano | 5BE27MLY | engaging | GTX Pro | high_ticket_4k_to_10k | US$ 4,821 | 73.5 | 50.0% | specialist_match | Maureen Marcano |
| Hayden Neloms | Y2EC6KYG | engaging | MG Advanced | mid_ticket_1k_to_4k | US$ 3,393 | 74.2 | 50.0% | specialist_match | Hayden Neloms |
| Hayden Neloms | ERFRHR3Z | engaging | MG Advanced | mid_ticket_1k_to_4k | US$ 3,393 | 74.2 | 50.0% | specialist_match | Hayden Neloms |
| Hayden Neloms | 0EYXI1UN | engaging | MG Advanced | mid_ticket_1k_to_4k | US$ 3,393 | 74.2 | 50.0% | specialist_match | Hayden Neloms |
| Hayden Neloms | NUQPJV8A | engaging | MG Advanced | mid_ticket_1k_to_4k | US$ 3,393 | 74.2 | 50.0% | specialist_match | Hayden Neloms |

## Sellers Excluded From Specialist Candidate Pool

| sales_agent | manager | regional_office | closed_opportunities | win_rate | history_maturity |
| --- | --- | --- | --- | --- | --- |
| Carl Lin | Summer Sewald | West | 0 | n/a | no_history |
| Carol Thompson | Celia Rouche | West | 0 | n/a | no_history |
| Elizabeth Anderson | Cara Losch | East | 0 | n/a | no_history |
| Mei-Mei Johns | Melvin Marxen | Central | 0 | n/a | no_history |
| Natalya Ivanova | Rocco Neubert | East | 0 | n/a | no_history |
| Wilburn Farren | Cara Losch | East | 79 | 69.6% | thin_history |

## Output Files

- `data/processed/seller_segment_fit.csv`
- `data/processed/open_deal_specialist_recommendations.csv`
- `data/processed/seller_best_fit_deals.csv`
