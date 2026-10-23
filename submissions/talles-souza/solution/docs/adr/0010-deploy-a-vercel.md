# ADR 0010: Deploy A na Vercel: web estática + API como função

**Status:** aceita (o deploy em si não foi feito; ver "Não verificado")

## Contexto

Localmente, `npm start` sobe um processo só que serve a web construída e a API na mesma porta. Publicado, o vendedor precisa abrir um endereço e ter a mesma coisa: a lista calculada pela API e, se a API falhar, a mesma lista calculada no navegador.

## Decisão

- **Duas partes no mesmo projeto Vercel.** A web é o estático do build do Vite (`apps/web/dist`, servido pela CDN). A API é uma função serverless Node.
- **O mesmo app.** A função (`apps/api/src/vercel.ts`) monta o mesmo `criarApp` do `npm start`, com a mesma carga conferida do `deals.json` e o mesmo banco opcional ([ADR 0009](0009-banco-com-papel-restrito.md)). O export default é o app Hono no adaptador de Node do Hono (`getRequestListener` de `@hono/node-server`): o handler `(req, res)` das funções Node da Vercel. O `serveStatic` do Hono fica só no `npm start`.
- **`npm run build` gera tudo.** Constrói a web e roda `scripts/construir-vercel.mjs`, que escreve a saída no formato da Build Output API: `.vercel/output/static` (a web), `.vercel/output/functions/api.func` (a API num arquivo só, pelo esbuild, com o `deals.json` e o `.sha256` em `data/`) e `.vercel/output/config.json` (rotas).
- **Rotas.** `/api/*` e `/health` vão para a função; o resto, para o estático. As mesmas rotas estão no `vercel.json`, com o `buildCommand` e o `installCommand`.
- **Ambiente.** Só `DATABASE_URL` (opcional). O IP do rate limit vem de `x-real-ip`, que a borda da Vercel preenche, porque na função o socket é o proxy.

## Consequências

- `npm run test:funcao` sobe a função construída num servidor HTTP local e confere `/health` (8.800 negócios, sha256 do `deals.json`), a fila (2.089 abertos) e o 404. Rodado nesta máquina: passou.
- Rate limit e disjuntor vivem na memória de cada instância da função; com várias instâncias, cada uma conta o seu.
- Se a função não subir (dado que não confere), a web cai para o modo local com o aviso de sempre, porque `/dados/deals.json` sai do estático.

## Não verificado

Sem deploy, não verifiquei na Vercel: que a plataforma usa a saída `.vercel/output` gerada pelo `buildCommand`; o tamanho máximo do pacote da função (o `index.mjs` tem cerca de 1,1 MB, mais o `deals.json`); que `x-real-ip` chega preenchido; e o tempo de partida a frio com o `deals.json` de 5 MB. A documentação lida ("Hono on Vercel") não fala desses pontos. Ficam para conferir no primeiro deploy.

## Alternativas consideradas

- **Zero configuração (o app Hono detectado pela Vercel):** é o caminho da documentação, mas a ordem entre o build da web e o empacotamento da função, e o import de TypeScript dos workspaces, não estão garantidos sem testar na plataforma. A Build Output API deixa o resultado do build explícito e testável localmente.
- **Adaptador `hono/vercel`:** na versão instalada do Hono, ele vem marcado como obsoleto, com remoção prevista na versão 5.
- **Tudo numa função (servindo também o estático):** perderia a CDN e o modo local quando a função falha.
