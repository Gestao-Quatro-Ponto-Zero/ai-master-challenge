# Iterations Log

Registro de iterações: hipóteses, erros, correções e mudanças de direção.

---

## Iteração 1 — Descoberta do repositório (FASE 0)
- **Hipótese inicial:** estrutura local espelha o plano das 8 fases. → Confirmada, com 1 lacuna (template de submissão ausente).
- **Quase-erro evitado:** `wc -l` sugeria ~29,8k registros no Dataset 1; contagem via parser CSV revelou 8.469 (campos multi-linha). Lição: nunca confiar em contagem de linhas físicas para CSV com texto livre.
- **Saída:** `docs/project_discovery.md` validado pelo humano antes de avançar.

## Iteração 2 — Setup e auditoria (FASE 1)
- Ambiente: `.venv` estava vazio → instalados pandas, numpy, matplotlib, seaborn, scipy, nbformat, nbclient, ipykernel.
- Abordagem: exploração via scripts → consolidação em notebook executado de ponta a ponta → `data_audit.md` escrito a partir dos outputs reais do notebook (números nunca digitados de memória).
- **Hipótese inicial (implícita no plano):** FRT/TTR seriam durações utilizáveis para medir gargalos. → **Refutada pelos dados**: são timestamps aleatórios em ~3 dias de calendário, com TTR anterior ao FRT em 49,3% dos casos (detalhes em D-005). Mudança de direção registrada para a FASE 3.

## Iteração 3 — Correção de afirmação não verificada (FASE 1)
- **Erro detectado:** a primeira versão do notebook afirmava "nenhum par passa de |ρ| ≈ 0,04" na matriz de correlação, sem que todos os pares tivessem sido conferidos.
- **Verificação:** ao recalcular, encontrou-se ρ = −0,545 entre delta (TTR−FRT) e hora do FRT.
- **Análise:** é artefato mecânico do sorteio de horários no mesmo dia (quanto mais tarde o FRT, mais negativo o delta) — não é sinal operacional; na verdade **reforça** o diagnóstico de dados sintéticos.
- **Correção:** célula de leitura reescrita, título do heatmap ajustado, notebook re-executado por completo. Lição: toda afirmação quantitativa passa por verificação antes de ir ao relatório.

## Iteração 4 — Painel de design da FASE 2 (multi-agente)
- Espec de features escrita ANTES de codificar, com 3 decisões contenciosas marcadas explicitamente.
- Painel de 3 lentes independentes (estatística, negócio/ROI, avaliador G4) executado via workflow multi-agente.
- **Onde a IA-revisora corrigiu a IA-autora:** (a) a lógica `abs(delta) > alvo` para SLA estava conceitualmente errada — regra real não usa `abs()`; (b) a ordenação de AHT Phone 10 < Chat 12 era indefensável (telefone é síncrono 1:1; chat tem concorrência de sessões); (c) faltavam custo/hora, fator de anualização e faixas de sensibilidade — sem eles a FASE 3 não fecharia o ROI.
- Resultado: D-008/D-009 e a implementação final divergem da espec original em pontos materiais. Julgamento humano/agente sênior > primeira ideia.

## Iteração 5 — Erros de implementação pegos por teste/execução (FASE 2)
- **Erro 1 (2×):** `.map()` sobre Series categórica devolve dtype category, que não aceita multiplicação — quebrou em `est_handle_minutes` e depois em `sla_violation` (os testes unitários usavam Series comuns e não pegaram; o notebook com a coluna categórica real pegou). Correção: `.astype(float)` pós-map + teste de regressão com input categórico.
- **Erro 2:** na prova analítica do SLA, o denominador incluía tickets não-Closed (`NaN > t` → False), diluindo a taxa observada ~3× (11,1% vs 34,7% teórico). Correção: `.dropna()` antes da comparação — observado passou a bater com o teórico (32,5% vs 34,7%; 22,4% vs 22,2%), fechando a prova.
- Lição: validação numérica cruzada (teórico vs observado) pega bugs que "parecem funcionar".

## Iteração 6 — Verificação adversarial dos artefatos da FASE 2 (multi-agente)
- 4 verificadores independentes: (1) fórmulas doc×código×testes; (2) recálculo independente de todos os números afirmados, a partir do CSV bruto; (3) aderência ao plano mestre + confirmação item a item dos ajustes D-008/D-009; (4) contradições entre documentos.
- **Achados corrigidos:** (a) [major] média de `est_handle_minutes` escrita como 14,8 no dicionário quando o real é **18,4 min/ticket** (~24% de erro num número que ancora o ROI — pego em paralelo por auto-verificação e por 3 dos 4 verificadores, que recomputaram do zero); (b) [major] `description_demo` com status `measured` furava o próprio guardrail machine-readable (`features_by_status('measured')` a devolveria como feature "livre para modelos") → criado status `demo_only` + teste dedicado; (c) [minor] doc dizia "dtypes anuláveis" onde o delta é float64/NaN — wording corrigido; (d) [minor] notebook citava "12 testes" (real: 13 → 14 após o novo guardrail); (e) [minor] TL;DR do audit imprecisão sobre FRT (existe para Pending também).
- **~40 checagens passaram** sem achados (fórmulas, contagens, percentuais, prova analítica do SLA recomputada, D-008/D-009 confirmados item a item).
- Estado final: 14 testes ✅, notebook re-executado sem erros, parquets regenerados.

## Iteração 7 — FASE 3: painel, implementação e correções pegas em execução
- Painel de 3 lentes sobre a espec do diagnóstico aprovou as 4 decisões contenciosas **com ajustes materiais**: decomposição do backlog (Open≠Pending), rodada demonstrativa separada para colunas sintéticas (D-011), limites de efeito via IC no lugar de "p alto prova nulo", baseline de alvo embaralhado no RF, ramp-up/regime/break-even no ROI e cenários de negócio coerentes (conservador ≠ tudo-low).
- **Erros meus pegos antes do relatório:** (a) o texto da rodada demonstrativa dizia "nada correlaciona" enquanto o output mostrava FRT com p=0,046 — corrigido transformando o falso-positivo previsto em nota metodológica (com BH: p=0,139); (b) o título do tornado dizia "deflexão e AHT dominam" mas o output real mostra implantação (R$ 100k) > AHT (92,8k) > custo/h (71,6k), com deflexão em 5º no ano 1 — título, leitura e recomendação corrigidos e re-executados.
- Kwarg legado `tickets_per_year` seria silenciosamente ignorado pelo novo contrato de overrides → adicionada validação com ValueError + teste de regressão.
- Estado: 27 testes ✅ (14 data_prep + 13 roi_model), notebook de 36 células executado sem erros, 10 gráficos novos.

## Iteração 8 — Verificação da FASE 3 (plano B após limite de sessão)
- A verificação multi-agente (4 verificadores) caiu por limite de sessão da conta. Em vez de re-executar no dia seguinte, foi substituída por um **script de verificação independente** (`verify_fase3.py`): recomputa do zero, a partir do parquet e do modelo, cada número afirmado no `diagnostic_report.md` e compara com o publicado.
- **Resultado: 51 checagens, 0 falhas** — funil, qui-quadrados, Cramér V, satisfação, reincidência, pools de horas, KW demonstrativo, Spearman/IC/MDE, eta², Tukey, OLS/logística, rodada demonstrativa (incl. p_BH do falso-positivo), e todos os números do ROI (cenários, break-evens, payback).
- Lição de processo: verificação numérica é automatizável como script reprodutível; o multi-agente agrega mais nas checagens *qualitativas* (contradições narrativas entre documentos), que aqui já haviam sido feitas manualmente durante a construção.

## Iteração 9 — FASE 4: matriz de automação (inline, sem painel)
- Verificação prévia nos dados evitou uma armadilha: a intenção era ancorar os recortes "dentro do tipo" no cruzamento Subject×Type do D1 — o crosstab mostrou distribuição uniforme (cada um dos 16 subjects aparece igualmente nos 5 tipos: sintético). A matriz foi então fundamentada nos critérios declarados do plano + exemplos reais do D2, com o disclosure explícito no doc (§5).
- Matriz implementada como código (`src/automation.py`) no padrão de fonte única das fases anteriores; tabelas do doc geradas do código e protegidas por teste verbatim (drift no futuro quebra o CI).
- Par didático Access × Administrative rights (D2) usado para provar que a decisão é por natureza do intent, não semelhança de texto — reset de senha automatiza, concessão de privilégio nunca.
- 9 testes novos (36 no total).

## Iteração 10 — FASE 5: ML com restrições de infraestrutura
- **Restrição real contornada:** embeddings de 47,8k docs em CPU (~40 min estimados) × limite de 10 min por execução de shell → `src/embed_corpus.py` **resumável** (memmap + progresso em JSON, sai antes do limite e retoma). Na prática o throughput pós-warmup foi ~5× o benchmark (que incluía o load do modelo) e uma rodada bastou.
- **Bug pego em execução:** `CalibratedClassifierCV` quebrou com dtype arrow-backed do parquet (`ArrowExtensionArray` não aceita indexação por array nos splits internos) → conversão explícita para numpy + registro.
- **Erro meu pego por teste:** expectativa errada num teste de brinquedo do `pick_threshold` (esperava 0,85; a lógica correta dá 0,65) — o código estava certo, o teste foi corrigido com a explicação.
- Resultado honesto registrado: embeddings PERDEM para TF-IDF na classificação deste corpus (texto pré-processado) — em vez de esconder, virou limitação declarada com condição de reavaliação (texto cru).
- 5 testes novos (41 no total), artefatos de produção salvos para a FASE 6.

## Iteração 11 — FASE 6: protótipo Streamlit verificado no browser
- App de 4 páginas montado 100% sobre os módulos testados das fases anteriores (nenhuma lógica de negócio nova no app além de layout) + `src/copilot.py` (orquestração com heurísticas demo rotuladas, 6 testes).
- Correção de performance pega antes do deploy: `embed_texts` instanciava o SentenceTransformer a cada chamada (~5-10s por busca) → singleton em módulo.
- **Verificação funcional no browser (não só "o servidor sobe"):** as 4 páginas foram navegadas e validadas — Copilot executado de ponta a ponta (Access 99% acima do gate, prioridade High por "deadline", equipe IAM, 5 similares sendo 4 da mesma classe, resposta sugerida) e ROI Simulator com números idênticos ao modelo testado (4.404 h, 2,6 FTE, R$ 146 mil regime, payback 17,0m, ROI ano1 −24%).
- **Nota de evolução:** os números de payback/ROI acima pertencem ao modelo inicial da D-012 e foram substituídos pela decisão final D-019 (implantação interna R$ 0).
- Ajustes durante a verificação: deprecação `use_container_width` corrigida em 10 pontos; gramática do template de resposta.
- 47 testes no total, todos passando; `requirements.txt` pinado criado.

## Iteração 12 — Redesign do front-end do protótipo (feedback humano)
- **Feedback do humano:** o app funcional estava visualmente cru ("quero um sistema bonito, clean, atual"). Redesign completo: sistema visual próprio (`src/ui.py`) com tema escuro único e comprometido — paleta dark validada do guia de dataviz, tipografia Inter, KPI cards customizados, chips, callouts com borda de acento, cards de cenário, nav do sidebar como menu, gráficos com template dark coeso (títulos fora do gráfico, barras finas, grid hairline) e cromo do Streamlit oculto.
- **Bugs pegos na verificação em browser:** (a) template plotly com estilo de título sem texto renderizava "undefined" literal em todos os gráficos; (b) fonte Inter não aplicava em headers (especificidade do Streamlit) — seletor reforçado; (c) o CSS que escondia o círculo do radio com `display:none` **removia o input da árvore de acessibilidade** (quebrava teclado/leitor de tela) — trocado por ocultação visual (`width:0; opacity:0`), confirmado que os radios voltaram à árvore.
- **Aprendizado de infra:** Streamlit não recarrega módulos importados (`src/ui.py`) em processos já rodando — verificação exigiu instância nova; usuário orientado a reiniciar o servidor local.
- **Localização histórica:** `src/ui.py` era o helper do worktree da v1. A implementação Streamlit foi usada para comparação durante o desenvolvimento, mas não integra o pacote final.
- Varredura final nas 4 páginas via browser: 0 exceções, Copilot ponta a ponta OK (4 cards, 5 similares, callout, 15 chips), ROI com 7 sliders.

## Iteração 13 — FASE 7: template real obtido e submissão montada
- Pendência aberta desde a FASE 0 (template de submissão ausente na pasta local) resolvida: repo original localizado via busca (`Gestao-Quatro-Ponto-Zero/ai-master-challenge`) e `templates/submission-template.md` baixado — o README da submissão segue a estrutura oficial EXATAMENTE, em vez do fallback planejado.
- Estrutura `submissions/thales-barbosa/` montada autocontida e verificada: suíte de testes completa re-executada DE DENTRO da pasta da submissão (pipeline regenerado ali) para provar reprodutibilidade no formato final.
- FASE 8 (process log) não teve trabalho novo: os 4 arquivos foram mantidos continuamente desde a FASE 0, como o guia exige — apenas copiados para a submissão.

## Iteração 14 — Bug reportado pelo humano: sidebar não reabria após recolher
- **Sintoma:** o botão de recolher a sidebar funcionava, mas o controle de reabrir sumia — usuário ficava preso sem navegação.
- **Causa 1 (o sintoma):** o CSS do redesign escondia `[data-testid="stToolbar"]` inteiro para sumir com o botão "Deploy" — e o controle de reabrir a sidebar vive nessa região do header. Correção: esconder apenas os itens específicos (Deploy, menu, status), nunca o header/toolbar inteiro.
- **Causa 2 (achada na investigação):** o conteúdo da sidebar tinha 133px de overflow horizontal (labels com `width:100%` + padding sem `border-box`) e a animação de recolher/expandir deixava o container com `scrollLeft` deslocado — navegação parcialmente fora da tela ao reabrir. Correção: `box-sizing: border-box` nos itens de menu + `overflow-x: hidden` no conteúdo da sidebar.
- **Verificação:** ciclo completo fechar→reabrir executado em servidor limpo via browser — botão de reabrir visível no estado recolhido, navegação 100% visível ao reabrir, zero exceções. Resíduo cosmético de 10px documentado (overflow fantasma interno do Streamlit, contido pelo `overflow-x: hidden`).
- Correção propagada para a cópia da submissão; 47 testes seguem passando.

## Iteração 15 — Protótipo v2: FastAPI + front "PAUTA" (feedback humano: "SaaS premium")
- **Feedback do humano:** auditoria completa do projeto com foco em UX/UI — a análise foi considerada forte, mas o app "muito feio" para a barra de SaaS premium. Diagnóstico da auditoria: o teto era estrutural (widgets nativos do Streamlit com casca de CSS), não falta de capricho. Confirmado nos docs oficiais que o challenge não exige stack.
- **Decisão (D-017):** trocar só a camada de apresentação; core testado intacto. FastAPI + web/ artesanal.
- **Processo de design com IA:** workflow de 3 conceitos concorrentes + painel julgador → conceito "PAUTA" (editorial). A paleta proposta pelo painel **reprovou** no validador de dataviz (CVD ΔE 3,0; chroma abaixo do piso) — substituída por steps validados (ΔE 41,3, todos os checks PASS). Onde a IA errou e como corrigi: confiar no validador, não no olho do modelo.
- **Bugs pegos na verificação em browser (sondas de DOM/JS):** (a) `requestAnimationFrame` não dispara em aba sem pintura — count-up dos KPIs do ROI nunca escrevia o valor final; corrigido com conclusão garantida via `setTimeout` (robusto também para abas em background); (b) o count-up sobrescrevia o `<span>` de unidade dentro do valor — id movido para span interno; (c) classe `.stamp-sage` referenciada e não definida; (d) linha duplicada no model card do Copilot.
- **Verificação ponta a ponta:** 4 views navegadas; filtro Email → 2.143 tickets com KPIs recalculados; Copilot com exemplo de veto → 3 vetos + carimbo VETADO + 5 similares + rascunho; ROI deflexão 0% → 1.841 h (só assistência, confere com o modelo); console sem erros; sem overflow horizontal. Números conferidos contra o diagnóstico (9.207 h · 5,5 FTE · R$ 368 mil · R$ 146 mil · payback 17,0).
- **Nota de evolução:** a verificação registrou o modelo econômico vigente naquela iteração; a D-019 o substituiu por implantação interna R$ 0 e payback imediato no cenário-base.
- Revisão adversarial de 4 lentes (números×docs, backend, front, UX/a11y) com verificação cética por achado — correções aplicadas antes da sincronização da submissão.

## Iteração 16 — Portal do cliente, perfis e pt-BR de ponta a ponta (análise competitiva)
- **Gatilho humano:** análise do app de outro candidato (Flask com login cliente/admin e "resposta na hora"). Diagnóstico da análise: o *framing* de produto dele é superior (demonstra a deflexão), mas a análise dele fabrica métricas de tempo (soma 24h nos deltas negativos dos timestamps que nossa auditoria provou serem sorteio) e a "busca semântica" é TF-IDF sobre ~14 FAQs com stopwords em inglês para texto pt. Decisão: roubar o fluxo, não os números (D-018).
- **Onde a IA errou e como foi corrigido (registro honesto):** na primeira verificação do pipeline multilíngue, TODO texto vago em pt-BR classificava como Hardware com 100% de confiança (atrator da classe majoritária + LogReg C=10 superconfiante) — o gate de confiança sozinho deixava passar. O diagnóstico via similaridade máxima da busca (0,47 no vago vs 0,6–0,8 nos casos reais) levou à **dupla trava** (gate + piso de evidência 0,55), verificada: vago agora cai em triagem humana.
- **Bug de infra pego:** script de treino morria em `UnicodeEncodeError` no console cp1252 do Windows (seta →) APÓS avaliar e ANTES de salvar artefatos — re-rodado com PYTHONIOENCODING=utf-8.
- **Verificação ponta a ponta (API + UI):** login dos 2 perfis com visões distintas (cliente: só Central de Ajuda; admin: 5 telas); pergunta pt-BR "senha" → Access 99% autoatendimento; vago → humano (evidência); advogado → 3 vetos + prioridade elevada High; chamado #2 aberto pela UI com contexto; resolução na Fila → base de conhecimento (toast + contadores); **reask de "cobrança duplicada" devolveu a resolução humana aprendida (sim 0,72), inclusive após restart do servidor** (KB re-embeddada do SQLite). 47 testes passando; console sem erros.
- Exemplos do Copilot/portal reescritos em pt-BR e **curados com verificação** (fraseado de Storage testado até classificar certo; exemplo de Purchase trocado por um que demonstra o gate honestamente).

## Iteração 17 — Auditoria pré-submissão e correções aprovadas em gates
- **Gatilho humano:** conferir exatamente o pacote exigido, comparando documentos oficiais, template e estrutura de outro candidato; depois corrigir item a item, cada alteração sujeita a aprovação.
- **Correção 1 — ROI:** removido o cenário de implantação externa. A implantação passou a R$ 0 em código, testes, notebook, relatório, interface e README. Base recalculada: R$ 84,5 mil líquidos no ano 1, ROI 282%, payback imediato; regime R$ 146,2 mil/ano e ROI 487%.
- **Correção 2 — reprodutibilidade:** criado `solution/bootstrap.py`. A execução limpa confirmou retomada do embedding interrompido, ordem correta do pipeline e artefato multilíngue final; uma segunda execução confirmou idempotência. Dependência ausente (`itsdangerous`) foi explicitada.
- **Validação real:** 51 testes passaram; notebook diagnóstico executou 20/20 células de código sem erro; JavaScript passou na checagem de sintaxe; servidor respondeu com `ready=true`; homepage, login admin, endpoint protegido e portal foram testados. Um texto de senha foi para autoatendimento e um texto vago foi bloqueado pelo piso de evidência.
- **Limitação observada:** a sonda pt-BR de cinco exemplos acertou três; dois intents ainda confundem classes. O achado foi mantido como limitação e reforça a necessidade de piloto, dados pt-BR rotulados e monitoramento.
- **Correção 3 — rastreabilidade:** plano mestre incorporado ao process log; ferramentas, contagens, artefatos atuais e natureza das screenshots corrigidos; referências antigas preservadas somente quando identificadas como histórico.

<!-- Novas iterações devem ser adicionadas abaixo, sem reescrever o histórico. -->
