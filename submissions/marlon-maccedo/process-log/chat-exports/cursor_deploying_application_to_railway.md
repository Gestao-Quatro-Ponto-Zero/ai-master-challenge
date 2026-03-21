# Deploying application to Railway
_Exported on 3/20/2026 at 23:53:24 GMT-3 from Cursor (2.5.17)_

---

**User**

Me ajude a subir essa aplicação pra Railway.
Você já tem as ferramentas disponíveis via MCP.
O ID do workspace é 8637db62-7334-47ee-b96f-35b48b706dcb
Os railway.toml já estão configurados

---

**Cursor**


Verificando as ferramentas do Railway MCP e a estrutura da aplicação.



Verificando se existe um projeto vinculado e qual é a estrutura atual:



Projeto **g4-ai-master** encontrado. Verificando se o Railway CLI está instalado e como fazer o link.



Criando `railway.toml` no root do monorepo para o portal (app principal):



Gerando o domínio público para o serviço ficar acessível:



A aplicação foi publicada no Railway. Resumo do que foi feito:

## Deploy concluído

1. **Link do projeto**  
   O diretório `submissions/bubex/` foi linkado ao projeto **g4-ai-master** (ID: `8637db62-7334-47ee-b96f-35b48b706dcb`).

2. **Configuração do Railway**  
   Foi criado o arquivo `submissions/bubex/railway.toml` no root do monorepo, apontando para o app **Portal** (landing que conecta aos outros desafios), pois os Dockerfiles exigem o monorepo inteiro.

3. **Build e deploy**  
   O deploy foi feito com sucesso; o build levou ~56 segundos.

4. **Domínio gerado**  
   URL pública:

   **https://g4-ai-master-production.up.railway.app**

---

### Próximos passos (opcional)

- **Variáveis de ambiente**: Se quiser ativar os blocos de AI insights nos dashboards (churn, support, social), configure `OPENROUTER_API_KEY` no dashboard do Railway (project → Variables).
- **Outros serviços**: Hoje está no ar apenas o **Portal**. Para publicar churn-dashboard, lead-scorer, social-dashboard e support-triage como serviços separados, é preciso configurá-los no Railway (por exemplo, criando um service por app e ajustando Root Directory e Dockerfile path).

O portal deve estar acessível na URL acima.

---

**User**

Nós temos 4 aplicações rodando em diferentes portas. Não precisamos criar um service pra cada e cruzar as URLs via env var?

---

**Cursor**


Sim — no modelo atual (vários apps Next.js, cada um com sua própria porta e Dockerfile), **faz sentido ter um service no Railway por aplicação** e **amarrar as URLs com variáveis de ambiente** (principalmente no Portal e em qualquer lugar que gere links absolutos).

### Por quê

- No Railway, **cada service** costuma ter **um processo** e **um domínio público** (ou um domínio customizado por service).
- Localmente você usa `localhost:3000`, `3002`, etc.; na nuvem isso vira **URLs diferentes** (`https://churn-xxx.up.railway.app`, etc.), não “portas no mesmo host” expostas ao browser.
- O **Portal** precisa saber para onde apontar os links — daí **`NEXT_PUBLIC_*`** (ou o prefixo que vocês já usarem) no build/runtime do Portal.

### Padrão prático

1. **Um service por app** (portal, churn, lead-scorer, social, support — são 5 se todos forem públicos; você disse 4, pode ser que um fique só interno ou agrupem mentalmente).
2. Em cada service: **root do repo** = `submissions/bubex`, **`railway.toml` / Dockerfile** = o par que vocês já têm por app (`apps/.../Dockerfile`).
3. No **Portal** (e só onde precisar): variáveis tipo  
   `NEXT_PUBLIC_CHURN_URL`, `NEXT_PUBLIC_LEAD_SCORER_URL`, etc., com as URLs geradas pelo Railway (ou domínio próprio).

### Alternativa (menos comum no seu caso)

Um **único service** com **reverse proxy** (Caddy/Nginx) roteando por path ou subdomínio — possível, mas mais operação e um único ponto de falha; para submissão com apps já separados, **vários services + env** costuma ser mais claro.

Resumindo: **sim, criar um service por app e cruzar URLs via env (no Portal) é o caminho alinhado com o que vocês já têm no monorepo.**

---

**User**

Então faça

---

**Cursor**


Implementando services separados no Railway e variáveis de ambiente no Portal. Explorando como o Portal referencia os outros apps.




Criando o script de deploy por serviço (usando os `railway.toml` existentes em cada app) e fazendo o deploy dos quatro serviços.




Detectando o problema: o Railway respeita `.gitignore` no upload, então `**/data/*.csv` e `**/data/*.json` não são enviados e o build do Next falha. Atualizando o script para usar `railway up --no-gitignore` e adicionando scripts no `package.json`.




Revertendo `--no-gitignore` (incluía `node_modules` ~200MB). Ajustando `.gitignore` para permitir upload dos dados dos apps sem versionar `node_modules`.




Fazendo deploy dos outros serviços e gerando domínios.




Segue o que foi feito:

## Implementado

### 1. **Cinco services no Railway**
- **g4-ai-master** → Portal (já existia)  
- **churn-dashboard**, **lead-scorer**, **social-dashboard**, **support-triage** → criados e com deploy concluído  

### 2. **Variáveis no Portal** (`g4-ai-master`)
| Variável | Valor |
|----------|--------|
| `URL_CHURN` | `https://churn-dashboard-production-3cb2.up.railway.app` |
| `URL_LEAD_SCORER` | `https://lead-scorer-production-f59c.up.railway.app` |
| `URL_SOCIAL` | `https://social-dashboard-production-38d8.up.railway.app` |
| `URL_SUPPORT` | `https://support-triage-production.up.railway.app` |

O Portal já usava essas envs com `dynamic = 'force-dynamic'`; o deploy foi refeito para garantir que tudo está alinhado.

### 3. **`.gitignore`**
O CLI do Railway **não envia** arquivos ignorados. Foram adicionadas exceções para os dados dos apps (`apps/churn-dashboard/data/*`, etc.), senão o `next build` no Docker quebrava (CSV/JSON ausentes). **`railway up --no-gitignore`** não é usado: isso subia `node_modules` (~200MB) e gerava **413**.

### 4. **`scripts/railway-deploy-service.sh`**
- Uso: `./scripts/railway-deploy-service.sh <app>`  
- Apps: `portal` (service **`g4-ai-master`**), `churn-dashboard`, `lead-scorer`, `social-dashboard`, `support-triage`  
- Usa `railway service <nome>` (sem TTY) e, se não passar flags, roda com **`-c`**.

### 5. **`package.json`**
Scripts: `pnpm railway:deploy:portal`, `railway:deploy:churn-dashboard`, etc.

### 6. **`.env.example`**
Documentação das variáveis do Portal para produção.

### 7. **`DEVLOG.md`**
Entrada na sessão 12.

---

**Portal:** https://g4-ai-master-production.up.railway.app  

**Opcional:** definir `OPENROUTER_API_KEY` nos services **churn-dashboard**, **support-triage** e **social-dashboard** no dashboard da Railway (insights com LLM).

Se no futuro você renomear o service `g4-ai-master` para `portal`, ajuste o `case portal)` em `scripts/railway-deploy-service.sh` (`SERVICE_NAME`).

