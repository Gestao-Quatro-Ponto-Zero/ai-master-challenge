# Submissão — Talles Souza — Challenge 003

## Sobre mim

- **Nome:** Talles Souza
- **LinkedIn:** [linkedin.com/in/tallessouzamartins](https://linkedin.com/in/tallessouzamartins)
- **Challenge escolhido:** 003 — Lead Scorer

---

## Executive Summary

**Para quem é: o vendedor, na segunda de manhã**, com a pergunta "onde eu foco hoje?". Ele abre a ferramenta, diz quem é e vê os negócios abertos dele em quatro grupos pela idade: **Foque agora** (41 a 60 dias), **Siga no ritmo** (até 40), **Aborde primeiro** (sem data de início) e **Nutrição** (mais de 60, recolhida); cada negócio aparece em 3 linhas: um score de 0 a 100 ("Score 61": se o negócio é bom, pela idade dele contra o histórico e pelas respostas do vendedor), a próxima ação e o produto com o que está em jogo ("US$ 4.821 em jogo", fora do score); o lugar na tela diz por onde começar (o grupo, depois a chance × o preço), e o porquê do score, a posição na lista, a chance e quanto deve render ficam a um clique. Se o Foque de um vendedor fica vazio, os negócios do Siga dele sobem para o Foque. Os grupos saem do dado: dos negócios abertos em 30/09/2017, ganharam até o fim do ano 50,2% dos que tinham até 40 dias, 26,6% dos de 41 a 60 e 2,6% dos de mais de 60 (medido no próprio histórico, dentro da amostra), enquanto vendedor, conta, produto e setor, testados fora da amostra, não separam ganho de perda (AUC de 0,486 a 0,522; 0,50 é uma moeda). Pôr o Foque (27%) acima do Siga (50%) é uma escolha, não uma medição: trabalhar primeiro o que ainda fecha mas está esfriando, já que o dataset não registra o efeito de o vendedor agir. A chance vem de um motor que testou 19 fatores, óbvios e derivados, fora da amostra e sem olhar o futuro: só a idade sobreviveu (AUC 0,830). O manager acompanha a mesma lista num painel que responde "onde meu time está perdendo dinheiro?": US$ 69.395 de receita esperada nos próximos 3 meses; 33 negócios do Foque agora, com US$ 67.896 em jogo, sem próxima conversa marcada; 1.532 parados há mais de 60 dias; 500 que nunca tiveram a primeira conversa; e uma linha por vendedor. A recomendação ao time é seguir essa fila, encaminhar à Nutrição o que passou do tempo em que negócios fecham e começar a registrar quem decide, qual é o problema do cliente e a próxima conversa com data, que é o que este CRM não tem.

---

## Solução

### Abordagem

1. **Medir antes de escolher.** Medi o sinal dos 5 datasets do processo e escolhi o 003, o único com sinal medido e com um usuário claro, o vendedor ([sessão 01](process-log/sessoes/sessao-01-escolha-do-desafio.md)).
2. **Testar o óbvio fora da amostra.** Vendedor, conta, produto e setor pareciam separar (vendedores de 55% a 70% de ganho), mas não se repetem no trimestre seguinte. A idade, sim ([sessão 02](process-log/sessoes/sessao-02-entender-o-pipeline.md)).
3. **Entender o negócio antes de desenhar a solução.** Diagnóstico da operação descrita no enunciado, com revisor adversarial, só com o que o enunciado e o dado sustentam ([sessão 03](process-log/sessoes/sessao-03-pgg-e-pmv-do-teste.md) e [sessão 04](process-log/sessoes/sessao-04-autopsia-dados-e-design.md)).
4. **Desenho, construção e verificação** em fatias verticais, com cada número da tela travado em teste e o aceite rodado pela sessão coordenadora, não pelo "terminei" de quem construiu ([sessão 05](process-log/sessoes/sessao-05-construcao-e-verificacao.md)).
5. **O sistema mede a chance, e o score explica o negócio.** Motor de pontos com replay temporal e seleção fora da amostra; score de qualidade separado da ordem da tela e do valor em jogo; painel do manager com 4 números de dinheiro em jogo ([sessão 06](process-log/sessoes/sessao-06-motor-score-e-verificacao.md)).

### O que o vendedor vê

A tela inicial pergunta "Quem é você?" (os 35 vendedores de `sales_teams.csv`, por escritório e manager) e abre **Onde focar hoje**, com os negócios abertos dele em quatro grupos, nesta ordem:

| Grupo | Idade do negócio | Ação sugerida |
|---|---|---|
| **Foque agora** | 41 a 60 dias | A chance está caindo: marque a próxima conversa esta semana. |
| **Siga no ritmo** | até 40 dias | Marque a próxima conversa com data. |
| **Aborde primeiro** | sem data de início | Faça a primeira conversa: descubra quem decide e qual problema o cliente quer resolver. |
| **Nutrição** | mais de 60 dias | Encaminhar para nutrição (sai da fila ativa). Começa recolhida; dá para encaminhar um por um ou "Encaminhar os {n}", com confirmação. |

- **Cada negócio em 3 linhas:** "**Score 61**" (se o negócio é bom: a idade dele contra o histórico e as respostas do vendedor; sem data de início e sem resposta, "Score —"), a ação e "{produto} · US$ {preço} em jogo · ver por quê". O lugar do cartão na tela diz por onde começar; o score não muda a ordem, e o preço não entra no score. O "ver por quê" abre o detalhe com a conta do score: "Aberto há 57 dias: 22% dos negócios com essa idade fecharam (a melhor faixa fecha 52%).", uma linha por resposta ("Decisor confirmado: +10") e a posição ("Na sua lista: 1º de 88 (o grupo, depois o que há a ganhar)."). Ali também ficam a chance de fechar em 3 meses e a conta por fator, com o que vale 0 e o porquê.
- **Receita esperada:** "Deve render cerca de US$ {valor} em 3 meses (estimativa pela chance)". No topo, a soma dos abertos dele, com o aviso de que não conta negócios novos e não é promessa. Um campo opcional "Sua comissão (%)" transforma o total em comissão estimada.
- **Três perguntas opcionais, de sim ou não** (método BANT, ver Lógica): está falando com quem decide a compra? o cliente confirmou que o problema dele é um que o produto resolve? tem próxima conversa marcada, com data? Cada resposta mexe no score: "Sim" soma 10 e "Não" tira 15. Esses pesos são heurística declarada: o histórico não tem essas respostas, então não há como medir quanto cada uma vale. Um "Não" também troca a ação por uma frase concreta ("Proponha uma data agora. Sem data marcada, a chance continua caindo."). Nenhuma resposta muda o grupo, a ordem da tela ou a receita esperada.
- **Aceitar ou contestar** cada ação; contestar pede um motivo.
- **Acompanhar a equipe:** o painel do manager responde "onde meu time está perdendo dinheiro?", só para ler, com filtros por vendedor, manager ou região. No topo, 4 números, cada um com a frase do que mede: **receita esperada do time** ("nos próximos 3 meses, sem contar negócios novos"); **Foque agora sem próxima conversa marcada**, com quantos e quanto em jogo ("vai esfriar se ninguém agir"); **pipeline parado**, acima de 60 dias ("inflando o pipeline"); **leads sem primeira conversa** ("nunca abordados"). Embaixo, uma linha por vendedor com os mesmos números e as respostas registradas, ordenada pelo Foque sem próxima conversa; os 35 aparecem, com zero quando for o caso. Sem ranking por taxa de ganho e sem botão de ação: quem age é o vendedor.
- Também: a tela do negócio por dentro, "Novo negócio" (para ver em que grupo um cliente novo entraria) e "Como a nota funciona" (o cálculo e o que foi testado).

### Setup

Detalhes completos em [`solution/README.md`](solution/README.md) e no [runbook](solution/docs/runbook.md).

| Ferramenta | Versão | Para quê |
|---|---|---|
| Node.js | 22.18 ou mais nova | tudo |
| npm | 10.9 ou mais novo | instalar e rodar |
| uv | qualquer recente (opcional) | testes da camada de dados e regenerar o `deals.json` |
| Chromium do Playwright | opcional | só para `npm run test:e2e` |

O `solution/data/deals.json` (as 4 tabelas do CRM já juntas, 8.800 oportunidades) vem no repositório, com o SHA-256 ao lado. Não precisa baixar nada do Kaggle para rodar.

```bash
cd solution
npm install
npm start          # constrói a web e sobe app + API em http://localhost:8787
```

```bash
npm test           # fronteiras entre contextos + typecheck + lint + domínio, API, web e dados
npm run test:e2e   # navegador de ponta a ponta, com um vídeo por fluxo em e2e/videos/
```

- **Banco compartilhado (opcional):** com `DATABASE_URL` apontando para um Postgres (papel que só lê os negócios e só lê e acrescenta respostas e decisões, no schema `lead_scorer`), as respostas valem em qualquer aparelho e chegam ao painel da equipe. Sem ela, ficam no navegador. Ver [ADR 0009](solution/docs/adr/0009-banco-com-papel-restrito.md).
- **Deploy:** `npm run build` gera a saída para a Vercel (web estática + API como função) e `npm run test:funcao` a confere localmente ([ADR 0010](solution/docs/adr/0010-deploy-a-vercel.md)).
- **URL:** [https://lead-scorer-g4.vercel.app](https://lead-scorer-g4.vercel.app)

### Lógica

**Testamos 19 fatores (óbvios e derivados) com validação fora da amostra; só a idade sobreviveu (AUC 0,830).** Os pesos de cada fator saem de um recorte do histórico (abertos em 30/06/2017) e são testados no recorte seguinte (abertos em 30/09/2017, desfecho até 31/12); só entra o fator que melhora a previsão em negócios que o cálculo não viu ([`motor_de_pontos.mjs`](process-log/scripts/motor_de_pontos.mjs) → [`motor-de-pontos-2026-10-23.txt`](process-log/evidencias/motor-de-pontos-2026-10-23.txt)):

| Fator | AUC sozinho na validação | Quanto subiria o AUC da chance | Entrou? |
|---|---|---|---|
| idade | 0,830 | (primeiro passo) | **entrou** |
| idade ÷ ciclo do produto | 0,821 | −0,0003 | não |
| idade ÷ ciclo do vendedor | 0,805 | −0,0020 | não |
| vendedor | 0,569 | −0,0329 | não |
| gerente | 0,548 | −0,0635 | não |
| escritório | 0,548 | −0,0745 | não |
| funcionários da conta | 0,536 | +0,0039 | não |
| receita da conta | 0,535 | −0,0031 | não |
| preço ÷ receita da conta | 0,530 | +0,0016 | não |
| setor | 0,505 | −0,0050 | não |
| produto | 0,496 | −0,0096 | não |
| outros 8 (série, perdas, ganhos e taxa da conta, empresa-mãe, carga, estágio, conta já comprou) | 0,499 a 0,538 | +0,0011 no máximo | não |

**Três coisas separadas: o score diz se o negócio é bom; o lugar na tela diz por onde começar; o valor diz quanto está em jogo.** O score (0–100) parte da chance da faixa de idade do negócio contra a melhor faixa (que vale 100) e soma as respostas do vendedor: +10 por "Sim", −15 por "Não". **Esses pesos são heurística declarada**, porque o histórico não tem essas respostas. O lugar na tela é o grupo e, dentro dele, a chance × o preço. O preço aparece à parte e não entra no score.

**Base.** Lead scoring em dois eixos, Perfil × Interesse (RD Station, "Lead Scoring: o guia definitivo para pontuar seus contatos automaticamente", rdstation.com/blog/marketing/o-que-e-lead-scoring), com os pontos de cada atributo calculados pelo método de pontuação da HubSpot (HubSpot, "Lead scoring: o que é e como usar", br.hubspot.com/blog/sales/pontuacao-de-leads): **pontos = taxa de fechamento do atributo ÷ taxa geral**. Um atributo que fica perto de 1,0 não separa nada e não ganha peso. Este dataset não tem engajamento do lead (visitas, e-mails, conversas), então a idade do negócio entra no eixo de Interesse como substituta: ela diz se o negócio ainda anda.

**O método aplicado aos dados** ([`metodo_hubspot.py`](process-log/scripts/metodo_hubspot.py) → [`metodo-hubspot.txt`](process-log/evidencias/metodo-hubspot.txt)):

| Eixo | Atributo | Pontos (mín. a máx.) | Base | Leitura |
|---|---|---|---|---|
| Perfil | setor | 0,97 a 1,03 | 6.711 fechados, 63,2% ganhos | sem pontos |
| Perfil | produto | 0,95 a 1,03 | idem | sem pontos (entra só como valor) |
| Perfil | porte (receita da conta, em quartis) | 0,97 a 1,04 | idem | sem pontos |
| Perfil | escritório | 0,99 a 1,01 | idem | sem pontos (fica como filtro) |
| Perfil | vendedor | 0,87 a 1,11 | idem | não se repete fora da amostra (AUC 0,522): sem pontos, fica como filtro |
| Interesse | idade do negócio aberto | 0,00 a 2,23 | 2.409 abertos em 30/09/2017, 23,2% ganharam até 31/12 | **separa**: monta os grupos e o indicador |

**O score: a qualidade do negócio.** O vendedor lê o número do cartão como "esse negócio é bom?", e o score responde isso (`solution/packages/dominio/src/score/qualidade.ts`, [ADR 0012](solution/docs/adr/0012-score-e-qualidade.md)):

1. **A idade (o dado):** `round(100 × chance da faixa de idade ÷ maior chance entre as faixas)`, com as chances do motor. Hoje: até 40 dias 90 a 100, 41–50 dias 61, 51–60 dias 41, 61–90 dias 15, acima de 90 dias 1.
2. **As respostas do vendedor** às 3 perguntas do BANT (quem decide, o problema confirmado pelo cliente, a próxima conversa com data): +10 por "Sim", −15 por "Não", sem resposta não muda; o resultado fica entre 0 e 100. **Os pesos são heurística declarada**, num config próprio (`qualidade.config.ts`), porque o histórico não tem essas respostas para calibrá-los. "Não" pesa mais porque é um fato que trava a venda; "Sim" é o esperado de um negócio vivo.

Sem data de início não há idade: sem resposta, o cartão diz "Score —" e o detalhe pede "Responda as perguntas para pontuar."; com uma resposta, o score parte de 50. O "ver por quê" mostra a conta: "Aberto há 57 dias: 22% dos negócios com essa idade fecharam (a melhor faixa fecha 52%).", uma linha por resposta ("Decisor confirmado: +10") e a posição na lista.

**A ordem da tela** é outra coisa: o grupo (Foque agora, Siga no ritmo, Aborde primeiro, Nutrição, com o Siga promovido quando o Foque está vazio) e, dentro dele, o que há a ganhar (chance × preço de tabela; sem data, o preço; empate, o preço maior na frente). O grupo vem antes do valor porque, pelo valor na lista inteira, um produto caro parado passaria um negócio vivo barato. Na lista de Zane Levy, o primeiro da Nutrição (GTX Pro, US$ 4.821, chance de 8%) ficaria acima do único do Foque agora (GTX Basic, US$ 550, chance de 21%). Por isso o Foque agora pode estar no topo com score menor que o do Siga no ritmo logo abaixo: está ali porque a chance dele está caindo e é agora que o esforço conta, não porque é melhor.

**O valor** ("US$ 4.821 em jogo") fica numa linha própria. Ele não entra no score: o mesmo negócio com outro preço tem o mesmo score.

Medido no `deals.json`, sem respostas ([`score_qualidade.mjs`](process-log/scripts/score_qualidade.mjs) → [`score-qualidade-2026-10-23.txt`](process-log/evidencias/score-qualidade-2026-10-23.txt)):

- toda a Nutrição fica entre 1 e 15 (0 dos 1.532 acima de 15);
- em nenhum dos 27 vendedores com negócio aberto um Siga no ritmo fica abaixo de um Foque agora;
- os 500 sem data mostram "Score —";
- multiplicar o preço por 10 não muda o score de nenhum dos 1.589 com data;
- dentro de cada grupo, o valor esperado nunca sobe de um cartão para o de baixo.

Em Zane Levy, o Foque agora é "Score 41 · GTX Basic · US$ 550 em jogo", 1º de 88. Um "Sim" para "quem decide" leva esse negócio a 51; os 3 "Sim", a 71; os 3 "Não", a 0. A ordem da tela continua a mesma.

**O sistema calcula a chance (motor de pontos).** Ninguém digitou peso: na carga, o motor testa 19 fatores no histórico e fica só com o que melhora a previsão em negócios que ele não viu ([`motor_de_pontos.mjs`](process-log/scripts/motor_de_pontos.mjs) → [`motor-de-pontos-2026-10-23.txt`](process-log/evidencias/motor-de-pontos-2026-10-23.txt)):

- **Fatores:** os óbvios (idade, produto, série, setor, receita e funcionários da conta, vendedor, gerente, escritório, estágio) e os derivados (idade ÷ ciclo típico dos ganhos do produto e do vendedor; ganhos, perdas e taxa de ganho da conta antes do corte; a conta já comprou; empresa-mãe; preço ÷ receita da conta; carga do vendedor). Cada um medido só com o que se sabia no dia do corte; "sem dado" vale 0.
- **Pontos por valor:** `round(10 × ln(taxa do valor ÷ taxa geral))`, com 20 negócios fictícios na taxa geral somados a cada valor e 0 ponto abaixo de 30 negócios.
- **Replay sem futuro:** pontos medidos nos 1.686 abertos em 30/06/2017 (desfecho até 30/09); escolha medida nos 2.409 abertos em 30/09/2017 (desfecho até 31/12). Entra o fator de maior AUC; depois, só quem sobe o AUC do score em 0,005 ou mais. Os pesos finais saem do recorte mais recente.

(A tabela do motor está no começo desta seção.)

**AUC da chance na validação: 0,830; só a idade: 0,830.** O sistema testou 18 hipóteses além da idade e nenhuma acrescentou previsão fora da amostra; vendedor, gerente e escritório pioram. A chance fica com a idade porque o motor mediu, não porque alguém decidiu, e se o dado mudar ela muda sozinha. Os 500 negócios sem data de início ficam sem chance: no replay nenhum deles pode entrar, então não há evidência sobre eles (na tela, entram só pelo preço, e o score espera a primeira resposta).

**A idade separa, e quanto.** A chance de cada faixa sai de um replay no próprio histórico: os 2.409 negócios abertos em 30/09/2017, a idade de cada um nesse dia e quem ganhou até 31/12/2017 ([`curva_fina.py`](process-log/scripts/curva_fina.py) → [`curva-fina.txt`](process-log/evidencias/curva-fina.txt)):

| Faixa de idade | 0–10 | 11–20 | 21–30 | 31–40 | 41–50 | 51–60 | 61–90 | > 90 |
|---|---|---|---|---|---|---|---|---|
| Negócios no replay | 283 | 205 | 191 | 180 | 164 | 201 | 460 | 725 |
| Ganharam até 31/12 | 49,8% | 51,7% | 49,2% | 50,0% | 32,3% | 21,9% | 6,7% | 0% |
| Pontos no motor | +7 | +8 | +7 | +7 | +3 | −1 | −11 | −36 |
| Chance no detalhe | 47% | 52% | 47% | 47% | 31% | 21% | 8% | 1% |
| Score (só a idade) | 90 | 100 | 90 | 90 | 61 | 41 | 15 | 1 |

Os grupos seguem a curva: até 40 dias ela fica plana perto de 50% (Siga no ritmo); entre 41 e 60 cai a cada 10 dias (Foque agora: ainda fecha, mas está esfriando, que é o "deixam oportunidades boas esfriar" do enunciado); depois de 60 quase some (Nutrição). Pôr o Foque acima do Siga é uma **suposição declarada**: o efeito de o vendedor agir sobre um negócio não foi medido, porque o dataset não registra ações.

**Quanto separa, com o que mede.** AUC (0,5 = acaso) para o alvo "ganhou até 31/12/2017", nos **1.879 negócios abertos em 30/09/2017 com até 138 dias** ([`auc_faixas.py`](process-log/scripts/auc_faixas.py) → [`auc-faixas.txt`](process-log/evidencias/auc-faixas.txt)):

| Score | AUC |
|---|---|
| os 3 grupos (Siga > Foque > Nutrição) | **0,759** |
| as 8 faixas do indicador | **0,767** |
| ingênuo: vendedor + conta + produto + setor (taxas treinadas até 30/09) | 0,483 |
| ordenar pelo preço de tabela | 0,488 |

Ressalva: os 0,759 e 0,767 são **dentro da amostra**. As taxas das faixas saem deste mesmo replay e os limites de 40 e 60 dias foram escolhidos olhando esta curva. Dois testes de robustez, no mesmo arquivo de evidência: em outro corte (30/06 → 30/09/2017), a idade crua, sem os limites de 40 e 60 dias (escolhidos no corte de 30/09), dá 0,691; e, entre os negócios que de fato fecharam, a idade não separa ganho de perda (0,495). Ou seja: a idade mede se o negócio ainda anda, não se o cliente é bom ([`idade_robustez.py`](process-log/scripts/idade_robustez.py) → [`idade-robustez.txt`](process-log/evidencias/idade-robustez.txt)).

**Receita esperada.** Chance do motor (sem arredondar) × preço de tabela do produto, nos próximos 3 meses. O preço de tabela serve de valor porque, nos ganhos, a mediana do `close_value` é 1,0 × o preço de tabela nos 7 produtos ([`explorar-pipeline.txt`](process-log/evidencias/explorar-pipeline.txt), seção "Valor"), com razão média de 0,996 ([`receita-esperada.txt`](process-log/evidencias/receita-esperada.txt)). Hoje, nos 2.089 abertos: **US$ 69.395** ([`score-qualidade-2026-10-23.txt`](process-log/evidencias/score-qualidade-2026-10-23.txt), seção "receita esperada"). A soma dos pontos vira chance pela razão (taxa base × e^(pontos ÷ 10)). Backtest no recorte mais recente: nos 2.409 abertos em 30/09/2017, a conta pela chance previa **US$ 1.254.677**, e os que ganharam até 31/12 fecharam **US$ 1.251.928** (+0,2%). A outra conversão do motor, por log-odds, comprimia a curva (0 a 10 dias fechou 49,8% e virava chance de 38%) e previa US$ 1.077.805 (−13,9%) ([`motor-de-pontos-2026-10-23.txt`](process-log/evidencias/motor-de-pontos-2026-10-23.txt), seção "calibração da receita"). Mesma ressalva: dentro da amostra, então mostra coerência, não previsão. A receita esperada ordena dentro do grupo e nunca muda o grupo; as respostas do vendedor não entram nela, porque os pesos delas não foram medidos.

**O painel do manager: onde o time está perdendo dinheiro.** As mesmas regras da tela do vendedor, somadas por filtro, cada número com quantos negócios e quanto está em jogo (a soma do preço de tabela) ([`integracao.test.ts`](solution/packages/dominio/src/aplicacao/integracao.test.ts)):

| Métrica | Regra | Time inteiro | West |
|---|---|---|---|
| Receita esperada do time | soma de chance × preço dos abertos com data | US$ 69.395 | US$ 38.435 |
| Foque agora sem próxima conversa marcada | negócios que a tela de cada vendedor mostra no Foque (com o Siga promovido quando o Foque dele está vazio) sem "Sim" para "Tem próxima conversa marcada, com data?" | 33 · US$ 67.896 | 17 · US$ 36.502 |
| Pipeline parado | abertos há mais de 60 dias (Nutrição) | 1.532 · US$ 3.779.334 | 716 · US$ 1.935.958 |
| Leads sem primeira conversa | abertos sem data de início | 500 · US$ 1.073.986 | 0 · US$ 0 |

A tabela por vendedor repete essas colunas e soma, linha a linha, o número do time (há teste disso). Ela é ordenada pelo Foque sem próxima conversa, o que precisa de ação, e não pela taxa de ganho, que não se repete fora da amostra (AUC 0,522).

**Por que BANT: quanto de cada método o dataset cobre.** Antes de escolher, contei, critério por critério, o que as 4 tabelas preenchem e se esse campo separa o desfecho (AUC nas evidências acima):

| Método | Critérios que o dado cobre | O resto | Perguntas ao vendedor por negócio |
|---|---|---|---|
| **BANT** | **1 de 4**: Timing, pela idade, com sinal (0,766) | Budget e Need só por proxy, sem sinal (preço 0,488, porte 0,508; produto 0,500); Authority, nada | 3 |
| MEDDIC | 0 de 6 | nenhum critério no dado | 6 |
| SPICED | 1 de 5: Situation, só descritivo e sem sinal (setor 0,486; porte 0,508), e só nos 32% dos abertos que têm conta | Pain, Impact, Critical Event e Decision, nada | 4, mais completar a conta |

BANT fica porque é o único em que um critério vem do dado e separa: o Timing é a idade. Authority, Need e o próximo passo viram perguntas de sim ou não, a menor carga das três opções. Nenhum dos métodos pode ser medido aqui como preditor, porque o dataset não tem resposta gravada para nenhum deles.

**BANT, ancorado no que o dado tem.**

| Letra | De onde vem | Na ferramenta |
|---|---|---|
| **T** (tempo) | `engage_date` → idade contra a curva | monta os grupos e a parte do dado no score |
| **B** (orçamento) | `products.sales_price` | o valor em jogo e a receita esperada; não entra no score e não muda o grupo |
| **A** (quem decide) | o dataset não tem coluna | pergunta de sim ou não ao vendedor; +10 ou −15 no score (heurística) |
| **N** (necessidade) | o dataset não tem coluna | pergunta de sim ou não ao vendedor; +10 ou −15 no score (heurística) |
| próximo passo | o dataset não tem coluna | pergunta: "tem próxima conversa marcada, com data?"; +10 ou −15 no score (heurística) |

Para cada "Não", uma ação concreta em uma frase, na lógica de Alex Hormozi, *$100M Leads* (livro) e o framework de vendas "Decision Making & Selling with Logic": a objeção vira o próximo passo. As respostas mudam o score e a ação, nunca o grupo: o motor recusa um método que tente mover um negócio por resposta, e um teste responde "Não" e "Sim" às 3 perguntas dos 2.089 abertos e confere que nenhum muda de grupo.

**Premissas e cuidados.**
- **"Hoje" = 31/12/2017**, o último fechamento do dataset, como premissa declarada (o enunciado não fixa data; contar até a data real daria anos para todos). A tela mostra essa data.
- **O teto de 138 dias pode ser artefato do gerador sintético.** Nenhum negócio fechou depois de 138 dias, ganho ou perdido, e 1.291 dos 1.589 em negociação estão abertos há mais tempo que isso. A ferramenta diz o que o dado mostra e não chama esses negócios de mortos: eles vão para Nutrição.
- **Conta vazia não penaliza.** Todos os 6.711 fechados têm conta, e nenhum dos 647 negócios sem conta abertos em 30/09/2017 (com até 138 dias) fechou até 31/12. Neste dataset, todo negócio que fecha tem conta; usar "sem conta" como penalidade seria pôr o desfecho dentro da nota (vazamento). Na tela, aparece como "sem dado de conta", neutro.

### Resultados

Na base inteira, em 31/12/2017: **Foque agora 30 · Siga no ritmo 27 · Aborde primeiro 500 · Nutrição 1.532** (2.089 abertos), pela idade. Na tela, quem fica com o Foque vazio vê o Siga no Foque: 3 negócios de 2 vendedores de West sobem. Dos 35 vendedores, 8 aparecem com zero abertos (5 nunca tiveram negócio e 3 só têm fechados), e todos estão no seletor. No painel do manager: US$ 69.395 de receita esperada; 33 negócios do Foque sem próxima conversa marcada (US$ 67.896 em jogo); 1.532 parados (US$ 3.779.334); 500 sem primeira conversa (US$ 1.073.986). Verificação do build (rodada pela sessão coordenadora, não aceita pelo relatório de quem construiu): `npm test` verde (domínio 143, API 65 mais 3 que só rodam com banco, web 88, dados 11), 12 de 12 fluxos de ponta a ponta com vídeo em [`solution/e2e/videos/`](solution/e2e/videos/), integração com o banco real em transação desfeita. Detalhes na [sessão 05](process-log/sessoes/sessao-05-construcao-e-verificacao.md) e na [sessão 06](process-log/sessoes/sessao-06-motor-score-e-verificacao.md).

### Recomendações

1. **Na segunda de manhã, abrir pelo Foque agora** (41 a 60 dias): a chance ainda existe (32% e 22%) e cai a cada 10 dias. Depois, Siga no ritmo (perto de 50%). Pôr o Foque primeiro é uma escolha, não uma medição; a recomendação 5 diz como testá-la.
2. **Encaminhar a Nutrição.** São 1.532 dos 2.089 abertos, com mais de 60 dias. Menos de 10% dos negócios dessa idade fecharam no histórico. Tirá-los da fila ativa deixa à vista os 57 que ainda estão no tempo em que negócios fecham.
3. **Registrar o que falta no CRM:** quem decide, qual problema o cliente quer resolver e a próxima conversa com data. São as 3 perguntas da ferramenta. Com elas registradas, o eixo de Perfil e a qualificação passam a poder ser medidos, coisa que este dataset não permite.
4. **Exigir data de início.** Os 500 negócios sem `engage_date` são todos da região Central, que também não tem nenhum negócio no Foque agora: sem data, a ferramenta não tem como dizer onde o vendedor deve focar.
5. **Medir depois de um trimestre** se os negócios do Foque agora fecham mais que os de mesma idade do trimestre anterior. É o teste que falta para confirmar a suposição da ordem dos grupos.

### Limitações

- **A dor por trás do pedido é previsibilidade de receita, e a ferramenta só cobre parte dela.** A receita esperada (US$ 69.395) estima o que os negócios abertos hoje devem render em 3 meses; não é a receita do período. No 4º trimestre de 2017, 637 dos 1.196 ganhos vieram de negócios que entraram depois de 30/09 ([`receita-esperada.txt`](process-log/evidencias/receita-esperada.txt)), e a ferramenta não modela o que ainda vai entrar.
- **Escolher o perfil não é login.** "Quem é você?" diz de quem é a lista. Qualquer pessoa com acesso vê todos os negócios, e o banco grava o vendedor do negócio, não quem clicou.
- **Respostas compartilhadas exigem a API com o banco configurado.** Sem `DATABASE_URL`, respostas e decisões ficam no navegador de cada vendedor (e na memória da API, que some ao reiniciar): não passam de um aparelho para outro nem chegam ao painel da equipe.
- **Comissão não existe no dataset.** O campo é opcional, preenchido pelo vendedor, e nenhum percentual é sugerido.
- **Os pesos das respostas no score são escolha, não medida.** +10 por "Sim" e −15 por "Não" estão num config, declarados como heurística: o histórico não tem as respostas para calibrá-los. Com as respostas gravadas no banco e o desfecho dos negócios, dá para medi-los como o motor mede a idade.
- **Canal, oferta e contexto do cliente não existem no dado.** Não há origem do lead, campanha, oferta, histórico de contato nem capacidade de cada vendedor. Nada disso entra na nota.
- **Dataset sintético e parado no tempo.** "Hoje" é fixo em 31/12/2017, o teto de 138 dias pode ser do gerador, e não há integração com um CRM vivo.
- **Rate limit em memória, por processo**, e as fontes da interface vêm do Google Fonts sem SRI (há fontes de reserva). Lista completa em [`solution/README.md`](solution/README.md#limitações).

**O que precisaria para escalar:** login com SSO e papéis (o vendedor vê os seus, o manager a equipe dele), com histórico de quem fez o quê; ingestão contínua do CRM, com "hoje" igual à data real; registrar as 3 perguntas e as ações do vendedor, para medir se o Foque agora fecha mais que o resto e recalibrar os limites de 40 e 60 dias com dado vivo; trazer canal, oferta e contexto do cliente para o eixo de Perfil; rate limit compartilhado e um proxy de borda com TLS.

---

## Process Log — Como usei IA

> Registro completo, por sessão: [process-log/README.md](process-log/README.md)

### Metodologia

Trabalhei com a IA como trabalharia instrumentando uma área: primeiro o ambiente e as regras, depois o problema. Detalhes em [process-log/instrumentacao.md](process-log/instrumentacao.md).

1. **Etapas com critério de aceite.** E0 instrumentação → E1 escolha → E2 dados e lógica do score → E3 construção → E4 verificação → E5 documentação. Nenhuma etapa começa sem o problema e o critério de aceite escritos.
2. **Decidir antes de agir.** Uso o ECC (Everything Claude Code) modificado, com os **8Rs do PMV** (Plano Mínimo Viável), do livro *Inteligência Pragmática* (Max Peters), que adaptei em hooks. Um hook barra o primeiro comando e a primeira escrita de cada arquivo até a IA declarar objetivo, alternativas, impacto, custo, controle e reversibilidade.
3. **Medir antes de afirmar.** Todo número sobre os dados vem de um script em `process-log/scripts/` com a saída bruta em `process-log/evidencias/`. Antes de rodar cada medição nova, a previsão fica gravada em arquivo, para que acerto e erro sejam comparáveis com o resultado.
4. **Registro fora da conversa.** Cada etapa fecha com um registro em `process-log/sessoes/` (o que foi feito, onde desconfiei e conferi, próximo passo). Um hook avisa a IA quando há trabalho mais novo que o último registro.
5. **Higienização de contexto por etapa (`/clean`).** Na troca de etapa, o Jev (TypeSafe) julga o que da conversa ainda é relevante. Eu aprovo o plano de corte, e o corte só acontece com a sessão fechada e depois de um backup. A atenção do modelo fica na etapa atual, e o que saiu continua auditável aqui.
6. **O próprio teste como projeto, com revisor adversarial.** O objetivo do teste foi escrito como PGG (os 4Cs do mesmo livro) e planejado como PMV (8Rs), numa esteira de diagnóstico minha: qualificar o problema, diagnosticar o negócio, mapear oportunidades e pré-mortem, desenhar a arquitetura. Cada fase fecha num portão de um revisor adversarial que reprova e devolve (até 3 voltas antes de escalar para mim; a f0 teve 4, a 4ª por ordem minha, e a f1, a f2 e a f3 tiveram 3 cada), e o diagnóstico não recebe a solução. A construção roda ao lado das fases seguintes.
7. **Construção delegada, aceite conferido.** O código foi escrito por workers supervisionados pelo Orca, em paralelo, cada um com spec em arquivo (entradas, passos, saídas, critério de aceite, definição de pronto). O aceite eu confiro rodando, não pelo "terminei" do worker.
8. **Evidência do processo:** os registros por sessão, os scripts com as saídas brutas e os vídeos do E2E. Não há export de chat, e o histórico de commits foi condensado num commit só para a entrega.

**Iterações:** 4 fases de diagnóstico com 13 voltas de portão no total (4 + 3 + 3 + 3); 6 ondas de construção (esqueleto, três workers em paralelo, integração com revisão e E2E, a onda de receita, painel e banco, os ajustes da verificação, e o motor de pontos com o score de qualidade e o painel do manager).

O conteúdo dos meus frameworks próprios não está no repositório; aqui está como eles entram no processo e o efeito observado.

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| Claude Code (Claude Opus 5.5) | Coordenador: leitura do repo, medições, diagnóstico, desenho, verificação e este registro |
| Workers do Orca (Claude Code) | Construção em paralelo (domínio, API, web, ajustes) e extração do sistema visual de referência, com spec em arquivo e aceite conferido |
| Subagentes do Claude Code | Fases da esteira de diagnóstico, revisor adversarial, revisão de código e de segurança só leitura, documentação |
| Jev (TypeSafe) | Higienização de contexto por etapa (`/clean`) |
| ECC modificado (8Rs de PMV) | Hooks e cartão de decisão antes de cada ação; lembrete de registro no process log |
| uv + pandas 3.1.0, Node 22 | Medições reproduzíveis (`process-log/scripts/`) |
| Playwright | Ponta a ponta no navegador, com vídeo de cada fluxo |

### Workflow

1. **E0–E1:** instrumentei o ambiente e medi o sinal dos 5 datasets; escolhi o 003 ([sessão 01](process-log/sessoes/sessao-01-escolha-do-desafio.md)).
2. **E2:** medi o pipeline e testei os atributos fora da amostra; a tese do score passou a ser "idade × valor", com explicação ([sessão 02](process-log/sessoes/sessao-02-entender-o-pipeline.md)).
3. **PGG e PMV do teste**, com revisor adversarial em 4 voltas na f0 ([sessão 03](process-log/sessoes/sessao-03-pgg-e-pmv-do-teste.md)).
4. **Diagnóstico do negócio** pela operação do enunciado, camada de dados com testes e sistema visual de referência ([sessão 04](process-log/sessoes/sessao-04-autopsia-dados-e-design.md)).
5. **E3–E4:** desenho final, construção em ondas por workers, revisão independente, E2E com vídeo e verificação pelo coordenador ([sessão 05](process-log/sessoes/sessao-05-construcao-e-verificacao.md)).
6. **Motor, score e painel:** o motor de pontos (19 fatores, replay sem futuro, seleção fora da amostra), o score de qualidade separado da ordem e do valor, o painel do manager com 4 números e a verificação em produção ([sessão 06](process-log/sessoes/sessao-06-motor-score-e-verificacao.md)).
7. **E5:** este README, os registros da sessão 05 e da sessão 06 e as evidências reprodutíveis, com cada número da Lógica rodado de novo a partir do repositório.

### Onde a IA errou e como corrigi

Cada registro de sessão tem a seção "Onde desconfiei e conferi". Os casos que mudaram o resultado:

- **A primeira leitura concluiu que nem a idade previa.** O caso registrou "a idade não ordena os negócios vivos" com AUC 0,505, mas esse número media só ganho × perda entre os 935 negócios que fecharam. O revisor apontou o recorte; na pergunta certa, "ganhou até 31/12" entre os 1.879 abertos em 30/09/2017 com até 138 dias, a idade dá 0,766 ([`idade-robustez.txt`](process-log/evidencias/idade-robustez.txt)). É a base do produto.
- **Sinal com cara de ciência.** Os vendedores iam de 55% a 70% de ganho, e o caminho óbvio seria pesar por vendedor. Testado fora da amostra: AUC 0,522. Ficou fora da nota.
- **O rascunho do Foque punha no topo os negócios "perto do limite"** (61 a 138 dias). No backtest, essa faixa ganhou 4,7%, contra 50,2% dos de até 40 dias. A curva fina mostrou que a queda começa depois de 40, e o Foque ficou em 41 a 60 dias.
- **O número de benefício era de outro corte.** O revisor pegou que o AUC citado (0,753) vinha de 4 faixas de uma medição anterior, não dos grupos em uso. Medido de novo com os grupos e as faixas da ferramenta, com a previsão gravada antes: 0,759 e 0,767, com o rótulo de dentro da amostra.
- **A receita esperada podia ser lida como receita do trimestre.** Medido: 637 dos 1.196 ganhos do 4º trimestre vieram de negócios que entraram depois do corte. O texto da tela diz "Não conta negócios novos que vão entrar".
- **Um texto prometia o que o motor não fazia** ("Sem data, o negócio vai para nutrição"). O motor passou a recusar qualquer efeito de resposta sobre o grupo, com teste, e o texto virou "Proponha uma data agora. Sem data marcada, a chance continua caindo."
- **Arredondamento que contradizia a frase:** 6,7% virava "1 em 10" ao lado de "menos de 1 em cada 10 fechou". Agora a tela dá a taxa da faixa em % (7%).
- **A conversão por log-odds errava a receita em −14%.** No backtest, ela previa US$ 1.077.805 contra US$ 1.251.928 fechados; a conversão pela razão previa US$ 1.254.677 (+0,2%) e ficou ([sessão 06](process-log/sessoes/sessao-06-motor-score-e-verificacao.md)).
- **Na verificação em produção, um negócio da Nutrição aparecia com score acima do Foque, e o Foque de alguns vendedores ficava vazio com negócios vivos no Siga.** Corrigidos: o grupo vem antes do valor, o score mede a qualidade (nenhuma Nutrição acima de 15; nenhum Siga abaixo de um Foque nos 27 vendedores), e o Siga sobe para o Foque vazio.
- **Vazamento pelo "sem dado" no motor.** Todo negócio que fecha tem conta, então "sem conta" virava sinal do desfecho. Corrigido no motor: a taxa geral é a de quem tem o dado, "sem dado" vale 0 e cada fator é medido só em quem tem o dado, com teste de vazamento.
- **Arquivos fora dos commits:** o `.gitignore` do repositório ignora `submissions/`, e dois commits saíram sem arquivos novos. O próprio worker pegou ao conferir a lista de arquivos ignorados; dali em diante, cada arquivo novo entra com `git add -f`.
- Também: uma citação do enunciado cortada no ponto que mudava o sentido, uma "previsão" escrita depois do resultado, e um framework do livro que eu tinha atribuído a mim ([sessão 03](process-log/sessoes/sessao-03-pgg-e-pmv-do-teste.md)).

### O que eu adicionei que a IA sozinha não faria

- **Medir antes de afirmar como regra do ambiente**, não como boa intenção: hooks que barram a ação sem cartão de decisão, scripts com saída guardada e previsão gravada antes de rodar.
- **O vendedor como usuário que age.** Quem aceita, contesta ou encaminha é o vendedor; o manager acompanha, só para ler e com filtros, onde o time está perdendo dinheiro e em que lista agir.
- **"Hoje" = 31/12/2017, mantido e declarado** como premissa na tela e no README.
- **Nutrição em vez de "morto".** O teto de 138 dias pode ser do gerador; a ferramenta não declara mortos os 81% dos negócios em negociação que passaram dele.
- **BANT só onde o dado sustenta**, com cada letra ancorada numa coluna ou virando pergunta.
- **Receita esperada e comissão**, para o vendedor saber quanto deve coletar, sem inventar o percentual que o dataset não tem.
- **Os 35 vendedores sempre visíveis**, inclusive os 8 sem negócio aberto, com o seletor "Quem é você?".
- **Recusar ressalvas e pedir mais uma volta** do revisor, em vez de aceitar o "bom o suficiente".
- **Experiência de operação comercial** (cadência de follow-up e priorização de pipeline), que dá o porquê do Foque: o negócio que ainda fecha mas está esfriando.

### Tempo

**Tempo ativo da sessão principal: 7 h 46 min.** Soma dos intervalos de até 5 min entre eventos da sessão principal do Claude Code; pausas maiores não contam; medido por [`process-log/scripts/tempo_ativo.mjs`](process-log/scripts/tempo_ativo.mjs), com `--ate 2026-10-23T21:31:00Z`. Saída bruta em [`process-log/evidencias/tempo-ativo-2026-10-23.txt`](process-log/evidencias/tempo-ativo-2026-10-23.txt).

---

## Evidências

- [ ] Screenshots das conversas com IA
- [x] Gravações de tela: os vídeos dos fluxos de ponta a ponta (`solution/e2e/videos/`)
- [ ] Chat exports: não há. A evidência do processo são os registros por sessão, os scripts, as saídas brutas e os vídeos.
- [x] Registros por sessão (`process-log/sessoes/`), cada um com "Onde desconfiei e conferi"
- [ ] Git history: a entrega vai num commit só; a iteração está nos registros por sessão
- [x] Outro: scripts de medição e as saídas brutas (`process-log/scripts/`, `process-log/evidencias/`), todos rodados de novo a partir do repositório na E5

---

_Submissão enviada em: (preencher no PR)_
