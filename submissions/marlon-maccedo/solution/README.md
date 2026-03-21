# Submissão — monorepo (pnpm)

## Railway com repositório Git (GitHub)

A **raiz do repositório do desafio** não contém `package.json` nem apps. Se cada service apontar para essa raiz, o **Railpack** não encontra Node e falha com *“could not determine how to build”*.

### Obrigatório em cada service

1. **Root Directory** (Settings → Build → Root Directory):  
   `submissions/marlon-maccedo/solution`  
   *(troque `marlon-maccedo` pelo nome da pasta da sua submissão no fork)*  

   **Isso não faz todos os services virarem o Portal.** O Root Directory é só o **contexto do monorepo** (onde estão `package.json`, `packages/`, `apps/`). Pode ser **o mesmo caminho em todos** os services.

2. **Builder:** **Dockerfile** (evite Railpack/Nixpacks na raiz errada).

3. **Railway Config File** (Settings → **Config file path** / *Railway Config File*):  
   O arquivo `railway.toml` **na raiz de `solution/` foi removido de propósito** — um único arquivo ali fazia **todos** os services herdarem o mesmo `dockerfilePath` (ex.: Portal).  
   Na documentação oficial: *“The Railway Config File does not follow the Root Directory path”* — use o caminho **a partir da raiz do repositório Git**, por exemplo:

   | Service | Config file path (repo root →) |
   |--------|--------------------------------|
   | Portal | `submissions/marlon-maccedo/solution/apps/portal/railway.toml` |
   | Churn | `submissions/marlon-maccedo/solution/apps/churn-dashboard/railway.toml` |
   | Lead Scorer | `submissions/marlon-maccedo/solution/apps/lead-scorer/railway.toml` |
   | Social | `submissions/marlon-maccedo/solution/apps/social-dashboard/railway.toml` |
   | Support | `submissions/marlon-maccedo/solution/apps/support-triage/railway.toml` |

   Cada um desses arquivos já define `dockerfilePath` relativo ao **Root Directory** (`apps/.../Dockerfile`).

   **Alternativa:** não usar Config File e definir só o **Dockerfile path** no painel (mesmos caminhos da coluna “Dockerfile” acima, relativos a `solution/`).

### Variáveis e deploy local

- Variáveis de ambiente: ver `.env.example` na raiz deste monorepo.
- Deploy via CLI a partir desta pasta: scripts em `scripts/railway-deploy-service.sh` e `pnpm railway:deploy:*`.
