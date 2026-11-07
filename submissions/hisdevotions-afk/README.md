# Submissão — ROBERTO QUIRINO — Challenge 003

## Sobre mim

- **Nome:** Roberto Quirino
- **LinkedIn:** https://www.linkedin.com/in/roberto-quirino/
- **Challenge escolhido:** 003 (Lead Scorer)

---

## Executive Summary

Construí o Pipeline em Foco, um app de vendas em React com um motor de scoring em Python. Na segunda de manhã ele mostra a cada vendedor em que deals trabalhar, o que fazer em cada um e por quê. Um bot manda a mesma fila por Slack ou email. Antes de pontuar qualquer coisa, testei cada característica do CRM contra o acaso: vendedor, conta, tamanho da conta, produto, setor, região e manager não mudam a chance de ganhar nesta base. O sinal que passou foi a idade do deal, e é ela que define o score. O achado que mais importa para a Head de RevOps: 65% do pipeline declarado (US$ 3,2 mi de US$ 5,0 mi) está em deals parados além do maior ciclo que a base já fechou.

App publicado: https://hisdevotions-afk.github.io/ai-master-challenge/

![Overview](process-log/screenshots/12-overview.png)

---

## Setup

Para só ver, abra o link acima. Para rodar local (Node 22+):

```bash
cd submissions/hisdevotions-afk/solution/app
npm install
npm run dev          # http://localhost:5173
```

O `data.json` com os scores já está versionado, então não precisa de Python para ver o app. Para recalcular (Python 3.12+, sem dependências):

```bash
cd submissions/hisdevotions-afk/solution/engine
python3 scoring.py                    # lê ../data/*.csv e grava ../app/public/data.json
python3 scoring.py --ref 2017-11-30   # simula outro "hoje"
python3 test_scoring.py               # testes do motor (ou python3 -m pytest)
```

O bot lê o mesmo `data.json` e não escreve texto novo, só reformata as filas:

```bash
python3 notify.py --agent "Hayden Neloms"                       # imprime no terminal
python3 notify.py --agent "Hayden Neloms" --webhook $SLACK_URL  # Slack (incoming webhook)
python3 notify.py --agent "Hayden Neloms" --to time@empresa.com # email (precisa de SMTP_HOST)
python3 notify.py --all --targets targets.json                  # um digest por vendedor, cada um no seu destino
python3 test_notify.py
```

Sem `--webhook`, `--to` ou `--targets` o bot só imprime. Trecho real da saída:

```
*Feche esta semana* (5)
  - Konmatfix — GTX Plus Pro — US$ 721 em 30d: Peça um sim ou não esta semana: em 21 dias o deal passa do maior ciclo que a base já fechou. É cliente da casa, fale com quem aprovou a última compra; junte com os outros 9 deals abertos da conta.
  - Sem conta vinculada — MG Advanced — US$ 604 em 30d: Feche antes de esfriar: a chance cai a cada semana, e em 3 dias fica abaixo de metade do pico.
```

---

## O que o vendedor vê

| Tela | Pergunta que responde |
|---|---|
| Overview | "Em que eu trabalho esta semana?" Quatro filas com verbo (feche, decida, mantenha em movimento, engaje) e a ação do momento |
| Pipeline | "Como está tudo?" Lista e kanban na mesma ordem das filas. Na fila Decidir dá para decidir em lote, com desfazer |
| Ficha do deal | "Por que esse score?" Os motivos, a curva histórica e o contexto da conta |
| Forecast | "Quanto vai entrar?" Declarado, esperado e próximos 30 dias, por região, manager ou vendedor |
| Contas | "Qual o histórico com esse cliente?" |
| Time | "Quem produz o quê?" Receita ganha, ticket médio e higiene de pipeline de cada pessoa |

Todas as telas têm filtro em cascata de região, manager e vendedor. Com um vendedor escolhido, a Overview abre com "Bom dia, Hayden."

---

## Lógica do scoring

**1. Testar antes de usar.** Para cada característica, uma simulação responde: se todos os grupos tivessem a mesma chance de ganhar, com que frequência o acaso produziria diferenças tão grandes quanto as dos dados?

| Característica | p vs. acaso | No score? |
|---|---|---|
| Idade do deal | < 0,001 | Sim |
| Mês de fim de trimestre | < 0,001 | Não: diz quando o deal é registrado, não se um aberto vai fechar |
| Vendedor / Vendedor × produto | 0,30 / 0,22 | Não |
| Produto / duração do ciclo por produto | 0,48 / 0,10 | Não |
| Tamanho da conta (receita / funcionários) | 0,64 / 0,78 | Não |
| Região / Manager / Conta / Setor | 0,78 / 0,88 / 0,95 / 0,99 | Não |

**2. O score.** `score = P(ganhar nos próximos 30 dias | idade)`, em %. A curva aprende com os 6.711 deals fechados e também com os abertos: um deal aberto há 90 dias que não fechou é evidência de que 90 dias não garantem fechar em 30. Nesta base o melhor score possível é 31% (deals com 85 dias). Por isso a tela mostra o score junto de uma faixa, que compara com esse máximo: um deal de 28% é "alta", não uma nota baixa. O valor do deal não entra no score.

**3. A ordem das filas** é a receita esperada em 30 dias (valor × score), mostrada ao lado do score na mesma tabela. Assim o número que ordena está sempre visível.

**4. As filas e as ações.** Os limites saem dos dados e se ajustam com outra base:
- *Avançar*: menos de 44 dias. Ainda cedo.
- *Fechar*, de 44 a 138 dias, com a ação mudando conforme a fase: antes do pico, "envie a proposta"; no pico (85 dias), "peça a decisão"; depois dele, "feche antes de esfriar"; a partir de 115 dias, quando a chance cai abaixo de metade do pico, "peça um sim ou não".
- *Decidir*: 138 dias ou mais. Nenhum deal da base fechou depois disso. A sugestão de encerrar ou confirmar vem de quanto o deal passou do limite, comparado com a mediana dos parados (653 para encerrar, 648 para confirmar). Falta de conta no CRM não manda encerrar: é falha de cadastro, não sinal de deal morto, e vira uma tarefa de cadastro na própria ação.
- *Prospectar*: ainda não engajado, sem score.

**5. O contexto da conta muda a ação, não o score.** Conta não muda a chance de ganhar (p = 0,95), mas saber que o cliente já comprou 34 vezes ou que tem outros 13 deals abertos muda a conversa. Isso aparece como motivo e entra no texto da ação.

**6. Sem LLM em tempo de execução.** Todo texto é montado a partir dos números, então sempre bate com o dado e ninguém precisa de chave de API.

**7. Correções nos dados.** `GTXPro` virou `GTX Pro` (1.480 deals perdiam o preço no join) e `technolgy` virou `technology`.

---

## Recomendações para a Head de RevOps

1. **Limpar o forecast esta semana.** 1.301 deals (US$ 3,2 mi) estão além de qualquer ciclo já fechado. Cada vendedor decide os seus na fila Decidir.
2. **Cadastrar as contas.** 1.425 dos 2.089 deals abertos (68%) estão sem conta. Sem conta não há histórico do cliente, e o contexto que melhora a ação some.
3. **Cobrar receita e higiene de pipeline, não taxa de ganho.** Receita e volume variam muito entre vendedores (de US$ 1,15 mi a US$ 0 no histórico). Taxa de ganho não varia além do acaso (p = 0,30), então ranquear por ela é ranquear ruído.
4. **Registrar atividade no CRM** (email, reunião). Hoje a idade é o único sinal. Com atividade, o score passa a distinguir o deal velho que tem reunião marcada para amanhã.

---

## Limitações

- **Dados que parecem artefato.** Alguns padrões são limpos demais para uma operação real: a região Central não tem nenhum deal em negociação, e todos os 500 prospects estão lá; 62% do pipeline aberto passou do maior ciclo já fechado. O app mostra esses achados, mas eles podem vir de como a base foi gerada. Em uma empresa real, eu confirmaria no CRM antes de mudar a cobrança do time.
- **Sem atividade no CRM.** Um deal com 150 dias e reunião marcada para amanhã aparece como parado.
- **Retrato de 31/12/2017.** Em produção o motor rodaria toda noite e as decisões voltariam para o CRM. Hoje ficam no `localStorage`, com exportar e importar em JSON.
- **Viés de sobrevivência no limite de 138 dias.** A base termina em 31/12/2017, e um deal aberto há 150 dias pode ter um desfecho que ainda não foi registrado. Por isso a fila Decidir pede requalificar ou encerrar, e o sistema nunca encerra sozinho.
- **O pico da curva depende de um ponto só.** Ele é a idade com o maior valor entre as que têm pelo menos 30 deals, e pode mudar com a amostra. Suavizar a curva antes de procurar o pico resolveria.
- **Destino do bot.** O `sales_teams.csv` não tem email nem Slack de ninguém, então `targets.json` é um diretório mantido à mão (em produção viria do SSO).
- **Escala.** Trocar `load()` por uma query no CRM é a única mudança necessária. Com uma base 100 vezes maior, a curva precisa de um algoritmo O(n log n), anotado no código.

---

## Process Log — Como usei IA

O registro completo, com os erros, está em [`process-log/PROCESS.md`](process-log/PROCESS.md). O histórico de commits da branch mostra a evolução.

| Ferramenta | Para que usei |
|---|---|
| Claude Code (Claude Opus 5.5 e Claude Sonnet 5) | Exploração dos dados, testes estatísticos, motor, app, revisão visual e documentação |
| Codex (`/codex:adversarial-review`) | Revisão adversarial da correção do motor, por um modelo diferente do que a escreveu |
| Claude Design | Mockup de referência que guiou o visual da Overview |
| Impeccable e Humanizer (skills do Claude Code) | Detector de padrões de interface gerada por IA; revisão do texto |
| Chrome headless e Claude in Chrome | Screenshots e medição do layout no desktop e no celular |

### Onde a IA errou e como corrigi

| Erro | Como apareceu | Correção |
|---|---|---|
| Sugeriu "esse vendedor fecha 40% menos que os pares" | Teste de significância: p = 0,22 | Nenhuma feature entra no score sem passar no teste |
| Rotulou 2 vendedores como acima ou abaixo da média | 35 comparações a 95% geram 1 ou 2 falsos positivos | Correção de Bonferroni e um teste que impede o rótulo |
| A curva de "fecham em 30 dias" ignorava os deals abertos | Auditoria externa do motor | Os abertos entraram no denominador |
| O score tinha correlação de 0,90 com o preço, quase "ordenar por valor" | Mesma auditoria | O score virou a chance de ganhar em 30 dias, sem o preço |
| No celular, a página ficava com 712 px numa tela de 390 px | Auditoria final, renderizando num iframe de 390 px | Coluna do grid em `minmax(0, 1fr)` |
| A ficha do deal dizia "28% de chance de **fechar**" ao lado de "chance de fechar 40%" | Review crítico com olhar de avaliador (seção 20 do PROCESS.md) | Um número só, "chance de ganhar em 30 dias", com o mesmo nome em todas as telas |
| A Overview mostrava US$ 116,8 mil e US$ 120,5 mil como a mesma "receita esperada" | Mesmo review | Os dois lugares usam o mesmo total |
| Deal sem conta era sugerido para "encerrar como perdido" | Mesmo review: 68% dos abertos não têm conta, e isso é cadastro, não sinal | A sugestão usa só o tempo parado; a conta vira tarefa de cadastro |
| Os 259 deals da fila Fechar tinham a mesma frase de ação | Mesmo review | Ação por fase da curva e pelo histórico da conta |

### O que eu adicionei que a IA sozinha não faria

- **Contexto de operação real.** A ideia de que o deal "morto" pede uma decisão, e não um alerta que nunca para, vem do CRM que eu uso em produção.
- **Escopo de produto.** A IA começou com uma tela só. Eu puxei para um app de vendas completo, pegando o melhor do Salesforce e refinando.
- **Desconfiança do output.** Conferi os números na tela antes de irem para o README. Vários erros da tabela só apareceram porque revisei a saída em vez de aceitar "os testes passaram".
- **Olhar de quem avalia.** No fim, pedi um review como o de um diretor que vai avaliar o trabalho, e corrigi o que confundia quem usa, não só o que estava errado no código.

---

## Evidências

- [x] Process log: [`process-log/PROCESS.md`](process-log/PROCESS.md)
- [x] Screenshots da versão atual em [`process-log/screenshots/`](process-log/screenshots/) (12 a 17); as de versões anteriores ficam em `screenshots/old/`
- [x] Git history: commits da branch `submission/hisdevotions-afk`

---

_Submissão enviada em: 07/11/2026_
