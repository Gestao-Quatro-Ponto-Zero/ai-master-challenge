# AI Master Challenge

**O teste para quem vai transformar áreas inteiras usando IA.**

O G4 está construindo um novo tipo de profissional: o **AI Master** — capaz de entrar em qualquer área e usar IA generativa para resolver problemas reais de forma transformacional.

---

## Descrição

Este repositório contém os desafios do processo seletivo para AI Master no G4 Educação. Os desafios cobrem quatro áreas de negócio (dados, operações, vendas e marketing) e avaliam como candidatos usam IA como ferramenta estratégica — não apenas para executar, mas para pensar, diagnosticar e entregar soluções funcionais.

A submissão é feita via Pull Request, e o processo de uso de IA precisa ser documentado. Entregar algo parecido com o output direto de um modelo não é suficiente — o baseline já foi gerado internamente com múltiplos modelos.

---

## Tech Stack

Os challenges não impõem tecnologia. Exemplos aceitos por challenge:

| Challenge | Ferramentas prováveis |
|-----------|----------------------|
| 001 — Churn | Python/R, Jupyter, Pandas, visualização |
| 002 — Suporte | Python, NLP/LLMs, frameworks web |
| 003 — Lead Scorer | Qualquer stack funcional (React, Streamlit, etc.) |
| 004 — Social Media | Python/R, notebooks, visualização |

---

## Como instalar e rodar

Este repositório é o ponto de entrada para candidatos. Não há aplicação central a instalar — cada submissão tem seu próprio setup.

### Para participar

```bash
# 1. Fork este repositório
# 2. Clone o fork
git clone https://github.com/SEU-USUARIO/ai-master-challenge.git
cd ai-master-challenge

# 3. Crie sua branch
git checkout -b submission/seu-nome

# 4. Crie sua pasta de submissão
mkdir -p submissions/seu-nome

# 5. Desenvolva sua solução e adicione ao process log
# 6. Commit e push
git push origin submission/seu-nome

# 7. Abra um Pull Request para main com título:
# [Submission] Seu Nome — Challenge XXX
```

**Requisitos:** Git, conta no GitHub, e qualquer runtime exigido pela sua solução.

---

## Desafios disponíveis

| # | Desafio | Área | O que entregar |
|---|---------|------|---------------|
| [001](./challenges/data-001-churn/) | Diagnóstico de Churn | Dados / Analytics | Análise de causa-raiz + recomendações acionáveis |
| [002](./challenges/process-002-support/) | Redesign de Suporte | Operações / CX | Diagnóstico de 30K tickets + protótipo de automação |
| [003](./challenges/build-003-lead-scorer/) | Lead Scorer | Vendas / RevOps | Ferramenta funcional de priorização de pipeline |
| [004](./challenges/marketing-004-social/) | Estratégia Social Media | Marketing | Análise de 52K posts + estratégia baseada em dados |

**Time budget recomendado:** 4–6 horas por challenge.

---

## O que é avaliado

- Entendimento do problema antes de executar
- Uso inteligente de IA (não copy-paste)
- Solução que resolve o problema de verdade
- Documentação do processo de uso de IA (obrigatória — sem ela a submissão é desclassificada)

---

## Estrutura do repositório

```
ai-master-challenge/
├── challenges/
│   ├── README.md                    ← Índice e guia de escolha
│   ├── data-001-churn/              ← Challenge 001: Diagnóstico de Churn
│   ├── process-002-support/         ← Challenge 002: Redesign de Suporte
│   ├── build-003-lead-scorer/       ← Challenge 003: Lead Scorer
│   └── marketing-004-social/        ← Challenge 004: Estratégia Social Media
├── submissions/
│   └── <nome-candidato>/
│       ├── README.md                ← Resumo executivo + process log
│       ├── solution/                ← Solução (análise, código, protótipo)
│       ├── process-log/             ← Evidências de uso de IA
│       └── docs/                    ← Documentação adicional
├── templates/
│   └── submission-template.md       ← Template obrigatório para README da submissão
├── CONTRIBUTING.md                  ← Instruções de submissão via PR
├── submission-guide.md              ← O que incluir e como estruturar
└── README.md
```

---

## Submissão

- Leia o [Guia de Submissão](./submission-guide.md)
- Use o [template de submissão](./templates/submission-template.md)
- Siga as regras em [CONTRIBUTING.md](./CONTRIBUTING.md)
- Só modifique arquivos dentro de `submissions/seu-nome/`

---

## Sobre o G4

O [G4](https://g4educacao.com) é a maior plataforma de educação executiva do Brasil. Este processo seletivo busca profissionais que usem IA para transformar áreas inteiras de negócio — não apenas para automatizar tarefas pontuais.

*Dúvidas? Abra uma [issue](../../issues).*
