# Pipeline Focus Console

Aplicação web funcional para o Challenge 003 - Lead Scorer.

## Rodar localmente

```bash
npm install
npm run dev -- --host 127.0.0.1 --port 5180
```

Abra:

```text
http://127.0.0.1:5180/
```

Build de produção:

```bash
npm run build
```

Lint:

```bash
npm run lint
```

## App publicado

```text
https://pipeline-focus-buddy.lovable.app/
```

## Dados

Os CSVs do desafio estão em:

```text
public/data/
src/data/
```

Arquivos usados:

- `accounts.csv`
- `products.csv`
- `sales_teams.csv`
- `sales_pipeline.csv`
- `data_dictionary.csv`

## Scoring

A lógica principal fica em:

```text
src/lib/scoring.ts
```

O score é rule-based e explicável, de 0 a 100, usando:

- estágio do deal;
- valor esperado;
- fit da conta;
- timing/risco de esfriamento;
- sinal do produto;
- histórico do vendedor/manager/região.

Cada oportunidade mostra motivo, próxima ação, fatores positivos, riscos, composição do score, dados usados e limitações.
