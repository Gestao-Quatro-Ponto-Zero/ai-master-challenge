# Submissão — Daniel Gomes Resende — Challenge 003

## Sobre mim

- **Nome:** Daniel Gomes Resende
- **LinkedIn:** https://www.linkedin.com/in/danielgresende/
- **Challenge escolhido:** 003 — Lead Scorer

---

## Executive Summary

Olhei os dados antes de desenhar e eles mudaram o produto. Nestes dados, nada do que se sabe de um negócio aberto (produto, setor, porte, vendedor) separa ganho de perda; só o tempo separa. Existe uma janela: nenhum negócio foi ganho depois de 138 dias aberto, e os fechamentos acontecem até o fim do trimestre seguinte ao do engajamento. Por isso a ferramenta não dá nota: ela diz ao vendedor, na segunda de manhã, quais negócios ainda estão **vivos**, o que está na **fila para engajar** e o que é **para limpar**. Em doze datas de teste, nenhum dos 717 negócios distintos que saíram da janela foi ganho. A recomendação principal é limpar o pipeline: na data dos dados, 1.474 dos 1.589 negócios em andamento já estão fora da janela.

---

## Solução

### Como rodar

Precisa só de Python (testado com 3.12 e 3.14; nada para instalar, `requirements.txt` é vazio). Da raiz do repositório:

```bash
python3 submissions/daniel-resende/solution/run.py --port 8000
```

O comando recalcula tudo a partir dos quatro CSVs e abre em **http://127.0.0.1:8000/**. Não precisa de chave de API nem de conta: os textos de IA já vêm gerados no repositório, e a tela funciona igual sem eles.

Outros comandos, todos da raiz e todos só com Python:

| Comando | O que faz |
|---|---|
| `python3 submissions/daniel-resende/solution/build.py` | recalcula os arquivos de cada segunda-feira em `solution/out/` |
| `python3 submissions/daniel-resende/solution/check_contract.py` | confere cada arquivo emitido contra `docs/contrato-score.md` e os textos contra os fatos |
| `python3 -m unittest discover -s submissions/daniel-resende/solution/tests` | os testes, em linhas reais do dataset |
| `python3 submissions/daniel-resende/solution/numbers.py` | imprime cada número citado neste README (saída guardada em `docs/numeros-saida.txt`) |
| `python3 submissions/daniel-resende/solution/drift.py` | relatório de desvio: diz se a janela mudou em relação à guardada em `solution/window.json` |
| `python3 submissions/daniel-resende/solution/validate.py` e `confirm.py` | a validação da regra, sem vazamento, e a confirmação em datas novas |
| `python3 submissions/daniel-resende/solution/ai/check.py` | confere os 148 textos de IA guardados |
| `python3 submissions/daniel-resende/solution/ai/generate.py` | regenera os textos (só este precisa do Claude Code instalado e logado; não usa chave de API) |

### Abordagem

1. **Auditoria antes de qualquer tela** (`solution/audit.py`). O que um negócio aberto carrega de verdade: não tem valor de fechamento, 1.425 dos 2.089 abertos não têm conta, e os 500 em Prospecting não têm data nenhuma.
2. **Validação pelo tempo e pelo que se sabia** (`solution/validate.py`). Para cada data de corte, o código apaga tudo o que aconteceu depois, decide com o que sobrou e só então olha o desfecho. Comparei três candidatos de score com "ordenar por valor".
3. **Confirmação com a regra congelada** (`solution/confirm.py`). Três datas que não moldaram a regra, e a contagem em negócios distintos.
4. **O produto que os dados sustentam.** A promessa inicial era "os cinco primeiros" de cada vendedor. Os dados não sustentam isso; sustentam a separação entre vivo e para limpar. O produto foi redesenhado em cima dela.

### A lógica, nas palavras do vendedor

- **Vivo**: o negócio ainda está dentro da janela em que negócios já foram ganhos, ou seja, aberto há no máximo 138 dias e antes do fim do trimestre seguinte ao que começou.
- **Para limpar**: passou de um dos dois limites. Nenhum negócio assim foi ganho nos testes. A ação é encerrar no CRM e parar de gastar a segunda-feira com ele. A tela não diz por que parou: os dados não dizem.
- **Fila para engajar**: ainda não tem data de engajamento. É só uma lista por preço de tabela; nada mais nos dados ordena esses negócios.
- **Valor** é o preço de tabela do produto, porque negócio aberto não tem valor de fechamento.
- **Entre os vivos**, a ordem é por valor de tabela e, no empate, quem tem mais dias restantes vem primeiro. A contagem regressiva e a marca "esfriando" (vivo há mais de 90 dias) informam, mas não mudam a ordem.
- **"Cerca de X em cada 100"**: para cada idade, quantos negócios que chegaram abertos até ali foram ganhos depois. É uma conta sobre todos os negócios daquela idade, com a data da conta; não é a chance de um negócio.
- **Segunda-feira do passado**: a tela mostra o que teria dito em cinco segundas de 2017, só com o que se sabia naquele dia, e o que aconteceu depois com cada negócio.
- **Gestor**: valor vivo contra valor parado por vendedor, gestor e regional; quem não tem nenhum vivo; o tamanho das filas. Só fatos.
- **IA**: redige o próximo passo de cada negócio vivo, o briefing de segunda de cada vendedor e o resumo de cada gestor. Não decide nem calcula: todo número e todo nome é um marcador que o código preenche, e um texto com um dígito fora de marcador é recusado.

### Resultados / Findings

Todos os números abaixo saem de `solution/numbers.py` (`docs/numeros-saida.txt`).

**A afirmação que sustenta o produto: vivo ou para limpar.**

- O ganho mais demorado levou 138 dias; 6.710 de 6.711 fechamentos ocorreram até o fim do trimestre seguinte ao do engajamento.
- Nos doze cortes medidos, **717 negócios distintos** saíram da janela: **nenhum foi ganho depois**, 1 foi perdido e 716 seguiam abertos no fim dos dados.
- Nas cinco segundas do passado que a tela mostra, os negócios para limpar eram 92, 350, 350, 420 e 717: nenhum foi ganho depois.
- O limite, dito com clareza: os cortes se sobrepõem no tempo e não existe período que a regra nunca viu. É uma checagem de que a regra não foi ajustada a datas específicas, não um teste independente.

**A segunda-feira padrão (01/01/2018, dados fechados em 31/12/2017).**

| | Negócios | Valor de tabela |
|---|---|---|
| Vivos | 115 | US$ 235.930 |
| Fila para engajar | 500 | US$ 1.073.986 |
| Para limpar | 1.474 | US$ 3.656.299 |

18 dos 35 vendedores não têm nenhum negócio vivo. A regional Central tem toda a fila (500) e nenhum vivo; East e West têm os vivos (45 e 70) e nenhuma fila.

**A ordem entre os vivos é secundária.** Nas três datas de confirmação, a regra que ordena por tempo e valor ganhou de "ordenar por valor" no top 5 de cada vendedor (valor ganho em 90 dias: 432.044 contra 396.111; 321.094 contra 295.729; 238.551 contra 229.454). Mas a ordem que a tela usa (valor de tabela, com mais dias restantes no desempate) **não foi confirmada em datas novas**. E com 7 preços de tabela, ordenar por valor é quase ordenar por produto: em 52 dos 98 pares vizinhos das listas de vivos, o valor empata e quem decide é o desempate.

**O tempo, nas palavras do vendedor** (conta de 31/12/2017, 4.767 negócios que já tinham tido tempo de fechar): de cada 100 que chegaram abertos aos 0, 30, 60, 90, 120 e 138 dias, foram ganhos depois cerca de 47, 42, 39, 26, 4 e 0.

**As telas** (capturas em `process-log/screenshots/`):

- [O vendedor na segunda-feira](process-log/screenshots/02-vendedor-segunda-1920.png) e [no celular](process-log/screenshots/04-vendedor-celular-412.png)
- [Um vendedor que só tem fila](process-log/screenshots/05-vendedor-so-com-fila-1366.png)
- [Uma segunda-feira do passado, com o que aconteceu depois](process-log/screenshots/06-segunda-do-passado-1366.png)
- [A saúde do pipeline para o gestor](process-log/screenshots/07-gestor-1920.png)

### Recomendações

1. **Limpar o pipeline.** 1.474 negócios, US$ 3.656.299 de tabela, estão fora da janela em que algo já foi ganho. Encerrar no CRM, ou reabrir com data nova quando houver fato novo.
2. **Olhar a Central.** A regional não tem nenhum negócio vivo e concentra os 500 negócios da fila. É a primeira conversa do gestor.
3. **Registrar o que falta.** Conta em todo negócio aberto e a data de entrada em Prospecting: sem elas a fila não pode ser ordenada nem medida.
4. **Medir o ganho de verdade** com um grupo de controle: metade do time com a ferramenta, metade sem, por um ciclo de vendas.

### Limitações

- **A janela é uma regularidade deste dataset.** Os 138 dias e o prazo do trimestre foram vistos nos dados inteiros antes de a regra ser escrita. `drift.py` avisa quando eles mudarem.
- **A ordem entre os vivos não foi confirmada** em datas novas, e é quase ordem por produto.
- **A frase "cerca de X em cada 100"** descreve uma faixa de idade, não um negócio, e o nível muda com a data da conta (aos 90 dias: 38 em agosto, 33 em outubro, 26 em dezembro; `docs/confirmacao-saida.txt`). Nas duas segundas mais antigas a conta ainda não existe, e a tela diz isso.
- **A fila não é medida por nada**: sem data, nenhum teste alcança esses negócios, e ela não pode ser reconstruída no passado.
- **"Para limpar" não diz o motivo.** Os dados não distinguem negócio abandonado de negócio que ninguém atualizou no CRM.
- **Valor é preço de tabela**, não receita esperada.
- **Os textos de IA** existem só para a segunda padrão. A conferência garante números e nomes; contra julgamento indevido ela usa uma lista de palavras, que não pega tudo.
- **Não medido**: celular real (só emulado) e o escurecimento automático de alguns navegadores de celular.
- **Fora do escopo**: login, edição do CRM, envio por e-mail ou Slack, previsão de receita. A fonte da interface (Bricolage Grotesque) vai junto, sob a licença OFL (`solution/web/fonts/OFL.txt`).

---

## Process Log — Como usei IA

> **Este bloco é obrigatório.** Sem ele, a submissão é desclassificada.

### Ferramentas usadas

_Liste as ferramentas de IA que usou e para quê._

| Ferramenta | Para que usou |
|------------|--------------|
| _ex: Claude Code_ | _Análise exploratória dos dados e geração de gráficos_ |
| _ex: Cursor_ | _Construção do protótipo web_ |
| _ex: ChatGPT_ | _Brainstorm de hipóteses iniciais_ |

### Workflow

_Descreva passo a passo como você trabalhou. Onde a IA entrou em cada etapa?_

1.
2.
3.

### Onde a IA errou e como corrigi

_A IA fez algo errado? Você percebeu? Como corrigiu?_



### O que eu adicionei que a IA sozinha não faria

_Qual foi seu julgamento, contexto, ou insight que fez diferença?_



---

## Evidências

_Anexe ou linke as evidências do processo:_

- [ ] Screenshots das conversas com IA
- [ ] Screen recording do workflow
- [ ] Chat exports
- [ ] Git history (se construiu código)
- [ ] Outro: _____________

---

_Submissão enviada em: [data]_
