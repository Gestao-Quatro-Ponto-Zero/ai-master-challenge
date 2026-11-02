# Challenge 002 — Redesign de Suporte

**Estado: preparação do projeto. A solução ainda não foi implementada.**

## Sobre mim

- Nome: a confirmar para a entrega final.
- LinkedIn: a preencher.
- Challenge escolhido: 002 — Redesign de Suporte.

## Executive Summary

O projeto irá diagnosticar gargalos de suporte, propor uma automação com limites
claros de intervenção humana e demonstrá-la em um protótipo. Nesta etapa foram
preparados o contexto compartilhado, o plano de execução e o registro do processo.
Os datasets ainda serão auditados; resultados, impacto e arquitetura permanecem
em aberto.

## Solução

### Abordagem

Auditar os dados antes de definir seu uso conjunto, reproduzir o diagnóstico e
selecionar uma automação com base nas evidências. O contexto técnico usa uma base
mínima em OKF v0.2, consultada de forma seletiva pelas ferramentas de IA.

### Resultados / Findings

Ainda não há resultados analíticos ou métricas de desempenho.

### Recomendações

Serão formuladas e priorizadas após a análise dos dados.

### Limitações

Os volumes, unidades e características anunciados no briefing ainda não foram
verificados nos arquivos. A estratégia de uso dos dois datasets será definida
na próxima etapa.

## Process Log — Como usei IA

O [process log](process-log/README.md) reúne a narrativa e as mensagens acessíveis
dos chats de preparação, comparação dos desafios e desenvolvimento desta base.
As mensagens arquivadas preservam opiniões anteriores, inclusive recomendações
de desafio que foram superadas pela decisão de escolher o 002.

## Navegação

- [Estado do projeto](PROJECT_STATUS.md)
- [Plano com critérios de aceite](execution/plan.md)
- [Conhecimento compartilhado](knowledge/index.md)
- [Estratégia de validação](docs/validation-strategy.md)
- [Checagens de consistência e validade das evidências](docs/foundation-controls.md)
- [Fonte de verdade dos sete ajustes da revisão](docs/architecture-review.md#lista-oficial-para-validação)
- [Backlog](execution/backlog.md)

As instruções para executar a aplicação, os resultados dos testes e o CodeTour
serão incluídos quando esses artefatos existirem.

## Como iniciar uma sessão de trabalho

A partir da raiz do repositório, entre na pasta da submissão:

```bash
cd submissions/giovanne-berteli-comba
```

Leia `AGENTS.md`, `PROJECT_STATUS.md`, `execution/plan.md` e `knowledge/index.md`;
depois consulte somente os documentos necessários à tarefa. Se a ferramenta
permanecer na raiz, indique explicitamente a leitura de
`submissions/giovanne-berteli-comba/AGENTS.md`. A busca padrão na raiz pode omitir
esta pasta por causa do `.gitignore`.

Para verificar a base e os hashes de suas entradas, execute na pasta da submissão:

```bash
python3 -I -m unittest discover -s tests -v
python3 -I scripts/check_foundation.py
```

Esses comandos validam a fundação; a aplicação e os dados ainda serão implementados
e auditados. Consulte o escopo e o procedimento de revalidação no link acima.

O process log e os exports de chats são evidências para a equipe de recrutamento.
As regras de trabalho os excluem do contexto padrão das sessões, inclusive na
retomada. As decisões atuais devem estar nos documentos operacionais indicados.
