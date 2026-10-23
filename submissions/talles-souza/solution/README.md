# Lead Scorer

O vendedor abre a ferramenta na segunda de manhã e tem uma pergunta: **onde eu foco hoje?** A tela inicial pergunta quem ele é e responde com os negócios abertos dele em grupos, do que mais precisa dele para o que menos precisa. Cada negócio aparece num cartão de 3 linhas: o score de 0 a 100 (se o negócio é bom: a idade dele contra o histórico e as respostas do vendedor), a próxima ação e "{produto} · US$ {preço} em jogo · ver por quê"; o porquê do score, a posição na lista, a chance e quanto deve render ficam a um clique. No topo, a soma do que os negócios abertos dele devem render. O vendedor pode responder três perguntas opcionais e aceitar ou contestar a ação. O manager acompanha a equipe num painel de métricas por filtro, só para leitura.

**Testamos 19 fatores (óbvios e derivados) com validação fora da amostra; só a idade sobreviveu (AUC 0,830).** O motor de pontos mediu cada um no histórico, com os pesos aprendidos num recorte e testados no seguinte, e só aceitou o fator que melhorou a previsão em negócios que ele não tinha visto ([`motor-de-pontos-2026-10-23.txt`](../process-log/evidencias/motor-de-pontos-2026-10-23.txt), gerado por [`motor_de_pontos.mjs`](../process-log/scripts/motor_de_pontos.mjs)):

| Fator | AUC sozinho na validação | Quanto subiria o AUC da chance | Entrou? |
|---|---|---|---|
| Idade | 0,830 | (primeiro passo) | **entrou** |
| Idade ÷ ciclo do produto | 0,821 | −0,0003 | não melhorou |
| Idade ÷ ciclo do vendedor | 0,805 | −0,0020 | não melhorou |
| Vendedor | 0,569 | −0,0329 | não melhorou |
| Gerente | 0,548 | −0,0635 | não melhorou |
| Escritório | 0,548 | −0,0745 | não melhorou |
| Perdas anteriores da conta | 0,538 | +0,0011 | não melhorou |
| Funcionários da conta | 0,536 | +0,0039 | não melhorou |
| Receita da conta | 0,535 | −0,0031 | não melhorou |
| Preço ÷ receita da conta | 0,530 | +0,0016 | não melhorou |
| Carga do vendedor | 0,513 | −0,0237 | não melhorou |
| Ganhos anteriores da conta | 0,511 | −0,0040 | não melhorou |
| Setor | 0,505 | −0,0050 | não melhorou |
| Série | 0,500 | 0,0000 | não melhorou |
| Conta tem empresa-mãe | 0,500 | 0,0000 | não melhorou |
| Taxa de ganho da conta | 0,499 | −0,0049 | não melhorou |
| Produto | 0,496 | −0,0096 | não melhorou |
| Estágio | 0,500 | 0,0000 | n pequeno: no replay, todo aberto já tinha começado |
| Conta já comprou | 0,500 | 0,0000 | n pequeno: no corte, toda conta com dado já tinha comprado |

**Três coisas separadas: o score diz se o negócio é bom; o lugar na tela diz por onde começar; o valor diz quanto está em jogo.** O número do cartão ("Score 61") é a qualidade do negócio: a chance de fechar da faixa de idade dele, comparada com a melhor faixa (que vale 100), mais as respostas do vendedor às 3 perguntas (+10 por "Sim", −15 por "Não"; esses pesos são heurística declarada, porque o histórico não tem essas respostas). O lugar na tela é o grupo (Foque agora, Siga no ritmo, Aborde primeiro, Nutrição) e, dentro dele, o que há a ganhar (a chance × o preço de tabela). O preço aparece à parte ("US$ 4.821 em jogo") e não entra no score. Por isso um negócio do Foque agora pode estar no topo da tela com score 41: está ali porque a chance dele está caindo, não porque é melhor que o do Siga no ritmo (90). Detalhes em [Lógica](#lógica).

Usa os dados reais do desafio (as 4 tabelas do CRM, 8.800 oportunidades) e roda num comando.

Documentação técnica em [`docs/`](docs/): [arquitetura](docs/arquitetura.md), [contextos](docs/contextos/), [decisões (ADRs)](docs/adr/), [resiliência](docs/resiliencia.md), [segurança](docs/seguranca.md) e [runbook](docs/runbook.md).

---

## Setup

### O que precisa

| Ferramenta | Versão | Para quê |
|---|---|---|
| Node.js | 22.18 ou mais nova (`.node-version`: 22.18.0; `engines` do `package.json`) | tudo |
| npm | 10.9 ou mais novo (`packageManager`: npm@10.9.3) | instalar e rodar |
| uv | qualquer recente (opcional) | testes da camada de dados e regenerar o `deals.json` |
| Chromium do Playwright | opcional | só para `npm run test:e2e` |

O `data/deals.json` (as 4 tabelas já juntas) **vem no repositório**, com o `data/deals.json.sha256` ao lado. Não precisa baixar nada do Kaggle para rodar.

### Rodar

Todos os comandos na pasta `solution/`.

```bash
npm install
npm start
```

Abra **http://localhost:8787**. O `npm start` constrói a web e sobe a API servindo app + API na mesma porta. Depois do build, o log confirma com a linha `Lead Scorer em http://localhost:8787 (app + API)`, seguida do total de deals, da data de referência e do começo do SHA-256 conferido. A saúde fica em `http://localhost:8787/health`.

Outra porta: `PORT=8799 npm start` (no PowerShell: `$env:PORT=8799; npm start`).

Para desenvolver, com recarga automática:

```bash
npm run dev      # web em http://localhost:5173 (repassa /api e /health) + API em 8787
```

Se a linha `[api] Lead Scorer em …` não aparecer, suba os dois em terminais separados (ver [runbook](docs/runbook.md#npm-run-dev-sem-a-api)).

### Banco compartilhado (opcional)

Sem configuração, respostas e decisões ficam no navegador de cada vendedor e na memória da API. Para que valham em qualquer aparelho e cheguem ao painel da equipe, a API usa um Postgres pela variável de ambiente **`DATABASE_URL`**: a string de conexão de um papel que só lê `deals`, `vendedores` e `metadados` e só lê e acrescenta em `respostas` e `decisoes`, no schema `lead_scorer` (ver [ADR 0009](docs/adr/0009-banco-com-papel-restrito.md)). A URL nunca vai para o código nem para o repositório.

```bash
DATABASE_URL='<string de conexão>' npm start   # PowerShell: $env:DATABASE_URL='<…>'; npm start
```

O log da partida diz de onde vieram os negócios (`do banco compartilhado` ou `do deals.json`) e onde ficam as respostas. A API só usa os negócios do banco se o metadado dele (`sha256_deals_json` e `formato`) bater com o `deals.json` embarcado. Se o banco cair, ela continua com o `deals.json` e grava na memória.

### Deploy na Vercel (forma A: web estática + API como função)

```bash
npm run build        # web (apps/web/dist) + saída da Vercel em .vercel/output (estático + função)
npm run test:funcao  # sobe a função construída localmente e confere /health, a fila e o 404
```

O `vercel.json` manda `/api/*` e `/health` para a função e o resto para o estático (as mesmas rotas vão em `.vercel/output/config.json`). Na Vercel, a única variável é `DATABASE_URL`, opcional como acima. O `npm start` local continua servindo app + API numa porta só. Detalhes e o que não foi verificado: [ADR 0010](docs/adr/0010-deploy-a-vercel.md).

### Testar

```bash
npm test         # fronteiras + typecheck + lint + testes de unidade e integração + camada de dados
npm run test:e2e # ponta a ponta no navegador, com vídeo de cada fluxo em e2e/videos/
```

- `npm test` roda, nesta ordem: a checagem de fronteiras entre contextos (`scripts/checar-fronteiras.mjs`), o typecheck, o lint, os testes do domínio (106), da API (65, mais 3 de integração com o banco que só rodam com `DATABASE_URL`) e da web (86), e os testes da camada de dados (11, em Python pelo uv). Contagens da última execução nesta máquina. Sem uv, os testes de dados são pulados com aviso; sem o CSV do Kaggle (variável `CRM_DADOS`), o pytest marca os de contagem como pulados. Nenhum teste precisa de banco; os de integração gravam dentro de uma transação desfeita (ROLLBACK).
- `npm run test:e2e` sobe o app com `npm start` na porta 8787 (`E2E_PORTA` muda) e grava um vídeo por fluxo em `e2e/videos/`. Na primeira vez: `npx playwright install chromium`.

### Regenerar o `deals.json`

Só se quiser refazer a junção a partir do CSV original ([CRM Sales Predictive Analytics](https://www.kaggle.com/datasets/agungpambudi/crm-sales-predictive-analytics), CC0):

```bash
uv run --no-project --python 3.12 --with pandas==3.1.0 python -X utf8 data/preparar_dados.py <pasta-com-os-4-csv> [saida.json]
```

Grava o JSON (formato 2: os deals das 4 tabelas juntas e o time de vendas inteiro, os 35 de `sales_teams.csv`) e o `.sha256` ao lado. Sem `saida.json`, sobrescreve `data/deals.json`. O resultado é determinístico: a regeneração conferida nesta máquina deu o mesmo SHA-256 do arquivo versionado (`cd205caa…`).

---

## Lógica

### A pergunta e a data de "hoje"

A tela "Onde focar hoje" responde à pergunta do vendedor com os negócios abertos dele (Prospecting e Engaging). Na entrada, "Quem é você?" lista o time inteiro, os 35 vendedores de `sales_teams.csv`, agrupados por escritório e manager; a escolha fica no navegador. Quem não tem negócio aberto (8 dos 35: 5 nunca tiveram negócio no histórico e 3 só têm fechados) vê "Você não tem negócios abertos agora." e zero em todos os números.

**Premissa:** "hoje" é o último fechamento do dataset, **31/12/2017** (`referencia` em `data/deals.json`). O histórico termina aí; contar a idade até a data real daria anos para todos os negócios. O rodapé da tela mostra essa data.

### Os grupos da tela

A política em `packages/dominio/src/priorizacao/politica.provisoria.config.ts` põe cada negócio num bloco **pela idade** (dias desde o início, `engage_date`, até a referência):

| Grupo na tela | Idade | Ação sugerida (texto do config) |
|---|---|---|
| **Foque agora** | 41 a 60 dias | A chance está caindo: marque a próxima conversa esta semana. |
| **Siga no ritmo** | até 40 dias | Marque a próxima conversa com data. |
| **Nutrição** | acima de 60 dias | Encaminhar para nutrição (o negócio sai da fila ativa). |
| **Aborde primeiro** | sem data de início | Faça a primeira conversa: descubra quem decide e qual problema o cliente quer resolver. |

"Aborde primeiro" é um bloco próprio (`sem_inicio`): sem data não há idade, e o domínio não inventa uma.

**Por que esses limites.** A chance de fechar medida no histórico fica perto de 50% até 40 dias, cai a cada 10 dias entre 41 e 60, e quase some depois. Foque agora é a faixa em que o negócio ainda fecha, mas está decidindo: é onde o esforço do vendedor mais tende a mudar o resultado [Provável].

Na fila de todos os abertos (2.089): Foque agora 30, Siga no ritmo 27, Nutrição 1.532 (1.291 além do ganho mais longo do histórico), Aborde primeiro 500. Fonte: `packages/dominio/src/aplicacao/integracao.test.ts` e `apps/api/test/integracao.test.ts`.

**Foque vazio, Siga promovido.** Se o Foque agora de um vendedor fica vazio, os negócios do Siga no ritmo dele aparecem no Foque, pelo que há a ganhar, e o Siga some da tela dele; com o Foque não vazio, nada muda (`montarFila`). O grupo da idade de cada negócio não muda: o painel do manager conta pela idade, e a ação do negócio continua a da idade dele. Na base, isso acontece com 2 vendedores de West (Elease Gluck, 2 negócios; Hayden Neloms, 1): na tela de todos, Foque 33 e Siga 24.

### O score, a ordem da tela e o valor: três coisas separadas

O vendedor lê o número do cartão como "esse negócio é bom?". Então o score responde isso, e só isso. Por onde começar é a ordem da tela; quanto está em jogo é o preço, numa linha própria.

| | O que diz | De onde vem | Onde aparece |
|---|---|---|---|
| **Score** (0–100) | se o negócio é bom | a idade contra o histórico + as respostas do vendedor | "Score 61", no cartão e no topo do detalhe |
| **Ordem da tela** | por onde começar | o grupo, depois o valor esperado (chance × preço) | a posição do cartão; "Na sua lista: 1º de 88" só no "ver por quê" |
| **Valor** | quanto está em jogo | o preço de tabela do produto | "GTX Pro · US$ 4.821 em jogo", no cartão |

**O score** (`packages/dominio/src/score/qualidade.ts`) tem duas partes:

1. **A idade (o dado).** `round(100 × chance da faixa de idade ÷ maior chance entre as faixas)`, com as chances do motor de pontos (conversão razão). A melhor faixa vale 100. Hoje: 0–10 dias 90, 11–20 dias 100, 21–40 dias 90, 41–50 dias 61, 51–60 dias 41, 61–90 dias 15, acima de 90 dias 1.
2. **As respostas do vendedor** às 3 perguntas (quem decide, o problema confirmado pelo cliente, a próxima conversa com data): cada "Sim" soma **10**, cada "Não" tira **15**, sem resposta não muda nada. O resultado fica entre 0 e 100. **Os pesos são heurística declarada**: o histórico não tem essas respostas, então não há como medir quanto cada uma vale. Eles moram em `packages/dominio/src/score/qualidade.config.ts`, com esse aviso no próprio arquivo; trocar a escolha é trocar o config. "Não" pesa mais que "Sim" de propósito: um "não" é um fato que trava a venda, e o "sim" é o que se espera de um negócio vivo.

**Sem data de início** (os 500 em Prospecting) não há idade. Sem nenhuma resposta, o cartão diz "**Score —**" e o detalhe pede "Responda as perguntas para pontuar."; com pelo menos uma resposta, o score parte de 50 e aplica os ajustes. Em Nutrição as perguntas não valem, e o score fica só com a idade (1 a 15).

**O valor não entra no score.** O mesmo negócio com outro preço tem o mesmo score (teste em `packages/dominio/src/priorizacao/priorizacao.test.ts`; nos 1.589 abertos com data, multiplicar o preço por 10 não muda nenhum score).

**A ordem da tela** não mudou: o grupo, depois o valor esperado (chance × preço; sem data de início, o preço); empate, o preço maior, depois o mais novo e o id (`posicionarNaTela` e `compararNaLista`). O score não muda a ordem, nem as respostas: responder "Sim" sobe o score e deixa o cartão onde está. Por isso o Foque agora pode estar no topo com score menor que o do Siga no ritmo logo abaixo. Ele está ali porque a chance está caindo e é agora que o esforço conta, não porque é um negócio melhor.

Medido no `deals.json` ([`score-qualidade-2026-10-23.txt`](../process-log/evidencias/score-qualidade-2026-10-23.txt), gerado por [`score_qualidade.mjs`](../process-log/scripts/score_qualidade.mjs)), sem respostas:

- toda a Nutrição fica entre 1 e 15 (0 dos 1.532 acima de 15);
- em nenhum dos 27 vendedores com negócio aberto um Siga no ritmo fica abaixo de um Foque agora (Siga 90–100, Foque 41 ou 61);
- os 500 sem data mostram "Score —";
- dentro de cada grupo, o valor esperado nunca sobe de um cartão para o de baixo.

Os cartões de Zane Levy (West): Foque agora "Score 41 · GTX Basic · US$ 550 em jogo", em 1º de 88; Siga no ritmo "Score 90 · GTX Plus Pro · US$ 5.482 em jogo"; Nutrição "Score 15 · GTX Pro · US$ 4.821 em jogo". Um "Sim" para "quem decide" leva o primeiro a 51; os 3 "Sim", a 71; os 3 "Não", a 0. A ordem da tela continua a mesma.

**O "ver por quê"** abre o detalhe e mostra a conta, uma linha por parte:

- "Aberto há 57 dias: 22% dos negócios com essa idade fecharam (a melhor faixa fecha 52%)." A frase usa o que fechou de fato no replay; a conta usa a chance do motor, que é essa taxa suavizada. Por isso, acima de 90 dias, a frase diz 0% e o score é 1.
- Uma linha por resposta: "Decisor confirmado: +10", "Sem próxima conversa marcada: −15".
- A posição: "Na sua lista: 1º de 88 (o grupo, depois o que há a ganhar)."

O detalhe também mostra a chance absoluta ("Chance de fechar em 3 meses: 21%") e a conta da chance por fator, com os zeros e o motivo de cada um. Ao responder, a tela anuncia "O score foi de 41 para 51." junto com a ação.

**Por que o score não é a posição nem o valor.** Se o número do cartão fosse a posição na tela, um negócio sem decisor e sem problema confirmado teria nota alta só por estar no grupo de cima, e o vendedor leria "lead bom". Se o preço entrasse no score, um produto caro parado passaria um negócio vivo barato. O enunciado pede um scorer que diga ao vendedor onde focar; a nota dele precisa dizer se o negócio é bom, e o resto da tela diz por onde começar e quanto vale.

#### A ordem da tela, em detalhe

A **posição** de cada negócio na lista de abertos do vendedor segue a ordem em que a tela mostra. Primeiro vem o grupo, na ordem da tela (Foque agora, Siga no ritmo, Aborde primeiro, Nutrição), já com a promoção do Siga quando o Foque do vendedor está vazio. Dentro do grupo vem o que há a ganhar: o valor esperado (chance de fechar em 3 meses × preço de tabela) ou, sem data de início, o preço. Empate no valor: fica na frente o de preço maior, depois o mais novo, depois o id; assim cada negócio tem a sua posição (`posicionarNaTela` em `packages/dominio/src/priorizacao/index.ts`, a comparação em `packages/dominio/src/score/posicao.ts`). A lista é sempre a do vendedor do negócio, e o filtro da tela não muda a posição.

**Por que o grupo vem antes do valor.** Pelo valor esperado na lista inteira, um produto caro parado passaria um negócio vivo barato. Na lista de Zane Levy, o primeiro da Nutrição (GTX Pro, US$ 4.821, chance de 8%) ficaria acima do único negócio do Foque agora (GTX Basic, US$ 550, chance de 21%). Com o grupo na frente, o Foque dele é o 1º de 88. Na lista de Darcel Schlecht (Central, sem Foque nem Siga), o Aborde primeiro vem antes de toda a Nutrição.

**Sem data de início**, a chance não dá pra medir: o negócio entra no grupo Aborde primeiro, na ordem do preço, e "Por que está em Aborde primeiro" diz "Ainda sem primeira conversa. US$ {preço} em jogo: comece por este."

### A chance: o sistema calcula, sem peso digitado

A chance vem do motor de pontos (`packages/dominio/src/score/motor.ts`). Nenhum peso está digitado no código: ele mede tudo no `deals.json`, na carga, e os limites do método ficam em `packages/dominio/src/score/motor.config.ts`.

1. **19 fatores candidatos**, cada um medido só com o que se sabia no dia do corte. Óbvios: idade (as faixas da curva), produto, série, setor, receita e funcionários da conta (quartis das contas), vendedor, gerente, escritório e estágio. Derivados: idade ÷ mediana do ciclo dos ganhos do mesmo produto e do mesmo vendedor; ganhos, perdas e taxa de ganho da conta antes do corte; a conta já comprou; tem empresa-mãe; preço ÷ receita da conta; carga do vendedor (negócios abertos dele no corte). Contadores e razões viram quartis medidos no próprio corte. Dado que falta vira "sem dado" e vale 0.
2. **Pontos por valor** (método HubSpot, em escala log): `round(10 × ln(taxa do valor ÷ taxa geral))`. A taxa do valor soma 20 negócios fictícios na taxa geral (o peso de 10 ganhos e 10 perdas), e valor com menos de 30 negócios vale 0. A taxa geral de cada fator é a dos negócios que têm o dado: nenhum negócio sem conta fechou, então medir contra todos daria pontos a qualquer valor de conta só porque a conta existe.
3. **Replay sem olhar o futuro.** Treino: os 1.686 abertos em 30/06/2017, desfecho "ganhou até 30/09" (609 ganharam). Validação: os 2.409 abertos em 30/09/2017, desfecho "ganhou até 31/12" (559). Um teste apaga tudo o que veio depois do corte (quem começou depois some; quem fechou depois volta a estar aberto) e confere que nenhum fator de nenhum negócio muda, no arquivo real e em dados de teste.
4. **Seleção gulosa fora da amostra.** Entra primeiro o fator de maior AUC na validação, com os pontos do treino. Depois, a cada passo, entra o que mais sobe o AUC do score, se subir 0,005 ou mais, medido nos negócios que têm o dado dele. A seleção para quando nenhum sobe.
5. **Pesos finais** no recorte mais recente (abertos em 30/09 → 31/12), só com os fatores escolhidos. **Chance** = taxa base desse recorte (23,2%) × e^(pontos ÷ 10), com teto em 100% (a conversão pela razão, `conversao: 'razao'` no config); no detalhe, em %. A decomposição por fator vai junto na API (`POST /api/score/avaliar`), e a tabela do motor em `GET /api/score/motor`.

A tabela completa do que o motor mediu (cada fator, o acerto sozinho na validação e por que entrou ou não) está no começo deste README.

**AUC da chance na validação: 0,830. Só a idade: 0,830.** O motor ficou só com a idade. Os derivados da idade (contra o ciclo do produto ou do vendedor) chegam perto sozinhos (0,821 e 0,805), mas não acrescentam nada a ela; vendedor, gerente e escritório pioram a validação. Se o dado mudar, o motor refaz a medição na carga e a chance (e com ela o score) muda sozinha.

Os pontos da idade que valem hoje (recorte 30/09 → 31/12):

| Idade | 0–10 | 11–20 | 21–30 | 31–40 | 41–50 | 51–60 | 61–90 | > 90 |
|---|---|---|---|---|---|---|---|---|
| Negócios | 283 | 205 | 191 | 180 | 164 | 201 | 460 | 725 |
| Ganharam até 31/12 | 49,8% | 51,7% | 49,2% | 50,0% | 32,3% | 21,9% | 6,7% | 0% |
| Pontos | +7 | +8 | +7 | +7 | +3 | −1 | −11 | −36 |
| Chance | 47% | 52% | 47% | 47% | 31% | 21% | 8% | 1% |
| Score (só a idade) | 90 | 100 | 90 | 90 | 61 | 41 | 15 | 1 |

O "ver por quê" usa a taxa da faixa ("Ganharam até 31/12") na frase e a chance na conta do score. O "Por que está em {grupo}" do detalhe diz o mesmo em frase: até 40 dias, "{taxa}% dos negócios com essa idade fecharam"; de 41 a 60, "a chance cai rápido"; acima de 90, "nenhum negócio com mais de 90 dias fechou".

**Sem data de início** (os 500 em Prospecting): sem chance. No replay nenhum deles pode entrar (sem data não se sabe se estavam abertos no corte), então o motor não tem evidência sobre eles (`pontuarSemData: false` no config). Na tela, entram na ordem só pelo preço de tabela, e o score espera a primeira resposta do vendedor.

**A conversão.** Os pontos são log de razão de taxas, e a soma vira chance pela razão (taxa base × e^(pontos ÷ 10)). Na receita do recorte mais recente, essa conta prevê US$ 1.254.677 contra US$ 1.251.928 realizados (+0,2%). A outra conversão do motor, por log-odds, comprimia a curva (0 a 10 dias fechou 49,8% e virava chance de 38%) e previa US$ 1.077.805 (−13,9%). As duas estão no motor (`conversao` em `motor.config.ts`), e a em uso é a razão ([`motor-de-pontos-2026-10-23.txt`](../process-log/evidencias/motor-de-pontos-2026-10-23.txt), seção "calibração da receita").

A tela diz o que o score é e o que fica fora dele: "O score diz se o negócio é bom: a idade dele contra o histórico e as suas respostas. O preço fica fora do score: ele diz quanto está em jogo."

### Receita esperada: quanto deve render, e a ordem dentro do grupo

Cada negócio aberto tem uma **receita esperada** nos próximos 3 meses: a chance do motor, **sem arredondar**, × o preço de tabela do produto (`Avaliacao.esperado`, no contexto `score`). Ex.: 45 dias (chance 0,3132) e US$ 4.821 → ≈ US$ 1.510. As respostas do vendedor mudam o score, não a receita esperada: os pesos delas são heurística, e a receita fica só com o que foi medido. O preço de tabela serve de valor porque, nos ganhos, a mediana do `close_value` é 1,0 × o preço de tabela nos 7 produtos ([`process-log/evidencias/explorar-pipeline.txt`](../process-log/evidencias/explorar-pipeline.txt), seção "Valor").

| Situação | O detalhe diz |
|---|---|
| esperado de US$ 1 ou mais | "Deve render cerca de US$ {esperado} em 3 meses (estimativa pela chance)." |
| esperado que arredonda para US$ 0 | "Pela chance, quase nada deve render." |
| sem data de início | "Sem data de início: não dá pra estimar." |

O preço de tabela aparece só no detalhe do negócio, rotulado "Preço de tabela: US$ {valor}", para que os dois valores digam cada um o que medem.

- **A ordem dentro do grupo** é a receita esperada, da maior para a menor (sem data de início, o preço); empate, o preço maior; depois a idade menor e o id. Ela nunca muda o grupo (o grupo vem da idade) e não depende do score.
- **No topo da lista**: "Dos seus negócios abertos hoje, devem sair cerca de US$ {total} nos próximos 3 meses.", com o aviso "Estimativa pelo histórico: chance de fechar × preço de tabela. Não conta negócios novos que vão entrar. Não é promessa." e quantos negócios sem data ficam fora da conta. Na base inteira, o total é **US$ 69.395** ([`score-qualidade-2026-10-23.txt`](../process-log/evidencias/score-qualidade-2026-10-23.txt), seção "receita esperada"). Acima de 90 dias a chance não é zero: a suavização dá chance de 0,6% a quem nenhum negócio da faixa fechou, e por isso a Central, só com negócios antigos ou sem data, soma US$ 5.227.
- **Comissão, opcional.** O vendedor pode digitar "Sua comissão (%)"; o campo começa vazio e fica guardado no navegador. Preenchido, a tela mostra "Sua comissão estimada nesses negócios: cerca de US$ {total × %}". O dataset não tem comissão, e nenhum percentual é sugerido.

**Backtest (dentro da amostra).** Nos 2.409 negócios abertos em 30/09/2017, com os pesos finais do motor, a conta pela razão previa US$ 1.254.677 para os 3 meses seguintes; os que ganharam até 31/12/2017 fecharam US$ 1.251.928 (+0,2%; por log-odds seriam −13,9%, ver a conversão acima). Os pesos vêm desse mesmo recorte, então o teste mede coerência, não previsão. E o total não é a receita do período: negócios que entram depois também fecham. Fonte: [`motor-de-pontos-2026-10-23.txt`](../process-log/evidencias/motor-de-pontos-2026-10-23.txt).

### As perguntas do vendedor (método BANT)

O método está em `packages/dominio/src/qualificacao/metodo.provisorio.config.ts`. Dois critérios vêm do dado: **T** (tempo: a idade contra a curva) e **B** (orçamento: o preço de tabela como contexto). Três só o vendedor sabe, e viram perguntas de sim ou não, opcionais, nos blocos Foque agora, Siga no ritmo e Aborde primeiro:

| Pergunta | Critério | Se a resposta for "não", a ação vira |
|---|---|---|
| Você está falando com quem decide a compra? | A (quem decide) | Descubra quem decide a compra e marque uma conversa com essa pessoa. |
| O cliente confirmou que o problema dele é um que o produto resolve? | N (necessidade) | Pergunte qual problema o cliente quer resolver e confirme com ele que o produto resolve. Sem isso, nada do que você falar vai importar. |
| Tem próxima conversa marcada, com data? | Compromisso | Proponha uma data agora. Sem data marcada, a chance continua caindo. |

- "Não" troca a ação pela frase da pergunta (a primeira respondida com "não", na ordem do método).
- **Cada resposta mexe no score**: "Sim" soma 10, "Não" tira 15 (ver [O score](#o-score-a-ordem-da-tela-e-o-valor-três-coisas-separadas)). **Os pesos são heurística declarada**: o histórico não tem essas respostas, então não há como medir quanto cada uma mexe na chance. Por isso elas mudam o score e a ação, mas não a chance do motor, a receita esperada, o grupo nem a ordem da tela.
- **Nenhuma resposta muda o grupo.** O método nem aceita um efeito sobre o bloco: `validarMetodo` recusa. Um teste responde "Não" (e depois "Sim") às 3 perguntas dos 2.089 abertos e confere que nenhum muda de grupo (`packages/dominio/src/aplicacao/aplicacao.test.ts`). Deixar em branco não penaliza.

### Aceitar ou contestar

Toda ação sugerida pode ser aceita ou contestada na tela do negócio. Contestar exige um motivo (3 caracteres ou mais).

**Nutrição** começa recolhida, mostrando só quantos negócios há nela. O vendedor pode abrir e encaminhar um por um, ou usar "Encaminhar os {n}". A confirmação aparece na própria tela ("Encaminhar {n} negócios para nutrição?") e só "Sim, encaminhar" grava: uma decisão por negócio, todas com a mesma data. O encaminhado continua visível no grupo, marcado "Encaminhado em {data}.", com "Contestar".

Respostas e decisões ficam no navegador do vendedor e, se a API tiver o banco compartilhado, também no banco. O banco só recebe linhas novas: a resposta que vale é a mais recente de cada pergunta (ver [Banco compartilhado](#banco-compartilhado-opcional)).

### O que não decide o grupo, e por quê

O grupo vem só da idade (a política). Vendedor, conta, produto, setor e porte da empresa **não** mudam o grupo, e o motor mediu que também não entram na chance (nem, por ela, no score):

- **Fora da amostra, nenhum melhora a previsão.** Na tabela do motor acima, nenhum desses fatores sobe o AUC do score em 0,005; vendedor (−0,0329), gerente (−0,0635) e escritório (−0,0745) pioram a validação. Uma medição anterior, nos fechados, aponta o mesmo: treino nos fechados até 30/09/2017, teste nos 1.985 fechados do 4º trimestre, AUC do vendedor 0,522, da conta 0,488, do produto 0,500, do setor 0,486, dos quatro juntos 0,498 ([`process-log/evidencias/validar-sinal.txt`](../process-log/evidencias/validar-sinal.txt)).
- **Ficam com 0 ponto, à vista.** A conta de cada negócio lista esses fatores com "0 · não muda a chance no histórico", e "Como a nota funciona" mostra a tabela do motor inteira: fator, se entrou, acerto sozinho, pontos por valor e quantos negócios.

Esses campos continuam úteis como **contexto** (conta, porte e setor aparecem na tela do negócio; "sem dado de conta" é neutro) e como **filtro** (vendedor, manager, região). O produto entra pelo valor.

### As outras telas

- **O negócio por dentro** (`#/deal/<id>`): indicador, motivo, grupo, ação com aceitar/contestar, as perguntas e o contexto.
- **Novo negócio** (`#/novo-lead`): o vendedor descreve um cliente que ainda não está no sistema e vê em que grupo ele entraria. Não é guardado.
- **Acompanhar a equipe** (`#/manager`): responde a uma pergunta, **"onde meu time está perdendo dinheiro?"**, só para ler, com filtros por vendedor, manager ou região. No topo, 4 números, cada um com o rótulo e a frase do que mede:
  1. **Receita esperada do time**: soma de chance × preço dos abertos com data, "nos próximos 3 meses, sem contar negócios novos";
  2. **Foque agora sem próxima conversa marcada**: quantos e quanto está em jogo nos negócios que a tela de cada vendedor mostra em Foque agora (com o Siga no ritmo promovido quando o Foque dele está vazio) sem "Sim" para "Tem próxima conversa marcada, com data?": "vai esfriar se ninguém agir";
  3. **Pipeline parado**: quantos e quanto em jogo nos abertos acima de 60 dias (Nutrição): "inflando o pipeline";
  4. **Leads sem primeira conversa**: quantos e quanto em jogo nos abertos sem data de início: "nunca abordados".

  Sem filtro: US$ 69.395; 33 negócios com US$ 67.896 em jogo; 1.532 com US$ 3.779.334; 500 com US$ 1.073.986 (`packages/dominio/src/aplicacao/integracao.test.ts`). Embaixo, a **tabela por vendedor** com as mesmas 4 colunas e "respostas registradas" (negócios com alguma resposta ÷ negócios em que as perguntas valem), ordenada por "Foque sem próxima conversa"; os 35 vendedores aparecem, com zero quando for o caso. Sem o banco compartilhado, o painel mostra "Respostas gravadas neste navegador: {x} de {n}". Não há ranking por taxa de ganho: fora da amostra, o vendedor não prevê ganho (AUC 0,522), e um ranking assim julgaria pessoas por ruído. Não há botão de ação: quem age é o vendedor. A curva por idade e a qualidade do dado ficam em "Como a nota funciona".
- **Como a nota funciona** (`#/como-funciona`): o score é a qualidade do negócio (a idade medida + as respostas, com os pesos declarados como heurística); a ordem da tela usa o que há a ganhar, e o preço fica fora do score; abaixo, de onde vem a chance: a tabela do motor (cada fator, se entrou, o acerto sozinho, os pontos por valor e quantos negócios), o acerto da chance (AUC 0,830) ao lado do acerto só da idade, a curva por idade e os limites dos dados, com a qualidade do dado (negócios sem empresa cadastrada e sem data de início).

---

## Limitações

- **Sem login.** "Quem é você?" diz de quem é a lista; não é autenticação. Qualquer pessoa com acesso vê todos os negócios, e o banco grava o vendedor do negócio, não quem clicou. Para escalar: SSO e autorização por papel (o vendedor vê os seus, o manager o time dele). Localmente, a API sobe só em `127.0.0.1` e avisa se `HOST` aponta para fora.
- **Respostas compartilhadas exigem o banco.** Sem `DATABASE_URL`, respostas e decisões ficam no navegador de cada vendedor e na memória da API (somem quando ela reinicia): não passam de um aparelho para outro e não chegam ao painel do manager. Com o banco, ficam no schema `lead_scorer`, por um papel que só lê e acrescenta ([ADR 0009](docs/adr/0009-banco-com-papel-restrito.md)). Um "Novo negócio" nunca vai para o banco, porque não existe na tabela de negócios.
- **Sem comissão no dado.** O dataset não tem comissão. A estimativa de comissão só aparece se o vendedor digitar o percentual dele, e fica só no navegador.
- **A receita esperada é estimativa pela chance.** Vale para os negócios abertos hoje, com a chance do motor; não conta negócios que ainda vão entrar e não é previsão da receita do período. Pela conversão em uso (razão), ficou 0,2% acima do realizado no recorte mais recente, dentro da amostra.
- **Os pesos das respostas no score são escolha, não medida.** +10 por "Sim" e −15 por "Não" estão declarados no config como heurística; o histórico não tem as respostas para calibrá-los. Com respostas gravadas no banco e o desfecho dos negócios, dá para medir os pesos do mesmo jeito que o motor mede a idade.
- **Política e método trocáveis.** A política está marcada como provisória no config (`provisoria: true`): os limites 40/60 vêm da curva medida e podem ser recalibrados. O método em uso é BANT. Trocar qualquer um é trocar o arquivo de config (ver [ADR 0003](docs/adr/0003-metodo-e-politica-como-config.md)).
- **Dataset sintético e parado no tempo.** Nenhum ganho do histórico levou mais de 138 dias, e 1.291 dos 1.589 negócios em Engaging estão abertos há mais tempo que isso ([`process-log/evidencias/validar-sinal.txt`](../process-log/evidencias/validar-sinal.txt)). Esse teto pode ser do gerador dos dados, não do mercado [Provável]. "Hoje" é fixo em 31/12/2017; não há integração com um CRM vivo.
- **A região Central não tem negócio no foco.** Por região, Foque agora fica West 14, East 16, Central 0; os 500 negócios sem data de início são todos da Central (`packages/dominio/src/aplicacao/integracao.test.ts`). A tela mostra o grupo vazio com a faixa ("Nenhum negócio seu está entre 41 e 60 dias hoje.").
- **Rate limit em memória, por processo.** Com mais de uma instância (como as funções da Vercel), cada uma conta o seu. Localmente, o IP vem do socket; na Vercel, do cabeçalho `x-real-ip` que a borda dela preenche (não verificado sem deploy).
- **O timeout da API não interrompe cálculo síncrono.** A fila inteira cabe no limite de 5 s (travado em `apps/api/test/integracao.test.ts`), mas um cálculo que travasse seguraria o processo.
- **Fontes da interface vêm do Google Fonts**, sem SRI. Sem acesso a elas, a página usa as fontes de reserva declaradas nos tokens (Georgia, Segoe UI e outras do sistema).

**O que precisaria para escalar:** login com SSO e papéis, com o histórico de quem fez o quê; ingestão contínua do CRM em vez do arquivo estático, com "hoje" igual à data real; recalibrar a política com dado vivo e medir se Foque agora fecha mais que o resto; rate limit compartilhado (por exemplo, num cache) e um proxy de borda com TLS.
