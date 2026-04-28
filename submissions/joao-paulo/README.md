# Submissão — João Paulo — Challenge 001

## Sobre mim

- **Nome:** João Paulo
- **LinkedIn:** [João Paulo Borges](https://www.linkedin.com/in/joao-pauloborges)
- **Challenge escolhido:** Challenge 001 — Diagnóstico de Churn

---

## Executive Summary

Desenvolvi uma solução end-to-end para diagnóstico de churn em um contexto SaaS, combinando consolidação analítica, modelagem preditiva e uma camada executiva de visualização para priorização de retenção. A entrega integra múltiplas tabelas do dataset RavenStack para transformar eventos de uso, suporte, assinaturas e churn em uma visão única por conta. O principal resultado é uma priorização objetiva das contas com maior risco e maior impacto financeiro, permitindo identificar rapidamente onde agir e quanto de receita está exposto. A recomendação central é estruturar a operação de retenção em torno de sinais precoces de queda de uso, deterioração de suporte e concentração de MRR em contas críticas.

---

## Solução

### Abordagem

A solução foi organizada em quatro etapas principais:

1. **Leitura e validação dos dados**  
   Carregamento das tabelas do dataset e aplicação de verificações de consistência para garantir integridade mínima da base analítica.

2. **Construção da visão analítica por conta**  
   Consolidação dos sinais de negócio, produto e suporte em uma tabela central (`account_360`), usada como base para análise executiva e modelagem.

3. **Modelagem de risco de churn**  
   Treinamento de um modelo supervisionado para estimar probabilidade de churn por conta, complementado por métricas de performance e geração de drivers explicativos.

4. **Tradução executiva dos resultados**  
   Geração de outputs analíticos e de um dashboard HTML voltado à tomada de decisão, com foco em MRR em risco, fila de retenção e principais drivers do portfólio.

---

### Resultados / Findings

A solução gera os seguintes artefatos principais:

- **`account_360.csv`**: visão consolidada por conta
- **`churn_risk_drivers.csv`**: fatores explicativos de risco
- **`model_metrics.json`**: métricas do modelo
- **Dashboard executivo em HTML**: visão de priorização e narrativa de negócio

Principais achados do projeto:

- O churn não se distribui de forma homogênea no portfólio; ele se concentra em grupos com sinais operacionais claros.
- Queda de uso e piora em indicadores de suporte aparecem como sinais relevantes de deterioração.
- O risco precisa ser priorizado junto com impacto financeiro; nem toda conta de alto risco tem o mesmo peso para a operação.
- Uma camada executiva de visualização melhora muito a capacidade de transformar score em ação.

---

## Análise do desempenho do modelo

O modelo treinado apresentou métricas próximas de aleatoriedade (ROC AUC ~ 0.5), o que indica baixa capacidade preditiva no dataset utilizado.

Essa observação foi analisada considerando os seguintes fatores:

### 1. Natureza do dataset

O dataset RavenStack é sintético e não foi gerado com foco explícito em separabilidade entre classes de churn. Isso significa que:

- muitas variáveis possuem baixo poder discriminatório
- relações entre comportamento e churn não são fortemente estruturadas

### 2. Sinal limitado nas features

Apesar da engenharia de features, os sinais disponíveis (uso, suporte, receita) não apresentaram separação clara entre churn e não churn.

Isso sugere que:
- ou o churn é pouco explicável com essas variáveis
- ou o dataset não contém padrões fortes suficientes

### 3. Objetivo da solução

O foco principal desta submissão não foi maximizar performance preditiva, mas sim:

- estruturar corretamente o problema de churn
- construir uma base analítica consistente (account_360)
- traduzir sinais em uma narrativa executiva acionável

### 4. Valor da abordagem mesmo com baixa AUC

Mesmo com baixa performance do modelo, a solução gera valor ao:

- identificar drivers operacionais relevantes
- estruturar priorização de contas baseada em múltiplos sinais
- fornecer visibilidade executiva do risco

### 5. Próximos passos sugeridos

Para melhoria do modelo em um cenário real:

- inclusão de mais dados comportamentais
- criação de features temporais mais ricas
- análise de balanceamento e qualidade do target

Em resumo, a baixa performance do modelo não invalida a solução, mas reforça a importância de interpretar churn como um problema multifatorial, e não puramente preditivo. 

obs: Foram realizados testes com variações de modelos, sem ganho significativo de performance, reforçando a hipótese de baixo poder preditivo do dataset.

---

### Recomendações

1. **Criar uma fila de retenção priorizada por risco e impacto financeiro**  
   O time deve atuar primeiro nas contas com combinação de alta probabilidade de churn e maior MRR exposto.

2. **Monitorar sinais precoces de deterioração operacional**  
   Redução de uso, aumento de fricção em suporte e movimentos comerciais recentes devem ser acompanhados continuamente.

3. **Transformar análise em rotina de gestão**  
   O dashboard não deve ser apenas um deliverable estático; ele deve servir como instrumento recorrente de acompanhamento executivo.

4. **Evoluir a explicabilidade da operação de retenção**  
   Mais do que prever churn, a empresa deve estruturar quais alavancas operacionais reduzem o risco observado.

---

### Limitações

- O dataset utilizado é sintético, embora estruturado de forma realista.
- Algumas relações causais observadas devem ser interpretadas como sinais correlacionais dentro do escopo disponível.
- O modelo foi desenvolvido para fins analíticos e demonstrativos, não como sistema de produção com monitoramento contínuo.
- A explicabilidade depende da qualidade e granularidade das variáveis disponíveis nas tabelas de origem.

---

## Como rodar o projeto

### Requisitos

- Python 3.10 ou superior

### Instalação

```bash
cd solution
python -m venv .venv
```

Ativar ambiente:

**Windows (PowerShell):**
```bash
.\.venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```bash
.\.venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

Instale o projeto:

```bash
pip install -e .
```

### Execução

Rode o pipeline principal:

```bash
python main.py
```

### Testes

Para executar os testes:

```bash
pytest
```

### Outputs esperados

Após a execução, os principais arquivos gerados ficam na pasta `output/`, incluindo:

- `account_360.csv`
- `churn_risk_drivers.csv`
- `model_metrics.json`
- dashboard HTML executivo

---

## Estrutura da solução

```text
solution/
├── main.py
├── pyproject.toml
├── README.md
├── data/
├── output/
├── src/
└── tests/
```

---

## Créditos do dataset

Este projeto utiliza o dataset sintético **RavenStack**, com crédito ao autor original **River @ Rivalytics**. Conforme a documentação do dataset, ele pode ser utilizado para fins educacionais e de portfólio com a devida atribuição ao autor.

---

## Process Log — Como usei IA

> O detalhamento completo das evidências está na pasta `process-log/`.

### Ferramentas usadas

| Ferramenta | Para que usei |
|------------|---------------|
| ChatGPT | Estruturação da solução, revisão crítica da narrativa e refinamento do dashboard executivo |
| Codex / assistente de código | Ajustes de implementação, correções e refatorações pontuais |
| Python | Construção do pipeline, modelagem e geração dos outputs |

### Workflow

1. Compreensão do problema e definição da estratégia de entrega
2. Exploração do dataset e desenho da visão analítica por conta
3. Construção das features e modelagem de churn
4. Geração dos outputs analíticos
5. Iterações de melhoria no dashboard executivo
6. Revisão final da submissão com foco em clareza, reprodutibilidade e impacto

### Onde a IA errou e como corrigi

A IA foi útil para acelerar estrutura, escrita e iteração técnica, mas algumas sugestões precisaram ser ajustadas após validação manual. Em especial, houve necessidade de revisar decisões de narrativa, consistência entre outputs e clareza executiva do dashboard. Também refinei componentes do código e do texto para garantir alinhamento com os objetivos reais da submissão.

### O que eu adicionei que a IA sozinha não faria

A principal contribuição autoral foi a transformação da análise em uma narrativa executiva orientada à decisão, priorizando impacto financeiro, legibilidade para liderança e clareza na ação recomendada. Também houve julgamento humano na seleção do que manter, do que remover e de como traduzir sinais analíticos em uma entrega mais forte para banca avaliadora.

---

## Evidências

As evidências de uso de IA serão entregues na pasta `process-log/`, incluindo narrativa de workflow, iterações e materiais de apoio.

---

_Submissão enviada em: 17/04/2026_
