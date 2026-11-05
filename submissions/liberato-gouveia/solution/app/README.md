# Tela do Lead Scorer (Lovable)

**App publicado:** https://lead-scorer-liberato.lovable.app

A tela foi construída no Lovable pelo Claude, a partir de prompts aprovados pelo Liberato (`process-log/prompts/`). Ela **não recalcula notas, chances, valores esperados nem classificações**. Tudo isso vem do motor (`solution/motor/`). A tela só carrega, filtra, conta, soma e formata.

## O que está nesta pasta
O **projeto completo** do Lovable, exportado pelo botão oficial "Download codebase" em 04/11/2026. São os 77 arquivos que a API do Lovable lista para o projeto (commit `396c42e`), com 2 exclusões:
- `README.md` genérico do Lovable: substituído por este
- `AGENTS.md`: instruções para agentes de IA sobre uma sincronização com GitHub que este projeto não usa

Não há `node_modules`, arquivos compilados, arquivos `.env` nem chaves. A varredura está registrada no Registro 11, e o `.gitignore` do projeto impede que dependências instaladas sejam incluídas.

| Arquivo ou pasta | O que é |
|---|---|
| `src/routes/index.tsx` | **A tela**: tudo o que é específico deste app |
| `src/styles.css` | Cores da faixa de aviso e das ações, e a fonte |
| `src/routes/__root.tsx`, `src/router.tsx`, `src/server.ts`, `src/start.ts` | Estrutura do TanStack Start (modelo do Lovable) |
| `src/components/ui/` | Componentes shadcn/ui (modelo do Lovable) |
| `src/test/` | Teste automático do modelo do Lovable |
| `package.json`, `bun.lock` | Dependências e versões travadas |
| `vite.config.ts`, `tsconfig.json`, `vitest.config.ts`, `eslint.config.js`, `components.json`, `bunfig.toml`, `.prettierrc` | Configurações |

## De onde vêm os dados
Ao abrir, a tela lê o arquivo do motor publicado na branch de entrega:
`https://raw.githubusercontent.com/libegouv/ai-master-challenge/refs/heads/submission/liberato-gouveia/submissions/liberato-gouveia/solution/motor/saida/deals_priorizados.json`

Se o motor rodar de novo e a branch for atualizada, a tela mostra os dados novos em até ~5 minutos (cache do GitHub).

## Como rodar localmente (testado em 04/11/2026: Node 22.23.4 e npm 10.9.9)

```bash
cd solution/app
npm install --legacy-peer-deps   # veja a observação abaixo
npm run dev                      # o endereço local aparece no terminal
npm test                         # teste automático do projeto
npm run build                    # compilação de produção
```

**Observações:**
- **`npm install` sem `--legacy-peer-deps` falha** nessa versão do npm, com o erro interno `Cannot read properties of null (reading 'edgesOut')` na resolução de dependências pares. Com a opção, foram instalados 509 pacotes em 18 s. O projeto também traz o `bun.lock` do Lovable, e `bun install` é a forma nativa dele, mas **não foi testada**.
- `npm run build` gera uma versão para Cloudflare Workers (a hospedagem do Lovable) em `.output/`. O comando `vite preview` **não** serve esse formato (devolveu erro 500). Para avaliar a versão de produção, use o link publicado.

## Testes da tela
- **Teste de ponta a ponta com cliques reais:** `process-log/analises/fase4_teste_app.py`. São 29 verificações comparadas com o arquivo do motor, e o resultado está em `process-log/analises/resultados/fase4_teste_app_local.txt`. Para rodar:
  ```bash
  pip install playwright && playwright install chromium
  python process-log/analises/fase4_teste_app.py http://127.0.0.1:5173 solution/motor/saida/deals_priorizados.json process-log/prints
  ```
- **Testes na versão publicada,** pelo navegador do app Claude: `process-log/analises/resultados/fase3d_testes_tela.md`.
