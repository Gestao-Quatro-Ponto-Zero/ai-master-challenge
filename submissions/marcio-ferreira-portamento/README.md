# Submissão — Marcio Ferreira — Challenge 003 (Lead Scorer)

## Sobre mim

- **Nome:** Marcio Ferreira (Estúdio Portamento Design)
- **Challenge escolhido:** 003 — Lead Scorer (Vendas / RevOps)

---

## Executive Summary

Construí uma plataforma de **Revenue Intelligence (CommandCenter)** full-stack usando Next.js e FastAPI. Em vez de entregar apenas uma tabela com "notas", a ferramenta fornece insights acionáveis no nível macro (Estagnação de pipeline, Hot Signals, Valor Esperado) e no nível micro (Scoring de cada deal acompanhado por uma rigorosa **Explainability Engine** que dita o próximo passo). 

A solução comprova que a inteligência de negócios + UX supera o uso raso de Machine Learning. Transformamos uma planilha estática em uma máquina de conversão baseada em *Signal-based Selling*.

---

## Solução e Regras de Negócio (O "Porquê")

### 1. Fim do "Achismo" (Redução de Ciclo de Venda)
Hoje, um vendedor acorda com milhares de leads na base e tenta adivinhar quem vai comprar. 
* **A Inteligência:** Nosso motor de IA cruzou o histórico e descobriu que produtos Premium em setores de Software possuem alta conversão. A IA prioriza esses clientes automaticamente, colocando o dinheiro mais próximo da mesa no topo da fila indiana do Pipeline.

### 2. A Regra dos "5 Minutos" e Sinais Quentes
Dados de mercado provam que responder um *Sinal Quente* nos primeiros minutos triplica as chances de conversão.
* **A Inteligência:** Criamos a **Aba de Filtro "Sinais Quentes"** que isola o ruído. O lead não se perde no meio de contatos antigos. O vendedor foca estritamente em quem está engajado agora.

### 3. Combate à Estagnação (O Gráfico de Zumbis)
Através da Análise de Dados (EDA) nos arquivos CSV, descobrimos que o ponto de não-retorno nesta base são **85 dias**. Passou disso, a chance de venda despenca.
* **A Inteligência:** O dashboard possui um **Gráfico de Barras de Tendência (Volume vs Estagnação)** que varre os leads reais e os categoriza por idade (<30d, 30-60d, 60-85d, 85+d), usando um sistema semafórico. Leads estagnados recebem *Red Flags* (🚨) e punições severas no Score.

### 4. A Matemática Transparente (Explainability Engine)
Sistemas convencionais dão um número "mágico" que o vendedor desconfia. Nossa solução não é uma "caixa preta".
* **Como funciona:** Todo lead nasce como um contato frio, recebendo um **Score Base Padrão de 40 pontos**. A partir daí, o sistema soma bônus (+20 por responder rápido, +10 por ser 'Sweet Spot') e subtrai penalidades (-20 por estagnar). 
* **O Modal:** Quando o usuário clica em "Ver Deal", o sistema explica linha a linha a matemática e sugere uma Ação (ex: "Ligar para Decisor").

### 5. Copiloto de IA Universal
Para acabar com a fricção de execução, todo Deal possui um botão **"Acionar Assistente de IA"**. A ideia é que o vendedor não perca 20 minutos redigindo um email de follow-up, a IA fará isso baseada no contexto exato do Score.

---

## Process Log — Como usei IA

> Fui auxiliado pelo meu AI Conselheiro ("Antigravity") durante toda a arquitetura, refatoração e implementação.

### Workflow & Pivotagem de Design
1. **EDA e Regras de Negócio:** A IA extraiu as estatísticas reais do CSV (limites de 85 dias, conversão por setor/tamanho) e cruzou com *benchmarks B2B reais* para montar o algoritmo de pontos em Python (`scorer.py`).
2. **Design e UX (O Efeito Puta Merda):** Originalmente, criamos um painel engessado (futurista demais). Como Diretor Criativo, solicitei à IA a transição para um padrão **SaaS Light Mode**, focado em acionabilidade. Refatoramos componentes para `Recharts` e filtros dinâmicos com `useState`.
3. **Debugging Cirúrgico:** A IA me auxiliou na resolução de um bug obscuro de quebra de caracteres Unicode (*Surrogate Pairs* de Emojis) no React que afetava o motor de explicabilidade.

### Ferramentas usadas
* **Gemini 3.1 Pro (Antigravity):** Análise exploratória, arquitetura de UI/UX, debugging de Next.js/Tailwind v4 e FastAPI.
* **Python (Pandas & FastAPI):** Base de ingestão de dados CSV e roteamento das APIS.
* **React (Next.js + Tailwind + Recharts):** Componentização e renderização limpa do Dashboard.
* **Docker:** Containerização para deploy instantâneo.

---

## Setup de Execução (Avaliação)

Para rodar a solução na sua máquina (sem precisar instalar Python ou Node localmente):
1. Tenha o [Docker Desktop](https://www.docker.com/products/docker-desktop) instalado e rodando.
2. Na raiz da pasta `solution/`, execute no terminal:
   ```bash
   docker-compose up --build
   ```
   *(Nota: O Docker construirá as imagens e instalará automaticamente todas as dependências de Backend/`requirements.txt` e Frontend/`node_modules` de forma isolada).*
3. Acesse **`http://localhost:3000`** no seu navegador para visualizar o CommandCenter com os dados dinâmicos da base. O ambiente Backend estará rodando na porta `8000`.

---
_Submissão finalizada e auditada conforme os padrões da Portamento Design._
