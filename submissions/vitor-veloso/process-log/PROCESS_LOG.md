# Process Log — Case 003: Lead Scorer

**Candidato:** Vitor Ricardo Ferreira Veloso  
**GitHub:** [vvitorveloso](https://github.com/vvitorveloso)  
**Data:** 17/11/2026  
**Desafio:** G4 AI Master — Challenge 003: Lead Scorer (RevOps / Build)  

---

## 1. Ferramentas Utilizadas e Justificativa

| Ferramenta | Propósito no Desafio | Justificativa de Escolha |
|---|---|---|
| **Google Antigravity CLI / Gemini 3.8 Flash** | Exploração analítica, estruturação de arquitetura, geração de código, refatoração de regras e documentação. | Capacidade analítica profunda para leitura de dados complexos, raciocínio em múltiplos passos e integração fluida com ambiente shell/git. |
| **Python 3 & Pandas** | Carga, transformação e validação determinística de dados. | Padrão da indústria para análise tabular; confiabilidade estatística e reprodutibilidade imediata. |
| **Vanilla HTML5, CSS3 Moderno & JS (ES6)** | Interface visual interativa (Dashboard de Priorização). | Zero overhead de instalação para o usuário final; roda diretamente em qualquer navegador sem `npm`, `node` ou builds complexos. |
| **Git & GitHub CLI / SSH** | Controle de versão, isolamento em branch de entrega e abertura de Pull Request. | Rastreabilidade completa de todas as alterações sem tocar em arquivos fora da pasta de submissão do candidato. |

---

## 2. Decomposição do Problema

Antes de escrever qualquer código ou promptar solicitações, o desafio da Head de RevOps foi decomposto nas seguintes etapas lógicas:

1. **Objetivo do Usuário Final (Vendedor):**
   - O vendedor abre a tela na segunda-feira às 8h da manhã.
   - Ele não quer ver um ranking puramente baseado em maior valor (pois deals de $50k travados há 6 meses desperdiçam tempo).
   - Ele precisa responder a duas perguntas: *"Quais são os 3 a 5 deals que devo ligar hoje?"* e *"Por que esses deals têm prioridade sobre os outros?"*.

2. **Diagnóstico dos Dados Reais:**
   - Auditoria das 4 tabelas relacionais do CRM (`sales_pipeline.csv`, `accounts.csv`, `products.csv`, `sales_teams.csv`).
   - Identificação de lacunas nos dados (ex: ausência de contas associadas a leads recentes, divergências de string entre tabelas).
   - Levantamento de benchmarks históricos reais a partir das 6.711 oportunidades já concluídas (Won vs Lost).

3. **Arquitetura de Scoring & Explainability:**
   - Criação de uma matriz de pontuação balanceada e explicável de 0 a 100 pontos, contemplando:
     - Estágio de maturidade comercial (`Engaging` vs `Prospecting`).
     - Frescor temporal e penalização de inatividade (decay temporal).
     - Fit da conta e taxa de conversão histórica do cliente.
     - Ticket financeiro do produto.
     - Taxa de sucesso histórica do vendedor.
   - Cálculo de *Expected Value* ($\text{EV} = \text{Score\%} \times \text{Valor}$) para visão executiva de diretoria.
   - Tradução dos fatores matemáticos em justificativas qualitativas claras em português e recomendação acionável de próximo passo.

4. **Entrega de Interface Útil:**
   - Criação de uma CLI robusta para automações e exportações rápidas.
   - Criação de uma aplicação web autocontida com visualização rica, cartões de KPI, filtros dinâmicos por vendedor e região, e tabela interativa de oportunidades.

---

## 3. Onde a IA Errou e Como Foi Corrigida (Iterações e Julgamento Humano)

Durante o desenvolvimento assistido por IA, intervenções críticas foram necessárias:

1. **Tentativa inicial de utilizar modelos de Machine Learning caixa-preta:**
   - *Comportamento da IA:* A primeira sugestão padrão de IA foi treinar um classificador `RandomForest` ou `XGBoost` usando scikit-learn para estimar probabilidade de vitória.
   - *Correção Humana:* Rejeitei a abordagem. Conforme a especificação do case destaca: *"A Head de RevOps não quer um modelo em notebook que ninguém vai usar... explainability ganha. Um scoring baseado em regras + heurísticas bem apresentado vale mais que um XGBoost sem interface."* Redirecionei o desenvolvimento para um motor determinístico modular por pilares com pesos auditáveis, onde cada ponto adicionado ou subtraído possui explicação textual explícita.

2. **Divergência de nomenclatura no Dataset (`GTXPro` vs `GTX Pro`):**
   - *Descoberta da IA:* Ao inspecionar os merges entre tabelas, a análise identificou que mais de 1.100 oportunidades estavam com valor nulo de produto porque no pipeline constava `'GTXPro'` e na tabela de produtos constava `'GTX Pro'`.
   - *Ação:* Implementamos o saneamento explícito em `scoring_engine.py` para padronizar os nomes, garantindo que 100% dos produtos fossem precificados corretamente.

3. **Tratamento de Leads sem Conta Associada (68% dos ativos):**
   - *Desafio:* A IA inicialmente sugeriu descartar oportunidades com `account == NaN` por considerá-las dados corrompidos.
   - *Intervenção Humana:* Identifiquei que na prática comercial de RevOps, muitas oportunidades em estágio embrionário (`Prospecting` e início de `Engaging`) chegam via inbound/outbound antes do vendedor formalizar o cadastro da empresa no CRM. Em vez de descartar, incorporamos isso como regra de negócio: atribuímos uma pontuação base reduzida, geramos um alerta visual explícito de *"Cadastro incompleto (sem conta)"* e recomendamos como próximo passo *"Identificar e cadastrar a empresa cliente no CRM"*.

---

## 4. O que eu Adicionei que a IA Sozinha Não Faria

- **Concepção de Tiers Operacionais Comerciais:** A divisão das oportunidades em 4 grupos práticos (*Prioridade Alta*, *Prioridade Média*, *Em Risco* e *Prioridade Baixa*) alinhada aos rituais de vendas de uma equipe de 35 consultores.
- **Detecção de "Deal Staling" (Negócios Estagnados):** O dado mostrou que negócios fechados com vitória demoram em média 52 dias. Ao constatar negócios ativos há mais de 150 dias sem desfecho, introduzimos a penalidade de estagnação de até -25 pontos e a classificação direta no tier "Em Risco", evitando que a equipe comercial perca tempo com deals zumbis.
- **Usabilidade Zero-Barrier:** Em vez de exigir que a avaliadora instale pacotes pesados como Streamlit ou configure ambientes virtuais complexos, desenhei uma arquitetura em que o script compila um relatório HTML5 moderno e autocontido, servido por um servidor HTTP nativo do Python na porta 8050. Funciona em qualquer sistema operacional com apenas 1 comando.

---

## 5. Histórico de Versões e Commits

A construção foi conduzida em etapas atômicas e registradas na branch `submission/vitor-veloso`:
- *Commit 1:* Download e integração dos dados reais do Kaggle CRM em `solution/data/`.
- *Commit 2:* Implementação do motor `scoring_engine.py` com calibragem de benchmarks históricos e explainability.
- *Commit 3:* Construção da CLI e gerador de Dashboard Web `lead_scorer_app.py` e servidor `server.py`.
- *Commit 4:* Elaboração da documentação completa em `README.md` e do Process Log em `process-log/PROCESS_LOG.md`.
