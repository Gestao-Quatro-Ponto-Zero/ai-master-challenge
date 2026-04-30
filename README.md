# AI Master Challenge

**O teste para quem vai transformar áreas inteiras usando IA.**

O G4 está construindo um novo tipo de profissional: o **AI Master** — capaz de entrar em qualquer área e usar IA generativa para resolver problemas reais de forma transformacional.

---

## Descrição

Repositório do processo seletivo para AI Master no G4 Educação. Os desafios cobrem quatro áreas de negócio (dados, operações, vendas e marketing) e avaliam como candidatos usam IA como ferramenta estratégica — não apenas para executar, mas para pensar, diagnosticar e entregar soluções funcionais.

A submissão é feita via Pull Request e o processo de uso de IA precisa ser documentado. Entregar algo parecido com o output direto de um modelo não é suficiente — o baseline já foi gerado internamente com múltiplos modelos.

---

## Tech Stack

Os challenges não impõem tecnologia. Ferramentas comuns por challenge:

| Challenge | Ferramentas prováveis |
|-----------|----------------------|
| 001 — Churn | Python/R, Jupyter, Pandas, visualização |
| 002 — Suporte | Python, NLP/LLMs, frameworks web |
| 003 — Lead Scorer | Qualquer stack funcional (React, Streamlit, etc.) |
| 004 — Social Media | Python/R, notebooks, visualização |

A submissão de referência (`submissions/luis-braghin`) usa:

| Tecnologia | Uso |
|-----------|-----|
| React 18 + TypeScript | Framework UI |
| Vite 5 | Build tool |
| Tailwind CSS 3 + shadcn/ui | Design system |
| Recharts | Gráficos (bar, pie, scatter, line) |
| TanStack Query | Gerenciamento de estado/dados |
| React Router 6 | Roteamento |
| Lucide React | Ícones |
| Vitest + Playwright | Testes |

---

## Como instalar e rodar

Este repositório é o ponto de entrada para candidatos. Não há aplicação central — cada submissão tem seu próprio setup.

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

# 5. Desenvolva sua solução e documente o process log
# 6. Commit e push
git push origin submission/seu-nome

# 7. Abra um Pull Request para main com título:
# [Submission] Seu Nome — Challenge XXX
```

**Requisitos:** Git, conta no GitHub, e qualquer runtime exigido pela sua solução.

### Rodar a solução de referência (Challenge 003)

**Opção 1 — Deploy:**
Acesse [g4-lead-scorer.vercel.app](https://g4-lead-scorer.vercel.app/)

**Opção 2 — Local:**
```bash
cd submissions/luis-braghin/solution
npm install
npm run dev
# Abrir http://localhost:8080
```

**Requisitos:** Node.js 18+

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

## Principais funcionalidades

- **4 challenges independentes** cobrindo dados, operações, vendas e marketing
- **Submissão via Pull Request** com estrutura padronizada
- **Process log obrigatório** — documenta como a IA foi usada (sem ele, a submissão é desclassificada)
- **Template de submissão** com seções obrigatórias (executive summary, abordagem, resultados, limitações)
- **Solução de referência** (Challenge 003) — dashboard interativo G4 Deal Intelligence com scoring multidimensional de 2.089 deals, 6 visões (vendedor, manager, executivo, analytics, deal detail, premissas) e deploy funcional

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
│   └── submission-template.md       ← Template obrigatório para o README da submissão
├── CONTRIBUTING.md                  ← Instruções de submissão via PR
├── submission-guide.md              ← O que incluir e como estruturar
└── README.md
```

---

## O que é avaliado

- Entendimento do problema antes de executar
- Uso inteligente de IA (não copy-paste)
- Solução que resolve o problema de verdade
- Documentação do processo de uso de IA (obrigatória — sem ela a submissão é desclassificada)

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
