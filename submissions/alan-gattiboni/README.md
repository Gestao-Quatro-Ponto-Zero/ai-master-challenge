# Submissão — Alan Gattiboni — Challenge 002

## Sobre mim

- **Nome:** Alan Gattiboni
- **LinkedIn:** www.linkedin.com/in/alangattiboni
- **Challenge escolhido:** 002 — Redesign de Suporte (Operações / CX)

---

## Executive Summary

_A preencher ao final — 3-5 frases: o que encontrei, o que construí, e a
principal recomendação._

---

## Solução

### Abordagem

_A preencher._

### Resultados / Findings

_A preencher._

### Recomendações

_A preencher._

### Limitações

_A preencher._

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

_A ser preenchido conforme o pipeline é construído (Blocos 1+). Cada etapa
documenta aqui seu próprio comando de reprodução._

---

## Process Log — Como usei IA

> **Bloco obrigatório.** Sem ele, a submissão é desclassificada.

### Ferramentas usadas

| Ferramenta    | Para que usei |
| ------------- | ------------- |
| _a preencher_ | _a preencher_ |

### Workflow

_A preencher._

### Onde a IA errou e como corrigi

_A preencher._

### O que eu adicionei que a IA sozinha não faria

_A preencher._

---

## Evidências

- [ ] Screenshots das conversas com IA
- [ ] Chat exports
- [ ] Git history

---

_Submissão enviada em: [data]_
