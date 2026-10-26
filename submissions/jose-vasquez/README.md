# Submissão — José Vásquez Valenzuela — Challenge 003

## Sobre mim

- **Nome:** José Vásquez Valenzuela
- **LinkedIn:** [linkedin.com/in/josé-vásquez-valenzuela-2a6376328](https://www.linkedin.com/in/jos%C3%A9-v%C3%A1squez-valenzuela-2a6376328)
- **Challenge escolhido:** 003 — Lead Scorer

---

## Executive Summary

Construí o **Lead Scorer "Segunda-feira"**, uma ferramenta com duas telas. O **vendedor** abre e vê **as 5 vendas da semana** (até 5 de maior valor esperado), cada uma com nota de 0 a 100, o motivo em português, a próxima ação e um botão para marcar como feita. A **chefe de vendas** vê **o pipeline de verdade**: o CRM mostra US$ 5,0 mi em vendas abertas, mas 1.291 delas (US$ 3,2 mi) estão paradas há mais tempo do que qualquer venda da história levou, e 546 não têm cliente cadastrado. No teste com o passado (4 datas de 2017), focar nos 20% do topo da lista capturou **59,2% da receita dos 90 dias seguintes**, contra 48,4% ordenando só por preço, 45,3% com a nota "óbvia" (taxa do vendedor no produto × preço) e 20,0% ao acaso. A principal recomendação: **limpar o pipeline antes de qualquer previsão**, porque nos testes o CRM mostrou 3 a 5 vezes o que entrou de fato.

---

## Solução

### Como rodar

**Abrir a ferramenta:** dois cliques em `solution/app/index.html`. Não precisa instalar nada.

**Online, sem instalar nada:** **https://joseteiadirector.github.io/ai-master-challenge/submissions/jose-vasquez/solution/app/**

Os dados do desafio terminam em 31/12/2017, então a ferramenta trata esse dia como "hoje".

**Recalcular e testar** (Python 3.10+; o teste da tela usa Node 22+ e Google Chrome):

```bash
pip install -r solution/requirements.txt
python3 solution/analise/01_dados.py        # o que os dados mostram (etapa 2)
python3 solution/testes/teste_passado.py    # a nota funciona? (grava docs/resultado-teste.*)
python3 solution/motor/nota.py              # gera solution/app/dados.js
node solution/testes/teste_tela.mjs         # clica em tudo na tela e tira as fotos
```

Os 4 CSVs originais do Kaggle estão em `solution/data/`, sem alteração.

### Abordagem

1. **Entender o problema antes dos dados.** A chefe de vendas tem duas queixas: tempo gasto em vendas que não fecham e vendas boas que esfriam. Daí os dois usuários: o vendedor (onde focar) e a chefe (o que é real no pipeline).
2. **Desenhar a arquitetura antes do código** ([`docs/arquitetura.md`](docs/arquitetura.md)): dados → motor em Python → página estática. Abre com dois cliques e pode ser ligada a um CRM sem mexer na tela.
3. **Testar cada hipótese nos dados** antes de ela entrar na nota. Vendedor, produto, setor, região, gerente e porte foram descartados com números.
4. **Medir a chance sem olhar o futuro.** "Fotos do passado": em cada fim de mês, quais vendas estavam abertas, há quantos dias, e quantas foram ganhas nos 90 dias seguintes.
5. **Provar que a nota funciona** contra quatro alternativas, inclusive a nota "óbvia" que usa os atributos sugeridos pelo próprio desafio, com um teste que confere se o motor não espia o futuro.
6. **Construir a tela pensando na segunda-feira de manhã** e testá-la com cliques automáticos.

### Resultados / Findings

**A ferramenta** (fotos em [`docs/screenshots/`](docs/screenshots/)):

| Tela | O que mostra | Botões |
|---|---|---|
| **Vendedor** | As 5 da semana: até 5 vendas de maior valor esperado, sem as de valor muito baixo (nota abaixo de 20). Cada uma com nota, motivo, próxima ação, chance e valor esperado. Depois, as outras vendas abertas e duas listas de limpeza | Feito · Ainda viva / Encerrar · Cadastrado |
| **Chefe de vendas** | Pipeline do CRM × previsão real de 90 dias × parado × sem cliente, com a explicação da diferença, filtro por região e gerente, e o próximo passo de cada vendedor | — |
| **Como a nota funciona** | Os 5 passos da nota, a curva de chance e o resultado dos testes | Apagar marcações |

**Como a nota é calculada:**

| Passo | Regra (vinda dos dados) |
|---|---|
| 1. Chance pelo tempo aberta | Fotos de 12 fins de mês. Até 100 dias: 44% a 59%. Depois cai: 45% → 32% → 22% → 10% → 0% aos 138 dias |
| 2. Relação vendedor-cliente | Se o vendedor já ganhou com aquele cliente: 57%; sem histórico: 48% |
| 3. Ajuste pelo último trimestre | A chance caiu ao longo de 2017. O motor confere o último trimestre já conhecido (previu 734 vendas ganhas, foram 576) e multiplica a chance por 78% |
| 4. Valor esperado | Chance × preço do produto (o valor fechado é o preço de tabela) |
| 5. Nota de 0 a 100 | Posição do valor esperado entre as vendas abertas |

| Status | Regra | Próxima ação |
|---|---|---|
| Fase de risco | até 14 dias (metade das vendas perdidas morre nesse prazo) | Falar com o cliente esta semana |
| Ativa | 15 a 100 dias | Avançar para a proposta |
| Esfriando | 101 a 138 dias | Pedir uma decisão |
| Prospecção | sem data de início no CRM | Primeiro contato |
| Parada | mais de 138 dias | Confirmar ou encerrar |
| Sem cliente | cliente não cadastrado | Cadastrar o cliente |

**O que os dados mostraram** (script [`solution/analise/01_dados.py`](solution/analise/01_dados.py)):

| Descoberta | Número |
|---|---|
| Negociações paradas além da venda mais longa da história (138 dias) | 1.291 de 1.589 (81%), US$ 3,2 mi |
| Vendas abertas sem cliente | 1.425 de 2.089; nenhuma das 6.711 encerradas estava sem cliente |
| Taxa de ganho por produto, setor, região, gerente e porte | Sempre entre 60% e 66% |
| Diferença entre vendedores (55% a 70%) | 33% de chance de ser só acaso (sorteio com 1.000 rodadas) |
| A taxa de um semestre se repete no outro? | Quase não: vendedor 0,23; produto 0,18; setor −0,13 |
| Vendas perdidas | Metade morre nos primeiros 14 dias |
| Região Central | Tem as 500 prospecções do dataset; as outras regiões não têm nenhuma |

**Teste com o passado** (4 datas, 30/06 a 30/09/2017; resultado completo em [`docs/resultado-teste.txt`](docs/resultado-teste.txt)):

| Focando nos 20% do topo da lista | Receita dos 90 dias seguintes capturada |
|---|---|
| **Nota do Lead Scorer** | **59,2%** |
| Nota só pelo tempo aberta | 56,4% |
| Só o maior preço | 48,4% |
| Nota "óbvia": taxa do vendedor no produto × preço | 45,3% |
| Ao acaso ("feeling", média de 1.000 sorteios) | 20,0% |

A nota ganhou de cada alternativa **nas 4 datas**. Vendas empatadas (mesmo preço, mesma nota) são ordenadas por sorteio, com média de 200 sorteios, para nenhum método ganhar pela ordem do arquivo. O teste também embaralha tudo o que aconteceu depois da data e confere que o motor aprende exatamente o mesmo.

**Previsão para a chefe de vendas:**

| Data | O CRM mostrava | A ferramenta previu | Entrou em 90 dias |
|---|---|---|---|
| 30/06/2017 | US$ 4,2 mi | US$ 1,5 mi | US$ 1,4 mi |
| 31/07/2017 | US$ 5,5 mi | US$ 1,6 mi | US$ 1,7 mi |
| 31/08/2017 | US$ 5,4 mi | US$ 1,5 mi | US$ 1,3 mi |
| 30/09/2017 | US$ 5,8 mi | US$ 1,5 mi | US$ 1,2 mi |

### Recomendações

1. **Limpar o pipeline primeiro.** Revisar as 1.291 vendas paradas (US$ 3,2 mi) e cadastrar o cliente das 546 vendas sem cliente. Enquanto isso não acontece, qualquer relatório do CRM está inflado: nos testes ele mostrou 3 a 5 vezes o que entrou.
2. **Perguntar ao time de CRM se o cliente só é preenchido no fechamento.** Se for, as vendas sem cliente podem voltar para a lista com nota. Se não for, são registros sem cliente real e devem sair do pipeline.
3. **Usar a ferramenta toda segunda-feira:** cada vendedor trabalha as 5 da semana e marca o que fez; a chefe acompanha o próximo passo de cada um.
4. **Não premiar nem cobrar vendedores pela taxa de ganho.** A diferença entre eles é compatível com acaso e não se repete de um semestre para o outro.
5. **Olhar a região Central.** Ela tem todas as 500 prospecções do dataset, e as 408 negociações dela estão abertas há 138 dias ou mais (403 já passaram do limite): as prospecções não estão virando negociação nova.
6. **Registrar a data de criação das prospecções e o motivo das perdas.** São os dados que mais melhorariam a nota.

### Limitações

- **A chance ainda é um pouco otimista nas vendas mais promissoras,** mesmo com o ajuste do último trimestre: prevê 62% e acontecem 54%. Nas faixas médias acerta melhor (prevê 44%, acontecem 47%; prevê 54%, acontecem 51%). A ordem das vendas está certa, que é o que importa para priorizar.
- **A previsão da chefe erra entre −4% e +25%** nas 4 datas (antes do ajuste, errava de +12% a +35%). O ajuste usa só o último trimestre e chega com atraso quando a queda continua.
- **Prospecções não têm data no dataset.** Não dá para testar a chance delas; usamos a de uma venda que acabou de começar. Por isso o teste com o passado só avalia vendas em negociação.
- **O preço pesa muito.** Vendas do mesmo produto, na mesma faixa de dias e com a mesma relação ficam com a mesma nota.
- **As marcações ficam no navegador de cada vendedor.** Para o time inteiro, precisariam ir para o CRM.
- **Para escalar:** ligar o motor ao CRM (hoje lê CSV), rodar todo dia, acrescentar sinais de atividade (e-mails, reuniões, que não existem nos dados) e controlar o acesso por vendedor (hoje cada um escolhe o próprio nome).

---

## Process Log — Como usei IA

> Detalhes em [`process-log/`](process-log/): uma narrativa por etapa e os trechos da conversa com a IA.

### Ferramentas usadas

| Ferramenta | Para que usou |
|---|---|
| Claude Code (Claude Opus 5.5) | Leitura do desafio, exploração dos dados, testes estatísticos, motor da nota, tela HTML/JS, testes automáticos e documentação |
| Python + pandas + numpy | Análise, motor e teste com o passado |
| Node + Google Chrome sem janela | Teste automático da tela e fotos |
| Git | Histórico de cada etapa |

### Workflow

1. Pedi à IA para explicar o desafio em linguagem simples e só segui depois de concordar com o resumo.
2. Decidi os dois usuários (vendedor e chefe de vendas) e exigi a arquitetura documentada antes do código.
3. Conferi que os dados eram os oficiais (85 clientes, 7 produtos, 35 vendedores, 8.800 vendas).
4. Exploração: cada hipótese virou um número; as que não passaram ficaram fora da nota.
5. Motor → teste com o passado → correções → novo teste.
6. Tela → teste automático com cliques → fotos → correções.
7. Revisão final: cada número da documentação conferido com a saída dos scripts.

### Onde a IA errou e como corrigi

| Erro da IA | Como foi pego | Correção |
|---|---|---|
| "Vendas que passam de 90 dias fecham 71%" | O número só conta vendas que já fecharam (viés de sobrevivência) | Chance medida com fotos do passado: até 100 dias fica entre 44% e 59% e depois cai a zero |
| Mandou 879 vendas paradas há mais de 138 dias para a lista "cadastrar cliente" | Conferindo a contagem de cada lista | Parada vem antes de cadastro: não faz sentido cadastrar o cliente de uma venda morta |
| Primeiro teste deu "só o maior preço" = 42,7% | Número diferente do esperado; investigando, só há 7 preços e o resultado dependia da ordem dos empates | Empates desfeitos por sorteio (média de 200): 48,4% |
| Tela da chefe dizia o mesmo "próximo passo" para todos os vendedores | Olhando as fotos geradas pelo teste | Próximo passo específico de cada vendedor |
| A chance era otimista (previa 66%, fechavam 53%) e a previsão errava de +12% a +35% | Teste com o passado; a causa: a chance de ganhar caiu ao longo de 2017 (62% em janeiro, 44% em setembro), e as fotos chegam com 90 dias de atraso. Usar só fotos recentes não resolveu | Ajuste pelo último trimestre já conhecido: erro da previsão passou para −4% a +25%, sem mudar a ordem das vendas |

### O que eu adicionei que a IA sozinha não faria

- **Dois usuários.** A ferramenta não é só para o vendedor: quem fez o pedido foi a chefe de vendas, e ela precisa saber quanto do pipeline é real.
- **Arquitetura e dados conferidos antes de qualquer código.** Pedi a arquitetura documentada desde o início e conferi os dados contra a descrição do desafio.
- **Zero número sem prova.** Exigi que cada número da documentação saísse de um script, e que tudo fosse testado de novo antes da entrega.
- **Atacar os pontos fracos em vez de só declarar.** A chance otimista estava escrita nas limitações; pedi para corrigir a causa antes de entregar.
- **Nada que pareça estranho para quem usa.** Na revisão final, não aceitei dois pontos que estavam certos nos dados, mas confundiriam: uma venda de US$ 16 entre as 5 da semana, e a previsão de US$ 0,2 mi ao lado dos US$ 5,0 mi do CRM sem explicação. A semana passou a ignorar vendas de valor muito baixo, e a tela da chefe passou a explicar a diferença.

---

## Evidências

- [x] Narrativa escrita do processo, etapa por etapa — [`process-log/`](process-log/)
- [x] Trechos da conversa com a IA: as minhas mensagens que mudaram o rumo do trabalho — [`process-log/04-trechos-da-conversa.md`](process-log/04-trechos-da-conversa.md)
- [x] Git history — um commit por etapa
- [x] Scripts que reproduzem cada número — [`solution/analise/`](solution/analise/) e [`solution/testes/`](solution/testes/)
- [x] Resultado do teste com o passado — [`docs/resultado-teste.txt`](docs/resultado-teste.txt)
- [x] Teste automático da tela e fotos — [`solution/testes/teste_tela.mjs`](solution/testes/teste_tela.mjs) e [`docs/screenshots/`](docs/screenshots/)

---

_Submissão enviada em: 26/10/2026_
