# Checkpoints de Entrega e Commits

## Objetivo

Usar commits como evidencia de evolucao do trabalho e apoio ao process log. O challenge nao exige provar tempo por commit, mas o historico ajuda a demonstrar iteracao, criterio e uso inteligente das 4-6h recomendadas.

## Politica

- Commits devem representar checkpoints reais, nao commits cosmeticos.
- Cada checkpoint deve deixar a submissao em estado compreensivel.
- Como `submissions/` esta no `.gitignore` do repositorio oficial, usar `git add -f` para incluir os arquivos da entrega.
- Nao alterar arquivos fora de `submissions/kadug/`.

## Sequencia Planejada

1. `chore: scaffold challenge 001 submission`
2. `docs: define analytics-first architecture and delivery plan`
3. `analysis: validate churn dataset schema and joins`
4. `analysis: generate churn findings and risk segments`
5. `docs: write executive diagnosis and process log`
6. `feat: add minimal streamlit churn dashboard`

## Registro no Process Log

Cada commit relevante deve ser citado no process log com:

- decisao tomada;
- evidencia gerada;
- onde a IA ajudou;
- o que foi revisado ou corrigido por julgamento humano.
