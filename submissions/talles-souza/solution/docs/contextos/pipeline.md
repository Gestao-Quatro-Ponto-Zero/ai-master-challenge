# Contexto `pipeline`

## Responsabilidade

Dar ao vendedor uma base confiável: carregar o `deals.json` (as 4 tabelas do CRM já juntas), conferir que é o arquivo publicado, validar o formato e expor os negócios com a idade de cada um. Também mede a janela em que os ganhos fecham e marca as lacunas do dataset, para que nenhuma tela invente dado que não existe.

Não decide grupo nem nota: só fatos.

## Contrato público (`packages/dominio/src/pipeline/index.ts`)

Tipos:
- `Deal`: um negócio com vendedor, manager, região, produto, preço de tabela, conta (ou `null`), estágio, datas ISO, `idadeDias` (só abertos com início), `duracaoDias` (só fechados) e `lacunas`.
- `Pipeline`: `deals`, `abertos`, `time` (os 35 vendedores, com manager e região), `janela`, `catalogo`, `contas`, `lacunas`, `referencia`.
- `MembroDoTime`: nome, manager e região de um vendedor.
- `Janela`: `referencia`, `ganhos`, `p50Dias`, `p95Dias`, `maxDias` (duração dos ganhos).
- `SituacaoJanela`: `prospeccao` | `na_janela` | `perto_do_limite` | `alem_da_janela`.
- `NovoLead`: vendedor, produto, conta e data de início opcionais.

Funções:
- `lerPipeline(bruto)` → `Resultado<Pipeline>`; erros `dados_invalidos` e `formato_invalido`.
- `conferirChecksum(bytes, arquivoSha256)` → `Resultado<string>`; erros `checksum_ilegivel`, `checksum_divergente`, `checksum_indisponivel`.
- `calcularJanela(deals, referencia)` e `situacaoNaJanela(deal, janela)`.
- `criarDealDeLead(lead, pipeline)` → `Resultado<Deal>`; erro `lead_invalido`.
- `FORMATO_DEALS = 2` (o formato com o time de vendas).

Contrato HTTP (`http.ts`): `ROTA_RESUMO`, `ROTA_DEALS`, `rotaDeal(id)`, `consultaDealsSchema`, `idDealSchema`, `novoLeadSchema`.

## Rotas da API

| Rota | O que devolve |
|---|---|
| `GET /api/pipeline/resumo` | formato, referência, total, abertos, janela, lacunas, catálogo, contas e o SHA-256 conferido |
| `GET /api/pipeline/deals` | lista paginada; filtros `vendedor`, `manager`, `regiao`, `estagio`, `aberto`; `limite` 1 a 2.500 (padrão 500), `deslocamento` |
| `GET /api/pipeline/deals/:id` | um negócio; id fora do formato (8 caracteres A–Z/0–9) → 400; inexistente → 404 `deal_nao_encontrado` |

Parâmetro desconhecido na query → 400 (schema estrito).

## Tela da web

`apps/web/src/pipeline/VisaoManager.tsx`, rota `#/manager` ("Acompanhar a equipe"): o painel "onde meu time está perdendo dinheiro?" (4 métricas e a tabela por vendedor), com filtros por vendedor, manager ou região (o cálculo é do contexto `priorizacao`). Só leitura; quem age é o vendedor.

## Testes

- `packages/dominio/src/pipeline/pipeline.test.ts`: leitura, recusa de formato, janela (p50/p95 por interpolação linear), situação na janela, lead novo, SHA-256 com LF, CRLF e BOM.
- `packages/dominio/src/aplicacao/integracao.test.ts`: com o arquivo real, 8.800 negócios, 2.089 abertos, 7 produtos, referência 2017-12-31, janela p50 57 / p95 116 / máximo 138 dias, checksum que bate.
- `apps/api/test/contrato.test.ts` (bloco `pipeline`) e `apps/api/test/integracao.test.ts` (checksum divergente não carrega).
- `apps/web/src/infra/clienteLocal.test.ts`: o modo local confere o mesmo checksum e recusa o que não bate.
- `data/test_preparar_dados.py`: 11 testes da junção contra o CSV do Kaggle, inclusive os 35 vendedores (5 sem negócio).

## Invariantes

- O arquivo só é aceito se o SHA-256 bate com o `.sha256`, o `formato` é 2, o `total` declarado é igual ao número de negócios e todo negócio é de um vendedor do time (sem vendedor repetido).
- "Hoje" é a `referencia` do arquivo: o último `close_date` do dataset (2017-12-31).
- `idadeDias` existe só em negócio aberto com data de início; `duracaoDias`, só em fechado.
- Lacuna fica marcada, nunca é preenchida: `sem_conta`, `sem_engage_date`. As duas correções de nome também ficam marcadas no negócio: `produto_normalizado` (GTXPro → GTX Pro) e `setor_normalizado` (erro de digitação em `technology`).
- Lead novo: o vendedor precisa estar no time e o produto no catálogo; data de início no formato ISO, que exista de fato (sem 30 de fevereiro) e não seja depois da referência. O id é estável para o mesmo lead (`LEAD` + 8 hexadecimais), para as respostas se ligarem a ele.
- O domínio não faz I/O: quem lê o arquivo (ou o banco, se o metadado dele conferir) é a API (`apps/api/src/carregador.ts`) ou o modo local da web.
