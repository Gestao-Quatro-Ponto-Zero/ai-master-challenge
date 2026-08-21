# Relatório de Backtest — Lead Scorer

Saída de `make validate` (`validation/backtest.py`), a suíte que reproduz — sobre os dados reais, não uma amostra — toda premissa estrutural por trás da fórmula descrita em [`../docs/architecture.md`](../docs/architecture.md) e derivada em [`../docs/analise-lead-scoring.md`](../docs/analise-lead-scoring.md). Cada seção abaixo é gerada por comando único; a única edição manual é a NOTA ao final da seção 2, sinalizando um achado que o texto impresso pelo próprio script ainda não reflete (ver nota).

**Resumo das 13 seções:**

| # | Pergunta | Resultado |
|---|---|---|
| 1 | Atributo firmografico preve ganho/perda? | FALSO — AUC 0.472–0.506 (equivalente a chute aleatório) em todos os atributos, isolados e combinados |
| 2 | E coincidencia de amostra? | MISTO — product/sector/account: p alto (0.12–0.92), compatível com ruído; sales_agent: p=0.000, ver NOTA abaixo |
| 3 | Encolhimento hierarchico colapsa niveis sem sinal? | PARCIAL — conta×produto e produto×setor colapsam (k=∞); produto não colapsa mais (k=0.6966, dominado por GTK 500) |
| 4 | Curva de risco e monotonica e censura de 138d se sustenta? | VERDADEIRO |
| 5 | PRIORIDADE concentra valor melhor que ordenar por preco puro? | VERDADEIRO (45.0% vs 27.9% no top 10%) |
| 6 | Condicionar p_hat por produto x setor melhora a predicao? | FALSO (pior que prior global) |
| 6.1 | `mult_setor` se comporta como a política pretende? | VERDADEIRO — teto ±15% respeitado em todas as 70 células, auditoria de consistência OK |
| 7 | Curva de aging por produto melhora a predicao? | FALSO (pior que curva global) |
| 8 | Duração de ciclo varia por produto? | FALSO (dispersão real menor que ruído) |
| 9 | CONFIANCA esta distribuida de forma saudavel para monitorar? | AVISO (30.8% sem precedente histórico) |
| 10 | Efeito da reclassificação de 200 dias? | 653 reclassificados; funil 2089→1436; base rate 63.15%→57.55% (GTK 500 dominado por amostra pequena) |
| 11 | Populações organica/reclassificada se sobrepõem (circularidade)? | FALSO — não se sobrepõem (138d vs 200d) |
| 12 | Fit por vendedor é distinguível de acaso? | MISTO — vendedor×produto p=0.041 (limítrofe, sem correção p/ múltiplas comparações); vendedor×setor p=0.199 |
| 13 | Denominador dos artefatos de análise está correto? | VERDADEIRO — 179/179 e 292/292 linhas aprovadas |

Leitura: as seções 1-2 seguem sustentando que não há como classificar QUEM vai ganhar com confiança suficiente para um classificador categórico — mas a seção 2 agora mostra `sales_agent` como estatisticamente significativo nesta calibração (ver NOTA); a 3-5 sustentam o modelo de valor em risco; a 6-8 são três tentativas de refinar o motor, todas descartadas por piorarem a previsão fora da amostra (exceto `mult_setor`, seção 6.1, implementado por decisão de produto apesar do resultado negativo da seção 6); a 9 é o painel de monitoramento; a 10-11 reproduzem o efeito e a integridade da reclassificação de 200 dias; a 12-13 reproduzem o fit por vendedor e travam o denominador dos artefatos de análise. Detalhe completo de cada seção abaixo.

---

## 1. Ausência de sinal preditivo por atributo firmográfico

Pergunta: dá pra adivinhar se um negócio vai ser GANHO ou PERDIDO só
olhando dados de cadastro (vendedor, produto, setor, conta)?
Método: separamos os negócios fechados em dois grupos por data — os
mais antigos (treino) e os mais recentes (teste) — e medimos se o
padrão aprendido no grupo antigo acerta no grupo novo.

Corte cronológico (treino/teste): 2017-09-12
Treino: 5871 negócios · Teste: 1493 negócios

AUC (Area Under Curve) é uma nota de 0 a 1 para o quão bem um atributo
separa ganhos de perdas: 0,50 = mesmo que jogar uma moeda (nenhum poder
preditivo); 1,00 = previsão perfeita. Abaixo, a AUC de cada atributo
isolado (taxa de ganho aprendida no treino, testada no teste):
  vendedor                 AUC = 0.484
  conta                    AUC = 0.492
  setor                    AUC = 0.472
  escritório regional      AUC = 0.478

AUC combinada (gradient boosting, todos os atributos): 0.506
-> ~0,50 indica ausência de poder discriminativo (chute aleatório).
Achado: nem um atributo isolado, nem todos combinados, batem uma
moeda viciada — não existe sinal preditivo firmográfico nestes dados
que um classificador consiga explorar.

## 2. Testes de permutação (semente fixa)

Pergunta: será que a falta de sinal da Seção 1 é só coincidência
desta amostra específica, ou é um padrão robusto?
Método: embaralhamos aleatoriamente, centenas de vezes, qual
vendedor/produto/setor/conta está associado a cada negócio, e
comparamos a diferença REAL entre grupos com a diferença que
aparece só por acaso nessas versões embaralhadas ('semente fixa'
quer dizer que o embaralhamento é sempre o mesmo, então o
resultado é reproduzível).

  sales_agent      dispersão obs.=0.0518 dispersão nula média=0.0306 p=0.000
  product          dispersão obs.=0.0185 dispersão nula média=0.0135 p=0.116
  sector           dispersão obs.=0.0115 dispersão nula média=0.0172 p=0.917
  account          dispersão obs.=0.0477 dispersão nula média=0.0537 p=0.935

p-valor = a chance de ver, só por acaso (embaralhado), uma diferença
tão grande quanto a real observada. p-valor alto (>0,05, tipicamente
bem mais) = a diferença real é do tamanho que apareceria só por acaso
— ou seja, não há padrão real.

**NOTA (2026-08-21, atualização desta execução):** com a população de calibração recalculada após a reclassificação de 200 dias (7.364 negócios, vs. 6.711 na calibração original), `sales_agent` passou de p=0,262 para **p=0,000** — estatisticamente significativo, ao contrário de `product`/`sector`/`account`, que seguem com p alto. Isso não muda a fórmula: `p̂` nunca condicionou por vendedor, e a seção 12 abaixo já reproduz esse mesmo sinal de forma independente (`vendedor×produto`, p=0,041, limítrofe e sem correção para múltiplas comparações) — é a base do mecanismo de **fit por vendedor** usado só na sugestão de redistribuição de sobrecarga, nunca em `p̂`/SCORE. `product`, `sector` e `account` continuam compatíveis com ruído amostral (p entre 0,12 e 0,94).

## 3. Encolhimento hierárquico — derivação de k

Pergunta: quanto peso dar à taxa de conversão histórica de cada
produto (ou combinação conta×produto, produto×setor), sem deixar
grupos com poucos negócios — e portanto números instáveis —
distorcerem a fórmula?
Método: 'encolhimento hierárquico' puxa a taxa de cada grupo em
direção à média geral (0,5755), com força k. k é calculado a partir
dos próprios dados: quanto menor a diferença real entre os grupos
comparada à diferença esperada só por acaso, maior o k — mais o
grupo é puxado pra média. Quando k = ∞, o grupo 'colapsa': recebe
peso zero e usa direto a média geral. É o que esperamos ver quando
um atributo não carrega sinal real.
Nenhum nível, incluindo produto, usa uma constante de política
congelada sobrepondo esse cálculo — o motor de scoring lê exatamente
o k derivado abaixo (`K_PRODUTO` foi removido em 2026-08-21).

  conta×produto    grupos= 528 var_obs=0.027996 var_esperada_por_acaso=0.029104 k=∞ (colapsa)
  produto×setor    grupos=  70 var_obs=0.016116 var_esperada_por_acaso=0.017652 k=∞ (colapsa)
  produto          grupos=   7 var_obs=0.002863 var_esperada_por_acaso=0.001175 k=0,6966 (não colapsa)

p̂_produto (usando o k derivado do nível de produto acima, sem constante congelada):
  GTX Basic        p_hat=0.5766
  GTX Pro          p_hat=0.5846
  MG Special       p_hat=0.5980
  MG Advanced      p_hat=0.5487
  GTX Plus Pro     p_hat=0.5813
  GTX Plus Basic   p_hat=0.5664
  GTK 500          p_hat=0.4314

NOTA — o nível de PRODUTO não colapsou nesta execução: variância em excesso positiva produz k = 0,6966, usado diretamente pelo motor de scoring para calcular p̂_produto acima — não há mais uma constante congelada para comparar. Um k pequeno frente ao n de cada produto significa pouco encolhimento (a taxa bruta domina); um k grande puxaria mais forte em direção à taxa global. Qualquer mudança de regime entre execuções fica visível aqui, sem precisar de um cenário de falha dedicado.

## 4. Curvas de aging — monotonicidade e fronteira de censura

Pergunta: o risco de o negócio esfriar realmente aumenta com o
tempo, sem 'zigue-zagues' estranhos, e existe um limite de idade
confiável pra fazer essa conta?
Método: recalculamos do zero as curvas de risco e de probabilidade
de ganho por idade do negócio, e conferimos duas coisas: (a) nenhum
negócio fechado nos dados é mais velho que o limite de censura
configurado; (b) a curva de risco nunca 'desce' — só sobe ou fica
igual conforme o negócio envelhece (monotonicidade).
'Censura' aqui quer dizer: não confiamos em extrapolar a curva além
do que já foi observado — acima do limite, a fórmula volta pro
valor médio histórico (prior) em vez de inventar um número.

Duração máxima observada entre negócios fechados: 138 dias
Limite de censura configurado: 138 dias
-> confirmado: nenhum negócio fechado excede o limite de censura.
risco(t) isotônico é não-decrescente em todos os pontos recalculados. OK.

p_ganho(t) recalculado nos extremos: t=0 -> 0,632  t=120 -> 0,752
-> p_ganho sobe com a idade (não decai): True
Achado contraintuitivo: a chance de ganhar SOBE com a idade do
negócio, não desce. O que a idade realmente consome é a janela de
decisão (quanto tempo resta pra fechar em breve), não a chance de
sucesso em si — por isso URGÊNCIA usa risco(t), não um decaimento.

## 5. Concentração de PRIORIDADE (não é validação preditiva)

Pergunta: a fórmula PRIORIDADE realmente separa o que é urgente e
valioso do resto da fila, ou dá praticamente no mesmo que ordenar
só pelo preço de tabela do produto?
Método: ordenamos a fila por PRIORIDADE e medimos quanto valor
total (em R$) está concentrado nos 10% e 30% do topo — e
comparamos com ordenar simplesmente pelo preço de tabela puro,
sem PRIORIDADE. Esta seção NÃO testa se a fórmula prevê quem vai
ganhar (isso já foi respondido nas seções 1 e 2); ela testa só se
a priorização concentra valor no topo.

Top 10% da fila por PRIORIDADE captura 45,0% do total
Top 30% da fila por PRIORIDADE captura 79,7% do total
Top 10% por preço de tabela puro captura 27,9% do total
Top 30% por preço de tabela puro captura 68,8% do total
-> concentração de valor, não poder preditivo: p̂ varia só 0,51-0,79 contra 487x de amplitude em VALOR. A diferenciação vem de valor e urgência.
Achado: PRIORIDADE concentra MAIS valor em risco no topo da fila do que simplesmente ordenar por preço de tabela (45,0% vs. 27,9% no top 10%) — o ganho vem de combinar VALOR com URGÊNCIA (idade do negócio), não de uma previsão fina de quem vai ganhar.

## 6. Condicionamento de p̂ por produto×setor — validação cruzada

Pergunta: condicionar a probabilidade de ganho por produto E setor,
em vez de só por produto, melhora a previsão fora da amostra?
Método: validação cruzada 5-fold com semente fixa. Em cada rodada,
80% dos negócios fechados calibram cada alternativa e os 20%
restantes medem o erro fora da amostra (logloss e brier — quanto
menor, melhor).

  prior_global               logloss=0,66795  brier=0,23751
  produto_encolhido          logloss=0,66794  brier=0,23750
  produto_setor_encolhido    logloss=0,66974  brier=0,23834
  produto_setor_bruto        logloss=0,69137  brier=0,24146

Células produto×setor: 70 — mediana de 86 negócios fechados por célula.
Achado: condicionar por produto×setor é PIOR que o prior global achatado (confirmado) — a amostra por célula é pequena demais para sustentar a diferenciação.
Este resultado negativo é reproduzido e impresso a cada execução, independentemente do motor de scoring aplicar `mult_setor` — ver a subseção 6.1 abaixo para a reprodução do mult_setor em si, um mecanismo distinto (encolhimento em direção a p̂_produto, não à taxa global, e teto de ±15%), implementado por decisão de produto apesar deste resultado.

## 6.1. `mult_setor` — reprodução e auditoria de consistência

Pergunta: o `mult_setor` efetivamente usado pelo motor de scoring se comporta como a política pretende — encolhimento pesado (K_SETOR=25) calando amostra pequena, teto de ±15% como salvaguarda, e a mesma função aplicada de forma consistente ao funil aberto e à distribuição de referência (negócios Won)?

Célula de maior amostra: GTX Basic × retail (n=274) -> mult_setor=1,1500 (teto acionado)
Célula de menor amostra: GTK 500 × services (n=1) -> mult_setor=0,9615 (esperado próximo de 1,0)
Faixa de mult_setor nas 70 células: [0,9259, 1,1500] — dentro de [0,85, 1,15] em todas as células: sim. Como todo mult_setor está garantidamente no intervalo do clip, p̂_produto×mult_setor nunca sai de [0,85×p̂_produto, 1,15×p̂_produto] para nenhum produto.

Auditoria de consistência funil aberto x referência: 70 combinações produto×setor recalculadas de forma independente e comparadas ao ScoringContext de produção (o mesmo objeto compartilhado pelas duas populações) -> consistentes.

## 7. Curvas de aging por produto — validação cruzada

Pergunta: uma curva de aging (risco de resolver em 30 dias) própria
por produto prevê melhor que a curva GLOBAL usada em produção?
Método: mesma validação cruzada 5-fold da seção 6, aplicada às faixas de idade.

  prior_global               logloss=0,65828  brier=0,23277
  curva_global               logloss=0,64936  brier=0,22859
  curva_por_produto_bruta    logloss=0,65525  brier=0,23044
  curva_por_produto_encolhida logloss=0,65275  brier=0,23008

Achado: a curva de aging GLOBAL tem o menor logloss entre todas as alternativas (confirmado) — aging é o único sinal real desta base, e reparti-lo por produto piora a previsão.
Ao menos um produto tem uma faixa de idade com uma única observação — sem amostra para curva própria.

## 8. Efeito de produto sobre a duração do ciclo

Pergunta: produtos diferentes têm ciclos de venda sistematicamente
mais longos ou mais curtos, ou a variação entre eles é só ruído?
Método: teste de permutação (semente fixa) sobre a dispersão das
medianas de duração de ciclo por produto.

Dispersão observada entre medianas: 22,0 dias  ·  dispersão nula média: 28,9 dias  ·  p=0,638
Achado: a dispersão observada entre produtos é MENOR que a dispersão sob rótulos embaralhados — os produtos são mais parecidos entre si em duração de ciclo do que uma atribuição aleatória produziria. Sustenta manter URGÊNCIA global.

Taxa de resolução em 30 dias por produto e faixa de idade (linha GLOBAL para comparação):
  faixa 0-45: GLOBAL=0,470 (n=6711)
  faixa 45-88: GLOBAL=0,322 (n=3377)
  faixa 88-138: GLOBAL=0,832 (n=1538)

## 9. Distribuição de CONFIANÇA e das duas metades

Acompanha a calibração de SUPORTE_JANELA_IDADE_DIAS e SUPORTE_SATURACAO_N — se uma recalibração futura tornar essas constantes inadequadas, a distribuição abaixo muda de forma visível, em vez de silenciosa.

n = 1436
  p10  CONFIANÇA=  20,0  completude=  20,0  suporte=  23,5
  p25  CONFIANÇA=  23,5  completude=  40,0  suporte=  35,0
  p50  CONFIANÇA=  35,0  completude=  40,0  suporte= 100,0
  p75  CONFIANÇA=  40,0  completude=  80,0  suporte= 100,0
  p90  CONFIANÇA=  80,0  completude= 100,0  suporte= 100,0
  p95  CONFIANÇA= 100,0  completude= 100,0  suporte= 100,0
  p99  CONFIANÇA= 100,0  completude= 100,0  suporte= 100,0

Fração sem precedente histórico: 30,8%
Fração governada por completude (vs. suporte): 64,6%

## 10. Antes/depois da reclassificação de 200 dias

Pergunta: qual o efeito de tratar as 653 oportunidades abertas há
200 dias ou mais como Lost — no tamanho do funil, na taxa de vitória
global e na taxa por produto?

Oportunidades reclassificadas: 653
Funil aberto: 2089 -> 1436
Base rate global: 63,15% -> 57,55% (-5,60pp)

Taxa de vitória por produto, antes -> depois (pp = pontos percentuais):
  GTK 500          n=  25->  35  60,00% -> 42,86%  (-17,14pp) [AMOSTRA PEQUENA]
  GTX Plus Pro     n= 745-> 824  64,30% -> 58,13%  ( -6,16pp)
  GTX Basic        n=1436->1587  63,72% -> 57,66%  ( -6,06pp)
  GTX Plus Basic   n=1051->1153  62,13% -> 56,63%  ( -5,50pp)
  MG Advanced      n=1084->1192  60,33% -> 54,87%  ( -5,47pp)
  GTX Pro          n=1147->1247  63,56% -> 58,46%  ( -5,10pp)
  MG Special       n=1223->1326  64,84% -> 59,80%  ( -5,04pp)

Achado: 653 reclassificados fazem o funil aberto cair de 2089 para 1436 e o base rate global cair 5,60pp. A maior variação de taxa por produto é dominada por amostra pequena (GTK 500) — não é o maior efeito real, é o mais ruidoso.

## 11. Auditoria da circularidade acima de 138 dias

Pergunta: a faixa de idade acima de 138 dias na população de
calibração é feita de desfechos observados, ou inteiramente de
rótulos que nós mesmos atribuímos por serem velhos?

Idade máxima entre fechados organicamente: 138 dias
Idade mínima entre reclassificados: 200 dias
-> confirmado: as duas populações não se sobrepõem, e nenhum reclassificado entrou nas curvas.

## 12. Fit por vendedor — permutação e suporte

Pergunta: a taxa de vitória de um vendedor num produto ou setor é
distinguível de acaso, uma vez controlado o mix de produtos/setores
que cada vendedor efetivamente atende?
Método: embaralhamos os rótulos de vendedor (mantendo produto/setor
fixos por negócio) e comparamos a dispersão real da taxa por célula
vendedor×dimensão com a dispersão sob rótulos aleatórios.

  vendedor×produto  células=178 dispersão obs.=0,0885 dispersão nula média=0,0821 p=0,0410
  vendedor×setor    células=292 dispersão obs.=0,1035 dispersão nula média=0,1004 p=0,1985

Derivação de k_fit por variância em excesso: vendedor×produto k=3,869; vendedor×setor k=5,447. K_FIT congelado em produção = 25,0 (constante de política — sempre mais conservador que qualquer k derivado abaixo dele, encolhendo o fit com mais força do que os dados por si só exigiriam).
Células com suporte insuficiente (< 10 negócios fechados): 14 de 178 (vendedor×produto), 54 de 292 (vendedor×setor).

Achado: vendedor×produto distinguível de acaso (p < 0,05) (p=0,0410); vendedor×setor indistinguível de acaso (p=0,1985). Mesmo onde o p-valor fica perto do corte convencional de 0,05, é um sinal fraco sobre 178 células testadas sem correção para múltiplas comparações — não é evidência robusta de mérito individual. O fit é entregue com a ressalva estatística acoplada ao número em toda superfície, exatamente por isso.
NOTA: a reprodução honesta encontra sinal fraco e limítrofe em vendedor×produto — consistente com o `sales_agent` p=0,000 da seção 2 (mesma origem: identidade do vendedor carrega algum sinal residual nesta calibração, controlado por produto/setor aqui, não controlado lá) — registrado para a próxima recalibração revisar, sem mudar K_FIT (constante de política, mais conservador que o k derivado).

## 13. Auditoria do denominador dos artefatos de análise

Pergunta: os artefatos analysis_by_product_detailed.csv e
analysis_by_sector_detailed.csv calculam a taxa de vitória sobre
Won + Lost, sem deixar Engaging/Prospecting vazarem para o
denominador — o defeito que os artefatos anteriores tinham?

  analysis_by_product_detailed.csv  179 linhas -> APROVADO
  analysis_by_sector_detailed.csv   292 linhas -> APROVADO

Achado: denominador travado por auditoria — nenhuma linha destes artefatos publica taxa cujo denominador inclua oportunidade em aberto.

## Conclusão

Juntando as 13 seções: não há como prever com confiança QUEM vai
ganhar por produto/setor/conta (seções 1, 2 e 6-7), então não faz
sentido construir um classificador de probabilidade categórica sobre
essas dimensões. `sales_agent` é a exceção mensurada nesta calibração
(seção 2, p=0,000; seção 12, p=0,041 controlando por produto/setor) —
um sinal fraco e nunca usado em `p̂`/SCORE, mas a base estatística real
do mecanismo de **fit por vendedor**, entregue só na sugestão de
redistribuição de sobrecarga, sempre com a ressalva estatística
acoplada.

O que os dados sustentam é ordenar o funil por SCORE (percentil de
PRIORIDADE, o valor em risco) — quanto vale o negócio, ajustado pela
chance histórica do produto (seção 3) e pela urgência de agir agora
(seção 4) — e essa priorização de fato concentra valor no topo da fila
(seção 5). Três tentativas de refinar o motor com condicionamento
adicional foram testadas e as três pioraram a previsão fora da
amostra: p̂ por produto×setor (seção 6), curvas de aging por produto
(seção 7) e duração de ciclo por produto (seção 8) — os dois últimos
ficam documentados, não implementados. O primeiro (produto×setor)
segue confirmado como pior (seção 6) e continua NÃO implementado
nessa forma direta — mas `mult_setor` (seção 6.1), um mecanismo
distinto com encolhimento pesado em direção a p̂_produto e teto de
±15%, foi implementado por decisão de produto apesar desse resultado.
A seção 9 acompanha CONFIANÇA (completude/suporte) para a próxima
recalibração. As seções 10-11 reproduzem o impacto e a circularidade
da reclassificação de 200 dias; as seções 12-13 reproduzem o fit por
vendedor e travam o denominador dos artefatos de análise por teste.

Os dados justificam ordenar o funil por SCORE (percentil de valor em
risco), não por um classificador de probabilidade categórica nem por
hierarquias de condicionamento adicionais sobre produto/setor/conta: a
hierarquia de encolhimento confirma isso para conta×produto e
produto×setor (produto em si deixou de colapsar após a recalibração
de 200 dias — ver seção 3, dominado por GTK 500), e condicionar por
setor ou por produto (aging, duração de ciclo) piora a previsão fora
da amostra em vez de melhorá-la. `sales_agent` é a única dimensão com
sinal estatisticamente mensurável nesta calibração — usado apenas no
fit de redistribuição de carga, nunca em `p̂`.

STATUS: OK — premissas estruturais confirmadas, com uma atualização
de regime (produto não colapsa mais; `sales_agent` passou a ser
estatisticamente significativo) registrada acima e em
`docs/decisions-log.md`.
