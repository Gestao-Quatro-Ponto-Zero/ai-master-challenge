# Process Log — Narrativa

Log cronológico de como o Claude Code foi usado ao longo deste challenge. Cada entrada é escrita no momento em que a decisão/ação acontece — não reconstruída depois. Datas no formato AAAA-MM-DD.

Convenção: cada entrada tem quem decidiu o quê. "Decisão: Gabriel" = veio de mim, direcionado ao Claude. "Execução: Claude" = o Claude implementou/gerou a partir dessa direção.

---

## 2026-08-19 — Validação de dados, sessão de grilling e consolidação de design

**Contexto:** dados carregados (8.800 oportunidades, 6.711 fechadas, 2.089 abertas). Análise exploratória inicial convergira para uma conclusão contrachoque: nenhum atributo firmográfico ou comportamental prevê ganho/perda (AUC 0,50 em todos os modelos testados, testes de permutação p = 0,31–0,98). Mas o valor é previsível (R² = 0,98), e a diferença entre um negócio bom e um ruim é de até 400×.

**Decisão: Gabriel** — pedi ao Claude Code para estruturar a decisão de design como uma **árvore de decisão** levantando questões estruturadas, validando cada resposta contra os dados e congelando as decisões antes de começar a implementar.

**Execução: Claude** — 
1. **Levantamento de 32 questões** em rodadas sucessivas (Rounds 1–6), cobrindo:
   - Q1–Q5: estratégia geral (score de valor vs ML preditivo, unidade de trabalho, recomendações, escopo, idioma)
   - Q6–Q11: composição do score (pesos, tiers, decaimento temporal, deployment surface)
   - Q12–Q17: stack técnico e UI (FastAPI + React, normalização, forma das explicações, write-back)
   - Q18–Q22: tie-breakers (urgência como componente, seletor de vendedor, gestão, dados em memória, split scoring/api)
   - Q23–Q32: calibração final (pesos, tier cutoffs, product coverage, tier mapping, segurança)

2. **Validação de cada resposta contra os dados:**
   - Permutation tests (2.000 shuffles) confirmaram ausência de sinal em agent/product/sector/account
   - Análise de staleness: 81% dos 1.289 deals em "Engaging" estão parados há mais tempo que o deal mais demorado que já fechou (138 dias)
   - Teste de porte: close_value/list_price = 1,00 ± 0,01 em todas as portes — porte não muda margem, só volume
   - Decomposição de backtest: top 30% by score = 67,3% of revenue, baseline (price only) = 67,8% — diferença marginal, mas o score vence por explainability

3. **Consolidação em arquivos de decisão:**
   - Criado `docs/decisions-log.md` (1.200+ linhas) documentando cada decisão com o raciocínio por trás
   - Atualizado `docs/architecture.md` com a arquitetura real, componentes, fluxo de dados e limitações
   - Criado `CLAUDE.md` (370 linhas) como context-card do projeto para quem vier depois
   - Corrigido `analise-lead-scoring.md` em quatro pontos críticos:
     - Removido `MULT_PORTE` da fórmula de deal (era dupla contagem do product mix)
     - Relabelado ticket médio de 1.490 para receita-por-tentativa (a diferença entre receita ÷ todos vs receita ÷ ganhos)
     - Adicionado baseline de preço puro ao backtest (67,8% vs 67,3% do modelo)
     - Corrigido `CICLO_P95_GANHO` de 129 para 116 dias

**Decisões cristalizadas (congeladas, não revisáveis sem consenso):**
- Score = `0,50·valor + 0,40·urgência + 0,10·zona` com referências de normalização fixas
- Três lanes: Prioridades (298 Engaging ≤138d), Novos (500 Prospecting), Zumbis (1.291 >138d)
- Tiers congelados em 74 / 62 / 47, nunca recompilados
- Sem porte em formula de deal, sem setor, sem gerente, sem vendedor — todos reprovados por teste de permutação
- FastAPI + React com `scoring/` como pacote puro importado por API, CLI e validação
- Data de referência configurável, padrão = max(close_date) dos dados
- Validação como artefato que roda AUC 0,505 + testes de permutação + comparação com baseline de preço

**Execução: Claude** — 
4. **Criação do OpenSpec change "add-lead-scorer"** com schema spec-driven:
   - `proposal.md` (48 linhas): resumo executivo da mudança
   - `specs/lead-scoring/spec.md` (227 linhas): requisitos comportamentais de cálculo, faixa, lanes, explicabilidade, features excluídas, com cenários testáveis
   - `specs/pipeline-api/spec.md` (204 linhas): superfície HTTP — listagem por lane, filtros, rollup de gestão, pontuação avulsa, segurança (sem auth, CORS, sem stack traces)
   - `specs/pipeline-ui/spec.md` (218 linhas): interface (tiles, 4 abas, seletor de vendedor, filtros, aba Gestão, exportação de congelados, tema, português)
   - `specs/scoring-validation/spec.md` (125 linhas): reprodução do AUC, testes de permutação, baseline de preço, determinismo
   - `design.md` (94 linhas): decisões técnicas (motor puro, referência fixa, escala logarítmica, zona em degraus, corte de 138d como política, dados em memória, FastAPI+React, data configurável)
   - `tasks.md` (156 linhas): 46 tarefas em 6 grupos (fundação/dados, formulas, API, interface, validação, empacotamento)

**Descobertas e correções durante a validação:**
- Permutation test de agent spread (p=0,307) matou definitivamente qualquer tentativa de usar win rate de vendedor como preditor
- Bimodal cycle distribution (0–19d peak, 60–90d peak, vale 20–39d) evidencia preenchimento em lote, rejeitou decaimento linear suave
- `MULT_PORTE` investigation: ticket médio por porte variava, mas close_value/list_price era flat 1,00 em todos — o efeito era product mix (premium share 40%→48%), não margem
- Baseline de preço puro capturou 67,8% de receita nos top 30%, vs 67,3% do modelo — não invalida, mas habilita a leitura honesta de que o score é uma transformação monotônica do preço quando P(win) é constante

**Pendente / próximos passos:**
- Execução das 46 tarefas de implementação em sequência de dependência
- Integração do código com CI/CD e tests
- Submissão de PR ao repositório raiz (exigirá fork antes)

---

## 2026-08-19 — Revisão da fórmula e do OpenSpec (via skill `openspec-update-change`)

**Contexto:** ainda antes de qualquer código em `solution/` (só o esqueleto de pastas existia), trouxe uma especificação estatística mais rigorosa da fórmula de priorização — encolhimento hierárquico para `p̂`, curvas de aging isotônicas, censura acima de 138 dias — e pedi para revisar o OpenSpec e os `.md` de arquitetura/decisões pra essa versão, validando que ainda batia com o brief do Challenge 003 e checando se a fórmula ficava mais assertiva.

**Decisão: Gabriel** — pedi explicitamente para: (1) validar contra `challenges/build-003-lead-scorer/README.md`, não só aceitar a fórmula nova sem checar encaixe; (2) trocar os rótulos Diamante/Ouro/Prata/Bronze por Foco urgente/Acompanhar/Engajar/Qualificar/Desistir; (3) garantir que oportunidades sem `account` continuam pontuáveis; (4) adicionar controle de acesso por nível (Manager/Supervisor/Sales Agent) com isolamento completo de dados; (5) explicação + plano de ação por oportunidade; (6) exportação de um CSV com os dados tratados e os scores, para consulta posterior; (7) testes unitários e e2e da API como parte do DoD.

**Execução: Claude** —
1. Usou a skill `openspec-update-change` para reconciliar a mudança `add-lead-scorer` já existente em vez de criar uma nova, já que a intenção (priorizar pipeline por valor+urgência) continuava a mesma — só a fundamentação estatística e o escopo (RBAC, export, testes) mudaram.
2. Confirmou a cardinalidade real de `sales_teams.csv` (35 `sales_agent` → 6 `manager` → 3 `regional_office`) antes de desenhar o RBAC, em vez de supor uma hierarquia — foi isso que definiu o mapeamento Sales Agent/Supervisor/Manager sem precisar inventar uma identidade sintética de administrador.
3. Reescreveu as quatro specs (`lead-scoring`, `pipeline-api`, `pipeline-ui`, `scoring-validation`), o `design.md` e o `proposal.md` do change, e o `tasks.md`, alinhados à nova fórmula, aos 5 estados, ao RBAC e à exportação.
4. Sinalizou explicitamente, em vez de decidir sozinho e esconder, dois pontos de julgamento que a especificação recebida não resolvia sozinha: (a) como mapear os 5 estados novos, já que eram 5 rótulos substituindo 4 faixas antigas — não é uma troca 1:1; (b) como reconciliar `SCORE = percentil(PRIORIDADE)` (pedido na fórmula nova) com a decisão anterior de rejeitar normalização por percentil (por causa de instabilidade) — resolvido congelando o percentil por geração do dataset processado, não recalculando por requisição.
5. Rodou `openspec validate add-lead-scorer --strict` — só warnings de linter esperando `SHALL/MUST` em specs em inglês (o repositório já usa `DEVE`/`NÃO PODE` em português desde antes desta revisão), sem erros reais.
6. Atualizou `docs/architecture.md`, `docs/decisions-log.md` (nova entrada, no formato Decisão/Por quê do próprio arquivo) e o `CLAUDE.md` da submissão para refletir a mesma revisão.

**Descoberta técnica:** a fórmula recebida define `VALOR` em dólares reais (não mais normalizado em escala logarítmica 0–100 como na versão anterior) e só converte para 0–100 no fim, via percentil — uma mudança estrutural que exigiu revisitar a decisão de design #2 do `design.md` antigo (que rejeitava percentil), não só trocar constantes.

**Pendente:** nenhum código foi escrito ainda — esta sessão só revisou planejamento (OpenSpec + docs), consistente com a skill usada, que não edita código. Implementação segue os `tasks.md` atualizados.

---

## 2026-08-19 — Correções de fundo: ESTADO vs CONFIANÇA e referência de SCORE

**Contexto:** logo após a primeira revisão (entrada anterior), você me fez uma pergunta de esclarecimento que expôs dois erros de design na minha primeira versão do OpenSpec revisado — não eram erros de cálculo, mas de modelo conceitual.

**Questão levantada:** Você perguntou se ESTADO **realmente era a mesma coisa que CONFIANÇA**, ou se eram conceitos diferentes — CONFIANÇA sendo "quanto devo acreditar no score" (o fundamento) e ESTADO sendo "que ação recomendo" (que pode depender tanto do score quanto de quão sólido é). Você também apontou que **percentil deveria ser contra histórico de negócios ganhos**, não contra o funil aberto mesmo congelado.

### Correção 1: ESTADO cruza CONFIANÇA e SCORE, não se reduz a CONFIANÇA

**Descoberta:** minha primeira versão fazia ESTADO derivar quase só de CONFIANÇA (D→Desistir, C→Qualificar, B→Engajar, e só dentro de A um corte de SCORE separava Foco urgente de Acompanhar). Isso estava errado — a ação certa depende de **dois eixos de verdade**:
- CONFIANÇA: quanto sei / quanto devo confiar neste número (A–D)
- SCORE: quanto vale esta oportunidade, em risco agora

**Correção:** ESTADO vem de uma tabela 4×2 — CONFIANÇA (A/B/C/D) cruzada com SCORE (≥50 ou <50):

| CONFIANÇA | SCORE ≥ 50 | SCORE < 50 |
|---|---|---|
| A | Foco urgente | Acompanhar |
| B | Acompanhar | Engajar |
| C | Engajar | Qualificar |
| D | Desistir | Desistir |

A diagonal prova que o cruzamento é real: um SCORE alto com CONFIANÇA B não vira Foco urgente (vira Acompanhar — o score é bom, mas a confiança não sustenta urgência); um SCORE baixo com CONFIANÇA C não é Desistir (é Qualificar — falta informação, não necessariamente falta valor). Só CONFIANÇA D é regra de mão única — abaixo do suporte histórico dos dados, nenhum SCORE justifica outra ação que revisão em lote.

**Implicação:** remove o artefato da primeira versão de tentar derivar ESTADO quase só de um eixo com tiebreaker no outro.

### Correção 2: Percentil de SCORE contra histórico de ganhos, não contra funil aberto

**Descoberta:** na primeira versão, eu havia congelado o percentil por geração do dataset (em vez de recalcular a cada request) para evitar instabilidade — uma boa meia-solução, mas ainda usava a distribuição do funil aberto como referência. Você apontou que a referência deveria ser **fixa e histórica**: PRIORIDADE calculada sobre os 4.238 negócios "Won" (cada um com PRIORIDADE na idade real do fechamento).

**Correção:** a distribuição de referência de SCORE é **histórica e imutável** — PRIORIDADE dos negócios ganhos. Só muda no ciclo trimestral de recalibração, nunca em resposta ao funil aberto. Consequência:
- SCORE de uma oportunidade nunca se move porque outras oportunidades entraram ou saíram do pipeline
- SCORE ≈ 82 significa literalmente "vale mais que 82% dos negócios que historicamente viraram receita"
- O corte de ESTADO (50) deixou de ser uma constante a derivar à parte — é simplesmente a mediana da referência

**Implicação:** resolve a tensão entre "estabilidade" (decisão antiga rejeitou percentil) e "flexibilidade" (nova fórmula pedia percentil) sem artifícios de congelamento por geração.

**Execução: Gabriel** — Corrigi:
1. As quatro specs do OpenSpec (lead-scoring, pipeline-api, pipeline-ui, scoring-validation)
2. `design.md` (decisões 2 e 8)
3. `tasks.md` (2.9, 2.9.1, 2.11, 2.12, 2.16)
4. `docs/architecture.md` (seção de SCORE e de ESTADO)
5. `CLAUDE.md` (revisado "Revised 2026-08-19")
6. `docs/decisions-log.md` (entrada 2026-08-19, revisada in-place para documentar as correções — cada uma marcada explicitamente como correção, não mudança de ideia caprichosa)

**Validação:** `openspec validate add-lead-scorer --strict` continua limpo (só warnings esperados de linter RFC2119 em português).

**Pendente:** nenhum código foi escrito ainda — toda essa sessão foi refinamento de planejamento baseado em feedback de modelo conceitual.

---

## 2026-08-19 — Implementação completa via `/opsx:apply` (81 tarefas, 8 grupos)

**Contexto:** com o OpenSpec já consolidado (proposal/specs/design/tasks), pedi ao Claude Code para executar `/opsx:apply add-lead-scorer` e implementar as 81 tarefas de `tasks.md` em sequência — `scoring/` primeiro (é a dependência de tudo mais), depois RBAC, API, interface, validação, empacotamento e documentação.

**Execução: Claude** — implementou as oito seções do `tasks.md` nesta ordem, verificando cada uma contra dados reais antes de marcar como concluída (não apenas escrevendo código e assumindo que bate com a spec):

1. **`scoring/`** (Python puro, sem web) — `constants.py`, `repository.py`, `shrinkage.py`, `curves.py`, `model.py`, `reference.py`, `confianca.py`, `estado.py`, `explicacao.py`, `export.py`, `pipeline.py`. 59 testes unitários, incluindo os três exemplos de referência literais dos specs.
2. **RBAC** (`api/auth/`) — derivação de papel a partir de `sales_teams.csv`, tokens assinados com `itsdangerous`, resolução de escopo com interseção filtro×escopo. 10 testes unitários, incluindo o caso de dois supervisores no mesmo escritório.
3. **API** (FastAPI) — 8 endpoints, validação de entrada, CORS enumerado, handler de erro sem stack trace. 32 testes (contrato + e2e), incluindo o ciclo completo identificação→token→escopo→403→401→rollup→export.
4. **Interface** (React + TypeScript + Tailwind, tema G4 Business) — seleção de identidade, 5 abas + Gestão, filtros sincronizados com URL, tabela ordenável, decomposição e plano de ação visíveis por linha.
5. **`validation/`** — AUC isolada/combinada, testes de permutação, reprodução de `k`, verificação de monotonicidade de `risco(t)`, concentração de PRIORIDADE. Relatório de texto por comando único.
6. **Empacotamento** — `docker-compose.yml` (api + web/nginx), `Makefile`, `README.md` da solução.

### Onde a saída da IA foi verificada e corrigida durante a implementação

**1. Constante `K_PRODUTO = 4` — achado, não bug, mas exigiu decisão explícita.** Ao implementar `validation/shrinkage_check.py` para reproduzir honestamente o cálculo de `k` (mesma fórmula: variância esperada por acaso / variância em excesso), o recálculo do zero mostrou colapso (`k = ∞`) não só em conta×produto e produto×setor (esperado, documentado), mas **também no nível de produto** — mais fraco que qualquer um dos quatro atributos testados por permutação. Isso contradiz o texto da spec, que descreve `k = 4` como o valor calibrado no nível de produto. Decisão tomada (documentada em `docs/architecture.md` e impressa pelo próprio `backtest.py` a cada execução): manter `K_PRODUTO = 4` como constante **congelada** desta calibração — é o valor que todos os outros documentos do projeto (CLAUDE.md, design.md, decisions-log.md) já assumem, e reproduz exatamente os exemplos de referência dos specs (`p̂_produto(GTK 500) = 0,604`, `p̂_produto(MG Special) = 0,648`) — em vez de recalcular e colapsar `p̂_produto` para a constante global em produção, o que quebraria os testes formais e reverteria uma decisão de design já tomada e documentada por Gabriel. O relatório de validação expõe essa tensão explicitamente em vez de escondê-la.

**2. Discrepância de preço no texto da spec.** O cenário "Prospecting recebe PRIORIDADE completa" em `specs/lead-scoring/spec.md` cita GTX Basic a US\$ 1.585 — o catálogo real (`products.csv`) tem GTX Basic a US\$ 550. Não é um teste formal obrigatório (a task 2.15 não cobra esse número específico), então a implementação seguiu o dado real (`PRECO_TABELA["GTX Basic"] = 550.0`) e não o número do texto da spec, que aparenta ser um erro de digitação/geração da própria spec.

**3. `lightgbm` trocado por `HistGradientBoostingClassifier` (scikit-learn).** `pip install -r validation/requirements.txt` falhou neste ambiente: `lightgbm` precisa de `libomp` nativo via Homebrew no macOS, que não está instalado por padrão. Como isso quebraria diretamente o critério de aceitação "partida por comando único, sem passos manuais adicionais" (task 7.2) em qualquer máquina sem a lib pré-instalada, troquei para o gradient boosting nativo do scikit-learn — mesmo papel, zero dependência de compilação nativa. Registrado em `proposal.md`, `architecture.md` e `validation/requirements.txt`.

**4. Dois bugs reais encontrados testando a interface no navegador** (não apenas checagem de tipos — a app rodando de verdade, com a API real, clicando pelos cinco papéis):
   - A aba ativa (`?aba=gestao` na URL) sobrevivia à troca de identidade. Um Manager na aba Gestão que trocasse para um Sales Agent (que não tem Gestão) ficava com a tela presa em "Carregando rollup…" para sempre, porque o rollup nunca é buscado para esse papel. Corrigido: a troca de identidade agora limpa a URL, e a aba é validada contra o papel corrente antes de renderizar.
   - Um token inválido ou expirado (por exemplo, a API reiniciando com um novo segredo de assinatura em memória) deixava a tela em branco para sempre, sem nenhuma mensagem — o usuário não tinha como saber que precisava clicar em "Trocar identidade". Corrigido: qualquer resposta 401 de qualquer chamada agora limpa a sessão automaticamente e volta para o seletor de identidade.

---

## 2026-08-20 — Sessão de grilling (33 perguntas) + OpenSpec + implementação do redesenho de SCORE/CONFIANÇA/ESTADO

**Contexto:** com o RBAC já removido (entrada anterior deste mesmo dia), apontei três problemas de uso na entrega validada: PRIORIDADE em dólares lia como "venda o produto caro" (não "trabalhe isto primeiro"), CONFIANÇA D forçava o estado Desistir para a maioria do funil, e Acompanhar/Engajar davam o mesmo conselho. Pedi a skill `grilling` para stress-testar o redesenho antes de qualquer código.

**Decisão: Gabriel** — usar `/grill-me` com três instruções de partida: PRIORIDADE virar um score, não um valor em dólares; melhorar a fórmula de CONFIANÇA; renomear o estado `qualificar` para "Prioritize".

### Execução: Claude — sessão de grilling em rodadas, cada pergunta fundamentada em número medido

Diferente da sessão de 2026-08-19 (que também usou perguntas em rodadas, mas sobre decisões de design ainda não implementadas), esta rodou sobre um sistema já em produção — cada resposta do Claude vinha acompanhada de um script Python rodado contra os dados reais (`bash`/`.venv/bin/python` inline), não de estimativa. Isso mudou o rumo da conversa mais de uma vez:

1. **Q1 corrigiu uma premissa do próprio Gabriel** — a alegação de que `qualificar` estava vazio não se confirmou (197 oportunidades reais); a pergunta certa era se o estado carregava informação útil, não se existia.
2. **Q2–Q9 mediram, não supuseram, se a hierarquia de encolhimento (produto×setor, conta×produto) carrega sinal** — validação cruzada 5-fold mostrou que um prior global achatado batia qualquer condicionamento adicional, o oposto do que "melhorar a fórmula de CONFIANÇA" presumia inicialmente.
3. **Q15–Q19 testaram a proposta de Gabriel de calcular URGÊNCIA/`p̂` por produto** (não só o CONFIANÇA original) — também pior fora da amostra, incluindo um teste de permutação específico para duração de ciclo por produto.
4. **Q20–Q28 iteraram a fórmula de CONFIANÇA várias vezes dentro da própria sessão**, cada iteração medida antes de prosseguir: `min` vs. média (decisivo: 353 oportunidades com completude 100/suporte 0 pontuariam 50 sob média, 25 sob `min`), suporte multiplicativo vs. aditivo (multiplicativo deixava 76% do funil em zero), e o vazamento onde support penalizava Prospecting duas vezes pela mesma ausência de `engage_date`.
5. **Q29–Q32 encontraram e corrigiram, dentro da própria grilagem, uma regressão que a rodada anterior introduzira** — expandir completude de 2 para 5 campos (pedido do próprio Gabriel, para dar granularidade real à escala) fez a completude sozinha penalizar oportunidades em Prospecting sem conta 4 vezes pela mesma causa, derrubando de novo a correção da rodada anterior. Resolvido roteando `revisao_lote` por uma condição nomeada (`s_idade == 0`) em vez de um corte sobre o número combinado — a fórmula ficou robusta à forma exata de completude.

**Decisão: Gabriel** — confirmar CONFIANÇA=`min(completude, suporte)` com suporte aditivo ponderado (0,75/0,25) e completude de 5 campos; ESTADO como árvore de decisão de 4 valores; manter "Priorizar" como rótulo em português (a chave interna do estado fica em inglês, mas a interface é sempre PT-BR).

### Execução: Claude — OpenSpec (`redesign-score-confianca-estado`) e implementação completa via `/opsx:apply`

1. **`openspec-propose`**: criou `proposal.md`, deltas de 4 specs (`lead-scoring`, `scoring-validation`, `pipeline-api`, `pipeline-ui`), `design.md` e `tasks.md` (73 tarefas). Ao escrever as deltas, descobriu que `refine-pipeline-ux` (a mudança anterior deste mesmo dia) havia sido arquivada **sem que suas deltas fossem aplicadas à spec principal** — `openspec/specs/` ainda descrevia identificação por papel e tokens, que o código já não tinha. Sinalizado a Gabriel em vez de ignorado; Gabriel pediu para fechar a lacuna junto ("escreva as deltas") em vez de deixar para depois.
2. **`openspec validate --strict`** encontrou 3 rodadas de erros reais — cenários de comportamento existentes na spec principal que as deltas MODIFIED omitiam (perda de cenário é rejeitada pelo validador, não só um lint) — cada um corrigido carregando o cenário original para o corpo novo.
3. **`/opsx:apply`**: implementou as 73 tarefas em ordem — `scoring/` (motor puro), regeneração do CSV, `api/` (schemas/query/rotas), `web/` (React), `validation/` (3 artefatos novos de reprodução + correção do relatório de encolhimento), documentação.
4. **Achado real durante a implementação, não previsto no design**: `constants.classificar_porte` só verificava `employees is None`, mas o merge com `accounts.csv` preenche funcionários ausentes com `NaN` — e `NaN < limiar` é sempre `False` em Python. As 1.425 oportunidades sem conta caíam silenciosamente em "Enterprise" em vez do prior neutro que o requisito de VALOR já prometia desde 2026-08-19. Corrigido (`employees != employees` cobre NaN); a correção moveu a distribuição final de ESTADO (`Priorizar` de 63 para 54) e reconciliou os números medidos durante a grilagem com os números do sistema já corrigido — a diferença entre os dois foi investigada e documentada, não descartada como ruído.
5. **Verificação visual no navegador** (não só testes automatizados): fila trabalhável default, chips de estado, régua de idade, link e visão de revisão em lote, ordenação por CONFIANÇA, tooltip da nova exibição de CONFIANÇA, painel de detalhe, aba Gestão com a coluna de CONFIANÇA mediana — confirmando que a "descoberta real" de que a mediana de CONFIANÇA por vendedor é quase sempre 25 (distribuição muito concentrada, não um bug) não invalidava o requisito, só limitava seu poder discriminativo — registrado como achado, não corrigido às pressas.

**Testes:** 84 unitários em `scoring/` (todos reescritos), 46 em `api/` (13 novos), 13 em `validation/` (9 novos), `tsc -b` limpo em `web/`.

---
