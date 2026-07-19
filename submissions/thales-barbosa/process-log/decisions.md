# Decision Log

Decisões de projeto com contexto, alternativas e justificativa. Atualizado continuamente.

---

## D-001 — Tratar o Dataset 1 como amostra de uma operação de 30k tickets/ano
**Fase:** 0 · **Data:** 2026-07-16
**Contexto:** O brief afirma ~30.000 registros; o arquivo real tem 8.469.
**Decisão:** Usar os 8.469 como amostra representativa e extrapolar volumes/custos para 30k tickets/ano no modelo de ROI, com a premissa explícita.
**Alternativa descartada:** ignorar a discrepância (violaria a regra "tudo comprovado pelos dados").

## D-002 — Dataset 2 como corpus principal de NLP
**Fase:** 0 · **Data:** 2026-07-16
**Contexto:** O texto do Dataset 1 é sintético (placeholders `{product_purchased}`, frases desconexas). O Dataset 2 tem 47.837 tickets reais rotulados.
**Decisão:** Classificador e busca semântica (FASE 5) serão treinados/avaliados no Dataset 2; o Dataset 1 fornece métricas operacionais e distribuições de negócio.

## D-003 — Process log iniciado na FASE 1 e atualizado a cada fase
**Fase:** 1 · **Data:** 2026-07-16
**Contexto:** O guia de submissão exige evidência de processo contínuo (1 prompt → 1 resposta = submissão fraca).
**Decisão:** `process-log/` criado agora com 4 arquivos vivos, atualizados no fechamento de cada fase.

## D-004 — Gráficos salvos em `docs/assets/` durante as fases de análise
**Fase:** 1 · **Data:** 2026-07-16
**Contexto:** A estrutura final (`submissions/thales-barbosa/solution/assets/`) só é montada na FASE 7.
**Decisão:** Trabalhar em `docs/assets/` agora e mover tudo na FASE 7, evitando caminhos quebrados durante o desenvolvimento.

## D-005 — FRT/TTR tratados como timestamps sintéticos; Hipóteses A e B rejeitadas
**Fase:** 1 · **Data:** 2026-07-16
**Contexto:** O plano exigia testar se `Time to Resolution` é tempo total (A) ou tempo pós-1ª-resposta (B).
**Evidências:** colunas são timestamps, não durações; TTR < FRT em 49,3% dos Closed; correlação FRT×TTR ≈ 0,06; todos os eventos em 3 dias de calendário (96% em 01/jun/2023); delta com distribuição triangular ±24h (assinatura de duas uniformes independentes); não existe timestamp de abertura do ticket.
**Decisão:** rejeitar ambas as hipóteses e classificar as colunas como horários aleatórios sintéticos. Nenhuma métrica de duração derivada delas fundamenta decisão de negócio.
**Consequência:** o diagnóstico da FASE 3 será ancorado em volume, mix canal×tipo×prioridade, taxas de status e satisfação, com benchmarks externos declarados como premissa para conversão em horas/custo.

## D-006 — Nulos estruturais não serão imputados
**Fase:** 1 · **Data:** 2026-07-16
**Contexto:** FRT/TTR/Resolution/Satisfação têm nulos que dependem 100% do `Ticket Status` (Open: tudo nulo; Pending: só FRT presente; Closed: tudo presente).
**Decisão:** tratar como "não se aplica" (MNAR por design), nunca imputar. Análises de satisfação/tempo usam apenas os 2.769 Closed, com a restrição documentada.

## D-007 — Diretrizes de ML fixadas pela auditoria do Dataset 2
**Fase:** 1 · **Data:** 2026-07-16
**Contexto:** Dataset 2 tem 8 classes com desbalanceamento 7,7:1 (Hardware 28,5% vs Administrative rights 3,7%) e 14 docs com <3 palavras.
**Decisão:** FASE 5 usará split estratificado, macro-F1 + F1 por classe como métricas principais, filtro de docs <3 palavras e atenção especial à classe guarda-chuva `Miscellaneous` (threshold de confiança para triagem humana).

## D-008 — Espec da FASE 2 revisada por painel de 3 lentes antes da implementação
**Fase:** 2 · **Data:** 2026-07-16
**Contexto:** A espec de feature engineering tinha 3 decisões contenciosas (herança do D-005). Submetida a um painel multi-agente com lentes independentes: rigor estatístico, negócio/ROI e avaliador do challenge.
**Vereditos e ajustes incorporados:**
1. `response_minutes`/`total_handling_minutes` → **N/A documentado** (sem timestamp de abertura), com tabela de rastreabilidade cobrindo as 7 features-exemplo do plano e recomendação de instrumentação (`created_at`) ao cliente. Colunas 100% NaN foram rejeitadas (burocracia + risco de uso acidental).
2. Marcação sintética **no nome** (`synthetic_`) + dicionário machine-readable `FEATURE_STATUS` (measured / synthetic_demo / assumption / target_derived) consultável pela FASE 3+.
3. Premissas com **faixa low/base/high**, definição operacional (minutos de agente, ciclo completo, chat ajustado por concorrência), ordenação corrigida (Email 18 > Phone 15 ≈ Social 15 > Chat 10 — a proposta original Phone 10 < Chat 12 não sobrevivia a sabatina), custo/hora do agente (R$ 30/40/55) e fator de anualização (3,542) adicionados como fonte única em `src/data_prep.py`.
4. Contradição com `data_audit.md` §2.4 reconciliada (o audit prometia criar as features de tempo do plano; a decisão final é N/A + prefixo sintético — §2.4 atualizado com nota de revisão).
5. Features negadas fechadas como **classe** (toda agregação temporal), não caso a caso; `is_rated ≡ is_closed` documentada como identidade estrutural.

## D-009 — `sla_violation` NÃO é materializada como coluna; mecanismo real como função pura
**Fase:** 2 · **Data:** 2026-07-16
**Contexto:** O plano pedia `sla_violation`. A proposta original (abs(delta) > alvo, sufixo `_demo`) foi rejeitada pelo painel: (a) `abs()` não é a regra real de SLA (durações reais são ≥ 0; a regra é `duração > alvo`); (b) uma taxa de violação materializada sobre delta sintético viraria "métrica real" no primeiro screenshot.
**Decisão:** implementar `sla_violation(duration_minutes, priority, targets)` como função pura com a regra de produção (negativos = input inválido → NA), coberta por testes unitários; **nenhuma coluna de SLA no parquet** (garantido por teste); demonstração tripla no notebook, incluindo a prova analítica `P(delta > t) = (1−t/24)²/2` — verificada: Critical 34,7% teórico vs 32,5% observado; High 22,2% vs 22,4%.
**Guardrail:** nenhum agregado/gráfico de SLA sobre tempos sintéticos nas fases 3–7.

## D-010 — P1 recomposta em sinais válidos; exigências de tempo cumpridas em seção demonstrativa rotulada
**Fase:** 3 · **Data:** 2026-07-16
**Contexto:** O plano exige tempos médios/medianas/percentis/heatmaps por segmento, mas D-005 provou que os tempos são sintéticos. Painel de 3 lentes aprovou a recomposição com ajustes.
**Decisão:** (a) resposta principal ancorada em funil de status **decomposto** (Open 33,3% = sem 1ª resposta ≠ Pending 34,0% = esperando cliente — duas alavancas), uniformidade testada com qui-quadrado + Cramér V + MDE, satisfação com IC e pools de horas premissa-based; (b) seção demonstrativa entrega LITERALMENTE tudo que o plano pede (média/mediana/P25-P95/heatmap/tabelas, delta E FRT) com **marca d'água dentro dos PNGs**; (c) sinais válidos primeiro, demonstrativa por último; (d) disclosure simétrico (uniformidade sintética vale para backlog/satisfação também); (e) leitura de snapshot, não de fluxo/aging.

## D-011 — Exceção formal: colunas sintéticas em análises, restrita à rodada demonstrativa
**Fase:** 3 · **Data:** 2026-07-16
**Contexto:** O plano manda testar FRT/TTR contra satisfação; o guardrail da FASE 2 proíbe `synthetic_demo` em modelos. Contradição apontada pelo painel.
**Decisão:** análises principais da P2 (OLS/RF/ANOVA/Spearman) rodam SEM colunas sintéticas; a exigência do plano é cumprida numa **rodada demonstrativa separada e rotulada** (Spearman rating × FRT/TTR/delta) com correção BH própria. Política de múltiplas comparações pré-declarada (BH por família) — e funcionou: o FRT saiu com p=0,046 sem correção (falso-positivo previsto; p_BH=0,139, |ρ|=0,038 < MDE 0,053).

## D-012 — Modelo de ROI inicial: ramp-up, regime, break-even e cenários de negócio coerentes — **SUPERADA PELA D-019**
**Fase:** 3 · **Data:** 2026-07-16
**Contexto:** Painel exigiu completar o modelo econômico para sobreviver a sabatina de diretor.
**Decisão:** `src/roi_model.py` ganhou: (a) **ramp-up ano 1** (50/65/80%) separando ROI ano-1 de ROI de regime; (b) **cenários de negócio** pareando economia-low com custo-high (conservador) — `roi_scenario('low')` uniforme fica só para sensibilidade; (c) **break-even de deflexão** (ano 1: 62,7% — investimento mesmo; regime: 8,1% — paga com folga); (d) volume anual no tornado (±20%); (e) run cost com escopo declarado (tokens+plataforma+sustentação, sobre 100% dos tickets — sem 3º componente de custo, evitando falsa precisão); (f) deflexões como **fonte única** com mini-racional por tipo no docstring, importadas pela FASE 4; (g) economia comunicada como **capacidade liberada** (captura exige realocação — recomendada: backlog Open); (h) validação de overrides desconhecidos (kwarg errado levanta ValueError em vez de ser ignorado). Resultado honesto: ano 1 negativo no base (−R$ 35k), regime +R$ 146k/ano, payback 17 meses, conservador não se paga → recomendação de piloto com gates. *(Nota: a premissa de implantação externa foi revisada depois — ver D-019: construção interna pelo AI Master, implantação R$ 0; os números deste registro refletem a decisão na data.)*
**Status:** esta foi a primeira formulação, com custo externo de implantação. A D-019 substituiu integralmente essa premissa econômica; os números acima permanecem apenas como registro histórico da iteração e **não são usados na entrega final**.

## D-013 — Matriz de automação como código (fonte única) com guarda anti-drift
**Fase:** 4 · **Data:** 2026-07-17
**Contexto:** O painel da FASE 3 exigiu que a matriz da FASE 4 importasse as constantes de deflexão (nunca redigitasse) e fosse coberta por teste de consistência.
**Decisão:** matriz vive em `src/automation.py` (tiers, critérios 1-5 do plano, o-que-automatiza/nunca-automatiza por tipo, 6 regras transversais de veto, roteamento das 8 classes do D2); as tabelas do `automation_strategy.md` são **geradas** por `render_*_markdown()` e um teste compara doc↔código **verbatim**. Invariantes testadas: ordenação tier↔deflexão monotônica; `julgamento_humano ≥ 4` bloqueia automação plena; Miscellaneous nunca defletida (D-007); vetos cobrem Critical e risco legal.
**Princípio de desenho registrado:** decisão por camada e intent — triagem 100% automática em todos os tiers (ataca os 33,3% Open); resolução segue a matriz; vetos têm precedência sobre tudo.
**Disclosure:** recortes por intent derivam de critérios declarados, não de frequências do D1 (Subject×Type é uniforme/sintético — verificado antes de escrever a matriz).

## D-014 — Classificador: TF-IDF+LogReg vence por simplicidade em empate técnico; gate em 0,50
**Fase:** 5 · **Data:** 2026-07-17
**Contexto:** Plano exige comparar TF-IDF, Sentence Transformers e Embeddings com accuracy/precision/recall/F1.
**Resultados (teste estratificado n=9.565):** tfidf_linsvc macro-F1 0,8669 · tfidf_logreg 0,8652 · embed_logreg (MiniLM) 0,8118.
**Decisão:** diferença < 0,005 = empate técnico (critério pré-declarado no script de treino) → desempate por simplicidade operacional: **tfidf_logreg** (probabilidades nativas, sem camada de calibração, treino em segundos). Embeddings perderam na classificação porque o texto do D2 é pré-processado (formato que favorece bag-of-words) — mas seguem na **busca semântica** (FAISS, 47.823 docs), onde a qualidade é visivelmente alta.
**Gate de confiança:** threshold 0,50 → 90,4% de cobertura com accuracy 90,2% nos cobertos; os 9,6% abaixo do gate concentram Miscellaneous (19,1% vs 14,8% da base) — o gate implementa mecanicamente a regra da FASE 4 (guarda-chuva → humano). Registrado: existem erros com confiança 1,0 → QA amostral e escape hatch continuam obrigatórios.

## D-015 — Protótipo: componentes de demonstração rotulados; SLA honesto no dashboard
**Fase:** 6 · **Data:** 2026-07-17
**Contexto:** O plano exige que o Copilot devolva prioridade e resposta sugerida, mas o corpus de treino (D2) não tem rótulo de prioridade nem base de conhecimento para RAG; e o Dashboard Executivo pede "SLA" com tempos que a auditoria provou serem sintéticos.
**Decisão:** (a) prioridade sugerida = heurística por palavras-chave e resposta sugerida = template por classe + citação dos semelhantes — ambas **rotuladas como demo na própria UI**, com o caminho de produção declarado (modelo treinado com rótulos reais; LLM+RAG sob os mesmos vetos e gate); (b) o card de SLA mostra a matriz de alvos + aviso explicando por que não há % de violação (D-009) e o que instrumentar para ligá-lo; (c) nenhum número do app deriva de features sintéticas — todos os cards vêm dos módulos testados (`data_prep`, `roi_model`, `automation`, `ticket_ai`), com a nota de premissas fixa na sidebar; (d) vetos da FASE 4 aplicados no Copilot por detecção textual (demo), com o exemplo "cliente irritado + advogado" pré-carregado para o avaliador ver o veto disparar.

## D-016 — Estrutura da submissão: autocontida, com dados brutos e sem artefatos pesados
**Fase:** 7 · **Data:** 2026-07-17
**Contexto:** A submissão vai por PR ao repo do G4 (`Gestao-Quatro-Ponto-Zero/ai-master-challenge`); o template oficial foi obtido do repo original (pendência da FASE 0 resolvida) e o README o segue exatamente, com as 10 seções do plano mestre embutidas nas suas seções.
**Decisões de empacotamento:** (a) `solution/` é autocontida — src, notebooks, tests, docs (com assets), app, requirements; os caminhos relativos do código continuam válidos porque a raiz do módulo (`ROOT = parents[1]`) passa a ser `solution/`; (b) os **2 CSVs brutos vão juntos** (18 MB, licença CC0 — o avaliador roda o pipeline sem depender do Kaggle); (c) `data/processed/` e `models/` **ficam fora** (regeneráveis por 3 comandos documentados; embeddings ~10 min em CPU); (d) process-log copiado na íntegra; evidências declaradas: narrativa escrita + git history + notebooks comentados (formatos aceitos pelo guia).
**Status atual:** a D-020 simplificou a regeneração para `python bootstrap.py` e retirou Git da lista de evidências até que o histórico final seja efetivamente criado. A descrição acima permanece como registro do empacotamento naquela iteração.

## D-017 — Protótipo v2: troca da camada de apresentação (Streamlit → FastAPI + front artesanal "PAUTA")
**Fase:** 6 (revisão) · **Data:** 2026-07-18
**Contexto:** Auditoria do protótipo v1 com feedback humano ("deve parecer um SaaS premium; está feio"): mesmo com o redesign da iteração 12, o app lia como "dashboard de framework" — widgets nativos do Streamlit com casca de CSS, navegação por radio, cromo vazando (Deploy/menu), sem identidade de produto. Verificado nos documentos oficiais do challenge que **nenhuma stack é exigida** (o protótipo é "diferencial"; "qualquer ferramenta é permitida") — Streamlit era decisão do plano mestre do autor, não regra do G4.
**Decisão:** trocar **apenas a camada de apresentação**, preservando 100% do core testado: FastAPI expõe uma API JSON fina (`/api/bootstrap`, `/api/operational`, `/api/copilot`, `/api/roi`) sobre os módulos das fases 2–5; front artesanal em `web/` (HTML/CSS/JS puro, sem build, sem CDN em runtime — ECharts e fontes vendorados). Setup do avaliador continua 1 comando (`python app.py`). A v1 foi mantida durante o desenvolvimento para comparação e retirada do pacote final para evitar código sem uso.
**Processo de design:** painel de 3 conceitos independentes (editorial data-journalism, command center, minimal fintech) julgado por 3 lentes (CEO/engenheiro/avaliador G4) → vencedor **PAUTA** (metáfora editorial: cada ticket é uma história; o console é a redação) com enxertos dos perdedores (pipeline de loading honesto, chips de exemplo, disciplina pt-BR, recálculo vivo). Paleta categórica **validada pelo validador do guia de dataviz** (a proposta original do painel FALHOU nos checks de CVD/chroma — substituída por steps validados na superfície dark, pior ΔE adjacente 41,3; regra "cores se computam, não se estimam").
**Guardrails mantidos:** nenhum número redigitado (tudo computado dos módulos ou de `models/metrics.json`); rótulos de demo/premissa na própria UI; notas de rodapé vivas ligando cada número à sua fonte metodológica (D-005/D-009/D-011 continuam valendo).

## D-018 — Portal do cliente com perfis + pipeline multilíngue + dupla trava de segurança
**Fase:** 6 (extensão) · **Data:** 2026-07-19
**Contexto:** Análise do app de um concorrente (Flask, perfil cliente/admin) mostrou um diferencial real de *framing*: ele demonstra a deflexão acontecendo (cliente pergunta → IA responde → escala qualificado), enquanto nosso protótipo era só back-office. Decisão do humano: adotar o fluxo de produto sem herdar os defeitos dele (o diagnóstico dele fabrica durações a partir dos timestamps sintéticos com `raw + 24h` nos negativos — exatamente o que a nossa FASE 1 provou ser inválido).
**Decisões:**
(a) **Perfis por sessão** (login demo cliente/admin, senhas via env): cliente vê só a Central de Ajuda; admin vê as 4 telas + Fila de Chamados. Endpoints analíticos gated por perfil.
(b) **Portal do cliente**: pergunta em pt-BR → classificação + busca semântica → 3 modos honestos: `selfservice` (playbook por classe + casos parecidos), `low_conf` (gate/evidência → humano) e `veto` (regras FASE 4 → humano com prioridade elevada). Chamado abre com contexto, categoria, confiança e prioridade.
(c) **Loop de aprendizado**: resolução humana validada (mín. 10 caracteres — o concorrente aceitava lixo) é embeddada na hora e persiste em SQLite; a próxima pergunta parecida devolve a resolução da equipe (verificado: similaridade 0,72 no reask, sobrevive a restart).
(d) **Pipeline multilíngue**: embedder trocado para `paraphrase-multilingual-MiniLM-L12-v2` (corpus re-embeddado, 47.823 docs) e classificador re-treinado sobre embeddings. Trade-off declarado: F1 macro em inglês cai de 0,865 (TF-IDF) para **0,784**, gate recalibrado para **0,70** (cobertura 64%, accuracy 91,7% nos cobertos) — o ganho é pergunta pt-BR encontrar tickets em inglês no mesmo espaço. Baseline inglês preservado em `models/en_baseline/`.
(e) **Dupla trava (achado da verificação):** em texto vago/fora de domínio, o classificador cross-lingual fica **superconfiante na classe majoritária** (ex.: "oi, sobre aquilo que a gente conversou" → Hardware 100%). A trava de confiança sozinha não pega; adicionado **piso de evidência da busca** (similaridade máxima ≥ 0,55) — sem caso de apoio no arquivo, a ação automática é bloqueada e o caso vai a humano. Vetos e prioridade com padrões bilíngues; veto eleva prioridade Low/Medium → High (coerência com FASE 4 §3).
(f) **R$ na Mesa de Operações**: coluna "R$ defletíveis/ano" (horas defletíveis × custo/hora base) — diferente do concorrente, derivada do modelo de premissas declaradas, não de tempos fabricados.

## D-019 — Reframe econômico: economia operacional em primeiro plano; implantação interna (AI Master)
**Fase:** 6 (revisão) · **Data:** 2026-07-19
**Contexto:** Feedback do humano sobre os cards executivos de ROI: o brief pede quantificar desperdício em horas/custo e estimar economia ("automação X economiza Y horas/mês") — **não pede** estimativa de investimento; e no contexto da vaga, quem constrói a solução é o próprio AI Master já no headcount, não um time externo contratado — o custo de construção é absorvido pela folha, não é caixa novo.
**Decisão final:** (a) os cards executivos mostram **cenários de economia** — variam performance da automação (deflexão + assistência) e custo recorrente: horas liberadas/ano, R$/ano brutos e FTE, com a linha "líquido de tokens/plataforma"; (b) implantação incremental fica **fixa em R$ 0 em todos os cenários**, pois a construção é interna pelo AI Master já no headcount; (c) o slider de implantação externa é removido; (d) payback é imediato quando o líquido do ano 1 é positivo e "nunca" quando não é; (e) código, testes, notebook, relatório, README e interface usam exclusivamente esta premissa.
**Resultado recalculado (base):** ano 1 líquido **R$ 84,5 mil**, ROI ano 1 **282%**, payback **imediato**; regime líquido **R$ 146,2 mil/ano**, ROI **487%**. O conservador segue negativo devido à combinação de performance baixa e custo recorrente alto.
**Registro honesto:** a faixa de implantação 80/120/180 mil foi uma premissa autoral inicial para construção dedicada e está preservada somente no histórico da D-012. Ela foi rejeitada pelo humano por não representar o contexto da vaga e não aparece como cenário vigente.

## D-020 — Auditoria pré-submissão: bootstrap único e process log autocontido
**Fase:** 7–8 (revisão) · **Data:** 2026-07-19
**Contexto:** A comparação com a estrutura de outro candidato e com os documentos oficiais mostrou que a análise estava forte, mas a entrega ainda exigia vários comandos manuais, citava um plano mestre fora da pasta submetida e continha referências ao protótipo antigo.
**Decisão:** (a) criar `solution/bootstrap.py` como entrada única, retomável e idempotente para preparar dados, embeddings e modelos; (b) manter o baseline inglês durante o treino, mas garantir que o artefato servido ao final seja o classificador multilíngue; (c) adicionar `process-log/project-plan.md`, tornando a principal instrução humana parte da submissão; (d) atualizar o registro sem apagar as versões históricas, marcando decisões superadas; (e) não apresentar Git como evidência enquanto o histórico final não existir.
**Validação:** bootstrap completo executado a partir de artefatos ausentes em cerca de 27 minutos e repetido em 0,1 s; 51 testes passando; notebook diagnóstico sem erros; app real com API saudável, login, endpoint protegido e dois fluxos do portal testados.
**Limitação registrada:** uma sonda exploratória curta em pt-BR acertou 3 de 5 intenções; o sistema permanece protótipo com dupla trava e escalonamento humano, não classificador pronto para produção.

<!-- Novas decisões devem ser adicionadas abaixo, sem reescrever o histórico. -->
