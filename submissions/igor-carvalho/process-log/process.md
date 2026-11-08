# Processo do projeto — G4 Sales Priority (Lead Scorer)

Arquivo gerado pela IA com base na conversa e no arquivo [workflow.md] organizada pelo **tipo de solicitação**: o que eu pedi à IA como **Implementação** (algo novo), **Melhoria** (evoluir algo que já existia) e **Correção** (algo que estava errado ou fora do que eu queria). Cada fase mostra o que eu solicitei, em ordem, e o resultado quando há.

## 1. Contexto
- Desafio: priorizar deals para o vendedor (o que fazer hoje) e dar visão de gestão ao manager.
- Dataset (Kaggle, na pasta do projeto): ~8,8 mil oportunidades, 35 vendedores, 6 managers, 3 escritórios (Central, East, West).
- Estrutura: `solution/backend` (Python), `solution/frontend` (React), `solution/model-lab`, `docs/`, `process-log/`.

## 2. Resumo por tipo de solicitação

| Tipo | Fase | O que eu solicitei |
|---|---|---|
| Implementação | A | Avaliar o melhor modelo para os dados do Kaggle, com no mínimo 3 opções para comparar |
| Implementação | A | Plano da aplicação e contrato da API |
| Implementação | B | Definir as regras de negócio (foco, decidir, zumbi) com base nos dados |
| Implementação | C | Exemplo da página principal, só o front |
| Implementação | D | Backend (treinador + API) com SQLite, sem treinar durante requisições |
| Implementação | D | Coleção para testar a API |
| Implementação | E | Converter o artefato em JS para React componentizado, sem hooks |
| Implementação | F | Camada SQLAlchemy |
| Implementação | H | Heatmap do funil (depois ocultado) |
| Implementação | J | Fase 1 das sugestões do vendedor externo |
| Implementação | K | Laboratório isolado (`model-lab`) com simulação de 7 dias |
| Implementação | L | Documentação, ambiente na Oracle e cron de retreino diário |
| Melhoria | A | Modelo passou a prever ganho em até 30 dias (ranking em vez de probabilidade) |
| Melhoria | C | Avaliar a tela como vendedor experiente e criar versões visuais |
| Melhoria | D | Arquivo de configuração centralizada; análise de qualidade do código; remover o Bruno |
| Melhoria | E | Revisão de usabilidade como vendedor ("Seu dia", motivo estruturado do feedback) |
| Melhoria | F | Um repositório por arquivo, para o código ficar mais fácil de entender |
| Melhoria | G | Code review do backend como dev sênior (SOLID, bad smells), sem implementar |
| Melhoria | H | Entender valor esperado x preço para a visão do vendedor |
| Melhoria | K | Se o modelo puder melhorar, implementar no backend |
| Correção | F | Regras de negócio estavam no front; mover para o backend e entregar dados prontos pela API |
| Correção | H | Heatmap do funil removido da tela por ser complexo demais (código mantido) |
| Correção | I | "Seu dia" e "Foco da semana" mostravam os mesmos deals |
| Correção | K | Score alto em deals parados e acompanhando quase só o preço; modelo refeito |

## 3. Linha do tempo

### Fase A — Escolha do modelo (notebooks)
**Implementação**
- Pedi que a IA avaliasse qual seria o melhor modelo para os dados do Kaggle que coloquei no projeto.
- Pedi no mínimo 3 opções para eu validar e comparar, em vez de uma resposta única. Eu queria analisar os resultados e escolher.
- Solicitei a criação de um plano e de um contrato da API.
- Escolhi o LightGBM pelos resultados, em que as chances de ganho seriam maiores. Racional da IA para o modelo escolhido:
  - Histórico só com deals fechados até a data T; snapshots semanais até T−60 dias; rótulo só se fechou até T (evita vazamento).
  - Shrinkage K=30 e janela recente de 90 dias; LightGBM (lr 0,03; 15 folhas; min_child_samples 150; early stopping 50 na última fatia temporal).
  - Calibração "shrink-to-base" (alpha entre 0,1 e 1,0); só é "útil" se o Brier superar o de uma constante.
  - Backtest: AUC ≈ 0,55 (IC95% 0,517–0,563), lift@20 ≈ 1,09. Modesto, mas com ganho de receita no topo.

**Melhoria**
- O modelo evoluiu para prever a chance de ganho **em até 30 dias** (rótulo `won_30d`, snapshots até T−30, calibração por deslocamento de nível). A calibração atual não é "útil", então a chance em % fica oculta e o modelo vale pelo ranking. Ver `solution/backend/docs/MODELO.md`.

### Fase B — Análise do score e definição das regras de negócio
**Implementação**
- Perguntei algumas vezes à IA o que o score deveria representar: chance de ganhar, valor ou os dois, e como isso vira ação para o vendedor.
- Pedi para definir as regras de negócio: quando um deal está em foco, quando exige decisão e quando é "zumbi" (deal parado que ninguém fecha mais).
- Quis ver a base de cada regra nos dados, não números arbitrários.

### Fase C — Protótipo da tela
**Implementação**
- Pedi um exemplo de como a página principal ficaria, só o front, sem backend.

**Melhoria**
- Passei um bom tempo avaliando como a tela deveria ser e entendendo qual era o foco do score: o que o vendedor precisa ver primeiro, em que ordem, e por que cada deal aparece naquela posição.
- Pedi avaliação "como vendedor com muita experiência de mercado", melhorias e versões visuais para comparar.

### Fase D — Backend Python
**Implementação**
- Solicitei à IA construir o backend (treinador e API) com banco SQLite, sem treinar durante requisições.
- Escolhi o SQLite para ter um banco local, sem me preocupar muito com infraestrutura; em um caso real eu escolheria o PostgreSQL.
- Pedi uma coleção para testar a API.

**Melhoria**
- Organizar o código e criar um arquivo de configuração centralizada.
- Pedi uma análise de qualidade do código.
- Removi o Bruno por não ser mais necessário (a coleção de teste passou a ser a do Postman).

### Fase E — Frontend real (chat separado do front)
**Implementação**
- Pedi para reorganizar o front e converter o artefato em JS para um React componentizado, mas sem hooks.

**Melhoria**
- Após o refactor, pedi à IA para revisar a usabilidade como se fosse um vendedor ("Seu dia", motivo estruturado do feedback).

### Fase F — Regras de negócio só no backend
**Correção**
- Verifiquei que boa parte da regra de negócio estava no front. Pedi à IA para mover a regra para o backend e ter os dados prontos para a API.

**Melhoria**
- Pedi para refatorar o backend separando os repositórios por arquivo, porque assim o código fica mais fácil de entender.

**Implementação**
- Pedi para adicionar o SQLAlchemy, para facilitar a troca de banco de dados no futuro e dar maior abstração.

### Fase G — Revisão e documentação final
**Melhoria**
- Pedi à IA para agir como Dev Sênior e fazer um code review do backend, verificando princípios como SOLID e bad smells. Pedi somente para revisar, não implementar. A IA criou o arquivo `docs/PLANO_PENDENCIAS.md`.

### Fase H — Funil em heatmap
**Implementação**
- Pedi para a IA corrigir alguns problemas do front, como adicionar um heatmap do funil.

**Correção**
- Depois pedi para remover o heatmap, porque queria algo mais simples na tela. A implementação continua no código, mas não é apresentada.

**Melhoria**
- Perguntei coisas como a diferença entre valor esperado e preço, para me sentir mais confortável com a visualização do vendedor.

### Fase I — Semana x dia
**Correção**
- "Seu dia" e "Foco da semana" mostravam os mesmos deals. Pedi para a IA arrumar, determinando que a semana contenha os leads com prioridade alta e média; a semana passou a ter mais leads que o dia.

### Fase J — Sugestões de um vendedor externo
**Melhoria**
- Tirei um print do frontend e subi no ChatGPT para ter uma visão mais fresca. Pedi um feedback da página e uma lista de melhorias em fases.

**Implementação**
- Com as sugestões do ChatGPT, pedi ao Claude para implementar as tarefas da fase 1, para focar no que atende a dor do vendedor. A fase 1 continha:
  - Detalhe com indicadores separados: índice (posição, não probabilidade), preço, valor esperado (com horizonte) e probabilidade só se a API enviar.
  - Tabela de fatores (observado, referência, peso a favor/contra) a partir de `GET /deals/{id}`.
  - "Confiança da previsão" separada de "Completude dos dados" (`data_quality`; a conta não entra no modelo).
  - A chance em % só aparece se `calibration.useful` for verdadeiro; `G4_SHOW_PROBABILITY=false` esconde sempre.
- As fases 2 a 4 não foram implementadas.

### Fase K — Novo modelo e laboratório de validação
**Implementação**
- Criei um novo perfil de Data Scientist para validar se o modelo atual estava condizente com a realidade. Pedi um laboratório isolado, sem alterar nada no código, com uma simulação de 7 dias que cria novos leads e retreina. Para essa tarefa usei o modelo Opus.

**Melhoria**
- Coloquei a condição de que, se o modelo pudesse ser melhorado, a IA implementasse no backend.

**Correção** (o que o laboratório encontrou e o que a IA fez)
- `model-lab`: backtest real em 13 datas de 2017, simulação de 7 dias com mocks no formato dos CSVs e veredito com critérios de aceite em números (correlação com a receita real em 30 dias, score alto que não seja deal parado, estabilidade PSI, regras de negócio). Sai com código 1 se o score não passar.
- Diagnóstico (`PLANO_NOVO_MODELO.md`): o score seguia quase só o preço (Spearman 0,98); deal velho parecia melhor por viés de sobrevivência; 30 dos 62 deals com score ≥ 80 estavam parados; o limiar de zumbi (máximo histórico) era frágil; o portão de qualidade usava sempre as mesmas datas.
- Desafiante "receita esperada em 30 dias": receita capturada no top 20% de 56,4% para 64,4% e acerto do top-5 do vendedor de 16,3% para 22,4% no backtest; Spearman com a receita real de 0,82 para 0,98 na simulação.
- Levado para o backend (`docs/MODELO.md`): novo alvo `won_30d`, limiares por quantil (P90 e P99), "Decidir agora" limitado a 79, calibração só por deslocamento de nível, portão com datas móveis e receita capturada contra a ordenação só por preço.
- Limite assumido: sem dados de atividades (contatos, reuniões) o ganho é moderado.

### Fase L — Fases subsequentes
**Implementação**
- Pedi ajuda da IA para criar documentação, montar o ambiente na Oracle e criar um cron para retreinar todos os dias quando tiver novos leads.

## 4. Pendências
Ver `docs/PLANO_PENDENCIAS.md`. Principais: autenticação com senha (schema v2), endpoints de Adiar/Encerrar/Marcar feito, fonte dos leads novos. Do plano de melhorias: fases 2 a 4 (feedback estruturado, "Ignorar" como ação comercial, filtros, histórico de prioridade, tela de gestor); snapshots das previsões.

## 5. Como rodar
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
