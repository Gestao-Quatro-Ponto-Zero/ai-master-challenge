# Submissão — Renan de Castro Albuquerque — Challenge 003

## Sobre mim

- **Nome:** Renan de Castro Albuquerque
- **LinkedIn:** https://www.linkedin.com/in/renan-castro-albuquerque/
- **Challenge escolhido:** 003 — Lead Scorer

---

## Executive Summary

Construí uma ferramenta em Streamlit que diz ao vendedor onde focar, separando o pipeline em três listas com uma ação clara cada: **Focar**, **Prospectar** e **Limpar**. Antes de construir, a análise dos dados mostrou que **62% do pipeline aberto (1.291 de 2.089 deals) está parado há mais tempo do que qualquer deal já levou para fechar** neste CRM — então o maior ganho não é um score sofisticado, é separar o que está vivo do que provavelmente morreu. O score usa valor esperado (chance × preço), em que a chance vem da idade do deal, o único fator que se sustentou num teste com dados que o modelo não tinha visto. A ferramenta não encerra deals sozinha: o vendedor confirma, e cada confirmação registra o último contato — um dado que o CRM não tinha.

---

## Solução

### Como rodar

Requisitos: Python 3.10+.

```bash
cd solution
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
streamlit run app.py
```

Abre em `http://localhost:8501`. Os dados (CC0, do [Kaggle](https://www.kaggle.com/datasets/agungpambudi/crm-sales-predictive-analytics)) já estão em `solution/data/`.

Outros comandos:

| Comando | O que faz |
|---|---|
| `python dados.py` | Confere a carga dos dados (8.800 deals, 2.089 abertos) |
| `python score.py` | Mostra o top 3 de cada lista no terminal |
| `python validacao.py` | Roda o teste que justifica o score (ver abaixo) |

As decisões dos botões ficam em `solution/decisoes.csv`. Para começar do zero, use **"Desfazer todas as decisões"** na barra lateral.

### Estrutura do código

```
dados.py      → carrega os 4 CSVs, corrige problemas e junta tudo
score.py      → calcula lista, chance, valor esperado e a explicação de cada deal
decisoes.py   → salva e aplica as decisões do vendedor (Manter / Encerrar / Recomeçar)
app.py        → a tela
validacao.py  → testa se o score prevê deals que ele não viu
```

### Abordagem

1. **Auditei os dados antes de qualquer código.** Problemas encontrados e tratados:
   - O pipeline escreve `GTXPro` e o catálogo `GTX Pro` → o join perdia o preço sem erro.
   - Os dados vão até 31/12/2017 → essa é a data de "hoje" da ferramenta (senão todo deal teria 8 anos).
   - 68% dos deals abertos não têm conta → tamanho/setor da conta não serve para a maioria.
   - Só 30 dos 35 vendedores têm deals; só 2.089 dos 8.800 deals estão abertos.
2. **Defini o problema pelo uso, não pelo modelo:** o vendedor precisa saber *o que fazer* com cada deal. Daí as três listas, cada uma com uma ação.
3. **Validei cada ideia antes de colocar no score** (treino nos deals fechados até jun/2017, teste nos que entraram depois).
4. **Testei a tela como usuário**, encontrei falhas de usabilidade e corrigi.

### Lógica do score

| Lista | Quem entra | Ordem | Ação |
|---|---|---|---|
| 🎯 Focar | Em negociação há até 138 dias | Valor esperado | Trabalhar para fechar |
| 🌱 Prospectar | Ainda não entrou em negociação | Valor esperado | Iniciar contato |
| 🧹 Limpar | Em negociação há mais de 138 dias | Maior valor; empate → parado há menos tempo | Confirmar com o cliente |

**Por que 138 dias?** É o maior tempo que um deal fechado já levou neste CRM. Acima disso, não existe histórico para estimar a chance.

**Valor esperado = chance de fechar × preço de tabela.** Sem o preço, um deal de US$ 55 com 80% ficaria acima de um de US$ 26.768 com 70%. O preço vem do catálogo, porque `close_value` só existe depois que o deal fecha (usá-lo seria vazamento).

**A chance vem da idade do deal.** Deals perdidos morrem cedo (mediana de 14 dias); os ganhos demoram mais (mediana de 57). Então, quem sobrevive já passou da fase em que a maioria dos perdidos morre:

| Deal ainda aberto no dia... | 0 | 30 | 90 | 120 |
|---|---|---|---|---|
| % que foi ganho no histórico | 63% | 68% | 71% | 75% |

**O que ficou de fora, e por quê:**

| Fator | Resultado do teste | Decisão |
|---|---|---|
| Vendedor × produto (taxa varia de 47% a 81%) | Correlação de **−0,04** entre duas metades aleatórias dos dados → é sorte, não talento. AUC 0,502 | Fora do cálculo. Aparece na tela como histórico, com aviso, para o vendedor não achar que a ferramenta ignora o desempenho dele |
| Produto, setor, região, manager | Taxa de ganho entre 60% e 65% em todos | Fora |
| Dados da conta | Faltam em 68% dos deals abertos | Fora |

**Resultado da validação** (`python validacao.py`):

| Score | AUC |
|---|---|
| Média geral (sem modelo) | 0,500 |
| Vendedor × produto | 0,502 |
| Vendedor × produto + idade | 0,519 |
| **Só idade (escolhido)** | **0,536** |

O ganho é modesto e eu não escondo isso: os dados têm pouco sinal. O valor da ferramenta está mais na triagem do pipeline e na clareza da ação do que na precisão do score.

### Humano no controle

Na lista Limpar, a ferramenta **sugere, mas não decide**. O CRM não tem nenhum registro de contato, então ela não tem como saber se o cliente ligou ontem. O vendedor escolhe:

- ✅ **Manter** — ainda está negociando. O deal volta para Focar e a data vira o **último contato confirmado**: a ferramenta passa a gerar o dado que faltava.
- ❌ **Encerrar** — desistiu. Sai do pipeline, mas **não** entra no histórico de perdidos (um deal de 400 dias distorceria a curva de idade).
- ♻️ **Recomeçar** — vale tentar com uma proposta nova. Vira prospect, como uma negociação nova.

Toda decisão mostra para onde o deal foi e pode ser desfeita.

### Recomendações

1. **Limpar o pipeline primeiro.** 1.291 deals parados escondem os 298 que estão vivos. Começar pelos GTK 500 (US$ 26.768 cada).
2. **Registrar a data de criação dos deals e cada contato com o cliente.** São os dois dados que mais limitam a ferramenta hoje.
3. **Recalibrar o score a cada trimestre** com os deals recém-fechados (`validacao.py` já faz o teste).

### Limitações

- **A chance sai otimista em ~6 pontos.** No teste, previsões de 67% e 72% viraram 60% e 67% na prática: o 2º semestre de 2017 teve taxa de ganho menor que o 1º, e o score não tem como saber disso.
- **Prospectar é ordenado só pelo valor do produto.** O CRM não registra quando o deal foi criado, então um prospect esquecido há um ano parece igual a um de ontem.
- **Não há registro de atividade.** "Esfriar" só pode ser medido pela idade desde o início da negociação, até o vendedor começar a usar o botão Manter.
- **As decisões ficam num CSV local.** Para um time inteiro, precisariam ir para um banco de dados ou de volta para o CRM.
- **Os dados são de um CRM fictício** (2016–2017). Os achados valem para este dataset; num CRM real, a validação precisa ser refeita.

### Próximos passos (para escalar)

- Gravar as decisões no próprio CRM, via API, em vez de num CSV.
- Usar os registros de "Manter" para incluir a recência do contato no score.
- Uma visão para o manager: quem tem mais deals parados e quanto valor está preso em Limpar.

---

## Process Log — Como usei IA

> O log detalhado, decisão por decisão, está em [`process-log/notas-processo.md`](process-log/notas-processo.md).

### Ferramentas usadas

| Ferramenta | Para que usei |
|---|---|
| Claude (chat com execução de código) | Segunda leitura do repositório, auditoria dos dados, escrita do código, testes automáticos e prints da tela |
| Streamlit | Interface |

### Workflow

1. Li o desafio e pedi ao Claude uma segunda leitura procurando pegadinhas no repositório e nos dados.
2. Antes de codar, discuti o problema com o Claude em formato de perguntas: quem usa, que decisão toma, o que o score deve medir.
3. Construí em etapas (dados → score → tela → envio), rodando e conferindo os números na minha máquina a cada etapa.
4. Validei o score com dados que o modelo não viu, antes de confiar nele.
5. Testei a tela como se fosse o vendedor, encontrei problemas e pedi as correções.

### Onde a IA errou e como corrigi

1. **Disse que deal mais velho tem menos chance.** O teste mostrou o contrário até 138 dias.
2. **Tratou vendedor × produto como sinal.** O teste mostrou que era ruído (correlação −0,04) → saiu do cálculo.
3. **Primeira versão da tela** com valor cortado ("US$ 26....") e setas ↑ que sugeriam crescimento → corrigido olhando a tela.
4. **No roteiro de testes, previu 33 deals em Limpar para a Rosalina.** Testando, eu vi 34: o número dela tinha sido medido depois de um teste que já tinha encerrado um deal.
5. **Depois de um clique, o seletor de listas ficava sem nenhuma opção marcada** → corrigido.

### O que eu adicionei que a IA sozinha não faria

1. **Criei o botão "Recomeçar"**, porque assim o vendedor tem a oportunidade de fechar uma venda com um cliente que antes estava dado como "morto", voltando com uma nova abordagem.
2. **Separei os deals em listas, cada uma com uma ação**, para deixar de forma intuitiva e objetiva o que precisa ser feito. Assim o vendedor consegue usar o sistema sem que nada fique bagunçado.
3. **Criei a terceira lista (Prospectar) e calculei o score dela também**, porque a ferramenta faz um cálculo real e mostra o porquê da posição de cada deal — por exemplo, por que um deal de US$ 26 mil com 70% de chance vem antes de um de US$ 55 com 80%.
4. **Fiz o botão "Manter" registrar a data do clique como último contato**, porque o CRM não tinha essa informação e quem sabe se o cliente ainda está ativo é o vendedor. Assim, a própria ferramenta passa a criar o dado que faltava.

---

## Evidências

- [x] Log de processo: `process-log/notas-processo.md`
- [x] Conversa completa com o Claude: https://claude.ai/share/2f5662fc-7270-486d-9dc8-c9d8ef760736
- [x] Prints da tela (antes e depois do teste de usabilidade): `process-log/screenshots/`
- [x] Git history

---

_Submissão enviada em: 23/11/2026_