# Submissão — Igor Carvalho — Challenge 003 (Lead Scorer)

## Índice

- [Sobre mim](#sobre-mim)
- [Executive Summary](#executive-summary)
- [Process Log — Como usei IA](#process-log--como-usei-ia)
  - [Ferramentas usadas](#ferramentas-usadas)
  - [Workflow](#workflow)
  - [Onde a IA errou e como corrigi](#onde-a-ia-errou-e-como-corrigi)
  - [O que eu adicionei que a IA sozinha não faria](#o-que-eu-adicionei-que-a-ia-sozinha-não-faria)
  - [O que faria diferente após esse teste](#o-que-faria-diferente-após-esse-teste)
- [Solução](#solução)
  - [Como rodar](#como-rodar)
  - [Abordagem geral](#abordagem-geral)
  - [Lógica de scoring (critérios e por quê)](#lógica-de-scoring-critérios-e-por-quê)
  - [Resultados / Findings](#resultados--findings)
  - [Recomendações](#recomendações)
  - [Limitações](#limitações)
- [Evidências](#evidências)

---

## Sobre mim

- **Nome:** Igor Carvalho
- **LinkedIn:** [https://www.linkedin.com/in/igorcarvalho/]
- **Challenge escolhido:** 003 — Lead Scorer (Build)

---

## Executive Summary

Construí o **G4 - Sales Priority**: uma ferramenta que o vendedor abre, vê o pipeline ordenado pela receita esperada em 30 dias (chance de ganhar em até 30 dias x preço do produto) e entende, em cada deal, o motivo da posição e a ação sugerida.  

São três partes:
* Treinador de ML com validador
* API com FastAPI
* Tela React para o vendedor

O resultado é uma lista de prioridades que o vendedor consegue usar no dia a dia. Os 20% de deals no topo concentram 61% da receita que de fato fechou, contra 33% se o vendedor apenas seguisse o ticket mais alto. A ferramenta também aponta quais deals estão parados e deveriam ser decididos ou encerrados, o que limpa o pipeline e devolve tempo para as oportunidades que importam. O score indica onde focar, não prevê o resultado de cada deal, e é por isso que mostra a posição do deal em vez de uma probabilidade. Uma primeira versão do modelo deixava deals parados no topo da lista; um laboratório de validação (`model-lab`) detectou isso antes de chegar ao vendedor, e o modelo foi refeito. Podendo usar a ferramenta para priorizar a semana e passar a registrar atividades no CRM (e-mails, reuniões, último contato), que é o dado que mais melhoraria a precisão. Detalhes técnicos: AUC 0,67 (IC95% 0,659 a 0,682) em 30 dias.

Link do app: https://150-230-177-222.sslip.io/  

---


## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usou |
|---|---|
| Claude (conversa principal, com agente de código) | Modelo e notebooks, backend (trainer, API, SQLite, SQLAlchemy), testes, Docker, treino diário, `model-lab`, documentação e code review |
| Claude (conversa separada do frontend) | Refatorar o protótipo para React + TypeScript, API mock e cliente HTTP, testes do front |
| Claude Design (canvas) | Protótipo visual da tela do vendedor (v1, v2 principal e v3) e avaliação de usabilidade |
| Postman | Testes manuais da API (a coleção foi gerada a partir de uma coleção Bruno com 38 requests) |

### Workflow

1. **Modelo e regras do score (Fases A e B).** Defini com a IA o protocolo point-in-time, o backtest temporal e as faixas de ação antes de escrever o backend; o plano da aplicação e o contrato da API ficaram documentados.
2. **Protótipo (Fase C).** Iterei o design como "vendedor sênior": KPIs que filtram a tabela, score visível, paginação e ações rápidas. Escolhi a v2 como principal.
3. **Backend, testes e organização (Fases D a F).** Trainer, API, RBAC e esquema SQLite congelado, com coleção de testes rodada contra a API real e uma revisão de qualidade.
4. **Frontend (Fase G).** Conversa separada refatorou o protótipo para React com class components, API mock e cliente HTTP.
5. **Regras de negócio para o backend (Fase H).** Uma auditoria achou regras duplicadas no front; mandei mover tudo para a API e o front passou a só exibir.
6. **Operação.** Treino diário com lock e log, e Docker que treina no build.
7. **Camada de dados e testes (Fases I e J).** SQLAlchemy com um repositório por entidade (pedido meu), e uma matriz de testes de regras de negócio com muitos casos (de 169 para 408 testes).
8. **Code review (Fase K).** Pedi a revisão do código de ponta a ponta (SOLID, KISS, patterns e smells), sem alterar nada, para decidir o que corrigir.
9. **Validação e troca do modelo (Fase Q).** O `model-lab` mostrou que o score não condizia com a realidade (deals parados com score alto). Implementei o desafiante de receita esperada em 30 dias, com limiares por quantil e portão de qualidade com datas móveis.
10. **Refinos do front (Fases L a P).** Configuração por `.env`, heatmap do funil (depois ocultado), popup alinhado ao modelo, semana x dia e as sugestões de um vendedor externo (só a Fase 1 do plano).

Detalhes: [`process-log/workflow.md`](./process-log/workflow.md).

### Onde a IA errou e como corrigi

- **Regras de negócio duplicadas no front.** A primeira versão do front carregava faixas, limiares, textos e totais. Percebi pela auditoria, decidi que o front não pode ter regra e a API passou a entregar `view`, `priority_level`, `suggested_action` e `confidence_reason`. Um teste de arquitetura falha se um literal de regra voltar para o front.
- **Validação contra uma cópia errada do backend.** O front foi testado contra uma cópia sem SQLAlchemy, então o resultado "verde" não valia. Tratei como válido só o que roda no servidor da minha máquina (`npm run test:integration` com a API no ar).
- **Primeiro modelo com viés de sobrevivência.** Treinado só com deals fechados, ele achava que deal velho era bom e o score seguia quase só o preço. O `model-lab` provou isso com números e o modelo foi refeito com alvo de 30 dias e todos os deals abertos.
- **Popup de explicação inconsistente com o modelo.** Ele dizia que "nenhum deal passou de X dias" e que Prospecção usava um índice; perguntei se condizia com o modelo, e os textos foram corrigidos.
- **Expectativa de que retreinar todo dia melhora a acurácia.** Pedi o retreino diário para melhorar a acurácia; a IA explicou que isso não é garantido, e o portão de qualidade só promove o modelo que passa.
- **A IA revisando o código que ela mesma escreveu** achou 6 riscos reais de operação, reproduzidos em script (um erro de chave estrangeira vira "retreino em andamento", job órfão trava os retreinos, o cron e a API têm travas diferentes, segredo JWT padrão, versão ativa em duas fontes, erro 500 fora do log). Ainda não foram corrigidos; estão no plano de pendências.


### O que eu adicionei que a IA sozinha não faria

- Delimitei o escopo: dentre algumas versões, eu escolhi uma única versão do front; as demais versões ficaram apenas no protótipo.
- Defini os princípios de arquitetura: **regra de negócio só no backend**, esquema do banco congelado, e acesso a dados somente por repositórios, um arquivo por entidade, na pasta `repository/`.
- Exigi o laboratório de validação (`model-lab`) para testar o score contra a realidade antes de confiar nele.
- Decidi que a semana mostra prioridade Alta + Média e o dia só o topo, e que o índice não deve ser lido como probabilidade.
- Pedi treino diário e Docker com um comando (treina no build, cron e API) e a remoção de qualquer referência a CRM na interface e na API.
- Exigi testes de regra de negócio com muitos casos de uso, em vez de só testes unitários.
- Controlei o ritmo: respostas sucintas e nada criado quando eu só queria entender ou decidir.

### O que faria diferente após esse teste

- Tentaria fazer um plano mais focado com a IA, como eu criei 4 perfis, (Dev Backend, Dev Frontend, Data Scientist, Vendedor para auditoria), então acredito que a sequência pode ter se perdido
- Criaria um perfil de "Product Owner" para tentar criar um melhor plano de desenvolvimente, para avaliar se a solução seria melhor atendida
- Criaria o plano como "Tarefas" para ser avaliada pela "Auditoria" onde tudo que fosse feito seria auditado pelo PM e Vendedor
- Passaria um tempo maior entendendo o problema e a possível solução, como se fosse uma conversa entre PM e Vendedor, ai teria maior assertividade na criação de tudo

---

## Solução

Código em [`solution/`](./solution): `backend/` (Python), `frontend/` (React + TypeScript) e `model-lab/` (laboratório que valida se o score condiz com a realidade; não é necessário para rodar a aplicação). A cronologia completa das decisões, com o que pedi e o que a IA entregou em cada fase, está em [`process-log/workflow.md`](./process-log/workflow.md).

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
cp .env.example .env   # G4_API_URL (padrão http://localhost:8000)
npm run dev           # http://localhost:5173, já entra como o vendedor vicki-laflamme
```

Alternativas e testes:

| O que | Comando |
|---|---|
| Tudo em Docker (treina no build, cron diário e API) | `cd solution/backend && cp .env.example .env && ./scripts/up.sh` |
| Front sem backend (dados de exemplo) | `npm run dev:mock` |
| Testes do backend | `make test` (`make test-all` inclui dataset real e performance) |
| Testes do frontend | `npm test` e `npm run typecheck` |
| Validar o score contra a realidade (opcional) | `cd solution/model-lab && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/python run_lab.py` |
| Testar a API na mão | importar `solution/backend/g4-lead-scorer.postman_collection.json` no Postman e rodar a pasta `00 Auth` primeiro |

Usuários de teste (login só por `user_key`, sem senha, por ser um MVP): `vicki-laflamme` (vendedor), `celia-rouche` (manager) e `revops` (vê tudo).

### Abordagem geral

1. **Problema antes do modelo.** A Head de RevOps pediu algo que o vendedor use, não um notebook. Por isso o desenho parte da tela da segunda-feira de manhã: o que ele precisa ver primeiro e por quê.
2. **Features point-in-time.** Para uma data T só entram deals fechados até T. A mesma função de features serve ao treino, à pontuação em lote e ao what-if, o que evita vazamento de futuro. As taxas históricas (vendedor, produto, vendedor x produto, últimos 90 dias) são encolhidas para a média (K = 30).
3. **LightGBM com alvo "ganha em até 30 dias"**, treinado com snapshots semanais do pipeline que incluem todos os deals abertos (os parados entram como 0). Isso elimina o viés de sobrevivência do primeiro modelo, em que deal velho parecia bom. Backtest com datas móveis (os 4 últimos snapshots, 14 dias entre elas) e calibração só por deslocamento de nível: a probabilidade em % só é exibida se superar uma constante em Brier.
4. **Score = percentil de `p30 x preço`** (receita esperada em 30 dias) entre os deals abertos não zumbis, mais regras de faixa por idade do deal. O vendedor vê faixas de ação e um índice de posição, não probabilidades.
5. **Validei o score contra a realidade.** Defini um `model-lab` roda um backtest real e uma simulação de 7 dias com retreino; ele mostrou que o primeiro modelo acompanhava quase só o preço (correlação 0,98) e que 30 dos 62 deals com score >= 80 estavam parados.
6. **Arquitetura em camadas.** Núcleo compartilhado (`lead_core`), treinador (`lead_trainer`) e API (`lead_api`); acesso a banco só por repositórios SQLAlchemy (um por entidade); esquema SQLite congelado e protegido por hash; **toda regra de negócio no backend**, e o frontend só exibe (um teste de arquitetura falha se uma regra aparecer no front).

### Lógica de scoring (critérios e por quê)

Após alguma tentativas, verifiquei com a IA para ser mais assertivo no score e ficou definido como:

| Faixa (nesta ordem) | Regra | Ação sugerida ao vendedor |
|---|---|---|
| `prospecting` | Deal sem contato registrado | Iniciar o engajamento |
| `review` (zumbi) | Idade > P99 do ciclo fechado (127 dias nos dados atuais); sem score | Encerrar ou reativar |
| `stale_risk` | Idade > 104 dias (P90 das durações fechadas); o score só ordena e fica limitado a 79 | Decidir agora |
| `focus` (prioridade Alta) | Score >= 80 | Agendar conversa esta semana |
| `follow_up` (Média) | Score 40 a 79 | Manter o ritmo |
| `low` (Baixa) | Score < 40 | Só se for rápido |

- **Por que receita esperada e não só probabilidade:** o preço varia muito entre produtos, então ordenar por probabilidade colocaria deals pequenos no topo. O horizonte de 30 dias vem de `/meta` e é exibido na tela.
- **Limiares por quantil, não pelo máximo:** fechamentos tardios isolados (limpeza de carteira) não movem o corte de zumbi.
- **Foco da semana** = prioridade Alta + Média; "Seu dia" é o topo dessa lista.
- **Confiança baixa** quando o vendedor tem menos de 30 deals fechados (o histórico dele é pouco confiável) ou quando o deal está em Prospecting.
- **Explicabilidade:** cada deal traz os 3 principais motivos (contribuição de cada feature no LightGBM, em linguagem de vendas, sempre como "associação, não causa") e a lista completa na tela de detalhe.
- **Visões por papel:** vendedor vê os próprios deals, manager vê o time, RevOps vê tudo; fora do escopo a API responde 404.

### Resultados / Findings

Dados reais: 8,8 mil oportunidades, 35 vendedores, 6 managers e 3 escritórios. 6.711 deals fechados treinaram o modelo e 2.089 deals abertos (Engaging e Prospecting) foram pontuados.

| Métrica (modelo atual, backtest com datas móveis, protocolo `won_30d.v1`, 9.636 casos) | Resultado |
|---|---|
| AUC de "ganha em 30 dias" | **0,670** (IC95% 0,659 a 0,682) |
| Receita capturada pelos 20% do topo | **61,4%** (ordenando só pelo preço: 33,2%) |
| Acerto do top-5 de cada vendedor | 23,3% |
| Parados entre os 20% do topo | 20,3% |
| Limiares aprendidos dos dados | duração típica 45 dias, atraso 104, zumbi 127 |
| Calibração da probabilidade | não útil (Brier 0,142 vs. 0,131 da constante), então o % não é exibido |

| Do modelo antigo para o atual (`model-lab`) | Antes | Depois |
|---|---|---|
| Receita capturada no top 20% (backtest real) | 56,4% | 64,4% (no notebook; 61,4% no backend) |
| Correlação do score com a receita real em 30 dias (simulação de 7 dias) | 0,82 | 0,98 |
| Ganhos dos dias seguintes que estavam no top 20% da véspera | 2,4 de 9,6 | 4,6 de 9,6 |

O AUC de 0,55 do modelo antigo mede outra coisa ("o deal termina ganho?") e não é comparável com o 0,67 atual.

Leituras honestas dos números:

- O sinal é moderado, mas **acima do acaso** (o limite inferior do IC fica acima de 0,5), e o portão de qualidade exige isso, além de superar a ordenação só por preço, para promover um modelo novo.
- Boa parte da receita capturada no topo ainda vem do preço do produto; o modelo acrescenta cerca de 28 pontos percentuais sobre a ordenação só por preço (61% contra 33%).
- Uma parcela grande dos deals abertos é zumbi (sem desfecho observável). Só apontar isso já é útil para a higiene do pipeline.
- Sem dados de atividades (contatos, reuniões) o ganho é limitado; é o principal próximo salto.

O que foi construído para o vendedor:

- API com 16 rotas: login, `/me`, `/meta`, `/filters`, `/deals` (filtros, abas, ordenação, paginação), detalhe do deal, feedback ("funcionou", "discordo", "ignorar"), what-if, resumo por vendedor/manager/escritório, saúde e administração (recarregar modelo, retreinar, consultar job).
- Tela React do vendedor com KPIs que filtram a lista, abas (foco da semana, decidir agora, baixa prioridade, prospecção e a revisar), "Seu dia", detalhe com indicadores separados (índice, preço, receita esperada e, só se a calibração for útil, a probabilidade), tabela de fatores a favor e contra, confiança da previsão separada da completude dos dados, filtros por produto e busca. O heatmap de funil (produto x tempo) existe como componente, mas está oculto. O protótipo original está em `solution/frontend/prototype/`.
- Treino diário (script com lock e log, agendamento por launchd ou cron) e Docker (treina no build, sobe cron e API).

### Recomendações

1. **Usar a ferramenta como ranking e como higiene de pipeline**: priorizar a faixa Foco, forçar uma decisão sobre os `stale_risk` e encerrar ou reativar os zumbis.
2. **Registrar atividades no CRM** (e-mails, reuniões, último contato). É o maior ganho potencial: hoje o modelo só enxerga vendedor, produto, preço e idade do deal.
3. **Aproveitar o feedback já coletado** (`deal_feedback`) para medir onde o vendedor discorda do score e para acompanhar o uso real.
4. **Medir o ganho em campo** com um grupo de controle (um escritório com a ferramenta, outro sem) antes de mostrar probabilidades.
5. Antes de produção: autenticação com senha ou SSO, retreino a partir do CRM e não de CSV, e as correções do plano de pendências ([`docs/PLANO_PENDENCIAS.md`](./docs/PLANO_PENDENCIAS.md)).

### Limitações

- **Poder preditivo moderado** (AUC 0,67 em 30 dias) e poucas variáveis; sem atividades do CRM. A taxa de ganho em 30 dias varia muito entre janelas, por isso a probabilidade não é exibida. Retreinar todo dia não garante acurácia melhor: o portão só promove o modelo novo se ele passar.
- **Login sem senha** (troca `user_key` por JWT). Senha exige uma nova versão do esquema do banco, que está congelado de propósito.
- "Adiar", "Encerrar como perdido" e "Marcar feito" ainda são locais no navegador; a API não tem essas rotas.
- Não há dados de último contato, meta ou próxima ação.
- **Leads novos do dia** entram só por CSV em `data/`; não há leitura direta de CRM ou banco.
- **Docker e o agendamento diário foram escritos, mas não executados** em ambiente real. O backtest usa datas móveis, mas os dados vão só até 2017-12-31.
- Para escalar: rate limit compartilhado (hoje em memória), fila de jobs real, CI e trocar SQLite. Um code review do backend achou 6 riscos de operação, listados e priorizados no plano de pendências.

---

## Evidências

- [ ] Screenshots das conversas com IA
- [ ] Screen recording do workflow
- [ ] Chat exports
- [x] Git history (commits da branch `submission/igor-carvalho`)
- [x] Narrativa escrita: [`process-log/process.md`](./process-log/process.md), com o que pedi e o que a IA entregou em cada fase
- [x] Outro: screenshots do app funcionando, em [`process-log/screenshots/`](./process-log/screenshots/)
  - [Meu dia](./process-log/screenshots/pagina-01-meu-dia.png)
  - [Pipeline: foco da semana](./process-log/screenshots/pagina-02-pipeline-foco-da-semana.png)
  - [Pipeline: decidir agora](./process-log/screenshots/pagina-03-pipeline-decidir-agora.png)
  - [Pipeline: baixa prioridade](./process-log/screenshots/pagina-04-pipeline-baixa-prioridade.png)
  - [Pipeline: prospecção](./process-log/screenshots/pagina-05-pipeline-prospeccao.png)
  - [Pipeline: a revisar](./process-log/screenshots/pagina-06-pipeline-a-revisar.png)
  - [Como a prioridade é calculada](./process-log/screenshots/pagina-07-como-a-prioridade-e-calculada.png)

---

_Submissão enviada em: 08/11/2026_
