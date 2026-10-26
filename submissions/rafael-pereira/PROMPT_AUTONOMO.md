/anthropic-skills:opus-plan


## 1. Fontes (leia tudo antes de planejar)
- Esta pasta: os CSVs originais do Kaggle (accounts, products, sales_teams, sales_pipeline, metadata).
- kit-lead-scorer/:
  - CLAUDE.md: regras e as 7 decisões já fechadas. São obrigatórias.
  - docs/briefing.md: achados e números da fase 0.
  - PROMPTS.md: especificação detalhada dos blocos 0 a 7. Use como especificação de cada etapa.
  - GUIA.md: armadilhas e checklist final.
  - process-log/: a fase 0, já registrada, e os scripts de análise.
- Repositório https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge: README.md, challenges/build-003-lead-scorer/README.md, submission-guide.md, CONTRIBUTING.md e templates/submission-template.md.

## 2. Setup
1. Se `gh auth status` estiver ok, rode `gh repo fork Gestao-Quatro-Ponto-Zero/ai-master-challenge --clone` dentro desta pasta. Se não estiver, rode git clone do repositório original. Em seguida, crie a branch `submission/rafael-pereira`.
2. Copie o conteúdo de kit-lead-scorer/ para submissions/rafael-pereira/ e os 4 CSVs para submissions/rafael-pereira/solution/data/raw/.
3. ATENÇÃO: o .gitignore do repositório ignora submissions/. Use sempre `git add -f`.
4. Detecte o Python disponível (`python` ou `py`). Crie um venv fora do que vai para o git e instale o requirements.

## 3. Execução
Execute os blocos 0 a 6 do PROMPTS.md em ordem, com um commit por bloco ("bloco N: ..."). Em todo bloco, atualize docs/DECISIONS.md e escreva process-log/NN_bloco-N.md.

Os checkpoints que no PROMPTS.md dizem "espere meu ok" viram autoverificações registradas no log:
- **Bloco 1:** responda você mesmo às 4 perguntas abertas do briefing (seção 9), justificando cada resposta.
- **Bloco 2:** decida 2a, 2b e 2c com base nos números e mostre a evidência.
- **Bloco 3:**
  - Antes de codar, faça uma checagem explícita de vazamento: nenhuma informação posterior à data T pode entrar no treino.
  - Compare o score com os 3 baselines do PROMPTS.md (valor, data mais recente e aleatório).
  - Se o score não bater os baselines, ajuste uma única vez. Se ainda assim não bater, documente com honestidade. Não maquie resultado.
- **Bloco 4:**
  - Abra a página em file:// com Playwright (headless). Confirme que ela carrega sem erros no console, que os filtros funcionam e que os totais batem com SCORING.md.
  - Confira o layout em 390px e em 1280px de largura e salve os screenshots em process-log/screenshots/.
  - Faça uma passada como "vendedor na segunda de manhã": liste 3 atritos reais, corrija e tire screenshots de antes e depois.
- **Bloco 6:**
  - Rode a revisão independente com um subagente de contexto limpo, conforme o PROMPTS.md.
  - Corrija os critérios com nota ≤3 e rode uma segunda revisão.
  - Salve as duas revisões em process-log/06_revisao-independente.md.

## 4. Regras do process log (inegociáveis)
- Registre o que realmente aconteceu nesta execução: erros, testes que falharam, hipóteses descartadas, versões refeitas e o antes/depois. Essa é a evidência de iteração que a banca procura.
- Não invente intervenções minhas. Decisões desta execução levam a marca "decisão autônoma do Claude". A fase 0 (process-log/00_fase0_exploracao.md) contém as minhas decisões reais: preserve-a como está.
- No README, a seção "O que eu adicionei que a IA sozinha não faria" deve ser apenas um rascunho, iniciado por "[RASCUNHO — Rafael revisar]", baseado na fase 0.
- Todo número na documentação ou na interface sai de um script reprodutível.
- Sobre mim: Rafael Pereira, https://www.linkedin.com/in/rafael-pereira-30122003-, Challenge 003.

## 5. Definição de pronto (verifique tudo antes de encerrar)
- [ ] `pytest` passa e `python -m scorer.build` regenera data.js, os briefs e os snapshots do zero.
- [ ] solution/app/index.html abre por duplo-clique, sem servidor e sem erros no console.
- [ ] O README segue templates/submission-template.md, com executive summary de até 5 frases.
- [ ] docs/ contém SCOPE.md, DATA_QUALITY.md, SCORING.md (com a tabela de backtest contra os 3 baselines em pelo menos 2 cortes), MODEL_CARD.md e DECISIONS.md.
- [ ] process-log/ tem os blocos 0 a 6, os screenshots e as duas revisões independentes.
- [ ] `git status` mostra que nada fora de submissions/rafael-pereira/ foi alterado.

## 6. Pare antes de publicar
Não faça push nem abra o PR, porque a submissão sai no meu nome. Deixe tudo pronto:
- os commits locais;
- o texto do PR em kit-lead-scorer/PR.md, fora do repositório, com o título "[Submission] Rafael Pereira — Challenge 003";
- os comandos exatos para push, para ativar o GitHub Pages (branch submission/rafael-pereira, pasta root) e para rodar o `gh pr create`.

## 7. Entrega final
Responda com:
1. Como abrir a ferramenta (caminho local e a URL futura do GitHub Pages).
2. A tabela de backtest.
3. As 5 decisões principais.
4. As limitações.
5. A minha lista de ações: revisar o rascunho do README, fazer o push, ativar o Pages e abrir o PR.
