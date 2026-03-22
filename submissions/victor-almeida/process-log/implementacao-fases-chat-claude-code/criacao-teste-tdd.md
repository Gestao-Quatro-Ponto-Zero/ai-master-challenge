╭─── Claude Code v2.1.81 ──────────────────────────────────────────────────────╮
│                                                    │ Tips for getting        │
│             Welcome back CompleteAuto!             │ started                 │
│                                                    │ ✔ Run /init to create … │
│                       ▐▛███▜▌                      │ ─────────────────────── │
│                      ▝▜█████▛▘                     │ Recent activity         │
│                        ▘▘ ▝▝                       │ No recent activity      │
│       Opus 4.6 (1M context) · Claude Max ·         │                         │
│       completecarapp@gmail.com's Organization      │                         │
│                ~/ai-master-challenge               │                         │
╰──────────────────────────────────────────────────────────────────────────────╯

❯ /clear                                                                        
  ⎿  (no content)

❯ Coloque nas @specs/ e no @CLAUDE.md que sempre que for tocar uma task, use o  
TDD test-driven development e NUNCA burle os testes, sempre faca o teste        
verdadeiro e só passe e finalize a task se o teste deu certo, nao burle pelo    
terminal, e por lugar nenhum faca o teste de verdade.                           
  ⎿  Listed directory specs/
  ⎿  Read CLAUDE.md (180 lines)

⏺ Vou adicionar a diretriz de TDD no CLAUDE.md e criar uma spec dedicada para
  isso.

  Read 1 file (ctrl+o to expand)
  ⎿  Interrupted · What should Claude do instead?

❯ Eu nao quero quE CRIE UMA SPEC pra isso, quero que as SPECS Existentes tenham 
 seus proprios testes TDD e o claude md também, nao precisa de uma spec so pra  
teste.                                                                          

⏺ Entendido. Vou adicionar a diretriz de TDD no CLAUDE.md e incluir seção de
  testes em cada spec existente. Primeiro, vou ler todas as specs.

  Read 8 files (ctrl+o to expand)

⏺ Vou ler as specs que faltaram e o scoring_engine.

  Read 2 files (ctrl+o to expand)

⏺ Agora vou fazer as edições. Começo pelo CLAUDE.md e depois cada spec.

⏺ Update(CLAUDE.md)
  ⎿  Added 42 lines
      113  - Filtros por vendedor/manager/região agregam muito valor
      114  - Comunicação em **português (PT-BR)**
      115  
      116 +## TDD — Test-Driven Development (OBRIGATÓRIO)                
      117 +                                                              
      118 +**Toda task DEVE seguir o fluxo TDD rigoroso:**               
      119 +                                                              
      120 +1. **Escrever o teste ANTES do código** — o teste define o com
          +portamento esperado                                           
      121 +2. **Rodar o teste e ver ele FALHAR** (Red) — confirma que o t
          +este é real                                                   
      122 +3. **Implementar o código mínimo** para fazer o teste passar (
          +Green)                                                        
      123 +4. **Refatorar** se necessário, mantendo os testes passando (R
          +efactor)                                                      
      124 +5. **Só considerar a task concluída quando TODOS os testes pas
          +sam genuinamente**                                            
      125 +                                                              
      126 +### Regras invioláveis                                        
      127 +                                                              
      128 +- **NUNCA burlar testes** — não alterar assertions para forçar
          + pass, não skipar testes, não mockar o que deveria ser testado
          + de verdade                                                   
      129 +- **NUNCA fingir que testes passaram** — sempre rodar `pytest`
          + de verdade e mostrar o output real                           
      130 +- **NUNCA manipular o terminal** para esconder falhas — sem `|
          +| true`, sem `2>/dev/null` em testes, sem grep seletivo no out
          +put                                                           
      131 +- **NUNCA comentar ou remover testes** que estão falhando para
          + "resolver" o problema — corrigir o código, não o teste       
      132 +- **NUNCA usar `assert True`** ou assertions triviais que semp
          +re passam — cada assertion deve verificar comportamento real  
      133 +- **Testes devem testar lógica real** — dados de entrada → pro
          +cessamento → resultado esperado verificável                   
      134 +- **Cada spec tem seus próprios critérios de teste** — consult
          +ar a seção "Testes TDD" da spec correspondente antes de implem
          +entar                                                         
      135 +                                                              
      136 +### Estrutura de testes                                       
      137 +                                                              
      138 +```                                                           
      139 +submissions/victor-almeida/solution/                          
      140 +├── tests/                                                    
      141 +│   ├── __init__.py                                           
      142 +│   ├── test_data_loader.py      ← Testes do data_model.md    
      143 +│   ├── test_scoring_engine.py   ← Testes do scoring_engine.md
      144 +│   ├── test_deal_zombie.py      ← Testes do deal_zombie.md   
      145 +│   ├── test_nba.py              ← Testes do next_best_action.
          +md                                                            
      146 +│   ├── test_filters.py          ← Testes do filters.md       
      147 +│   ├── test_metrics.py          ← Testes do metrics_summary.m
          +d                                                             
      148 +│   ├── test_pipeline_view.py    ← Testes do pipeline_view.md 
      149 +│   └── test_formatters.py       ← Testes de utils/formatters.
          +py                                                            
      150 +```                                                           
      151 +                                                              
      152 +### Comando para rodar testes                                 
      153 +                                                              
      154 +```bash                                                       
      155 +cd submissions/victor-almeida/solution && python -m pytest tes
          +ts/ -v                                                        
      156 +```                                                           
      157 +                                                              
      158  ## Como se diferenciar
      159  
      160  O avaliador vai ver várias submissões. As fracas são previsíve
           is:

⏺ Agora vou adicionar a seção de testes TDD em cada spec. Vou fazer as edições
  em paralelo.

⏺ Update(specs/data_model.md)
  ⎿  Error editing file

  Read 1 file (ctrl+o to expand)

⏺ Update(specs/data_model.md)
  ⎿  Added 115 lines
      613  | **Proxy de valor** | `sales_price` do produto, usado como es
           timativa de `close_value` para deals ativos (que nao tem valor
            de fechamento). |
      614  | **Fit** | Compatibilidade vendedor-setor, medida pelo win ra
           te do vendedor no setor vs media do time. |
      615  | **Saude da conta** | Win rate historico da conta em deals fe
           chados. Indica se a conta tende a converter ou nao. |
      616 +                                                              
      617 +---                                                           
      618 +                                                              
      619 +## 11. Testes TDD (test_data_loader.py)                       
      620 +                                                              
      621 +Antes de implementar `data_loader.py`, escrever os seguintes t
          +estes em `tests/test_data_loader.py`. Todos devem falhar inici
          +almente (Red) e passar apos a implementacao (Green).          
      622 +                                                              
      623 +### 11.1 Testes de carregamento basico                        
      624 +                                                              
      625 +```python                                                     
      626 +def test_load_data_returns_dict_with_expected_keys():         
      627 +    """load_data() retorna dict com chaves 'pipeline', 'accoun
          +ts', 'products', 'sales_teams'."""                            
      628 +                                                              
      629 +def test_load_accounts_returns_dataframe_with_expected_columns
          +():                                                           
      630 +    """accounts tem colunas: account, sector, year_established
          +, revenue, employees, office_location, subsidiary_of."""      
      631 +                                                              
      632 +def test_load_products_returns_exactly_7_products():          
      633 +    """products tem exatamente 7 registros."""                
      634 +                                                              
      635 +def test_load_sales_teams_returns_at_least_30_agents():       
      636 +    """sales_teams tem pelo menos 30 registros."""            
      637 +                                                              
      638 +def test_load_pipeline_returns_at_least_8000_records():       
      639 +    """pipeline tem pelo menos 8.000 registros."""            
      640 +```                                                           
      641 +                                                              
      642 +### 11.2 Testes de normalizacao                               
      643 +                                                              
      644 +```python                                                     
      645 +def test_product_gtxpro_normalized_to_gtx_pro():              
      646 +    """No pipeline, 'GTXPro' deve ser normalizado para 'GTX Pr
          +o'."""                                                        
      647 +                                                              
      648 +def test_sector_technolgy_normalized_to_technology():         
      649 +    """Em accounts, 'technolgy' deve ser normalizado para 'tec
          +hnology'."""                                                  
      650 +                                                              
      651 +def test_all_pipeline_products_exist_in_products_table():     
      652 +    """Apos normalizacao, todos os produtos do pipeline existe
          +m na tabela products."""                                      
      653 +```                                                           
      654 +                                                              
      655 +### 11.3 Testes de tipos e conversoes                         
      656 +                                                              
      657 +```python                                                     
      658 +def test_engage_date_is_datetime_type():                      
      659 +    """Coluna engage_date no pipeline deve ser datetime64.""" 
      660 +                                                              
      661 +def test_close_date_is_datetime_type():                       
      662 +    """Coluna close_date no pipeline deve ser datetime64."""  
      663 +                                                              
      664 +def test_close_value_is_numeric_type():                       
      665 +    """Coluna close_value no pipeline deve ser numerica."""   
      666 +```                                                           
      667 +                                                              
      668 +### 11.4 Testes de colunas derivadas                          
      669 +                                                              
      670 +```python                                                     
      671 +def test_is_active_true_for_prospecting_and_engaging():       
      672 +    """is_active == True para deals Prospecting e Engaging, Fa
          +lse para Won e Lost."""                                       
      673 +                                                              
      674 +def test_days_in_stage_nan_for_prospecting():                 
      675 +    """days_in_stage deve ser NaN para todos os deals Prospect
          +ing."""                                                       
      676 +                                                              
      677 +def test_days_in_stage_positive_for_engaging():               
      678 +    """days_in_stage deve ser positivo para deals Engaging."""
      679 +                                                              
      680 +def test_reference_date_is_2017_12_31():                      
      681 +    """get_reference_date() retorna pd.Timestamp('2017-12-31')
          +."""                                                          
      682 +```                                                           
      683 +                                                              
      684 +### 11.5 Testes de integridade referencial                    
      685 +                                                              
      686 +```python                                                     
      687 +def test_all_pipeline_agents_exist_in_sales_teams():          
      688 +    """Todos os sales_agent do pipeline existem em sales_teams
          +."""                                                          
      689 +                                                              
      690 +def test_all_non_null_accounts_exist_in_accounts_table():     
      691 +    """Todos os account nao-nulos do pipeline existem em accou
          +nts."""                                                       
      692 +                                                              
      693 +def test_opportunity_id_is_unique():                          
      694 +    """opportunity_id no pipeline e unico."""                 
      695 +```                                                           
      696 +                                                              
      697 +### 11.6 Testes de nulidade por stage                         
      698 +                                                              
      699 +```python                                                     
      700 +def test_prospecting_has_no_engage_date():                    
      701 +    """Deals Prospecting tem engage_date 100% nulo."""        
      702 +                                                              
      703 +def test_prospecting_has_no_close_date():                     
      704 +    """Deals Prospecting tem close_date 100% nulo."""         
      705 +                                                              
      706 +def test_engaging_has_engage_date():                          
      707 +    """Deals Engaging tem engage_date 100% preenchido."""     
      708 +                                                              
      709 +def test_won_has_positive_close_value():                      
      710 +    """Deals Won tem close_value > 0."""                      
      711 +                                                              
      712 +def test_lost_has_zero_close_value():                         
      713 +    """Deals Lost tem close_value == 0."""                    
      714 +```                                                           
      715 +                                                              
      716 +### 11.7 Testes de enriquecimento (JOINs)                     
      717 +                                                              
      718 +```python                                                     
      719 +def test_pipeline_has_sales_price_after_merge():              
      720 +    """Pipeline enriquecido tem coluna sales_price (do JOIN co
          +m products)."""                                               
      721 +                                                              
      722 +def test_pipeline_has_manager_after_merge():                  
      723 +    """Pipeline enriquecido tem coluna manager (do JOIN com sa
          +les_teams)."""                                                
      724 +                                                              
      725 +def test_pipeline_has_sector_after_merge():                   
      726 +    """Pipeline enriquecido tem coluna sector (do JOIN com acc
          +ounts). NaN quando account e nulo."""                         
      727 +                                                              
      728 +def test_get_active_deals_returns_only_active():              
      729 +    """get_active_deals() retorna apenas Prospecting e Engagin
          +g."""                                                         
      730 +```                                                           

⏺ Agora as outras specs em paralelo.

  Read 1 file (ctrl+o to expand)

⏺ Agora vou adicionar as seções de TDD às specs restantes em paralelo.

⏺ Update(specs/scoring_engine.md)
  ⎿  Added 141 lines
      1117  ```
      1118  
      1119  **Nota:** `constants.py` e `explainability.py` sao adicoes em
             relacao ao PRD original. A separacao de constantes facilita 
            calibracao futura, e o modulo de explicabilidade isola a logi
            ca de geracao de texto da logica de calculo.
      1120 +                                                             
      1121 +---                                                          
      1122 +                                                             
      1123 +## 15. Testes TDD (test_scoring_engine.py)                   
      1124 +                                                             
      1125 +Antes de implementar o scoring engine, escrever os seguintes 
           +testes em `tests/test_scoring_engine.py`. Todos devem falhar 
           +inicialmente (Red) e passar apos a implementacao (Green).    
      1126 +                                                             
      1127 +### 15.1 Testes do Stage Score                               
      1128 +                                                             
      1129 +```python                                                    
      1130 +def test_stage_score_prospecting_returns_30():               
      1131 +    """Prospecting deve retornar score 30."""                
      1132 +                                                             
      1133 +def test_stage_score_engaging_returns_70():                  
      1134 +    """Engaging deve retornar score 70."""                   
      1135 +                                                             
      1136 +def test_stage_score_won_returns_0():                        
      1137 +    """Won nao e deal ativo, retorna 0."""                   
      1138 +                                                             
      1139 +def test_stage_score_unknown_returns_0():                    
      1140 +    """Stage desconhecido retorna 0."""                      
      1141 +```                                                          
      1142 +                                                             
      1143 +### 15.2 Testes do Value Score                               
      1144 +                                                             
      1145 +```python                                                    
      1146 +def test_value_score_gtk500_near_100():                      
      1147 +    """GTK 500 ($26.768) deve ter value_score proximo de 100.
           +"""                                                          
      1148 +                                                             
      1149 +def test_value_score_mg_special_around_39():                 
      1150 +    """MG Special ($55) deve ter value_score em torno de 39."
           +""                                                           
      1151 +                                                             
      1152 +def test_value_score_uses_product_price_when_close_value_null
           +():                                                          
      1153 +    """Quando close_value e null, usa sales_price do produto.
           +"""                                                          
      1154 +                                                             
      1155 +def test_value_score_zero_when_max_value_zero():             
      1156 +    """Se max_value = 0, retorna 0 (sem divisao por zero)."""
      1157 +                                                             
      1158 +def test_value_score_always_between_0_and_100():             
      1159 +    """value_score deve estar sempre entre 0 e 100."""       
      1160 +```                                                          
      1161 +                                                             
      1162 +### 15.3 Testes do Velocity Score                            
      1163 +                                                             
      1164 +```python                                                    
      1165 +def test_velocity_score_healthy_deal():                      
      1166 +    """Deal com 44 dias em Engaging (ratio 0.5) -> score 100,
           + label 'saudavel'."""                                        
      1167 +                                                             
      1168 +def test_velocity_score_at_reference():                      
      1169 +    """Deal com 88 dias em Engaging (ratio 1.0) -> score 100,
           + label 'saudavel'."""                                        
      1170 +                                                             
      1171 +def test_velocity_score_attention():                         
      1172 +    """Deal com 95 dias (ratio ~1.08) -> score ~85, label 'at
           +encao'."""                                                   
      1173 +                                                             
      1174 +def test_velocity_score_alert():                             
      1175 +    """Deal com 120 dias (ratio ~1.36) -> score ~60, label 'a
           +lerta'."""                                                   
      1176 +                                                             
      1177 +def test_velocity_score_zombie():                            
      1178 +    """Deal com 200 dias (ratio ~2.27) -> score ~10, label 'q
           +uase_morto'."""                                              
      1179 +                                                             
      1180 +def test_velocity_score_prospecting_returns_neutral():       
      1181 +    """Deal em Prospecting (sem engage_date) retorna score ne
           +utro."""                                                     
      1182 +                                                             
      1183 +def test_velocity_decay_is_monotonically_decreasing():       
      1184 +    """Score de velocidade deve diminuir conforme ratio aumen
           +ta."""                                                       
      1185 +```                                                          
      1186 +                                                             
      1187 +### 15.4 Testes do Seller Fit Score                          
      1188 +                                                             
      1189 +```python                                                    
      1190 +def test_seller_fit_neutral_when_few_deals():                
      1191 +    """Vendedor com < 5 deals no setor retorna 50 (neutro).""
           +"                                                            
      1192 +                                                             
      1193 +def test_seller_fit_neutral_when_no_sector():                
      1194 +    """Deal sem setor (account null) retorna 50 (neutro).""" 
      1195 +                                                             
      1196 +def test_seller_fit_high_when_above_team_average():          
      1197 +    """Vendedor com WR acima da media do time retorna score >
           + 50."""                                                      
      1198 +                                                             
      1199 +def test_seller_fit_low_when_below_team_average():           
      1200 +    """Vendedor com WR abaixo da media retorna score < 50."""
      1201 +                                                             
      1202 +def test_seller_fit_clamped_at_100():                        
      1203 +    """Multiplicador > 2.0 deve ser clamped, score maximo = 1
           +00."""                                                       
      1204 +                                                             
      1205 +def test_seller_fit_clamped_at_0():                          
      1206 +    """Multiplicador < 0.3 deve ser clamped, score minimo = 0
           +."""                                                         
      1207 +                                                             
      1208 +def test_build_seller_fit_stats_uses_only_closed_deals():    
      1209 +    """Stats devem ser calculadas apenas com deals Won e Lost
           +."""                                                         
      1210 +```                                                          
      1211 +                                                             
      1212 +### 15.5 Testes do Account Health Score                      
      1213 +                                                             
      1214 +```python                                                    
      1215 +def test_account_health_neutral_when_few_deals():            
      1216 +    """Conta com < 3 deals fechados retorna 50 (neutro)."""  
      1217 +                                                             
      1218 +def test_account_health_high_winrate():                      
      1219 +    """Conta com 80% WR e 0 losses recentes -> score 80."""  
      1220 +                                                             
      1221 +def test_account_health_low_with_recent_losses():            
      1222 +    """Conta com WR baixo + losses recentes -> score penaliza
           +do."""                                                       
      1223 +                                                             
      1224 +def test_account_health_penalty_capped_at_30():              
      1225 +    """Penalizacao por losses recentes nao ultrapassa 30 pont
           +os."""                                                       
      1226 +                                                             
      1227 +def test_account_health_score_never_negative():              
      1228 +    """Score nunca fica abaixo de 0."""                      
      1229 +```                                                          
      1230 +                                                             
      1231 +### 15.6 Testes do Engine (integracao)                       
      1232 +                                                             
      1233 +```python                                                    
      1234 +def test_score_pipeline_returns_all_active_deals():          
      1235 +    """score_pipeline() retorna um score para cada deal ativo
           +."""                                                         
      1236 +                                                             
      1237 +def test_score_final_between_0_and_100():                    
      1238 +    """Todos os scores finais estao entre 0 e 100."""        
      1239 +                                                             
      1240 +def test_score_final_no_nan():                               
      1241 +    """Nenhum NaN no score final."""                         
      1242 +                                                             
      1243 +def test_won_and_lost_excluded_from_scoring():               
      1244 +    """Deals Won e Lost nao aparecem no resultado."""        
      1245 +                                                             
      1246 +def test_weighted_components_sum_to_final():                 
      1247 +    """Soma dos componentes ponderados = score final (toleran
           +cia 0.1)."""                                                 
      1248 +                                                             
      1249 +def test_engaging_mean_score_higher_than_prospecting():      
      1250 +    """Score medio de Engaging > score medio de Prospecting."
           +""                                                           
      1251 +                                                             
      1252 +def test_zombie_flag_set_when_ratio_above_2():               
      1253 +    """is_zombie = True quando velocity_ratio >= 2.0."""     
      1254 +                                                             
      1255 +def test_critical_zombie_requires_zombie_and_high_value():   
      1256 +    """is_critical_zombie requer is_zombie AND valor > P75.""
           +"                                                            
      1257 +                                                             
      1258 +def test_score_breakdown_has_all_components():               
      1259 +    """score_breakdown contem stage, expected_value, velocity
           +, seller_fit, account_health."""                             
      1260 +```                                                          

⏺ Update(specs/filters.md)
  ⎿  Added 72 lines
      555  | `sector` | accounts.csv (merge) | str |
      556  | `score` | scoring engine (calculado) | float |
      557  | `is_zombie` | scoring engine (calculado) | bool |
      558 +                                                              
      559 +---                                                           
      560 +                                                              
      561 +## 13. Testes TDD (test_filters.py)                           
      562 +                                                              
      563 +Antes de implementar `filters.py`, escrever os seguintes teste
          +s em `tests/test_filters.py`. Todos devem falhar inicialmente 
          +(Red) e passar apos a implementacao (Green).                  
      564 +                                                              
      565 +### 13.1 Testes da cascata hierarquica                        
      566 +                                                              
      567 +```python                                                     
      568 +def test_manager_options_filtered_by_office_central():        
      569 +    """Selecionar 'Central' retorna apenas Dustin Brinkmann e 
          +Melvin Marxen."""                                             
      570 +                                                              
      571 +def test_manager_options_filtered_by_office_east():           
      572 +    """Selecionar 'East' retorna apenas Cara Losch e Rocco Neu
          +bert."""                                                      
      573 +                                                              
      574 +def test_manager_options_all_when_office_todos():             
      575 +    """Selecionar 'Todos' retorna os 6 managers."""           
      576 +                                                              
      577 +def test_agent_options_filtered_by_manager():                 
      578 +    """Selecionar manager 'Cara Losch' retorna apenas os 6 ven
          +dedores dela."""                                              
      579 +                                                              
      580 +def test_agent_options_all_when_manager_todos():              
      581 +    """Selecionar manager 'Todos' com regiao 'East' retorna to
          +dos os vendedores do East."""                                 
      582 +```                                                           
      583 +                                                              
      584 +### 13.2 Testes do apply_filters                              
      585 +                                                              
      586 +```python                                                     
      587 +def test_apply_filters_office_filters_by_regional_office():   
      588 +    """Filtrar por office='Central' retorna apenas deals de ve
          +ndedores do Central."""                                       
      589 +                                                              
      590 +def test_apply_filters_manager_filters_by_manager():          
      591 +    """Filtrar por manager='Cara Losch' retorna apenas deals d
          +os vendedores dela."""                                        
      592 +                                                              
      593 +def test_apply_filters_agent_filters_by_sales_agent():        
      594 +    """Filtrar por agent retorna apenas deals daquele vendedor
          +."""                                                          
      595 +                                                              
      596 +def test_apply_filters_products_multiselect():                
      597 +    """Filtrar por lista de produtos retorna apenas deals com 
          +esses produtos."""                                            
      598 +                                                              
      599 +def test_apply_filters_score_range():                         
      600 +    """Filtrar por score_min=50, score_max=80 retorna deals co
          +m score nessa faixa."""                                       
      601 +                                                              
      602 +def test_apply_filters_zombie_mode_apenas_zumbis():           
      603 +    """Filtrar 'Apenas zumbis' retorna so deals com is_zombie 
          +== True."""                                                   
      604 +                                                              
      605 +def test_apply_filters_zombie_mode_ocultar_zumbis():          
      606 +    """Filtrar 'Ocultar zumbis' retorna so deals com is_zombie
          + == False."""                                                 
      607 +                                                              
      608 +def test_apply_filters_combined_and_logic():                  
      609 +    """Multiplos filtros combinam com logica AND (intersecao).
          +"""                                                           
      610 +                                                              
      611 +def test_apply_filters_empty_products_returns_all():          
      612 +    """Lista vazia de produtos trata como 'todos selecionados'
          +."""                                                          
      613 +                                                              
      614 +def test_apply_filters_empty_sectors_returns_all():           
      615 +    """Lista vazia de setores trata como 'todos selecionados'.
          +"""                                                           
      616 +                                                              
      617 +def test_apply_filters_no_filters_returns_all():              
      618 +    """Sem filtros ativos retorna todos os deals."""          
      619 +```                                                           
      620 +                                                              
      621 +### 13.3 Testes de edge cases                                 
      622 +                                                              
      623 +```python                                                     
      624 +def test_apply_filters_returns_empty_when_no_match():         
      625 +    """Combinacao impossivel retorna DataFrame vazio (sem erro
          +)."""                                                         
      626 +                                                              
      627 +def test_filter_state_dataclass_has_expected_fields():        
      628 +    """FilterState tem todos os campos: office, manager, agent
          +, products, sectors, score_min, score_max, zombie_mode."""    
      629 +```                                                           

⏺ Update(specs/deal_zombie.md)
  ⎿  Added 87 lines
      614  | Flag independente do score | Integrar zumbi como componente 
           do score | O Zumbi e uma comunicacao binaria ("este deal esta 
           morto"). O score ja reflete o problema via decay de velocidade
           . A flag adiciona clareza sem redundancia. |
      615  | Conta Recorrente Lost com threshold de 2 | Usar win rate da 
           conta (< 50%) | O threshold absoluto e mais intuitivo para o m
           anager. "Esta conta ja perdeu 15 deals" e mais acionavel que "
           win rate de 42%". |
      616  | Labels em portugues na UI | Labels em ingles | O usuario fin
           al e vendedor brasileiro. Linguagem natural em PT-BR e requisi
           to do projeto. |
      617 +                                                              
      618 +---                                                           
      619 +                                                              
      620 +## 15. Testes TDD (test_deal_zombie.py)                       
      621 +                                                              
      622 +Antes de implementar `deal_zombie.py`, escrever os seguintes t
          +estes em `tests/test_deal_zombie.py`. Todos devem falhar inici
          +almente (Red) e passar apos a implementacao (Green).          
      623 +                                                              
      624 +### 15.1 Testes de classificacao de zumbi                     
      625 +                                                              
      626 +```python                                                     
      627 +def test_engaging_100_days_not_zombie():                      
      628 +    """Deal Engaging com 100 dias (ratio 1.14) NAO e zumbi."""
      629 +                                                              
      630 +def test_engaging_180_days_is_zombie():                       
      631 +    """Deal Engaging com 180 dias (ratio 2.05) E zumbi."""    
      632 +                                                              
      633 +def test_engaging_270_days_is_chronic_zombie():               
      634 +    """Deal Engaging com 270 dias (ratio 3.07) e Zumbi Cronico
          +."""                                                          
      635 +                                                              
      636 +def test_prospecting_never_classified_as_zombie():            
      637 +    """Deals em Prospecting NAO podem ser classificados como Z
          +umbi (sem dados temporais)."""                                
      638 +                                                              
      639 +def test_zombie_threshold_is_176_days():                      
      640 +    """Threshold para Engaging = 2 * 88 (P75) = 176 dias."""  
      641 +```                                                           
      642 +                                                              
      643 +### 15.2 Testes de zumbi critico                              
      644 +                                                              
      645 +```python                                                     
      646 +def test_zombie_with_gtk500_is_critical():                    
      647 +    """Zumbi com GTK 500 ($26.768) provavelmente e Zumbi Criti
          +co (valor > P75)."""                                          
      648 +                                                              
      649 +def test_zombie_with_mg_special_not_critical():               
      650 +    """Zumbi com MG Special ($55) NAO e Zumbi Critico (valor <
          + P75)."""                                                     
      651 +                                                              
      652 +def test_non_zombie_never_critical():                         
      653 +    """Deal nao-zumbi nunca e classificado como Zumbi Critico.
          +"""                                                           
      654 +```                                                           
      655 +                                                              
      656 +### 15.3 Testes de conta recorrente lost                      
      657 +                                                              
      658 +```python                                                     
      659 +def test_account_0_losses_not_recurrent():                    
      660 +    """Conta com 0 losses nao e recorrente."""                
      661 +                                                              
      662 +def test_account_1_loss_not_recurrent():                      
      663 +    """Conta com 1 loss nao e recorrente."""                  
      664 +                                                              
      665 +def test_account_2_losses_is_recurrent():                     
      666 +    """Conta com 2 losses E recorrente."""                    
      667 +                                                              
      668 +def test_account_10_losses_is_high_risk():                    
      669 +    """Conta com 10 losses e recorrente E alto risco."""      
      670 +```                                                           
      671 +                                                              
      672 +### 15.4 Testes de valor estimado                             
      673 +                                                              
      674 +```python                                                     
      675 +def test_estimated_value_uses_close_value_when_available():   
      676 +    """Se close_value > 0, usar close_value."""               
      677 +                                                              
      678 +def test_estimated_value_uses_product_price_when_no_close_valu
          +e():                                                          
      679 +    """Se close_value null, usar preco de lista do produto."""
      680 +```                                                           
      681 +                                                              
      682 +### 15.5 Testes de resumo (get_zombie_summary)                
      683 +                                                              
      684 +```python                                                     
      685 +def test_zombie_summary_has_expected_keys():                  
      686 +    """Resumo contem: total_active_deals, total_zombies, pct_z
          +ombies, pipeline_total, pipeline_inflated."""                 
      687 +                                                              
      688 +def test_zombie_summary_pct_consistent():                     
      689 +    """pct_zombies = total_zombies / total_active_deals * 100.
          +"""                                                           
      690 +                                                              
      691 +def test_zombie_summary_pipeline_inflated_sum_of_zombie_values
          +():                                                           
      692 +    """pipeline_inflated = soma dos valores estimados dos deal
          +s zumbis."""                                                  
      693 +```                                                           
      694 +                                                              
      695 +### 15.6 Testes de sanidade com dados reais                   
      696 +                                                              
      697 +```python                                                     
      698 +def test_approximately_47_percent_engaging_are_zombies():     
      699 +    """Com referencia P75 (88d) e threshold 2x, ~40-55% dos de
          +als Engaging sao zumbis."""                                   
      700 +                                                              
      701 +def test_classify_zombies_adds_expected_columns():            
      702 +    """classify_zombies retorna DataFrame com colunas: is_zomb
          +ie, zombie_severity, zombie_label, time_ratio, estimated_value
          +, is_zombie_critical."""                                      
      703 +```                                                           

⏺ Update(specs/metrics_summary.md)
  ⎿  Added 74 lines
      444  - [ ] Edge cases: estados vazios, vendedor sem historico, pipe
           line zerado
      445  - [ ] Performance: metricas renderizam em < 200ms
      446  - [ ] Cache: `@st.cache_data` nos calculos de referencia
      447 +                                                              
      448 +---                                                           
      449 +                                                              
      450 +## 14. Testes TDD (test_metrics.py)                           
      451 +                                                              
      452 +Antes de implementar `metrics.py`, escrever os seguintes teste
          +s em `tests/test_metrics.py`. Todos devem falhar inicialmente 
          +(Red) e passar apos a implementacao (Green).                  
      453 +                                                              
      454 +### 14.1 Testes de calculo de KPIs                            
      455 +                                                              
      456 +```python                                                     
      457 +def test_count_active_deals_only_prospecting_and_engaging():  
      458 +    """Contagem de deals ativos inclui apenas Prospecting e En
          +gaging."""                                                    
      459 +                                                              
      460 +def test_pipeline_total_uses_estimated_value():               
      461 +    """Valor total usa close_value (Won) ou sales_price (ativo
          +s) como proxy."""                                             
      462 +                                                              
      463 +def test_zombie_count_matches_is_zombie_flag():               
      464 +    """Contagem de zumbis = len(df[df['is_zombie'] == True])."
          +""                                                            
      465 +                                                              
      466 +def test_win_rate_calculated_from_won_and_lost():             
      467 +    """Win rate = Won / (Won + Lost), usando deals historicos.
          +"""                                                           
      468 +                                                              
      469 +def test_win_rate_returns_none_when_no_closed_deals():        
      470 +    """Win rate e None quando nao ha deals fechados no filtro.
          +"""                                                           
      471 +```                                                           
      472 +                                                              
      473 +### 14.2 Testes de formatacao de moeda                        
      474 +                                                              
      475 +```python                                                     
      476 +def test_format_currency_millions():                          
      477 +    """1.200.000 -> '$1.2M'."""                               
      478 +                                                              
      479 +def test_format_currency_thousands():                         
      480 +    """45.000 -> '$45K'."""                                   
      481 +                                                              
      482 +def test_format_currency_small():                             
      483 +    """55 -> '$55'."""                                        
      484 +```                                                           
      485 +                                                              
      486 +### 14.3 Testes de distribuicao de score                      
      487 +                                                              
      488 +```python                                                     
      489 +def test_score_distribution_has_4_faixas():                   
      490 +    """Distribuicao retorna exatamente 4 faixas: Critico, Risc
          +o, Atencao, Alta."""                                          
      491 +                                                              
      492 +def test_score_distribution_counts_sum_to_total():            
      493 +    """Soma das contagens das faixas = total de deals."""     
      494 +                                                              
      495 +def test_score_80_falls_in_alta_prioridade():                 
      496 +    """Score 80 cai na faixa 'Alta (80-100)'."""              
      497 +                                                              
      498 +def test_score_39_falls_in_critico():                         
      499 +    """Score 39 cai na faixa 'Critico (0-39)'."""             
      500 +```                                                           
      501 +                                                              
      502 +### 14.4 Testes de pipeline health                            
      503 +                                                              
      504 +```python                                                     
      505 +def test_pipeline_health_sums_to_total_deals():               
      506 +    """Saudaveis + Zumbis = total de deals."""                
      507 +                                                              
      508 +def test_pipeline_health_zero_zombies():                      
      509 +    """Quando nao ha zumbis, donut mostra 100% saudavel."""   
      510 +```                                                           
      511 +                                                              
      512 +### 14.5 Testes de edge cases                                 
      513 +                                                              
      514 +```python                                                     
      515 +def test_metrics_handle_empty_dataframe():                    
      516 +    """DataFrame vazio nao causa erro, mostra zeros."""       
      517 +                                                              
      518 +def test_metrics_handle_single_deal():                        
      519 +    """DataFrame com 1 deal funciona corretamente."""         
      520 +```                                                           

⏺ Update(specs/next_best_action.md)  ⎿  Added 86 lines
      685  | `components/deal_detail.py` | Renderizar card de NBA expandi
           do |
      686  | `components/pipeline_view.py` | Coluna NBA resumida na tabel
           a |
      687  | `utils/formatters.py` | Formatacao de moeda, percentual, dia
           s |
      688 +                                                              
      689 +---                                                           
      690 +                                                              
      691 +## 12. Testes TDD (test_nba.py)                               
      692 +                                                              
      693 +Antes de implementar `nba.py`, escrever os seguintes testes em
          + `tests/test_nba.py`. Todos devem falhar inicialmente (Red) e 
          +passar apos a implementacao (Green).                          
      694 +                                                              
      695 +### 12.1 Testes de regras individuais                         
      696 +                                                              
      697 +```python                                                     
      698 +def test_nba01_deal_parado_fires_when_ratio_above_1():        
      699 +    """NBA-01 dispara quando 1.0 < ratio <= 1.5 (ex: 95 dias E
          +ngaging)."""                                                  
      700 +                                                              
      701 +def test_nba01_does_not_fire_below_reference():               
      702 +    """NBA-01 NAO dispara quando ratio <= 1.0."""             
      703 +                                                              
      704 +def test_nba02_deal_em_risco_fires_when_ratio_above_1_5():    
      705 +    """NBA-02 dispara quando 1.5 < ratio <= 2.0 (ex: 140 dias 
          +Engaging)."""                                                 
      706 +                                                              
      707 +def test_nba04_seller_fit_fires_when_wr_below_80pct_team():   
      708 +    """NBA-04 dispara quando seller_wr < team_wr * 0.8 e deals
          + >= 5."""                                                     
      709 +                                                              
      710 +def test_nba04_does_not_fire_with_few_deals():                
      711 +    """NBA-04 NAO dispara quando vendedor tem < 5 deals no set
          +or."""                                                        
      712 +                                                              
      713 +def test_nba05_conta_problematica_fires_with_2_losses():      
      714 +    """NBA-05 dispara quando conta tem >= 2 losses."""        
      715 +                                                              
      716 +def test_nba05_does_not_fire_with_1_loss():                   
      717 +    """NBA-05 NAO dispara com apenas 1 loss."""               
      718 +                                                              
      719 +def test_nba06_prioridade_maxima_fires_for_healthy_high_value(
          +):                                                            
      720 +    """NBA-06 dispara: Engaging + valor >= P75 + dias <= 88.""
          +"                                                             
      721 +                                                              
      722 +def test_nba06b_prospecting_alto_valor():                     
      723 +    """NBA-06B dispara: Prospecting + valor >= P75."""        
      724 +```                                                           
      725 +                                                              
      726 +### 12.2 Testes de resolucao de prioridades                   
      727 +                                                              
      728 +```python                                                     
      729 +def test_highest_priority_rule_wins():                        
      730 +    """Quando multiplas regras se aplicam, a de menor priorida
          +de numerica e a principal."""                                 
      731 +                                                              
      732 +def test_nba05_overrides_nba06():                             
      733 +    """NBA-05 (Conta Problematica) prevalece sobre NBA-06 (Pri
          +oridade Maxima)."""                                           
      734 +                                                              
      735 +def test_secondary_actions_limited_to_2():                    
      736 +    """Acoes secundarias sao limitadas a no maximo 2."""      
      737 +```                                                           
      738 +                                                              
      739 +### 12.3 Testes de deals zumbi                                
      740 +                                                              
      741 +```python                                                     
      742 +def test_zombie_deal_receives_nba_zb():                       
      743 +    """Deal com ratio > 2.0 recebe NBA-ZB (nao NBA-01 ou NBA-0
          +2)."""                                                        
      744 +                                                              
      745 +def test_zombie_nba_includes_days_and_ratio():                
      746 +    """Mensagem do zumbi inclui dias no stage e ratio."""     
      747 +```                                                           
      748 +                                                              
      749 +### 12.4 Testes de edge cases                                 
      750 +                                                              
      751 +```python                                                     
      752 +def test_deal_without_any_rule_gets_fallback():               
      753 +    """Deal sem nenhuma regra aplicavel recebe mensagem fallba
          +ck neutra."""                                                 
      754 +                                                              
      755 +def test_prospecting_without_temporal_data_skips_time_rules():
      756 +    """Deals Prospecting nao recebem NBA-01, NBA-02, NBA-ZB.""
          +"                                                             
      757 +                                                              
      758 +def test_deal_with_null_account_skips_nba05():                
      759 +    """Deal sem conta nao dispara NBA-05."""                  
      760 +                                                              
      761 +def test_nba_result_has_acao_principal():                     
      762 +    """NBAResult sempre tem acao_principal (nunca None)."""   
      763 +```                                                           
      764 +                                                              
      765 +### 12.5 Testes com dados reais                               
      766 +                                                              
      767 +```python                                                     
      768 +def test_hottechi_deals_receive_nba05():                      
      769 +    """Deals na conta Hottechi (82 losses) recebem NBA-05.""" 
      770 +                                                              
      771 +def test_gtk500_engaging_healthy_receives_nba06():            
      772 +    """Deal GTK 500 em Engaging ha 50 dias recebe NBA-06 (Prio
          +ridade Maxima)."""                                            
      773 +```                                                           

⏺ Agora as duas specs restantes: pipeline_view.md e ui_ux.md.

  Read 2 files (ctrl+o to expand)

⏺ Update(specs/pipeline_view.md)
  ⎿  Added 70 lines
      549  - [ ] Nenhum erro no console ao navegar entre deals
      550  - [ ] Valores monetarios formatados corretamente ($26.7K, nao 
           26768.0)
      551  - [ ] Dias no stage calculados a partir de 2017-12-31 (DATA_RE
           F)
      552 +                                                              
      553 +---                                                           
      554 +                                                              
      555 +## 13. Testes TDD (test_pipeline_view.py)                     
      556 +                                                              
      557 +Antes de implementar `pipeline_view.py` e `deal_detail.py`, es
          +crever os seguintes testes em `tests/test_pipeline_view.py`. T
          +odos devem falhar inicialmente (Red) e passar apos a implement
          +acao (Green).                                                 
      558 +                                                              
      559 +### 13.1 Testes de dados da tabela                            
      560 +                                                              
      561 +```python                                                     
      562 +def test_pipeline_view_only_active_deals():                   
      563 +    """Tabela contem apenas deals Prospecting e Engaging (nao 
          +Won/Lost)."""                                                 
      564 +                                                              
      565 +def test_pipeline_view_sorted_by_score_desc():                
      566 +    """Deals ordenados por score descendente por padrao."""   
      567 +                                                              
      568 +def test_pipeline_view_has_expected_columns():                
      569 +    """Tabela tem colunas: Score, Deal, Conta, Produto, Valor,
          + Stage, Dias no Stage, Vendedor."""                           
      570 +                                                              
      571 +def test_pipeline_view_displays_sem_conta_when_null():        
      572 +    """Quando account e null, exibir 'Sem conta'."""          
      573 +                                                              
      574 +def test_pipeline_view_value_uses_proxy_for_active():         
      575 +    """Valor exibido usa sales_price como proxy para deals ati
          +vos (sem close_value)."""                                     
      576 +                                                              
      577 +def test_pipeline_view_days_dash_for_prospecting():           
      578 +    """Dias no Stage mostra '—' para deals Prospecting (sem en
          +gage_date)."""                                                
      579 +```                                                           
      580 +                                                              
      581 +### 13.2 Testes de codigo de cores                            
      582 +                                                              
      583 +```python                                                     
      584 +def test_score_color_green_for_80_plus():                     
      585 +    """Score >= 80 retorna cor verde (#2ecc71)."""            
      586 +                                                              
      587 +def test_score_color_yellow_for_60_to_79():                   
      588 +    """Score 60-79 retorna cor amarela (#f1c40f)."""          
      589 +                                                              
      590 +def test_score_color_orange_for_40_to_59():                   
      591 +    """Score 40-59 retorna cor laranja (#e67e22)."""          
      592 +                                                              
      593 +def test_score_color_red_for_below_40():                      
      594 +    """Score < 40 retorna cor vermelha (#e74c3c)."""          
      595 +```                                                           
      596 +                                                              
      597 +### 13.3 Testes do deal detail                                
      598 +                                                              
      599 +```python                                                     
      600 +def test_deal_detail_score_breakdown_sums_to_total():         
      601 +    """Soma dos componentes ponderados = score total (toleranc
          +ia 0.1)."""                                                   
      602 +                                                              
      603 +def test_deal_detail_has_explanation_text():                  
      604 +    """Deal detail inclui texto de explicacao nao-vazio."""   
      605 +                                                              
      606 +def test_deal_detail_has_next_action():                       
      607 +    """Deal detail inclui next best action nao-vazia."""      
      608 +                                                              
      609 +def test_deal_detail_zombie_flag_shown_when_zombie():         
      610 +    """Deal zumbi mostra flag visual de alerta."""            
      611 +```                                                           
      612 +                                                              
      613 +### 13.4 Testes de formatacao                                 
      614 +                                                              
      615 +```python                                                     
      616 +def test_format_value_abbreviation():                         
      617 +    """26768 -> '$26.7K', 550 -> '$550', 55 -> '$55'."""      
      618 +                                                              
      619 +def test_velocity_status_vocabulary():                        
      620 +    """Ratio <= 1.0 -> 'saudavel', 1.0-1.2 -> 'no limite', > 2
          +.0 -> 'zumbi'."""                                             
      621 +```                                                           

⏺ Update(specs/ui_ux.md)
  ⎿  Added 77 lines
       959  - [ ] Tooltips em filtros e metricas
       960  - [ ] Caption descritivo abaixo de graficos
       961  - [ ] Contraste adequado em todas as cores
       962 +                                                             
       963 +---                                                          
       964 +                                                             
       965 +## 13. Testes TDD (test_formatters.py)                       
       966 +                                                             
       967 +Antes de implementar `utils/formatters.py`, escrever os segui
           +ntes testes em `tests/test_formatters.py`. Todos devem falhar
           + inicialmente (Red) e passar apos a implementacao (Green).   
       968 +                                                             
       969 +### 13.1 Testes de formatacao de moeda                       
       970 +                                                             
       971 +```python                                                    
       972 +def test_formatar_valor_milhoes():                           
       973 +    """1_200_000 -> '$1.2M'."""                              
       974 +                                                             
       975 +def test_formatar_valor_milhares():                          
       976 +    """26_768 -> '$26.8K' ou '$27K'."""                      
       977 +                                                             
       978 +def test_formatar_valor_centenas():                          
       979 +    """550 -> '$550'."""                                     
       980 +                                                             
       981 +def test_formatar_valor_dezenas():                           
       982 +    """55 -> '$55'."""                                       
       983 +                                                             
       984 +def test_formatar_valor_zero():                              
       985 +    """0 -> '$0'."""                                         
       986 +```                                                          
       987 +                                                             
       988 +### 13.2 Testes de formatacao de percentual                  
       989 +                                                             
       990 +```python                                                    
       991 +def test_formatar_percentual_normal():                       
       992 +    """0.632 -> '63.2%'."""                                  
       993 +                                                             
       994 +def test_formatar_percentual_zero():                         
       995 +    """0.0 -> '0.0%'."""                                     
       996 +                                                             
       997 +def test_formatar_percentual_cem():                          
       998 +    """1.0 -> '100.0%'."""                                   
       999 +```                                                          
      1000 +                                                             
      1001 +### 13.3 Testes de formatacao de dias                        
      1002 +                                                             
      1003 +```python                                                    
      1004 +def test_formatar_dias_positivo():                           
      1005 +    """45 -> '45 dias'."""                                   
      1006 +                                                             
      1007 +def test_formatar_dias_singular():                           
      1008 +    """1 -> '1 dia'."""                                      
      1009 +```                                                          
      1010 +                                                             
      1011 +### 13.4 Testes de cor por score                             
      1012 +                                                             
      1013 +```python                                                    
      1014 +def test_cor_por_score_verde():                              
      1015 +    """Score 85 -> '#2ecc71' (verde)."""                     
      1016 +                                                             
      1017 +def test_cor_por_score_amarelo():                            
      1018 +    """Score 65 -> '#f1c40f' (amarelo)."""                   
      1019 +                                                             
      1020 +def test_cor_por_score_laranja():                            
      1021 +    """Score 45 -> '#e67e22' (laranja)."""                   
      1022 +                                                             
      1023 +def test_cor_por_score_vermelho():                           
      1024 +    """Score 20 -> '#e74c3c' (vermelho)."""                  
      1025 +```                                                          
      1026 +                                                             
      1027 +### 13.5 Testes de badge HTML                                
      1028 +                                                             
      1029 +```python                                                    
      1030 +def test_badge_html_zumbi():                                 
      1031 +    """badge_html('Zumbi', 'zumbi') retorna HTML com classe b
           +adge-zumbi."""                                               
      1032 +                                                             
      1033 +def test_badge_html_saudavel():                              
      1034 +    """badge_html('OK', 'saudavel') retorna HTML com classe b
           +adge-saudavel."""                                            
      1035 +                                                             
      1036 +def test_score_html_aplica_cor_correta():                    
      1037 +    """score_html(85) retorna HTML com classe score-verde."""
      1038 +```                                                          

⏺ Pronto. Aqui o resumo do que foi feito:

  CLAUDE.md — Adicionada seção "TDD — Test-Driven Development (OBRIGATÓRIO)"
  com:
  - Fluxo Red → Green → Refactor obrigatório
  - 7 regras invioláveis (nunca burlar testes, nunca fingir que passaram, nunca
  manipular terminal, etc.)
  - Estrutura de arquivos de teste (tests/test_*.py)
  - Comando para rodar testes

  Cada spec recebeu sua seção de testes TDD com casos concretos:

  Spec: data_model.md
  Seção: §11
  Arquivo de teste: test_data_loader.py
  Testes: 19 testes (carregamento, normalização, tipos, JOINs, nulidade)
  ────────────────────────────────────────
  Spec: scoring_engine.md
  Seção: §15
  Arquivo de teste: test_scoring_engine.py
  Testes: 30 testes (stage, value, velocity, seller fit, account health,
    integração)
  ────────────────────────────────────────
  Spec: deal_zombie.md
  Seção: §15
  Arquivo de teste: test_deal_zombie.py
  Testes: 15 testes (classificação, zumbi crítico, conta recorrente, resumo)
  ────────────────────────────────────────
  Spec: filters.md
  Seção: §13
  Arquivo de teste: test_filters.py
  Testes: 15 testes (cascata, apply_filters, edge cases)
  ────────────────────────────────────────
  Spec: metrics_summary.md
  Seção: §14
  Arquivo de teste: test_metrics.py
  Testes: 13 testes (KPIs, formatação, distribuição, pipeline health)
  ────────────────────────────────────────
  Spec: next_best_action.md
  Seção: §12
  Arquivo de teste: test_nba.py
  Testes: 16 testes (regras individuais, prioridades, zumbis, edge cases)
  ────────────────────────────────────────
  Spec: pipeline_view.md
  Seção: §13
  Arquivo de teste: test_pipeline_view.py
  Testes: 12 testes (dados, cores, deal detail, formatação)
  ────────────────────────────────────────
  Spec: ui_ux.md
  Seção: §13
  Arquivo de teste: test_formatters.py
  Testes: 14 testes (moeda, percentual, dias, cores, badges)

✻ Brewed for 3m 45s