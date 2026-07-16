# Submissão · Artur Rocha · Challenge 001

## Sobre mim

- **Nome:** Artur Rocha
- **LinkedIn:** [linkedin.com/in/arturroocha](https://www.linkedin.com/in/arturroocha/)
- **Challenge escolhido:** 001 · Diagnóstico de Churn (RavenStack)

---

## Executive Summary

O CEO perguntou "o que está causando o churn?" e eu respondi a pergunta que ele precisava ouvir: essa causa não está nos dados que a RavenStack coleta, e eu provo isso com estatística (nenhum modelo prevê churn melhor que o acaso, AUC 0,50, confirmado por verificação adversarial independente). O paradoxo dele se resolve porque o CS e o Produto olham métricas cegas: satisfação de quem cancela e de quem fica é idêntica, e o uso está estagnado, não crescendo. A pesquisa de mercado explica o porquê: as causas dominantes de churn neste tipo de produto são humanas (saída do champion, valor não realizado, decisão de construir interno com IA) e invisíveis para a telemetria. Minha recomendação central: consertar o rastreamento de churn (as duas fontes internas se contradizem), montar cobertura de sinal humano (health score relacional, mapa de champion, entrevistas de saída reais, CS "anjo" escalonado por valor) e concentrar retenção nas 100 contas que valem 67% do MRR, medindo tudo com indicadores antecedentes e grupo de controle.

---

## Solução

**Entregável principal: [`solution/report.html`](solution/report.html)** (relatório executivo auto-contido, abre em qualquer navegador). Ferramenta que acompanha: watchlist de contas priorizadas por receita em risco (`solution/outputs/watchlist_full.csv`).

### Como rodar (reproduzir cada número)

```bash
pip install -r requirements.txt          # Python 3.10+
# baixe o dataset do Kaggle (5 CSVs) para a pasta data/:
# https://www.kaggle.com/datasets/rivalytics/saas-subscription-and-churn-analytics-dataset
for s in solution/scripts/0*.py solution/scripts/10*.py; do python3 "$s"; done
```

Os scripts usam caminhos relativos e rodam em qualquer máquina. A ordem numérica dos arquivos (01 a 10) é a ordem real do trabalho.

### Abordagem

1. Testei as 3 afirmações do CEO contra os números antes de aceitar o enunciado (uma caiu, uma é verdadeira, uma é verdadeira e é o próprio problema)
2. Cruzei as 5 tabelas em nível de conta e passei todo sinal por teste de significância (qui-quadrado, Mann-Whitney)
3. Medi se churn é sequer previsível: modelos com validação cruzada sob 2 rótulos de churn
4. Um subagente de IA independente tentou refutar o achado central de forma adversarial (Bonferroni, permutação, análise de poder) e não conseguiu
5. Li a voz do cliente (texto livre dos eventos de churn) e ela desmascarou os reason codes registrados
6. Pesquisei no mercado as causas prováveis de churn para este tipo de produto, com fontes, e cruzei com o ICP da base
7. Pesei tudo por receita, não por contagem de contas

### Resultados / Findings

- **Churn é imprevisível nos dados atuais**: AUC 0,47 a 0,55 em 7 modelos sob 2 rótulos; o melhor preditor individual evapora sob Bonferroni (p=1,0) e permutação (p=0,94), e a análise de poder mostra que qualquer sinal útil (AUC ≥ 0,59) teria sido detectado. Tudo reproduzível em `scripts/09_adversarial_verification.py`
- **As métricas do painel executivo são cegas**: satisfação 3,98 (churned) vs 3,96 (retained); uso estagnado em ~10,5k eventos/mês por 2 anos
- **O rastreamento interno está quebrado**: as duas fontes de churn concordam em só 75 contas (110 vs 352); a tabela de assinaturas nunca encerra registros; os motivos registrados não batem com o que o cliente escreveu ao sair
- **1 em 5 churns veio logo após upgrade** (gap de expansão, fenômeno documentado no mercado)
- **A receita está concentrada**: top 20% das contas = 67% do MRR (43% pelo método alternativo; concentrada sob qualquer um)
- **O ICP DevTools é o mais exposto**: 31% de churn, menor ticket médio, e é o segmento mais capaz de reconstruir a ferramenta internamente com IA (build vs buy, tendência documentada: 35% das empresas já substituíram um SaaS por ferramenta interna)

### Recomendações (priorizadas)

1. Consertar o rastreamento de churn e trocar reason codes por entrevistas de saída reais (base de tudo)
2. Cobrir o sinal humano nº 1: health score relacional + mapa de champion (champion sai = 51% de churn; agir em 48h = +33% de renovação)
3. Encurtar o tempo até o valor no onboarding (70% do churn acontece nos primeiros 90 dias)
4. CS "anjo" com NPS proativo, escalonado por valor (alto toque nas 100 contas que valem 67% do MRR; automação na cauda longa), com cenários de retorno em dólares e premissas declaradas (`scripts/10_mrr_robustness_e_cenarios.py`)
5. Conversa estratégica de build vs buy com o segmento DevTools/EUA
6. Aposentar as métricas de vaidade do painel

Cada recomendação tem dono, esforço e a forma de medir se funcionou (indicadores antecedentes + grupo de controle), detalhado no relatório, seção 7.

### Limitações

- O dado é sintético (declarado pela documentação do dataset): sustento o achado estrutural, leio magnitudes como ilustrativas
- Não tenho o porquê real do churn, e esse é o ponto: ele não está nos dados; as recomendações constroem a capacidade de descobri-lo
- Os valores de MRR dependem de uma escolha de método (declarada no relatório) porque a tabela de assinaturas nunca fecha registros; os achados relativos resistem sob os dois métodos
- Build vs buy, NPS e anjos entram como apostas informadas com desenho de experimento, não como conclusões provadas por esta base

---

## Process Log · Como usei IA

> Narrativa completa, com erros e correções: [`process-log/PROCESS-LOG.md`](process-log/PROCESS-LOG.md)

### Ferramentas usadas

| Ferramenta | Para que usei |
|---|---|
| Claude Code (Opus 4.8 / Fable 5) | Orquestrador: análise Python, subagentes, relatório, revisões |
| 4 subagentes | 2 exploradores do repositório, 1 cético adversarial, 1 pesquisador de mercado |
| Python (pandas, scikit-learn, scipy, matplotlib) | Análise reproduzível (10 scripts em `solution/scripts/`) |

### Workflow (resumo)

1. Dois subagentes leram o repositório do desafio em paralelo antes de qualquer execução
2. Análise em 8 scripts na ordem real do trabalho (explorar → causa raiz → stress-test preditivo → receita/watchlist → gráficos → relatório → voz do cliente → ICP)
3. Subagente cético tentou refutar o achado central e não conseguiu (fortaleceu com Bonferroni, permutação e análise de poder)
4. Pesquisa de mercado com fontes, redirecionada no meio do voo para incluir a hipótese build vs buy
5. Revisão adversarial final contra o próprio trabalho antes da entrega

### Onde a IA errou e como corrigi

- A IA tunelou em números e ia entregar um relatório estatisticamente correto e estrategicamente vazio. Eu trouxe o fator humano (churn se reduz com mecânica humana), a hipótese build vs buy e a exigência de condicioná-la ao ICP
- Join inicial inflou a tabela mestre (748 linhas para 500 contas); pego por validação de contagem e corrigido com assert
- Linguagem com cara de IA (travessões, voz impessoal); exigi primeira pessoa e zero travessão, com assert no script que falha se travessão voltar
- A revisão final pegou: método de MRR não declarado, churn sem base temporal (22% em 2 anos ≈ 12% ao ano), e verificou que o pico final de churn não é artefato do recorte dos dados

### O que eu adicionei que a IA sozinha não faria

A tese. A IA achou o vazio (AUC 0,50) e eu dei o significado dele: se o porquê não está na telemetria, ele é humano, e a solução é cobertura de sinal humano, não um modelo melhor. Mais: a hipótese build vs buy que eu conheço por viver esse mercado, o desenho do CS anjo escalonado por custo, e o padrão de comunicação honesta (limitações explícitas, sem causa-raiz inventada).

---

## Evidências

- [x] Narrativa escrita passo a passo (`process-log/PROCESS-LOG.md`)
- [x] Git history com a evolução do trabalho
- [x] Scripts comentados e reproduzíveis (`solution/scripts/01` a `10`, a ordem dos arquivos é a ordem real; caminhos relativos + `requirements.txt`)
- [x] Saídas intermediárias (`solution/outputs/`)

---

_Submissão enviada em: [DATA DO PR]_
