# Relatório de Backtest — Lead Scorer

Saída de `make validate` (`validation/backtest.py`), a suíte que reproduz — sobre os dados reais, não uma amostra — toda premissa estrutural por trás da fórmula descrita em [`architecture.md`](./architecture.md) e derivada em [`analise-lead-scoring.md`](./analise-lead-scoring.md). Cada seção abaixo é gerada por comando único, sem edição manual.

**Resumo das 14 seções:**

| # | Pergunta | Resultado |
|---|---|---|
| 1 | Atributo firmografico preve ganho/perda? | FALSO — AUC 0.475–0.523 isolada, 0.500 combinada (equivalente a chute aleatório) |
| 2 | E coincidencia de amostra? | FALSO — nenhum atributo é significativo: sales_agent p=0.262, product p=0.374, sector p=0.965, account p=0.947; nenhum sobrevive a Holm nem a Benjamini-Hochberg sobre os 6 testes da suíte |
| 3 | Encolhimento hierarchico colapsa niveis sem sinal? | VERDADEIRO — os três níveis abaixo do global colapsam (k=∞); p̂ = 0.632 para os sete produtos, amplitude 0.00pp |
| 4 | Curva de risco e monotonica e censura de 138d se sustenta? | VERDADEIRO |
| 5 | PRIORIDADE concentra valor melhor que ordenar por preco puro? | VERDADEIRO (48.8% vs 29.5% no top 10%) |
| 6 | Condicionar p_hat por produto x setor melhora a predicao? | FALSO (pior que prior global) |
| 7 | Curva de aging por produto melhora a predicao? | FALSO (pior que curva global) |
| 8 | Duração de ciclo varia por produto? | FALSO (dispersão real menor que ruído) |
| 9 | CONFIANCA esta distribuida de forma saudavel para monitorar? | AVISO (52.5% sem precedente histórico) |
| 10 | Qual seria o efeito do expurgo de 200 dias? | MEDIDO, NÃO APLICADO — fabricaria 16.66pp de amplitude em p̂ (real: 0.00pp) e tornaria sales_agent significativo (p 0.262 → <0.001), porque as candidatas se concentram em algumas carteiras (χ²=576.4, gl=29, p<0.0001; correlação −0.794 entre fração expurgada e taxa hipotética) |
| 11 | Ha desfecho atribuido por nos na calibracao? | FALSO — 6711 fechados, todos com desfecho registrado |
| 12 | Fit por vendedor é distinguível de acaso? | FALSO nos dois nulos — 'vendedor importa?' p=0.5877 (produto) e p=0.5447 (setor); 'existe afinidade além dos efeitos principais?' p=0.8736 e p=0.8771 |
| 13 | Denominador dos artefatos de análise está correto? | VERDADEIRO — 179/179 e 292/292 linhas aprovadas |
| 14 | "Não rejeitou" na seção 2 significa que os vendedores são iguais? | FALSO — os 15.42pp entre o melhor e o pior cabem no acaso (mediana nula 14.38pp), mas a dispersão verdadeira estimada é τ̂=1.08pp (>0) e o menor τ detectável com 80% de poder é 3.04pp: a diferença plausível cai inteira na zona cega do teste |

Leitura: as seções 1-2 sustentam que não há como classificar QUEM vai ganhar — nenhum atributo firmográfico, vendedor incluído, se distingue de ruído, nem isoladamente nem depois de corrigir para a família de 6 testes; a 3-5 sustentam o modelo de valor em risco; a 6-8 são três tentativas de refinar o motor, todas descartadas por piorarem a previsão fora da amostra; a 9 é o painel de monitoramento; a 10 mede a distorção que o expurgo de 200 dias introduziria e a 11 confirma que nenhum desfecho da calibração foi atribuído por nós; a 12-13 reproduzem a ausência de sinal do fit por vendedor — em dois nulos, um para 'vendedor importa em algum grau?' e outro para 'existe afinidade vendedor×produto?', que é a pergunta que a palavra fit faz — e travam o denominador dos artefatos de análise; a 14 mede o poder dos testes de vendedor e fixa a leitura correta de todos os "não rejeita" acima: eles afirmam que este histórico **não enxerga** diferença entre vendedores, não que ela não exista. Detalhe completo de cada seção abaixo.

---


## 1. Ausência de sinal preditivo por atributo firmográfico
Pergunta: dá pra adivinhar se um negócio vai ser GANHO ou PERDIDO só
olhando dados de cadastro (vendedor, produto, setor, conta)?
Método: separamos os negócios fechados em dois grupos por data — os
mais antigos (treino) e os mais recentes (teste) — e medimos se o
padrão aprendido no grupo antigo acerta no grupo novo.

Corte cronológico (treino/teste): 2017-09-18
Treino: 5350 negócios · Teste: 1361 negócios

AUC (Area Under Curve) é uma nota de 0 a 1 para o quão bem um atributo
separa ganhos de perdas: 0,50 = mesmo que jogar uma moeda (nenhum poder
preditivo); 1,00 = previsão perfeita. Abaixo, a AUC de cada atributo
isolado (taxa de ganho aprendida no treino, testada no teste):
  vendedor                 AUC = 0.523
  conta                    AUC = 0.486
  setor                    AUC = 0.475
  escritório regional      AUC = 0.500

AUC combinada (gradient boosting, todos os atributos): 0.500
-> ~0,50 indica ausência de poder discriminativo (chute aleatório).
Achado: nem um atributo isolado, nem todos combinados, batem uma
moeda viciada — não existe sinal preditivo firmográfico nestes dados.

## 2. Testes de permutação (semente fixa)
Pergunta: será que a falta de sinal da Seção 1 é só coincidência
desta amostra específica, ou é um padrão robusto?
Método: embaralhamos aleatoriamente, centenas de vezes, qual
vendedor/produto/setor/conta está associado a cada negócio, e
comparamos a diferença REAL entre grupos com a diferença que
aparece só por acaso nessas versões embaralhadas ('semente fixa'
quer dizer que o embaralhamento é sempre o mesmo, então o
resultado é reproduzível).

  sales_agent      dispersão obs.=0.0340 dispersão nula média=0.0314 p=0.262
  product          dispersão obs.=0.0150 dispersão nula média=0.0139 p=0.374
  sector           dispersão obs.=0.0099 dispersão nula média=0.0172 p=0.965
  account          dispersão obs.=0.0473 dispersão nula média=0.0540 p=0.947

p-valor = a chance de ver, só por acaso (embaralhado), uma diferença
PELO MENOS tão grande quanto a real observada. p-valor alto (>0,05,
tipicamente bem mais) = a diferença real é do tamanho que apareceria
só por acaso — ou seja, ESTES dados não sustentam afirmar um efeito.
O p-valor mínimo que 2000 permutações conseguem afirmar é 1/(2000+1) = 0.00050 — por isso esta suíte reporta 'p < 0,001' e nunca 'p = 0,000'. Zero é impossível como probabilidade: com um número finito de reamostragens não se distingue 'nunca acontece' de 'acontece menos de uma vez em 2000' (correção add-one, `permutation_tests._p_valor`).
Duas leituras erradas que este número NÃO autoriza:
  1. p alto NÃO prova que o efeito não existe. Ausência de evidência não é
     evidência de ausência: um efeito real, mas pequeno demais para 6711
     negócios, devolveria o mesmo p alto. A conclusão deste trabalho precisa
     apenas do enunciado mais fraco — não há base para pôr o atributo no score.
  2. p NÃO é a probabilidade de o efeito existir (nem de não existir). É a
     frequência com que o acaso, sozinho, produziria o que os dados mostram.
-> p alto (>0,05, tipicamente bem mais) = dispersão observada compatível com ruído.
Achado: todos os atributos testados têm p-valor alto — confirma, de
um segundo jeito independente, o resultado da Seção 1.

Correção para múltiplas comparações — 6 testes de permutação rodam nesta suíte (os 4
acima e os 2 da seção 12). Seis testes contra o corte de 0,05 sem correção levariam a
chance de ao menos um falso positivo de 5% para 1-(1-0,05)^6 = 26,5%:
  teste              origem        p             Holm (FWER)             B-H (FDR)
  sales_agent        §2       0.2619  não rejeita (α=0.0083)  não rejeita (≤0.0083)
  product            §2       0.3738  não rejeita (α=0.0100)  não rejeita (≤0.0167)
  vendedor×setor     §12      0.5447  não rejeita (α=0.0125)  não rejeita (≤0.0250)
  vendedor×produto   §12      0.5877  não rejeita (α=0.0167)  não rejeita (≤0.0333)
  account            §2       0.9470  não rejeita (α=0.0250)  não rejeita (≤0.0417)
  sector             §2       0.9645  não rejeita (α=0.0500)  não rejeita (≤0.0500)
Nenhum dos seis sobrevive a qualquer das duas correções — e nenhum precisaria: nenhum
chega perto do corte nem sem correção. A correção fica registrada porque a família de
testes é o que dá sentido ao corte, não porque algum resultado dependa dela.
Composição da família, explicitada porque a escolha é auditável: a seção 12 roda DOIS
nulos por dimensão e entra aqui com o p do nulo GLOBAL, o MENOR dos dois
(0.5877 contra 0.8736 em vendedor×produto).
São 6 entradas e não 8 pelo mesmo motivo: quanto mais testes na família, mais apertados
ficam os cortes de Holm e B-H e MAIS fácil fica não rejeitar. As duas escolhas jogam
contra a tese deste trabalho — família curta e p mais baixo são o cenário em que 'não há
sinal' teria a maior chance de cair. Não caiu.

## 3. Encolhimento hierárquico — derivação de k
Pergunta: quanto peso dar à taxa de conversão histórica de cada
produto (ou combinação conta×produto, produto×setor), sem deixar
grupos com poucos negócios — e portanto números instáveis —
distorcerem a fórmula?
Método: 'encolhimento hierárquico' puxa a taxa de cada grupo em
direção à média geral (0.632), com força k. k é calculado a partir
dos próprios dados: quanto menor a diferença real entre os grupos
comparada à diferença esperada só por acaso, maior o k — mais o
grupo é puxado pra média. Quando k = ∞, o grupo 'colapsa': recebe
peso zero e usa direto a média geral. É o que esperamos ver quando
um atributo, como já vimos nas seções 1 e 2, não carrega sinal real.
Nenhum nível, incluindo produto, usa uma constante de política
congelada sobrepondo esse cálculo — o motor de scoring lê exatamente
o k derivado abaixo.

  conta×produto    grupos= 525 var_obs=0.025899 var_esperada_por_acaso=0.027981 k=∞ (colapsa)
  produto×setor    grupos=  69 var_obs=0.012264 var_esperada_por_acaso=0.015229 k=∞ (colapsa)
  produto          grupos=   7 var_obs=0.000316 var_esperada_por_acaso=0.001515 k=∞ (colapsa)

p̂_produto (usando o k derivado do nível de produto acima, sem constante congelada):
  GTX Basic        p_hat=0.6320
  GTX Pro          p_hat=0.6320
  MG Special       p_hat=0.6320
  MG Advanced      p_hat=0.6320
  GTX Plus Pro     p_hat=0.6320
  GTX Plus Basic   p_hat=0.6320
  GTK 500          p_hat=0.6320

NOTA — o nível de PRODUTO colapsou nesta execução (variância em excesso ≤ 0, mais fraco do que qualquer um dos quatro atributos testados por permutação acima, todos com p > 0,05): sem constante de política a sobrepor o colapso, p̂_produto usa diretamente a taxa global de calibração (0.632) para todos os produtos — o comportamento correto, sem exigir mudança de código nem revisão manual de constante alguma.

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

p_ganho(t) recalculado nos extremos: t=0 -> 0.632  t=120 -> 0.752
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
ganhar (isso já foi respondido — negativamente — nas seções 1 e 2);
ela testa só se a priorização concentra valor no topo.

Top 10% da fila por PRIORIDADE captura 48.8% do total
Top 30% da fila por PRIORIDADE captura 78.8% do total
Top 10% por preço de tabela puro captura 29.5% do total
Top 30% por preço de tabela puro captura 68.9% do total
-> concentração de valor, não poder preditivo: p̂ varia só 0.63-0.75 contra 487x de amplitude em VALOR. A diferenciação vem de valor e urgência.
Achado: PRIORIDADE concentra MAIS valor em risco no topo da fila do que simplesmente ordenar por preço de tabela (48.8% vs. 29.5% no top 10%) — o ganho vem de combinar VALOR com URGÊNCIA (idade do
negócio), não de uma previsão fina de quem vai ganhar (que já vimos,
nas seções 1 e 2, que não existe).

## 6. Condicionamento de p̂ por produto×setor — validação cruzada
Pergunta: condicionar a probabilidade de ganho por produto E setor,
em vez de só por produto, melhora a previsão fora da amostra?
Método: validação cruzada 5-fold com semente fixa. Em cada rodada,
80% dos negócios fechados calibram cada alternativa e os 20%
restantes medem o erro fora da amostra (logloss e brier — quanto
menor, melhor).

  prior_global               logloss=0.65828  brier=0.23277
  produto_encolhido          logloss=0.65828  brier=0.23277
  produto_setor_encolhido    logloss=0.66016  brier=0.23364
  produto_setor_bruto        logloss=0.68042  brier=0.23664

Células produto×setor: 69 — mediana de 85 negócios fechados por célula.
Achado: condicionar por produto×setor é PIOR que o prior global achatado (confirmado) — a amostra por célula é pequena demais para sustentar a diferenciação.
Consequência no motor: setor NÃO entra em p̂ nem em SCORE, em nenhuma forma — nem como condicionamento direto, nem como multiplicador encolhido sobre p̂. Setor continua sendo lido para a completude de CONFIANÇA e para o fit vendedor×setor da redistribuição de carga (seção 12) — nunca para o score.

## 7. Curvas de aging por produto — validação cruzada
Pergunta: uma curva de aging (risco de resolver em 30 dias) própria
por produto prevê melhor que a curva GLOBAL usada em produção?
Método: mesma validação cruzada 5-fold da seção 6, aplicada às faixas de idade.

  prior_global               logloss=0.65828  brier=0.23277
  curva_global               logloss=0.64936  brier=0.22859
  curva_por_produto_bruta    logloss=0.65525  brier=0.23044
  curva_por_produto_encolhida logloss=0.65275  brier=0.23008

Achado: a curva de aging GLOBAL tem o menor logloss entre todas as alternativas (confirmado) — aging é o único sinal real desta base, e reparti-lo por produto piora a previsão.
Ao menos um produto tem uma faixa de idade com uma única observação — sem amostra para curva própria.

## 8. Efeito de produto sobre a duração do ciclo
Pergunta: produtos diferentes têm ciclos de venda sistematicamente
mais longos ou mais curtos, ou a variação entre eles é só ruído?
Método: teste de permutação (semente fixa) sobre a dispersão das
medianas de duração de ciclo por produto.

Dispersão observada entre medianas: 22.0 dias  ·  dispersão nula média: 28.9 dias  ·  p=0.638
Achado: a dispersão observada entre produtos é MENOR que a dispersão sob rótulos embaralhados — os produtos são mais parecidos entre si em duração de ciclo do que uma atribuição aleatória produziria. Sustenta manter URGÊNCIA global.

Taxa de resolução em 30 dias por produto e faixa de idade (linha GLOBAL para comparação):
  faixa 0-45: GLOBAL=0.470 (n=6711)
  faixa 45-88: GLOBAL=0.322 (n=3377)
  faixa 88-138: GLOBAL=0.832 (n=1538)

## 9. Distribuição de CONFIANÇA e das duas metades
Acompanha a calibração de SUPORTE_JANELA_IDADE_DIAS e SUPORTE_SATURACAO_N — se uma recalibração futura tornar essas constantes inadequadas, a distribuição abaixo muda de forma visível, em vez de silenciosa.

n = 2089
  p10  CONFIANÇA=  20.0  completude=  20.0  suporte=  23.5
  p25  CONFIANÇA=  23.5  completude=  40.0  suporte=  23.5
  p50  CONFIANÇA=  23.5  completude=  40.0  suporte=  23.5
  p75  CONFIANÇA=  40.0  completude=  80.0  suporte= 100.0
  p90  CONFIANÇA=  80.0  completude= 100.0  suporte= 100.0
  p95  CONFIANÇA=  95.4  completude= 100.0  suporte= 100.0
  p99  CONFIANÇA= 100.0  completude= 100.0  suporte= 100.0

Fração sem precedente histórico: 52.5%
Fração governada por completude (vs. suporte): 44.6%

## 10. Sensibilidade ao expurgo de 200 dias (medido, NÃO aplicado)
Pergunta: e se as oportunidades abertas há 200 dias ou mais fossem
tratadas como Lost e entrassem na calibração? Esta seção mede esse
cenário sem aplicá-lo — o motor calibra só sobre desfecho observado.

Expurgo aplicado em produção: NÃO (a carga não reescreve deal_stage).
Candidatas: 653 oportunidades abertas há 200-423 dias
Funil aberto: 2089 real (seria 1436)
Base rate global: 63.15% real (seria 57.55%, -5.60pp)

Taxa de vitória por produto, real -> hipotética (pp = pontos percentuais):
  GTK 500          n=  25->  35  60.00% -> 42.86%  (-17.14pp) [AMOSTRA PEQUENA]
  GTX Plus Pro     n= 745-> 824  64.30% -> 58.13%  ( -6.16pp)
  GTX Basic        n=1436->1587  63.72% -> 57.66%  ( -6.06pp)
  GTX Plus Basic   n=1051->1153  62.13% -> 56.63%  ( -5.50pp)
  MG Advanced      n=1084->1192  60.33% -> 54.87%  ( -5.47pp)
  GTX Pro          n=1147->1247  63.56% -> 58.46%  ( -5.10pp)
  MG Special       n=1223->1326  64.84% -> 59.80%  ( -5.04pp)

Efeito sobre o encolhimento do nível de produto:
  variância em excesso: -0.00120000 real -> +0.00168735 hipotética
  k derivado:           inf real -> 0.6966 hipotético
  amplitude de p̂ entre produtos: 0.00pp real -> 16.66pp hipotética

Efeito sobre os testes de permutação (p-valor real -> hipotético):
  sales_agent    0.262 ->  <0.001  <- VIRARIA significativo neste cenário hipotético
  product        0.374 ->   0.116
  sector         0.965 ->   0.922
  account        0.947 ->   0.922

Dispersão da taxa de vitória entre vendedores: 15.42pp real -> 19.94pp hipotética (13 vendedores não receberiam nenhuma perda atribuída)

Por que o expurgo fabrica sinal de vendedor — o mecanismo, medido:
  concentração das candidatas por vendedor: qui-quadrado=576.4 (gl=29, p<0,0001) — as oportunidades paradas NÃO se distribuem por igual entre carteiras
  correlação entre fração da carteira expurgada e taxa de vitória hipotética: -0.794
  O expurgo só adiciona DERROTA, nunca vitória. Como ele cai concentrado, a taxa
  hipotética de cada vendedor vira, em boa parte, uma função de quanto funil parado
  ele tinha — idade de pipeline relida como habilidade de fechar. O 'sinal de vendedor'
  do cenário hipotético é a régua se medindo, não o vendedor.

Achado: o expurgo não é neutro. Ele encolhe o funil em 653 oportunidades, derruba o base rate 5.60pp e — o que importa — cria discriminação onde o dado observado não tem nenhuma: a amplitude de p̂ entre produtos sai de 0.00pp para 16.66pp, puxada por GTK 500 (amostra pequena), e a identidade do vendedor passa a ser lida como sinal porque as oportunidades paradas se concentram em algumas carteiras. É por isso que a carga nunca o aplica — ver process-log/decisions-log.md.

## 11. Auditoria de circularidade — nenhum desfecho atribuído por nós
Pergunta: existe na população de calibração algum desfecho que não
veio do CRM — um rótulo que o próprio sistema atribuiu?

População de calibração: 6711 negócios fechados
Fechados sem close_date (rótulo sem evento): 0
Idade máxima observada até o fechamento: 138 dias (fronteira de censura: 138)
Idade máxima no funil ABERTO: 423 dias — acima da censura, pontuada com p̂ revertido ao prior, nunca convertida em Lost.
-> confirmado: todo negócio da calibração tem desfecho registrado, e a censura cobre toda a faixa de idade que a calibração viu.

## 12. Fit por vendedor — permutação e suporte
Pergunta: existe AFINIDADE vendedor×produto (ou vendedor×setor) —
este vendedor indo bem NESTE produto, acima do que o desempenho geral
dele e a dificuldade geral do produto já explicam? É essa e só essa
a pergunta que a palavra 'fit' faz.
Método: dois nulos, porque são duas perguntas diferentes.
  GLOBAL  — embaralha os rótulos de vendedor sobre todas as linhas,
            com produto/setor fixos por negócio. Responde 'vendedor
            importa em algum grau?'. NÃO isola afinidade: embaralhar
            destrói junto o efeito principal do vendedor, que entra
            inteiro na estatística.
  ADITIVO — ajusta logit(ganho) = α + β_vendedor + γ_dimensão e
            sorteia desfechos desse modelo (bootstrap paramétrico).
            Cada réplica é um mundo em que vendedores diferem entre
            si, produtos diferem entre si e ninguém tem afinidade
            com nada. O que sobra acima dessa nula é interação — e
            só isso é fit.

  vendedor×produto  células=178 dispersão obs.=0.0815
      nulo GLOBAL  (vendedor importa?) nula=0.0824 p=0.5877
      nulo ADITIVO (existe fit?)       nula=0.0865 p=0.8736
  vendedor×setor    células=288 dispersão obs.=0.1003
      nulo GLOBAL  (vendedor importa?) nula=0.1008 p=0.5447
      nulo ADITIVO (existe fit?)       nula=0.1052 p=0.8771

Derivação de k_fit por variância em excesso: vendedor×produto k=5.262; vendedor×setor k=9.389. K_FIT congelado em produção = 25.0 (constante de política — sempre mais conservador que qualquer k derivado abaixo dele, encolhendo o fit com mais força do que os dados por si só exigiriam).
Células com suporte insuficiente (< 10 negócios fechados): 17 de 178 (vendedor×produto), 53 de 288 (vendedor×setor).

Achado: vendedor×produto indistinguível de acaso no nulo global (p=0.5877) e não há fit no nulo aditivo (p=0.8736); vendedor×setor indistinguível de acaso no nulo global (p=0.5447) e não há fit no nulo aditivo (p=0.8771).
Sob o nulo aditivo a dispersão observada fica ABAIXO da média simulada em ambas as dimensões: as células vendedor×produto são mais parecidas entre si do que um mundo sem afinidade nenhuma já produziria. Não há interação a encontrar, e não há correção para múltiplas comparações a aplicar — não existe sinal a corrigir. O fit ordena candidatos numa sugestão de redistribuição de CARGA; ele não mede mérito individual nem afinidade, e é entregue com a ressalva estatística acoplada ao número em toda superfície, exatamente por isso (Requirement "Declaração de ausência de significância estatística do fit").
Nota de leitura: as 178 células não são 178 testes. A dispersão é uma estatística OMNIBUS — um único teste que agrega todas as células —, então não existe multiplicidade em nível de célula a corrigir aqui. A multiplicidade real desta suíte são os 6 testes de permutação (4 na seção 2, 2 nesta), e a seção 2 já reporta o resultado sob Holm e Benjamini-Hochberg.

## 13. Auditoria do denominador dos artefatos de análise
Pergunta: os artefatos analysis_by_product_detailed.csv e
analysis_by_sector_detailed.csv calculam a taxa de vitória sobre
Won + Lost, sem deixar Engaging/Prospecting vazarem para o
denominador — o defeito que os artefatos anteriores tinham?

  analysis_by_product_detailed.csv  179 linhas -> APROVADO
  analysis_by_sector_detailed.csv   292 linhas -> APROVADO

Achado: denominador travado por auditoria — nenhuma linha destes artefatos publica taxa cujo denominador inclua oportunidade em aberto (proposal.md: os artefatos anteriores tinham 159 de 179 e 219 de 292 linhas incorretas por esse exato defeito).

## 14. Poder do teste de vendedor — o que este histórico enxergaria
Pergunta: as seções 2 e 12 não rejeitam. Isso significa que os
vendedores são iguais, ou que a diferença entre eles é menor do que
esta amostra consegue ver? São afirmações diferentes, e só a segunda
é sustentável — um teste que não rejeita só informa junto com o seu
poder.
Método: (a) compara a amplitude real entre carteiras com a que o
        acaso já produz com os mesmos tamanhos de carteira;
        (b) estima a dispersão VERDADEIRA por variância em excesso;
        (c) simula mundos em que a habilidade realmente varia e mede
        com que frequência o teste da seção 2 os pegaria (MDE);
        (d) repete no cenário mais favorável possível — um vendedor
        escolhido ANTES de olhar o dado.

  amplitude observada (melhor - pior de 30 vendedores) = 15.42pp
  a mesma amplitude sob acaso puro: mediana 14.38pp, IC95 [9.90, 21.19]pp -> a amplitude real CABE no que o acaso entrega de graça
  dispersão observada 3.40pp = ruído binomial esperado 3.23pp + excesso -> τ̂ = 1.08pp (amplitude implicada entre melhor e pior: 4.07pp)

  Poder do teste omnibus da seção 2 (α=0.05, corte de dispersão 3.81pp):
    τ verdadeiro= 1.0pp (amplitude real ~ 15.2pp) -> poder  12.6%
    τ verdadeiro= 1.5pp (amplitude real ~ 15.9pp) -> poder  21.4%
    τ verdadeiro= 2.0pp (amplitude real ~ 16.8pp) -> poder  39.0%
    τ verdadeiro= 2.5pp (amplitude real ~ 17.8pp) -> poder  61.0%
    τ verdadeiro= 3.0pp (amplitude real ~ 18.9pp) -> poder  79.2%
    τ verdadeiro= 3.5pp (amplitude real ~ 20.2pp) -> poder  90.2% <- corte de 80% (MDE interpolado: 3.04pp)
    τ verdadeiro= 4.0pp (amplitude real ~ 21.6pp) -> poder  97.3%
    τ verdadeiro= 5.0pp (amplitude real ~ 24.7pp) -> poder  99.7%
    τ verdadeiro= 7.5pp (amplitude real ~ 33.7pp) -> poder 100.0%
    τ verdadeiro=10.0pp (amplitude real ~ 43.1pp) -> poder 100.0%
  Um vendedor de carteira mediana (n=220) escolhido ANTES de olhar o dado, realmente acima dos demais:
    + 5.0pp -> poder  30.9%
    + 6.3pp -> poder  47.6%
    +10.0pp -> poder  88.8%
    +15.0pp -> poder  99.8%
  Quanto histórico faltaria para τ̂=1.08pp sair da zona cega (hoje: 220 fechados por vendedor):
    n=  220 fechados por vendedor -> poder   8.8%
    n=  500 fechados por vendedor -> poder  20.4%
    n= 1000 fechados por vendedor -> poder  48.8%
    n= 2000 fechados por vendedor -> poder  85.0%
    n= 4000 fechados por vendedor -> poder  99.1%
    n= 8000 fechados por vendedor -> poder 100.0%

Achado: as duas leituras extremas estão erradas. A amplitude de 15.42pp entre o melhor e o pior vendedor NÃO é achado — o acaso entrega 14.38pp de mediana com estas carteiras, e é por isso que a seção 2 não rejeita. Mas 'não rejeita' também não é 'são iguais': a estimativa pontual da dispersão verdadeira é τ̂=1.08pp — positiva, e equivalente a ~4.07pp entre o melhor e o pior, um quarto do que a tabela crua sugere. O menor τ que este histórico detectaria em 80% das amostras é 3.04pp, ACIMA de τ̂: a diferença plausível entre vendedores cai inteira na zona cega do teste.
Consequência no motor: nenhuma mudança. Um efeito que não se distingue de zero não entra em p̂ nem em SCORE — publicar τ̂ como se fosse mensurado seria vender ruído como habilidade, e é exatamente o erro que a seção 10 mostra o expurgo cometendo. O que muda é a redação: a ferramenta afirma que não CONSEGUE VER diferença entre vendedores neste histórico, não que ela não exista. A diferença importa para a decisão de produto — τ̂ pequeno ainda vale receita sobre uma carteira inteira, e o caminho para medi-lo não é este dado observacional e sim alocação aleatorizada de leads comparáveis (ver roadmap.md).
Dimensionamento desse experimento: aleatorizar a alocação remove o confundimento — a taxa de vitória deixa de misturar habilidade com qualidade da carteira recebida — mas NÃO compra poder. Para enxergar τ̂=1.08pp seriam necessários ~2000 negócios fechados por vendedor, contra os 220 de hoje (9× o histórico atual). O experimento se justifica pelo desenho, não por um atalho estatístico: ele torna a resposta interpretável como habilidade e permite acumular amostra de propósito — e, no meio-tempo, detecta um efeito grande caso exista.

## Conclusão
Juntando as 14 seções: não há como prever com confiança QUEM vai
ganhar (seções 1 e 2), então não faz sentido construir um
classificador de probabilidade categórica. O que os dados sustentam
é ordenar o funil por SCORE (percentil de PRIORIDADE, o valor em risco) —
quanto vale o negócio, ajustado pela chance histórica do produto (seção 3)
e pela urgência de agir agora (seção 4) — e essa priorização de fato
concentra valor no topo da fila (seção 5). Três tentativas de refinar o
motor com condicionamento adicional foram testadas e as três pioraram a
previsão fora da amostra: p̂ por produto×setor (seção 6), curvas de aging
por produto (seção 7) e URGÊNCIA por produto (seção 8) — nenhuma das três
está implementada. A seção 9 acompanha CONFIANÇA
(completude/suporte) para a próxima
recalibração. A seção 10 mede a distorção que o expurgo de 200 dias
introduziria e a 11 confirma que nenhum desfecho da calibração foi
atribuído por nós; as seções 12-13 reproduzem a ausência de
sinal robusto do fit por vendedor e travam o denominador dos artefatos
de análise por teste. A seção 14 fecha a leitura das seções 2 e 12: o
que elas afirmam não é que os vendedores sejam iguais, e sim que
qualquer diferença real entre eles é menor do que este histórico
conseguiria enxergar.

Os dados justificam ordenar o funil por SCORE (percentil de valor em risco), não
por um classificador de probabilidade categórica nem por hierarquias de
condicionamento adicionais: nenhum atributo firmográfico isolado carrega sinal
acima do ruído amostral, a hierarquia de encolhimento confirma isso nos três
níveis abaixo do global — conta×produto, produto×setor e produto — que colapsam
todos (seção 3), e condicionar por setor ou por produto (aging, URGÊNCIA) piora
a previsão fora da amostra em vez de melhorá-la.

STATUS: OK — todas as premissas estruturais confirmadas.
