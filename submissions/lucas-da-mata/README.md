# Submissao - Lucas da Mata - Challenge 003

## Sobre mim

- **Nome:** Lucas Gabriel da Silva Mata
- **LinkedIn:** https://br.linkedin.com/in/olucasdamata
- **Challenge escolhido:** 003 - Lead Scorer

---

## Executive Summary

Construí o **Pipeline Focus Console**, uma aplicação web funcional para transformar o pipeline de 8.800 oportunidades do dataset em uma fila de foco comercial. A ferramenta prioriza apenas deals abertos, explica por que cada oportunidade recebeu aquele score, mostra riscos e sugere a próxima ação para o vendedor. A decisão principal foi otimizar para uso real de segunda-feira de manhã: o vendedor abre a tela e sabe qual deal atacar primeiro, por que ele importa e quando escalar para o manager.

App publicado: https://pipeline-focus-buddy.lovable.app/

Codigo fonte externo: https://github.com/olucasdamata/pipeline-focus

Codigo fonte incluido nesta submissao: [`solution/pipeline-focus-console/`](./solution/pipeline-focus-console/)

---

## Solucao

### Abordagem

Comecei pelo pedido da Head de Revenue Operations: a prioridade não era construir um modelo sofisticado, mas uma ferramenta que o vendedor realmente usasse. A partir disso, defini a primeira tela como uma fila priorizada, não como um notebook, landing page ou kanban genérico.

A aplicação carrega os quatro CSVs reais do desafio:

- `accounts.csv`
- `products.csv`
- `sales_teams.csv`
- `sales_pipeline.csv`

O `sales_pipeline.csv` é tratado como tabela central e conectado a contas, produtos e time comercial.

### Resultados / Findings

O console entrega:

- fila priorizada com 2.089 deals abertos;
- score de 0 a 100 por oportunidade;
- motivo do score em linguagem de vendedor;
- próxima melhor ação;
- fatores positivos e fatores de risco;
- confiança do score e limitações dos dados;
- filtros por vendedor, manager, região, stage, prioridade e produto;
- visão RevOps por manager;
- brief operacional de segunda-feira;
- export CSV e cópia da lista de ações.

### Recomendacoes

1. Usar o console como fila operacional diária para vendedores.
2. Usar a visão RevOps para managers acompanharem deals de alto score, risco de esfriamento e baixa confiança.
3. Evoluir o score com dados reais de atividade comercial, como última interação, próximo passo registrado, histórico de reunião e motivo de perda.

### Limitacoes

- A versão atual é rule-based, não um modelo preditivo treinado.
- Deals abertos sem `close_value` usam o preço de tabela do produto como valor estimado.
- O dataset não inclui última atividade real, próxima reunião, e-mails ou notas do vendedor.
- A confiança do score cai quando há join ausente, datas faltando ou fallback para média do time.

---

## Process Log - Como usei IA

O process log completo está em [`process-log/PROCESS_LOG.md`](./process-log/PROCESS_LOG.md).

### Ferramentas usadas

| Ferramenta | Para que usei |
| --- | --- |
| ChatGPT / Codex | Análise do desafio, decomposição do problema, implementação, QA e documentação |
| Lovable | Preview, refinamento visual e publicação da aplicação |
| GitHub | Versionamento, PRs e histórico de evolução |

### Workflow

1. Li o README do desafio e isolei o pedido real da Head de RevOps.
2. Escolhi uma fila operacional como primeira tela, porque o vendedor precisa decidir onde focar agora.
3. Modelei um score explicável com fatores ponderados.
4. Construí a aplicação web em React/TanStack Start.
5. Refinei a UI para parecer ferramenta real, não tela de teste.
6. Validei build, lint, comportamento de filtros, idioma, export e publicação.
7. Registrei as decisões e limitações para deixar a entrega auditável.

### Onde a IA errou e como corrigi

- A primeira versão tinha uma tela de upload que fazia o produto parecer uma demo técnica. Removi porque o cliente pediu uma ferramenta que o vendedor abre e usa.
- Algumas validações do browser confundiam cache/preview antigo com estado real. Passei a validar build local, commit GitHub e URL pública separadamente.
- A exportação e a cópia dependiam demais de permissões do navegador. Adicionei fallback visível: link de CSV pronto e textarea copiável.

### O que eu adicionei que a IA sozinha não faria

- A decisão de priorizar a necessidade da Head de RevOps acima de qualquer feature visual.
- O corte de produto: tabela priorizada primeiro, kanban fora do escopo.
- A camada de confiança/limitações para não vender score como verdade absoluta.
- O brief de segunda-feira e a visão RevOps, para demonstrar uso real por vendedor e manager.

---

## Evidencias

- [x] Git history no repo da solução
- [x] Aplicação publicada
- [x] Process log escrito
- [x] Setup e lógica documentados
- [x] Código fonte incluído em `solution/pipeline-focus-console/`
- [x] Screenshots finais anexados em `process-log/screenshots/`
- [x] QA final documentado em `docs/QA_REPORT_2026-06-29.md`
- [x] LinkedIn preenchido

---

Submissão preparada em: 2026-06-29
