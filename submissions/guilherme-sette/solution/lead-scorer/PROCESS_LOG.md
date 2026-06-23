# Process Log - Lead Scorer

Este arquivo documenta como a solucao foi construida com apoio de IA, conforme exigido pelo guia de submissao do desafio.

## Ferramentas usadas

- Codex para engenharia de software, analise dos CSVs, ETL, heuristicas de score, frontend estatico, validacoes e documentacao.
- Navegador/web apenas quando necessario para obter contexto externo ou arquivos publicos.
- Execucao local de scripts Python para gerar e validar os artefatos.

## Como o problema foi decomposto

1. Entender o README do desafio e fixar o escopo: ferramenta funcional de lead scoring para Sales/RevOps.
2. Baixar os CSVs e documentacao do dataset de CRM.
3. Criar uma camada ETL padronizada antes de qualquer modelagem.
4. Fazer raio X dos vendedores: desempenho, carteira, historico, dispersao e red-flags.
5. Avaliar fit vendedor vs produto, conta, setor, porte e ticket.
6. Definir uma politica de score operacional, nao uma probabilidade de fechamento.
7. Criar front com duas divisoes: vendedor e gerente.
8. Adicionar governanca de gerente para remanejamento e revisao.
9. Auditar criticamente o projeto contra o README, setup, explicabilidade e process log.
10. Corrigir reprodutibilidade do ETL e adicionar benchmark simples contra baselines.
11. Validar visualmente o front atual por screenshots headless e corrigir overflow encontrado.

## Decisoes humanas relevantes

- Manter o desafio estritamente no escopo do README local.
- Usar Untitled UI apenas como referencia visual, nao como dependencia obrigatoria.
- Evitar vender ML ou forecast calibrado quando o dataset nao suporta snapshots historicos reais.
- Tratar remanejamento como recomendacao sujeita a aprovacao do gerente, nao alteracao automatica de ownership.
- Usar vendedores de baixa performance como red-flag e last-chance, sem jogar carga nova indiscriminadamente.
- Priorizar explicabilidade e utilidade operacional acima de sofistificacao estatistica.

## Onde a IA errou ou precisou ser corrigida

- O download binario direto do Kaggle ficou bloqueado sem sessao autenticada; a alternativa foi baixar arquivos equivalentes de um espelho publico e documentar a origem.
- A primeira versao de nomes de status do front nao comunicava bem o uso real; os labels foram ajustados.
- A aba de gerente apareceu no portal de vendedor por conflito de CSS com o atributo `hidden`; foi corrigido com regra explicita.
- A fila de aprovacao precisou ser reposicionada como aba propria do gerente.
- A validacao visual por navegador causou instabilidade no ambiente; a auditoria passou a evitar esse caminho e usar validacao estatica/arquivos.
- A transcricao local existe, mas a auditoria mostrou que ela nao e prova perfeita de completude literal e cronologica sem exportacao oficial do chat.
- O benchmark mostrou que valor puro ainda e forte para captura de receita historica; por isso a narrativa foi ajustada para apresentar o score como priorizacao operacional, nao maximizador estatistico puro.
- A primeira recaptura visual revelou overflow no cenario do gerente; o CSS foi ajustado para dar prioridade a tabela em desktop 1440px e permitir quebra de textos longos no resumo de equipe.
- As pesquisas anexadas foram copiadas para `reports/research_sources/` para preservar a prova documental junto da submissao.

## Iteracoes principais

- Clone do monorepo e definicao do arquivo de transcricao.
- Download e organizacao dos CSVs.
- ETL com `data/raw`, `data/processed`, dimensoes, fato e checks de qualidade.
- Analises de dados e vendedores.
- Fit vendedor-segmento e recomendacoes de especialista.
- Politica de score e roteamento.
- Front estatico com portal de vendedor e gerente.
- Fila de aprovacoes para remanejamento e revisao gerente.
- Auditoria critica do projeto.
- Ajustes de reprodutibilidade, README, validacao e process log.
- Benchmark historico simples e curadoria de reports obsoletos.
- Screenshots atuais do portal do vendedor, gerente/cenario e gerente/aprovacoes.

## Evidencias de verificacao

- Scripts de ETL, raio X, fit e score foram executados localmente.
- Outputs principais foram gerados em `data/processed`.
- Payload do frontend foi gerado em `frontend/data/dashboard_data.json`.
- A auditoria critica esta em `reports/project_critical_review.md`.
- O benchmark historico esta em `reports/score_benchmark.md`.
- A validacao visual esta em `reports/frontend_visual_validation.md`.
- Os arquivos-fonte da pesquisa estao em `reports/research_sources/`.
- A validacao do transcript esta em `reports/transcript_integrity_report.md`.
- A copia do transcript completo disponivel no momento da preparacao deve ser mantida em `reports/full_chat_transcript.md`.

## Limitacoes do processo

- O transcript local foi mantido manualmente e nao substitui uma exportacao oficial do cliente.
- A aplicacao e estatica e nao tem autenticacao, permissoes ou persistencia real de aprovacao.
- O score e uma heuristica operacional, nao uma probabilidade calibrada.
- O fit vendedor-segmento e associativo, nao causal.
- A alta taxa de oportunidades abertas sem conta conhecida reduz a confianca de parte relevante do scoring.
