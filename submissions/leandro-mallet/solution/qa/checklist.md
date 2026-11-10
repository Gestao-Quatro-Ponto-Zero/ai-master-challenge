# Checklist de aceite — Challenge 003

Fontes: `challenges/build-003-lead-scorer/README.md`, `submission-guide.md`, `CONTRIBUTING.md`, `templates/submission-template.md` e `.gitignore` do repositório oficial.

Status: ⬜ não verificado · ✅ ok · ❌ falhou (detalhe em `testes.md`).

---

## 1. Git e PR (CONTRIBUTING)

| # | Item | Status |
|---|---|---|
| G1 | **Pegadinha:** o `.gitignore` oficial ignora `submissions/`. Todo arquivo da entrega entra com `git add -f`. Conferir com `git ls-files submissions/leandro-mallet` que nada ficou de fora (app, dados, process log, screenshots) | ⬜ |
| G2 | `datasets/` também é ignorado. Se o app depende dos CSVs, eles estão dentro de `submissions/leandro-mallet/` e versionados (licença CC0 permite) | ⬜ |
| G3 | Nenhum arquivo alterado fora de `submissions/leandro-mallet/` (`git diff --name-only main...submission/leandro-mallet`). Arquivos locais de sessão (`CLAUDE.md`, `CONTEXTO-SESSAO.md`, `PLANO-SESSOES.md`, `.claude/`) fora do diff | ⬜ |
| G4 | Branch `submission/leandro-mallet`; PR para `main` do repositório oficial, vindo do fork | ⬜ |
| G5 | Título exato: `[Submission] Leandro Mallet — Challenge 003` | ⬜ |
| G6 | Um PR só; atualização = push na mesma branch | ⬜ |
| G7 | Commits com autor noreply (sem e-mail pessoal) e mensagens que contam a história | ⬜ |
| G8 | Nome consistente entre pasta, título do PR e README ("Leandro Mallet") | ⬜ |

## 2. Estrutura da pasta (submission-guide)

| # | Item | Status |
|---|---|---|
| E1 | `README.md` na raiz da submissão, seguindo o template | ⬜ |
| E2 | `solution/` com o código e os dados usados | ⬜ |
| E3 | `process-log/` com `screenshots/` e `chat-exports/` preenchidos | ⬜ |
| E4 | `docs/` só se tiver conteúdo (pasta vazia não vai para o git) | ⬜ |

## 3. README da submissão (template)

| # | Item | Status |
|---|---|---|
| R1 | Sobre mim: nome, LinkedIn, challenge escolhido | ⬜ |
| R2 | Executive summary em 3–5 frases | ⬜ |
| R3 | Abordagem, Resultados, Recomendações, Limitações | ⬜ |
| R4 | Process log: tabela de ferramentas, workflow passo a passo, **onde a IA errou**, **o que eu adicionei** | ⬜ |
| R5 | Evidências marcadas (screenshots, chat export, git history) e com link para os arquivos | ⬜ |
| R6 | Data de envio preenchida | ⬜ |
| R7 | Curto ("40 páginas onde 5 resolveriam" é sinal de fraqueza) | ⬜ |

## 4. Solução funcional (README do challenge — requisitos mínimos)

| # | Item | Status |
|---|---|---|
| S1 | **Roda** seguindo só as instruções, a partir de um clone limpo, em outra máquina/pasta | ⬜ |
| S2 | Usa os **dados reais** do dataset (8.800 oportunidades, não amostra) | ⬜ |
| S3 | Tem **lógica de scoring** que não é só ordenar por valor (testar: o ranking não é igual ao ranking por `expected_value`) | ⬜ |
| S4 | O vendedor entende **por que** o deal tem score alto ou baixo (frases, não só pontos) | ⬜ |
| S5 | Filtro por vendedor, manager e região (bônus citado no brief) | ⬜ |
| S6 | Pensado para "segunda-feira de manhã": abre e diz onde focar hoje | ⬜ |
| S7 | Link público funcionando sem login, se houver deploy | ⬜ |

## 5. Documentação mínima (obrigatória)

| # | Item | Status |
|---|---|---|
| D1 | **Setup:** dependências com versão, comandos, URL | ⬜ |
| D2 | **Lógica:** critérios do score e por quê, com o número que justifica cada um | ⬜ |
| D3 | **Limitações:** o que não faz e o que precisaria para escalar (específicas destes dados, não genéricas) | ⬜ |

## 6. Process log (sem ele = desclassificado)

| # | Item | Status |
|---|---|---|
| P1 | Ferramentas de IA usadas e por quê | ⬜ |
| P2 | Como o problema foi decomposto antes de promptar | ⬜ |
| P3 | Onde a IA errou e como foi corrigido (casos concretos) | ⬜ |
| P4 | O que o Leandro adicionou que a IA sozinha não faria | ⬜ |
| P5 | Número de iterações visível (`decisoes.md` + histórico de commits) | ⬜ |
| P6 | Chat export revisado: sem token, sem e-mail pessoal, sem outros projetos | ⬜ |

## 7. Critérios de qualidade (como o G4 avalia)

| # | Pergunta do G4 | Como conferir | Status |
|---|---|---|---|
| Q1 | Funciona de verdade? | S1 executado do zero e registrado em `testes.md` | ⬜ |
| Q2 | O score faz sentido e vai além do óbvio? | `scoring/validacao.md` mostra que score alto fechou mais, em período separado do que definiu o score | ⬜ |
| Q3 | Vendedor não técnico usa e entende? | Teste como vendedor em `testes.md`, sem jargão na tela | ⬜ |
| Q4 | A tela ajuda a decidir ou só mostra dados? | Cada deal do topo tem ação (focar / requalificar / desistir) | ⬜ |
| Q5 | Outro dev mantém o código? | Estrutura clara, sem caminho absoluto (`H:\`, `C:\`), sem código morto, comentários curtos | ⬜ |
| Q6 | Supera o baseline? | Todas as armadilhas de `baseline.md` em ✅ | ⬜ |

## 8. Higiene

| # | Item | Status |
|---|---|---|
| H1 | Nenhuma menção a outras empresas, clientes ou projetos do candidato (busca por nome na pasta da submissão, com a lista de termos mantida fora do repositório) | ⬜ |
| H2 | Nenhum segredo, token, `.env` ou e-mail pessoal | ⬜ |
| H3 | Fim de linha LF em todos os arquivos de texto | ⬜ |
| H4 | Sem `node_modules`, `__pycache__`, `.venv` ou arquivos grandes desnecessários versionados | ⬜ |
| H5 | Data de referência fixa e documentada (dados terminam em 2017-12-31) | ⬜ |
| H6 | Nenhum nome de empresa ou projeto do candidato nos **chat-exports** (incluindo comandos, buscas e mensagens entre sessões citados nas conversas) nem nas **mensagens de commit** (`git log --format=%B`). Mesma lista de termos de H1, mantida fora do repositório; trocar por termo genérico antes do PR | ⬜ |

## 9. Critérios do avaliador (comentários públicos do G4)

Origem: seção "Critérios reais do avaliador" em [benchmark-prs.md](benchmark-prs.md). Itens marcados **bloqueador** reprovaram candidatos mesmo com o resto elogiado.

| # | Item | Como verificar | Status |
|---|---|---|---|
| A1 | **Hipóteses antes da IA** registradas com data, antes da análise | Arquivo no process log com as hipóteses do Leandro e o resultado de cada uma (confirmada / derrubada) | ⬜ |
| A2 | **Momentos de correção ou redirecionamento da IA**, concretos e datados | `decisoes.md` tem pelo menos 3 linhas em que a decisão do Leandro foi diferente da proposta da IA | ⬜ |
| A3 | **Insights do Leandro × insights da IA** separados | Seção no README que diz de quem veio cada achado principal | ⬜ |
| A4 | O que foi **descartado** e por quê | README ou `decisoes.md` lista hipóteses e componentes descartados, com o número | ⬜ |
| A5 | Seção curta de **steering humano** no README (10–15 linhas), legível sem abrir o transcript | Ler o README de cima a baixo | ⬜ |
| A6 | **Chat export com conteúdo** dentro do repo, não link | `process-log/chat-exports/` tem o texto das conversas; nenhum link de conversa como única evidência | ⬜ |
| A7 | **Log textual** além dos prints | Existe narrativa em texto; prints só ilustram | ⬜ |
| A8 | **Bloqueador:** nenhuma dependência ou artefato de build versionado | `git ls-files submissions/leandro-mallet` sem `node_modules`, `.venv`, `__pycache__`, `dist`, `.next` | ⬜ |
| A9 | **Bloqueador:** documentação igual ao código | Cada peso, corte e componente citado no README, em `scoring/` e na tela confere com o código (incluindo `app/COMO-RODAR.md`) | ⬜ |
| A10 | **Score testado ponta a ponta com os dados reais**: cada componente mexe no ranking | `validacao.md` mostra a contribuição de cada componente e um caso em que ele muda a ordem | ⬜ |
| A11 | **As 4 tabelas aproveitadas e o porquê de cada exclusão visível** | README tem uma tabela "atributo → testado? → resultado → onde aparece (score / contexto na tela / fora)" cobrindo accounts, products, sales_teams e sales_pipeline | ⬜ |
| A12 | Dados de conta, produto e time aparecem **como contexto na tela**, mesmo fora do score | Teste no app: o detalhe do deal mostra setor, porte, série/preço, manager e região | ⬜ |
| A13 | Data de referência = **máximo do dataset**, dita no README e na tela | README + cabeçalho do app | ⬜ |
| A14 | Solução **para usar**: código e instruções no repo, sem entrypoint falso | Seguir o COMO-RODAR de um clone limpo (ver S1) | ⬜ |
| A15 | **Insights principais no topo do README**, em poucas linhas | Executive summary com os 3–5 achados e o número de cada | ⬜ |
| A16 | **PR aberto só com tudo pronto** (prints, link publicado testado, chat export), porque a avaliação pode sair em horas | Todos os itens deste checklist em ✅ antes de abrir o PR | ⬜ |
