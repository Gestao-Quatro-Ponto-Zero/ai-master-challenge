# Lead Scorer: setup, lógica e limitações

Ferramenta que o vendedor abre na segunda-feira e vê **quais deals empurrar esta semana, por quê, e o que fazer com cada um**.
O manager vê o mesmo painel filtrado pelo time dele, e a aba "Time" mostra onde falta pipeline.

![Foco da semana](../process-log/screenshots/desktop-2-detail.png)

---

## Setup

### Só usar (zero instalação)

Abra `app/index.html` no navegador (duplo clique). Os dados já pontuados estão em `app/data.js`.
Funciona offline, sem servidor, em desktop e celular.

### Recalcular o score (testado com Python 3.13 + pandas 3.0)

```bash
cd submissions/felipe-holanda/solution
pip install -r requirements.txt          # pandas + numpy, nada mais
python -m lead_scorer.build              # recalcula e regrava app/data.js (~5 s)
python -m lead_scorer.build --as-of 2017-09-18   # "volta no tempo" para qualquer segunda-feira
python -m lead_scorer.backtest           # reproduz a validação
```

Para trocar os dados (ex.: export novo do CRM), substitua os CSVs em `data/` (mesmo formato) ou use `--data-dir`.

### Testes

```bash
pip install -r requirements-dev.txt
python -m pytest -q        # 11 testes: sem vazamento de futuro, correção de censura, filas, explicações, backtest, forecast
```

### Estrutura

```
solution/
├── app/                 interface (HTML + CSS + JS puro, sem build)
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   └── data.js          gerado por lead_scorer.build
├── lead_scorer/
│   ├── data.py          carga, joins e correções de qualidade dos CSVs
│   ├── scoring.py       toda a lógica de score, fases, ações e explicações
│   ├── backtest.py      roda o scorer de produção em datas passadas
│   └── build.py         CLI que gera app/data.js
├── tests/
└── data/                CSVs originais (Kaggle / Maven Analytics, CC0)
```

---

## Lógica do score

### A pergunta mudou no meio do caminho

O brief sugere "deal stage, tempo no pipeline, tamanho da conta, produto e vendedor" como features. Testei todas antes de usar
(`process-log/analysis/02_signal_tests.py`):

| Feature | Separa Won de Lost? | p-valor (χ²) |
|---|---|---|
| Vendedor (30) | não | 0,26 |
| Produto (7) | não | 0,37 |
| Setor | não | 0,97 |
| Conta (85) | não | 0,94 |
| Região / manager | não | 0,60 / 0,79 |
| Porte da conta (receita) | fraco, some com correção para múltiplos testes | 0,03 |
| Win rate histórico da conta | não (correlação −0,04) | n/a |

E em backtest (`03_backtest.py`), prever **"esse deal vai fechar?"** não funciona com nenhuma combinação:

| Modelo | AUC média (0,5 = chute) |
|---|---|
| Win rate por vendedor + produto + setor + conta + região | 0,48 |
| Gradient boosting com todas as features | 0,49 |
| Só idade do deal | 0,52 |

Um score que dá "+15 pontos porque o vendedor tem win rate alto" estaria apresentando **ruído como explicação**.
Isso é pior que não ter score, porque o vendedor confia no porquê.

O que os dados respondem bem é outra pergunta: **"o que deve fechar ganho no próximo mês, e quanto vale?"**.
A idade do deal prevê *quando* ele fecha (AUC 0,60 a 0,80 para "fecha ganho nos próximos 30 dias"), e o valor varia 486x entre produtos.

### Fórmula

```
Score (0-100) = Valor (0-60) + Momento (0-40)

Valor   = 60 × log(preço / 55) / log(26.768 / 55)
Momento = 40 × ripeness(idade) / pico da curva

ripeness(x) = P(fechar GANHO nos próximos 30 dias | deal ainda aberto com x dias desde o engage)
```

- **Valor em log**: com escala linear, um GTK 500 (US$ 26.768) valeria 486 MG Special e toda lista começaria pelos 40 GTK 500.
  Log mantém o valor importante sem apagar o resto.
- **Ripeness** é estimada no histórico, contando como "em risco" tanto os deals que fecharam quanto os que **continuam abertos**
  (raciocínio de Kaplan-Meier). Sem essa correção, a curva dizia que 78% dos deals com 127 dias fecham ganhos no mês; com ela, 5%.
  Era o maior erro da primeira versão (ver process log).
- **60/40**: testei 3 combinações e o produto puro valor × ripeness (`04_score_design.py`). O produto capturou ~1 p.p. a mais de receita,
  mas o aditivo tem mais acerto no top 10 e é explicável em pontos ("+45 de 60 pelo valor, +39 de 40 pelo momento"). Escolhi explicabilidade.

### A curva por trás do "momento"

Os deals se decidem em duas ondas: logo no começo (a mediana de duração dos perdidos é 14 dias) e de novo entre ~60 e ~100 dias,
com pico em 85 dias (31% fecham ganhos no mês seguinte). Depois disso a chance cai toda semana, e **nenhum deal da história levou mais de 138 dias**.

### Filas e fases (o score diz a ordem, a fase diz a ação)

| Fila / fase | Regra | Ação sugerida |
|---|---|---|
| **Foco**: Início | ≤ 14 dias | Qualificar rápido |
| **Foco**: Aquecendo | antes da janela | Manter cadência |
| **Foco**: Janela de fechamento | ripeness ≥ 75% do pico (≈ 59 a 102 dias) | Empurrar para o fechamento esta semana |
| **Foco**: Esfriando | depois da janela | Pedir decisão |
| **Foco**: Última janela | ≤ 20 dias do maior ciclo histórico | Forçar decisão até a data X |
| **Revisar ou encerrar** | idade > 138 dias (sem precedente) | Confirmar se existe; senão, encerrar como Lost |
| **Prospectar** | sem data de engage | Primeiro contato, ordenado por valor |

### Validação

Rodei **o mesmo código de produção** em 9 segundas-feiras passadas (abril a novembro/2017), cada uma só com os dados conhecidos naquela data,
e medi quanto da receita que **de fato** fechou ganha nos 30 dias seguintes estava no **top 10 de cada vendedor**:

| Ordenação | Receita do mês no top 10 | Top 10 que virou Won no mês |
|---|---|---|
| **Lead Scorer (valor + momento)** | **47%** | **23%** |
| Só valor de lista | 41% | 15% |
| Aleatório | 18% | 16% |

Ganha de "só valor" em 7 das 9 datas. As 2 em que perde são as primeiras (abril e maio), quando havia pouco histórico para calibrar a curva.
Para o vendedor, isso significa ~50% mais acerto nas ligações da semana.

---

## O que a ferramenta mostra além do score

- **US$ 3,2 milhões (64% do valor em aberto) estão em 1.291 deals sem precedente**: em Engaging há mais tempo do que qualquer
  deal já levou para fechar. O forecast que soma esse pipeline está inflado. Ficam numa fila separada, ordenados por valor, com a ação de confirmar.
- **68% do pipeline aberto não tem conta preenchida.** Cada deal mostra o alerta.
- **Região Central não tem receita esperada para o próximo mês**: 5 deals vivos, nenhum novo engajamento aberto desde agosto,
  e é dona de todos os 500 prospects (US$ 1,07 mi). O gargalo ali é prospect → engage, não priorização.
- **14 de 35 vendedores não têm nenhum deal vivo**, incluindo 5 que nunca tiveram um deal e 3 que fecharam centenas mas estão com a carteira zerada.
- **Plano da semana em texto** (botão no topo): top 10 + os 5 maiores deals a confirmar, pronto para colar no Slack ou no e-mail.
- **Limpeza com saída para o CRM**: na fila "Revisar ou encerrar" o vendedor marca cada deal como "está vivo" ou "encerrar".
  O progresso fica salvo no navegador e o botão "Exportar CSV para o CRM" gera a lista de atualizações (ID, decisão, ação no CRM).
- **Saúde do pipeline** (aba Time): deals vivos vs sem precedente e novos engajamentos no fim de cada mês, e três forecasts lado a lado:
  o ingênuo (pipeline em Engaging × 63%), o que considera a idade dos deals e o esperado para os próximos 30 dias.
  Hoje o ingênuo é 15x maior que o que considera a idade.
- **Funcionou?**: escolha uma das 9 segundas-feiras do backtest e veja o top 10 que cada vendedor teria recebido, com o desfecho real
  de cada deal (ganhou em X dias, ganhou depois, perdeu, continuou aberto) e a comparação com ordenar só por valor.
  Respeita os filtros: o manager vê como a ferramenta teria se saído com o time dele.

---

## Limitações

**Do dado**
- Não há atividades (e-mails, reuniões, ligações), motivo de perda, nem histórico de mudança de estágio. É isso que faria
  prever "vai fechar?" ser possível. Hoje o score responde "quando" e "quanto", não "se".
- O dataset é sintético. Achados como "nenhum deal fecha no mesmo trimestre em que foi engajado" e a taxa de vitória de 80% nos
  meses de fim de trimestre parecem artefatos da geração, por isso **não entraram no score**.
- Prospecting não tem data nenhuma: não dá para saber há quanto tempo o prospect está parado.
- 68% dos deals abertos sem conta impedem usar setor/porte (que, de qualquer forma, não mostraram sinal).

**Da solução**
- "Hoje" é o último dia do CRM (31/12/2017). Em produção seria a data real, lida de um CRM ao vivo, não de CSV.
- A curva é global. Com mais dados, valeria uma curva por produto ou por região (testado por vendedor x produto: o spread observado é igual ao esperado pelo ruído).
- Fila "Revisar" não sabe distinguir deal morto de deal com data errada: por isso a ação é verificar, não descartar.

**Para escalar**
1. Ler direto do CRM (API do Salesforce/HubSpot) num job diário que roda `lead_scorer.build`, e servir a página estática atrás do SSO.
2. Registrar o que o vendedor fez com cada sugestão (ligou, avançou, encerrou) para medir o efeito real e recalibrar.
3. Puxar atividades do CRM: aí sim um modelo de "vai fechar?" passa a ter sinal, e entraria como terceiro componente do score, só depois de bater o backtest atual.
4. Entregar o "plano da semana" por Slack toda segunda às 8h (o texto já é gerado pela página).
