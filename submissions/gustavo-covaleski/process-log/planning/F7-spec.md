# F7 — Comunicação (spec para o Claude Code)

- **Teto:** 35 min. Ao chegar a 42 min (120%), pare e proponha o corte no report.
- **Leia antes:** `CLAUDE.md`; `planning/F0-escopo.md`; todos os `planning/F*-report.md`; `process-log/process-log.md`; `docs/*.md`; `templates/submission-template.md` e `CONTRIBUTING.md` do repositório.
- **Regra central:** todo número dos textos vem de um arquivo de `solution/outputs/` (citado) ou de uma premissa rotulada. Nada de afirmação sobre a experiência profissional do Gustavo: onde for preciso, deixe `[GUSTAVO: …]` para ele preencher.

## Passo 0 — Dano da injeção em amostra maior, só clássico (≤ 5 min)

Em `f5_injecao.py`, com uma função nova e sem mudar os 5 ataques versionados:
- Universo: **todos** os tickets do holdout por grupo que estão na faixa `IA decide` (≈ 13%).
- Aplique os 5 ataques a cada um (≈ 6.200 pares). Só clássico; nenhuma chamada de LLM.
- Conte quantos pares **continuam em `IA decide` com rótulo diferente do original** (dano silencioso) e quantos atingem a categoria-alvo continuando em `IA decide`. Reporte as duas taxas com IC de Wilson 95%, destacando o limite superior.
- Grave em `f5_injecao.json` sob a chave `dano_ampliado`. Não mude a política nem ligue o detector.

## Passo 1 — `docs/memo-diretor.md` (≤ 10 min)

**Uma página, no máximo 400 palavras**, para um Diretor de Operações que lê em 5 minutos. Cada frase com número leva uma nota curta com o arquivo de origem no fim. Estrutura obrigatória:

1. **Decisão pedida** (primeira frase): aprovar um piloto de 4 semanas com três frentes:
   - instrumentar os 5 eventos;
   - colocar a triagem em modo sombra e depois ativar `IA decide` só nas categorias que passaram (Access e Purchase), com `IA sugere` nas categorias da política;
   - escrever com o time a definição das 8 filas;
   - e **não** contratar LLM para classificar.
2. **Por que** (3 a 4 frases):
   - os dados de tempo e CSAT de hoje não permitem achar gargalo (T3 e T5); o problema é medição, não volume (`f2_mde.csv`);
   - a IA decide sozinha em ~13% do volume, com ~98,9% de precisão (`f4_politica_por_categoria.csv` ou o JSON da F4);
   - a taxonomia não se explica sozinha: revisor externo concorda 47%, LLM acerta 26,5%, e o modelo treinado nos rótulos históricos acerta 85% (`revisao_rotulos_adjudicada.csv`, `f3_llm.json`, `f3_classico.json`).
3. **Ganho**, honesto:
   - triagem no cenário A, ~R$ 6,8 mil/ano (faixa de R$ 3,2 mil a R$ 13 mil, `f4_economia.csv`);
   - cenário B, zero;
   - o ganho maior está na faixa `IA sugere` e nas reatribuições evitadas, e os dois serão medidos no piloto.
   - Diga explicitamente que os números de roteamento vêm de 47.837 tickets reais de TI (DS2) e que o volume da operação é premissa.
4. **Risco e controle:**
   - dano silencioso da injeção (passo 0);
   - rollback em segundos com o modo sombra (`docs/producao.md`);
   - o portão de qualidade barra uma versão pior.
5. **Próximas 4 semanas**, uma linha por semana:
   - S1: eventos + modo sombra;
   - S2–S3: medir precisão pelas correções e o tempo de confirmação na faixa `IA sugere`;
   - S4: ativar `IA decide` em Access e Purchase se a meta se confirmar; diagnóstico por canal × prioridade possível em ~3,6 semanas (`f2_mde.csv`).

## Passo 2 — `README.md` da submissão, no template do G4 (≤ 12 min)

Siga as seções de `templates/submission-template.md`, na ordem. Leitura de 5 minutos: o detalhe fica em `docs/`.

- **Sobre mim:** `[GUSTAVO: nome, LinkedIn]`; Challenge 002.
- **Executive Summary:** 3 a 5 frases, coerentes com o memo.
- **Abordagem:** decomposição em fases com portões; regras de decisão fixadas antes de ver o resultado (consequências das armadilhas, critério da Q2, *e* mínimo, regra por categoria, detector de injeção); holdout congelado antes de qualquer modelo.
- **Resultados:** uma tabela de no máximo 12 linhas (achado | número | arquivo). Inclua:
  - 49,30% de resolução antes da 1ª resposta;
  - texto do DS2 pré-processado;
  - vazamento de +0,31 p.p. no agregado e 91,84% × 84,97% localizado;
  - clássico a 85,07%;
  - LLM 26,5% × clássico 69,5% na faixa de abstenção;
  - 18 de 21 casos "original errado" em que o modelo segue o original;
  - faixas 12,98 / 31,41 / 55,61;
  - sensibilidade pós-hoc rotulada como tal;
  - injeção (troca de rótulo e dano em `IA decide`);
  - detector com 4,75% de falso positivo, não adotado;
  - latência p50/p95.
- **Recomendações:** as do memo, priorizadas.
- **Limitações:**
  - DS1 sintético;
  - DS2 pré-processado e de outro domínio (premissa de transferência);
  - um único revisor;
  - *e* dos quase-duplicados usado como estimativa do erro humano;
  - LLM testado com 1 exemplo por categoria e sem temperatura 0 (não determinístico);
  - ganho da faixa `IA sugere` não quantificado;
  - câmbio em `f3_*.json` não usado;
  - retreino de 21,5 s a 78,2 s;
  - tempo total acima do orçamento (ver process log).
- **Process Log — Como usei IA:**
  - tabela de ferramentas (Claude no chat do Projeto: planejamento, crítica e revisão; Claude Code: execução; Claude Haiku 5.5: braço LLM do experimento);
  - workflow em fases;
  - "Onde a IA errou e como corrigi": resuma a tabela do `process-log.md`, sem inventar;
  - "O que eu adicionei": **só** os itens já registrados como decisão do Gustavo no process log, citados; o resto como `[GUSTAVO: …]`.
- **Evidências:** links para `process-log/`, `process-log/chat-exports/`, `process-log/screenshots/`, o histórico de commits.
- **Como rodar:**
  - Python 3.11+, venv e `pip install -r requirements.txt`;
  - baixar os 2 CSVs do Kaggle (links do brief) para `../../../data/` ou definir `DATA_DIR`;
  - `.env` opcional, fora do repositório, só para os scripts de LLM;
  - ordem dos scripts por fase;
  - `pytest solution/tests -q`;
  - `streamlit run solution/app.py`.
- No fim: `_Submissão enviada em: [GUSTAVO: data]_`.

## Passo 3 — Process log final (≤ 5 min)

- Em `process-log/process-log.md`, acrescente uma tabela de **tempo por fase**: orçado (F0-escopo) × real.
  - Real medido pelo Gustavo: F0 = 60 min; F3a = ~180 min.
  - As demais vêm dos reports, marcadas como "estimativa do Claude Code".
  - Total e estouro.
- Conte as iterações: portões, specs, reports e correções.
- Não preencha nenhuma coluna "Decisão minha" vazia nem a coluna "já vi em produção".
- Copie `planning/F*-spec.md` e `planning/F*-report.md` para `process-log/planning/`. **Antes**, verifique que nenhum deles contém texto de ticket: não pode haver sequência de 8 palavras seguidas igual a um trecho de documento do DS2, nem nome ou e-mail do DS1 (checagem automática). Se algum contiver, não copie esse arquivo e reporte.
- **Não copie** `planning/F1-revisao/`, `planning/F3/` nem `planning/F5/`.

## Passo 4 — Checagens finais

- `pytest solution/tests -q` passa.
- Todo link relativo do README e do memo aponta para um arquivo que existe.
- O memo tem até 400 palavras (conte e reporte).
- `f1_splits.csv` com o mesmo hash.
- Liste os `[GUSTAVO: …]` pendentes no report.

## Passo 5 — Report

`planning/F7-report.md` (formato da seção 8 do `CLAUDE.md`). Linha da F7 no process log com "Decisão minha" vazia. **Nenhum commit, nenhum push, nenhum PR.**
