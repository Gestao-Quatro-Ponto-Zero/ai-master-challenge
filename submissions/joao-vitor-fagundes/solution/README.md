# POWER CRM: solução funcional

Aplicação local para explorar as 8.800 oportunidades do challenge, entender P/O/W/E e receber automaticamente a próxima ação por oportunidade.

## Execução rápida

Pré-requisitos:

- Python 3.9 ou superior;
- acesso à internet para consultar o read model demonstrativo.

```bash
python3 view/server.py
```

Abra [http://127.0.0.1:4173](http://127.0.0.1:4173).

Não há `npm install`, build ou variável de ambiente obrigatória para avaliar a demonstração. O servidor usa somente a biblioteca padrão do Python.

## Caminho de avaliação recomendado

1. Confirme que as quatro colunas do pipeline aparecem simultaneamente.
2. Use os filtros de vendedor, região, produto e Warmth.
3. Abra qualquer card e consulte o POWER Profile.
4. Expanda as evidências de P e E.
5. Observe o R ser carregado automaticamente; feche e reabra o card para confirmar a reutilização do resultado salvo.
6. Visite `/directory.html` e `/power-framework`.

## Arquitetura

```text
Browser
  ├─ Pipeline / Directory / POWER Profile
  ├─ GET /api/opportunity-power ──> servidor Python ──> Supabase read model
  └─ POST generate-recommendation ──> Supabase Edge Function
                                             ├─ cache Postgres
                                             └─ OpenAI Responses API
```

- `opportunity_power` é uma view somente de leitura protegida por RLS.
- A `anon key` presente no cliente é uma credencial pública do Supabase; ela não concede escrita.
- `service_role` e `OPENAI_API_KEY` existem apenas como secrets da Edge Function.
- `power_recommendations` e os contadores de uso não possuem leitura pública; somente a Edge Function acessa essas tabelas.
- A geração usa reserva atômica por oportunidade/hash/versão: chamadas simultâneas aguardam o mesmo resultado em vez de duplicar chamadas à IA.
- O demo aceita até 500 novas gerações por hora e 2.000 por dia. Os limites podem ser alterados pelos secrets `RECOMMENDATION_HOURLY_LIMIT` e `RECOMMENDATION_DAILY_LIMIT`.
- A função restringe origens de navegador ao servidor local documentado; `ALLOWED_ORIGINS` permite configurar destinos adicionais.
- O servidor local mantém cache em memória para as páginas do read model e reduz chamadas repetidas.
- O servidor local envia CSP, proteção contra framing, `nosniff`, política de referência e bloqueio de câmera, microfone e geolocalização.
- Se o proxy local não estiver disponível, o frontend consegue consultar o endpoint público diretamente.

## POWER implementado

P, O, W e E são resultados determinísticos pré-calculados. R é consultado automaticamente na abertura do card: se não existir uma versão válida, o modelo gera e salva; se `opportunity_id`, `input_hash` e `prompt_version` não mudarem, o resultado salvo é reutilizado.

| Pilar | Cálculo |
|---|---|
| P | Média das win rates de setor, produto, tier de ticket e match completo, ponderadas pela força da amostra. |
| O | Preço de catálogo dividido pelo maior preço; tiers derivados da posição no catálogo. |
| W | Percentual de ciclos encerrados com duração maior ou igual à idade atual; temperaturas derivadas dos quartis. |
| E | Média da win rate histórica do vendedor em produto, setor e tier de ticket. |
| PP | `(12P + 3O + 4W + 6E) / 25`; resultado armazenado usado para ordenar cada etapa. |
| R | Saída textual estruturada a partir de P/O/W/E e do contexto disponível. |

Detalhes, fórmulas e exemplos: [`../docs/power-framework.md`](../docs/power-framework.md).

## Priorização e interface

O board mantém um único pipeline canônico: `Prospecting`, `Engaging`, `Won` e `Lost` aparecem simultaneamente. Dentro de cada coluna, `POWER Priority` ordena o maior PP primeiro. O PP só existe quando P, O, W e E estão disponíveis; registros incompletos aparecem como `PP indisponível` no fim da própria etapa, nunca como zero.

Cada coluna possui scroll independente. O frontend renderiza um lote inicial, observa o fim de cada coluna e acrescenta novos cards sem alterar a posição das demais. Os cards já renderizados permanecem no DOM; `content-visibility` adia o trabalho visual dos elementos fora da viewport. A carga inicial busca uma amostra prioritária das quatro etapas em paralelo; os contadores exatos chegam na primeira resposta e não fazem count-up teatral. O restante sincroniza em segundo plano e a finalização atualiza metadados sem substituir os cards já visíveis.

## Reprodução dos dados e scores

### 1. Baixar e auditar o dataset

```bash
python3 -m pip install -r requirements-audit.txt
python3 scripts/download_data.py --output-dir data/raw
python3 scripts/audit_data.py \
  --data-dir data/raw \
  --output ../docs/data-audit.json
```

Checksums e proveniência estão em [`data/raw/README.md`](./data/raw/README.md). O diagnóstico legível está em [`../docs/data-audit.md`](../docs/data-audit.md).

### 2. Gerar a camada processada

```bash
python3 scripts/build_power_dataset.py --output-dir data/processed
```

O script usa somente a biblioteca padrão, normaliza as chaves conhecidas, calcula P/O/W/E e gera os CSVs de importação. Para oportunidades históricas, P e E usam apenas negócios encerrados antes do momento avaliado.

### 3. Reconstruir a infraestrutura opcionalmente

O código necessário está em:

- `supabase/migrations/20260828195500_initial_power.sql`: tabelas, índices, view, grants e RLS;
- `supabase/functions/generate-recommendation/index.ts`: Recommendation Engine;
- `data/processed/`: imports na ordem accounts, products, sales_teams, opportunities, power_score_runs e power_scores.

A demonstração já aponta para o projeto remoto. A reconstrução em outro projeto exige Supabase CLI e a configuração privada de `OPENAI_API_KEY`; nenhuma credencial privada é versionada.

### 4. Rodar as verificações determinísticas

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Os testes refazem a camada processada em diretório temporário e verificam contagens, cobertura, tiers derivados, unicidade, ranges dos scores e os critérios realmente implementados em E.

## Estrutura relevante

```text
solution/
├── data/
│   ├── raw/                 # snapshot e checksums do dataset
│   └── processed/           # gerada pelo script: tabelas normalizadas e scores
├── scripts/
│   ├── audit_data.py
│   ├── build_power_dataset.py
│   └── download_data.py
├── tests/
│   └── test_power_pipeline.py
├── supabase/
│   ├── migrations/
│   └── functions/generate-recommendation/
└── view/
    ├── index.html           # pipeline
    ├── directory.html       # diretório derivado
    ├── backend.js           # cliente do read model
    ├── app.js               # interações do CRM
    └── server.py            # servidor e proxy local
```

## Limitações técnicas

- A demonstração requer disponibilidade do projeto Supabase informado no código.
- R requer disponibilidade da Edge Function e da API do modelo; P/O/W/E continuam funcionando se R falhar.
- A aplicação é read-only e não persiste movimentações de cards.
- O PP é uma régua de ação dentro de cada etapa, não um classificador treinado de `Won` versus `Lost`; nos estágios encerrados, ele organiza oportunidades de expansão ou reativação.
- O acesso público é adequado ao dataset fictício; dados comerciais reais exigiriam autenticação e políticas por usuário/equipe.
- A cota da Recommendation Engine protege o demo contra consumo irrestrito, mas não substitui autenticação individual em produção.
- Não há suíte automatizada de UI; o checkpoint foi validado por rebuild dos dados, verificações de sintaxe, smoke test HTTP, navegação e console do navegador.

## Design system

`view/design-system.css`, apesar do nome, é a camada compartilhada de tokens e componentes utilizada pelo CRM funcional. Os antigos HTML e JS de exploração visual não fazem parte do pacote final de submissão.
