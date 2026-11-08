# Plano de pendências — G4 Lead Scorer

Criado em 2026-11-07. Compara o que o challenge 003 exige com o que existe hoje e lista o que falta, na ordem sugerida. Nenhum item foi implementado; cada um tem um critério de aceite verificável. Esforços são estimativas.

## Situação em relação ao challenge

| Exigência | Situação |
|---|---|
| Software que roda, com dados reais | Atendida (backend, API e tela do vendedor sobre o dataset do Kaggle) |
| Lógica de scoring, e o vendedor entende o porquê | Atendida (valor esperado, faixas, motivos por deal) |
| Filtro por vendedor, manager e região (bônus) | Atendida (escopo por papel e filtros) |
| Documentação mínima (setup, lógica, limitações) | Atendida no `README.md`; faltam prints da tela e caminhos corrigidos |
| **Process log com evidências** | **Falta: `process-log/` está vazio. Sem ele a submissão é desclassificada** |
| Setup reproduzível por outra pessoa | Não verificado em máquina limpa; Docker nunca executado |
| PR somente dentro de `submissions/igor-carvalho/` | Cuidado com o `.gitignore` da raiz (item 0.3) |

## Fase 0 — Bloqueios antes do PR (cerca de meio dia)

- [ ] **0.1 Process log.** Exportar as três conversas (principal, frontend e design) para `process-log/chat-exports/`; salvar em `process-log/screenshots/` prints dos momentos citados no README (auditoria que achou regra no front, front testado contra a cópia errada, code review com os 6 riscos); opcional: gravação curta de tela. *Aceite:* um avaliador consegue seguir o README, "Onde a IA errou" e achar a evidência de cada item.
- [ ] **0.2 Dados pessoais.** Preencher LinkedIn e a data da submissão no `README.md`.
- [ ] **0.3 Git.** O `.gitignore` da raiz do desafio ignora `submissions/`, então nada da pasta entra sem `-f`, e `git add -f` na pasta inteira também adiciona `.env`, `.venv`, `node_modules` e `var/` (ignorados só pelos `.gitignore` internos). Não edite o `.gitignore` da raiz (PR que altera fora da pasta é rejeitado). Sugestão, conferindo antes do commit:
  ```bash
  git checkout -b submission/igor-carvalho
  git add -f -- submissions/igor-carvalho \
    ':!**/node_modules' ':!**/.venv' ':!**/.env' ':!**/var' ':!**/_to_delete' \
    ':!**/__pycache__' ':!**/.pytest_cache' ':!**/.ruff_cache' ':!**/dist' ':!**/*.egg-info'
  git status            # conferir: nada de .env, .venv, node_modules, .db, .tgz
  ```
  Título do PR: `[Submission] Igor Carvalho — Challenge 003`. *Aceite:* `git diff --cached --stat` lista só arquivos de `submissions/igor-carvalho/` e nenhum segredo.
- [ ] **0.4 Limpar a pasta.** Apagar `solution/_to_delete/` (3 MB de pacotes de transferência e arquivos antigos). *Aceite:* a pasta não existe.
- [ ] **0.5 Modelo no repositório.** `backend/.gitignore` ignora `artifacts/` (904 KB), mas o README do frontend diz que "o repositório já traz um modelo". Decidir: (a) versionar `artifacts/v2026.11.1` e `artifacts/CURRENT` para o avaliador rodar `make api` direto (recomendado), ou (b) manter ignorado e corrigir o README do frontend para exigir `make train`. *Aceite:* o README descreve exatamente o que acontece.
- [ ] **0.6 Caminhos antigos.** Trocar `backend/` e `frontend/` por `solution/backend` e `solution/frontend` em `docs/workflow.md`, `solution/frontend/README.md` e `solution/backend/README.md` (inclusive o exemplo de cron), e os três caminhos absolutos de `solution/backend/deploy/com.g4.lead-trainer.plist`. *Aceite:* `grep -rn "projects/g4-lead-scorer/backend" submissions/igor-carvalho` não retorna nada.
- [ ] **0.7 Validar do zero.** Clonar a branch numa pasta limpa e seguir só o README: `make install`, `make train` (anotar o tempo), `make api`, `make test`, `npm install`, `npm run dev`, `npm test` e `npm run test:integration` com a API no ar. *Aceite:* tudo passa; cada divergência vira correção no README.
- [ ] **0.8 Docker.** Executar `./scripts/up.sh` e `make docker-train`; se não der tempo, retirar a promessa do README. *Aceite:* `GET /api/v1/health/ready` responde `ok` e o log do cron aparece em `var/logs`.
- [ ] **0.9 Prints da tela.** Adicionar 2 a 3 capturas da tela do vendedor (lista, detalhe com motivos, filtros) em `docs/img/` e linkar na seção Resultados. *Aceite:* o README mostra a ferramenta funcionando sem precisar rodá-la.

## Fase 1 — Riscos de operação (cerca de 1 dia)

Achados do code review do backend (relatório completo: `docs/CODE_REVIEW.md`, a exportar). Cada correção leva um teste novo e não muda banco nem API.

- [ ] **R1** `job_repository.py:29`: só tratar como `JobAlreadyRunning` a violação do índice `ux_job_one_retrain`; outros `IntegrityError` sobem como erro. *Aceite:* criar job com `requested_by` inexistente não devolve 409 "já existe retreino".
- [ ] **R2** `services/jobs.py`: no startup, marcar jobs `queued` e `running` antigos como `failed`; adicionar `timeout=` ao `subprocess.run`. *Aceite:* reiniciar a API no meio de um treino não bloqueia o próximo `POST /admin/retrain`.
- [ ] **R3** `run_daily.sh` e `POST /admin/retrain`: uma só entrada de retreino (o cron chama a API) ou a mesma trava nos dois. *Aceite:* duas execuções simultâneas nunca treinam ao mesmo tempo.
- [ ] **R4** `settings.py`, `docker-compose.yml`, `Makefile`: recusar iniciar fora do modo dev com o segredo JWT padrão ou menor que 32 caracteres. *Aceite:* a API não sobe em modo produção com o padrão.
- [ ] **R5** `registry.py` e `store.py`: gravar o `CURRENT` primeiro e reconciliar com o banco no startup. *Aceite:* teste simulando queda entre os dois passos termina consistente.
- [ ] **R6** `main.py`: registrar no log JSON também as respostas 500, com o mesmo `request_id`. *Aceite:* um endpoint que levanta exceção gera uma linha de log com `status=500`.

## Fase 2 — Lacunas de produto

Decisões que dependem de você; as três primeiras mexem no esquema SQLite, que está congelado.

- [ ] **P1 Ações do vendedor na API: "Adiar", "Encerrar como perdido", "Marcar feito".** Hoje ficam só no navegador (`TODO(api)` no front). O `CHECK` de `deal_feedback.action` só aceita `worked`, `disagree` e `ignore`, então exige **schema v2**. Entregar: migração v2, três rotas, remover os `TODO(api)`, testes de contrato. *Aceite:* o estado sobrevive a recarregar a página e a trocar de navegador.
- [ ] **P2 Autenticação com senha ou SSO.** Exige schema v2 (coluna `password_hash`) ou OIDC. Fazer junto com P1 para uma só migração. Incluir limite de tentativas em `/auth/login` e mensagem única para usuário inexistente. *Aceite:* login sem senha deixa de funcionar.
- [ ] **P3 Motivo estruturado no feedback** (campo novo em `deal_feedback`, também schema v2).
- [ ] **P4 Fonte dos leads novos do dia.** Implementar outro `DealRepository` (a porta já existe em `lead_trainer/repository.py`): CSV incremental, banco ou CRM. *Aceite:* o treino das 02:00 enxerga os leads do dia sem editar CSV à mão.
- [ ] **P5 Último contato, meta e próxima ação.** A API não tem fonte. Definir o contrato e de onde vêm os dados; depende de P4.
- [ ] **P6 Vendedores sem usuário.** 5 vendedores do CSV não aparecem em `users` (ex.: Carol Thompson); causa não confirmada. *Aceite:* a causa documentada e todo vendedor do CSV com usuário, ou a exclusão justificada.
- [ ] **P7 Plano B de score.** Benchmark com regressão logística e fallback `MODEL_ENGINE=rules` para quando nenhum modelo passar no portão. *Aceite:* comparação de AUC e lift no `docs/`, e a API serve o fallback.
- [ ] **P8 Mapeamento do contrato para Firestore** (oferta ainda sem resposta; só se for a base escolhida).

## Fase 3 — Qualidade e escala

- [ ] **Q1 CI** (GitHub Actions): `pytest`, `ruff`, `npm test` e `npm run typecheck` a cada push. *Aceite:* o PR mostra os checks em verde.
- [ ] **Q2 Dívida de design D1 a D17** do code review: um único limiar 80/40, `StrEnum` para banda, estágio e visão, dividir `ModelBundle` e `run_training`, `ModelLifecycle`, configuração única, exceções de domínio. Ordem proposta no relatório: duplicação, tipos e estrutura. *Aceite:* `radon` sem blocos em C; os testes de contrato continuam passando.
- [ ] **Q3 Escala.** Rate limit compartilhado (hoje em memória), fila de jobs real, banco além do SQLite, container sem root e supervisão do cron.
- [ ] **Q4 Makefile carregar o `.env`** (hoje só a API o lê; o treinador não).

## Ordem recomendada

1. Fase 0 inteira (sem 0.1 a submissão cai).
2. Fase 1 (R1 a R6), porque são bugs de verdade.
3. P1 e P2 numa única migração para schema v2, se você autorizar.
4. P4 e P6, depois Q1.
5. O resto conforme a prioridade do time comercial.
