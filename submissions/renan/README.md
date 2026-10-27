# Submissão — Renan — Challenge 003 (Lead Scorer)

## Sobre mim

- **Nome:** Renan Garcia Oliveira
- **LinkedIn:** [linkedin.com/in/renan-garcia-022951127](https://www.linkedin.com/in/renan-garcia-022951127/)
- **Challenge escolhido:** 003 — Lead Scorer (Vendas / RevOps)

---

## Executive Summary

Construí a **Régua**, um sistema web que o vendedor abre na segunda-feira e sabe onde focar, por quê, e o que largar. Antes de pontuar, testei os dados: **neste CRM ninguém consegue prever ganho vs. perda** (produto, setor, porte e vendedor ficam dentro do ruído estatístico; backtest com AUC ≈ 0,5). O que dá para saber é o valor de cada deal e quais estão mortos: **nenhum dos 6.711 deals fechados levou mais de 138 dias, e 81% dos deals em Engaging já passaram disso — 64% do valor do pipeline aberto**. A Régua prioriza pelo valor esperado, tira os parados da pauta para uma fila de revisão e explica cada score com um "recibo" que fecha a conta. Um Agente Gestor (Claude) responde perguntas sobre o pipeline, restrito aos dados, e um Radar avisa o que exige ação sem ninguém perguntar.

**App:** https://regua-lead-scorer.vercel.app · **Código:** [`solution/`](./solution/) · **Process log:** [`process-log/PROCESS_LOG.md`](./process-log/PROCESS_LOG.md)

---

## Solução

### Setup

```bash
cd submissions/renan/solution
npm install
npm run dev        # http://localhost:3000
```

Requisitos: Node.js 20.9+. Os dados do Kaggle (licença CC0) já estão em `solution/data/raw/`; `npm run dev` e `npm run build` geram o dataset e a análise antes de subir o app.

| Comando | O que faz |
|---|---|
| `npm test` | 34 testes: parser, motor de score, backtest, ferramentas e rota do agente (API simulada) |
| `npm run analyze` | Exploração + backtest; regenera [`docs/FINDINGS.md`](docs/FINDINGS.md) |
| `npm run build` | Build de produção |

**Agente Gestor (opcional):** em **Configurações**, cada usuário cola a própria chave da API da Anthropic (fica só no navegador). Sem chave, todo o resto funciona, inclusive o Radar.

### Telas

| Tela | Para quê |
|---|---|
| **Hoje** | Pauta do vendedor (ou do time) ordenada por valor esperado, com a régua de dias em cada deal, indicadores e o painel da fila de revisão |
| **Pipeline** | Todos os deals abertos, com busca e filtros por vendedor, manager, escritório, produto e momento (filtros na URL) |
| **Parados** | Fila de revisão: deals abertos há mais de 138 dias, para revisar ou desqualificar |
| **Deal** | Ficha do CRM, régua de dias com marcos e o recibo do score (base + fatores = chance × preço = valor esperado) |
| **Time** | Higiene do pipeline por vendedor, **sem ranking de desempenho** (diferenças são ruído) |
| **Agente Gestor** | Radar de alertas (sem IA) + perguntas aos dados com respostas em formato de painel |
| **Metodologia** | Como o score funciona, achados, backtest e qualidade dos dados, lidos do `analysis.json` |
| **Configurações** | Chave da API do próprio usuário, modelo e esforço do agente |

### Lógica do score

```
Chance de fechar = taxa geral (63,2%)
                 → ajustada pelo tempo no pipeline (curva de sobrevivência)
                 → ajustada por vendedor, produto, setor e porte (Bayes empírico)
Valor esperado   = chance × preço de tabela
Score (0–100)    = posição do valor esperado entre os deals ativos
Parado           = aberto há mais de 138 dias (maior ciclo já fechado) → sai da pauta
```

- **Pesos aprendidos, não inventados:** o Bayes empírico zera os fatores cuja variação cabe no ruído. Hoje produto, setor e porte pesam zero, e o vendedor quase zero. Se o CRM ganhar sinal (ex.: atividades), os pesos sobem sozinhos.
- **Momento do deal**, com limites tirados do histórico: Início (até 14 dias, metade das perdas), Em andamento, Reta final (88–138 dias), Parado (138+).
- **Explicação que fecha a conta:** cada fator vira pontos percentuais que somam exatamente a chance exibida (há teste para isso).

Detalhes: [`docs/SCORING.md`](docs/SCORING.md).

### Resultados / Findings

Números reproduzíveis por `npm run analyze` ([`docs/FINDINGS.md`](docs/FINDINGS.md)).

| Achado | Número |
|---|---|
| Taxa de vitória histórica | 63,2% (6.711 deals fechados) |
| Variação por produto / setor / porte | 60–65%, dentro do ruído (após Bayes empírico: 63,2% para todos) |
| Vendedores | 55–70% bruto, mas qui-quadrado 33,3 com 29 g.l. (compatível com taxas iguais) |
| Maior ciclo já fechado | 138 dias |
| Deals em Engaging além de 138 dias | 81% (1.291 deals, 64% do valor aberto) |
| Ordenar só por preço | 47% do top 20% seriam deals parados |
| Backtest (3 cortes) | Chance com AUC ≈ 0,5; valor esperado captura ~50% da receita no top 20% vs. ~19% do acaso |
| Deals abertos sem conta | 68% (1.425 de 2.089) |
| Fim de trimestre | 80,7% de vitória no último mês vs. 52,3% nos outros (pode ser artefato; fora do score) |

### Recomendações

1. **Revisar a fila de parados agora.** São 1.291 deals e US$ 3,2 mi de valor de tabela que provavelmente não são receita. Limpar isso corrige a previsão e libera tempo, que é a primeira dor da Head de RevOps.
2. **Trabalhar a reta final toda segunda.** 190 deals entre 88 e 138 dias; 66 deles passam do limite nos próximos 14 dias (Radar).
3. **Não ranquear vendedores por taxa de vitória.** As diferenças são ruído; usar isso para coaching puniria por sorte.
4. **Registrar o que prevê fechamento.** O CRM não tem atividades, próximos passos nem motivos de perda, por isso nenhum modelo acerta. Próximo passo de produto: triagem de 1 clique na fila de parados (ainda ativo / desqualificar com motivo / fechou), exportando para o CRM. Cada triagem gera o dado que hoje falta, e o motor já está pronto para aprender com ele.
5. **Cadastrar a conta nos deals.** 68% dos deals abertos não têm conta, o que impede qualquer análise por cliente.

### Limitações

- **Dataset sintético:** os padrões, ou a falta deles, podem não refletir um CRM real.
- **A regra de "parado" não foi validada fora da amostra:** nos cortes do backtest nenhum deal tinha passado do ciclo máximo. Ela se apoia no histórico (nenhum ciclo acima de 138 dias).
- **Deals abertos usam o preço de tabela;** nos ganhos, o valor fechado fica entre 87% e 112% dele.
- **O Agente Gestor foi testado com a API simulada** (loop, ferramentas, erros), não com chamadas reais nesta entrega. A chave é do usuário, guardada no navegador; em produção o caminho seria SSO e uma chave da empresa num cofre de segredos.
- **Sem persistência:** não há banco nem login. Para escalar: conector do CRM com sync diário, banco para a triagem e para o histórico de scores, e notificação semanal (e-mail ou Slack) com a pauta de cada vendedor.

---

## Process Log — Como usei IA

Narrativa completa, fase a fase: [`process-log/PROCESS_LOG.md`](process-log/PROCESS_LOG.md). O histórico de commits da branch `submission/renan` mostra a evolução.

### Ferramentas usadas

| Ferramenta | Para que usei |
|---|---|
| Claude Code (desktop, Claude Opus 5.5) | Leitura do repositório, arquitetura, exploração dos dados, motor de score, backtest, UI, testes, docs, git |
| Skills do Claude Code | `bencium-innovative-ux-designer` (10 direções visuais), `frontend-design`, `ui-typography`, `vercel-react-best-practices`, `vercel-composition-patterns`, `web-design-guidelines`, `design-audit`, `claude-api` |
| Claude in Chrome | Fork no GitHub, download do dataset no Kaggle, verificação visual das telas |
| API do Claude (no produto) | Agente Gestor com tool use, restrito aos dados |

### Workflow

1. **Entender antes de codar:** comparei os 4 desafios, escolhi o 003 e escrevi arquitetura, hipóteses e plano com time-box antes de qualquer código.
2. **Perfilar os dados:** achei 68% dos deals abertos sem conta, o nome "GTXPro" divergente e o setor "technolgy".
3. **Testar as hipóteses antes do score:** produto, setor e vendedor são ruído; o tempo tem um limite duro de 138 dias.
4. **Score com pesos aprendidos (Bayes empírico) + backtest honesto.** Quando o backtest deu AUC ≈ 0,5, reescrevi a tese em vez de esconder.
5. **Design:** 10 direções só tipográficas e escolha minha (E + G, claro e escuro). Depois, também a meu pedido, a reconstrução como sistema (menu lateral, cards, painéis), mantendo a régua de dias como identidade.
6. **Agente Gestor:** desenho iterado comigo até virar um assistente de dados ativo, restrito ao pipeline, com a chave de cada usuário.

### Onde a IA errou e como corrigi

- **Números fora do script oficial:** a IA citou no doc uma correlação (0,10) tirada de um script exploratório. Ao mover para o `npm run analyze`, o valor real era 0,32. Regra adotada: número só vai para doc ou UI se o script reproduz.
- **`git add -f` forçou o `node_modules`** para contornar o `.gitignore` do G4, que ignora `submissions/`. Eu peguei, desfizemos, e criamos o `git-add.sh`.
- **Primeira UI "editorial demais":** seguia a direção tipográfica à risca e não parecia um sistema. Pedi a reconstrução como produto.
- **Bugs pegos por teste:** data de referência quebrando sem datas; deal duplicado na resposta do agente (caixa diferente no código); rótulo da régua colidindo; rolagem horizontal de 2 px no celular.

### O que eu adicionei que a IA sozinha não faria

- **A decisão de testar antes de pontuar e de assumir o resultado incômodo** (AUC ≈ 0,5) como tese do produto.
- **Não mostrar ranking de vendedores**, porque puniria pessoas por sorte.
- **A escolha visual** (E + G) e a exigência de que fosse um sistema de verdade.
- **As regras do agente:** nunca falar fora dos dados, ser ativo (Radar) e usar a chave de cada usuário, nunca a da empresa.
- **O contexto de quem trabalha com leads B2B:** o que importa para o vendedor na segunda de manhã é saber o que atacar e o que largar.

### Tempo

Cerca de **8h30**, acima da meta de 4–6h do G4. O excedente veio da reconstrução da interface como sistema e do Agente Gestor, que eu decidi incluir depois de avaliar o resultado. Registro por fase em [`docs/PLAN.md`](docs/PLAN.md).

---

## Evidências

- [x] Git history (commits por fase na branch `submission/renan`)
- [x] Narrativa escrita ([`process-log/PROCESS_LOG.md`](process-log/PROCESS_LOG.md))
- [x] Scripts de exploração ([`process-log/exploration/`](process-log/exploration/))
- [x] Direções de design geradas e escolhidas ([`design/`](design/))
- [x] Documentos de decisão ([`docs/`](docs/))

---

_Submissão enviada em: 27/10/2026_
