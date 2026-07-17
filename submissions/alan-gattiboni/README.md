# Submissão — Alan Gattiboni — Challenge 002

## Sobre mim

- **Nome:** Alan Gattiboni
- **LinkedIn:** www.linkedin.com/in/alangattiboni
- **Challenge escolhido:** 002 — Redesign de Suporte (Operações / CX)

---

## Executive Summary

As duas fontes de tickets fornecidas ocupam posições opostas de qualidade: uma é
sintética e não instrumenta a operação, a outra é real e classificável. Auditei
as duas, diagnostiquei onde a operação concentra esforço e desperdício, propus
uma arquitetura de automação de triagem e a implementei num protótipo que atinge
F1-macro 0,856 em dado que o modelo nunca viu, com uma camada que desvia o ticket
incerto para revisão humana. A recomendação central é automatizar a triagem por
classificação onde há sinal e instrumentar a captura de dados antes de automatizar
qualquer decisão de desfecho no atendimento ao cliente.

**Vitrine visual:** [`pipeline_inspector.html`](pipeline_inspector.html) reúne o registro cru auditado, os gates de qualidade e o classificador com abstenção, com dados reais extraídos das fontes. Baixe o arquivo e abra no navegador para a versão renderizada.

---

## Solução

### Abordagem

Tratei o desafio como um problema de produto de dados. Antes de propor automação,
auditei a qualidade das fontes, qualifiquei o que tem sinal recuperável e rejeitei
formalmente o que não tem. A solução avança em quatro atos: auditoria adversarial
das fontes, diagnóstico operacional, proposta de automação e protótipo funcional
medido. Cada ato é um artefato inspecionável, e cada decisão se apoia num achado
computado.

### Resultados / Findings

**Auditoria das fontes.** As duas fontes ocupam posições opostas de qualidade. O
D1 (`customer_support_tickets`, 8.469 tickets reais, contra os ~30K do enunciado
que conta linhas físicas) tem descrição 100% sintética, com placeholder de
template cru, e metadados categóricos de distribuição uniforme (entropia
normalizada acima de 0,999), sem sinal de negócio. O D2 (`all_tickets`, 47.837
tickets de TI interno) é real, com sinal discriminativo no texto. As duas fontes
não compartilham chave nem taxonomia, e forçar cruzamento seria invenção.

**Diagnóstico operacional.** A demanda do D2 concentra em três categorias, top-3
em 66,18%. O `Miscellaneous` reúne 14,76% dos tickets num balde difuso que custa
cerca de 353 horas de re-roteamento manual. O D1 não instrumenta a operação: os
atributos não explicam os desfechos (eta-quadrado máximo 0,00210) e os carimbos
de tempo não medem duração, com resolução antes da primeira resposta em 49,3% dos
casos.

**Protótipo.** Um classificador TF-IDF mais linear atinge F1-macro 0,856 no
holdout, contra 0,055 de um baseline de classe majoritária. A camada de abstenção
no limiar 0,5 automatiza 76,7% dos tickets a F1-macro 0,931 e desvia o restante
para revisão humana. O que a revisão herda é o `Hardware` ambíguo, a maior classe
e o sorvedouro de confusão do modelo. O `Miscellaneous`, categoria difusa no
vocabulário, é classificado com F1 0,829, o que separa vocabulário difuso de
dificuldade de classificação.

### Recomendações

**Automatizar a triagem por classificação.** Onde há sinal, o classificador
roteia o ticket para a fila certa e ataca as 353 horas de re-roteamento manual. A
camada de abstenção desvia o ticket difuso ou incerto para revisão humana, uma
automação que reconhece o próprio limite.

**Instrumentar a captura antes de automatizar desfecho no cliente.** O D1 prova
que priorização e previsão de satisfação não têm sinal para treinar. Capturar
timestamps reais e campos com semântica de negócio é o passo anterior a qualquer
automação de decisão no atendimento ao cliente.

**Manter a arquitetura agnóstica de fonte.** O pipeline recebe qualquer operação
de tickets pela mesma porta de ingestão, o que permite plugar uma fonte nova sem
reescrever o fluxo.

### Limitações

- O D1 é sintético. Não sustenta treino nem diagnóstico de operação real de
  cliente. A submissão prova esse estado e usa o D2 para o que roda.
- A hipótese inicial de que a abstenção capturaria o `Miscellaneous` não se
  confirmou. A medição mostrou o `Hardware` liderando o desvio, e o resultado foi
  assumido como veio.
- As duas fontes não são cruzáveis. Não forcei relação entre domínios distintos.
- O classificador é TF-IDF mais linear, simples por decisão de escopo. Um
  transformer seria infra que o desafio não pede.
- A IA generativa aparece na proposta de fluxo, na extração de intenção do texto
  livre, como desenho sem implementação no protótipo.

---

## Reprodução

### Pré-requisitos

- Python 3.12.4
- Dependências congeladas em `solution/requirements.txt`

### Setup

```bash
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Linux / macOS
source .venv/bin/activate

pip install -r solution/requirements.txt
```

### Dados

Os datasets **não** estão versionados neste repositório — a pasta `datasets/` é
git-ignored por regra do próprio challenge. Baixe os dois arquivos manualmente e
coloque-os, com os nomes exatos abaixo, em `solution/datasets/`:

| # | Arquivo                                 | Fonte (Kaggle)                                                                       |
| - | --------------------------------------- | ------------------------------------------------------------------------------------ |
| 1 | `customer_support_tickets.csv`          | `https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset`           |
| 2 | `all_tickets_processed_improved_v3.csv` | `https://www.kaggle.com/datasets/adisongoh/it-service-ticket-classification-dataset` |

> Sanity check pós-download: `df.shape` deve dar **8.469** linhas (Dataset 1) e
> **47.837** linhas (Dataset 2). Se o Dataset 1 vier com ~29.808 linhas, você
> abriu o CSV contando linhas físicas — descrições multi-linha inflam a
> contagem; o número de tickets reais é 8.469.

### Como executar

Os notebooks são autossuficientes e rodam do zero, cada um recarrega os dados por
conta própria. Ordem de leitura e execução:

```bash
jupyter lab
```

1. `solution/01_eda_adversarial.ipynb` — auditoria adversarial das fontes
2. `solution/02_diagnostico_operacional.ipynb` — diagnóstico operacional
3. `solution/03_proposta_automacao.md` — proposta de automação (documento com o
   fluxo, não executável)
4. `solution/04_prototipo_classificador.ipynb` — protótipo do classificador com
   abstenção

---

## Process Log — Como usei IA

> **Bloco obrigatório.** Sem ele, a submissão é desclassificada.

### Ferramentas usadas

| Ferramenta | Para que usei |
| ---------- | ------------- |
| Claude Opus | Arquitetura da solução, validação adversarial dos retornos de código, redação dos artefatos |
| Agente de código (VS Code) | Implementação e execução dos notebooks e do classificador |
| Perplexity Pro | Triangulação com evidência de mercado para furar o viés de confirmação da dupla |

### Workflow

Arquiteto e arquiengenheiro desenham cada bloco, o agente de código implementa e
reporta, e o retorno é validado contra os dados brutos antes de qualquer commit.
Cada bloco tem um dev-log em `process-log/dev-log/` que registra a thread de
instrução, execução e correção. As decisões e o plano vivem versionados em
`docs/PLAN.md`, e cada bloco fecha num commit próprio.

### Onde a IA errou e como corrigi

- A contagem de ~30K tickets do enunciado veio de linhas físicas. A auditoria
  provou 8.469 tickets reais e documentou a divergência.
- A hipótese de que a abstenção capturaria o `Miscellaneous` foi levantada na
  proposta e refutada pela medição no protótipo, onde o `Hardware` lidera o
  desvio. Assumi a releitura.
- O agente de código reportou a matriz de confusão invertendo linha e coluna. A
  revalidação contra o holdout pegou o deslize, e o notebook trata a direção
  correta.
- O agente reincidiu numa construção de escrita banida do projeto. A revisão
  corrigiu antes do commit.

### O que eu adicionei que a IA sozinha não faria

- A decisão de tratar a submissão como produto de dados auditável, no molde da
  minha Central de Dados RH.
- A postura de rejeitar formalmente o dado sintético com prova documentada, em
  vez de maquiar um diagnóstico sobre ele.
- O uso do Perplexity como quarto membro para furar o viés de confirmação da
  dupla.
- As decisões de escopo: o que manter humano, e o modelo simples por escolha
  consciente contra over-engineering.
- O ceticismo que revalidou cada número contra os CSVs e pegou os erros da IA
  antes de cada commit.

---

## Evidências

- [x] Dev-logs por bloco em `process-log/dev-log/` (thread instrução, execução, correção)
- [x] Git history: um commit por bloco, mensagens versionadas
- [x] Vitrine de inspeção: [`pipeline_inspector.html`](pipeline_inspector.html) (baixar e abrir no navegador)
- [ ] Screenshots das conversas com IA

---

_Submissão enviada em: [data]_