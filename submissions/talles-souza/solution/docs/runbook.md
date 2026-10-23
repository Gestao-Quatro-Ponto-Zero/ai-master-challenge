# Runbook

Como pôr no ar, conferir e consertar a ferramenta que responde ao vendedor "onde eu foco hoje?". Todos os comandos na pasta `solution/`. Exemplos em bash; no PowerShell, variável de ambiente se define antes: `$env:PORT=8799; npm start`.

## Rodar

```bash
npm install            # uma vez
npm start              # constrói a web e sobe app + API em http://localhost:8787
```

Sinal de que subiu (log):

```
Lead Scorer em http://localhost:8787 (app + API)
dados: 8800 deals, referência 2017-12-31, sha256 cd205caa8344… (do deals.json); respostas e decisões: memória deste processo (sem DATABASE_URL)
```

Conferir: `curl http://127.0.0.1:8787/health` → `{"status":"ok","versao":"0.1.0","dados":{"total":8800,"referencia":"2017-12-31","checksum":"76c6…"},…}`.

Parar: `Ctrl+C` (o servidor fecha em até 3 s).

### Variáveis

| Variável | Padrão | Para quê |
|---|---|---|
| `PORT` | `8787` | porta (1 a 65535; fora disso não sobe) |
| `HOST` | `127.0.0.1` | interface; fora do loopback, o servidor avisa que não há login |
| `DEALS_PATH` | `data/deals.json` | outro arquivo de dados (precisa do `.sha256` ao lado) |
| `SERVIR_WEB` | `apps/web/dist` se existir | pasta da web construída; `0` sobe só a API |
| `RATE_LIMIT_CAPACIDADE` / `RATE_LIMIT_RECARGA_POR_SEGUNDO` | `60` / `2` | rate limit por IP |
| `TIMEOUT_MS` | `5000` | timeout por requisição |
| `PAYLOAD_MAX_BYTES` | `1048576` | limite do corpo |
| `CORS_ORIGENS` | `http://localhost:5173,http://localhost:4173` | origens liberadas (separadas por vírgula) |
| `DATABASE_URL` | (vazia) | banco compartilhado das respostas e decisões ([ADR 0009](adr/0009-banco-com-papel-restrito.md)); vazia = `deals.json` + memória |

### Desenvolver

```bash
npm run dev            # API em 8787 (recarrega ao salvar) + web em http://localhost:5173
```

A web do Vite repassa `/api` e `/health` para a API (`API_URL`, padrão `http://localhost:8787`). Para subir as partes separadas:

```bash
npm run dev -w @lead-scorer/api     # terminal 1
npm run dev -w @lead-scorer/web     # terminal 2
```

## Testar

```bash
npm test               # tudo, menos o E2E
npm run test:e2e       # E2E com vídeo
```

`npm test` roda em sequência e para no primeiro erro:

| Passo | Comando isolado | O que confere |
|---|---|---|
| Fronteiras | `node scripts/checar-fronteiras.mjs` | nenhum contexto importa o interno de outro; o domínio não faz I/O |
| Tipos | `npm run typecheck` | TypeScript strict nos 3 pacotes |
| Lint | `npm run lint` | ESLint |
| Unidade e integração | `npm run test:unit` | domínio (71), API (53), web (73), na última execução |
| Dados | `npm run test:dados` | a junção em Python (10 testes) pelo uv |

O `test:dados` procura o CSV em `CRM_DADOS` (pasta com os 4 arquivos do Kaggle). Sem o CSV, o pytest marca os testes de contagem como pulados; sem uv, o passo inteiro é pulado com aviso. Nenhum dos dois casos falha o `npm test`.

`npm run test:e2e` sobe o app com `npm start` na porta 8787 (`E2E_PORTA` muda), roda os 5 fluxos em desktop e o de 390 px também no perfil de celular (6 execuções) e grava um vídeo por execução em `e2e/videos/`.

## Gerar o `deals.json`

O arquivo já vem no repositório. Para refazer a partir do CSV:

```bash
uv run --no-project --python 3.12 --with pandas==3.1.0 python -X utf8 data/preparar_dados.py <pasta-com-os-4-csv> [saida.json]
```

- Sem `saida.json`, sobrescreve `data/deals.json` e o `data/deals.json.sha256`.
- Saída esperada: `8800 deals e 35 vendedores → … (referência 2017-12-31, sha256 cd205caa8344…)`.
- O resultado é determinístico: com o mesmo CSV, o mesmo SHA-256.
- O build da web copia os dois arquivos para `apps/web/public/dados/` (modo local) sozinho, no `predev` e no `prebuild`.

## Problemas comuns

### Porta ocupada

Sintoma: a API termina com `Error: listen EADDRINUSE: address already in use 127.0.0.1:8787`, ou o Vite recusa a 5173 (ele está com `strictPort` e não troca de porta sozinho).

- Use outra porta: `PORT=8799 npm start`.
- Ou ache e feche o processo:
  - Windows: `netstat -ano | findstr :8787` e `taskkill /PID <pid> /T /F`
  - macOS/Linux: `lsof -i :8787` e `kill <pid>`

### Checksum divergente

Sintoma: `A API não subiu: checksum_divergente: O deals.json não bate com o checksum publicado.` (ou, no navegador em modo local, a mesma mensagem).

Causa: o `deals.json` foi editado, truncado ou trocado sem regenerar o `.sha256`. Um editor que muda o fim de linha também muda o hash.

Correção:
- Para voltar ao publicado: `git checkout -- data/deals.json data/deals.json.sha256`.
- Para usar um arquivo novo: gere com `preparar_dados.py` (que grava os dois juntos). Não edite o `.sha256` à mão.
- `checksum_ilegivel`: o `.sha256` não está no formato `<64 hexadecimais>  deals.json`.

### Playwright sem navegador

Sintoma: `npm run test:e2e` falha dizendo que o executável do navegador não existe e pede para rodar `npx playwright install`.

Correção: `npx playwright install chromium` (uma vez). A versão do Playwright é fixa no `e2e/package.json`; se a execução pedir também o modo headless ou o ffmpeg (usado na gravação do vídeo), `npx playwright install chromium chromium-headless-shell ffmpeg`.

### Python do sistema sem pandas

Sintoma: `ModuleNotFoundError: No module named 'pandas'` ao rodar `python data/preparar_dados.py`, ou o Python do sistema quebrado.

Correção: use o uv, que baixa um Python 3.12 e o pandas isolados, sem mexer no sistema:

```bash
uv run --no-project --python 3.12 --with pandas==3.1.0 python -X utf8 data/preparar_dados.py <pasta-com-os-4-csv>
```

O `npm test` já chama o pytest assim (`scripts/testar-dados.mjs`).

### `npm run dev` sem a API

Sintoma: o Vite sobe em 5173, mas a linha `[api] Lead Scorer em …` não aparece e a página mostra o aviso de modo local; o log do Vite mostra `http proxy error: /health … ECONNREFUSED`.

Visto num shell sem terminal interativo no Windows: o `tsx watch` da API não chegou a escutar dentro do `concurrently`. As mesmas partes sobem normalmente em terminais separados:

```bash
npm run dev -w @lead-scorer/api     # terminal 1: espere "Lead Scorer em http://localhost:8787"
npm run dev -w @lead-scorer/web     # terminal 2
```

Ou use `npm start`, que não depende do modo watch.

### A tela mostra "Sem conexão com o servidor"

A web caiu para o modo local: a API não respondeu (fora do ar, timeout, erro 5xx ou rate limit esgotado). A lista continua certa, calculada no navegador com o mesmo domínio. A cada 15 s a web pergunta a `/health`; quando a API volta, o aviso some. Confira a API com `curl http://127.0.0.1:8787/health`.

### O log diz `banco: metadado_divergente`

O banco foi carregado de outro `deals.json` (outro SHA-256 ou outro formato). A API segue com o arquivo embarcado e grava as respostas no banco normalmente. Para usar os negócios do banco, recarregue `lead_scorer.metadados` com o `sha256_deals_json` e o `formato` do `deals.json` em uso (o papel da aplicação não pode alterar o metadado).

### O log diz `banco: … falhou; usando a memória`

O banco não respondeu (rede, credencial, limite de conexões). A API grava e lê na memória e responde `armazenamento: "memoria"`; depois de 3 falhas seguidas, o disjuntor fica aberto por 30 s. Confira a `DATABASE_URL` e a rede; quando o banco volta, a próxima tentativa fecha o circuito.

### Construir para a Vercel

`npm run build` gera `.vercel/output` (estático + função); `npm run test:funcao` sobe a função construída e confere `/health`, a fila e o 404. Se faltar `apps/web/dist`, o script avisa e para. Ver [ADR 0010](adr/0010-deploy-a-vercel.md).

### 421 `host_invalido`

A API foi chamada por um nome que não está na lista dela (`localhost`, `127.0.0.1` ou `[::1]` na porta, mais as origens do `CORS_ORIGENS`). Use um desses nomes, ou acrescente a origem em `CORS_ORIGENS`.
