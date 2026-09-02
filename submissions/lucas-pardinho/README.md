# Submissão — Lucas dos Santos Pardinho — Challenge 003

## Sobre mim

- **Nome:** Lucas dos Santos Pardinho
- **LinkedIn:** não informado
- **Challenge escolhido:** 003 — Lead Scorer (Vendas / RevOps)
- **Solução:** G4 Focus
- **Demo online:** a preencher depois da validação do deploy

## Executive Summary

O **G4 Focus** transforma as 2.089 oportunidades abertas do CRM em uma fila de trabalho explicável, para que vendedores e gestores saibam onde agir primeiro. A solução combina propensão histórica de conversão (65%), acionabilidade/frescor (20%) e valor relativo (15%), sem apresentar essa heurística como uma probabilidade perfeita. A aplicação usa os 8.800 registros reais do dataset, mostra motivos e alertas de qualidade em cada recomendação e separa oportunidades ainda em prospecção das que já estão em negociação. O resultado é um produto web executável, com API, pipeline reproduzível, testes, Docker e caminho de deploy no Railway.

## Solução

### O problema que escolhi resolver

Ordenar por valor favoreceria deals grandes, mas não necessariamente bons. Treinar um classificador diretamente na fotografia final do CRM, por outro lado, criaria risco de vazamento temporal: datas e valores de fechamento só existem depois que o resultado é conhecido. A proposta do G4 Focus é mais pragmática: gerar uma recomendação operacional explicável com os sinais disponíveis antes do desfecho e deixar claro onde a evidência ainda é limitada.

### Abordagem

1. Auditei relacionamentos, ausências, datas e distribuições antes de definir a interface.
2. Normalizei apenas inconsistências verificáveis, como `GTXPro` no pipeline versus `GTX Pro` no catálogo, preservando os dados brutos.
3. Separei `Prospecting` de `Engaging`: sem data de engajamento, o primeiro grupo precisa de uma fila de qualificação, não de uma falsa comparação com negociações em andamento.
4. Usei um score híbrido, com contribuições limitadas e explicação por oportunidade.
5. Transformei o resultado em fluxo de trabalho: **Foco agora**, **Acelerar**, **Nutrir**, **Resgatar ou desqualificar** e **Qualificar**.

Detalhes de cálculo, guardrails e validação estão em [Metodologia de scoring](./docs/scoring-methodology.md).

### Resultados / Findings

| Achado confirmado | Implicação para o produto |
|---|---|
| 8.800 oportunidades: 4.238 `Won`, 2.473 `Lost`, 1.589 `Engaging` e 500 `Prospecting` | A tela inicial deve priorizar as 2.089 oportunidades ainda abertas, sem esconder o histórico usado como evidência. |
| 1.425 oportunidades sem conta | O score precisa funcionar com evidência parcial e exibir confiança/alerta, em vez de imputar uma empresa fictícia. |
| 500 registros sem `engage_date`, todos em `Prospecting` | A fila **Qualificar** deve ser avaliada por completude e potencial, não por envelhecimento desde o engajamento. |
| 2.089 registros sem `close_date` e `close_value`, correspondentes ao pipeline aberto | Esses campos não podem entrar no score de uma oportunidade aberta. |
| `GTXPro` não casa com `GTX Pro` sem normalização | Sem o reparo, 1.480 oportunidades perderiam os atributos do produto. |
| Ciclos fechados duram no máximo 138 dias, enquanto o grupo `Engaging` atual está muito envelhecido | O produto precisa tornar deals parados visíveis e sugerir resgate ou desqualificação, não apenas premiar valor. |
| Holdout temporal: 4.726 fechamentos antes de 2017-10-01 tiveram 64,37% de vitórias; os 1.985 do Q4, 60,25% | Há mudança temporal; uma taxa histórica única tende a ficar otimista e precisa de monitoramento/recalibração. |
| Features estáticas de produto, setor, região e porte produziram AUC aproximada de 0,489 no holdout e Brier pior que o baseline; agente elevou a AUC apenas para ~0,518 | A evidência não sustenta vender um modelo preditivo forte. O agente fica fora do score principal e o produto assume priorização operacional conservadora. |

O relatório gerado pela versão executada do pipeline é a fonte de verdade para contagens, distribuições e componentes finais do score: `solution/generated/model-report.json` e `solution/generated/data-quality.json`.

### O que o usuário recebe

- Visão executiva do pipeline, valor em aberto, filas e alertas.
- Carteira priorizada com busca e filtros por vendedor, manager, região, etapa e fila.
- Score de 0 a 100 com motivos legíveis, nível de confiança e flags de qualidade.
- Separação explícita entre prioridade de negociação e qualificação de prospect.
- Página de metodologia e endpoints JSON para integração.

### Recomendações

1. **Rodar um piloto com um time regional por 30 dias.** Medir taxa de contato, avanço de etapa, conversão e tempo economizado por fila, sempre comparando com um grupo de controle.
2. **Registrar os eventos que hoje não existem.** Próxima atividade, último contato, origem do lead, mudanças de etapa e motivo de perda aumentariam muito a capacidade preditiva.
3. **Criar snapshots imutáveis do pipeline.** Eles permitem treinar e validar um modelo temporal sem reconstruir o passado a partir do estado final.
4. **Recalibrar por período, não por vendedor.** O vendedor deve ser filtro e dimensão de monitoramento; usá-lo como atalho no score principal pode cristalizar diferenças de território e distribuição de carteira.
5. **Tratar score como apoio, não como decisão automática.** O feedback do vendedor deve ser capturado e auditável antes de automatizar cadências ou descarte.

## Como executar

### Opção recomendada: Docker

Pré-requisito: Docker Desktop ou Docker Engine com Compose.

```bash
cd submissions/lucas-pardinho/solution
docker compose up --build
```

Depois abra [http://localhost:3000](http://localhost:3000). O health check deve responder em [http://localhost:3000/api/health](http://localhost:3000/api/health).

### Execução local sem Docker

Pré-requisitos: Python 3.11+ e Node.js 20+.

```bash
cd submissions/lucas-pardinho/solution
python3 analytics/pipeline.py \
  --data-dir data/raw \
  --normalized-dir data/normalized \
  --output-dir generated

cd web
npm ci
npm run check
HOSTNAME=127.0.0.1 PORT=3000 npm start
```

Por padrão, a aplicação fica em `http://localhost:3000`. Para desenvolvimento de interface, use `npm run dev` depois de gerar os artefatos.

Mais detalhes:

- [Guia operacional da solução](./solution/README.md)
- [Arquitetura e contratos](./docs/architecture.md)
- [Metodologia de scoring](./docs/scoring-methodology.md)
- [Proveniência e integridade dos dados](./docs/data-provenance.md)
- [Fork, Git, Pull Request e Railway](./docs/submission-and-deployment.md)

## Limitações

- O dataset é uma fotografia final, não um histórico de mudanças de etapa. Portanto, o score atual é uma priorização híbrida explicável, não uma promessa causal nem uma probabilidade perfeitamente calibrada.
- Não há atividades comerciais, canal de aquisição, próxima tarefa, motivo de perda ou histórico de contatos.
- A data de referência é inferida do último fechamento observado; uso produtivo deve receber um `snapshot_at` explícito.
- Amostras pequenas recebem regularização/backoff e menor confiança; segmentos raros não devem ser interpretados como padrões estáveis.
- A versão do challenge é read-only e baseada em arquivos. Escala real exigiria integração autenticada com CRM, snapshots, controle de acesso, telemetria e monitoramento de drift.
- O deploy no Railway e a URL pública só serão marcados como validados depois de um teste real do endpoint de saúde e da interface publicada.

## Process Log — Como usei IA

> Este registro é uma narrativa curada do processo, não uma transcrição inventada. Fatos verificados, decisões e hipóteses aparecem separados.

### Ferramentas usadas

| Ferramenta | Para que usei |
|---|---|
| Codex | Leitura do brief, decomposição do problema, EDA verificável, discussão de leakage/fairness, implementação paralela com escopos isolados, testes e documentação. |
| Git e GitHub | Fork, branch de submissão, rastreabilidade das mudanças e Pull Request final. |

### Workflow

1. Li o enunciado e as regras de submissão antes de escrever código.
2. Validei ZIP, schemas, contagens, ausências e chaves do dataset.
3. Testei os sinais disponíveis e reduzi o escopo do modelo quando a evidência estática se mostrou fraca.
4. Defini o produto e suas filas a partir da decisão comercial que precisava ser tomada.
5. Separei pipeline de dados, aplicação e empacotamento em frentes independentes; depois integrei pelos contratos JSON.
6. Reservei a etapa final para testes de pipeline, build, container, API, interface e revisão do diff.

### Onde a IA errou e como corrigi

Durante a exploração, uma direção tentadora era chamar o score de “probabilidade de fechamento” e dar peso alto a correlações estáticas. A amostra disponível não sustenta essa promessa: ela contém o resultado final e não traz snapshots históricos. Corrigi o contrato para **prioridade explicável**, removi variáveis pós-desfecho, limitei a influência de segmentos pequenos e deixei a validação temporal completa como próximo passo.

Outro erro concreto apareceu no relacionamento de produtos: uma junção literal trataria `GTXPro` como produto desconhecido. Em vez de descartar os 1.480 registros, normalizei esse alias de forma explícita e testável.

### O que eu adicionei que a IA sozinha não decidiria

O principal julgamento de produto foi não otimizar apenas um ranking. Eu converti o score em filas com intenções diferentes, separei `Prospecting` de `Engaging`, mantive o vendedor fora do componente principal para reduzir risco de reforçar desigualdades históricas e exigi motivos/flags em cada recomendação. Essas decisões tornam o output mais seguro e utilizável na reunião de pipeline.

### Evidências

- [Narrativa detalhada e decision log](./process-log/README.md)
- Código, testes e relatórios gerados dentro desta pasta
- Histórico Git e discussão do Pull Request no fechamento da submissão
- Screenshots ou chat export: não anexados; a narrativa escrita é o formato de evidência escolhido neste repositório

---

**Submissão enviada em:** a preencher no fechamento
