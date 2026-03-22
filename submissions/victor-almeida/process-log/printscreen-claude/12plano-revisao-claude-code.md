Plano: Revisão e Melhoria dos Testes Playwright — Lead Scorer                                                                                                                                                                             
                                                                                                 
 Contexto                            

 Os testes E2E em testes/ validam a aplicação Lead Scorer contra os critérios do Challenge 003. A aplicação é um Streamlit com scoring de 5 componentes, filtros hierárquicos, NBA, deal zumbi, e explainability. Os testes precisam
 garantir que tudo isso funciona de verdade — não apenas que textos existem na página.

 ---
 Análise dos Testes Atuais

 O que está BOM

 ┌─────────────────────────────────────────────────────────────┬──────────────────────────────────────────────┐
 │                           Aspecto                           │                  Avaliação                   │
 ├─────────────────────────────────────────────────────────────┼──────────────────────────────────────────────┤
 │ Estrutura em 7 grupos mapeando os 5 critérios do challenge  │ Excelente                                    │
 ├─────────────────────────────────────────────────────────────┼──────────────────────────────────────────────┤
 │ Helpers (waitForStreamlit, selectInSidebar, getMetricValue) │ Bem escritos, conhecem a estrutura Streamlit │
 ├─────────────────────────────────────────────────────────────┼──────────────────────────────────────────────┤
 │ Anti-jargão (3.5)                                           │ Teste inteligente — valida UX de verdade     │
 ├─────────────────────────────────────────────────────────────┼──────────────────────────────────────────────┤
 │ Console errors (7.1) com filtro de erros benignos           │ Pragmático                                   │
 ├─────────────────────────────────────────────────────────────┼──────────────────────────────────────────────┤
 │ Mobile viewport (7.3)                                       │ Diferencial real                             │
 ├─────────────────────────────────────────────────────────────┼──────────────────────────────────────────────┤
 │ Constantes EXPECTED com dados reais do dataset              │ Boa preparação                               │
 └─────────────────────────────────────────────────────────────┴──────────────────────────────────────────────┘

 Problemas CRÍTICOS

 1. Constantes EXPECTED declaradas mas NUNCA usadas

 const EXPECTED = {
   totalActiveDeals: 2089,
   totalAgents: 35,
   generalWinRate: 63.2,
   // ... tudo isso nunca é verificado
 };
 Impacto: Zero validação de dados reais. A app poderia mostrar números inventados e os testes passariam.

 2. Helper selectInSidebar definido mas NUNCA chamado

 O helper mais importante (interagir com filtros) existe mas nenhum teste o usa. Os testes de filtro só verificam que widgets existem — nunca interagem.

 3. Testes sem assertion (sempre passam)

 - 6.2 (Visão manager) — só console.log, sem expect(). SEMPRE passa.
 - 6.4 (Seller-Deal Fit) — mesmo problema. SEMPRE passa.

 4. Testes com assertion fraca (quase sempre passam)

 - 2.2 (Scores 0-100) — só verifica que a palavra "score" existe na página. Não extrai nenhum valor numérico.
 - 2.4 (Ordenação por score) — só verifica que a tabela tem células. Não verifica ordenação.
 - 5.4 (Contagem pós-filtro) — regex /\d+/ no sidebar sempre passa (sliders têm números).

 5. Fallback que mascara falha

 - 4.5 (Deal detail) — se não encontra expanders, dá console.log e passa. Deveria falhar ou testar alternativa concretamente.

 Testes que FALTAM

 ┌────────────────────────────────────────────────────────────────────────┬───────────────────────────────────────────────────────────────────────────────────────────────────┬────────────┐
 │                             Teste Faltando                             │                                           Justificativa                                           │ Prioridade │
 ├────────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────┼────────────┤
 │ Interação com filtros (selecionar região → verificar que dados mudam)  │ Filtro hierárquico é feature central do PRD. Testar presença sem interação é insuficiente.        │ ALTA       │
 ├────────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────┼────────────┤
 │ Cascata de filtros (região filtra managers, manager filtra vendedores) │ É o principal diferencial de UX. Se quebrar, a ferramenta é inútil.                               │ ALTA       │
 ├────────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────┼────────────┤
 │ Validação de dados reais (usar EXPECTED)                               │ Sem isso, não sabemos se a app carregou os dados certos.                                          │ ALTA       │
 ├────────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────┼────────────┤
 │ Seleção de deal + breakdown (clicar deal → ver 5 componentes)          │ Explainability é requisito obrigatório. Precisa testar que funciona, não só que palavras existem. │ ALTA       │
 ├────────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────┼────────────┤
 │ Score numérico real (0-100)                                            │ Extrair valores da tabela e verificar range                                                       │ MÉDIA      │
 ├────────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────┼────────────┤
 │ Paginação (app tem 25 deals/página)                                    │ Feature implementada mas não testada                                                              │ MÉDIA      │
 ├────────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────┼────────────┤
 │ NBA ao selecionar deal                                                 │ Verificar que recomendação aparece com texto acionável                                            │ MÉDIA      │
 ├────────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────┼────────────┤
 │ Filtro por score (slider)                                              │ Mover slider → verificar que deals fora do range somem                                            │ MÉDIA      │
 ├────────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────┼────────────┤
 │ Performance de filtro                                                  │ Filtrar → resultado em < 3s                                                                       │ BAIXA      │
 └────────────────────────────────────────────────────────────────────────┴───────────────────────────────────────────────────────────────────────────────────────────────────┴────────────┘

 ---
 Problemas Estruturais

 Config vs. realidade

 - playwright.config.ts define testDir: "./tests/e2e" mas o spec está em testes/lead_scorer.spec.ts (raiz)
 - webServer.cwd: "." deveria apontar para submissions/victor-almeida/solution/
 - BASE_URL duplicado (config e spec)

 ---
 Plano de Ação

 Fase 1 — Corrigir o que está errado

 1. Corrigir config — testDir, webServer.cwd, remover BASE_URL duplicado do spec
 2. Adicionar assertions nos testes 6.2 e 6.4 — transformar console.log em expect()
 3. Corrigir teste 4.5 — remover fallback silencioso, ou testar alternativa real
 4. Fortalecer teste 2.2 — extrair valores numéricos da tabela e verificar range 0-100
 5. Fortalecer teste 2.4 — extrair primeiros N scores e verificar que estão em ordem decrescente

 Fase 2 — Adicionar testes de dados reais

 6. Novo teste 1.6: Dados reais carregados corretamente
   - Verificar que métrica de deals ativos = ~2089
   - Verificar que win rate geral ≈ 63.2%
   - Usar as constantes EXPECTED já definidas

 Fase 3 — Adicionar testes de interação

 7. Novo teste 5.5: Cascata de filtros funciona
   - Selecionar região "Central" → verificar que managers da lista são só os de Central
   - Usar selectInSidebar (finalmente!)
 8. Novo teste 5.6: Filtro muda dados da tabela
   - Contar deals antes → aplicar filtro → contar deals depois → verificar que mudou
 9. Novo teste 5.7: Slider de score filtra
   - Verificar interação com slider (se possível via Streamlit)
 10. Novo teste 4.6: Seleção de deal mostra breakdown
   - Clicar em um deal na pipeline → verificar que painel de detalhe aparece com 5 componentes
 11. Novo teste 4.7: NBA aparece ao selecionar deal
   - Selecionar deal → verificar que recomendação tem texto acionável específico

 Fase 4 — Testes de paginação

 12. Novo teste na pipeline: Paginação funciona
   - Verificar que existe controle de página
   - Clicar próxima página → verificar que deals mudam

 Localização dos arquivos

 - Config: testes/playwright.config.ts
 - Spec principal: testes/lead_scorer.spec.ts (ou mover para testes/tests/e2e/)
 - Todos dentro de testes/ — fora da pasta de submissão

 Verificação

 1. Corrigir o cwd do webServer para apontar à solution
 2. Rodar npx playwright test com a app ativa
 3. Todos os testes devem executar (não skipar)
 4. Testes novos de interação devem ser resilientes ao timing do Streamlit (waits adequados)