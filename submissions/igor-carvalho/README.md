# Submissão — Igor Carvalho — Challenge 003 (Lead Scorer)

## Sobre mim

- **Nome:** Igor Carvalho
- **LinkedIn:** [preencher]
- **Challenge escolhido:** 003 — Lead Scorer (Build)

---

## Executive Summary

Construí o **G4 - Sales Priority**: uma ferramenta que o vendedor abre, vê o pipeline ordenado por valor esperado (probabilidade de ganhar x preço do produto) e entende, em cada deal, o motivo da posição e a ação sugerida. São três partes: um treinador (LightGBM com features point-in-time e backtest temporal), uma API (FastAPI com login, escopo por vendedor/manager/RevOps e score explicável) e uma tela React para o vendedor. O resultado é honesto e modesto: AUC 0,55 (IC95% 0,517 a 0,563) e lift de 1,09 nos 20% do topo, então o modelo serve como **ranking e higiene de pipeline** (deals velhos, zumbis, vendedores com pouco histórico), não como previsão de probabilidade. Recomendo usar a ferramenta para priorizar a semana e passar a registrar atividades do CRM (e-mails, reuniões, último contato), que é o dado que falta para o modelo melhorar.

---

## Solução

Código em [`solution/`](./solution): `backend/` (Python) e `frontend/` (React + TypeScript). A cronologia completa das decisões está em [`docs/workflow.md`](./docs/workflow.md).

### Como rodar

Requisitos: Python 3.10+ e Node 18+. Os dados reais do Kaggle (CC0) já estão em `solution/backend/data/`.

```bash
# 1) Backend (terminal 1)
cd solution/backend
python3 -m venv .venv && source .venv/bin/activate
make install          # dependências (pip install -e ".[api,dev]")
make train            # treina, faz o backtest e ativa o modelo (grava em artifacts/)
make api              # API em http://localhost:8000/docs

# 2) Frontend (terminal 2)
cd solution/frontend
npm install
npm run dev           # http://localhost:5173, já entra como o vendedor vicki-laflamme
```

Alternativas e testes:

| O que | Comando |
|---|---|
| Tudo em Docker (treina no build, cron diário e API) | `cd solution/backend && cp .env.example .env && ./scripts/up.sh` |
| Front sem backend (dados de exemplo) | `npm run dev:mock` |
| Testes do backend (408 rápidos) | `make test` (`make test-all` inclui dataset real e performance) |
| Testes do frontend | `npm test` e `npm run typecheck` |
| Testar a API na mão | importar `solution/backend/g4-lead-scorer.postman_collection.json` no Postman e rodar a pasta `00 Auth` primeiro |

Usuários de teste (login só por `user_key`, sem senha, por ser um MVP): `vicki-laflamme` (vendedor), `celia-rouche` (manager) e `revops` (vê tudo).

### Abordagem

1. **Problema antes do modelo.** A Head de RevOps pediu algo que o vendedor use, não um notebook. Por isso o desenho parte da tela da segunda-feira de manhã: o que ele precisa ver primeiro e por quê.
2. **Features point-in-time.** Para uma data T só entram deals fechados até T. A mesma função de features serve ao treino, à pontuação em lote e ao what-if, o que evita vazamento de futuro. As taxas históricas (vendedor, produto, vendedor x produto, últimos 90 dias) são encolhidas para a média (K = 30).
3. **LightGBM com validação temporal**, backtest em três datas (2017-08-01, 2017-09-15 e 2017-11-01) e calibração "shrink-to-base": a probabilidade só é exibida se superar uma constante em Brier.
4. **Score = percentil do valor esperado** entre os deals abertos não zumbis, mais regras de faixa por idade do deal. O vendedor vê faixas de ação, não probabilidades.
5. **Arquitetura em camadas.** Núcleo compartilhado (`lead_core`), treinador (`lead_trainer`) e API (`lead_api`); acesso a banco só por repositórios SQLAlchemy (um por entidade); esquema SQLite congelado e protegido por hash; **toda regra de negócio no backend**, e o frontend só exibe (um teste de arquitetura falha se uma regra aparecer no front).

### Lógica de scoring (critérios e por quê)

| Faixa (nesta ordem) | Regra | Ação sugerida ao vendedor |
|---|---|---|
| `prospecting` | Deal sem contato registrado | Iniciar o engajamento |
| `review` (zumbi) | Idade > 138 dias, maior duração já vista em deal fechado; sem score | Encerrar ou reativar |
| `stale_risk` | Idade > 104 dias (P90 das durações fechadas) | Decidir agora |
| `focus` (prioridade Alta) | Score >= 80 | Agendar conversa esta semana |
| `follow_up` (Média) | Score 40 a 79 | Manter o ritmo |
| `low` (Baixa) | Score < 40 | Só se for rápido |

- **Por que valor esperado e não só probabilidade:** o preço varia muito entre produtos, então ordenar por probabilidade colocaria deals pequenos no topo.
- **Confiança baixa** quando o vendedor tem menos de 30 deals fechados (o histórico dele é pouco confiável) ou quando o deal está em Prospecting.
- **Explicabilidade:** cada deal traz os 3 principais motivos (contribuição de cada feature no LightGBM, em linguagem de vendas, sempre como "associação, não causa") e a lista completa na tela de detalhe.
- **Visões por papel:** vendedor vê os próprios deals, manager vê o time, RevOps vê tudo; fora do escopo a API responde 404.

### Resultados / Findings

Dados reais: 8,8 mil oportunidades, 35 vendedores, 6 managers e 3 escritórios. 6.711 deals fechados treinaram o modelo e 2.089 deals abertos (Engaging e Prospecting) foram pontuados.

| Métrica (backtest em 3 datas, 3.071 deals de teste) | Resultado |
|---|---|
| AUC | **0,550** (IC95% 0,517 a 0,563) |
| Lift nos 20% do topo | 1,09 |
| Brier calibrado vs. constante (validação) | 0,2273 vs. 0,2317, então a calibração é útil (alpha 0,75) |
| Limiares aprendidos dos dados | duração típica 45 dias, atraso 104, zumbi 138 |
| Qualidade do código | 408 testes rápidos no backend, 8 arquivos de teste no front, complexidade média A (radon) |

Leituras honestas dos números:

- O sinal é fraco, mas **estatisticamente acima do acaso** (o limite inferior do IC fica acima de 0,5), e é isso que o portão de qualidade exige para promover um modelo novo.
- Os 20% do topo capturam cerca de 50% da receita realizada, mas isso vem **sobretudo do preço do produto**, não do modelo.
- Mais da metade dos deals abertos são zumbis (sem desfecho observável). Só apontar isso já é útil para a higiene do pipeline.

O que foi construído para o vendedor:

- API com 16 rotas: login, `/me`, `/meta`, `/filters`, `/deals` (filtros, abas, ordenação, paginação), detalhe do deal, feedback ("funcionou", "discordo", "ignorar"), what-if, resumo por vendedor/manager/escritório, saúde e administração (recarregar modelo, retreinar, consultar job).
- Tela React do vendedor com KPIs que filtram a lista, abas (foco, decidir, acompanhar, prospecção e revisão), detalhe com motivos, filtros por produto e busca. O protótipo original está em `solution/frontend/prototype/`.
- Treino diário (script com lock e log, agendamento por launchd ou cron) e Docker (treina no build, sobe cron e API).

### Recomendações

1. **Usar a ferramenta como ranking e como higiene de pipeline**: priorizar a faixa Foco, forçar uma decisão sobre os `stale_risk` e encerrar ou reativar os zumbis.
2. **Registrar atividades no CRM** (e-mails, reuniões, último contato). É o maior ganho potencial: hoje o modelo só enxerga vendedor, produto, preço e idade do deal.
3. **Aproveitar o feedback já coletado** (`deal_feedback`) para medir onde o vendedor discorda do score e para acompanhar o uso real.
4. **Medir o ganho em campo** com um grupo de controle (um escritório com a ferramenta, outro sem) antes de mostrar probabilidades.
5. Antes de produção: autenticação com senha ou SSO, retreino a partir do CRM e não de CSV, e as correções do plano de pendências ([`docs/PLANO_PENDENCIAS.md`](./docs/PLANO_PENDENCIAS.md)).

### Limitações

- **Poder preditivo baixo** (AUC 0,55) e poucas variáveis; sem atividades do CRM. Retreinar todo dia não garante acurácia melhor: o portão só promove o modelo novo se ele passar.
- **Login sem senha** (troca `user_key` por JWT). Senha exige uma nova versão do esquema do banco, que está congelado de propósito.
- "Adiar", "Encerrar como perdido" e "Marcar feito" ainda são locais no navegador; a API não tem essas rotas.
- Não há dados de último contato, meta ou próxima ação.
- **Leads novos do dia** entram só por CSV em `data/`; não há leitura direta de CRM ou banco.
- **Docker e o agendamento diário foram escritos, mas não executados** em ambiente real. As datas do backtest são fixas.
- Para escalar: rate limit compartilhado (hoje em memória), fila de jobs real, CI e trocar SQLite. Um code review do backend achou 6 riscos de operação, listados e priorizados no plano de pendências.

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usou |
|---|---|
| Claude (conversa principal, com agente de código) | Modelo e notebooks, backend (trainer, API, SQLite, SQLAlchemy), testes, Docker, treino diário, documentação e code review |
| Claude (conversa separada do frontend) | Refatorar o protótipo para React + TypeScript, API mock e cliente HTTP, testes do front |
| Claude Design (canvas) | Protótipo visual da tela do vendedor (v1, v2 principal e v3) e avaliação de usabilidade |
| Postman | Testes manuais da API (a coleção foi gerada a partir de uma coleção Bruno com 38 requests) |

### Workflow

1. **Entendimento e modelo (Fase A).** Defini com a IA o protocolo point-in-time, o backtest temporal e as faixas de ação antes de escrever o backend; o plano da aplicação e o contrato da API ficaram documentados.
2. **Protótipo (Fase B).** Iterei o design como "vendedor sênior": KPIs que filtram a tabela, score visível, paginação e ações rápidas. Escolhi a v2 como principal.
3. **Backend (Fases C e D).** Trainer, API, RBAC e esquema SQLite congelado, com coleção de testes rodada contra a API real e uma revisão de qualidade.
4. **Frontend (Fase F).** Conversa separada refatorou o protótipo para React com class components, API mock e cliente HTTP.
5. **Regras de negócio para o backend (Fase G).** Uma auditoria achou regras duplicadas no front; mandei mover tudo para a API e o front passou a só exibir.
6. **Operação (Fase H).** Treino diário com lock e log, e Docker que treina no build.
7. **Camada de dados e testes (Fases I e J).** SQLAlchemy com um repositório por entidade (pedido meu), e uma matriz de testes de regras de negócio com muitos casos (de 169 para 408 testes).
8. **Code review (final).** Pedi a revisão do código de ponta a ponta (SOLID, KISS, patterns e smells), sem alterar nada, para decidir o que corrigir.

Detalhes e datas: [`docs/workflow.md`](./docs/workflow.md).

### Onde a IA errou e como corrigi

- **Regras de negócio duplicadas no front.** A primeira versão do front carregava faixas, limiares, textos e totais. Percebi pela auditoria, decidi que o front não pode ter regra e a API passou a entregar `view`, `priority_level`, `suggested_action` e `confidence_reason`. Um teste de arquitetura falha se um literal de regra voltar para o front.
- **Validação contra uma cópia errada do backend.** O front foi testado contra uma cópia sem SQLAlchemy, então o resultado "verde" não valia. Tratei como válido só o que roda no servidor da minha máquina (`npm run test:integration` com a API no ar).
- **Expectativa de que retreinar todo dia melhora a acurácia.** Pedi o retreino diário para melhorar a acurácia; a IA explicou que isso não é garantido, e o portão de qualidade só promove o modelo que passa.
- **A IA revisando o código que ela mesma escreveu** achou 6 riscos reais de operação, reproduzidos em script (um erro de chave estrangeira vira "retreino em andamento", job órfão trava os retreinos, o cron e a API têm travas diferentes, segredo JWT padrão, versão ativa em duas fontes, erro 500 fora do log). Ainda não foram corrigidos; estão no plano de pendências.

### O que eu adicionei que a IA sozinha não faria

- Delimitei o escopo: só a tela v2 do vendedor vira front; as demais versões ficam apenas no protótipo.
- Defini os princípios de arquitetura: **regra de negócio só no backend**, esquema do banco congelado, e acesso a dados somente por repositórios, um arquivo por entidade, na pasta `repository/`.
- Pedi treino diário e Docker com um comando (treina no build, cron e API) e a remoção de qualquer referência a CRM na interface e na API.
- Exigi testes de regra de negócio com muitos casos de uso, em vez de só testes unitários.
- Controlei o ritmo: respostas sucintas e nada criado quando eu só queria entender ou decidir.

---

## Evidências

- [ ] Screenshots das conversas com IA (pasta `process-log/screenshots/`, ainda vazia)
- [ ] Screen recording do workflow
- [ ] Chat exports (pasta `process-log/chat-exports/`)
- [ ] Git history (commits da branch `submission/igor-carvalho`)
- [x] Narrativa escrita: [`docs/workflow.md`](./docs/workflow.md)

---

_Submissão enviada em: [preencher ao abrir o PR]_
