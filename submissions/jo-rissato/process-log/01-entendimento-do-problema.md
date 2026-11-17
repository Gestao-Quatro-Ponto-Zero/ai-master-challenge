# 01. Entendimento do problema, antes de abrir os dados

Registro em ordem cronológica, horário de Brasília. Regra desta etapa: nenhuma análise dos dados
até o Jó fechar a leitura do problema e as hipóteses. Até aqui, só a estrutura dos arquivos foi
conferida (colunas e contagem de linhas).

## Fato já registrado antes da conversa

- O brief fala em "~30.000 tickets por ano". O arquivo `customer_support_tickets.csv` tem **8.469**
  linhas. Ponto a esclarecer na auditoria: amostra, outro período ou erro do brief.
- O dataset de TI tem 47.837 textos em 8 grupos, como o brief descreve.

## Conversa de entendimento (Jó × Claude)

Formato: pergunta do Jó literal, resposta do Claude resumida, e o que o Jó decidiu a partir dela.

### 18:07, rodada 1: as 10 perguntas do Jó antes de responder as hipóteses

Perguntas literais do Jó:

1. O volume de tickets aumentou ou a equipe está demorando mais para resolver a mesma quantidade?
2. Quantos atendentes existem hoje e quantos tickets cada um resolve diariamente?
3. O maior gargalo está no tempo para responder, no tempo para solucionar ou na quantidade de tickets que ficam parados aguardando alguma ação?
4. Quantos tickets são reabertos porque o problema não foi resolvido corretamente na primeira tentativa?
5. Quais tipos de solicitações mais consomem o tempo da equipe?
6. Quanto tempo o atendente efetivamente trabalha em cada ticket e quanto tempo o ticket fica aguardando na fila?
7. A queda na satisfação está relacionada à demora, à qualidade das respostas ou à falta de resolução?
8. Qual é o custo operacional atual por ticket resolvido?
9. O que o diretor considera mais importante: reduzir custos, aumentar a capacidade de atendimento ou recuperar a satisfação?
10. Se conseguíssemos responder todos os tickets imediatamente, mas o tempo de resolução continuasse igual, o problema do diretor estaria resolvido?

Resposta do Claude: triagem de cada pergunta contra as colunas descritas no brief, sem abrir os números.

| # | O dado tem como responder? | Destino |
|---|---|---|
| 1 | Não: não há data de abertura do ticket, só data de compra | Limitação + pedido ao diretor |
| 2 | Não: não há coluna de atendente | Premissa declarada para o cálculo de horas |
| 3 | Em parte: há primeira resposta, resolução e status (Pending) | Hipótese a testar |
| 4 | Não: não há marcação de reabertura | Limitação; texto da resolução pode dar indício |
| 5 | Sim: tipo, assunto, produto × tempo de resolução | Hipótese a testar |
| 6 | Não: só tempo de calendário, não esforço do atendente | Limitação + premissa |
| 7 | Em parte: satisfação × tempo, canal, tipo, status | Hipótese a testar (pergunta central) |
| 8 | Não: não há custo | Premissa explícita (custo/hora) e sensibilidade |
| 9 | Não está no brief; o brief cita sobrecarga, tempo e satisfação, e as dicas citam ROI | Decisão do Jó |
| 10 | Pergunta de julgamento | Resposta do Jó |

Observação do Claude: 5 das 10 perguntas não têm resposta nos dados. Isso já é achado: a operação
não mede atendente, reabertura, esforço nem custo, e sem isso não dá para separar "volume subiu"
de "eficiência caiu".

### 18:13, rodada 2: Jó pede para olhar dentro dos zips

Pedido do Jó (literal): "você conseguiu acessar os arquivos do zip, acredito que la tem dados importantes que eu perguntei"

Decisão: abrir a **estrutura** do arquivo (formato e qualidade de cada coluna), ainda sem cruzar
variáveis nem testar hipóteses de satisfação ou gargalo.

O que o Claude encontrou (`customer_support_tickets.csv`):

- Cada zip tem um único CSV, já descrito no brief. Não há tabela extra de atendente, custo ou histórico.
- **Todas as 8.469 descrições** contêm o marcador literal `{product_purchased}`: o texto foi gerado por
  template e o produto nunca foi preenchido.
- O texto de **resolução** é frase aleatória sem sentido (ex.: "Case maybe show recently my computer
  follow."). Não serve para sugerir resposta.
- `First Response Time` e `Time to Resolution` são **carimbos de data e hora**, não durações, e todos
  caem numa janela de cerca de 27 horas (31/05/2023 21:53 a 02/06/2023 00:55).
- Dos 2.769 tickets com as duas datas, **1.365 (49%) têm a resolução antes da primeira resposta**.
  Impossível na vida real.
- Tipos de ticket são 5 (o brief cita 3), quase igualmente divididos (1.634 a 1.752 cada), padrão de
  sorteio uniforme.
- Status: 2.819 Open (sem primeira resposta), 2.881 Pending, 2.769 Closed. Satisfação, resolução e
  tempo de resolução só existem nos Closed.
- Nomes e e-mails gerados por biblioteca de dado falso (domínio example.com).

Leitura do Claude: o Dataset 1 é sintético. As métricas de tempo não medem fluxo real, então as
perguntas 3 e 6 do Jó não têm resposta confiável nele. A satisfação ainda não foi cruzada com nada.

### 18:26, rodada 3: Jó pede as métricas operacionais para formar as hipóteses

Pedido do Jó (literal): "mas na descricao dentro do git, cita essa questao.. preciso desses dados para responder O Dataset 1 tem métricas operacionais."

Decisão do Jó: ver os números descritivos antes de fechar as hipóteses. Registrado aqui para que a
ordem fique transparente.

Como não existe data de abertura do ticket, a única duração calculável é "resolução menos primeira
resposta", só nos 2.769 fechados.

- Horas entre 1ª resposta e resolução: mediana 0,2 h, mínimo -23,2 h, máximo 23,5 h; 1.365 negativos.
  Só os positivos: mediana 6,3 h.
- Satisfação (1 a 5): média 2,99, com cada nota entre 543 e 580 tickets. Distribuição plana.
- Satisfação por canal: 2,95 a 3,08. Por prioridade: 2,96 a 3,05. Por tipo: 2,93 a 3,03.
- Satisfação por faixa de tempo: 0-4 h 3,01; 4-12 h 3,07; 12 h+ 2,98; negativos 2,95.
- Prioridade Critical não é resolvida mais rápido que Low (medianas 0,3 h e 0,3 h).
- Status por canal: cerca de 1/3 Open, 1/3 Pending, 1/3 Closed em todos os canais.

Leitura do Claude: nenhuma variável mexe a satisfação. A diferença máxima (0,15 ponto) está dentro do
ruído de notas sorteadas de 1 a 5. Teste estatístico formal fica para a etapa de diagnóstico.

### 19:06, rodada 4: o que os "aguardando" estão aguardando

Pergunta do Jó (literal): "esse 1/3 que esta aguardando está aguardando o que?"

Resposta do Claude, conferida no dado:

| Status | Tickets | Com 1ª resposta | Com resolução | Com satisfação |
|---|---|---|---|---|
| Open | 2.819 | 0 | 0 | 0 |
| Pending Customer Response | 2.881 | 2.881 | 0 | 0 |
| Closed | 2.769 | 2.769 | 2.769 | 2.769 |

- "Pending Customer Response" = o atendente já respondeu e o ticket espera o **cliente** voltar.
- O dado não guarda o que foi perguntado ao cliente, nem há quanto tempo ele espera, nem se há
  lembrete ou fechamento automático por inatividade.
- Pendentes se distribuem igual entre tipos (551 a 597) e prioridades (676 a 771): 711 críticos
  estão parados esperando o cliente.
- Leitura operacional: o funil é Open (ninguém respondeu) → Pending (respondeu, cliente sumiu) →
  Closed. Só 1/3 chega ao fim, e só esse 1/3 avalia. A satisfação medida ignora os 2/3 que não
  terminaram, o que é viés de sobrevivência.

### 19:09, rodada 5: segmento, produtos e sistema de pagamento

Pergunta do Jó (literal): "tem registrado qual é o segmento do negócio, qual produtos eles vendem e se o sistema de pagamento que eles utilizam disponibiliza api de integracao?"

Resposta do Claude, conferida no dado:

- **Segmento:** não está registrado. O brief diz só "empresa de tecnologia".
- **Produtos:** 42, de marcas diferentes (Apple, Sony, Samsung, LG, Canon, Dyson, Microsoft Office,
  Adobe Photoshop, AutoCAD...), entre 178 e 240 tickets cada, de novo distribuição de sorteio.
  Compras entre 01/01/2020 e 30/12/2021. Assuntos incluem "Delivery problem" (561) e
  "Payment issue" (526). Leitura: perfil de **varejista/e-commerce multimarca de eletrônicos e
  software**, não de fabricante. Inferência, não fato.
- **Sistema de pagamento e API:** não registrado. O texto livre cita "paypal" 33 vezes e
  "credit card" 64, dentro de frases geradas por template, então não comprova o meio de pagamento.
- Consequência: qualquer automação que estorne, cancele ou consulte pagamento é **premissa de
  integração**, e o desenho tem que funcionar sem ela (IA prepara, humano executa).

### 19:10, rodada 6: esses produtos são vendidos pela empresa?

Pergunta do Jó (literal): "esses produtos aparecem como produtos negociados pela empresaiPhone, Samsung Galaxy, LG OLED, Canon, Dyson, PlayStation, Microsoft Office, Photoshop, AutoCAD ?"

Resposta do Claude: a coluna se chama `Product Purchased` ("produto comprado") e vem com
`Date of Purchase`. Não há coluna de vendedor, loja ou canal de venda, então o dado não afirma
quem vendeu. A favor de "a empresa vendeu": existem tickets de reembolso (1.752), cancelamento
(1.695), entrega (561) e pagamento (526), assuntos que só fazem sentido para quem vendeu. A favor
de alternativa: poderia ser um serviço de suporte técnico terceirizado. Conclusão: premissa
declarada "varejista multimarca", com a alternativa registrada nas limitações.

### 19:12, rodada 7: produtos por reembolso, cancelamento, entrega e pagamento

Pergunta do Jó (literal): "consegue seguimentar, quais sao os produtos atrelados aos pedidos de reembolso, pedidos de cancelamento, problemas de entrega e problema de pagameto?"

Resposta do Claude, conferida no dado:

| Recorte | Tickets | Média por produto | Faixa | Mais citados |
|---|---|---|---|---|
| Tipo reembolso | 1.752 | 42 | 25 a 52 | Sony Xperia 52, Sony PlayStation 52, Nikon D 51 |
| Tipo cancelamento | 1.695 | 40 | 25 a 53 | Xbox Controller 53, LG Smart TV 53, LG OLED 52 |
| Assunto entrega | 561 | 13 | 4 a 22 | Amazon Echo 22, Fitbit Charge 19, Philips Hue 19 |
| Assunto pagamento | 526 | 13 | 4 a 22 | Xbox Controller 22, Microsoft Surface 21, Nest 18 |

- Teste qui-quadrado produto × tipo de ticket: 138,8 com 164 graus de liberdade. Valor abaixo do
  esperado por acaso: **produto e tipo de ticket são independentes**. Nenhum produto concentra
  reembolso ou cancelamento.
- Incoerências: "problema de entrega" aparece para Adobe Photoshop e Microsoft Office (software);
  dentro do tipo "reembolso", os assuntos mais comuns são "Hardware issue", "Battery life" e
  "Installation support". Tipo e assunto foram sorteados separadamente.
- O ranking acima é ruído; publicar "Sony lidera reembolsos" seria conclusão falsa.

### 19:15, rodada 8: relatório completo produto × segmento

Pedido do Jó (literal): "quero um relatorio completo de cada segmento com todos os produtos de cada um e a porcentagem que cada produto / software tem de cada segmeto"

Feito por script reprodutível (`solution/analise/produto_por_segmento.py`), saída em
`docs/relatorio-produto-por-segmento.md` e `docs/produto-por-segmento.csv`. Segmentos: os 5 tipos
de ticket mais os assuntos entrega e pagamento. Software = Microsoft Office, Adobe Photoshop e
Autodesk AutoCAD (classificação do Claude). Conferência: a soma das % de cada segmento fecha 100%.

Resultado: cada produto tem entre 2% e 3% de qualquer segmento. O maior desvio entre a fatia no
segmento e a fatia no total é +1,9 p.p. (Xbox Controller em pagamento, 22 tickets). Software
representa 6,8% da base e entre 5,0% e 7,2% de cada segmento. Nenhum produto concentra problema.

### 19:21, rodada 9: qual canal tem o maior gargalo

Pergunta do Jó (literal): "e qual canal de atendimento tem o maior gargalo?"

| Canal | Tickets | Abertos | Aguardando cliente | Fechados | Críticos abertos | Fechados com tempo negativo | Mediana h (só positivos) |
|---|---|---|---|---|---|---|---|
| Telefone | 2.132 | 34,5% | 33,1% | 32,4% | 160 | 364 de 691 | 6,0 |
| Chat | 2.073 | 33,0% | 34,4% | 32,5% | 174 | 319 de 674 | 6,5 |
| Redes sociais | 2.121 | 32,9% | 34,9% | 32,2% | 166 | 336 de 684 | 6,4 |
| E-mail | 2.143 | 32,7% | 33,7% | 33,6% | 192 | 346 de 720 | 6,4 |

Qui-quadrado canal × status: 3,3 com 6 graus de liberdade (limite de significância a 5%: 12,59).
Nenhum canal trava mais que outro. O gargalo é igual nos quatro: cerca de 1/3 sem resposta em
qualquer canal, o que aponta para triagem e fila únicas, não para um canal específico. Telefone
tem a maior fatia de abertos (34,5%), mas a diferença é ruído.

### 19:22, rodada 10: combinações com os piores tempos de resolução

Pergunta do Jó (literal): "Quais combinações geram os piores tempos de resolução?"

Método: só os 1.404 fechados com tempo válido (descartados os 1.365 negativos). Mediana de horas
entre 1ª resposta e resolução por combinação, mínimo de 30 tickets (8 na combinação tripla). Para
saber se o "pior" é real, o Claude embaralhou os tempos 300 vezes e mediu qual seria a pior mediana
só por acaso (teste de permutação).

| Combinação | Pior real | Pior por acaso (mediana) | Limite 95% do acaso |
|---|---|---|---|
| Canal × prioridade | Chat/High 8,4 h (n=101) | 7,8 h | 8,8 h |
| Prioridade × tipo | High/Refund 8,8 h (n=83) | 8,2 h | 9,2 h |
| Canal × tipo | Chat/Cancelamento 7,3 h (n=75) | 8,3 h | 9,1 h |
| Canal × prioridade × tipo | Chat/Low/Technical 13,2 h (n=15) | 11,7 h | 14,2 h |

Todas as piores combinações ficam dentro do que o acaso produz. Contradição de negócio: a melhor
combinação canal × prioridade é Chat/Critical (4,5 h), e a pior é Chat/High (8,4 h). Prioridade não
organiza a fila. Conclusão: não há combinação que gere tempo pior de verdade neste dado.

### 19:29, rodada 11: o que mais influencia a satisfação

Pergunta do Jó (literal): "Quais variáveis mais influenciam o Customer Satisfaction Rating?"

Método (2.769 fechados, os únicos com nota): teste de Kruskal-Wallis para variáveis categóricas,
correlação de Spearman para numéricas, e um modelo Random Forest com todas as variáveis juntas,
validação cruzada de 5 partes. Ambiente: venv do case com pandas, scipy e scikit-learn.

| Variável | p-valor | Maior diferença entre grupos |
|---|---|---|
| Ano da compra | 0,057 | 0,10 ponto |
| Tamanho do texto da resolução | 0,124 | rho +0,029 |
| Tempo negativo (registro impossível) | 0,156 | 0,08 |
| Horas até resolver | 0,254 | rho +0,022 |
| Canal | 0,278 | 0,13 |
| Gênero | 0,625 | 0,06 |
| Prioridade | 0,629 | 0,09 |
| Produto | 0,667 | 0,68 (grupos pequenos) |
| Tipo | 0,699 | 0,09 |
| Tamanho da descrição | 0,770 | rho +0,006 |
| Assunto | 0,807 | 0,38 |
| Idade | 0,832 | rho -0,004 |
| Faixa de idade | 0,893 | 0,08 |

- Nenhuma das 13 variáveis passa de p < 0,05, mesmo sem correção para testes múltiplos.
- Modelo com tudo junto: R² = -0,023 (pior que prever a média) e acurácia de 21,6% na nota exata,
  contra 20,9% de chutar sempre a nota mais comum.
- Resposta: **nenhuma variável do dataset influencia a satisfação**. A nota se comporta como sorteio
  uniforme de 1 a 5. O que realmente move satisfação (resolveu na 1ª vez? reabriu? tom da resposta?)
  não foi coletado.

### 19:32, rodada 12: quantos tickets existem nos arquivos

Pergunta do Jó (literal): "quantos ticket totais você consegue ler nos arquivos?"

- Dataset 1: 8.469 tickets, todos lidos, IDs únicos, 392 descrições repetidas palavra por palavra.
  O brief diz ~30.000.
- Dataset 2: 47.837 textos, todos lidos, nenhum vazio, nenhum duplicado, mediana de 26 palavras.
  Categorias: Hardware 13.617, HR Support 10.915, Access 7.125, Miscellaneous 7.060, Storage 2.777,
  Purchase 2.464, Internal Project 2.119, Administrative rights 1.760. Classes desbalanceadas (7,7×
  entre a maior e a menor), o que importa para medir o classificador por categoria.
- Total: 56.306. Os dois arquivos não se ligam por nenhuma chave: são empresas e contextos
  diferentes (varejo para consumidor × TI interna).

### 19:33, rodada 13: base de cada análise

Pergunta do Jó (literal): "em todas essas analises você considerou todos esses tickkets?"

Resposta do Claude: não, e cada análise usou a base que o dado permite.

| Análise | Base usada | Por quê |
|---|---|---|
| Estrutura, status, funil, produtos × segmento, canal × status | 8.469 (todo o Dataset 1) | Campos preenchidos em todos |
| Tempo até resolver, satisfação, variáveis × satisfação | 2.769 fechados | Só fechados têm resolução e nota |
| Combinações com pior tempo | 1.404 | Fechados menos os 1.365 com tempo negativo |
| Dataset 2 | 47.837 só contados e categorizados | Ainda não analisado; é a base do classificador |

Ponto de atenção registrado: as conclusões de satisfação valem para 1/3 dos tickets (quem chegou ao
fim). Os 5.700 abertos ou pendentes não têm nota, então não se sabe a satisfação deles.

### 19:35, rodada 14: refazer tudo com 100% dos tickets

Pedido do Jó (literal): "quero que você refaça todas as analises que eu pedi, considerando 100% de todos os tickets"

Decisão do Claude, explicada ao Jó: satisfação e tempo de resolução não existem em 5.700 dos 8.469
tickets; estimar esses valores seria inventar dado. Para cobrir 100%, troquei o desfecho para o
**status** do ticket (sem resposta, aguardando cliente, fechado), que todo ticket tem. As análises
de produto × segmento, canal × status e estrutura já usavam 100%.

Script: `solution/analise/diagnostico_base_completa.py`; saída: `docs/relatorio-diagnostico-base-completa.md`.

- 8 variáveis contra o status (qui-quadrado): menor p-valor 0,073 (faixa de idade); V de Cramér
  máximo 0,067 (produto, 42 categorias). Nenhuma relação.
- Modelo com tudo junto: 34,2% de acerto no status contra 34,0% do chute; 67,3% contra 67,3% para
  "fechou ou não"; 66,7% contra 66,7% para "ficou sem resposta". O modelo não aprende nada.
- Canal × prioridade: a pior célula é Telefone/Low com 38,9% sem resposta (499 tickets), dentro do
  esperado para 16 células de ~500 tickets.
- Conclusão em 100% da base: o que faz um ticket travar não está em nenhuma variável registrada.

### 19:38, rodada 15: regra do Jó, nada sem dado

Fala do Jó (literal): "havona, importante você entender que aqui a gente não chuta nada, trabalhamos 100% baseado nos dados.. tudo aqui é decidido com base nnos dados"

Regra adotada a partir daqui: toda afirmação da entrega sai de um número do dado, com a base (n)
ao lado. O que o dado não tem vira **lacuna de dado** (o que precisa ser coletado), nunca
suposição. O registro anterior fica como está, para mostrar a correção; abaixo, o que o Claude
afirmou sem base e como passa a ser tratado:

| Afirmação anterior do Claude | Tinha dado? | Como fica |
|---|---|---|
| Empresa é "varejista multimarca" (rodadas 5 e 6) | Não, era dedução | Sai. Fato: 42 produtos em `Product Purchased`; segmento não registrado |
| Pendentes "provavelmente mais insatisfeitos" | Não | Sai. Fato: 5.700 tickets sem nota; satisfação deles desconhecida |
| Gargalo é "falta de triagem" (rodadas 9 e 10) | Parcial | Fica só o fato: 33,3% sem resposta em todos os canais; prioridade sem relação com status (p = 0,227) |
| O que move satisfação é "resolver na 1ª vez, reabertura, tom" | Não, era experiência de operação | Sai como conclusão; vira lista de campos que não existem no dado |
| Premissas de custo/hora e atendentes (rodada 1) | Não | Sem custo no dado, não haverá cálculo de custo em reais; horas só onde o dado tem tempo |
| "Chute" como linha de base do modelo | Termo, não suposição | Renomeado para "linha de base" nos relatórios |

### 19:40, rodada 16: as piores combinações se mantêm com a base total?

Pergunta do Jó (literal): "esse resultado permanece, pos a analise total ou tem alguma coisa que precisa acrescentar?"

Refeito por script (`solution/analise/combinacoes.py`), 1.000 embaralhamentos por cruzamento, saída
em `docs/relatorio-combinacoes.md`.

- Tempo até resolver: a base continua 1.404 (só eles têm tempo coerente). Resultado mantido:
  nenhuma combinação passa do limite do acaso.
- Acrescentado: a mesma análise em 100% dos 8.469 tickets, medindo % sem resposta. Telefone/Baixa
  (499 tickets, 38,9%) passou do limite de 95% (38,6%), p = 0,049 em 5.000 embaralhamentos. Com 8
  testes, a correção de Bonferroni leva o limite a 40,1%: não passa. Nenhuma combinação se destaca.
- O Claude registra que um "sim" isolado em 8 testes é o esperado por acaso e não foi tratado como
  achado.

### 19:53, resposta 1 do Jó: onde o fluxo trava

**Pergunta do brief:** Onde o fluxo trava? Gargalos por canal, prioridade, tipo de ticket. Quais combinações geram os piores tempos de resolução?

**Resposta adotada pelo Jó** (tabelas da rodada 16, coladas por ele como resposta):

1. Tempo até resolver (base: 1.404 fechados com registro coerente)

| Cruzamento | Pior combinação | Tickets | Limite do acaso (95%) | É real? |
|---|---|---|---|---|
| Canal × prioridade | Chat / Alta: 8,4 h | 101 | 8,8 h | não |
| Prioridade × tipo | Alta / Reembolso: 8,8 h | 83 | 9,2 h | não |
| Canal × tipo | Chat / Cancelamento: 7,3 h | 75 | 9,2 h | não |
| Canal × prioridade × tipo | Chat / Baixa / Problema técnico: 13,2 h | 15 | 14,3 h | não |

2. % sem resposta (base: 8.469 tickets, 100% do Dataset 1)

| Cruzamento | Pior combinação | Tickets | Limite do acaso (95%) | É real? |
|---|---|---|---|---|
| Canal × prioridade | Telefone / Baixa: 38,9% | 499 | 38,6% | passou por 0,3 ponto |
| Prioridade × tipo | Alta / Cancelamento: 37,9% | 398 | 39,8% | não |
| Canal × tipo | Redes sociais / Cancelamento: 36,3% | 413 | 39,6% | não |
| Canal × prioridade × tipo | Telefone / Alta / Cobrança: 44,7% | 103 | 48,4% | não |

**Conclusão (aprovada pelo Jó às 19:54):** Nenhuma combinação de canal, prioridade e tipo é pior que o acaso. Telefone / Baixa passou do limite simples por 0,3 ponto, mas não resiste à correção para 8 testes (limite de 40,1%). O fluxo trava igual em todos os recortes: 1/3 dos tickets fica sem resposta.

### 20:26, rodada 17: o que impacta a satisfação, com 100% das notas

Pedido do Jó (literal): "me responde essa pergunta com base em 100% de toda a base. O que impacta satisfação?"

Base: a nota existe em 2.769 tickets (32,7%), todos os fechados; os outros 5.700 (67,3%) não têm
nota. A análise usa 100% das notas existentes. Script `solution/analise/satisfacao.py`, saída
`docs/relatorio-satisfacao.md`.

- Notas de 1 a 5 entre 19,6% e 20,9% cada; aderência a sorteio uniforme p = 0,797.
- 15 variáveis testadas (as 9 do arquivo e 6 derivadas: horas até resolver, registro impossível,
  dias entre compra e 1ª resposta, hora da 1ª resposta, tamanho da descrição e da resolução).
  Menores p: hora da 1ª resposta 0,033 e dias desde a compra 0,041; corrigidos para 15 testes,
  0,502 e 0,619. Nenhuma passa.
- Modelos com tudo: Random Forest 21,2% contra 20,9% de linha de base; R² -0,013.

**Erro do Claude encontrado e corrigido nesta rodada:** o modelo de texto da descrição deu p = 0,002
no primeiro teste. O Claude não aceitou e conferiu: descrições repetidas não explicam (1 de 24 grupos
com nota igual), e o primeiro teste tinha vazamento (vocabulário aprendido com a base inteira). Com
validação correta em 10 divisões contra 40 sorteios: 21,7% contra 20,2%, p = 0,05, no limite e sem
resistir à correção. As palavras com mais peso não têm sentido de negócio.

Resposta: nenhuma variável registrada, nem o texto, impacta a satisfação.

## Rodada 18 (23:34 BRT): satisfação de quem teve o ticket fechado

**Pergunta do Jó (literal):** "mas e de quem teve o ticket fechado, não traz o daddo de satisfacao?"

**Resultado (n = 2.769 fechados):** todo ticket fechado tem nota (2.769 de 2.769) e nenhum ticket não fechado tem nota (0 de 5.700).

| Nota | Tickets | % |
|---|---|---|
| 1 | 553 | 20,0% |
| 2 | 549 | 19,8% |
| 3 | 580 | 20,9% |
| 4 | 543 | 19,6% |
| 5 | 544 | 19,6% |

Média 2,99, mediana 3. Notas 1 e 2: 39,8%. Notas 4 e 5: 39,3%.

## Rodada 19 (23:44 BRT): categoria contra nota

**Pergunta do Jó (literal):** "destrincha quais sao as categorias vs a nota, pra gente entender se existe uma categorias que puxam mais para determinadas notas"

**O que foi feito:** `solution/analise/categoria_vs_nota.py`, base de 2.769 fechados (100% das notas). Sete variáveis
(tipo, prioridade, canal, assunto, produto, gênero, faixa de idade) cruzadas com a nota de 1 a 5, com qui-quadrado,
V de Cramér, correção para 7 testes e resíduo ajustado por célula, com limite corrigido para 395 células (|3,83|).
Relatório em `docs/relatorio-categoria-vs-nota.md` e tabela completa em `docs/categoria-vs-nota.csv`.

**Resultado:** nenhuma variável puxa a nota (menor p = 0,148, gênero; corrigido 1,000). V de Cramér entre 0,029 e
0,126. Zero de 395 células passa do limite. A célula mais afastada é Garmin Forerunner com nota 4 (35,7% de 70
tickets, resíduo +3,44, abaixo de 3,83). Os produtos dos extremos (Fitbit Versa com média 2,5 e 54,0% de notas 1-2;
Dyson com média 3,2 e 54,2% de notas 4-5) têm cerca de 60 tickets cada, e a diferença cabe no acaso dos 42 produtos.

## Rodada 20 (antes de 23:48 BRT): o que é a coluna "Categorias"

**Pergunta do Jó (literal):** "nessa coluna que tem as categorias que tem os numeros, esses numeros se refere o que exatamente?"

**Resposta:** é a quantidade de valores diferentes que cada variável assume na base de 2.769 fechados (por exemplo,
Tipo de ticket = 5: Reembolso, Problema técnico, Cobrança, Dúvida de produto, Cancelamento). Não é contagem de tickets.

## Rodada 21 (23:48 BRT): resposta ao diretor sobre satisfação

**Pergunta do Jó (literal):** "o diretor me perguntou sobre esses pontos referente a satisfacao: É o tempo de resposta? O canal? O tipo de problema? levando em consideração os dados que levantamos me ajuda a connstruir uma resposta coerente pra essas perguntas"

**Dado novo desta rodada:** horas entre 1ª resposta e resolução só nos 1.404 fechados com registro coerente:
rho = +0,003, p = 0,921. Por quartil de tempo (até 3 h, 3 a 6,3 h, 6,3 a 11,4 h, 11,4 a 23,5 h), médias 2,99 / 3,01 /
3,13 / 2,97, Kruskal p = 0,426. O dado não tem a data de abertura, então o tempo até a 1ª resposta não pode ser medido.
Canal: médias de 2,95 (telefone) a 3,08 (chat), p = 0,278 (n = 2.769). Tipo: médias de 2,93 (reembolso) a 3,03, p = 0,699.

## Rodada 22 (23:49 BRT): resposta 2 salva

**Jó (literal):** "Sim, salva". A resposta da rodada 21 foi adotada como Diagnóstico 2, sem alteração.

## Rodada 23 (23:51 BRT): quanto estamos desperdiçando

**Pedido do Jó (literal):** "analisa os dados que levantamos e me traz um posicionamento sobre a terceira pergunta"

**O que foi feito:** medição de horas nos 1.404 fechados coerentes (soma 10.639 h, mediana 6,3 h; 25% mais lentos =
51,7% das horas; tipo p = 0,160, canal p = 0,791, prioridade p = 0,091 no Kruskal), volume parado por status e
checagem de textos repetidos (47 grupos, 439 tickets, nenhum cliente repetido no grupo: texto-modelo, não duplicata).
Custo não estimado: o dado não tem custo, atendente nem tempo trabalhado. Relatório em `docs/relatorio-desperdicio.md`.

## Rodada 24 (entre 23:51 e 23:58 BRT): o Jó reescreve o fechamento

O Jó propôs a própria versão da resposta, acrescentando "sem antes criar as métricas para isso", e perguntou:
"faz sentido esse completo que eu fiz?". Avaliação: faz sentido e o dado sustenta; sugeri separar a última frase em
duas e nomear as métricas (data de abertura, tempo trabalhado por ticket, custo da hora). Ele pediu: "manda a msg
completa agora para validar com a sua sugestao com maiorr detalhamento".

## Rodada 25 (23:58 BRT): resposta 3 salva

**Jó (literal):** "pode salvar". A versão detalhada foi adotada como Diagnóstico 3. O diagnóstico do brief está completo
(1. onde trava, 2. o que impacta a satisfação, 3. quanto desperdiça), todas as respostas escritas pelo Jó a partir
dos números desta base.

## Rodada 26 (23:59 BRT): volta às 6 perguntas do bloco 2

**Pedido do Jó (literal):** "traz as 6 perguntas novamente". Reapresentadas com o contexto atualizado pelos diagnósticos 1 a 3.

## Rodada 27 (08:05 BRT): tabelas de resultados

**Pedido do Jó (literal):** "traz tbm as tabelas de resultados das pesquisas que fizemos". Os seis relatórios de `docs/` foram reunidos num documento único (`relatorios/2026-11-11-resultados-consolidados.md` no workspace), sem alterar números.

## Rodada 28 (2026-11-11 08:08 BRT): atendentes e setores

**Pergunta do Jó (literal):** "nos arquivos tem qntos atenddentes trabalham e se eles estao setorizado, se sim quantos e quais setores?"

**Resposta:** não. O Dataset 1 tem 17 colunas e nenhuma identifica atendente, equipe ou setor. O Dataset 2 tem 2 colunas
(`Document`, `Topic_group`); as 8 categorias de `Topic_group` classificam o assunto do ticket, não quem atende. O brief
cita "o time está sobrecarregado" e "agente de suporte" sem número de pessoas nem divisão por setor. Lacuna de dado.

## Rodada 29 (2026-11-11 08:10 BRT): registro das lacunas de dado

**Pedido do Jó (literal):** "regiistra que levantamos a falta dessa informacao tbm"

**O que foi feito:** criado `docs/lacunas-de-dado.md`, com as 12 lacunas levantadas desde a rodada 1, cada uma com evidência, o que impede de responder e a rodada de origem. Número de atendentes (lacuna 1) e setorização (lacuna 2) entram a partir da rodada 28.

## Rodada 30 (2026-11-11 09:31 BRT): resposta do Jó à pergunta 1 do bloco 2 (problema real)

**Resposta do Jó (literal):** "Respondendo à primeira questão, onde o diretor disse que o time está sobrecarregado, que o tempo de resolução subiu e a satisfação caiu, tem alguns pontos importantes. Não dá para saber, pelos dados que foram passados, se o time está sobrecarregado de fato, porque a gente não tem dados de quantidade de pessoas versus os números de chamado, mas fica muito claro que há uma falta de processo no atendimento. Um outro ponto importante, o tempo de resolução de fato subiu, mas também não há indício claro que a satisfação caiu. Por que que não há indício claro? Porque falta essa estruturação de processos, não só do atendimento do time, mas também da estruturação de métricas. Então, eu não tenho dados para comprovar todos esses apontamentos, mas fica claro que há um problema real na empresa quanto ao processo de atendimento. Há um problema de tempo, há um problema de satisfação e há um problema de sobrecarga, mas não necessariamente esses são os motivos, e sim as consequências."

**Conferência contra o dado (Claude):** sobrecarga não mensurável (lacunas 1 e 2) e falta de processo sustentada por
números (prioridade não muda o status, p = 0,227, com 692 críticos sem resposta; 1/3 sem resposta igual em todos os
recortes; 49,3% dos fechados com tempo impossível; nota só no fechamento). Um ponto não se sustenta: "o tempo de
resolução de fato subiu". O dado não tem data de abertura nem série no tempo (as respostas cabem numa janela de 27 h),
então não dá para comparar períodos. O mesmo vale para "a satisfação caiu". Proposta de ajuste enviada ao Jó; não salvo.

## Rodada 31 (2026-11-11 09:42 BRT): resposta 1 do bloco 2 salva

**Jó (literal):** "Sim, salva". A versão ajustada da rodada 30 foi adotada como resposta à pergunta 1 do bloco 2. O ajuste retirou a afirmação "o tempo de resolução de fato subiu", que o dado não sustenta.

## Rodada 32 (2026-11-11 09:43 BRT): resposta do Jó à pergunta 2 do bloco 2 (custo, capacidade ou satisfação)

**Resposta do Jó (literal):** "Como não tem dados de custo, eu não consigo pontuar isso como uma prioridade nesse processo que vamos fazer de implementação. Mas posso adiantar que vamos ter um reflexo positivo de baixo custo na hora que a gente fizer a reestruturação e a automação de alguns pontos. Vamos priorizar tanto a capacidade de resposta e a satisfação do cliente. Isso vai ser trabalhado de forma conjunta. Ambos serão atendidos com o processo de automação que vamos construir, porque como a gente tem uma pulverização nos problemas, nas categorias, não tem como a gente trabalhar um único ponto, vamos trabalhar no processo de atendimento como um todo para conseguir resolver a sobrecarga de atendimento, tempo de atendimento e satisfação."

**Conferência contra o dado (Claude):** "pulverização" sustentada (5 tipos entre 19,3% e 20,7%; nenhum recorte concentra
falta de resposta, horas ou nota). Custo fora da prioridade por falta de dado: coerente com a lacuna 5. Dois pontos
pedem ajuste: (1) "reflexo positivo de baixo custo" é expectativa, não resultado medido, e precisa vir rotulada assim;
(2) satisfação não tem hoje nenhuma variável que a explique e 67,3% não têm nota, então priorizá-la começa por medi-la.
"Resolver a sobrecarga" foi alinhado à resposta 1 (sobrecarga é consequência e não mensurável). Proposta de ajuste enviada; não salvo.

## Rodada 33 (2026-11-11 09:45 BRT): resposta 2 do bloco 2 salva

**Jó (literal):** "Sim, salva". A versão ajustada da rodada 32 foi adotada. Ajustes: queda de custo rotulada como hipótese a medir; satisfação começa por medição; sobrecarga tratada como consequência, coerente com a resposta 1.

## Rodada 34 (2026-11-11 09:47 BRT): resposta do Jó à pergunta 3 do bloco 2 (responder na hora resolve?)

**Resposta do Jó (literal):** "O problema não é o tempo de resposta imediata, e sim a finalização do problema em questão. Então a respost é, não estaria resolvido. Como eu expliquei nas mensagens anteriores, aqui é um problema de processo. E a gente tem que olhar para esse processo como um todo para, de fato, resolver as três principais dores que o diretor trouxe."

**Conferência contra o dado (Claude):** o "não" se sustenta. Dos 5.650 tickets que já receberam a 1ª resposta
(2.881 aguardando o cliente + 2.769 fechados), só 2.769 (49,0%) foram fechados: responder não garante finalizar. Mesmo
que os 2.819 sem resposta fossem respondidos na hora, a proporção observada indica que cerca de metade continuaria
sem fechamento, se repetisse o padrão dos já respondidos (projeção rotulada como tal). Cuidado: o dado não mostra que
finalizar mais rápido melhora a nota (rho = +0,003, n = 1.404), então a resposta não deve prometer isso. Proposta de
ajuste enviada; não salvo.

## Rodada 35 (2026-11-11 09:49 BRT): resposta 3 do bloco 2 salva

**Jó (literal):** "Sim, salva". A versão ajustada da rodada 34 foi adotada, com a prova de que responder não é finalizar (49,0% dos respondidos fechados) e sem prometer ganho de satisfação por resolver mais rápido.

## Rodada 36 (2026-11-11 10:02 BRT): resposta do Jó à pergunta 4 do bloco 2 (ponto mais importante)

**Resposta do Jó (literal):** "O ponto mais importante da entrega é a reestruturação de todo o departamento do suporte.  Considerando desde da automação para receber o cliente, seja ele qual categoria ele se encaixa, até a resolução do problema de fato. E a definição até onde essas automações irão e o treinamento do time para essa nova realidade."

**Conferência contra o dado (Claude):** coerente com as respostas 1 a 3 (problema de processo, pulverizado, responder
não é finalizar). Pontos a amarrar: (1) "receber o cliente seja qual categoria" depende de um classificador ainda não
construído; a base existe (Dataset 2, 47.837 textos, 8 categorias de 3,7% a 28,5%), mas a precisão só pode ser
afirmada depois de medida; (2) treinamento do time não tem dado de equipe (lacunas 1 e 2), então entra como etapa do
plano, sem número; (3) faltou a medição, que as respostas 1 a 3 colocam como parte do problema. Proposta de ajuste enviada; não salvo.

## Rodada 37 (2026-11-11 10:05 BRT): resposta 4 do bloco 2 salva

**Jó (literal):** "Sim, salva". A versão ajustada da rodada 36 foi adotada: quatro frentes (entrada com classificador medido, acompanhamento até a resolução, limite da automação, time e medição).

## Rodada 38 (2026-11-11 10:12 BRT): resposta do Jó à pergunta 5 do bloco 2 (o que a IA nunca faz sozinha)

**Resposta do Jó (literal):** "Essa questão do o que a IA nunca deve responder ou executar sozinha, ela é uma pergunta profunda que eu não consigo responder antes de entender a fundo quais são os sistemas que a empresa utiliza, se esses sistemas têm API, o que essas APIs fornecem de acesso, mas eu acredito que a gente consegue automatizar bastante coisa e respondendo exatamente o que ela não pode executar sozinha, acredito que em um primeiro momento eu não colocaria na finalização do reembolso e no cancelamento. Os outros pontos, problemas técnicos, dúvidas de produto e até mesmo cobrança, a gente pode automatizar o máximo que a gente conseguir dentro das ferramentas que a empresa disponibilizar para a gente. E após os 30 dias, avaliamos se conseguimos avançar nas automações que ainda permanece manuais olhando para o histórico e métricas."

**Conferência contra o dado (Claude):** dependência de sistemas e API coerente com a lacuna 10. Reembolso e cancelamento
somam 3.447 tickets (40,7%), dos quais 867 críticos e 1.146 sem resposta. O dado não mostra que esses tipos sejam mais
arriscados (não há valor, estorno nem resultado); o critério é de julgamento (ação irreversível sobre dinheiro e
contrato) e deve vir rotulado assim. Cobrança mexe com dinheiro: separar responder e explicar (automatizável) de
alterar cobrança (pessoa). A coluna `Resolution` do Dataset 1 é texto sem sentido, então não há resposta correta de
referência para medir a qualidade da IA em problema técnico; a qualidade terá de ser medida na operação. Proposta de ajuste enviada; não salvo.

## Rodada 39 (2026-11-11 10:14 BRT): resposta 5 do bloco 2 salva

**Jó (literal):** "Sim, salva". Adotada a versão ajustada da rodada 38: a IA conversa em todos os tipos e não executa ação irreversível sobre dinheiro ou contrato (reembolso, cancelamento, alteração ou estorno de cobrança); critério rotulado como julgamento.

## Rodada 40 (2026-11-11 10:32 BRT): resposta do Jó à pergunta 6 do bloco 2 (como saber em 30 dias)

**Resposta do Jó (literal):** "Para a gente conseguir entender se todo esse processo de reestruturação funcionou, e eu estou chamando de processo de reestruturação porque não é somente automação. E sim o processo como um todo. E para isso vamos precisar implementar as métricas que vão nos orientar para compreender os resultados. Vamos incluir data e hora de abertura, qual foi o atendente que trabalhou, como que esse cliente chegou e como que ele finalizou, tempo trabalhado nesse atendimento, qual foi o custo desse atendimento perante o custo hora do atendente, se houve reabertura ou não, como estava a satisfação desse cliente quando ele chegou e como que está na finalização do ticket com uma pesquisa de NPS, entre outras, como porcentagem de tempo de pessoas sem resposta após encaminhar para um humano, demora de atendimentos críticos sem resposta, tempo de fechamento daquele ticket após a abertura, analise das notas dos tickets. Além de outras métricas que, após a reunião de levantamento de todo o processo, muito provavelmente irão surgir e vamos incluir nesse dashboard para entender o resultado daqui 30 dias."

**Conferência contra o dado (Claude):** as métricas cobrem as lacunas 1, 3, 4, 5, 7 e 9. Pontos a amarrar: (1) falta
dizer o que conta como "funcionou": comparar com a linha de base que o dado já dá (33,3% sem resposta, 692 críticos sem
resposta, 49,0% dos respondidos fechados, 32,7% com nota, 49,3% de tempo impossível), sem inventar meta numérica;
(2) métricas novas não têm linha de base, então os primeiros 30 dias viram a linha de base delas; (3) a nota atual é de
1 a 5; trocar só por NPS (0 a 10) quebra a comparação, então manter a nota de 1 a 5 ao lado do NPS. Proposta de ajuste enviada; não salvo.

## Rodada 41 (2026-11-11 10:34 BRT): resposta 6 do bloco 2 salva, bloco 2 completo

**Jó (literal):** "Sim, salva". Adotada a versão ajustada da rodada 40. Com isso, os 3 diagnósticos do brief e as 6 perguntas do bloco 2 estão respondidos pelo Jó, cada um com a versão original literal neste log e a tabela de evidências no arquivo do bloco 2.

## Rodada 42 (2026-11-11 10:37 BRT): início da parte 2, auditoria do Dataset 2

**Pedido do Jó (literal):** "Sim, começa" (resposta a "Começo a parte 2 pela auditoria do Dataset 2?").

**O que foi feito:** `solution/analise/auditoria_dataset2.py` gera `docs/relatorio-auditoria-dataset2.md`. Achados:
47.837 textos, 0 vazios, 0 duplicados (nem após normalizar), 0 conflitos de rótulo; texto já pré-processado (sem
maiúsculas, dígitos nem e-mails); 8 categorias de 3,7% a 28,5% (7,7 vezes); 1.210 textos de Compra (49,1% da categoria)
são o formulário "new purchase po", que pode inflar o acerto de Compra; palavras como "leave", "locked" e
"administrator" mudam de sentido entre categorias.

**Correção minha durante a auditoria:** a primeira versão dizia que "administrator aparece em formulário de compra"
sem conferir. Conferido: 1.184 dos 1.980 textos de Compra com essas palavras começam com "new purchase po", e a
palavra é a assinatura do formulário. A frase foi reescrita com o número.

## Rodada 43 (2026-11-11 10:43 BRT): classificador do Dataset 2

**Pedido do Jó (literal):** "Sim, segue" (resposta a "Sigo para o classificador com acerto medido por categoria?").

**O que foi feito:** `solution/analise/classificador.py`. 20% de teste separado antes de tudo; 5 modelos comparados
por validação cruzada só no treino, com o vetorizador dentro do pipeline (lição do vazamento da rodada 17). Escolhido
pelo F1 macro: regressão logística com peso por categoria (86,5% na validação). No teste: acurácia 87,0% contra 28,5%
da linha de base; F1 de 79,7% (Direitos de administrador) a 92,0% (Compra). Maior confusão relativa: 15% de Direitos
de administrador previstos como Hardware. Compra: 99,6% no formulário automático, 79,4% sem ele. Curva de confiança:
com limite 0,7 o modelo decide 77,0% dos tickets com 94,8% de acerto e passa 23,0% para uma pessoa.

**Limite declarado:** a curva foi lida no teste; o limite de operação deve ser fixado com tickets novos. O modelo prova
o método em TI interna, não o acerto nos 5 tipos do Dataset 1.

## Rodada 44 (2026-11-11 11:32 BRT): diferença entre os limites 0,7 e 0,8

**Pergunta do Jó (literal):** "qual é a difereca das duas opcoes?"

**Resposta:** a cada 1.000 tickets, pelos percentuais do teste: limite 0,7, a IA classifica 770 e erra cerca de 40, 230 vão para uma pessoa; limite 0,8, a IA classifica 684 e erra cerca de 25, 316 vão para uma pessoa. Subir de 0,7 para 0,8 evita cerca de 15 erros e manda 86 tickets a mais para o time. O limite vale só para classificar e encaminhar; ação irreversível continua sempre com uma pessoa (resposta 5).

## Rodada 45 (2026-11-11 11:33 BRT): decisão do limite de confiança

**Decisão do Jó (literal):** "0,8". No teste, a IA classifica sozinha 68,4% dos tickets com 96,4% de acerto, e 31,6% vão para triagem humana. O valor será revisto com os dados dos primeiros 30 dias (resposta 6).

## Rodada 46 (2026-11-11 11:33 BRT): rascunho do fluxo proposto

Com o limite 0,8 decidido, montei `docs/fluxo-proposto.md`: 9 etapas (entrada, leitura, roteamento, prioridade, primeira resposta, ação sobre dinheiro ou contrato, acompanhamento, fechamento, medição), cada uma com o papel da IA, o da pessoa e o dado que a sustenta. Três parâmetros ficam a definir (prazo do alerta de crítico, intervalo do follow-up, amostra de revisão). Enviado ao Jó para validação; não adotado ainda.

## Rodada 47 (2026-11-11 11:38 BRT): fluxo aprovado

**Jó (literal):** "Aprovado". O fluxo de 9 etapas de `docs/fluxo-proposto.md` foi adotado como a proposta de automação. Seguem a definir: prazo do alerta de crítico, intervalo do follow-up e amostra de revisão.

## Rodada 48 (2026-11-11 11:41 BRT): recepção conversacional antes do commit

**Pedido do Jó (literal):** "antes de comitar o atedimento sempre recebe o cliente de forma humanizada e conversa de forma inteligennte até entender qual é a categoria que o cliente se encaixa"

**Conferência contra o dado (Claude):** o Dataset 2 só tem um texto por ticket, então a conversa não pode ser medida
diretamente. Teste substituto: classificar só as 10 primeiras palavras e depois o texto inteiro, no mesmo teste
separado. Acerto 78,2% com 10 palavras contra 87,0% com o texto inteiro; dos 3.271 tickets abaixo de 0,8 com 10
palavras, 35,6% passam de 0,8 com o texto inteiro. Mais informação aumenta o acerto, o que sustenta perguntar antes de
rotear. Também medido: tickets mais longos não têm confiança maior (média de 0,868 até 10 palavras e 0,841 acima de 80),
então o ganho vem de informação útil, não de tamanho.

**Mudança no fluxo:** etapa 2 virou "Recepção e conversa" (a IA recebe de forma humanizada e pergunta até a confiança
passar de 0,8); etapa 3 passa para uma pessoa só depois do número máximo de perguntas, novo parâmetro a definir.

## Rodada 49 (2026-11-11 11:43 BRT): commit da parte 2

**Jó (literal):** "Sim, commita". Commit local `7a601fa`, sem push.

## Rodada 50 (2026-11-11 11:45 BRT): escopo do protótipo

**Pedido do Jó (literal):** "acredito que precisamos alem do roteador a ia conversacional, qndo precisar me fala que eu gero o token do deepseek, m fala se precisamos aprrensetar o painel das conversas e o dashboard"

**Leitura do brief (seção 3 e critérios):** protótipo é diferencial, não obrigatório; dashboard aparece só como um dos
exemplos. O critério que pesa é "funciona com dados reais, não com 3 exemplos cherry-picked", e o primeiro critério
é "usou ambos os datasets? o poder está no cruzamento". Recomendação enviada ao Jó: IA conversacional + roteador +
painel das conversas numa página só, rodando também em lote sobre o teste real; dashboard enxuto com os 5 indicadores
de linha de base do Dataset 1, ao lado das decisões do roteador. Chave da DeepSeek só em arquivo .env fora do repo,
com modo sem chave para o avaliador rodar.

## Rodada 51 (2026-11-11 11:53 BRT): protótipo construído, aguardando a chave da DeepSeek

**Pedido do Jó (literal):** "Aprovado" (escopo da rodada 50).

**O que foi feito:** `solution/prototipo/` com config, modelo (mesma separação e modelo do relatório), roteador
(funções puras), conversa (DeepSeek ou modo sem IA), lote e página Streamlit com Conversa, Painel do atendente e
Dashboard. 19 testes passando. Lote nos 9.568 tickets reais do teste: 68,4% roteados pela IA com 96,4% de acerto,
31,6% para triagem humana, iguais ao relatório. Dashboard confere com os relatórios (33,3%, 692, 49,0%, 32,7%, 49,3%).

**Achados durante a construção:**
- O texto do Dataset 1 não prevê o tipo do ticket (19,7% de acerto contra 20,7% da linha de base), então a trava de
  reembolso, cancelamento e alteração de cobrança é por regra, com a IA conversacional sinalizando também.
- Erro do modelo encontrado no teste do protótipo: "hello i need help" recebia 0,82 de confiança em Hardware e seria
  roteado sem o cliente ter dito o problema. Corrigido com a trava de texto sem conteúdo (a IA pede a descrição); 3
  testes novos cobrem o caso.
- Erro meu corrigido: uma substituição automática de formato reescreveu a própria função de formato e a página
  quebrou com recursão infinita; pego no teste da página e corrigido antes de mostrar.

## Rodada 52 (2026-11-11 11:58 BRT): IA conversacional ligada e testada

**Jó (literal):** "feito, pode testar" (chave da DeepSeek gravada por ele em arquivo fora do repositório).

**Teste com a DeepSeek, 9 conversas:** saudação faz a IA pedir o problema; "notebook não liga depois da atualização"
vai para Hardware com 0,89; reembolso de monitor com defeito e cancelamento de assinatura vão para "pessoa decide e
executa"; pedido de senha de administrador gera pergunta de esclarecimento com 0,46.

**Erro encontrado e corrigido:** a conversa "preciso de uma coisa / é sobre o sistema / não sei explicar direito / é
urgente" terminava roteada para Hardware com 0,89 de confiança, sem o cliente ter dito o problema. A contagem de palavras
úteis não pega português vago. Correção: a própria IA informa se o problema foi descrito (campo problema_descrito); com
isso a mesma conversa vai para uma pessoa depois de 3 perguntas. "Preciso de ajuda com uma pasta" também deixou de ser
roteado direto (1,00 em Armazenamento) e passou a pedir detalhe antes.

## Rodada 53 (2026-11-11 12:07 BRT): régua de validação antes do commit

**Pedido do Jó (literal):** "passa a régua de validação antes de comitar"

**O que foi feito:** régua da Creagle (`_REGUA-VALIDACAO-PRODUCAO.md`) aplicada ao protótipo, enquadrado como classe A
se fosse produção. Checklist com evidência em `docs/regua-validacao-prototipo.md`. 36 testes (eram 19), integração com
a DeepSeek simulada em 9 tipos de falha, bateria de IA real com 16 conversas (16 de 16), E2E da página, carga do lote
(9.568 tickets em 3,6 s, 309 MB), varredura de chave vazia. Pendente: homologação do Jó.

**Achados corrigidos:** pedido de dinheiro recebia pergunta de categoria (agora vai direto para pessoa); desistência
virava pergunta (destino novo "cliente desistiu"); falha da IA derrubava a conversa (agora pessoa assume); filtro de
travessão nas respostas. Erro meu: a primeira bateria testava desistência depois de a conversa já ter sido
encaminhada; roteiro corrigido. A bateria tinha passado nas checagens automáticas mesmo com o problema da pergunta
de categoria: ele só apareceu lendo as respostas uma a uma.

## Rodada 54 (2026-11-11 12:10 BRT): página no ar para homologação

**Pedido do Jó (literal):** "Sobe a página". Porta 8082 tirada do registro de portas da netcup (primeira livre, conferida com `ss`), só em 127.0.0.1, exposta por túnel efêmero do Cloudflare. `curl -sI` no link: HTTP/2 200; `/_stcore/health`: ok. Porta registrada no mesmo turno como temporária.

## Rodada 55 (2026-11-11 12:22 BRT): nome, coleta de contato e marca fora da tela

**Pedido do Jó (literal):** "inclui na conversa, pergunta pelo nome e a partir dali trata pelo nome com pacimonia.. antes de passar para um humano, pergunta cpf utilizado na compra, telefone de contato e email.. tbm tirra a palavra deepseek la de cima"

**Decisão de desenho (Claude):** CPF, telefone e e-mail não passam pela IA externa, pela regra do Jó de 2026-11-03
(dado pessoal só em IA local no Brasil). A coleta é feita pelo código, com validação (dígito verificador do CPF, DDD,
formato do e-mail), uma segunda chance para dado inválido e a opção de recusar. O nome vai à IA como [NOME] e o código
decide quando ele pode aparecer (no máximo uma vez a cada três respostas). Números e e-mails digitados no meio do
relato também são trocados por marcadores antes de ir à IA. Log com contato mascarado. A coleta vale para todo
encaminhamento a pessoas (fila, pessoa executa, triagem), não para quem desiste.

**Validação:** 64 testes (eram 36), com teste que prova que nenhum dado pessoal aparece no que vai à IA; bateria de IA
real 16 de 16; conversas lidas uma a uma. Ajuste de tom: depois do nome, "Prazer, Ana. Entendi o seu caso." antes de
pedir o CPF. Erro meu: um comando para reiniciar a página derrubou o próprio terminal (o padrão de busca do processo
casava com o comando); refeito por número de processo, página de volta no mesmo link com HTTP/2 200.

## Rodada 56 (2026-11-11 12:38 BRT): painel com ID, busca, motivo claro e fila em português

**Pedido do Jó (literal):** "no painel do atendente, cria um id de identificação da chamada, pra facilitar a busca, tbm cria um campo de busca pelo o id, no modo tira a linguagem usada e coloca atendimento por IA, os motivos precisam ficar mais claro, com menos informação técnica da ia e mais informação da chamada. atualiza isso e ja classifica as chamadas anteriores para eu trazer correções"
**Mensagem do Jó no meio do trabalho (literal):** "na fila de triagem humana trraz tudo para o portugues"

**O que foi feito:** ID sequencial ATD-xxxxx em toda chamada (`registro.py`), busca que aceita "ATD-00044", "atd44"
ou "44", horário em Brasília, origem da chamada (atendimento pela página, teste interno, teste automático) com filtro
"só atendimentos", "Atendimento por IA" no lugar do modo, e motivo escrito para o atendente (o que o cliente pediu e
por que a chamada está onde está), com a regra técnica guardada à parte. A IA passou a devolver um resumo em português
do pedido, sem dado pessoal. As 67 chamadas antigas foram reclassificadas com cópia de segurança antes: 1 atendimento
do Jó (ATD-00044, iPhone), 43 testes internos e 23 testes automáticos, pela regra de horário registrada no script. Os
200 tickets da fila de triagem foram traduzidos e guardados; a primeira tradução saiu literal demais e foi refeita
pedindo frases naturais sem fato novo; um lote voltou com número de itens errado, foi descartado e refeito.
79 testes passando (eram 64).

## Rodada 57 (2026-11-11 13:42 BRT): painel e dashboard redesenhados

**Pedido do Jó (literal):** "ainda no painel do atendente, precisamos melhorar a experencia do usuario, existe 67 chamados mas eu só consigo ver o que aconteceu com detalhes em 10. tbm não ficou claro pra que serve a fila de triagem humana: tickets reais do teste.. tbm não entenndi o pq você  colocou o botao mostra só atendimentos (sem o teste) quero conseguir analisar todas as chamadas e o painel precisa ficar intuitivo e com um visual pensando em UX.. ja no dashbord, ele tbm está bem fraquinho, precisa melhorar a experiencia dele, deixar mais intuitivo e trazer graficos e filtros para facilitar a compreesao"

**Como foi feito:** skill ui-ux-pro-max (sistema de design para painel de operação denso em dados: azul para dados,
âmbar para destaque, cor sempre com texto, ícones vetoriais no lugar de emoji, barras ordenadas com valor escrito,
filtro em toda visão). Painel: lista de todas as chamadas com seleção de linha e detalhe ao lado (conversa inteira,
motivo, contato mascarado), filtros de ID, situação, assunto e "quem gerou a chamada" com explicação, contadores por
situação. A fila de triagem saiu do painel e virou a aba "Fila do time (simulação)" do dashboard, com explicação.
Dashboard em 4 abas: Operação hoje (filtros de canal, prioridade e tipo, situação por recorte, notas), Simulação com a
IA (controle de limite que recalcula tudo, curva de encaminhamento e acerto, % por assunto), Fila do time e Chamadas
do protótipo. Conferido no navegador: o gráfico de situação por canal saiu espremido (só 2 de 4 canais com nome) e foi
corrigido. 79 testes passando.

## Rodada 58 (2026-11-11 13:45 BRT): ordem do detalhe da chamada

**Pedido do Jó (literal):** "na aba do painel coloca  a caixa da connversa em cima e a caixa com o id e motivo e dados do cliente em baixo". Ordem invertida no detalhe da chamada; título da conversa passou a trazer o ID.

## Rodada 59 (2026-11-11 14:53 BRT): correções por chamada e IA resolvendo sozinha

**Pedido do Jó (literal):** "clicou na linha, tem que mudar a conversa a lateral, mas pode manter qndo assinala tbm 
id 67 alem dos dados precisa perguntas qual é o sistema, perguntou e entedeu, vai até o final do suporte explicando pra ela e confirmando que ela conseguiu compartilhar 
id 66 qndo a pessoa fala que não sabe explicar, não use frases como: fico feliz em te audar, o foco ddeve ser na resolucao.. e as perrguntas tem que ser expecificas, como: qual é o sistema que você  precisa de ajuda? onde exatamente você  está com dificuldade? consegue me mandar um print da tela ? e vai até o final nesse caso de suporte de software 
id 63 a primeira msg veio em ingles, precisa manter tudo em portugues 
toda vez que eu entrar em uma nova conversa, puxa ela pra cima automaticamente 
id 62 alem dos dados você  tem que solicitar qual é o pedido exato que esta pedindo o reembolso 
is 61 tem que pedir o valor e qual foi o pedido que gerou a cobranca duplicada 

correige todas as outras conversas considerando esses feedbacks.. unica passagem para o time é cancelamento e reembolso o restante você  trata tudo sozinho"

**O que foi feito:** a IA passou a conduzir o suporte até o cliente confirmar que resolveu: perguntas específicas,
uma por vez (qual sistema, onde exatamente, qual mensagem aparece na tela), e solução em passos numerados com
confirmação. Só reembolso e cancelamento passam para o time; cobrança em dobro ou indevida conta como reembolso.
Antes do CPF, telefone e e-mail, o código pede o pedido exato (reembolso), o que cancelar (cancelamento) ou o valor e
o pedido (cobrança). Conversa sempre em português; o caso da chamada 63 foi refeito em português. Trava no código
para frase de cortesia vazia ("sem problema", "fico feliz em ajudar"). Cada mensagem atualiza a chamada, então o
painel mostra as em andamento. Painel: clique em qualquer célula da linha troca a conversa (a caixa de seleção
continua valendo) e a conversa abre sempre do começo, conferido no navegador. As 67 chamadas antigas ficam com a
situação "Robô anterior"; cada caso refeito aponta a chamada antiga que refaz (59 a 67 viraram 71 a 83; 44 virou 84).

**Validação:** 101 testes (eram 79). Bateria real com cliente simulado pela DeepSeek até o fim: 16 de 17. Falhou o
notebook que não liga depois de todos os testes: defeito físico, que a regra não prevê; a IA mandou a cliente abrir
atendimento na Dell e a conversa não fechou (laço de despedidas). Decisão pendente com o Jó. Na primeira rodada da
bateria saíram "Sem problema." (corrigido com a trava) e um falso alarme da checagem de dado pessoal ("e-mail" como
assunto do Outlook; checagem corrigida). Erro meu: `pkill -f` de novo derrubou o próprio terminal ao parar a
bateria; limpeza refeita em comando separado e regra gravada na memória.

**Não feito, com motivo:** print da tela. A DeepSeek não lê imagem e print pode trazer dado pessoal, que pela regra
de 2026-11-03 só vai para IA local no Brasil; a IA pede o texto da tela. As abas "Simulação com a IA" e "Fila do time"
do dashboard ainda falam de roteamento por fila, que a conversa não usa mais.

## Rodada 60 (2026-11-11 15:41 BRT): defeito de aparelho vai para a assistência técnica autorizada

**Pedido do Jó (literal):** "o caso do id 84 é caso de suporte, a instrucao esta correta mas tem que destinar ele pra uma assistencia tecnoca autorizada da empresa"

**O que foi feito:** destino novo "assistência técnica". Quando o problema é de aparelho com sinal de defeito
(bateria, aquecimento, carregamento, não liga, peça, tela) ou o cliente fala em garantia, a IA dá os passos de
verificação e o sistema encaminha o cliente à assistência técnica autorizada da empresa, mesmo que o sintoma tenha
aliviado, com o número do atendimento. O texto final é fixo: a rede autorizada não está nos dados e a IA não pode
inventar endereço nem prazo (placeholder registrado no LEIAME). A IA não manda mais o cliente para o suporte do
fabricante, o que fecha o laço de despedidas do notebook da rodada 59. Chamada refeita já sai da contagem como
"Robô anterior".

**Validação:** 105 testes. Bateria nos três casos de aparelho: na primeira passada, o notebook foi encaminhado só
com perguntas, sem nenhum passo; trava no código (só encaminha depois de ao menos um passo numerado) e nova passada,
3 de 3: iPhone ATD-00090 (refaz a 84) e notebook ATD-00088 na assistência depois dos passos, monitor ATD-00089 com
cabo solto resolvido pela IA, sem ir para a assistência. Observação para o Jó: o notebook ligou depois do reset e
mesmo assim foi para a assistência, pela mesma regra do iPhone.

## Rodada 61 (2026-11-11 17:29 BRT): pergunta de abertura mais aberta

**Pedido do Jó (literal):** "trocar essa frase  Qual é o sistema, programa ou aparelho com que você precisa de ajuda? para: como posso te ajudar hoje"

**O que foi feito:** depois do nome, a IA pergunta "Como posso te ajudar hoje?" (texto fixo em `conversa.py`). As
perguntas específicas (qual sistema, em que tela, qual mensagem) continuam valendo nas rodadas seguintes, quando o
relato vem vago. A frase antiga segue só na resposta de reserva, quando a IA não entende o relato.

**Validação:** 105 testes; página reiniciada na 8082, link do túnel respondendo 200.

## Pedido de 2026-11-11 17:34 BRT: apagar uma conversa de teste

**Pedido do Jó (literal):** "deleta a conversa id 91"

**O que foi feito:** a ATD-00091 (teste do próprio Jó, parada na pergunta do nome) foi removida de
`saida/conversas.jsonl`, com backup antes. O próximo ID parte do maior registrado, então a numeração não repete.

## Endereço fixo do protótipo (2026-11-11 19:16 BRT)

**Perguntas do Jó (literais):** "o link no claoudfire não pode cair?" / "Autorizo" / "abrre a pagiina que precisa ser feito isso e se possivel ja deixa pre prenchido pra eu só avancar" / "poss copiar o id do tunel aqui?" / "eu tenho que colocar o token no meio do comando?"

**O que foi feito:** o túnel temporário (trycloudflare) mudava de endereço a cada reinício e não tinha garantia. O
protótipo passou para `https://g4.creagle.com.br`, num túnel nomeado do Cloudflare, e a página e o túnel viraram
serviços que voltam sozinhos. Com o link público, a IA ganhou teto de gasto: 40 mil tokens por conversa e 600 mil por
dia; passou do teto, uma pessoa assume, como na IA fora do ar (2 testes novos, 107 no total).

## Régua de validação com o link público (2026-11-11 19:25 BRT)

**Perguntas do Jó (literais):** "acha valido colocar um login e senha ?" / "não precisa, passa a regua de validacao"

**Decisão:** sem login e sem aviso de dado fictício (o avaliador do G4 abre pelo PR público; senha publicada não
protege e senha à parte atrapalha a avaliação). Risco aceito: o painel mostra a todos o nome digitado por quem testou.

**O que a régua achou e foi corrigido:** (1) com várias pessoas ao mesmo tempo, o registro perdia conversas (20
simultâneas viraram 4, com erro de leitura e gasto contado pela metade): trava única de escrita e gravação atômica,
200 simultâneas sem perda; (2) texto digitado podia virar imagem externa ou link disfarçado no painel: desarmado na
exibição; (3) visitante veria traceback com caminho interno: desligado. 109 testes. Carga e estresse pelo link,
recuperação depois de derrubar página e túnel à força (7 s e 8 s), folga do host conferida. Soak de 6 h em curso.
Detalhe em `docs/regua-validacao-prototipo.md`.

## O que é homologação (2026-11-11 23:16 BRT)

**Pergunta do Jó (literal):** "o que é exatamente a homologação, é a aprovação do desenvolvimento?"

**Resposta:** sim, é o aceite do dono da demanda. A régua técnica prova que o protótipo aguenta e não quebra; a
homologação prova que ele faz o que o Jó pediu, testado por ele no link real. Sem o aceite por escrito o trabalho não
conta como pronto e não é commitado.

## Filtros do painel: reembolso e cancelamento (2026-11-11 23:39 BRT)

**Pergunta do Jó (literal):** "percebi pelos filtros que não tem nenhum case de cancelamento e reembolso mas só tem 9 resolvida pela ia, pq?"

**Dado (91 chamadas no registro):** 73 aparecem como robô anterior (gravadas antes das correções de 11/11 ou já
refeitas). Só 18 são do robô atual: 9 resolvidas pela IA, 4 aguardando decisão do time, 2 na assistência técnica,
2 desistências e 1 em atendimento. Os reembolsos e cancelamentos existem: são as 4 chamadas ATD-00071 a ATD-00074,
que aparecem como "Aguarda decisão do time", nome que não deixa claro que se trata de reembolso ou cancelamento.

**Pedido do Jó (literal, 2026-11-11 23:45 BRT):** "Sim, renomeia"

**O que foi feito:** a situação "Aguarda decisão do time" passou a se chamar "Reembolso ou cancelamento (time
decide)" no painel e no filtro (`app.py` e `registro.py`). 109 testes passando; página reiniciada e link com 200.

## Endereço da assistência técnica (2026-11-12 07:48 BRT)

**Pedido do Jó (literal):** "id 88 faltou o endeeco da assistecia que ela precisa levar"

**Dado:** o texto de encaminhamento é fixo e não tinha endereço de propósito: a base do case não traz endereço da
assistência e a IA não pode inventar. **O que foi feito:** o endereço passou a vir de configuração
(`ASSISTENCIA_ENDERECO`) e entra no fim do texto ("Leve o aparelho a: ..."); 110 testes. Falta o Jó definir o endereço.

**Pedido do Jó (literal, 2026-11-12 07:49 BRT):** "id 87 tbm precisa do endereco, o endereco da assistecia é sempre o mais proximo do endereco de cadastro da pessoa. tem que confirmar com ela se ela esta no endereco da nota/cadastro e manda o endereco da assistencia mais proximo"

**Dado:** nenhuma das bases do case tem endereço. O Dataset 1 traz nome, e-mail, idade, gênero, produto e data da
compra; o Dataset 2 só o texto do ticket. Não há cadastro com endereço nem rede de assistências: as duas precisam
ser criadas como base de demonstração. Proposta levada ao Jó antes de construir.

**Pedido do Jó (literal):** "Autorizo"

**O que foi feito (16:38 BRT):** defeito de aparelho agora pede o CPF, busca o cadastro, confirma se o cliente está no
endereço (mostra só bairro e cidade) ou pede o CEP, e indica a assistência autorizada mais perto, com endereço e
número do atendimento (`assistencias.py`, mensagens fixas, nada disso vai para a IA). Cadastro (10) e rede (9) são de
exemplo, marcados como tal no LEIAME. Mais perto = maior começo de CEP igual. O endereço configurável fixo da
primeira tentativa saiu. 118 testes. Refeitas com a DeepSeek real: ATD-00093 refaz a 87 (CPF de cadastro em
Campinas, "sim", assistência de Campinas) e ATD-00094 refaz a 88 (CPF sem cadastro, CEP 13083-970, Campinas).

## Régua da assistência mais perto (2026-11-12 16:52 BRT)

**Pedido do Jó (literal):** "passa a regua de validacao"

**Resultado:** 124 testes; E2E no link com a DeepSeek real (CPF do Rio, "não, estou em Curitiba", CEP de Curitiba,
assistência de Curitiba); bateria completa 16 de 17. Dois achados no E2E, corrigidos: a máscara do CPF aparecia
como "..003-88" no painel (asteriscos viravam formatação) e a frase "em Rio de Janeiro". Falha da bateria sem
relação com a mudança: no caso do Outlook, a IA deixou "Trabalhar Offline" para o fim (14 respostas). Detalhe em
`docs/regua-validacao-prototipo.md`, terceira passada.

## Verificações simples primeiro (2026-11-14 08:15 BRT)

**Pedido do Jó (literal):** "Sim, ajusta"

**O que foi feito:** regra nova no prompt da IA: começar pelas verificações que o cliente faz em segundos (modo
offline ou avião, internet, cabo e tomada, fechar e abrir o programa, reiniciar) e só depois as demoradas
(reinstalar, recriar perfil, arquivo de dados). Motivo: na bateria da rodada 62, o caso do Outlook levou 14
respostas e 30.385 tokens para chegar em "Trabalhar Offline". 124 testes; bateria completa rodada de novo.
**Resultado:** rodada 63 completa, 16 de 17: Outlook resolvido em 5 respostas (eram 14) e tokens médios de 5.800
para 4.424. Efeito colateral: a impressora com "Erro" na fila foi mandada à assistência sem tentar a solução de
programa; o critério da extração passou a exigir a tentativa de programa antes de tratar erro de tela como defeito.
Duas rodadas focadas: 8 de 8 no destino certo. Falso alarme "pede print" (Print Spooler) corrigido na checagem.

## Fechamento da entrega (2026-11-14 18:10 BRT)

**Pedido do Jó (literal):** "executa tudo o que falta para fechar e me manda o relatorio do passo a passo para encerrar o processo e enviar"

**O que foi feito:** abas do dashboard renomeadas para refletir a regra da rodada 59 ("Simulação com a IA" virou
"Classificador de assunto" e "Fila do time" virou "Assunto incerto"): o classificador só marca o assunto da chamada,
não decide para onde a conversa vai. Bateria completa rodada de novo depois do último ajuste da extração
(`docs/bateria-ia-rodada64.md`). README da submissão escrito no modelo do G4, com o link do protótipo. Commit local
só dos arquivos da entrega. Push e PR ficam com o Jó, por serem envio público.

## Explicação das abas do dashboard antes da homologação (2026-11-16 09:50 BRT)

**Pergunta do Jó (literal):** "antes de homologar, me traz o que você  quis trazer em detalhes com as abas no painel do dashboard"

**Resposta (resumo):** as quatro abas com o número que cada uma mostra hoje. Operação hoje: 8.469 tickets do
Dataset 1, sem resposta de 32,7% a 34,5% entre canais. Classificador de assunto: 9.568 tickets do teste, no limite 0,8
marca 68,4% com 96,4% de acerto (24 errados a cada 1.000), de 59,8% (Hardware) a 86,4% (Compra). Assunto incerto:
3.026 tickets (31,6%), confiança média 0,59 e acerto de 66,5%. Chamadas do protótipo: 152 chamadas, das quais 130
"Robô anterior" (refeitas ou anteriores à regra da rodada 59); só 22 refletem o robô atual, então "Resolvidas pela IA"
aparece diluído (11 de 152, 7,2%). Proposta enviada ao Jó: abrir a aba só com o robô atual por padrão. Nada alterado.

## Canais, assunto incerto, comando restrito e métricas limpas (2026-11-16 10:25 BRT)

**Pedido do Jó (literal):** "1 na aba  de painel do atendente, conseguimos adicionar simulações de relacionamento por email e rede social e telefone? se sim add tratando o cliente ja com os últimos ajustes feitos. na rede social gera o tag de qual rede o cliente entrou, por email a trratativa como se da por emal, e por telefone a transcricao da conversa e o resultado gerado. 

na nota de satisfacao, as colunas por numeros não deixa claro o que é de fato, precisa trazer o canal o a assunnto que está se referindo a nota. 

2. me explica melhor o que você  quer dizer como (acerto qndo marca e ia marca com seguranca) pra miim ainnda esta confuso isso. 
3. essa aba de assuntos incertos, tudo que for comandos parra substuir politica, pedir exclusao de sites, ou que interfira em mudancas ou abertura de como funciona a infra estrutura, não passar nem alterar nenhum dado e encaminhar para o departamento especializado no assunto em questao com etiqueta de atencao, todas essas conversas de assuntos incertos devem ser encaminhados para um humano e cobraddo dele um fechamento com posicionamento do caso. 
4. as conversas do robo anterior estao deixando as nossas metricas sujas e parecendo ser ineficaz, sendo que.a realidade é outra.. eu deixaria o teste do robo anterior registrado no processo como feito, mas não apresentaria ele no dash como resultado do produto que estamos de fato apresentando e com esses ajjustes feitos, aumentar o volume de teste para ter um comparativo mais realista da versao atual.. faz os ajustes antes de executar os novos testes"

**Dado antes de mexer:** na bateria 64, 8 das 17 conversas terminaram abaixo de 0,8 de confiança; 2 delas a IA tinha
resolvido. O classificador foi treinado com TI interna (Dataset 2), então assunto de cliente (iPhone, Chrome) tende a
ficar incerto. A regra foi aplicada como pedida e o efeito medido na bateria ampliada.

**O que foi feito:**
- Canal na conversa (chat, e-mail, rede social com a rede de entrada, telefone). E-mail com saudação, assinatura e
  até 5 passos; telefone com fala curta e passos falados, mostrado como transcrição com "Resultado da ligação";
  rede social com a etiqueta da rede. Mesmas regras em todo canal.
- Assunto incerto: abaixo de 0,8, a IA só pergunta; se esgotar 3 perguntas ou já for dar a solução, a resposta é
  descartada e uma pessoa assume (retoma o fluxo das rodadas 47 e 48).
- Comando restrito (mudar política, excluir site ou domínio, mexer em porta, firewall, servidor, DNS, VPN, acesso de
  administrador a servidor): trava por regra antes da IA externa, mais o sinal da IA como segunda camada; nada é
  executado nem repassado; vai ao departamento especializado (Segurança da informação, Web e sistemas ou
  Infraestrutura, nomes de exemplo) com etiqueta ATENÇÃO.
- Toda chamada que passa para pessoa (reembolso, cancelamento, assunto incerto, departamento, IA fora do ar) fica
  "Aguardando posicionamento" no painel, com o tempo de espera, e só fecha com texto de posicionamento.
- Chamadas de versões anteriores do robô saem do painel e do dashboard pela versão das regras (`VERSAO_ROBO`);
  continuam no registro e neste log.
- Notas de satisfação: agora por canal, prioridade, tipo ou assunto, com a média e o número de notas de cada grupo.
- Rótulos do classificador reescritos ("IA define o assunto sozinha", "Desses, assunto certo").
- Bateria ampliada: 22 casos em 4 canais (88 conversas), gasto contado à parte do teto da página.
- 146 testes (eram 124).

## Bateria ampliada e régua da versão atual (2026-11-16 11:25 BRT)

**Pedido do Jó (literal):** "me avisa quando terminar a bateria roda tbm a regua de validacao"

**Rodada 65 (88 conversas, 4 canais, 2026-11-16):** 80 de 88. Falhas lidas uma a uma: 4 do pedido de instruções
mandado ao departamento de Segurança (extração da IA, não a regra fixa), 1 monitor encaminhado à assistência no
telefone sem conferir o cabo (pergunta numerada contada como passo), e 3 expectativas ou checagens do próprio teste.
Achados fora das checagens: saudação dupla no e-mail e "mexe em a infraestrutura".

**Correções:** passo só conta quando manda o cliente fazer algo; pedido sobre a própria assistente não é comando
restrito; corpo do e-mail sem a saudação do chat; concordância da mensagem do departamento; checagem de promessa
só em afirmação. 154 testes.

**Rodada 66 (88 conversas, mesmas regras):** 86 de 88, com as 2 falhas na própria checagem (corrigida e repassada em
todas as respostas guardadas das rodadas 65 e 66, zero violação). Destinos: resolvida pela IA 22, assistência 3,
assunto incerto 19, departamento especializado 16, pessoa executa 16, cliente desistiu 8, IA atendendo 4. Média de
3.537 tokens por conversa (5.761 na rodada 64).

**Régua, quarta passada:** todos os itens verdes menos a homologação do Jó (docs/regua-validacao-prototipo.md).
Custo medido da regra do assunto incerto: nos casos de suporte a IA resolve 55% das conversas (7 de 10 casos na
rodada 64); Outlook, impressora, iPhone e Excel passam a ir para uma pessoa por causa do classificador de TI interna.

## Limite do assunto incerto para suporte (2026-11-16 11:43 BRT)

**Pergunta ao Jó:** manter o limite do assunto incerto em 0,8 também para suporte técnico, sabendo que a IA passa a
resolver 55% das conversas de suporte (22 de 40, rodada 66) e Outlook, impressora, iPhone e Excel vão para uma pessoa?

**Resposta do Jó (literal):** "Manter 0,8"

**Decisão:** limite único de 0,8 para todos os assuntos. Prioridade em segurança: assunto incerto sempre com uma
pessoa, que fecha com o posicionamento. Nada alterado no código.

## Ligação por voz no canal telefone (2026-11-16 17:34 a 18:40 BRT)

**Pergunta do Jó (literal, 17:34 BRT):** "o canal do tlefone teria que simular uma ligacao mesmo.. conseguimos?"

**Diagnóstico e proposta:** o telefone era texto digitado como transcrição. Proposta: botão Ligar, fala do cliente
pelo microfone do navegador, transcrição na própria máquina (a voz é dado pessoal e não vai à IA externa), resposta
falada por voz local. Número de telefone real (Twilio) descartado: exige conta e custo e não acrescenta para a
avaliação.

**Resposta do Jó (literal, 17:42 BRT):** "Sim, faz"

**Escolhas medidas:** faster-whisper "small" contra "base" em 5 frases do suporte: o base trocou palavras ("e-meios",
"imprimi"), o small acertou com o vocabulário do suporte. Voz da atendente: Piper pt_BR faber, local. Memória com os
dois modelos: 884 MB; teto do serviço de 768 MB para 1,5 GB.

**Bateria por voz (telefone, 22 casos por rodada):** a fala do cliente é sintetizada e passa pela mesma transcrição da
página.

| Rodada | Passou | Dados de contato aceitos | O que mudou antes |
|---|---|---|---|
| 67 | 21 de 22 | não medido; CPF, telefone e e-mail chegavam por extenso | primeira versão |
| 68 | 21 de 22 | 18 de 36 falas | ditado convertido; cliente dita dígito por dígito, com voz diferente da atendente |
| 69 | 20 de 22 | 24 de 24 | contexto da transcrição por etapa |
| 70 | 20 de 22 | 24 de 24 | muleta de fala deixa de virar nome |

As falhas das rodadas 69 e 70 vêm da transcrição ("reembolso" saiu "rainbows"; "em quantos dias" saiu "enquanto os
dias"), não das regras: os 4 comandos restritos foram ao departamento em todas as rodadas e nenhuma resposta
prometeu resultado. Limites e números na quinta passada da régua (docs/regua-validacao-prototipo.md). 191 testes.

## Ligação contínua e escuta melhor (2026-11-16 18:55 a 19:35 BRT)

**Pedido do Jó (literal, 18:55 BRT):** "tem como ddeixar mais dinamico a ligacao no sentido de manter o tempo todo
ligado a escuta e resposta sem eu ter que ficar mandando audio como whats? outro ponto precisa melhorar a escuta, não
esta entendendo o que eu estou falando, aumento o nivel de interpretacao"

**Mensagem do Jó (literal, 19:12 BRT):** "pode seguir, me avisa quando terminar"

**Diagnóstico:** a ligação de teste dele (ATD-00419) mostrou "Jó" transcrito como "Jorio" e a frase "Com problema no
___ que eu comprei" sem o aparelho. Medição em 12 falas humanas do FLEURS pt-BR: o small como estava errava 6,9% das
palavras; o medium erra 3,1%, mas leva 10 s por turno nesta CPU, e o large-v3-turbo, 11 a 15 s, porque o Whisper
sempre processa 30 s de áudio. Compilar o whisper.cpp (janela do tamanho da fala) foi bloqueado pelo ambiente.

**Feito:**
1. Ligação contínua: microfone aberto até o Desligar, detector de fala no navegador, resposta em voz e escuta de volta
   sozinha, frase de espera depois de 1,5 s, Desligar fecha a chamada.
2. Escuta: small sem filtro de silêncio e com 5 caminhos de busca (5,4% de erro, cerca de 4 s por turno), 6 threads.
3. Interpretação: na ligação por voz, a IA sabe que o texto é transcrição, entende pelo sentido ("rainbows" como
   reembolso) e pede para repetir quando não entende.

**Medido:** Chromium com microfone falso fez 3 turnos sem clique, 6,7 a 7,3 s do fim da fala à resposta. Rodada 71 por
voz: 20 de 22, dados ditados 21 de 21. 203 testes. Régua, sexta passada, verde menos a homologação.


## Saudação natural, nome da atendente, voz e frase de espera (2026-11-16 21:16 a 21:50 BRT)

**Pedido do Jó (literal, 21:16 BRT):** "eu mandei um oi tudo bem, e ele falou que ja tinha anaotado o que eu contei,
mas eu não tinha contado nada, isso quebra a experiencia e mostra que é um atendimento artificial.. o assisitente tbm
precisa de um nome, e a voz dele esta meio robotica e toda hora ele fala um instante, tem como deixar esses pontos
mais fluidos?"

**Diagnóstico:**
1. Na ligação dele (ATD-00442) "Oi, tudo bem?" virou relato: "tudo" e "bem" não estavam na lista de cortesias, então
   a frase tinha 2 palavras úteis, o mínimo de relato, e a saudação fixa dizia "Já anotei o que você contou".
2. A frase de espera tocava depois de 1,5 s, e a resposta leva de 6 a 8 s: tocava em quase toda fala.
3. Voz: o Piper só tem vozes masculinas em pt-BR (faber, cadu, edresson, jeff), e a atendente fala no feminino
   ("Obrigada"). Mexer na entonação do Piper quase não muda nada (variação de tom de 3,0 para 3,1 semitons em 5
   frases). Uma voz mais natural e feminina (Kokoro, local) exige baixar pacote e modelo, e o ambiente bloqueou:
   fica para a autorização do Jó.

**Feito:**
1. Cumprimentos ("tudo bem", "como vai", "beleza", "alô") não contam como relato. A primeira resposta responde ao
   cumprimento ("Tudo bem, sim, obrigada.") e só diz "Vou te ajudar com isso" quando há um problema contado.
2. A atendente se chama Clara (`NOME_ATENDENTE`, troca por variável de ambiente): no prompt, na saudação dos 4 canais,
   na assinatura do e-mail e ao atender a ligação ("Suporte, aqui é a Clara. Como posso te ajudar?"), sem se
   apresentar duas vezes.
3. Frase de espera só depois de 4 s, no máximo uma vez a cada 3 falas, com 3 frases mais naturais ("Hum, deixa eu
   ver aqui.", "Só um segundinho.", "Tá, já te falo.").
4. A primeira resposta devolve o "bom dia", "boa tarde" ou "boa noite" do cliente.

**Medido:** Chromium com microfone falso: "Oi, tudo bem?" recebeu "Tudo bem, sim, obrigada. Como posso te chamar?", e
a frase de espera tocou 1 vez em 3 respostas (eram 2 em 3). Rodada 72 por voz: 21 de 22 (20 na rodada 71), nenhuma
resposta com "anotei", dados ditados 21 de 21. 215 testes. Régua, sétima passada, verde menos a homologação.
Pendente do Jó: autorizar a voz Kokoro (baixar pacote e modelo) e homologar.

## Voz da atendente com o Kokoro (2026-11-16 21:47 a 22:25 BRT)

**Mensagem do Jó (literal, 21:47 BRT):** "Sim, pode baixar"

**Feito:** Kokoro instalado (pacote e modelo, fora do git), voz feminina `pf_dora` como voz da atendente e Piper de
reserva. Como o Kokoro é mais lento para gerar, a resposta toca frase a frase. Testado e descartado: cortar a
primeira frase longa na vírgula deixava um silêncio de cerca de 2,5 s no meio da frase. Corrigido no caminho:
Desligar no meio da fala deixava os trechos atrasados tocarem.

**Medido:** a transcrição erra 1,4% das palavras ditas pelo Kokoro contra 7,6% pelo Piper (pronúncia mais clara). O
custo é cerca de 1,4 s a mais por resposta (primeiro trecho em 2,0 s de mediana contra 0,6 s da resposta toda no
Piper, em 60 respostas reais). 227 testes; régua, oitava passada, verde menos a homologação.

## Sotaque, frase de espera e tempo de resposta (2026-11-16 23:08 BRT)

**Mensagem do Jó (literal, 23:08 BRT):** "melhorou, mas ela esta em portugues de portugal, tem como deixar portugues do
brasil? o só um momento ppode entrar de forma intercalada, tippo, repondeu duas sem falr na terceira fala.. ou procura
diminuir ainda mais o tempo para ela resonder"

**Causa do sotaque:** o pacote do Kokoro montava os fonemas sem juntar os sons compostos ("dj", "tch", ditongos), e a
voz pt-BR foi treinada com eles juntos. Corrigido no formato do treino, sem trocar de voz nem de modelo.

**Feito:** fonemas no formato do treino; frase de espera intercalada, duas respostas sem e a terceira com, 1 s depois
da pausa; transcrição com 1 caminho fora do ditado de dados (0,8 s mais rápida em fala longa, 5,4% contra 5,0% de
erro em 12 falas humanas).

**Medido:** E2E no Chromium com microfone falso, 4 turnos: 7,3 a 9,5 s do fim da fala à voz (eram 8,9 a 10,4 s); a
frase de espera tocou só na 3ª fala. 229 testes; régua, nona passada, verde menos a homologação. O sotaque não se mede
pela transcrição (1,5% nos dois jeitos): amostras antes e depois para o Jó ouvir.

**Mensagem do Jó (literal, 10:52 BRT), depois de ouvir as amostras:** "Ainda soa Portugal"

**Feito (2026-11-17 11:05 BRT):** testadas, sem baixar nada, as ferramentas de voz já na máquina. Chatterbox: 71 a 91
s por frase na CPU, descartado para ligação. Piper (sotaque brasileiro) com timbre feminino pelo OpenVoice: tom 174 Hz
(feminino, igual ao da voz de referência), 2,2 a 2,6 s por frase, cerca de 0,9 GB a mais, transcrição com 11,8% de
erro em 34 palavras. Amostras das 3 vozes para o Jó escolher no ouvido.

**Mensagem do Jó (literal, 11:20 BRT):** "não mudou muita coisa se a anterior tem uma performance melhor, volta pra ela"

**Decisão do Jó (11:20 BRT, confirmada na pergunta):** manter a voz Kokoro que já está no ar. A opção Piper com timbre
feminino foi descartada: o ganho no sotaque é pequeno e ela é mais lenta (2,2 a 2,6 s contra 1,7 a 1,8 s por frase) e
gasta cerca de 0,9 GB a mais. Nada mudou no serviço.

## Volta da ligação à versão anterior e régua final (2026-11-17 12:27 a 12:46 BRT)

**Mensagem do Jó (literal, 12:27 BRT):** "volta a estruta anterior da ligacao, a mulher 2 que eu tinha pedido para
regredir, essa eu testei agora e não esta boa.. depois que você  voltar para a ultima versao passa a regua de
validacao em todo o proeto e ai fechamos e liberamos a pr"

**Feito:** a ligação voltou ao código da primeira voz feminina (commit `040879e`). Saem o ajuste de fonemas, a frase
de espera fixa na 3ª fala e a transcrição com 1 caminho; volta a frase de espera depois de 4 s sem resposta. A voz
continua sendo a Kokoro `pf_dora`, agora sem o ajuste de fonemas, como era quando o Jó disse que melhorou.

**Régua, décima passada, no projeto inteiro:** 227 testes; E2E por texto e por ligação no link; carga, estresse,
segurança, recuperação e folga do host verdes; bateria repassada no chat (22 de 22) e no telefone por voz (21 de 22, a
mesma falha conhecida e segura das rodadas 71 e 72). Pendente: homologação do Jó e OK do push e do PR.

**Mensagem do Jó (literal, 12:48 BRT), depois da régua final:** "Pode fazer o push"

**Feito (12:49 BRT):** push da branch `submission/jo-rissato` para o fork. Conferido antes: o diff contra o main do
repositório da G4 só altera arquivos em `submissions/jo-rissato/` e não tem conflito. O PR é aberto pelo Jó.

**Abertura do PR (12:55 a 13:05 BRT):** o GitHub recusou o PR com "Validation failed: must be a collaborator", pelo Jó
e de novo pelo navegador com o formulário limpo. A sessão do navegador estava numa conta diferente da dona do fork.
**Mensagem do Jó (literal):** "Pode abrir a issue". Issue #251 aberta no repositório da G4 pedindo orientação.
