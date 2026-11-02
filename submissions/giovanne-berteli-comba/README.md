# Challenge 002 — Redesign de Suporte

**Estado: datasets adquiridos e auditados (D01). Protótipo ainda não implementado.**

## Sobre mim

- Nome: a confirmar para a entrega final.
- LinkedIn: a preencher.
- Challenge escolhido: 002 — Redesign de Suporte.

## Executive Summary

O projeto irá diagnosticar gargalos de suporte, propor uma automação com limites
claros de intervenção humana e demonstrá-la em um protótipo. Os dois datasets
foram adquiridos, versionados e auditados. A auditoria identificou limitações de
tempo, cobertura e rótulos que orientarão a escolha da solução. O uso conjunto,
a arquitetura da aplicação e o impacto operacional ainda serão definidos.

## Solução

### Abordagem

Auditar os dados antes de definir seu uso conjunto, reproduzir o diagnóstico e
selecionar uma automação com base nas evidências. O contexto técnico usa uma base
mínima em OKF v0.2, consultada de forma seletiva pelas ferramentas de IA.

### Resultados / Findings

- O arquivo operacional tem 8.469 tickets, em vez dos ~30 mil do briefing;
  o de classificação IT tem 47.837 textos em oito classes.
- Não há data de abertura; os campos temporais são timestamps, e 1.365 dos
  2.769 pares encerrados têm a resolução antes da primeira resposta.
- Satisfação está disponível só nos 2.769 encerrados (32,70% da base).
- Há descrições repetidas com rótulos conflitantes. O tratamento e os conjuntos
  de avaliação serão definidos antes de treinar ou ajustar modelos.

Evidências e populações no [relatório de auditoria](docs/data-audit.md). Ainda não
há diagnóstico operacional final, ganho medido ou resultado de modelo.

### Recomendações

Não converter os timestamps em duração total ou esforço poupado. Definir em D02
os papéis dos datasets e as métricas sustentadas pelos dados antes de implementar.

### Limitações

Os arquivos não sustentam tempo total de resolução sem eventos adicionais;
satisfação descreve apenas encerrados. Placeholders nos textos e conflitos de
rótulo limitam seu uso como referência. Não há chave comum de entidade entre os
datasets; não foi validada transferência entre taxonomias.

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
- [Auditoria dos datasets](docs/data-audit.md)
- [Como reproduzir a aquisição e a auditoria](data/README.md)
- [Checagens de consistência e validade das evidências](docs/foundation-controls.md)
- [Fonte de verdade dos sete ajustes da revisão](docs/architecture-review.md#lista-oficial-para-validação)
- [Backlog](execution/backlog.md)

O setup da auditoria e suas evidências estão nos links acima. A execução do
protótipo e o CodeTour serão incluídos quando esses artefatos existirem.

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

Esses comandos executam os testes disponíveis e verificam o recibo da fundação.
Para baixar os dados e regenerar a auditoria, siga o setup em `data/README.md`.
O protótipo ainda será implementado.

O process log e os exports de chats são evidências para a equipe de recrutamento.
As regras de trabalho os excluem do contexto padrão das sessões, inclusive na
retomada. As decisões atuais devem estar nos documentos operacionais indicados.
