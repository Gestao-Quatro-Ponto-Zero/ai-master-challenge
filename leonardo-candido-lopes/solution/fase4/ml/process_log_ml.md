# Process log — Componente ML (Fase 4)

> Ordem cronológica das decisões, tentativas e falhas. Legenda: **EVIDÊNCIA** (medido), **INTERPRETAÇÃO** (leitura do medido), **HIPÓTESE** (não verificada).

## 1. Auditoria e reconciliação dos 235

- **EVIDÊNCIA:** os 235 da Fase 3 vêm de 133 textos com menos de 5 palavras e 102 registros em 38 grupos de prefixo-15 com rótulos conflitantes, sem sobreposição. A conta foi reproduzida exatamente.
- **Decisão:** os curtos deixaram de ser excluídos. Nenhum é lixo (0 textos com 2 caracteres ou menos); são abreviações legítimas (ex.: "password reset contacted change"). Ficam com flag e passam por sensibilidade.
- **Decisão:** a quarentena dos conflitantes foi ampliada para incluir pares quase idênticos (cosseno 0,98 ou mais) com rótulos diferentes: 211 registros, dos quais 35 já estavam no critério de prefixo. Total em quarentena: 278.
- **Decisão:** nas quase-duplicatas com o mesmo rótulo, mantém-se 1 representante por prefixo-15 (566 removidos).
- **Resultado:** restam 46.993 registros limpos.

## 2. Split — v1 descartada, v2 adotada

- **v1:** os grupos eram componentes conexos de pares com cosseno 0,80 ou mais.
  - **EVIDÊNCIA:** maior grupo com 1.156 linhas (1.105 de Purchase, quase metade da classe); Purchase ficou com 5,8% no treino contra 2,0% no teste. Trocar a seed não mudou nada.
  - **INTERPRETAÇÃO:** com 0,80, os pares se encadeiam e superagrupam a família de templates de Purchase.
  - O revisor metodológico apontou o mesmo problema.
- **v2:** grupos com cosseno 0,90 ou mais, unidos aos grupos de prefixo-15.
  - **EVIDÊNCIA:** maior grupo limpo com 612 linhas; desvio máximo por classe de 0,52 / 0,91 / 1,61 p.p. (treino/val/teste).
  - Zero pares com cosseno 0,90 ou mais cruzando splits. Restam 13.751 pares na faixa 0,80–0,90 cruzando splits, um risco residual que foi medido (ver seção 6).
- **Método:** `StratifiedGroupKFold(20)`, com 3 folds para teste, 3 para validação e 14 para treino. O `GroupShuffleSplit` não estratifica, por isso não foi usado.
- O fold é atribuído a **todas** as 47.837 linhas. Assim, a sensibilidade sujo × limpo usa exatamente o mesmo split e o mesmo teste.

## 3. Pré-processamento

- **Escolha:** lowercase, remoção de pontuação, stopwords do sklearn (318 termos) e stemming Snowball.
  - Stemming em vez de lematização: é determinístico, rápido, não depende de modelos baixados e o D2 já vem tokenizado e sem pontuação.
  - O texto do D2 já vem pré-processado na origem. Aplicar a mesma função a qualquer texto novo garante consistência.
- **Efeito colateral conhecido:** "cannot" é stopword. Por isso a prioridade usa o texto bruto, não o pré-processado.

## 4. Seleção de modelo (F1-macro na validação, v2)

| Modelo | Parâmetro | F1-macro val | F1-macro treino |
|---|---|---:|---:|
| M0 Dummy (mais frequente) | — | 0,0562 | 0,0554 |
| M1 TF-IDF + LR | C = 0,1 | 0,8115 | 0,8500 |
| M1 TF-IDF + LR | C = 1 | 0,8353 | 0,9191 |
| M1 TF-IDF + LR | C = 10 | 0,8394 | 0,9890 |
| M2 TF-IDF + LinearSVC | C = 0,1 | 0,8390 | 0,9226 |
| **M2 TF-IDF + LinearSVC** | **C = 0,5** | **0,8412** | 0,9795 |
| M2 TF-IDF + LinearSVC | C = 1 | 0,8364 | 0,9920 |

- **Decisão:** LinearSVC com C = 0,5 tem o maior F1-macro na validação.
  - **INTERPRETAÇÃO:** a diferença para LR C = 10 (0,0018) está dentro da variação entre execuções (cerca de 0,002). Os dois são equivalentes na prática. O LinearSVC treina mais rápido (cerca de 9 s contra 19 s).
- **Modelo 3 não treinado:** o melhor F1-macro (0,84) ficou acima do gatilho de 0,75.
- Sobreajuste visível (treino 0,98 contra validação 0,84), mas a validação é o critério de escolha. A regularização mais forte (C = 0,1) teve validação parecida (0,839).
- **Parâmetro removido:** `multi_class='multinomial'` não existe mais no sklearn 1.9; o solver lbfgs já é multinomial por padrão.
- **Na v1** (split com cosseno 0,80), o vencedor foi LinearSVC com C = 0,1 (val 0,8307; teste calibrado 0,8347). Os números finais são os da v2.

## 5. Calibração

- O LinearSVC não tem `predict_proba`. Comparei `CalibratedClassifierCV` com cv = 5 nas versões sigmoid e isotônica, na validação:
  - **EVIDÊNCIA:** sigmoid com ECE 0,0675 e F1 0,8423; isotônica com ECE 0,0646 e F1 0,8404.
  - **Escolhida a isotônica:** menor ECE, com F1 dentro de 0,01 do melhor.
- **Teste:** ECE 0,0749. O reliability diagram mostra **subconfiança**: na faixa de 0,8–0,9 de confiança, a acurácia é 0,95; na de 0,7–0,8, é 0,88.
  - **INTERPRETAÇÃO:** os limiares são conservadores, ou seja, a precisão real fica acima da confiança nominal.

## 6. Limiares e avaliação

- **Limiares:** metas de precisão de 0,95 (AUTOMATIC) e 0,90 (piso) aplicadas na validação, o que dá limiar alto de **0,70** e baixo de **0,55**.
  - No teste: 0,70 tem cobertura de 65,6% e precisão de 95,8%; 0,55 tem 83,0% e 91,0%.
  - O 0,85 antigo, no teste, teria cobertura de 44,5% e precisão de 98,4%.
  - **Decisão pendente do negócio:** as metas 0,95 / 0,90 são proposta para validação.
- **Teste completo:** F1-macro de 0,8403.
  - Pior categoria: Administrative rights (0,760, recall 0,673). Segunda pior: Miscellaneous (0,825).
  - Os 10 erros mais confiantes de cada uma estão em `evaluation/error_analysis_worst2.csv`.
- **HIPÓTESE:** vários erros de Administrative rights são textos de hardware ou conectividade ("monitors are not working", "restart of the server"). Isso sugere ruído de rótulo, não falha do modelo.
- **Vazamento residual medido:**
  - Linhas de teste com vizinho no treino (cosseno 0,80 ou mais): n = 1.026, F1 0,921.
  - Linhas sem vizinho: n = 5.740, **F1 0,820**.
  - **INTERPRETAÇÃO:** para texto realmente novo, a expectativa honesta é F1 de cerca de 0,82.

## 7. Sensibilidade da limpeza

Mesmo LinearSVC (C = 0,5, sem calibração), mesmo split e mesmo teste limpo:

| Variante | n treino | F1-macro teste |
|---|---:|---:|
| A — sujo (sem limpeza) | 33.671 | 0,8362 |
| B — conservador (principal) | 33.237 | 0,8363 |
| C — conservador sem curtos | 33.146 | 0,8362 |
| D — agressivo | 32.763 | 0,8364 |

- **EVIDÊNCIA:** a diferença máxima é de 0,0002.
- **INTERPRETAÇÃO:** a limpeza não melhora o desempenho. O valor dela está em não avaliar com contradições e duplicatas. Os 160 registros em quarentena no fold de teste têm acurácia de apenas 0,756: são, de fato, casos com rótulo ambíguo.

## 8. Detector de domínio — 3 iterações

1. **v0:** negativos com a descrição completa do D1.
   - **EVIDÊNCIA:** F1 de validação = 1,0. Os termos mais fortes eram "hi", "thank", "regard" (IT) contra "issu assist", "product" (FC).
   - **INTERPRETAÇÃO:** o detector aprendeu o *estilo* (e-mail corporativo × template B2C), não o domínio.
2. **v1:**
   - Removi os tokens de estilo (mesma lista de boilerplate da Fase 2) e as 94 frases-template do D1 que aparecem em 20 ou mais tickets.
   - **EVIDÊNCIA:** frases técnicas como "I'm unable to access my account" aparecem aleatoriamente em tickets de reembolso. Usá-las ensinaria que "acesso" significa comercial.
   - Os termos mais fortes passaram a ser semânticos (access, laptop, oracle × refund, payment, delivery).
   - Os limiares tinham degenerado (0,20 / 0,15) e foram substituídos por uma banda fixa de 0,30 / 0,70. **Descartei a v1** porque a banda não era empírica e "company lunch" saía IT_INTERNAL.
3. **v2 (adotada):**
   - t_uncertain = 0,801 e t_oos = 0,1839, ambos no 1º percentil da validação in-domain (aceita-se cerca de 1% de abstenção em casos conhecidos).
   - OUT_OF_SCOPE passou a usar a similaridade máxima com os exemplos de treino.
   - **EVIDÊNCIA:** "company lunch" continua IT_INTERNAL, porque as palavras existem no D2.
   - **INTERPRETAÇÃO:** um detector binário sem exemplos de fora de escopo não aprende essa fronteira. Isso exige coletar exemplos reais.
- **Negativos usados:** D1 com Ticket Subject em Refund request, Delivery problem, Payment issue, Product recommendation e Cancellation request (2.667; 2.000 para treino e 667 para validação). Texto = assunto + frases que não são template.
- **Excluídos:** os assuntos técnicos B2C (ambíguos com TI).
- **Positivos:** 8.001 exemplos do treino do D2 (sem usar validação ou teste).

## 9. Regras de segurança e casos de teste

- **v1 das regras + split v1:** 12/15 aprovados. Falharam:
  - #3 Purchase (→ Hardware);
  - #5 admin (→ HR Support, decisão ASSISTED);
  - #9 lunch (IT_INTERNAL, decisão **AUTOMATIC**).
- **Revisão:** o caso #5 mostrou que uma regra baseada só na categoria prevista não protege contra erro do classificador. Adicionei a regra textual R4 (admin, sudo, root, privilege, elevated access → HUMAN_REQUIRED).
- **v2 final: 11/15 aprovados.** Os critérios foram definidos antes da execução e não foram alterados.
  - #3 continua falhando (Hardware 0,979, AUTOMATIC).
  - #5 agora tem a decisão segura (HUMAN_REQUIRED via R4), mas falha na categoria.
  - #7 passou a falhar: Internal Project 0,845 resultou em AUTOMATIC (na v1, 0,65, ASSISTED).
  - #9 continua falhando no domínio, mas a decisão caiu de AUTOMATIC para ASSISTED.
  - **INTERPRETAÇÃO:** o retreino com o novo split mudou a confiança em textos curtos e genéricos. Casos de uma frase são instáveis.
- **Não fiz ajustes para "passar" nos testes.** As mitigações sugeridas estão abaixo.

## 10. Mitigações propostas (não implementadas — exigem dado real ou decisão)

1. Coletar exemplos reais de pedidos de compra em linguagem natural ("order monitors") e de mensagens fora de escopo, e retreinar o detector com 3 classes.
2. Exigir no mínimo N tokens úteis (ex.: 5) para permitir AUTOMATIC, o que resolveria o caso #7. Precisa ser medido no validação antes de adotar.
3. Revisão humana amostral dos rótulos de Administrative rights e Miscellaneous.
4. Rodar em sombra (shadow mode) por 4 a 8 semanas e recalcular os limiares com dados reais.

---
## Etapa App + evidências visuais (Fase 4)
- **Construído:** interface Next.js (`app/nextjs_space`, páginas /, /metricas e /sobre) consumindo uma API FastAPI (`api/main.py`: /classify, /health, /test-cases, /model-metadata) que carrega `model/classifier_pipeline.pkl` e `model/domain_detector.pkl`.
- **Chamadas reais via curl:** login → Access 0,986 AUTOMATIC; reembolso → FINANCIAL_COMMERCIAL HUMAN_REQUIRED; "entire network is down" → categoria errada (HR Support 0,533), mas a regra R3_CRITICAL_LOW_CONF levou a ESCALATE.
- **Evidências:** 8 capturas automáticas com Playwright em `fase4/evidencias/`, com as respostas brutas em `capture_log.json`.
- **Falha nova encontrada:** "Can you book a table for the company lunch on Friday?" → IT_INTERNAL / Hardware 0,748 / AUTOMATIC. O detector de domínio não generaliza para fora da distribuição, e o resultado não depende só da frase exata do teste #9. Fica registrado sem correção, para não ajustar o sistema ao teste. Correção proposta para a próxima iteração: negativos reais de domínio (texto corporativo não-TI) no treino do detector, e AUTOMATIC exigindo também uma margem mínima entre top-1 e top-2 e similaridade mínima com o conjunto de treino.
- **Variação de frase muda o domínio:** reembolso e queda de rede, com outras palavras, saíram como INDETERMINATE. O resultado continua seguro (vai para humano), mas mostra que o detector é instável.

---
## 11. Ajustes finais controlados da Fase 4 (fechamento — NÃO é Fase 5)

Dois ajustes pontuais solicitados, sem retreino, sem alterar datasets, métricas originais ou resultados históricos.

### Ajuste 1 — Confiabilidade da categoria exibida
- Quando uma regra de segurança **sobrepõe** a decisão do classificador, a categoria prevista é marcada como **não confiável**, mas **preservada** (não é apagada nem substituída).
- Implementação: conjunto `UNRELIABLE_CATEGORY_RULES = {R1, R3, R4, R5, R9}` em `security_rules.py`. A API passa a devolver `category_raw` (categoria crua do classificador, sempre), `category_reliable` (bool) e `category_reliability_reason`. `inference.py` devolve os mesmos campos.
- UI (`triage-result.tsx`): badge "⚠ Categoria não confiável" + aviso de que a categoria foi preservada só para rastreabilidade; e duas linhas novas na Rastreabilidade ("Categoria (crua)" e "Categoria confiável"). Nenhuma mudança visual fora disso.

### Ajuste 2 — Barreira conservadora contra encaminhamento automático fora de escopo (R9_DOMAIN_NOT_VALIDATED)
- Nova regra posicionada **imediatamente antes** do ramo AUTOMATIC. No caminho que iria para AUTOMATIC, se `max_sim_train < AUTO_MIN_SIM` (ou indisponível) → rebaixa para **ASSISTED** (mantém o humano no loop; bloqueia roteamento automático). Só restringe, nunca afrouxa.
- **AUTO_MIN_SIM = 0,49**, origem documentada: `val_sim_quantiles` em `evaluation/domain_detector_results.json` = [p0=0,1405, p1=0,1839, p5=0,2299, **p50=0,49**]. Usa-se a **mediana** das similaridades in-domain da validação — critério calibrado existente, **não** um limiar inventado.
- Domínio indeterminado/fora de escopo/financeiro já caía em HUMAN_REQUIRED (R2) antes de qualquer automação — mantido. R9 cobre o caso em que o **detector erra e rotula como IT_INTERNAL** um texto fora de escopo (limitação conhecida): mesmo com confiança alta da categoria, não há ação automática.
- **Confiança elevada da categoria NÃO substitui validação do domínio:** R9 depende exclusivamente da similaridade com o treino, não da confiança do classificador.

### Achado honesto sobre margem e similaridade (critérios de abstenção avaliados)
- Avaliei **margem top1−top2** e **similaridade com o treino** como critérios adicionais. **Nenhum dos dois separa de forma limpa** os erros de domínio dos chamados de TI legítimos (ex.: texto fora de escopo com sim ≈ 0,25 convive com chamado de TI legítimo com sim ≈ 0,28–0,37).
- Por isso **NÃO** criei um gate de margem (seria inventar um discriminador sem base). A similaridade é usada **apenas** como critério **conservador** de abstenção da automação (rebaixa para ASSISTED), exatamente porque não há calibração suficiente para distinguir domínio — na dúvida, prefere-se revisão/confirmação humana.
- **O detector de domínio continua NÃO validado.** Este ajuste é uma barreira de contenção, não uma solução do problema de domínio. A mitigação definitiva (coletar negativos reais de domínio e retreinar) permanece pendente para iteração futura.

### Verificação (testes pontuais, resultados reais)
- Rodado o `test_cases.json` pela inferência pós-ajuste gravando em **arquivo novo** `test_results_pos_ajuste.json`; o histórico `test_results.json` (**11/15**) **não foi alterado**.
- **Resultado pós-ajuste: 12/15** (antes 11/15). Única mudança: **#7 (ambíguo)** passou a aprovar — o critério definido a priori era `decision_not: [AUTOMATIC]`, e R9 rebaixou de AUTOMATIC para ASSISTED (correção genuína pela nova barreira, não manipulação).
- **Falhas preservadas:** #3 (Purchase→Hardware, segue AUTOMATIC com sim 0,61 ≥ 0,49), #5 (admin→HR Support, HUMAN_REQUIRED via R4) e #9 (domínio, segue ASSISTED). Nenhuma falha foi removida.
- **AUTOMATIC continua ativo:** casos #3 e #4 (sim ≥ 0,49) seguem AUTOMATIC — chamados de TI dentro dos critérios de segurança continuam funcionando.
- **Fora de escopo não recebe automação:** caso fora de escopo rotulado como IT pelo detector → ASSISTED (R9) + categoria não confiável; OUT_OF_SCOPE/INDETERMINATE → HUMAN_REQUIRED (R2).
- **Categoria não confiável** confirmada para R1/R3/R4/R5/R9 (cru preservado).
- **Integração UI↔API** confirmada no navegador (preview): caso #1 login → confiança 91%, decisão ASSISTED via R9, categoria "Access" marcada como não confiável, Top 3 e categoria crua preservados na Rastreabilidade.
- **Arquivos alterados:** `ml/security_rules.py`, `ml/inference.py`, `api/main.py`, `app/nextjs_space/app/components/triage-result.tsx`. Resultados pós-ajuste em `ml/test_results_pos_ajuste.json` (novo).

---
## 12. Correção da R9 após auditoria de 10/11/2026 (inconsistência material do limiar de similaridade)

### 12.1 Descoberta da auditoria — a fundamentação da Seção 11 estava INCORRETA
A auditoria de 10/11/2026 revisou a origem do limiar `AUTO_MIN_SIM = 0,49` e demonstrou que a afirmação registrada na Seção 11 — de que **0,49 era a mediana das similaridades *in-domain*** — **está errada**.

Os `val_sim_quantiles` em `evaluation/domain_detector_results.json` foram calculados sobre uma **população MISTA**: a validação concatena positivos e negativos (`Xva = concat(pos_va, neg_va)` em `domain_detector.py`), ou seja **2.001 exemplos IT (in-domain) + 667 exemplos FC (fora de domínio)**. O p50 = 0,49 é a mediana dessa mistura, **não** dos chamados de TI legítimos.

Medianas separadas (reportadas na auditoria):
- IT (in-domain): **0,4276**
- FC (fora de domínio): **0,6506**
- população mista: **0,49**

Consequência grave: a similaridade com o treino **não discrimina domínio** — os textos FC fora de escopo pontuam *mais alto* (0,65) do que os chamados de TI legítimos (0,43). Um gate `sim ≥ 0,49` **penalizaria chamados de TI legítimos** (muitos abaixo de 0,49) enquanto **deixaria passar chamados externos** (acima de 0,49). É exatamente o inverso do pretendido. Fica aqui **registrado expressamente que a afirmação anterior (0,49 = mediana in-domain) estava incorreta.**

### 12.2 Correção aplicada (R9 v4 — conservadora)
- **Removido** por completo o critério de similaridade mínima: a constante `AUTO_MIN_SIM` **deixou de existir** em `security_rules.py`; o parâmetro `max_sim_train` foi **removido da assinatura de `decide(...)`**, da chamada em `inference.py` e da chamada em `api/main.py`.
- **Não** foi adotado nenhum limiar substituto (nem 0,4276, nem 0,65, nem outro) — não há validação que justifique qualquer corte de similaridade como prova de domínio.
- **A confiança do classificador NÃO foi usada como substituta** da validação de domínio.
- Como **não existe sinal validado** que autorize liberar automação com segurança (similaridade desacreditada + detector de domínio não validado), o ramo que antes poderia ir para AUTOMATIC passa a ser **sempre rebaixado para ASSISTED** via `R9_DOMAIN_NOT_VALIDATED` (mantém o humano no loop). Regra continua **só restringir, nunca afrouxar**.
- **Efeito colateral honesto:** com isso **AUTOMATIC zera** (nenhum roteamento 100% automático permanece) e a regra `R8_HIGH_CONFIDENCE` fica **inalcançável** (documentada como tal no `RULES_DOC`). É um **custo de utilidade** assumido conscientemente: na ausência de evidência validada, a prioridade correção > segurança > utilidade exige preferir confirmação humana.
- **Preservado** (não removido): marcação de categoria não confiável (`UNRELIABLE_CATEGORY_RULES`, agora incluindo R9), `category_raw`/`category_reliable`/`category_reliability_reason`, todas as regras de segurança R1–R7, e a identificação das falhas conhecidas. `max_sim_train` continua presente em `domain_detail` **apenas para rastreabilidade** (não é mais critério de decisão).

### 12.3 Testes direcionados (resultados reais) — gravados em `test_results_pos_ajuste.json`
Rodado `test_cases.json` pela inferência pós-correção; o histórico `test_results.json` (**11/15**, mtime 09/11) **não foi tocado**.

Distribuição de decisões (15 casos):

| Estado | AUTOMATIC | ASSISTED | HUMAN_REQUIRED | ESCALATE | PASS |
|---|---|---|---|---|---|
| Histórico pré-R9 (`test_results.json`) | 6 | 1 | 6 | 2 | 11/15 |
| Implementação intermediária (R9 v3, gate sim 0,49) | 2 | 5 | 6 | 2 | 12/15 |
| **Pós-correção (R9 v4)** | **0** | **7** | **6** | **2** | **12/15** |

- **Casos que mudaram de decisão pré-R9 → v4:** #1, #2, #3, #4, #7, #12 — todos de AUTOMATIC para ASSISTED.
- **Casos que mudaram v3 → v4:** #3 e #4 (AUTOMATIC → ASSISTED); eram os únicos que ainda chegavam a AUTOMATIC no gate 0,49.
- **Única mudança de status de teste pré-R9 → v4:** #7 (`Something is wrong with my setup`), critério `decision_not:[AUTOMATIC]` — era AUTOMATIC (falhava), agora ASSISTED via R9 (passa). Correção genuína.
- **Falhas conhecidas preservadas:** #3 (`order 5 new monitors` → Hardware≠Purchase, segue FALHA), #5 (admin → HR Support≠Administrative rights, HUMAN_REQUIRED via R4, FALHA), #9 (`company lunch` detectado como IT_INTERNAL, domínio+decisão, FALHA). **Nenhuma exceção artificial criada.**

### 12.4 Métricas de cobertura/precisão
Os arquivos `coverage_precision_*.csv` e `charts/ml_coverage_precision.json` (mtime 09/11) medem **apenas o classificador de categoria** e **nunca** incorporaram a R9. **Não foram recalculados aqui** e **não foram alterados** — permanecem como registro histórico pré-R9. Portanto **não** se declara melhora de precisão/cobertura do sistema: os testes direcionados acima medem *decisões*, não cobertura/precisão estatística do classificador.

### 12.5 Limitações que continuam abertas
- **Detector de domínio ainda NÃO validado** (treinado só com negativos sintéticos FC). Continua sem prova de que exclui chamados externos — não é apresentado como proteção confiável.
- **Nenhum roteamento automático ativo** (AUTOMATIC = 0). Todo caso exige ao menos confirmação de agente. Custo de utilidade assumido.
- Falhas de categoria conhecidas (#3, #5) seguem abertas.
- Mitigação definitiva de domínio (coletar negativos reais e revalidar) permanece pendente para iteração futura.

**A Fase 4 NÃO é declarada totalmente validada:** persistem riscos sem validação (detector de domínio) e falhas conhecidas preservadas.

### 12.6 Arquivos alterados nesta correção
`ml/security_rules.py` (R9 v4 + remoção de AUTO_MIN_SIM + assinatura de `decide` + anotação de R8 inalcançável), `ml/inference.py` (remoção de `max_sim_train` da chamada), `api/main.py` (remoção da extração/uso de `max_sim_train` + comentário de rastreabilidade). Resultados em `ml/test_results_pos_ajuste.json` (regenerado, não-histórico). Histórico `ml/test_results.json` intacto.
