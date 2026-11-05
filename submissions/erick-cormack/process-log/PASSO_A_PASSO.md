# Passo a passo — Challenge 003 (Lead Scorer)

Registro de tudo o que fiz, na ordem em que fiz, com o papel da IA em cada etapa. O resumo está no [`README.md`](../README.md); aqui estão os detalhes.

**Legenda:** 🧑 decisão ou ação minha · 🤖 executado pela IA (Claude ou agente do Lovable) · ✅ conferência

---

## Fase 0 — Preparação

1. 🧑 Li o README principal do repositório `Gestao-Quatro-Ponto-Zero/ai-master-challenge` e pedi ao Claude os parâmetros para começar: desafio, identificador da branch, conta do GitHub, prazo e regras de entrega.
2. 🤖 O Claude resumiu os desafios 001 (Churn) e 003 (Lead Scorer), que combinam com meu perfil.
3. 🧑 Escolhi o **003**, porque o entregável é software funcionando, e defini a stack **Lovable + Supabase**.
4. 🤖 Leitura do README do desafio: contexto, dataset (CRM Sales Predictive Analytics, 4 tabelas), entregáveis e critérios de qualidade.

## Fase 1 — Dados

5. 🤖 O Kaggle estava bloqueado no ambiente. Baixei os CSVs de um espelho público no GitHub, fixado num commit:
   `Dargoul-Ayoub/CRM-Sales-Opportunities-Maven-Sales-Challenge@4db6524`.
6. ✅ Contagens idênticas às do README do desafio: 8.800 deals, 85 contas, 7 produtos e 35 vendedores.

## Fase 2 — Análise exploratória (notebook `solution/analise/analise_exploratoria.ipynb`)

7. 🧑 Os primeiros números mostravam taxas de ganho planas. Em vez de começar pelo app, pedi uma análise detalhada antes de construir.
8. 🤖 O Claude escreveu e executou o notebook em 12 etapas:

| Etapa | O que foi feito | Resultado principal |
|---|---|---|
| 1. Carga | Leitura crua das 4 tabelas | `sales_pipeline` é a tabela central |
| 2. Qualidade e integridade | Nulos por estágio, chaves, duplicatas, regras de negócio, grafias | 1.425 abertos sem conta; `GTXPro`, `technolgy`, `Philipines` |
| 3. Limpeza | Função `limpar()` reaproveitável na carga do banco; data de referência | Snapshot em 31/12/2017; 6.711 fechados e 2.089 abertos |
| 4. Funil | Deals e valor por estágio | Taxa de ganho geral de 63,2% (4.238 de 6.711) |
| 5. Atributos estáticos | Taxa de ganho com IC de Wilson e qui² por produto, setor, região, manager, porte e país | Tudo entre ~60% e 65%; nenhum qui² significativo |
| 6. Vendedores | Simulação binomial com 10 mil sorteios; combinações vendedor × produto | Dispersão compatível com acaso (p = 31%) |
| 7. Tempo no pipeline | Ciclo por estágio e chance condicional "sobreviveu X dias" | Perdas nos 14 primeiros dias; teto de 138 dias; 63% → 69% → 76% |
| 8. Sazonalidade | Taxa de ganho por mês do trimestre | 81% no 3º mês, mas depende da data de fechamento (fica fora do score) |
| 9. Valor | Valor fechado ÷ preço de lista | Mediana 1,00; amplitude de US$ 55 a US$ 26.768 |
| 10. Backtest sem vazamento | Taxas históricas com shrinkage bayesiano (k = 20), só com o que se sabia antes; ML com split temporal; AUC com IC | Histórico: AUC 0,457–0,482 (IC abaixo de 0,5); ML: 0,529 e 0,512 |
| 11. Pipeline aberto | Faixas de idade, mês de engajamento dos parados, visão por vendedor e manager | 1.291 de 1.589 parados (81%), US$ 3,2 mi; anomalia do Central |
| 12. Conclusões | Tabela de indicadores e decisões de desenho | Score = chance pela idade × valor; filas de ação; atributos só como contexto |

9. ✅ Conferi os textos de leitura contra as saídas, célula a célula. Erros corrigidos:
   - os ICs de AUC ficam **abaixo** de 0,5, e não "cruzando" 0,5;
   - o Panamá não cruza a média (adicionei a nota de comparações múltiplas);
   - "4% acima de 120% do preço" era, na verdade, 1,9% (80 deals);
   - a hipótese de que o Central era mais disciplinado estava invertida;
   - rótulos sobrepostos nos gráficos foram reposicionados.
10. 🧑 Pedi uma **13ª etapa de robustez**: estatística descritiva, outliers, possíveis erros, censura, correlações e regressão inferencial.
11. 🤖 Resultados da etapa 13:
    - receita e funcionários são assimétricos, mas os 8 outliers são contas grandes legítimas;
    - erros de cadastro: Condax "fundada" em 2017 com deals desde 2016, e 27 grupos (64 deals) de prováveis duplicatas;
    - indícios de dados sintéticos: engajamentos iguais nos 7 dias da semana, e desconto como ruído normal (KS p = 0,57);
    - regressão logística inferencial sem nenhum coeficiente significativo (LR p = 0,82; pseudo-R² 0,0016);
    - correlações com o ganho todas desprezíveis (|Spearman| < 0,02; V de Cramér ≤ 0,07);
    - o teto de 138 dias se mantém nas coortes com mais de 200 dias de observação, então não é efeito de censura.
12. ✅ A regressão logística não convergia; padronizei as variáveis numéricas.
13. 🤖 Exportei o notebook para HTML (`analise_exploratoria.html`) e registrei os achados num resumo em Markdown.

## Fase 3 — Comunicação executiva

14. 🤖 Escrevi o **resumo executivo de uma página para C-level** num doc: "Em 30 segundos", "O que descobrimos", "Onde está o problema", "O que recomendamos" e "Ressalvas".
    Link: https://claude.ai/artifact/9MMx5jPRZnsMCwHHBquL6G

## Fase 4 — Banco de dados (Lovable Cloud / Supabase)

15. 🧑 Escolhi que o Claude conduzisse o Lovable diretamente, em vez de eu colar prompts, sabendo que isso consome créditos do meu workspace.
16. 🤖 Preparei os scripts locais:
    - `scripts/preparar_dados.py`: aplica as correções e gera CSVs limpos e arquivos de carga em `sql/seed/`;
    - `scripts/gabarito_score.py`: reimplementa o score em Pandas, para servir de gabarito independente.
17. 🤖 Criei o projeto no Lovable só com a estrutura base (título, subtítulo e navegação), sem banco nem lógica. Depois ativei o banco.
18. 🤖 Apliquei o esquema (`sql/01_schema.sql`):
    - tabelas `products`, `sales_teams`, `accounts` e `sales_pipeline`, com chaves estrangeiras e checks;
    - tabela `parametros` com data de referência (31/12/2017), ciclo máximo (138), fase de risco (14), reta final (104) e amostra mínima (100), editáveis sem mexer em código;
    - RLS com leitura pública e escrita só pelo dono do banco.
19. ✅ A extensão `http` não é suportada no Lovable Cloud. Troquei para `pg_net`, que é assíncrona: um passo dispara o download e o seguinte lê a resposta.
20. 🤖 O próprio banco baixou os 4 CSVs do GitHub (`sql/03_carga.sql`).
21. ✅ Conferi o MD5 de cada arquivo baixado pelo banco contra os arquivos da análise. Bateram byte a byte.
22. 🤖 Fiz a carga com as correções aplicadas.
23. ✅ Resultado exato: 7 produtos, 35 vendedores, 85 contas; 4.238 Won, 2.473 Lost, 1.589 Engaging e 500 Prospecting.
24. 🤖 Criei as views de score (`sql/02_score.sql`):
    - `v_curva_ganho`: chance de ganho por idade (0 a 138 dias), calculada dos deals fechados;
    - `v_deals_score`: um deal por linha, com fila, chance, valor esperado, score 0–100, prazo limite, momento, alertas e motivos em texto;
    - `v_resumo_vendedor`: números por vendedor para a visão do gestor.
25. ✅ Comparei o banco com o gabarito em Pandas: contagens, somas e score médio idênticos (Focar 298, Requalificar 1.291, Prospectar 500, US$ 505 mil de valor esperado).
26. ✅ Li os motivos gerados e achei "Faltam 0 dias" no último dia. Criei uma mensagem específica: "hoje é o último dia do limite histórico".
27. ✅ Testei como usuário anônimo (o app não tem login): lê as 3 views, com 8.800 deals, 30 vendedores e 139 pontos de curva.

## Fase 5 — App (agente do Lovable)

28. 🤖 Mandei ao agente do Lovable a especificação completa das telas (registrada em `docs/lovable_prompts.md`):
    - banco somente leitura: proibido criar ou alterar tabelas;
    - paginação, porque o PostgREST devolve no máximo 1.000 linhas;
    - filtros em cascata região → manager → vendedor, guardados na URL;
    - página **Meu pipeline**: cartões, 3 abas e painel "Por que este score" com motivos, conta, curva e contexto;
    - página **Visão do gestor**: tabela por vendedor, com % parado e destaque acima de 70%;
    - página **Início**: "Como o score funciona" e curva grande;
    - formatação pt-BR, estados de carregando, vazio e erro, e layout responsivo;
    - números esperados para o agente conferir ao terminar.
29. ✅ Revisei o código gerado (`CurvaChart.tsx`, `filters.ts`, `metrics.ts`, `useDeals.ts`) e um screenshot do preview. Achei:
    - a curva despencava para 0% no dia 138 (`p_ganho` nulo virava 0) e mostrava a cauda ruidosa;
    - o limite de 138 dias estava fixo no código;
    - o agente declarou pronto sem testar os filtros.
30. 🤖 Pedi as correções:
    - curva sólida só com amostra ≥ 100 e tracejada no valor que o score usa, com o eixo Y de 50% a 90%;
    - marcador do deal usando a chance do próprio deal;
    - parâmetros lidos da tabela `parametros`;
    - estado vazio útil, com atalhos para as outras filas;
    - testes de filtro com números que calculei antes.
31. ✅ Os testes bateram: Central = Focar 5, Requalificar 403, Prospectar 500; Darcel Schlecht = 0, 83, 111 (com o estado vazio).
32. 🧑 Autorizei a publicação numa URL pública, necessária para o avaliador abrir sem login.
33. 🤖 Publiquei em https://lead-scorer-g4.lovable.app.

Custo do agente do Lovable: cerca de 15 créditos (estrutura 1,3 + telas 9,7 + correções 3,8).

## Fase 6 — Verificação na URL pública

34. ✅ Cartões: 298 deals para focar, US$ 505.216 de valor esperado, 151 na reta final, 1.291 parados com US$ 3,2 mi e 1.425 sem conta.
35. ✅ Ranking: o primeiro é o 1LY8CAXD (GTK 500, 95 dias, 71%, US$ 18.912), igual ao gabarito; o desempate por prazo funciona.
36. ✅ Painel "Por que este score": motivos, conta, curva e ponto do deal corretos.
37. ✅ Os motivos mostravam valores com separador americano (US$ 18,912). Corrigi a formatação para pt-BR direto na view SQL; como o app lê ao vivo, não foi preciso republicar.
38. ✅ Visão do gestor conferida.

## Fase 6b — Evoluções que pedi direto no Lovable (12h27–14h31)

Depois da primeira publicação, mandei 10 mensagens ao agente do Lovable pelo próprio editor, sem passar pelo Claude. Texto integral em [`lovable_prompts.md`](lovable_prompts.md) (mensagens 4 a 13).

- 🧑 **Identidade visual do G4:** cores e fontes do site g4business.com (azul-marinho, dourado, Playfair Display e Archivo).
- 🧑 **Login para a avaliação:** um usuário exclusivo (`recrutamentog4@g4club.com.br`), com validade de 15 dias, até 20/11/2026, e cadastros públicos bloqueados.
- 🧑 **Página inicial mais completa:** resumo executivo do projeto e três novos gráficos (deals por fila, valor esperado por região e distribuição do score).
- 🧑 **Legibilidade:** fontes dos números melhores e paginação de 25 em 25 em "Meu pipeline".
- 🧑 **Resumo executivo em destaque:** card com fonte maior e botão "Detalhar mais", que abre um modal com a análise completa. O agente não conseguiu ler o doc pelo link, porque ele exige login, então colei o conteúdo em Markdown.
- 🧑 **Gráfico de valor esperado por manager** logo abaixo dos cartões de "Meu pipeline", respeitando os filtros.
- 🧑 **Exportação em PDF e XLSX** em "Meu pipeline" e "Visão do gestor", com as mesmas cores e respeitando os filtros.
- ✅ Em cada etapa, o agente testou no navegador e rodou os testes automatizados do projeto (11 testes passando).

## Fase 7 — Documentação e entrega

39. 🤖 README da submissão escrito no `templates/submission-template.md` do G4, com process log, tabela de erros da IA e evidências.
40. 🧑 Pendências minhas antes do Pull Request:
    - [ ] preencher o LinkedIn no README;
    - [ ] conectar o projeto do Lovable ao GitHub e copiar o código para a pasta `solution/app/` (ou linkar o repositório no README);
    - [ ] baixar da conversa principal a versão final de `analise_exploratoria.ipynb` e `analise_exploratoria.html` (com a etapa de robustez) e colocar em `solution/analise/`;
    - [x] fazer o fork do repositório (`emcormack/ai-master-challenge`);
    - [ ] criar a branch `submission/erick-cormack` e a pasta `submissions/erick-cormack/`;
    - [x] export das conversas em Markdown ([`chat_export.md`](chat_export.md));
    - [ ] anexar screenshots das conversas, a gravação de tela e o link oficial de compartilhamento da conversa;
    - [ ] abrir o Pull Request e preencher a data de envio.

---

## Como reproduzir

### Usar o app publicado
Abrir https://lead-scorer-g4.lovable.app e entrar com o e-mail `recrutamentog4@g4club.com.br` e a senha `G4Lead#2026` (válido até 20/11/2026). Com todos os filtros em "Todos", as abas devem mostrar Focar 298, Requalificar 1.291 e Prospectar 500.

### Recriar o banco do zero
Os arquivos ficam em `solution/sql/`.

1. Crie um projeto Supabase (ou Lovable Cloud).
2. Rode, em ordem:
   - `sql/01_schema.sql`;
   - `sql/03_carga.sql`: passo 1, aguarde alguns segundos, passo 2;
   - `sql/02_score.sql`.
3. Sem acesso à internet a partir do banco, rode `sql/seed/*.sql` em ordem, no lugar de `03_carga.sql`.
4. Conferência esperada: 7 / 35 / 85 / 8.800 linhas e, no pipeline, Engaging 1.589, Lost 2.473, Prospecting 500 e Won 4.238.
5. Testado do zero num PostgreSQL 16 limpo com `01_schema.sql`, os seeds e `02_score.sql`: Focar 298, Requalificar 1.291, Prospectar 500 e valor esperado em foco de US$ 505.215,57, idêntico ao banco publicado.

### Rodar o app localmente
Código em `solution/app/`. Configure `VITE_SUPABASE_URL` e `VITE_SUPABASE_PUBLISHABLE_KEY` e rode `npm install && npm run dev`.

### Reproduzir a análise
```bash
cd solution
pip install pandas numpy scipy scikit-learn statsmodels matplotlib jupyter
python scripts/preparar_dados.py      # limpa os CSVs e gera os seeds
python scripts/gabarito_score.py      # score em Pandas, para conferir o banco
jupyter nbconvert --execute --to notebook --inplace analise/analise_exploratoria.ipynb
```

### Estrutura da pasta

```
README.md                 submissão (template do G4)
solution/
  data/                   CSVs originais (CRM Sales Predictive Analytics, CC0)
  data_limpa/             CSVs com as correções aplicadas
  analise/                notebook da análise exploratória (+ HTML)
  scripts/                limpeza dos dados e gabarito do score em Pandas
  sql/                    esquema, score (views) e carga
  app/                    código do front-end (Lovable)
process-log/
  PASSO_A_PASSO.md        este arquivo
  chat_export.md          export das conversas com o Claude
  lovable_prompts.md      as 13 mensagens enviadas ao agente do Lovable
docs/
  resumo_executivo.md     resumo de uma página para C-level
```
