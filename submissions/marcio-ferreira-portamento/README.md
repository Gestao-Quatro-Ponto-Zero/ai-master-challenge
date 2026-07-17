# Submissão — Marcio Ferreira — Challenge 003 (Lead Scorer)

## Sobre mim

- **Nome:** Marcio Ferreira (Estúdio Portamento Design)
- **Challenge escolhido:** 003 — Lead Scorer (Vendas / RevOps)

---

## Executive Summary

Construí uma plataforma de **Revenue Intelligence (CommandCenter)** full-stack usando Next.js e FastAPI. Em vez de entregar apenas uma tabela com "notas", a ferramenta fornece insights acionáveis no nível macro (Estagnação de pipeline, Hot Signals, Valor Esperado) e no nível micro (Scoring de cada deal acompanhado por uma rigorosa **Explainability Engine** que dita o próximo passo). A solução comprova que a inteligência de negócios + UX supera o uso raso de ML.

---

## Solução

A solução finalizada pode ser orquestrada com um único comando Docker e roda em `localhost:3000` (Frontend) e `localhost:8000` (Backend).

### Abordagem

1. **Pesquisa de Mercado (B2B SaaS Benchmark):** Antes de programar, fiz um *deep-dive* no mercado B2B e descobri que ciclos Enterprise tendem a levar até 18 meses, enquanto SMBs levam ~45 dias.
2. **Análise do Dataset Específico (EDA):** Ao rodar scripts em Python (`pandas`) nos CSVs, descobri uma "pegadinha" no banco de dados fornecido: *todas* as empresas, independentemente do tamanho, fecham em uma média de **51 dias**. O limite para esfriar (percentil 75) é de **85 dias**.
3. **Engenharia Reversa da Burocracia:** Ajustei o scoring para o "Sweet Spot": empresas de faturamento médio/alto convertem mais (66%) que Enterprises gigantes (61%) por conta da proximidade com o decisor.

### Resultados / Findings

O nosso **Scoring Heurístico** atribui pontos baseados na ação atual:
*   🔥 **Hot Signals (+20 pts):** O deal passa de *Prospecting* para *Engaging* nos últimos dias. Isso aciona um alerta visual para o vendedor atuar **agora** (Signal-Based Selling).
*   🚨 **Stagnation Penalty (-20 pts):** Deals abertos há mais de 85 dias (limite estatístico validado pelo dataset) recebem um *red flag* para serem dados como "Lost" ou sofrerem intervenção da gestão.
*   **Explainability Engine:** O painel não dá um número vazio. Ele exibe caixas de texto literais: *"Score 82: Cliente no setor de Software (alta conversão). Empresa no Sweet Spot (baixo atrito de compra)."*

### Recomendações

1. **Integração AI Auto-Responder:** O botão "Acionar AI" no dashboard deve ser plugado a um webhook (ex: Make.com) para disparar follow-ups em menos de 5 minutos, aumentando a conversão.
2. **Signal-Based Trigger:** Conectar o pipeline a ferramentas de rastreio de navegação para que o status mude para "Engaging" automaticamente no momento em que o cliente acessar a página de preços.

### Limitações

A lógica de pontuação heurística atual baseia-se unicamente nas features fornecidas. Em escala, seria ideal substituir os pesos estáticos por um modelo Random Forest ou XGBoost, mas mantendo a interface de explicabilidade através do SHAP values. 

---

## Process Log — Como usei IA

> Fui auxiliado pelo meu AI Conselheiro ("Antigravity") durante toda a construção arquitetural.

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| **Gemini 3.1 Pro** | Análise exploratória dos dados, pesquisa de mercado de benchmarks B2B, arquitetura do algoritmo e geração das interfaces em React (Next.js) |
| **Python (Pandas)** | Cruzamento dos 4 CSVs e extração estatística do tempo de conversão (Percentil 75). |
| **Docker** | Containerização instantânea da solução para avaliação. |

### Workflow

1. A IA extraiu as estatísticas reais do `.csv` para descobrir que o tempo ótimo de conversão neste dataset é de ~50 dias.
2. Interrompi a geração de código pedindo para a IA procurar referências **reais do mercado externo** sobre B2B Tech, descobrindo o atrito do comitê de compras.
3. Decidimos cruzar a taxa de sucesso do dataset com a teoria do mercado para gerar um "Speed-to-Lead Penalty".
4. A IA construiu as rotas FastAPI no backend.
5. A IA construiu o painel do Next.js integrando as APIS.

### O que eu adicionei que a IA sozinha não faria

O insight sobre o **"Sweet Spot" de faturamento**: a IA notou a queda de conversão em empresas milionárias, mas foi o meu conhecimento tático que traduziu isso como *"O Decisor de uma SMB assina na hora; o da Enterprise exige 6 reuniões"*, transformando esse dado num score de burocracia na tela.

---

## Setup de Execução (Avaliação)

Para rodar a solução na sua máquina:
1. Tenha o [Docker Desktop](https://www.docker.com/products/docker-desktop) instalado.
2. Na raiz da pasta `solution/`, execute no terminal:
   ```bash
   docker-compose up --build -d
   ```
3. Acesse **`http://localhost:3000`** no seu navegador para visualizar o CommandCenter com os dados do vendedor "Darcel Schlecht" (o dashboard é dinâmico!).

---
_Submissão finalizada para o Processo Seletivo._
