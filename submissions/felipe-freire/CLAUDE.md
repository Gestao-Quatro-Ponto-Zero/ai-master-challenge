# Social Media Intelligence — instruções do projeto

## Identidade e missão

Este projeto resolve o Challenge 004: transformar dados de aproximadamente 52 mil posts em decisões auditáveis sobre engajamento, patrocínio, audiência e estratégia de conteúdo. A entrega deve permitir que o Head de Marketing entenda em cinco minutos o que fazer, por quê, com qual confiança e sob quais limitações.

## Fonte de verdade e escopo

- Brief: `../../challenges/marketing-004-social/README.md`.
- Arquitetura e gates: `docs/agent-architecture.md`.
- Contrato entre agentes: `docs/handoff-protocol.md`.
- Dados brutos são imutáveis em `data/raw/`; derivados ficam em `data/processed/`.
- Toda afirmação quantitativa deve apontar para um artefato reproduzível em `outputs/`.
- Ausência de dados de custo não autoriza chamar alcance ou engajamento de ROI. Use “eficiência” ou “uplift associado” e declare a limitação.
- Dados observacionais não demonstram causalidade. “Causou” só é permitido com desenho causal defensável e aprovado.

## Fluxo obrigatório

Execute o Orchestrator como agente principal: `claude --agent orchestrator`.

Fluxo nominal: Planner → Data Engineer → Software Engineer (fundação) → Data Analyst → Statistician → Marketing Strategist → ML Engineer (condicional) → Dashboard Builder → Software Engineer (consolidação) → Executive Writer → Reviewer → GitHub Publisher (somente com autorização humana).

Nenhuma etapa começa sem o gate anterior em estado `PASS`. `CONDITIONAL_PASS` exige pendências explícitas e sem impacto nas conclusões; `FAIL` retorna ao agente proprietário. O Orchestrator coordena, mas não analisa, programa nem interpreta.

Se ocorrer `API Error: Connection closed mid-response` ou qualquer interrupção de streaming, marque a execução corrente como `INCOMPLETE`. Verifique arquivos, manifest e testes antes de retomar; nunca infira `PASS` a partir de uma resposta truncada.

## Regras globais

1. Não invente valores, colunas, unidades, custos, datas, amostras ou resultados.
2. Inspecione schema e dicionário antes de escrever análise.
3. Preserve o grão do dado e documente todas as transformações.
4. Compare patrocinado e orgânico controlando, no mínimo, plataforma, período, categoria, tipo de conteúdo e faixa de seguidores; registre suporte comum.
5. Diferencie análise exploratória, confirmatória, preditiva e causal.
6. Reporte tamanho de efeito, incerteza, tamanho amostral e ajuste de múltiplas comparações; p-valor isolado não basta.
7. Use medianas, intervalos e distribuições quando métricas forem assimétricas; média isolada é insuficiente.
8. Faça split temporal ou por grupo quando houver dependência por creator; nunca deixe o mesmo creator vazar entre treino e teste quando isso inflar generalização.
9. Cada recomendação deve conter evidência, segmento, ação, prioridade, métrica de sucesso, risco e condição de parada.
10. Mantenha dados sensíveis e segredos fora do Git. Não faça commit de datasets grandes.
11. Registre decisões, correções da IA e validações humanas em `process-log/`.
12. Não altere uma conclusão aprovada para melhorar storytelling.

## Padrões de código

- Python legível, modular, determinístico e tipado nas interfaces públicas.
- Configuração e seeds explícitos; caminhos relativos à raiz da submissão.
- Funções pequenas, docstrings úteis e nomes de negócio; evite lógica crítica apenas em notebook.
- Valide schema, tipos, ranges, chaves, duplicidades e invariantes na entrada e saída.
- Separe extração/limpeza, análise, modelagem e apresentação.
- Teste transformações críticas, métricas, splits, filtros e agregações.
- Não silencie warnings estatísticos ou erros. Justifique qualquer exclusão.
- Artefatos gerados devem carregar timestamp, versão do dataset/config e script de origem.

## Padrões estatísticos e analíticos

- Pré-registre hipótese, população, unidade de análise, métrica primária e confundidores antes do teste confirmatório.
- Verifique distribuição, independência, suporte, missingness e sensibilidade a outliers.
- Para patrocínio, prefira regressão ajustada/ponderação ou matching com diagnóstico de balanço; não conclua pelo contraste bruto.
- Use erros-padrão robustos ou clusterizados por creator quando adequado.
- Controle FDR em famílias de testes; diferencie descoberta de validação.
- Faça análise de sensibilidade por plataforma, período, faixa de creator e definição de engagement.
- Não transforme associações de hashtags em receita causal.
- Para ML, compare contra baseline simples, use validação temporal/grupo, reporte calibração/erro por segmento e documente drift.

## Padrões de documentação e visualização

- Títulos de gráficos devem comunicar a conclusão; subtítulo informa população, período e métrica.
- Eixos, unidades, denominadores, `n` e fonte devem estar visíveis. Evite eixo truncado enganoso, 3D e decoração.
- Um gráfico deve responder uma pergunta. Remova gráficos redundantes.
- Relatório executivo: decisão primeiro, evidência depois, limitações sempre.
- Use linguagem probabilística proporcional à evidência.
- Toda tabela/figura final deve ter origem rastreável a código e dado processado.

## Limites dos agentes

- Cada agente atua somente no contrato descrito em `.claude/agents/<nome>.md`.
- Agentes não reescrevem outputs de outro agente; emitem solicitação de correção pelo protocolo.
- Statistician não recebe dados brutos; Strategist não recebe DataFrames; Dashboard Builder e Executive Writer não reinterpretam resultados.
- Software Engineer recebe apenas escopo técnico, estrutura, contratos, requisitos de execução/qualidade e limitações. Não recebe autoridade para interpretar dados, escolher testes, definir KPIs, alterar conclusões ou publicar no GitHub.
- Reviewer é read-only e não corrige a própria auditoria.
- GitHub Publisher só atua depois de `FINAL=PASS` e autorização humana explícita; não modifica o conteúdo aprovado.
- ML só roda se o Planner o justificar e o Orchestrator abrir o gate; o dashboard faz parte do fluxo solicitado e precisa de métricas congeladas.

## Checklist final obrigatório

- [ ] Todas as perguntas obrigatórias do desafio foram respondidas.
- [ ] Patrocinado vs. orgânico foi comparado de forma ajustada e sem alegação falsa de ROI.
- [ ] Segmentos têm tamanho amostral e estabilidade suficientes.
- [ ] Resultados possuem efeito, incerteza, `n` e limitações.
- [ ] Leakage, overfitting, missingness, duplicidade, seleção, sobrevivência, Simpson e multiplicidade foram verificados.
- [ ] Recomendações são priorizadas, mensuráveis e ligadas a evidências.
- [ ] Dashboard, se houver, reproduz números aprovados e não cria interpretações.
- [ ] Relatório executivo não altera conclusões técnicas.
- [ ] Código/testes reproduzem todos os artefatos finais.
- [ ] Fundação e consolidação técnicas passaram, incluindo execução end-to-end e testes de integração.
- [ ] Process log mostra iterações, falhas da IA e julgamento humano.
- [ ] Reviewer emitiu `PASS` sem bloqueadores.
- [ ] Publicação, se solicitada, ocorreu somente após aprovação humana e sem mudanças de conteúdo.

## Preservar durante compactação de contexto

Preserve objetivo e critérios de aceite, gate atual, decisões e justificativas, IDs de evidência, caminhos alterados, testes executados, erros pendentes e solicitações de correção abertas.
