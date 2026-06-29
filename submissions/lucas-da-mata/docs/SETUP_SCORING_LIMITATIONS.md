# Setup, Scoring e Limitacoes

## Como rodar

Repositorio da solução:

```bash
git clone https://github.com/olucasdamata/pipeline-focus.git
cd pipeline-focus
npm install
npm run dev -- --host 127.0.0.1 --port 5180
```

Versão incluída na submissão:

```bash
cd submissions/lucas-da-mata/solution/pipeline-focus-console
npm install
npm run dev -- --host 127.0.0.1 --port 5180
```

URL local:

```text
http://127.0.0.1:5180/
```

Build de produção:

```bash
npm run build
```

App publicado:

```text
https://pipeline-focus-buddy.lovable.app/
```

QA final da versão publicada:

```text
docs/QA_REPORT_2026-06-29.md
```

## Dados usados

A aplicação usa os quatro CSVs do desafio:

- `accounts.csv`
- `products.csv`
- `sales_teams.csv`
- `sales_pipeline.csv`

Relações:

- `sales_pipeline.account` -> `accounts.account`
- `sales_pipeline.product` -> `products.product`
- `sales_pipeline.sales_agent` -> `sales_teams.sales_agent`

Apenas deals abertos entram na fila:

- `Prospecting`
- `Engaging`

Deals `Won` e `Lost` alimentam o histórico de win rate.

## Lógica de scoring

O score é rule-based, explicável e ponderado de 0 a 100.

Pesos:

| Fator | Peso | Intuição |
| --- | ---: | --- |
| Stage | 20% | Deals em `Engaging` têm comprador mais próximo da receita |
| Valor | 20% | Valor esperado relativo ao pipeline aberto |
| Fit da conta | 20% | Receita e headcount da conta |
| Timing / risco | 20% | Dias desde `engage_date`; deals antigos perdem momentum |
| Produto | 10% | Sinal de produto/pacote pelo preço |
| Vendedor / manager / região | 10% | Win rate histórico com fallback progressivo |

O score nunca usa valor sozinho. O objetivo é transformar potencial, contexto, timing e risco em uma prioridade de ação.

## Explicabilidade

Cada oportunidade mostra:

- score total;
- prioridade;
- confiança;
- próxima melhor ação;
- por que recebeu aquela pontuação;
- fatores positivos;
- fatores de risco;
- composição da pontuação;
- dados usados;
- limitações.

## Faixas de prioridade

| Score | Prioridade | Uso |
| ---: | --- | --- |
| 80-100 | High priority | agir agora |
| 60-79 | Priority | trabalhar esta semana |
| 40-59 | Watch | monitorar |
| 0-39 | Low | despriorizar |

## Limitações

- O score é heurístico, não um modelo de machine learning treinado.
- O dataset é histórico e não contém última interação real, e-mails, chamadas, notas ou próxima reunião.
- Deals sem valor de fechamento usam preço de tabela do produto como valor estimado.
- Quando faltam joins ou histórico suficiente, o score usa fallback e mostra a limitação.
- O app não grava dados em CRM real e não faz automação de outreach.

## Proximas evoluções

- Conectar dados reais de atividade comercial.
- Aprender pesos com histórico de conversão real.
- Criar alertas semanais por vendedor/manager.
- Integrar com CRM para registrar próxima ação.
