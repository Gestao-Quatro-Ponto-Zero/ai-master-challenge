# Submissão — Daniel Fonseca — Challenge 002 (Redesign de Suporte)

## Sobre mim

- **Nome:** Daniel Fonseca
- **LinkedIn:** [danielcoelhof](https://www.linkedin.com/in/danielcoelhof/)
- **Challenge escolhido:** 002 — Redesign de Suporte

**Ver funcionando:** app em produção em https://triagem-case-ai-master-case-g4.vercel.app · vídeo (não listado): https://youtu.be/pLQ0Yh6tb64

---

## Executive Summary

O Dataset 1 tem 8.469 tickets, e nenhuma variável (canal, prioridade, tipo, assunto ou produto) muda de forma significativa o tempo, a satisfação ou a taxa de resposta. O gargalo mensurável é transversal: 33,3% dos tickets estão sem primeira resposta e 34,0% aguardam o cliente. A proposta é uma triagem com IA em 3 caminhos (Resposta automática, Revisão humana e Somente humano), medida no holdout de 9.567 tickets do Dataset 2: 31,2% seguem sozinhos com 98,8% de acerto, e RH, permissões administrativas, reembolso, cancelamento e prioridade crítica ficam sempre com pessoas. Aplicada ao suporte do Dataset 1, a triagem dá autonomia a 18,7% do volume, cerca de 806 horas de atendente e R$ 17 mil por ano com as premissas padrão. A recomendação é começar pela Revisão humana, que já alimenta a base de soluções validadas, e instrumentar a operação para medir o que hoje o dado não registra.

---

## Solução

### Abordagem

1. **Conferir o dado antes de concluir.** O brief fala em ~30 mil tickets e 3 tipos; o CSV tem 8.469 tickets e 5 tipos. O DS1 mostra sinais de dado sintético: todos os tempos caem numa janela de 27 h, 49,3% dos tickets fechados têm resolução antes da primeira resposta, o CSAT é uniforme de 1 a 5 e as resoluções são texto aleatório ([`context/data-findings.md`](context/data-findings.md)).
2. **Testar cada corte.** Cada número do diagnóstico tem p-valor e intervalo de confiança, e todos saem de scripts reproduzíveis em [`solution/analysis/`](solution/analysis/) (ADR-0003).
3. **Dar a cada dataset o seu papel.** O DS2 mede a IA (classificação e casos parecidos); o DS1 dimensiona a operação (volume, elegíveis e custo). Os dois se cruzam pelo papel, sem join por id (ADR-0009).
4. **Medir antes de escolher o classificador.** TF-IDF, kNN com embeddings, RAG ajustado, busca híbrida, LLM zero-shot e RAG + LLM, todos no mesmo holdout (ADR-0010).
5. **Construir o fluxo de verdade** (Supabase + n8n + OpenAI) e um app público que mostra o diagnóstico, o ROI e a triagem rodando ao vivo (ADR-0014 e ADR-0015).

### Resultados / Findings

**Diagnóstico operacional (DS1)**

| Pergunta do challenge | Resposta com o dado |
|---|---|
| Onde o fluxo trava? | 33,3% dos tickets estão sem primeira resposta e 34,0% aguardam o cliente. Nenhum canal, prioridade, tipo, assunto ou produto difere com p < 0,05. |
| O que impacta a satisfação? | Nenhuma variável testada. CSAT médio 2,99 (IC 95% 2,94–3,04); um modelo com 70 variáveis explica 2,1% da variação. O ranking por combinação vai de 2,29 a 3,57, com p = 0,50 no teste conjunto. |
| Quanto se desperdiça? | O ganho recuperável vem da automação: 18,7% do volume, ~806 h e ~R$ 17 mil por ano (premissas abaixo). |

O CSAT existe só para os 32,7% de tickets fechados. Os 67,3% sem resposta ou parados são os candidatos mais prováveis à insatisfação e ficam sem medida (viés de sobrevivência, tese registrada na ADR-0003).

**Proposta de automação (DS2 + DS1)**

```
ticket → embedding → voto dos 50 casos parecidos (pgvector) → regras → caminho
  ├─ Resposta automática: confiança ≥ 0,9, categoria não sensível e solução validada da categoria → o LLM adapta a solução
  ├─ Revisão humana: rascunho do LLM na fila; a aprovação vira solução validada e a base aprende
  └─ Somente humano: RH, permissões administrativas e termos de RH/jurídico → nota interna e alerta no Slack
```

| Caminho | Holdout DS2 (9.567 tickets) |
|---|---|
| Resposta automática | 31,2% dos tickets, 98,8% de acerto da categoria |
| Revisão humana | 28,4% |
| Somente humano | 40,5% |

- **O que não automatizar:** RH, permissões administrativas, reembolso, cancelamento, prioridade crítica e textos com termos de RH ou jurídico. No DS1, reembolso, cancelamento e prioridade crítica somam 55,6% do volume, por isso o ROI parte dos 44,4% elegíveis.
- **Classificador:** o RAG acerta 82,8% e o TF-IDF 86,9%. Escolhi o RAG porque ele mostra ao atendente os casos que sustentam cada decisão, aprende com a Revisão humana e fica simples de manter no n8n (ADR-0010). O LLM sozinho acerta 43%, e sua confiança declarada não serve como critério: com confiança ≥ 0,9, acerta 62%. O LLM fica só com a redação.
- **ROI:** 44,4% elegíveis × 42,2% de autonomia entre os não sensíveis = 18,7% de automação. Com 30 mil tickets por ano (brief), 8,6 min por ticket (MetricNet/HDI) e R$ 21,30 por hora (CAGED, CBO 4223-20, com encargos): ~806 h, ~R$ 17 mil por ano e 0,41 atendente em tempo integral. As quatro premissas são editáveis no app ([`docs/premissas-de-custo.md`](docs/premissas-de-custo.md)).

**Protótipo funcional**

- **App (Vercel):** Painel (Diagnóstico, ROI e Operação), Tickets (triagem ao vivo, fila de revisão e conversa por caminho) e Como foi feito (Proposta, Decisões e Condução).
- **n8n (4 fluxos):** triagem, aprovação na fila, keep-alive do Supabase e monitor de uso que só alerta ([`docs/n8n-flows.md`](docs/n8n-flows.md); JSON em [`solution/n8n/`](solution/n8n/)).
- **Supabase:** pgvector com 47.837 embeddings em `halfvec` 512. No banco, o voto bate com o cálculo local em 99,8% das categorias; latência p50 de 64 ms.
- **Custo medido em produção:** US$ 0,0006 a 0,0014 por triagem.

### Recomendações

1. **Instrumentar a operação antes de decidir por canal ou prioridade.** Registrar a abertura do ticket, o tempo de manuseio e uma pesquisa de satisfação também para quem não teve resposta. Com isso o diagnóstico passa a ter tempo real de fila e o CSAT deixa de ver só os casos fechados.
2. **Começar pela Revisão humana.** Cada rascunho aprovado vira solução validada e amplia a Resposta automática da categoria. A automação cresce na velocidade da validação humana.
3. **Manter o Somente humano fixo** para RH, permissões administrativas, reembolso, cancelamento e prioridade crítica, com a lista de bloqueio estreita (0,2% de falsos positivos no nível automático).
4. **Acompanhar três números por semana:** acerto da Resposta automática, taxa de rascunhos aprovados sem edição e tickets sensíveis que chegaram ao caminho automático.

### Limitações

- O DS1 é sintético. O diagnóstico mostra a ausência de sinal e as premissas de custo vêm de benchmarks com fonte.
- O DS2 vem sem resoluções. A base começa com um playbook-semente de 14 soluções em 6 categorias, escrito com a IA e revisado por mim, e cresce pela Revisão humana.
- No holdout, 15 tickets rotulados como sensíveis chegariam à Resposta automática. A lista de bloqueio pega 1 deles; os demais têm pouco conteúdo sensível e parecem ruído de rótulo do DS2.
- O app é público e sem login, com limites por IP e um monitor que só alerta. O Slack é simulado na interface, porque o projeto não tem workspace; o nó Slack fica desativado no n8n.

---

## Process Log — Como usei IA

> Narrativa por sessão em [`process-log/process-log.md`](process-log/process-log.md), 47 registros de erro e julgamento em [`process-log/judgment-log.md`](process-log/judgment-log.md) e 15 decisões com a origem de cada uma em [`docs/decisions/`](docs/decisions/).

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| Claude Code (Opus 5.5, app desktop) | Análise dos dados, testes estatísticos, avaliação dos classificadores, ADRs, PRD, app e documentação |
| MCPs do projeto (`supabase-g4`, `vercel-g4`, `n8n-g4`) | Migrations e consultas no Supabase, deploy na Vercel, construção e teste dos fluxos n8n, isolados das contas pessoais |
| Sessões paralelas do Claude Code | Duas frentes do app em worktrees separados (Painel e Tickets) e uma sessão para as conferências pelos MCPs |
| OpenAI API | Embeddings (`text-embedding-3-small`) e redação das respostas (`gpt-5.4-mini`) |

### Workflow

1. **Estrutura antes do código.** `AGENTS.md` como fonte única para qualquer agente, `context/STATE.md` para o handoff entre sessões e o protocolo de registrar ADR, process log e judgment log em cada sessão (ADR-0001).
2. **Dados (sessão 01).** Perfil dos datasets, testes de significância, cortes do diagnóstico e pesquisa das premissas de custo com conferência na fonte primária.
3. **Classificador (sessão 01).** Todos os métodos medidos no mesmo holdout; escolhi o RAG e a IA mediu o custo da escolha.
4. **Fluxos n8n (sessão 02).** Aprovei o rascunho nó a nó antes da construção; a IA testou ponta a ponta nos 3 caminhos e ativou com o meu OK.
5. **App (sessões 02 e 03).** PRD fechado em duas rodadas, base construída numa sessão e duas frentes em paralelo, depois integração, deploy, monitor de uso e a minha revisão em produção.
6. **Conferência (sessão 04).** Uma sessão lateral com os MCPs conferiu o Supabase e os 4 fluxos contra o JSON versionado.

### Onde a IA errou e como corrigi

- **ROI inflado (#37):** a primeira ponte do ROI dividia pelos tickets fora do Somente humano. A própria IA achou o erro ao escrever o script reproduzível; a automação foi de 23% para 18,7% e a economia de ~R$ 21 mil para ~R$ 17 mil por ano.
- **Precisão de 100% em todas as categorias (#21):** a IA desconfiou do número e achou o bug no próprio script, que comparava a previsão com ela mesma.
- **Leitura da saída do LLM (#32):** o teste ponta a ponta mostrou que o nó da OpenAI entregava objeto e o leitor esperava texto. O caminho de segurança mandou o ticket para revisão humana; o leitor foi corrigido.
- **Stage com arquivos demais (#5 e #38):** `git add -f` levou `.venv/` e `data/` para o stage, e depois os worktrees das frentes entraram como ponteiros. A correção foi o `scripts/git-add.sh` e o `.gitignore` da pasta.
- **Embeddings reduzidos sem medir (#11):** a IA escolheu 512 dimensões por cautela. Questionei, a IA mediu 1536 × 512 e a decisão passou a seguir a medição.
- **Riscos que a IA pegou:** o n8n atribuía sozinho credenciais de outros projetos meus aos nós do case (#30 e #33), e a IA trocou pelas credenciais G4 antes de qualquer execução. A proteção padrão da Vercel bloqueava a produção (#39).

### O que eu adicionei que a IA sozinha não faria

- **Isolamento de contas e memória portável (#4):** MCPs e contas exclusivas do case, e memória no repositório para o Codex ler a mesma coisa.
- **Viés de sobrevivência no CSAT (#14):** a nota só existe para quem teve o ticket fechado. Essa tese virou limitação e recomendação de instrumentação.
- **Cruzamento por papel (#13):** relacionar DS1 e DS2 pelo id não faria sentido. Cada dataset ganhou um papel.
- **RAG como classificador (#23):** escolha consciente de 4 p.p. a menos de acerto em troca de explicabilidade, aprendizado e manutenção no n8n.
- **Solução validada adaptada pelo LLM (#26)** e Resposta automática só com solução validada da categoria.
- **Escopo do app (#35 e #40):** de 8 páginas para 3 áreas, cerca de 10 elementos cortados, e depois navegação de um nível e a tela Tickets em formato de conversa.
- **Risco do app público (#36):** levantei o risco de abuso; o resultado foram limites por IP, token por navegador e um monitor que só alerta.
- **Slack em vez de WhatsApp (#7)**, **console como validador da solução (#8)** e **keep-alive só no n8n (#47)**.

---

## Evidências

- [ ] Screenshots das conversas com IA
- [x] Screen recording do workflow: [vídeo de apresentação](https://youtu.be/pLQ0Yh6tb64)
- [ ] Chat exports
- [x] Git history (commits com o trailer de co-autoria do Claude)
- [x] Outro: narrativa por sessão ([`process-log/process-log.md`](process-log/process-log.md)), judgment log ([`process-log/judgment-log.md`](process-log/judgment-log.md)), 15 ADRs com a origem de cada decisão ([`docs/decisions/`](docs/decisions/)) e o app com a seção "Como foi feito"

**Setup:** [`docs/setup.md`](docs/setup.md) (dados, variáveis de ambiente e agentes). Arquitetura em [`docs/architecture.md`](docs/architecture.md) e PRD do app em [`docs/prd/01-prd.md`](docs/prd/01-prd.md).

---

_Submissão enviada em: [data]_
