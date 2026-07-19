# Process Log - Challenge 002

## Sessao 1 - Setup e entendimento do problema

**Objetivo:** transformar o briefing do Challenge 002 em uma entrega completa: diagnostico operacional, proposta de automacao com IA e prototipo funcional.

**Uso de IA:** usei Codex para ler a estrutura do repositorio, interpretar o README do challenge, identificar os criterios de qualidade e montar a estrutura inicial da submissao.

**Decisoes tomadas:**

- Trabalhar dentro de `submissions/fernandofreitas/`, seguindo a regra do repositorio.
- Separar a entrega em tres blocos: analise, prototipo e documentacao.
- Manter este log atualizado ao longo do processo para evidenciar iteracao, julgamento e uso de IA.

**Riscos identificados:**

- Os datasets estao no Kaggle e podem exigir autenticacao.
- A entrega precisa usar dados reais; se o download automatico falhar, sera necessario baixar manualmente pelo navegador/Kaggle.

## Sessao 2 - Download e auditoria dos dados

**Objetivo:** obter os dois datasets reais e verificar se o conteudo batia com o briefing.

**Uso de IA:** usei Codex para instalar dependencias Python, tentar download via `kagglehub`, listar arquivos, ler colunas e gerar uma primeira auditoria de qualidade.

**O que aconteceu:**

- O download automatico funcionou sem token Kaggle.
- Dataset 1: `customer_support_tickets.csv`, 8.469 linhas e 17 colunas.
- Dataset 2: `all_tickets_processed_improved_v3.csv`, 47.837 linhas e 2 colunas.

**Julgamento humano aplicado:**

O briefing dizia cerca de 30.000 tickets no Dataset 1, mas o arquivo publico tinha 8.469. Decidi documentar isso como limitacao em vez de forcar a narrativa.

## Sessao 3 - Diagnostico operacional

**Objetivo:** identificar gargalos por canal, tipo, prioridade e combinacoes.

**Uso de IA:** usei Codex para escrever consultas exploratorias em pandas e interpretar os resultados.

**Erro/ajuste importante:**

A primeira conta de duracao gerou medias negativas porque 1.365 tickets fechados tinham `Time to Resolution` anterior a `First Response Time`. Isso indicou problema de instrumentacao. Corrigi a metrica tratando delta negativo como virada de dia (+24h) e marquei isso como limitacao metodologica.

**Principais achados:**

- 5.700 de 8.469 tickets estavam abertos ou pendentes.
- Mediana corrigida de resolucao: 11,6h.
- P90 corrigido: 21,7h.
- `Phone + High + Refund request` teve CSAT medio de 2,29.
- O excesso acima da mediana somou 8.733,5 horas nos tickets fechados.

## Sessao 4 - Prototipo de automacao

**Objetivo:** demonstrar que a proposta de IA funciona em algo executavel.

**Uso de IA:** usei Codex para treinar um classificador com TF-IDF + regressao logistica no Dataset 2 e transformar a classificacao em regras de roteamento no Dataset 1.

**Resultado do modelo:**

- Accuracy: 86,5%.
- Macro F1: 86,6%.

**Decisao de produto:**

Evitei automacao total. A regra final sempre escala `Critical` para humano, usa auto-roteamento apenas em alta confianca e mantem baixa confianca em triagem humana.

## Sessao 5 - Documentacao e entrega

**Objetivo:** deixar a entrega compreensivel para avaliadores tecnicos e nao tecnicos.

**Uso de IA:** usei Codex para estruturar README, diagnostico operacional, blueprint de automacao e instrucoes de setup.

**Arquivos produzidos:**

- `solution/flask_app.py`
- `solution/README.md`
- `solution/docs/operational-diagnosis.md`
- `solution/docs/automation-blueprint.md`
- `README.md`

## Sessao 6 - Reenquadramento colaborativo

**Objetivo:** ajustar o projeto para ser construido em conversa, validando decisoes antes de implementar a versao final.

**Uso de IA:** usei Codex para auditar novamente o Dataset 1 a partir dos CSVs locais em `C:\Users\Jufer\Downloads\datasets g4`, gerar um parecer de confiabilidade e transformar os achados em documento.

**Decisoes tomadas:**

- O produto final sera pensado como tres experiencias: assistente do cliente, abertura inteligente de ticket e painel admin.
- O assistente usara conhecimento recorrente por tras da interface, sem obrigar o cliente a navegar por FAQ.
- O painel admin respondera diretamente as perguntas do desafio.
- A auditoria dos dados vira parte da entrega, porque mostra julgamento critico.

**Achado importante:**

O Dataset 1 e estruturalmente consistente, mas tem problemas relevantes de qualidade textual e timestamps. Isso reforca que a automacao deve ser assistida, com limites claros, e nao uma promessa de resolucao autonoma para todos os tickets.

## Sessao 7 - Auditoria do Dataset 2

**Objetivo:** validar se o dataset de classificacao e adequado para sustentar a parte de IA da solucao.

**Uso de IA:** usei Codex para inspecionar estrutura, nulos, duplicados, distribuicao de categorias, tamanho dos textos e implicacoes para modelagem.

**Achados principais:**

- O Dataset 2 tem 47.837 registros, 2 colunas, sem nulos e sem duplicados.
- As categorias estao desbalanceadas: Hardware e HR Support somam mais de 50% da base.
- Os textos parecem pre-processados e ruidosos, mas sao adequados para classificacao local.

**Decisao metodologica:**

Usar o Dataset 2 para treinar um classificador e medir macro F1, nao apenas accuracy. Deixar claro que ele nao tem chave de juncao com o Dataset 1 e serve como base complementar para demonstrar automacao de triagem.

## Sessao 8 - Evolucao do conceito do produto

**Objetivo:** melhorar a proposta para ir alem de "abrir ticket + dashboard".

**Decisao tomada em conversa:**

Transformar o portal do cliente em um assistente de deflexao de tickets. Antes de abrir um chamado, o usuario descreve sua duvida em um input livre. A IA tenta responder rapidamente com FAQ/casos similares. Se nao houver informacao suficiente, ela pede abertura de ticket e coleta o contexto necessario.

**Nova proposta:**

- Cliente descreve a duvida.
- IA tenta resolver com base em conhecimento existente.
- Se resolver, o ticket e evitado.
- Se nao resolver, o ticket e aberto ja classificado e contextualizado.
- Humano resolve casos escalados.
- A resolucao humana alimenta a base de conhecimento para casos futuros.
- Admin acompanha gargalos, backlog, ROI, deflexao e aprendizado.

**Cuidado metodologico:**

Nao chamar isso de treinamento automatico irrestrito. No prototipo, a expressao correta e "base de conhecimento retroalimentada por resolucoes humanas". Em producao, isso exigiria revisao humana, avaliacao de qualidade e retreinamento controlado.

## Sessao 9 - Implementacao do MVP autenticado

**Objetivo:** transformar o conceito em um produto demonstravel e pronto para deploy rapido.

**Stack escolhida:**

- Flask com HTML/CSS customizado para interface e dashboard.
- pandas/scikit-learn para analise e classificacao.
- SQLite local para armazenar resolucoes humanas aprendidas no demo.
- OpenAI API opcional para resposta generativa do assistente.

**Funcionalidades implementadas:**

- login simples para Cliente e Admin;
- base interna com problemas recorrentes para busca/RAG;
- input livre para duvida do cliente;
- assistente com guardrails e fallback local;
- abertura de ticket quando a IA nao resolve;
- classificacao, prioridade e rota sugeridas;
- painel admin com diagnostico, fila, aprendizado e ROI;
- resolucao humana alimentando base de conhecimento;
- limites de caracteres, chamadas por sessao e saida curta para controlar custo e reduzir abuso.

**Validacao:**

O app respondeu HTTP 200 em `http://localhost:5000`.

## Sessao 10 - Revisao final de aderencia

**Objetivo:** comparar a entrega com o README oficial do challenge e remover inconsistencias.

**Ajustes feitos:**

- Removi a versao Streamlit antiga da entrega para evitar confusao.
- Mantive apenas o app Flask como prototipo principal.
- Atualizei README, setup, blueprint e checklist de aderencia.
- Reforcei o painel admin com p90, horas desperdicadas, combinacoes criticas, CSAT por tipo, matriz do que automatizar/nao automatizar e ROI estimado.
- Adicionei `.gitignore` local para evitar commit de SQLite, cache e tokens.

**Validacao:**

- `flask_app.py` compila.
- Rotas `/`, `/client` e `/admin` retornam status 200 no teste com Flask client.

## Sessao 11 - Evidencias visuais e preparo para Git

**Objetivo:** gerar evidencias visuais do projeto e preparar a submissao para commit.

**Screenshots gerados:**

- `process-log/screenshots/01-login.png`
- `process-log/screenshots/02-cliente-inicial.png`
- `process-log/screenshots/03-cliente-resposta-ia.png`
- `process-log/screenshots/04-cliente-abrir-ticket.png`
- `process-log/screenshots/05-ticket-aberto.png`
- `process-log/screenshots/06-admin-dashboard.png`

**Observacao:**

Os prints mostram o fluxo cliente/admin sem depender de deploy publico.
