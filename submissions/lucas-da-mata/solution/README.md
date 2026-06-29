# Pipeline Focus Console

## O que testar primeiro

Abra:

```text
https://pipeline-focus-buddy.lovable.app/
```

Fluxo recomendado para avaliação:

1. Veja o **Brief de segunda-feira** no topo.
2. Confira os cards de pipeline aberto, alta prioridade, valor priorizado e risco de esfriamento.
3. Use os filtros por vendedor, manager, região, stage, prioridade e produto.
4. Clique no primeiro deal da fila.
5. Leia o painel lateral: score, motivo, próxima ação, fatores positivos, riscos, dados usados e limitações.
6. Abra **Lógica da pontuação** para ver pesos e regras.
7. Teste **Copiar lista de ações** e **Exportar CSV**.
8. Confira a visão **RevOps para managers** e o bloco de **Qualidade do score**.

## Código fonte

```text
https://github.com/olucasdamata/pipeline-focus
```

O código também está incluído nesta própria submissão:

```text
solution/pipeline-focus-console/
```

Para rodar a versão local incluída no pacote:

```bash
cd submissions/lucas-da-mata/solution/pipeline-focus-console
npm install
npm run dev -- --host 127.0.0.1 --port 5180
```

## Stack

- React
- TanStack Start
- TypeScript
- Tailwind CSS
- PapaParse
- Lovable para preview/publicação

## Por que esta solução

O desafio pedia uma ferramenta funcional para vendedores, não um notebook ou uma apresentação. Por isso, a solução foi desenhada como uma fila operacional:

```text
deal -> score -> motivo -> risco -> próxima ação
```

## Dados

Os CSVs usados ficam em:

```text
public/data/
```

Arquivos:

- `accounts.csv`
- `products.csv`
- `sales_teams.csv`
- `sales_pipeline.csv`
- `data_dictionary.csv`

## Validação esperada

Na tela publicada, o avaliador deve ver:

- `CRM conectado · 8.800 negócios`
- `2.089` negócios abertos
- fila priorizada com `RDHTQLNI` no topo
- score e próxima ação por deal
- explicação transparente do score
- visão por manager
- resumo de confiança e limitações dos dados

## Evidências visuais

Screenshots finais:

- `../process-log/screenshots/01-public-dashboard-desktop.jpg`
- `../process-log/screenshots/02-scoring-logic-modal.jpg`
- `../process-log/screenshots/03-public-dashboard-mobile.jpg`
