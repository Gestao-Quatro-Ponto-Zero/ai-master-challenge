# Baseline — o que uma IA entrega só com o brief

O G4 já rodou este desafio em Claude, GPT e Gemini e guarda as respostas como baseline. Esse material não é público, então este arquivo reconstrói a entrega típica: é o que um modelo produz quando recebe só o README do challenge 003 e os quatro CSVs, sem olhar os dados antes de decidir o score.

Serve para uma coisa: comparar a nossa entrega com ela e cortar tudo o que for parecido.

Base: `data/raw/` (8.800 oportunidades). Data de referência usada nas contas abaixo: 2017-12-31, a última `close_date` do arquivo.

---

## 1. A entrega típica do baseline

**Score.** Soma ponderada de 0 a 100, com pesos escolhidos "por bom senso" e não medidos nos dados:

| Componente típico | Peso típico | Como o baseline calcula |
|---|---|---|
| Estágio do deal | 20–30 | Engaging vale mais que Prospecting |
| Valor do deal | 20–25 | Preço do produto (open deals não têm `close_value`) |
| Win rate do vendedor | 15–20 | Won / (Won + Lost) do vendedor, sem suavização |
| Porte da conta | 10–15 | Receita ou funcionários em faixas |
| Setor / produto | 10 | Win rate do setor ou do produto |
| Tempo no pipeline | 10–15 | Penalidade linear: quanto mais velho, pior |

**Interface.** Streamlit com:
- tabela ordenada por score, com cor verde/amarelo/vermelho;
- filtros laterais de vendedor, manager e região;
- 3 ou 4 KPIs no topo (pipeline total, win rate, ticket médio);
- um gráfico de barras ou de pizza por estágio;
- explicação do score como lista de pontos por componente ("Valor: +18, Vendedor: +12…"), às vezes com um gráfico SHAP ou de contribuição.

**Às vezes** um modelo (Random Forest, XGBoost, regressão logística) treinado em Won/Lost, com AUC reportada e "feature importance".

**Documentação.** README com `pip install -r requirements.txt` e `streamlit run app.py`, uma tabela de pesos, uma seção de limitações genérica ("dados sintéticos", "pesos podem ser calibrados", "integrar com o CRM via API") e um próximo passo de "treinar um modelo de ML".

**Process log.** Uma narrativa curta e linear: "pedi ao Claude o app, ajustei o layout, publiquei".

---

## 2. Onde o baseline erra nestes dados (medido)

| # | O que o baseline assume | O que os dados mostram | Consequência |
|---|---|---|---|
| A | Setor, produto, região e manager separam deals bons de ruins | Diferença entre o melhor e o pior grupo em win rate: produto 4,8 p.p. (60,0%–64,8%), setor 3,7 p.p., manager 2,3 p.p., região 1,4 p.p. Média geral 63,2% | Esses componentes somam ruído ao score. Pontos dados por setor ou região são decorativos |
| B | Porte da conta importa | Win rate por quartil de funcionários: 64,1% / 61,4% / 63,9% / 63,2%. Sem tendência | Mesmo caso de A |
| C | Histórico da conta prevê o próximo deal | Correlação entre o win rate da conta no 1º e no 2º semestre de 2017: −0,08 | "Conta boa" do passado não repete. Componente de conta não se sustenta como está no contrato |
| D | Dá para usar setor e porte nos deals abertos | **68% dos deals abertos não têm conta** (1.088 de 1.589 Engaging; 337 de 500 Prospecting). Won e Lost têm conta em 100% | Qualquer critério de conta deixa 2 em cada 3 deals abertos sem nota. O baseline costuma preencher com média em silêncio |
| E | Deal velho é deal frio (penalidade linear) | Entre os deals fechados, quanto mais tempo o deal sobrevive, **maior** a chance de ganhar. Win rate dos deals que duraram mais de d dias (ciclo > d): 63,2% (d = 0, todos), 68,7% (14), 71,1% (90), 75,6% (120). Com "pelo menos d dias" (≥) a curva é a mesma: 63,2 / 68,6 / 71,3 / 75,1%. Os Lost fecham rápido (mediana 14 dias) e os Won devagar (mediana 57). **Nota:** a subida depois das 2 primeiras semanas não é sinal. Ela vem do corte de 2016 (não há fechamento antes de mar/2017, então só sobraram ganhos antigos) e do fim de trimestre (ganhos registrados no 3º mês). Na coorte sem esse viés, a taxa fica plana depois de 15 dias (`analysis/findings.md`) | A penalidade linear erra o sinal; o certo é não premiar nem punir a idade além das 2 primeiras semanas e do limite de 138 dias |
| F | A idade do deal aberto é comparável ao ciclo histórico | O ciclo mais longo de um deal fechado é 138 dias. **1.291 dos 1.589 Engaging (81%) já têm mais de 138 dias** na data de referência (mediana 165) | Esses deals estão fora de tudo o que o histórico já viu. Não dá para tratá-los como "quentes" nem extrapolar a curva de E. É a principal pergunta de produto: são deals parados que precisam de requalificação |
| G | `today()` como data de referência | Os dados vão de 2016-10 a 2017-12 | Com a data de hoje, todo deal tem ~3.000 dias e o score de tempo zera para todos |
| H | Prospecting tem idade | Prospecting não tem `engage_date` (500 deals) | Baseline quebra (NaN) ou dá idade zero sem avisar |
| I | Win rate do vendedor é estável | Vai de 55,0% a 70,4% (mínimo de 79 deals fechados por vendedor). Correlação 1º × 2º semestre: 0,36 | É o único sinal com alguma persistência, mas fraco. Precisa de suavização e não pode dominar o score |
| J | Valor do deal é informação independente | Nos Won, `close_value` ÷ preço de tabela tem mediana 1,00 (0,66–1,34) | "Valor" é, na prática, o produto. Um score com peso alto em valor vira "ordenar por produto caro" — exatamente o que o brief proíbe |
| K | Os nomes batem entre tabelas | `GTXPro` no pipeline × `GTX Pro` no catálogo (1.480 deals); setor `technolgy` com erro de digitação; 5 vendedores do `sales_teams` sem nenhum deal | Join perde o preço de um produto inteiro sem erro visível; filtros mostram vendedores vazios |
| L | Taxa de vitória mensal é estável | Meses de fim de trimestre (mar, jun, set, dez) fecham 78–83% de Won; os outros 49–57% | Sinal de calendário real, mas vem da `close_date`, que deal aberto não tem. Cuidado com vazamento se alguém usar isso no score |

Leitura geral: nestes dados quase nada separa Won de Lost. Um score bonito com seis componentes ponderados é, em grande parte, ruído apresentado com confiança. O diferencial possível é dizer isso com números e construir a ferramenta em cima do pouco que tem sinal (vendedor suavizado, tempo relativo ao ciclo, valor esperado) e da higiene do pipeline (deals fora do ciclo, deals sem conta).

---

## 3. Armadilhas de baseline para evitarmos

Atualizar conforme a #3 (score) e a #4 (app) avançam. Status: ⬜ não verificado · ✅ evitado · ⚠️ presente na nossa entrega.

| # | Armadilha | Status | Onde conferir |
|---|---|---|---|
| 1 | Pesos escolhidos "por bom senso", sem medir se o critério separa Won de Lost | ⬜ | `scoring/` e `scoring/validacao.md` |
| 2 | Componente de setor, região, manager ou porte no score (spread < 5 p.p.) | ⬜ | `scoring/` |
| 3 | Componente "histórico da conta" sem prova de que persiste (corr −0,08) | ⬜ | `scoring/`, campo `components.conta` do contrato |
| 4 | Deals sem conta (68% dos abertos) recebem média sem aviso | ⬜ | `flags` contém `sem_conta`? A tela mostra? |
| 5 | Penalidade linear por idade (o sinal é o contrário até ~120 dias) | ⬜ | `scoring/` |
| 6 | Deals além do ciclo histórico (81% dos Engaging) tratados como normais | ⬜ | `action` = requalificar/desistir? A tela explica? |
| 7 | `today()` como data de referência | ⬜ | `reference_date` no JSON = 2017-12-31 ou data justificada |
| 8 | Prospecting com idade NaN ou zero sem aviso | ⬜ | `days_in_pipeline` dos Prospecting |
| 9 | Win rate do vendedor sem suavização (vendedor com poucos deals vira extremo) | ⬜ | `scoring/` |
| 10 | Score que, na prática, ordena por preço do produto | ⬜ | Correlação score × `expected_value`; top 10 de cada vendedor é só GTK 500 / GTX Pro? |
| 11 | `GTXPro` × `GTX Pro` sem tratamento (preço some) | ⬜ | `data/clean/`, deals GTX Pro com `expected_value` > 0 |
| 12 | Vendedores sem deals aparecendo no filtro | ⬜ | App |
| 13 | Uso de `close_date`/mês de fechamento como feature (vazamento) | ⬜ | `scoring/` |
| 14 | Explicação = lista de pontos por componente, sem frase que o vendedor entenda | ⬜ | `reasons` no JSON e na tela |
| 15 | Tela = tabela + KPIs + gráfico de pizza, sem "o que faço hoje" | ⬜ | App, visão do vendedor |
| 16 | Visão do manager igual à do vendedor com filtro | ⬜ | App, visão do manager |
| 17 | AUC / "feature importance" de modelo de ML como argumento principal | ⬜ | README, `scoring/validacao.md` |
| 18 | Validação ausente ou feita nos mesmos dados que definiram os pesos | ⬜ | `scoring/validacao.md` (separação no tempo?) |
| 19 | Limitações genéricas ("dados sintéticos", "integrar com o CRM") | ⬜ | README da submissão |
| 20 | Process log linear, sem erro da IA corrigido nem decisão do Leandro | ⬜ | `process-log/decisoes.md` |

---

## Como estes números foram obtidos

Contas feitas com pandas sobre `data/raw/*.csv`, considerando só deals Won e Lost para win rate. Ciclo = `close_date` − `engage_date` (mínimo de 1 dia). Diferença entre grupos = maior win rate menos o menor, sem arredondar antes de subtrair. Semestres: `close_date` antes e depois de 2017-07-01. Os números oficiais da análise são os da sessão de dados (`analysis/findings.md`); se divergirem, vale o de lá e este arquivo é corrigido.
