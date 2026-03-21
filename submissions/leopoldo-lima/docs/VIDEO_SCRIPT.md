# Roteiro de vídeo — Focus Score Cockpit (CRP-VID-01)

**Duração alvo:** 3–4 minutos · **Idioma:** português (BR) · **Navegador:** Chromium (gravado via Playwright — ver `docs/VIDEO_RUNBOOK.md`).

## 0. Abertura (15–20 s)

- «Este é o Focus Score Cockpit, entrega do Challenge 003 — Lead Scorer.»
- «A app corre em FastAPI com o dataset oficial em CSV; o modo padrão usa dados reais, não mock.»

## 1. Arranque e KPIs (30–40 s)

- Mostrar a página inicial já carregada (KPIs visíveis: total, abertas, ganhas, perdidas, score médio).
- «Os indicadores vêm do mesmo conjunto que alimenta o ranking — não é um dashboard estático.»

## 2. Ranking e filtros (45–60 s)

- Mencionar filtros: escritório regional, estágio do negócio, faixa de prioridade, pesquisa `q`.
- **Aplicar** filtro de estágio (ex.: Prospecção ou Engajamento) e mostrar a contagem de resultados a atualizar.
- «O ranking ordena por score; a primeira linha é o top pick do resultado filtrado.»

## 3. Detalhe e explicabilidade (50–60 s)

- Clicar numa linha do ranking.
- «No painel à direita aparecem resumo comercial e a secção Porque este score? — factores positivos, negativos, alertas e próxima ação sugerida.»
- «Isto vem do motor de scoring configurável em `config/scoring-rules.json` e da camada de narrativa na API.»

## 4. Combobox de gestor (40–50 s)

- Focar o campo «Gestor comercial».
- «Ao focar, a lista completa de gestores aparece; ao digitar, o filtro é incremental — primeiro por prefixo, depois por contém.»
- Digitar 3 letras de um nome existente e mostrar sugestões; opcionalmente mostrar empty state com string improvável.

## 5. Fecho (20–30 s)

- «Código, testes e process log estão no repositório; a demo reproduz-se com `python scripts/tasks.py dev` e o vídeo com o script Chromium documentado.»
- «Obrigado.»

## Notas de produção

- Resolução confortável: 1280×900 (igual ao script de gravação).
- Evitar mostrar URLs com tokens ou `.env`.
- Se o áudio for narração externa, sincronizar cortes com os passos do `scripts/record_demo_chromium.py`.
