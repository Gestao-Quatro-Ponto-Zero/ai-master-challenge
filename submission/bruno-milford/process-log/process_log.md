# Process Log — RavenStack Churn Intelligence

## 1. Identificação da entrega

- **Autor:** Bruno Milford de Oliveira
- **LinkedIn:** https://www.linkedin.com/in/bruno-milford-de-oliveira-848958151/
- **Challenge:** Diagnóstico de churn SaaS B2B — RavenStack
- **Solução desenvolvida:** Dashboard interativo de churn, retenção, receita, uso, suporte e contas em risco
- **Stack principal:** Python, Flask, SQLite, Jinja2, HTML, CSS, JavaScript e Plotly.js
- **Data da entrega:** 20 de julho de 2026

---

## 2. Objetivo deste registro

Este documento registra como a solução foi construída, quais ferramentas de inteligência artificial foram utilizadas, quais decisões foram tomadas, onde ocorreram erros, como esses erros foram corrigidos e qual foi a participação humana no resultado final.

O processo não consistiu apenas em gerar código por meio de IA. A solução foi construída de forma iterativa, com análise dos dados, definição das regras, validação dos cálculos, revisão visual, correção de falhas de carregamento e documentação técnica.

---

## 3. Arquivos de dados utilizados

Foram utilizadas cinco bases principais:

| Arquivo | Finalidade | Chave principal ou de relacionamento |
|---|---|---|
| `ravenstack_accounts.csv` | Cadastro e características das contas | `account_id` |
| `ravenstack_subscriptions.csv` | Assinaturas, planos, MRR, ARR e vigência | `subscription_id`, `account_id` |
| `ravenstack_feature_usage.csv` | Uso de funcionalidades e comportamento do produto | `subscription_id` |
| `ravenstack_support_tickets.csv` | Chamados de suporte, resolução, satisfação e escalonamentos | `account_id` |
| `ravenstack_churn_events.csv` | Eventos de churn, reativação e motivos registrados | `account_id` |

Os arquivos foram consolidados em um banco SQLite local:

```text
database/ravenstack.db
```

A visão executiva principal foi estruturada no nível de `account_id`.

A relação entre uso e conta foi realizada por meio de `subscription_id`.

---

## 4. Ferramentas utilizadas

| Ferramenta | Utilização |
|---|---|
| **ChatGPT** | Estruturação do problema, formulação de hipóteses, revisão analítica, criação dos prompts, discussão das métricas e preparação da submissão |
| **OpenAI Codex** | Leitura do repositório, criação e edição de código, construção do dashboard, correções, testes e documentação |
| **Python** | Processamento, consolidação dos dados e execução da aplicação |
| **Flask** | Backend, rotas de página e endpoints JSON |
| **SQLite** | Armazenamento consolidado das cinco bases |
| **pandas** | Importação e tratamento dos dados na criação do banco |
| **Jinja2** | Renderização dos templates HTML |
| **JavaScript** | Consumo da API, filtros, gráficos, tabelas e interações |
| **Plotly.js** | Visualização interativa dos dados |
| **HTML e CSS** | Construção e identidade visual da interface |
| **Git/GitHub** | Versionamento e organização da entrega |
| **unittest** | Validação automatizada das principais rotas e comportamentos |

---

## 5. Etapas do processo

### Etapa 1 — Entendimento do problema

O ponto inicial foi interpretar a contradição apresentada no desafio:

- os números indicavam aumento de churn;
- o time de Produto afirmava que o uso da plataforma havia crescido;
- o time de Customer Success entendia que o suporte e a satisfação estavam adequados.

A primeira decisão foi não aceitar indicadores agregados como explicação suficiente.

A investigação foi organizada para responder:

1. O churn aumentou em quantidade de contas ou também em receita?
2. O crescimento de uso ocorreu de maneira uniforme?
3. Existem segmentos com queda de uso escondidos pela média geral?
4. A satisfação média esconde contas com problemas recorrentes?
5. O churn está concentrado no início do relacionamento?
6. Quais contas ativas possuem sinais semelhantes aos churners?
7. Qual combinação de ações deveria ser priorizada?

---

### Etapa 2 — Análise das cinco bases

As cinco bases foram cruzadas para formar uma visão consolidada de cada conta.

Antes do cruzamento, foi necessário considerar que as tabelas possuíam granularidades diferentes:

- uma conta pode ter várias assinaturas;
- uma assinatura pode possuir muitos registros de uso;
- uma conta pode possuir vários tickets;
- uma conta pode possuir vários eventos de churn e reativação.

Para evitar dupla contagem, uso, suporte e eventos foram agregados antes de serem relacionados à visão principal.

A regra adotada foi:

```text
accounts.account_id
 ├── subscriptions.account_id
 ├── support_tickets.account_id
 └── churn_events.account_id

subscriptions.subscription_id
 └── feature_usage.subscription_id
```

---

### Etapa 3 — Identificação da inconsistência de churn

Durante a análise, foi encontrada uma inconsistência importante entre:

- o campo `churn_flag` da tabela de contas;
- os eventos efetivos da tabela `churn_events`.

A análise inicial encontrou:

- **339 contas** com evento efetivo de churn não classificado como reativação;
- **110 contas** marcadas com `churn_flag = true`;
- **265 contas** com evento de churn, mas sem a flag correspondente;
- **36 contas** com flag de churn, mas sem evento correspondente.

Essa divergência foi registrada como problema de qualidade dos dados.

Para que o dashboard utilizasse uma regra única, foi definida uma lógica consolidada.

```sql
CASE
    WHEN ultimo_evento.is_reactivation = 1 THEN 0
    WHEN ultimo_evento.churn_event_id IS NOT NULL THEN 1
    WHEN accounts.churn_flag = 1 THEN 1
    ELSE 0
END AS churned_account
```

Interpretação:

1. se o evento mais recente for uma reativação, a conta é considerada ativa;
2. caso contrário, se existir evento de churn, a conta é considerada churn;
3. na ausência de evento, utiliza-se `churn_flag` como fallback.

Essa regra passou a ser utilizada de forma centralizada no dashboard.

---

### Etapa 4 — Diagnóstico inicial

O primeiro diagnóstico consolidou:

- **500 contas**;
- **5.000 assinaturas**;
- **25.000 registros de uso**;
- **2.000 tickets**;
- **600 eventos de churn e reativação**.

Os principais achados foram:

- 339 de 500 contas possuíam evento efetivo de churn;
- aproximadamente 49,6% dos churners cancelaram em até 90 dias;
- cerca de 67,2% cancelaram em até 180 dias;
- a mediana de relacionamento dos churners foi de 93 dias;
- a mediana das contas ainda ativas foi de 298 dias;
- o uso médio nos 30 dias anteriores ao churn foi de 21,8 interações;
- o uso médio das contas ativas foi de 19,5 interações;
- a satisfação média foi semelhante entre churners e contas ativas;
- os motivos mais recorrentes estavam associados a funcionalidades, preço, orçamento, concorrência e suporte.

A conclusão foi que o churn não parecia ser causado principalmente por baixo uso ou satisfação média ruim.

O padrão mais forte foi:

```text
churn precoce + desalinhamento entre expectativa, funcionalidades, preço e orçamento
```

---

### Etapa 5 — Construção do primeiro prompt para o Codex

Foi criado um prompt para transformar os dados em um dashboard interativo.

A primeira versão solicitava:

- aplicação web local;
- leitura das bases;
- cruzamento das cinco tabelas;
- gráficos;
- filtros;
- KPIs;
- análise de churn;
- receita perdida;
- suporte;
- uso;
- contas em risco;
- qualidade dos dados;
- metodologia.

Essa etapa resultou na criação da estrutura inicial da aplicação.

---

### Etapa 6 — Implementação do protótipo Flask

O Codex analisou o repositório e criou uma aplicação modular com:

- Flask;
- SQLite;
- Jinja2;
- endpoints JSON;
- gráficos;
- filtros;
- tabelas;
- página de contas;
- página de detalhes;
- exportação CSV;
- README;
- testes.

Principais arquivos criados ou alterados:

```text
app.py
config.py
requirements.txt
README.md

routes/
├── api_routes.py
└── page_routes.py

services/
├── database_service.py
├── dashboard_service.py
├── churn_service.py
├── risk_service.py
└── account_service.py

templates/
├── base.html
├── dashboard.html
├── accounts.html
└── account_detail.html

static/
├── css/styles.css
└── js/
    ├── dashboard.js
    ├── accounts.js
    └── account_detail.js

tests/
└── test_app.py
```

Endpoints implementados:

```text
/api/health
/api/filters
/api/kpis
/api/churn/timeline
/api/churn/reasons
/api/churn/segments
/api/revenue
/api/usage
/api/support
/api/reactivation
/api/risk-accounts
/api/accounts
/api/accounts/<account_id>
/api/export/risk-accounts.csv
```

Testes registrados:

- 7 testes com `unittest`;
- validação HTTP de rotas;
- resposta HTTP 200;
- carregamento de 500 contas;
- exportação CSV;
- página inicial;
- listagem de contas;
- detalhe de conta.

---

### Etapa 7 — Revisão dos cálculos

Após a primeira implementação, foi solicitado ao Codex que explicasse como os cards do dashboard eram calculados.

Essa etapa foi necessária para verificar se os valores exibidos possuíam lógica correta.

A principal regra foi não somar todas as assinaturas históricas de uma conta.

Para cada conta:

1. se existir assinatura sem `end_date`, ela é priorizada;
2. caso contrário, é utilizada a assinatura mais recente por `start_date`.

Essa regra evita inflar MRR e ARR ao somar contratos antigos da mesma conta.

Principais cálculos:

| Indicador | Regra |
|---|---|
| Total de contas | Quantidade de contas na base consolidada filtrada |
| Contas ativas | Contas com `churned_account = 0` |
| Contas com churn | Contas com `churned_account = 1` |
| Taxa de churn | Contas com churn ÷ total de contas × 100 |
| MRR ativo | Soma do MRR da assinatura representativa das contas ativas |
| ARR ativo | Soma do ARR da assinatura representativa das contas ativas |
| MRR perdido | Soma do MRR da assinatura representativa das contas com churn |
| ARR perdido | Soma do ARR da assinatura representativa das contas com churn |
| Ticket médio mensal | Média de MRR das contas com valor maior que zero |
| Total de tickets | Soma dos tickets das contas filtradas |
| Contas reativadas | Contas com pelo menos um evento `is_reactivation = 1` |
| Alto risco | Contas ativas com `risk_score >= 60` |

Exemplo utilizado no dashboard:

```text
Total de contas = 500
Contas com churn = 350
Taxa de churn = 350 / 500 = 70,00%
Contas ativas = 500 - 350 = 150
```

---

### Etapa 8 — Ajuste visual do dashboard

A primeira interface funcional ainda apresentava aparência simples e pouco adequada para apresentação executiva.

Foi criado um novo prompt para o Codex, com foco em:

- layout SaaS B2B;
- sidebar escura;
- topbar;
- agrupamento de KPIs;
- filtros recolhíveis;
- responsividade;
- hierarquia visual;
- tabelas executivas;
- estados de carregamento;
- estados vazios;
- tratamento de erros;
- acessibilidade;
- melhor organização do JavaScript;
- preservação das APIs e regras existentes.

O Codex reestruturou a interface sem alterar:

- consultas SQL;
- endpoints;
- regras de churn;
- regra de receita;
- score heurístico.

Foram criados helpers JavaScript:

```text
static/js/api.js
static/js/ui.js
static/js/formatters.js
static/js/charts.js
```

Foram preservadas as páginas:

```text
/
/accounts
/accounts/<account_id>
```

O layout passou a ter:

- shell SaaS;
- sidebar;
- topbar;
- KPIs agrupados;
- filtros globais;
- seção executiva de atenção;
- gráficos reorganizados;
- tabela de risco;
- página de contas;
- visão detalhada de Customer Success;
- skeleton loaders;
- mensagens de erro;
- responsividade.

---

### Etapa 9 — Problema no carregamento dos gráficos

Após a reformulação, os dados estavam disponíveis nas APIs, mas alguns gráficos apareciam vazios.

A investigação identificou que os gráficos dependiam do Plotly carregado via CDN.

Quando a CDN falhava ou demorava, os containers permaneciam vazios.

A primeira correção tornou o carregamento assíncrono e adicionou um fallback local.

Mesmo assim, o comportamento ainda não ficou suficientemente confiável em todos os testes.

O problema foi reportado novamente, pois uma análise de dados não poderia ser apresentada com gráficos vazios.

---

### Etapa 10 — Correção definitiva do carregamento

A segunda correção mudou a estratégia:

1. o gráfico local em HTML/CSS passou a ser renderizado primeiro;
2. os dados reais da API são exibidos independentemente do Plotly;
3. se o Plotly carregar, ele melhora a visualização;
4. se o Plotly falhar, a representação local permanece visível;
5. foi adicionado cache-busting para evitar scripts antigos no navegador;
6. o dashboard deixou de falhar por causa de APIs secundárias.

Foram validados:

- churn ao longo do tempo;
- motivos de churn;
- churn por plano;
- churn por indústria;
- churn por país;
- KPIs com 500 contas;
- APIs principais com status 200;
- testes unitários;
- validação de sintaxe JavaScript.

Essa foi a correção que resolveu com sucesso o carregamento dos dados.

---

### Etapa 11 — Inclusão do plano de ação

Após os dados e gráficos estarem funcionando, foi solicitada a inclusão de um plano de ação diretamente na página inicial.

O objetivo foi evitar que o dashboard apenas apresentasse informações sem orientar decisões.

Foi criado um bloco com cinco prioridades dinâmicas, derivadas dos dados carregados:

1. contas críticas;
2. receita de alto valor em risco;
3. principal motivo de churn;
4. contas sem uso recente;
5. segmento ou indicador de satisfação que exige ação.

Arquivos alterados:

```text
templates/dashboard.html
static/js/dashboard.js
static/css/styles.css
```

O plano de ação foi posicionado após a seção “O que exige atenção”.

---

### Etapa 12 — Documentação técnica

Foi criado um prompt específico para o Codex analisar todo o repositório e produzir documentação fiel ao projeto real.

O Codex:

- analisou código Python;
- inspecionou rotas;
- revisou serviços;
- verificou banco SQLite;
- revisou scripts;
- validou dependências;
- verificou comandos;
- executou testes;
- eliminou caminhos absolutos;
- registrou limitações.

Documentos criados ou atualizados:

```text
README.md

docs/
├── ARCHITECTURE.md
├── DATABASE.md
├── DATA_DICTIONARY.md
├── MODEL.md
├── USER_GUIDE.md
└── TROUBLESHOOTING.md

.env.example
.gitignore
```

Comandos confirmados:

```powershell
pip install -r requirements.txt
python database/import_csv_to_sqlite.py
python database/check_database.py
python app.py
```

URL local:

```text
http://127.0.0.1:5000
```

Validações registradas:

- instalação das dependências;
- recriação das cinco tabelas;
- verificação do banco;
- sete testes unitários;
- inicialização do Flask;
- `/api/health` com HTTP 200;
- remoção de caminhos pessoais da documentação;
- ausência de senhas, tokens e credenciais.

---

## 6. Onde a IA errou ou produziu resultado insuficiente

### 6.1. Gráficos com categorias numéricas

Na primeira versão, alguns gráficos exibiam categorias como:

```text
0, 1, 2, 3
```

em vez dos nomes reais.

A correção exigiu revisar:

- labels;
- valores;
- agrupamentos;
- ordem das categorias;
- processamento de objetos JavaScript;
- mapeamento de nomes.

---

### 6.2. Ordem incorreta das faixas de relacionamento

O gráfico de tempo até churn ordenava as categorias de forma alfabética ou pelo valor.

Foi definida uma ordem fixa:

```text
0–30 dias
31–90 dias
91–180 dias
181–365 dias
Mais de 365 dias
```

---

### 6.3. Taxa de churn calculada com denominador incorreto

Uma versão inicial poderia calcular churn apenas sobre as contas canceladas, levando segmentos a apresentar 100%.

A fórmula foi corrigida para:

```text
taxa de churn =
contas com churn no segmento
÷
total de contas do segmento
```

Os tooltips passaram a apresentar:

- nome do segmento;
- contas com churn;
- total de contas;
- taxa.

---

### 6.4. Dupla contagem de receita

Somar todas as assinaturas históricas por conta inflaria MRR e ARR.

A correção foi selecionar apenas uma assinatura representativa por conta.

---

### 6.5. Dependência do Plotly via CDN

Os dados chegavam pelas APIs, mas os gráficos podiam ficar vazios quando o Plotly não carregava.

A correção final foi implementar visualização local independente da CDN.

---

### 6.6. Primeira interface pouco executiva

O protótipo inicial funcionava, mas apresentava:

- gráficos excessivamente grandes;
- pouca hierarquia;
- organização visual simples;
- tabelas densas;
- aparência pouco adequada para CEO e equipes executivas.

Foi necessário criar um prompt específico para UX/UI e revisar a implementação.

---

### 6.7. Limitação de testes no ambiente

Em algumas execuções, o ambiente virtual existente não podia ser utilizado e o comando `pytest` não estava disponível.

A solução foi:

- validar com o Python acessível no ambiente;
- utilizar `unittest`, que já fazia parte da implementação;
- realizar smoke tests HTTP;
- executar `node --check` nos arquivos JavaScript;
- registrar de forma transparente a limitação.

---

## 7. O que foi adicionado por decisão humana

A IA acelerou código, documentação e revisão, mas as decisões principais não foram delegadas integralmente.

Foram decisões humanas:

- tratar a contradição entre CEO, Produto e CS como centro da análise;
- não assumir que uso agregado significa saúde de toda a base;
- não usar satisfação média como evidência suficiente;
- separar quantidade de churn de impacto financeiro;
- exigir denominadores nos percentuais;
- impedir dupla contagem de receita;
- definir uma regra única de churn;
- separar risco de churn de impacto financeiro;
- não chamar score heurístico de modelo preditivo calibrado;
- solicitar explicação dos cálculos;
- rejeitar gráficos sem dados visíveis;
- exigir uma interface adequada para apresentação executiva;
- incluir um plano de ação no próprio dashboard;
- documentar limitações e inconsistências;
- manter o protótipo simples e executável localmente.

---

## 8. Score de risco

A solução utiliza um score heurístico e explicável.

O score considera sinais disponíveis, como:

- queda ou ausência recente de uso;
- baixa amplitude de funcionalidades;
- erros;
- tickets;
- escalonamentos;
- satisfação;
- downgrade;
- cobrança mensal;
- proximidade de renovação;
- MRR e ARR.

A classificação é utilizada apenas para priorização operacional.

O score não é apresentado como probabilidade estatística calibrada.

Faixas utilizadas no dashboard:

```text
Crítico
Alto
Médio
Baixo
```

Foi preservada a separação entre:

- risco comportamental;
- impacto financeiro;
- prioridade de atuação.

---

## 9. Limitações conhecidas

- Não existe um modelo preditivo de machine learning operacional.
- O score atual é heurístico.
- A base possui inconsistência entre `churn_flag` e eventos de churn.
- O SQLite não possui chaves primárias, estrangeiras, constraints ou índices explícitos em todas as tabelas.
- A importação recria as tabelas e não é incremental.
- Não existe autenticação.
- Não existe controle de acesso.
- Não existe deploy em ambiente produtivo.
- Não existe pipeline automatizado de atualização.
- Plotly é carregado via CDN, embora exista fallback visual local.
- O projeto utiliza dados locais.
- A análise identifica associações e padrões, não causalidade.
- A licença do repositório ainda não foi definida.
- A regra oficial de churn precisa ser validada pela empresa antes de uso produtivo.

---

## 10. Evidências produzidas

As evidências do processo incluem:

- screenshots das conversas com IA;
- prompts enviados ao Codex;
- respostas do Codex;
- registros dos arquivos alterados;
- explicações das métricas;
- resultados de testes;
- correções de layout;
- correções de carregamento;
- plano de ação;
- documentação técnica;
- histórico Git;
- dashboard funcional;
- relatório de submissão em PDF.

---

## 11. Resultado final

A entrega final contém:

- banco SQLite consolidado;
- scripts de criação e validação do banco;
- aplicação Flask;
- endpoints JSON;
- dashboard executivo;
- filtros;
- KPIs;
- análise de churn;
- análise de receita;
- análise de uso;
- análise de suporte;
- análise de reativação;
- contas em risco;
- exportação CSV;
- página de exploração de contas;
- detalhamento individual;
- score heurístico;
- plano de ação;
- fallback para gráficos;
- testes;
- documentação técnica;
- relatório de submissão;
- evidências do processo com IA.

---

## 12. Comandos finais de execução

### Instalar as dependências

```powershell
pip install -r requirements.txt
```

### Criar ou recriar o banco

```powershell
python database/import_csv_to_sqlite.py
```

### Validar o banco

```powershell
python database/check_database.py
```

### Executar os testes

```powershell
python -m unittest discover -s tests
```

### Iniciar a aplicação

```powershell
python app.py
```

### Abrir o dashboard

```text
http://127.0.0.1:5000
```

---

## 13. Conclusão

A inteligência artificial foi utilizada como acelerador de análise, desenvolvimento e documentação.

O processo exigiu revisão contínua, testes, correção de lógica, validação de métricas e decisões humanas sobre o que realmente deveria ser apresentado.

O principal aprendizado foi que a qualidade da entrega não depende apenas de gerar código. Ela depende de:

- formular corretamente o problema;
- entender os dados;
- definir regras consistentes;
- questionar resultados;
- validar cálculos;
- corrigir erros;
- documentar limitações;
- transformar análise em ação.

A solução final busca unir análise técnica, clareza executiva e utilidade operacional.
