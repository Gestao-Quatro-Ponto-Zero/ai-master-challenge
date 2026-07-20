# Registro de prompts

## Prompt Mestre do JourneyGraph

- **Identificação:** Prompt Mestre do JourneyGraph, lido e confirmado antes desta fase.
- **Finalidade:** estabelecer a tese do produto, os princípios de governança e causalidade, a sequência de fases, os gates de qualidade e os limites de implementação do JourneyGraph.
- **Estado:** utilizado como contexto; este registro não afirma que fases ou prompts futuros tenham sido executados.

## Prompt da Fase 0

- **Identificação:** “FASE 0 — FUNDAÇÃO, CONTEXTO E SEGURANÇA DO REPOSITÓRIO”.
- **Finalidade:** autorizar exclusivamente a fundação documental e estrutural da submissão, sua validação e um commit local.
- **Estado:** execução registrada neste commit.

### Reprodução fiel das instruções recebidas

1. Trabalhar exclusivamente em `submissions/carlos-henrique/`, sem implementar análise, modelos, journey mining, grafos, dashboard ou business case.
2. Criar a fundação do **JourneyGraph — Challenge 001: Diagnóstico de Churn**, incluindo estrutura, documentação de escopo e arquitetura, decisões, process log, política de dados e artefatos, reprodutibilidade e validação do escopo.
3. Usar o repositório `C:\Users\ataqu\Documents\GitHub\ai-master-challenge`, fork `acarloshenrique/ai-master-challenge`, branch `submission/carlos-henrique`, `origin` do fork, `upstream` oficial e HEAD esperado `4aed364d572fabe0f1fff1f0c6f32960b30fe575`.
4. Não configurar tracking, fazer push, criar branch remota ou abrir Pull Request nesta fase.
5. Formalizar D001 a D010: Challenge 001; tese do JourneyGraph; exclusão do conteúdo anterior do SupportOps Intelligence Graph; escopo único da pasta; event log antes do grafo; NetworkX antes de Neo4j; não causalidade; ausência e não substituição dos dados; Git remoto condicionado a autorização; e staging seletivo devido ao ignore de `submissions/`.
6. Antes de criar arquivos, executar `pwd`, status, branch, remotes, HEAD, diff de trabalho e diff staged. Bloquear em caso de divergência.
7. Criar exatamente 16 arquivos: README principal; README e requirements da solução; `src/__init__.py`; READMEs de scripts, tests, raw, processed, artifacts e reports; architecture, data-contract e repository-policy; workflow, prompts e decisions.
8. Não criar app, notebooks, modelos, dashboards, CSV, Parquet, GraphML, imagens, screenshots, scripts de análise ou download, bancos, cloud config, Dockerfile, CI, APIs ou código de grafo.
9. No README principal, registrar projeto, candidato, challenge, status de fundação, tese, problema, perguntas, arquitetura conceitual, escopo e exclusões, fontes esperadas, ausência dos datasets, governança, não causalidade, roadmap e ausência de resultados.
10. No README da solução, registrar propósito, arquitetura planejada, Python 3.11+, execução indisponível, dependência dos cinco datasets, ordem auditoria → event log → diagnóstico → survival → journey mining → grafo → watchlist → aplicação, ausência de APIs pagas no núcleo, reprodutibilidade e ausência de código analítico.
11. Em `requirements.txt`, listar somente pandas, numpy, scipy, statsmodels, scikit-learn, lifelines, networkx, plotly, streamlit, pyarrow, pydantic e pytest; não instalar pacotes ou gerar lockfile; adiar o pin de versões até a validação do ambiente.
12. Em `data/raw/README.md`, listar os cinco CSVs oficiais, proibir versionamento, exigir a fonte oficial e os cinco arquivos, adiar validação de nomes e schemas para a Fase 1 e proibir substituição silenciosa por dados sintéticos.
13. Em `data/processed/README.md`, reservar saídas derivadas e reproduzíveis, exigir scripts geradores e reconciliação e proibir sobrescrita de dados brutos.
14. Nos READMEs de artifacts e reports, documentar apenas categorias futuras e não criar qualquer artefato nesta fase.
15. Em `architecture.md`, descrever arquitetura planejada em camadas, fluxo das cinco fontes, event-log-first, modelo conceitual do grafo, separação descritiva/temporal/prescritiva, human-in-the-loop, experimentação, stack, opcionais, exclusões, riscos e decisões pendentes da auditoria.
16. Em `data-contract.md`, não inventar schemas; marcar chaves, colunas, granularidades, temporalidade e relacionamentos como `A CONFIRMAR NA FASE 1`; planejar testes de unicidade, integridade, missingness, duplicidade, cardinalidade, datas, ordem temporal, inflação de joins, leakage, churn recorrente e reativação.
17. Em `repository-policy.md`, registrar escopo, raiz imutável, remotes, branch, proibições de push/force push, commits, segredos, datasets, arquivos grandes, conflito do ignore e staging seguro arquivo por arquivo.
18. No process log, registrar data/hora, contexto, verificações, arquivos, validações, resultado e próximo gate; identificar o Prompt Mestre e reproduzir fielmente a Fase 0; documentar D001–D010 com contexto, decisão, justificativa, consequências e status; não inventar erros da IA.
19. Criar somente uma docstring e versão opcional em `solution/src/__init__.py`, sem qualquer lógica.
20. Validar status incluindo ignorados, listar arquivos, confirmar origem da regra de ignore, garantir diffs limitados ao caminho autorizado, legibilidade, requirements permitidos, ausência de CSV, segredos, resultados, conteúdo prévio indevido, datasets e arquivos excessivos; executar `python -m compileall submissions/carlos-henrique/solution/src`.
21. Fazer staging com `git add -f` seletivo e individual, revisar nomes e diff completo, e criar um único commit local com a mensagem `chore: establish JourneyGraph submission foundation`.
22. Após o commit, validar status, último log e estatísticas; não fazer push, não configurar upstream e não abrir PR. Retornar o relatório obrigatório da Fase 0 e solicitar o prompt da Fase 1 sem iniciar auditoria ou download.

### Critérios de bloqueio preservados

A execução deve parar se branch, árvore inicial, staging, remotes ou HEAD divergirem; se qualquer arquivo externo precisar ser alterado ou entrar no staging; se houver conteúdo prévio do Challenge 002 no clone; se arquivo oficial precisar ser modificado; se a estrutura oficial tiver mudado materialmente; ou se existir dúvida sobre exclusão ou sobrescrita.

Nenhum prompt de fase futura foi executado.
