## 1. Setup & Dependencies

- [x] 1.1 Add streamlit, pandas, plotly to requirements.txt
- [x] 1.2 Install dependencies and verify import

## 2. Data Loading & EDA

- [x] 2.1 Load all 4 CSVs into pandas, inspect dtypes and nulls
- [x] 2.2 Merge datasets (pipeline + accounts + products + sales_teams)
- [x] 2.3 EDA: win rates by seller, sector, product; stage distribution; time-in-stage analysis
- [x] 2.4 Calibrate scoring weights based on EDA findings

## 3. Scoring Engine
- [x] 3.1 Implement `src/scorer.py` with feature extraction functions
- [x] 3.2 Implement score computation with weighted features
- [x] 3.3 Implement historical win rate (seller + sector) with fallback logic
- [x] 3.4 Implement normalization and days-in-stage penalty
- [x] 3.5 Test scoring on sample deals and validate range 0–100

- [x] 4.1 Create `src/app.py` with Streamlit multi-tab layout
- [x] 4.2 Implement sidebar filters (seller, manager, region, stage, min score)
- [x] 4.3 Implement Pipeline tab with scored deal list sorted by score
- [x] 4.4 Implement score color coding (green/yellow/red bars)
- [x] 4.5 Implement top-level metrics (total deals, value, avg score)
## 5. Explainability

- [x] 5.1 Implement expandable score breakdown in Pipeline tab rows
- [x] 5.2 Implement Deal Detail tab with deal selector and full breakdown
- [x] 5.3 Add Plotly horizontal bar chart for factor contributions
- [x] 5.4 Add factor direction indicators (positive/negative vs average)

- [x] 6.1 Implement win rate by seller chart
- [x] 6.2 Implement stage distribution pie chart
- [x] 6.3 Implement average time by stage table
- [x] 6.4 Implement pipeline value by region chart
- [x] 6.5 Ensure sidebar filters apply to all analytics charts

- [x] 7.1 Run `streamlit run src/app.py` and verify all features work
- [x] 7.2 Test all filter combinations
- [x] 7.3 Fill process-log.md with full AI usage documentation (ferramentas, workflow, erros, contribuição humana)
- [x] 7.4 Final review against README quality criteria

- [x] 8.1 Create `submissions/<nome>/` directory with solution/, process-log/, docs/ subdirs
- [x] 8.2 Fill README.md from `templates/submission-template.md` (executive summary, abordagem, resultados, recomendações, limitações)
- [x] 8.3 Copy code (src/, data/, requirements.txt) into solution/
- [x] 8.4 Copy process-log.md and any evidence into process-log/
- [x] 8.5 Add docs/ with design.md reference or architecture notes
- [ ] 8.6 Create git branch `submission/<nome>`, commit, and verify no files outside submissions/ were modified
- [ ] 8.7 Open PR to `main` with title `[Submission] <Nome> — Challenge 003`
