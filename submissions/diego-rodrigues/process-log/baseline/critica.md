# Crítica dos baselines

Três modelos receberam o README do challenge 003, sem dados e sem ferramentas. As respostas estão íntegras nesta pasta:

- `nemotron-3.5-lightning.md`: `nvidia/nemotron-3.5-lightning`, via API do OpenRouter, sem ferramentas. Código, documentação e process log.
- `gemini-3.1.md`: Gemini 3.1 "Detailed research", na interface web, colado manualmente. Código, documentação e process log.
- `chatgpt-6.1-sol.md`: ChatGPT 6.1 Sol, na interface web, colado manualmente. Desenho de arquitetura, fórmula, plano de seis horas e critérios de aceite. Não traz código.

Não entraram no baseline: `gemma-4-31b`, `baidu/ernie-5.5-flash-preview`, `liquid/lfm-3-1.7b` e `nvidia/nemotron-3-ultra`. Os três primeiros deram limite de taxa ou erro do provedor; o último respondeu sem texto. O modelo do próprio build (Claude) fica fora do baseline, de propósito.

Os números abaixo saem de consultas sobre `data/` (dataset CC0 do Kaggle, `agungpambudi/crm-sales-predictive-analytics`). Os fechados são 6.711 deals (4.238 Won, 2.473 Lost). Os abertos são 2.089.

## O que cada baseline faz

**Nemotron.** Score de 0 a 100 com quatro fatores fixos: estágio (40%, Won=100, Engaging=75, Prospecting=50, Lost=0), valor do `close_value` (30%), receita da conta (20%) e frescor (10%, ≤30 dias=100, ≤90=50, mais=20). Não separa deals abertos de fechados.

**Gemini.** Score-base 50, com somas e subtrações: Engaging +20 ou Prospecting +5; menos de 15 dias no pipeline +15, mais de 60 dias −20, sem data −10; receita acima de 5.000 +10; subsidiária +10. Filtra só os abertos. Afirma que o score é "probabilidade de fechamento", sem nenhuma calibração.

**ChatGPT 6.1 Sol.** Score de 0 a 100 com cinco componentes: histórico do produto (30%), histórico do setor (20%), histórico da conta (10%), maturidade da etapa (25%: Engaging=1,00, Prospecting=0,40) e contexto temporal (15%, comparado ao percentil 75 da duração histórica por produto). As taxas históricas são suavizadas com k=20. Explicita que o score não é probabilidade, exclui `close_value` do deal aberto, separa Engaging de Prospecting, prevê uma seção "Revisar situação" para deals muito antigos e fixa a data de referência na maior data válida. É o único dos três que pensa em vazamento e em limitações explicitamente.

## Pontos da crítica

**1. Pesos para setor, porte e vendedor.** O dado desmente setor e porte.

| Atributo | Taxa de ganho entre os fechados | Leitura |
|---|---|---|
| Setor (10 valores) | 61,2% a 64,8% | sem diferença que sustente peso |
| Porte (quartis de receita) | 61,3% a 65,9% | sem diferença que sustente peso |
| Produto (7 valores) | 60,3% a 64,8% (suavizada, k=20) | sem diferença que sustente peso |
| Com subsidiária vs sem | 63,6% vs 63,1% | o bônus de +10 do Gemini não tem base |
| Vendedor | 55,0% a 70,4% | há dispersão visível, mas o plano registra p=0,28; não tratar como sinal sem teste |

O Nemotron pesa receita em 20%, e isso não se sustenta. O Gemini dá +10 para receita acima de 5.000, mas isso vale só para 8 das 85 contas (o campo está em milhões, então o corte é arbitrário). O ChatGPT Sol pesa setor em 20% e produto em 30%: pela tabela, o componente de produto quase não varia entre deals, e o peso de 50% dado a produto e setor vai para um sinal que não existe. O AUC dos atributos de cadastro fica perto de 0,5, como o plano já previa.

**2. Nenhum teste.** Nenhum dos três apresenta teste executado, backtest ou validação com dados fechados. O Nemotron e o Gemini entregam código sem teste. O ChatGPT Sol descreve `pytest` e critérios de aceite, mas são um plano, não resultado. O Gemini declara que o score "vai além do óbvio", mas não mede nada. Sem backtest, nenhum dos três sabe se o ranking ordena melhor do que a ordem atual.

**3. Nenhum zumbi.** Há 500 deals em Prospecting sem `engage_date`. O Gemini aplica −10 e os mantém na mesma fila. O Nemotron não trata o `NaN`, e a comparação falha em silêncio, então o frescor vira 20 (o pior valor). O ChatGPT Sol dá valor neutro (0,50) a esses deals e informa a limitação, o que é mais honesto, mas ainda não os separa como zumbis. Só ele prevê uma seção específica para revisão de deals antigos, o que se aproxima do que o plano chama de zumbi.

**4. Janela de decisão.** Os três limites têm problemas diferentes.
- O Gemini penaliza com −20 deals de mais de 60 dias. Mas 48% dos deals ganhos levaram mais de 60 dias para fechar. Com a referência do próprio Gemini (a maior `engage_date` dos abertos, 22/12/2017), 1.517 dos 2.089 abertos (73%) já passam desse limite. A regra penaliza a maioria do pipeline e também a maioria dos deals que de fato ganham.
- O Nemotron usa `pd.Timestamp.now()`, ou seja, novembro de 2026. Todos os deals têm `engage_date` de 2016 a 2017, então todos caem na faixa ">90 dias" e o frescor fica constante em 20. O componente não diferencia nada. (Conclusão pelo código; não rodei o app.)
- O ChatGPT Sol é o único que ancora a janela nos dados: o percentil 75 da duração histórica por produto. Pelo dado, o p75 global dos fechados é de 85 dias (88 para Won), e por produto varia de 82 a 92 dias. A ideia é correta. Mas a regra ainda usa três faixas com cortes de 1 e 2 vezes a referência, sem validação de que esses cortes separam algo.

**5. Métrica inventada.** O score de 0 a 100 é uma soma de pesos escolhidos à mão. Nenhum dos três mostra erro, precisão ou taxa de acerto. O Gemini chama o número de "probabilidade de fechamento", o que não é verdade. O ChatGPT Sol diz explicitamente que o score não é probabilidade e que seus pesos são "hipóteses iniciais", mas ainda assim não tem como verificar se as hipóteses ajudam.

**Efeito real da fórmula do ChatGPT Sol.** Pela tabela, o histórico de produto varia de 60% a 65%, e o de setor e de conta varia pouco. Os componentes de 60% do peso (histórico) somam quase uma constante. A ordem final fica quase toda explicada por estágio (diferença de 15 pontos entre Engaging e Prospecting) e tempo desde o início. Ou seja: o ChatGPT Sol, na prática, ordena a carteira pelos mesmos sinais que os outros dois, mas com mais texto para justificar pesos que o dado não sustenta.

**Vazamento (Nemotron).** Pontua `deal_stage` e `close_value`. Ambos são o próprio desfecho: `close_value` só tem valor nos Won (4.238 linhas, todas Won). Dar nota 100 a quem já ganhou é prever o passado. O Gemini evita isso, porque filtra só os abertos. O ChatGPT Sol evita o vazamento de forma explícita e a incluiu como critério de aceite.

**Código.** O Nemotron não compila: `SyntaxError` na linha da `st.write` com f-string sem aspas, e ainda usa as colunas `industry`, `employee_count` e `location`, que não existem (os nomes reais são `sector`, `employees` e `office_location`). O Gemini compila (`py_compile` sem erro), mas tem o problema do merge de produto, descrito abaixo, e não rodei o app. O ChatGPT Sol não tem código para verificar.

**Merge de produto (Gemini).** 1.480 deals com produto `GTXPro` não casam com o catálogo (que tem `GTX Pro`). Esses deals ficam com valor vazio e somem do "Pipeline Value". O ChatGPT Sol prevê essa checagem em "contas e produtos não encontrados sinalizados", mas sem ter executado.

## Conclusão para o Passo 4

Os três baselines confirmam os cinco pontos do plano: pesos sem base para setor e porte, nenhum teste executado, zumbis tratados como penalidade ou valor neutro, janelas de decisão fixas e métrica inventada. O Nemotron também vaza o desfecho e não compila. O Gemini filtra corretamente os abertos, mas sua janela de 60 dias é a principal falha. O ChatGPT Sol é o baseline mais bem pensado (vazamento, janela ancorada no p75 e limitações escritas), mas seus pesos de 50% em produto e setor não têm sinal no dado, e não há código nem teste executado.

Limitação deste baseline: os três modelos foram obtidos por canais diferentes (dois pela interface web, um pela API gratuita), e nenhum foi rodado em ambiente limpo. A comparação entre famílias continua fraca, porque são só três respostas e uma delas, a do Nemotron, veio de um provedor gratuito e instável.
