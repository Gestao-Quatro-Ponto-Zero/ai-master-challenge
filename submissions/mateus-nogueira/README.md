# Submissao — Mateus Nogueira — Challenge Lead Scorer

## Sobre mim

- **Nome:** Mateus Nogueira
- **LinkedIn:** https://www.linkedin.com/in/mateus-nogueira-10b519281/
- **Challenge escolhido:** Lead Scorer

---

## Executive Summary

Construi um sistema de scoring inteligente que transforma os dados brutos do pipeline comercial em prioridades acionaveis para o time de vendas. Analisando 8.800 oportunidades historicas, identifiquei que o tempo no pipeline e a combinacao produto x setor sao os sinais mais fortes para prever conversao — deals Won fecham em media em 52 dias vs 42 dias dos Lost, e a win rate por produto-setor varia de 52% a 73%. O modelo combina 5 componentes (fit do produto, timing, qualidade da conta, performance do vendedor e valor do deal) em um score de 0-100 com labels visuais e alertas automaticos. A principal recomendacao e priorizar os 2.089 deals ativos usando a visao Monday Morning (Kanban), onde os deals estao separados em "Fechar Agora", "Nutrir" e "Repensar" — e investir em integracao com CRM real para manter os scores atualizados em tempo real.

---

## Solucao

### Abordagem

O ponto de partida foi entender o problema do vendedor: ele tem centenas de deals no pipeline e nao sabe em qual investir tempo. Numero bruto de score nao resolve — precisa de resposta imediata e visual.

**Decomposicao do problema em 3 camadas:**

1. **Dados → Score**: Analisei os 8.800 deals historicos para identificar quais variaveis realmente separam Won de Lost. Testei correlacoes e cheguei a 5 componentes independentes, cada um com peso calibrado pela sua capacidade discriminativa. O tempo no pipeline recebeu o maior peso (25 pts) porque mostrou a maior separacao entre deals ganhos e perdidos.

2. **Score → Acao**: Um numero sozinho nao gera acao. Criei um sistema de alertas inteligentes que cruza score + tempo + stage + produto para gerar recomendacoes concretas ("Ligar agora", "Follow-up urgente", "Considerar descarte"). A ordem de prioridade foi calibrada para que oportunidades quentes nunca sejam ocultadas por alertas de tempo.

3. **Acao → Interface**: Priorizei a experiencia do vendedor. O score numerico virou elemento secundario — o primario e o label visual (🔥 Quente, 🧊 Congelado) com cor e icone. Cada deal mostra uma pill de acao sugerida. O Kanban Monday Morning ja entrega a priorizacao pronta em 3 colunas.

**Priorizacao**: Comecei pelo scoring engine (sem score bom, nada funciona), depois alertas (transformar score em acao), depois frontend (tornar acionavel), e por ultimo a visao de equipe (heatmap gerente x regiao para gestores).

### Resultados / Findings

**Dados do pipeline:**
- 8.800 oportunidades totais (2.089 ativas, 4.222 Won, 2.489 Lost)
- 35 vendedores, 6 gerentes, 3 regioes
- 7 produtos em 3 series
- 85 contas (porem 68% dos deals ativos nao tem conta vinculada)

**Sinais discriminativos encontrados:**
- **Tempo no pipeline**: deals Won fecham em media em ~52 dias, Lost em ~42 dias. Deals acima de 2x a media (~104 dias) tem probabilidade muito baixa de conversao.
- **Produto x Setor**: win rate varia de 52% a 73% dependendo da combinacao — forte sinal de fit de mercado.
- **Performance do vendedor**: win rate individual varia de 55% a 70% — vendedores com melhor historico convertem mais.
- **Qualidade da conta**: contas com historico de deals tem win rate de 53% a 75%.

**Calibracao do modelo (6.711 deals fechados):**
- 63.9% dos deals Won recebem score >= 55 (Morno ou melhor)
- 5.8% dos deals Won recebem score >= 75 (Quente)
- 1.9% dos deals Lost recebem score < 35 (Congelado)
- O modelo e conservador: prefere nao dar falso "Quente" a perder oportunidades reais.

**O que foi construido:**
- Scoring engine com 5 componentes explicaveis (0-100 pontos)
- 5 tipos de alerta inteligente com acoes recomendadas
- Interface com 5 visoes: Pipeline, Kanban, Dashboard, Equipe (heatmap), Detalhe do deal
- API REST com 8 endpoints
- Debug sistematico que identificou e corrigiu 14 bugs (6 de alta severidade)

### Recomendacoes

Em ordem de prioridade:

1. **Implementar a visao Monday Morning como rotina**: o Kanban com 3 colunas (Fechar Agora / Nutrir / Repensar) deve ser o ponto de partida de cada semana de vendas. Os deals na coluna "Fechar Agora" representam a maior probabilidade de receita imediata.

2. **Agir nos deals "Parado" e "Esfriando"**: deals acima de 2x a media de tempo no pipeline (~104 dias) tem probabilidade muito baixa de conversao. A recomendacao e fazer um review semanal desses deals com o gerente e decidir entre reengajar ou descartar — liberar o vendedor para focar em deals com mais potencial.

3. **Explorar as combinacoes produto x setor com alto win rate**: a variacao de 52% a 73% entre combinacoes sugere que existe fit de mercado que pode ser explorado. Direcionar vendedores para setores onde seus produtos convertem mais.

4. **Integrar com CRM real**: a maior limitacao atual e os dados estaticos. Conectar com Salesforce/HubSpot/Pipedrive via API permitiria scores atualizados em tempo real e adotar a ferramenta no dia a dia.

5. **Evoluir para modelo de ML**: os 5 componentes atuais podem servir como features iniciais para um modelo preditivo (XGBoost ou regressao logistica) treinado nos dados historicos, com recalibracao automatica periodica.

### Limitacoes

- **Dados estaticos**: a solucao carrega CSVs no startup — nao ha ingestao em tempo real de CRM.
- **Data de referencia fixa**: usa `max(close_date)` como "hoje" (2017-12-31). Em producao, usaria a data corrente.
- **Sem modelo de ML**: o scoring usa regras calibradas manualmente nos dados historicos, nao um modelo preditivo treinado. A acuracia poderia melhorar com ML.
- **68% dos deals sem conta**: a maioria dos deals ativos nao tem conta vinculada, limitando significativamente o componente Account Quality (recebem score neutro 5/20).
- **Calibracao especifica**: os pesos foram otimizados para este dataset. Com dados de outro CRM, precisariam de recalibracao.
- **Sem autenticacao**: qualquer pessoa com acesso ao URL ve todos os dados — nao ha controle de acesso por papel.
- **Sem persistencia de acoes**: o vendedor nao consegue registrar que contatou, agendou ou descartou um deal. Isso impede feedback loop para o modelo.
- **Sem testes automatizados**: a solucao nao tem suite de testes. Para producao, seria essencial ter testes unitarios no scoring e integracao nos endpoints.

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| Claude Code (Claude Opus 4.6) | Analise inicial dos dados, construcao da logica do backend (scoring engine, alertas, data loader) e frontend (SPA com Alpine.js + Tailwind) |
| Google Gemini | Brainstorming de abordagens e validacao de ideias |
| VS Code | Finalizacao da logica e debugging |

### Skills instaladas (Claude Code + VS Code)

Tanto o Claude Code quanto o VS Code tinham skills instaladas para melhorar a performance da IA:

| Categoria | Skill | Caminho |
|-----------|-------|---------|
| Brainstorming | brainstorming | `.agents/skills/brainstorming` |
| Analise de dados | data-scientist | `.agents/skills/data-scientist` |
| Frontend | frontend-design | `.agents/skills/frontend-design` |
| Debugging | debugger | `.agents/skills/debugger` |
| Debugging | systematic-debugging | `.agents/skills/systematic-debugging` |
| Debugging | debugging-strategies | `.agents/skills/debugging-strategies` |

### Workflow

1. **Analise exploratoria dos dados** (Claude Code): carreguei os 4 CSVs, identifiquei distribuicoes, correlacoes e sinais discriminativos entre Won e Lost. Descobri que tempo no pipeline e produto x setor sao os melhores preditores.

2. **Design do scoring engine** (Claude Code + Gemini): brainstormei abordagens (regras vs ML), defini 5 componentes com pesos baseados na capacidade discriminativa de cada variavel. Calibrei retroativamente nos deals fechados.

3. **Construcao do backend** (Claude Code): implementei data_loader, scoring_engine e alerts.py. API REST com FastAPI, 8 endpoints.

4. **Construcao do frontend** (Claude Code): SPA com Alpine.js + Tailwind. 5 visoes: Pipeline, Kanban, Dashboard, Equipe, Detalhe do deal. Iteracoes no heatmap e nas pills visuais de score.

5. **Debug sistematico** (Claude Code + VS Code): debug arquivo por arquivo usando skill de systematic-debugging. 14 bugs encontrados, 6 de alta severidade. Corrigidos e validados.

6. **Refinamento de UX** (VS Code): ajustes finais na interface, tratamento de erros HTTP, cache buster.

### Onde a IA errou e como corrigi

**Erros de frontend:**
- O heatmap de Equipe x Regiao precisou de 3 iteracoes para ficar usavel. A primeira versao (tabela com dados inline) ficou poluida e pouco intuitiva. A segunda (grid com barras de progresso e opacidade variavel) ficou confusa visualmente. Somente a terceira versao (heatmap simplificado — apenas cor de fundo + score grande + tooltip no hover) atingiu o nivel de clareza necessario.
- A coluna de "Acao Sugerida" na tabela do pipeline aparecia como um quadrado vazio. A causa era o servidor rodando uma versao antiga do codigo que nao incluia o campo `suggested_action` na resposta da API. A IA nao identificou isso sozinha — precisou de feedback do usuario para investigar.

**Erros de logica (14 bugs encontrados no debug sistematico):**
- **Normalizacao inconsistente**: o nome do produto "GTXPro" era normalizado para "GTX Pro" no pipeline, mas nao na tabela de produtos. Isso fazia o join falhar silenciosamente, deixando deals GTX Pro sem preco e sem serie.
- **Guards de NaN quebrados**: `if revenue and ...` rejeitava `revenue=0` como se fosse ausente. `close_value=NaN` passava pelo guard `is None or == 0` e gerava score errado de 4.0.
- **Ordem de prioridade de alertas**: o alerta "Parado" tinha prioridade sobre "Oportunidade Quente". Se a media de dias fosse baixa, um deal com score 80 era marcado como "Parado" ao inves de "Quente" — ocultando oportunidades reais.
- **Mutacao de cache global**: o endpoint de pipeline escrevia `display_stage` diretamente nos dicts globais, contaminando o cache para todas as requisicoes seguintes.
- **Dashboard ignorando filtros**: o win rate por produto e a contagem de deals por stage usavam dados globais ao inves dos dados filtrados por regiao/gerente.

### O que eu adicionei que a IA sozinha nao faria

A IA construiu a infraestrutura tecnica — scoring engine, endpoints, tabelas. Mas as decisoes de **produto** que transformam dados em ferramenta util para vendedor vieram de visao humana:

**Kanban Monday Morning**: A IA entregou uma tabela ordenada por score. Fui eu que identifiquei que o vendedor nao abre o dia lendo tabela — ele precisa de uma visao de priorizacao imediata em colunas: "o que fecho hoje", "o que nutro essa semana", "o que descarto". A separacao em 3 buckets com drag & drop simula o fluxo mental real de um vendedor priorizando sua carteira na segunda de manha.

**Visao por gerente (Heatmap Equipe x Regiao)**: A IA criou uma tabela flat com 35 vendedores. Fui eu que percebi que o gerente nao precisa ver vendedor por vendedor — ele precisa de uma visao macro: "qual equipe minha performa melhor em qual regiao?". O heatmap cruzado gerente x regiao responde isso em 2 segundos. A IA precisou de 3 iteracoes e direcao constante para chegar no formato visual correto.

**Sugestao de to-do para o vendedor**: A IA calculava score e classificava em labels. Fui eu que pedi que cada deal tivesse uma acao sugerida concreta — nao basta dizer "Quente", o vendedor precisa ler "Ligar agora" ou "Agendar follow-up". A pill colorida com urgencia (alta/media/baixa) e um nivel de prescricao que a IA sozinha nao adicionaria porque ela otimiza para dados, nao para comportamento humano.

**Dashboard com filtros que funcionam**: A IA construiu o dashboard com KPIs, mas os filtros de regiao e gerente so se aplicavam a alguns KPIs — o win rate por produto e a contagem por stage mostravam dados globais sempre. Fui eu que testei os filtros e percebi a inconsistencia. Sem esse teste manual, o gerente veria dados errados ao filtrar por sua regiao.

Em resumo: a IA e excelente para implementar logica, processar dados e gerar codigo. Mas as decisoes de "o que o usuario realmente precisa ver" — a camada de produto — vieram da experiencia humana com vendas e gestao comercial.

---

## Evidencias

- [x] Screenshots das conversas com IA e screen recordings do workflow: [Google Drive](https://drive.google.com/drive/folders/1h1vEIUVaihxnLYgEEXPv4g_vTYdNjqso?usp=sharing)
- [x] Git history (codigo construido iterativamente com commits)
- [x] Skills de IA instaladas em `.agents/skills/`
- [x] Debug log: 14 bugs identificados e corrigidos com rastreamento arquivo por arquivo

---

## Setup — Como Rodar

### Requisitos
- Python 3.10+
- pip

### Instalacao e execucao

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Rodar o servidor
python app.py

# 3. Acessar no navegador
# http://localhost:8000
```

### Dependencias
| Pacote | Versao | Funcao |
|--------|--------|--------|
| FastAPI | 0.115.0 | Framework web (API REST + templates) |
| Uvicorn | 0.30.6 | Servidor ASGI |
| Pandas | 2.2.2 | Processamento de dados |
| Jinja2 | 3.1.4 | Renderizacao de templates HTML |

---

## Estrutura do Projeto

```
G4 Challenge/
├── app.py                     # FastAPI: startup, 8 API endpoints, HTML route
├── requirements.txt           # fastapi, uvicorn, pandas, jinja2
├── backend/
│   ├── data_loader.py         # Leitura de CSVs, limpeza, joins, lookups
│   ├── scoring_engine.py      # 5 componentes de scoring (0-100)
│   └── alerts.py              # 5 tipos de alerta + buckets de prioridade
├── static/
│   ├── css/styles.css         # Estilos customizados (gauge, scrollbar, transicoes)
│   └── js/app.js              # Alpine.js: state, API calls, heatmap, drag & drop
├── templates/
│   └── index.html             # SPA com 5 visoes (Alpine.js + Tailwind)
└── data/
    ├── accounts.csv           # 85 contas
    ├── products.csv           # 7 produtos (3 series)
    ├── sales_teams.csv        # 35 vendedores, 6 managers, 3 regioes
    └── sales_pipeline.csv     # 8.800 oportunidades
```

---

_Submissao enviada em: 10/03/2026_
