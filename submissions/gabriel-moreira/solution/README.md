# Pipeline Priorizado — Lead Scorer

Ferramenta de triagem do pipeline de vendas por **valor em risco** (`PRIORIDADE = p̂ × VALOR × URGÊNCIA`), não por probabilidade categórica de fechamento — a evidência estatística por trás dessa escolha está em [`validation/`](./validation) e em [`../process-log/decisions-log.md`](../process-log/decisions-log.md). Este documento é o guia prático: como rodar, o que cada peça faz, e o que a solução explicitamente não faz.

## Como rodar

### Via Docker (comando único)

```bash
docker compose up --build
```

Abre em `http://localhost:8080`. O serviço `web` (nginx) serve o build do React e faz proxy de `/api/*` para o serviço `api` (FastAPI, porta 8000 também exposta no host).

### Sem Docker

```bash
make install   # cria os três venvs Python (scoring, api, validation) + npm install em web/
make dev-api   # terminal 1 — http://localhost:8000
make dev-web   # terminal 2 — http://localhost:5173 (proxy /api -> :8000)
```

Pré-requisitos: Python 3.10+, Node.js 18+. Sem banco de dados — os quatro CSVs em `../data/` carregam inteiros em memória na inicialização da API.

### Testes

```bash
make test
```

Roda, em sequência: os testes unitários do motor de scoring (`scoring/`, incluindo as duas metades de CONFIANÇA, a árvore de ESTADO, plano de ação em passos e os exemplos de referência dos specs), os testes de contrato/e2e da API (`api/`, cobrindo listagem paginada e ordenada com desempate estável, filtros de organização sem escopo de sessão, endpoint de detalhe, opções de filtro e exportação de identificadores filtrados), os testes de determinismo e consistência do artefato de validação (`validation/`, incluindo os três resultados negativos de condicionamento por setor/aging por produto/URGÊNCIA por produto), e a checagem de tipos do frontend (`web/`).

### Validação estatística

```bash
make validate
```

Imprime o relatório completo em texto — 14 seções: ausência de sinal preditivo firmográfico (AUC + testes de permutação, com correção para múltiplas comparações), derivação de `k` por nível hierárquico, monotonicidade de `risco(t)`, fronteira de censura de 138 dias, concentração de PRIORIDADE no topo da fila, três hipóteses de refinamento rejeitadas por validação cruzada, distribuição de CONFIANÇA, as duas auditorias que garantem que nenhum desfecho é atribuído por nós, os dois nulos do fit por vendedor, o denominador dos CSVs de análise e o poder dos testes de vendedor (τ̂ por variância em excesso e MDE — o que separa "não há diferença" de "a amostra não enxerga a diferença"). Ver [`validation/backtest.py`](./validation/backtest.py).

[`Relatório Gerado`](../docs/report.md)

## A fórmula, resumida

```
p̂          = encolhimento hierárquico (empirical Bayes) da taxa de ganho do produto, k derivado dos dados
VALOR      = preço de tabela × multiplicador de porte (prior neutro 1,00 se a conta é desconhecida)
URGÊNCIA   = risco(idade) — probabilidade de resolver nos próximos 30 dias, curva isotônica
PRIORIDADE = p̂ × VALOR × URGÊNCIA                    (dólares — valor intermediário auditável, não exibido)
SCORE      = percentil(PRIORIDADE) × 100              (contra os 4.238 negócios historicamente ganhos — número de prioridade exposto)
CONFIANÇA  = min(completude, suporte)                  (0–100 — veracidade do dado, não probabilidade)
ESTADO     = árvore(sem_precedente, SCORE≥95, CONFIANÇA<50)   (Priorizar / Acompanhar / Qualificar / Revisão em lote)
```

SCORE e CONFIANÇA nunca se combinam num único número — um ordena a fila, o outro diz o quanto acreditar na posição. PRIORIDADE em dólares não é exibida nem ordena a fila: a decomposição de `log(PRIORIDADE)` atribui 87,3% da variância a VALOR e 0,1% a `p̂` — ordenar por ela seria, na prática, ordenar por preço de tabela. Permanece calculada e exportada no CSV como valor auditável. A decomposição completa, com os exemplos de referência e o porquê de cada peça, está em [`../docs/architecture.md`](../docs/architecture.md).

Toda oportunidade aberta recebe SCORE — inclusive as 1.425 sem conta vinculada (VALOR usa o prior neutro de porte) e as 500 em Prospecting (URGÊNCIA fixa em 0,47, sem idade imputada).

## Abertura direta no pipeline

A aplicação abre direto na aba Oportunidades, com a fila trabalhável (993 oportunidades — os três estados `Priorizar`/`Acompanhar`/`Qualificar`) já visível — não há tela de seleção de identidade nem sessão a manter. `Revisão em lote` (1.096 oportunidades sem precedente histórico) fica numa visão própria, fora da fila padrão. Vendedor, gerente e escritório regional são **filtros ordinários** sobre o funil inteiro, iguais a produto e confiança: qualquer valor presente nos dados pode ser escolhido, e o recorte resultante é refletido na URL — compartilhável e recarregável.

Todo endpoint de dados é aberto, sem cabeçalho `Authorization`. Essa é uma decisão consciente para um dataset público de demonstração, sem informação real de cliente — não uma omissão. O trade-off e o caminho de produção (SSO/OIDC real, escopo aplicado no servidor) estão registrados em [`../process-log/decisions-log.md`](../process-log/decisions-log.md) e em "Limitações declaradas" abaixo.

## Sobrecarga de vendedor e sugestão de redistribuição

Uma terceira aba, **Sobrecarga**, compara a carteira de cada vendedor com a média do próprio escritório regional (`Central`/`East`/`West`) em cada ESTADO. Um par (vendedor, ESTADO) é marcado sobrecarregado quando `contagem ≥ 1,5× a média do escritório` **e** `contagem ≥ 5` (piso absoluto contra falso alarme em ESTADOs raros). Sobre o funil atual: 12 pares, 8 vendedores, 227 oportunidades.

Para cada oportunidade de vendedor sobrecarregado, o sistema sugere um colega do mesmo escritório — não sobrecarregado naquele ESTADO, com histórico de negócios fechados — combinando folga de carga com o fit histórico do candidato no produto e no setor da oportunidade. **A sugestão é só informativa**: nunca reatribui a oportunidade nem altera o dono registrado no dado processado ou em qualquer exportação; quem decide é o gestor. O vendedor sugerido só aparece na aba Sobrecarga e no painel de detalhe — a listagem geral de Oportunidades recebe apenas o booleano `sobrecarregado` (com filtro correspondente), nunca o nome do candidato.

O fit por vendedor é calculado apenas sobre os 6.711 negócios com desfecho registrado (nunca sobre abertos) e encolhido para o prior do escritório — mas os mesmos testes de permutação que sustentam a fórmula principal (AUC ≈ 0,50, seções 1-2 de [`report.md`](../docs/report.md)) não encontram sinal em vendedor como preditor: p = 0,262 sem controle, 0,588 em vendedor×produto e 0,545 em vendedor×setor — e, contra o nulo aditivo que isola afinidade (o que a palavra *fit* afirma), 0,874 e 0,877. Por isso toda superfície que exibe fit também exibe essa ressalva, e o fit **nunca** entra em `p̂`, VALOR, URGÊNCIA, PRIORIDADE, SCORE, CONFIANÇA ou ESTADO — é uma camada operacional separada da priorização, não um ajuste dela.

Fórmulas, encolhimento e endpoints (`GET /carga`, `GET /deals/sobrecarregados`) detalhados em [`../docs/architecture.md`](../docs/architecture.md) — especificado via OpenSpec antes da implementação, mas `openspec/` é gerado localmente e não faz parte deste checkout.

## Estrutura

```
scoring/      pacote Python puro (sem FastAPI/React) — a fórmula, importada por api/ e validation/
api/          FastAPI — listagem paginada/ordenada, filtros comuns, detalhe, rollup, carga, export
web/          React + TypeScript + Tailwind — abas Oportunidades/Sobrecarga/Gestão, filtros, painel de detalhe
validation/   evidência estatística executável — AUC, permutação, k, monotonicidade, concentração, auditorias
```

Ver [`../docs/architecture.md`](../docs/architecture.md) para o mapa completo de cada módulo.

## Limitações declaradas

- **Sem autenticação.** Nenhum endpoint de dados exige identificação — qualquer cliente lê o funil inteiro. Aceitável apenas porque o dataset é público e de demonstração, sem informação real de cliente. Produção exigiria SSO/OIDC real e escopo por papel aplicado no servidor — nenhum dos dois existe hoje, nem parcialmente. Documentado, não escondido — evolução de produção registrada em `../docs/architecture.md`.
- **Sem persistência.** Tudo em memória, recarregado do zero a cada inicialização. Caminho de produção: banco gerenciado (Supabase ou equivalente).
- **Sem previsão categórica de win/loss.** `p̂` varia só entre 0,63 e 0,75 — a diferenciação real vem de valor e urgência, não de probabilidade. A evidência de que isso é uma escolha correta, não uma limitação técnica, está em `validation/`.
- **A distribuição de referência de SCORE** (negócios ganhos) só se atualiza no ciclo trimestral de recalibração — um negócio fechado ontem não entra no percentil até a próxima recalibração. Decisão deliberada: é o que torna SCORE estável entre requisições.