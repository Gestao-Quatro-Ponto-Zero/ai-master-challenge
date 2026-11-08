# Workflow do projeto — G4 Sales Priority (Lead Scorer)

Como o projeto foi conduzido com a IA: em cada faze está a idéia geral do que foi pedido por mim e em alguns casos o resultado gerado pela IA.

## 1. Contexto
- Desafio: priorizar deals para o vendedor (o que fazer hoje) e dar visão de gestão ao manager.
- Dataset (Kaggle, na pasta do projeto): ~8,8 mil oportunidades, 35 vendedores, 6 managers, 3 escritórios (Central, East, West).
- Estrutura: `solution/backend` (Python), `solution/frontend` (React), `docs/`, `process-log/`.

## 2. Linha do tempo

### Fase A — Escolha do modelo (notebooks)
- Pedi que a IA avaliasse qual seria o melhor modelo para os dados do Kaggle que coloquei no projeto.
- Pedi no mínimo 3 opções para eu validar e comparar, em vez de uma resposta única. Eu queria analisar os resultados e escolher.
- Solicitei a IA a criar um plano e um contrato da API.
- Escolhi o LightGBM pelos resultados onde as chances de ganho seriam maiores, coloco abaixo alguns dados, segue o racional da IA para o modelo escolhido
- Modelo de probabilidade de ganho com **LightGBM**, features *point-in-time* e calibração.
  - Histórico só com deals fechados até a data T; fotos semanais até T−60 dias; rótulo só se fechou até T (evita vazamento).
  - Shrinkage K=30 e janela recente de 90 dias; LightGBM (lr 0,03; 15 folhas; min_child_samples 150; early stopping 50 na última fatia temporal).
  - Calibração "shrink-to-base" (alpha entre 0,1 e 1,0); só é "útil" se o Brier superar o de uma constante.
- Backtest: AUC ≈ 0,55 (IC95% 0,517–0,563), lift@20 ≈ 1,09. Modesto, mas com ganho de receita no topo.
- **Atualização:** o modelo evoluiu para prever a chance de ganho **em até 30 dias** (rótulo `won_30d`, fotos até T−30, calibração por deslocamento de nível). A calibração atual não é "útil", então a chance em % fica oculta e o modelo vale pelo ranking. Ver `solution/backend/docs/MODELO.md`.

### Fase B — Análise do score e definição das regras de negócio
- Perguntei algumas vezes para a IA o que o score deveria representar: chance de ganhar, valor ou os dois, e como isso vira ação para o vendedor.
- Pedi para definir as regras de negócio: quando um deal está em foco, quando exige decisão e quando é "zumbi" (deal parado que ninguém fecha mais).
- Quis ver a base de cada regra nos dados, não números arbitrários.

### Fase C — Protótipo da tela
- Pedi um exemplo de como a página principal ficaria, só o front, sem backend.
- Depois passei um bom tempo avaliando como a tela deveria ser e entendendo qual era o foco do score: o que o vendedor precisa ver primeiro, em que ordem, e por que cada deal aparece naquela posição.
- Pedi avaliação "como vendedor com muita experiência de mercado", melhorias e versões visuais para comparar.

### Fase D — Backend Python
- Solicitei a IA construir o backend, um treinador e API, com banco SQLite, sem treinar durante requisições, também solicitei organizar o código e criar um arquivo de configuração centralizada
- Escolhi o SQLite para ter um banco local, sem ficar me preocupando muito com infra estrutura, mas em caso real eu escolheria o PostgreSQL
- Ter uma coleção para testar a API; depois removi o Bruno por não ser mais necessário. Pedi também uma análise de qualidade do código.

### Fase E — Frontend real (chat separado do front)
- Pedi para reorganizar o front e converter de artefato com o JS para um React componentizado, mas sem hooks
- Após o refactor eu solicitei a IA revisar a usabilidade como se fosse um vendedor "Seu dia" e motivo estruturado do feedback.

### Fase F — Regras de negócio só no backend
- Verifiquei que a regra de negócio estava em boa parte no front, pedi para a IA mover a regra de negócio para o backend e ter os dados prontos para a API.
- E também pedi para refatorar o backend, separando os repositórios por arquivo, pois ai o código fica mais fácil de entender
- Bem como pedi para adicionar o SQLAlchemy para facilitar a troca de banco de dados no futuro e adicionar maior abstração

### Fase G — Revisão e documentação final
- Pedi agora para a IA agir como um Dev Sênior e fazer um code review do backend, verificando se o código estava seguindo princípios como SOLID e se tinha algum bad smell, pedi somente para revisar e não implementar, então a IA criou um arquivo `docs/PLANO_PENDENCIAS.md`

### Fase H — Funil em heatmap
- Pedi para a IA corrigir alguns problemas no front, como adicionar um heatmap do funil, mas pedi para remover o heatmap pois queria algo mais simples na tela, a implementação está no código mas não apresentado
- Também perguntei algumas coisas como a diferença entre valor esperado e preço, para me sentir mais confortável com a visualização de vendedor

### Fase I — Semana x dia
- Agora eu pedi para a IA arrumar o fato que a aba "Seu dia" e "Foco da semana" estavam iguais, determinei que a semana deveria conter os leads com prioridade alta e média o que passou a ter mais leads na lista
- "Seu dia" e "Foco da semana" mostravam os mesmos deals. A semana deve ter mais leads que o dia.

### Fase J — Sugestões de um vendedor externo
- Agora eu tirei um print do frontend e subi no ChatGPT para ter uma visão mais fresca e solicitei um feedback da página e pedi também para criar uma lista de coisas a melhorar em fases
- Após a análise do ChatGPT eu peguei as sugestões e pedi para o Claude implementar as tarefas de fase 1, para focar mais no que atenda a dor do vendedor.
- A fase 1 continha:
  - Detalhe com indicadores separados: índice (posição, não probabilidade), preço, valor esperado (com horizonte) e probabilidade só se a API enviar.
  - Tabela de fatores (observado, referência, peso a favor/contra) a partir de `GET /deals/{id}`.
  - "Confiança da previsão" separada de "Completude dos dados" (`data_quality`; a conta não entra no modelo).
  - A chance em % só aparece se `calibration.useful` for verdadeiro; `G4_SHOW_PROBABILITY=false` esconde sempre (padrão do código passou a `true`).
- Fases 2 a 4 não foram implementados

### Fase K — Novo modelo e laboratório de validação
- Agora eu criei um novo perfil como Data Scientist para validar se o modelo atual estava condizente com a realidade e solicitei que criasse um laboratório isolado sem alterar nada no código para criar uma simulação de 7 dias, onde ia criar novos leads e retreinar. Para essa tarefa usei o modelo Opus.
- Coloquei uma condição de que se o modelo pudesse ser melhorado, implemente no backend
- Aqui está o resultado da IA
  - `model-lab`: backtest real em 13 datas de 2017, simulação de 7 dias com mocks no formato dos CSVs e veredito com critérios de aceite em números (correlação com a receita real em 30 dias, score alto que não seja deal parado, estabilidade PSI, regras de negócio). Sai com código 1 se o score não passar.
  - Diagnóstico (`PLANO_NOVO_MODELO.md`): o score seguia quase só o preço (Spearman 0,98); deal velho parecia melhor por viés de sobrevivência; 30 dos 62 deals com score ≥ 80 estavam parados; o limiar de zumbi (máximo histórico) era frágil; o portão de qualidade usava sempre as mesmas datas.
  - Desafiante "receita esperada em 30 dias" (alvo: ganhou em até 30 dias, com todos os deals abertos): receita capturada no top 20% de 56,4% para 64,4% e acerto do top-5 do vendedor de 16,3% para 22,4% no backtest; Spearman com a receita real de 0,82 para 0,98 na simulação.
  - Levado para o backend (`docs/MODELO.md` do backend): novo alvo `won_30d`, limiares por quantil (P90 e P99), "Decidir agora" limitado a 79, calibração só por deslocamento de nível, portão com datas móveis e receita capturada contra a ordenação só por preço.
  - Limite assumido: sem dados de atividades (contatos, reuniões) o ganho é moderado.

### Fases subsequentes
- Pedi ajuda da IA para criar documentação e a criar o ambiente na Oracle, bem como criar uma cron para retreinar todos os dias quando tiver novos leads

## 3. Pendências
Ver `docs/PLANO_PENDENCIAS.md`. Principais: autenticação com senha (schema v2), endpoints de Adiar/Encerrar/Marcar feito, fonte dos leads novos, process-log. Do plano de melhorias: Fases 2 a 4 (feedback estruturado, "Ignorar" como ação comercial, filtros, histórico de prioridade, tela de gestor); snapshots das previsões.

## 4. Como rodar
```
# backend
cd solution/backend && cp .env.example .env
python3 -m venv .venv && source .venv/bin/activate
make install && make train && make api      # docs em http://localhost:8000/docs
make test

# frontend
cd solution/frontend && npm install && cp .env.example .env   # G4_API_URL
npm run dev                                 # API real; npm run dev:mock = sem backend
npm test && npm run typecheck
```
