# Fork, Git, Pull Request e Railway

Este guia registra o caminho reproduzível para entregar o G4 Focus. Os comandos assumem o fork `lucas3322/ai-master-challenge`, transporte SSH e branch `submission/lucas-pardinho`.

## 1. Fork e remotes

O fork é criado no GitHub a partir de `Gestao-Quatro-Ponto-Zero/ai-master-challenge`. Para um clone novo:

```bash
git clone git@github-pessoal:lucas3322/ai-master-challenge.git
cd ai-master-challenge
git remote add upstream https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge.git
git fetch upstream
git switch -c submission/lucas-pardinho upstream/main
```

Se o repositório local e a branch já existem, não recrie nada. Verifique:

```bash
git remote -v
git branch --show-current
git status --short
```

Estado esperado:

```text
origin    git@github-pessoal:lucas3322/ai-master-challenge.git
upstream  https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge.git
branch    submission/lucas-pardinho
```

Opcionalmente, confirme a autenticação SSH. O GitHub responde com uma mensagem de autenticação bem-sucedida e encerra sem shell interativo:

```bash
ssh -T git@github-pessoal
```

`github-pessoal` é o alias já configurado em `~/.ssh/config` nesta máquina. Em outro computador, use `git@github.com:lucas3322/ai-master-challenge.git` se a chave pessoal estiver associada diretamente a `github.com`.

## 2. Validar antes do commit

Na raiz do repositório:

```bash
cd submissions/lucas-pardinho/solution
python3 analytics/pipeline.py \
  --data-dir data/raw \
  --normalized-dir data/normalized \
  --output-dir generated

python3 -m unittest discover -s analytics/tests -p 'test_*.py'

cd web
npm ci
npm test
npm run build

cd ..
docker compose up --build -d
curl --fail http://localhost:3000/api/health
docker compose down
```

Se algum script da versão final diferir, `solution/README.md` e `package.json` são a fonte de verdade. Não troque uma falha por um check manual silencioso; registre o erro e a correção.

## 3. Adicionar somente a submissão

O `.gitignore` do repositório oficial ignora `submissions/`. Portanto, o primeiro `git add` precisa ser intencionalmente forçado:

```bash
cd /caminho/para/ai-master-challenge
git add -f -- submissions/lucas-pardinho \
  ':(exclude)submissions/lucas-pardinho/solution/web/node_modules/**' \
  ':(exclude)submissions/lucas-pardinho/solution/web/.next/**' \
  ':(exclude)submissions/lucas-pardinho/solution/**/__pycache__/**'
git diff --cached --name-only
```

Revise a lista. Todos os caminhos devem começar por `submissions/lucas-pardinho/`. Depois:

```bash
git commit -m "feat: add G4 Focus lead scoring submission"
git push -u origin submission/lucas-pardinho
```

Não inclua `.env`, tokens, credenciais do Railway, arquivos do diretório pessoal ou mudanças fora da pasta da submissão.

## 4. Criar o Pull Request pedido pela G4

No GitHub, abra **Compare & pull request** e confirme:

- **base repository:** `Gestao-Quatro-Ponto-Zero/ai-master-challenge`
- **base branch:** `main`
- **head repository:** `lucas3322/ai-master-challenge`
- **compare branch:** `submission/lucas-pardinho`
- **título:** `[Submission] Lucas dos Santos Pardinho — Challenge 003`

Corpo sugerido:

```markdown
## O que foi entregue

G4 Focus: aplicação web que transforma o CRM do Challenge 003 em filas
priorizadas, com score explicável, confiança e alertas de qualidade.

## Decisões principais

- prioridade híbrida: 65% conversão, 20% acionabilidade/frescor e 15% valor;
- Prospecting separado de Engaging;
- proteções contra leakage e uso do agente fora do score principal;
- pipeline reproduzível, API, testes e Docker.

## Como avaliar

Consulte `submissions/lucas-pardinho/README.md` e execute:

    cd submissions/lucas-pardinho/solution
    docker compose up --build

App: http://localhost:3000
Health: http://localhost:3000/api/health

## Evidências

O process log narrativo, decisões, correções e matriz de verificação estão em
`submissions/lucas-pardinho/process-log/README.md`.
```

Antes de criar o PR, confira a aba **Files changed**. Se houver qualquer arquivo fora de `submissions/lucas-pardinho/`, corrija a branch antes de enviar.

## 5. Deploy no Railway via GitHub

O deploy é separado do Pull Request. Primeiro publique a branch no fork; depois conecte-a ao Railway.

1. Entre no Railway e escolha **New Project** → **Deploy from GitHub repo**.
2. Autorize o acesso ao repositório `lucas3322/ai-master-challenge` se ele ainda não aparecer.
3. Selecione o repositório. Depois, em **Service Settings** → **Source**, selecione a branch `submission/lucas-pardinho`.
4. Em **Service Settings**, configure o **Root Directory** exatamente como:

   ```text
   /submissions/lucas-pardinho/solution
   ```

5. O Railway deve detectar `Dockerfile`; mantenha o builder Dockerfile.
6. Não fixe `PORT`. O Railway injeta esse valor; a imagem já escuta em `0.0.0.0`.
7. Em **Deploy**, configure **Healthcheck Path** como `/api/health` e timeout de 120 segundos.
8. Use restart **On Failure**, com no máximo 3 tentativas, e aplique as alterações pendentes para disparar o deploy.
9. Em **Networking**, gere um domínio público.

Não use `railway.toml` neste serviço novo. O Config as Code legado foi descontinuado para novos serviços; a configuração acima fica no painel. Infrastructure as Code com `.railway/railway.ts` seria útil se o projeto crescer para múltiplos serviços, mas aumentaria o escopo deste challenge sem benefício operacional agora.

Não há banco nem segredo obrigatório nesta versão. O pipeline roda durante a construção da imagem, usando os CSVs versionados na submissão.

## 6. Validar o deploy real

Copie o domínio gerado e execute:

```bash
export G4_FOCUS_URL="https://SEU-DOMINIO.up.railway.app"
curl --fail --show-error "$G4_FOCUS_URL/api/health"
curl --fail --show-error --head "$G4_FOCUS_URL/"
```

Depois abra a interface e verifique pelo menos:

- dashboard executivo carrega sem erro;
- carteira mostra oportunidades e filtros;
- detalhe explica score, confiança e flags;
- metodologia não chama o score de previsão perfeita;
- layout funciona em desktop e viewport móvel;
- logs do Railway não mostram loop de restart.

Somente após esses checks:

1. substitua “a preencher” pela URL validada no README da submissão;
2. atualize a matriz do process log com resultado e data;
3. faça commit e push na mesma branch;
4. confirme que o deploy automático publicou o novo commit;
5. adicione a URL ao corpo do PR.

## Troubleshooting

| Sintoma | Causa provável | Verificação |
|---|---|---|
| Railway não encontra o Dockerfile | Root Directory incorreto | Deve ser `/submissions/lucas-pardinho/solution`. |
| Build web não encontra JSONs | Pipeline não rodou ou caminho de artefatos divergiu | Confira o stage `analytics` e os quatro arquivos em `generated/`. |
| Health check recebe connection refused | Servidor preso em `127.0.0.1` ou ignorando `PORT` | Confirme `HOSTNAME=0.0.0.0` e `PORT` nos logs. |
| App sobe, mas retorna 500 nas APIs | Artefatos não foram copiados para o runner | Confira `GENERATED_DATA_DIR` e o conteúdo da imagem final. |
| Repositório não aparece no Railway | App do Railway sem permissão no fork | Atualize o acesso da integração GitHub. |
| Mudanças não entram no commit | `submissions/` está ignorado no repositório oficial | Use `git add -f submissions/lucas-pardinho` e audite o staged diff. |
