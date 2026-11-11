# Desenho do score

Status: **regra decidida pelo Leandro (decisões 28 e 29), com o FIT absoluto (O-51) e as perguntas P0 a P6 decididas (seção 4)**. A especificação vigente está no topo de [`regra-lead-score.html`](regra-lead-score.html). A seção 1 é o diagnóstico dos dados que embasou a regra; os números dela são os de `analysis/findings.md`.
Data de referência ("hoje"): **2017-12-31**, último dia com registro no dataset.
Números medidos sobre `data/raw/` com as regras de limpeza de `data/clean.py`. O script de validação vai reproduzir todos eles.

---

## 1. O que os dados mostram

### 1.1 A chance de ganhar é praticamente a mesma em todo lugar

Win rate geral: **63,2%** (4.238 Won / 6.711 fechados).

| Variável | Menor win rate | Maior win rate | Diferença |
|---|---|---|---|
| Produto (7) | 60,3% (MG Advanced) | 64,8% (MG Special) | 4,5 pts (GTK 500 tem só 25 fechados: 60%) |
| Setor (10) | 61,2% | 64,9% | 3,7 pts |
| Porte por receita (tercis) | 63,0% | 63,2% | 0,2 pt |
| Porte por funcionários (tercis) | 62,4% | 63,6% | 1,2 pt |
| Escritório regional (3) | 62,6% | 63,9% | 1,3 pt |
| Manager (6) | 62,1% | 64,4% | 2,3 pts |

- **Vendedor:** win rate vai de 55,0% a 70,4%, mas o desvio entre vendedores (3,7 pts) é o que o acaso sozinho produziria se todos tivessem a mesma taxa (3,4 pts; p95 de 4,3 pts). Só 2 dos 30 têm intervalo fora da média, e o acaso daria ~1,5.
- **Conta:** desvio de 4,8 pts contra 5,4 pts esperados só pelo acaso, ou seja, nenhum sinal.
- **Teste no tempo** (usar só o histórico anterior a cada deal, como seria na vida real): o win rate passado da conta, do vendedor e do vendedor × produto **não prevê** o resultado seguinte. Os quintis ficam todos entre 60% e 65%, sem ordem.
- **Idade do deal:** fotografando o pipeline no fim de cada mês (abr–nov/2017), deals novos e antigos ganham na mesma proporção (61%–71%, sem padrão estável).

**Conclusão:** um score de "probabilidade de fechar" montado com produto × setor × porte × vendedor ordenaria ruído. É o que uma IA faz sozinha a partir do brief, e o dado não sustenta isso.

### 1.2 O que de fato varia

**a) Valor.** O preço de tabela vai de US$ 55 (MG Special) a US$ 26.768 (GTK 500), uma diferença de 487×. O valor fechado acompanha a tabela: mediana de 99,8% do preço, 50% dos deals entre 93% e 106%.

**b) Idade do deal (dias desde o engajamento) diz se ele ainda está vivo e quando vai se decidir.** Fotografias do pipeline no fim de cada mês de abr a nov/2017 (13 mil deals-fotografia):

| Idade na fotografia | Resolveu (Won ou Lost) nos 30 dias seguintes | Nunca fechou até 31/12/2017 |
|---|---|---|
| 0–14 dias | 29% | 29% |
| 15–30 | 12% | 31% |
| 31–45 | 20% | 39% |
| 46–60 | 35% | 31% |
| 61–75 | 38% | 44% |
| **76–90** | **48%** | 43% |
| 91–105 | 32% | 66% |
| 106–120 | 20% | 80% |
| 121–138 | 3% | 97% |
| > 138 | 0% | 100% |

- Os deals perdidos morrem cedo (mediana de 14 dias até o Lost). Os ganhos fecham entre 45 e 120 dias (mediana de 57).
- **O deal mais longo que já fechou levou 138 dias.** O dataset permitiria ver ciclos de até 437 dias, então esse limite não vem do corte de datas.
- No pipeline aberto de hoje, **1.291 dos 1.589 deals em Engaging (81%) passaram de 138 dias**, ou seja, já são mais velhos que qualquer deal que fechou na história. Somam US$ 3,2 mi dos US$ 5,0 mi em aberto (preço de tabela). Desses, 340 passaram de 276 dias (o dobro do recorde).
- Por vendedor, a fatia de deals abertos acima de 138 dias vai de 38% a 88% (mediana de 71%).

**c) Conta preenchida.** **Nenhum dos 6.711 deals fechados (Won ou Lost) está sem conta.** No pipeline aberto, 1.425 dos 2.089 (68%) estão sem conta: 337 em Prospecting e 1.088 em Engaging.

**d) Fim de trimestre (contexto para o manager, fora do score).** Deals encerrados em mar/jun/set/dez ganham 80,7%. Nos outros meses, 52,3%. O volume de fechamentos é parecido em todos os meses: o time registra os ganhos no fim do trimestre e as perdas no meio.

### 1.3 Todos os atributos das 4 tabelas: o que foi testado e onde aparece

Teste de chance: a diferença entre o maior e o menor win rate dos grupos com 30 ou mais deals fechados (6.711 deals). Nenhum atributo fica de fora: o que não entra na nota aparece na tela como contexto, com o número, para o vendedor e o manager verem que foi olhado.

| Tabela | Atributo | Resultado | Veredito | Onde aparece |
|---|---|---|---|---|
| products | `product` / `sales_price` | Win 60,3%–64,8% (4,5 pts); preço de US$ 55 a US$ 26.768; valor fechado = 97%–100% da tabela (mediana por produto) | Chance geral: ruído. **Entra no FIT** (por vendedor, 3 meses). Valor: contexto (P5) | Detalhe do FIT + valor no cartão |
| products | `series` | 62,7%–63,4% (0,7 pt) | Chance geral: ruído. **Entra no FIT** | Detalhe do FIT |
| accounts | `sector` | 61,2%–64,9% (3,7 pts) | Chance geral: ruído. **Entra no FIT** | Detalhe do FIT |
| accounts | `revenue` (tercis) | 63,0%–63,2% (0,2 pt) | Chance geral: ruído. **Entra no FIT** | Detalhe do FIT |
| accounts | `employees` (tercis) | 62,4%–63,6% (1,2 pt) | Chance geral: ruído. **Entra no FIT** | Detalhe do FIT |
| accounts | `year_established` (tercis de idade) | 62,6%–64,2% (1,6 pt) | Ruído | Detalhe do deal |
| accounts | `subsidiary_of` (tem empresa-mãe) | 63,1% × 63,6% (0,6 pt) | Ruído | Detalhe do deal (grupo da conta) |
| accounts | `office_location` | 56%–75% (19 pts), mas cada país fora dos EUA é **uma conta só**; EUA 63,3% (n=5.555) × resto 62,6% (n=1.156) | Ruído (é o mesmo da conta). **Entra no FIT** como sede EUA × fora | Detalhe do FIT |
| accounts | histórico da conta | 53%–75% (22 pts), desvio 4,8 pts contra 5,4 pts do acaso; win rate passado não prevê o seguinte (quintis 60%–65%, sem ordem) | Ruído. **Entra no FIT** como empresa (só com 10+ fechados do vendedor na janela) | Detalhe do FIT |
| sales_teams | `sales_agent` | 55,0%–70,4% (15 pts), desvio 3,7 pts contra 3,4 pts do acaso; win rate passado não prevê o seguinte | Ruído | Visão do manager: win rate por vendedor com a faixa do acaso desenhada |
| sales_teams | `manager` | 62,1%–64,4% (2,3 pts) | Ruído | Filtro + visão do manager |
| sales_teams | `regional_office` | 62,6%–63,9% (1,4 pt) | Ruído | Filtro + visão do manager |
| pipeline | `account` vazia | 0 de 6.711 fechados sem conta; 68% dos abertos sem | Sem penalidade: o FIT usa só produto e série | Flag `sem_conta` + tarefa |
| pipeline | `engage_date` (idade) | Não muda a chance; muda quando o deal se decide e se ainda está vivo (tabela da seção 1.2) | **Entra no score** | Componente HEAT + alertas |
| pipeline | `deal_stage` | Prospecting não tem data de engajamento: não há como medir idade | Sem sinal | HEAT 50 declarado "sem dado de tempo" |
| pipeline | `close_date` | Fim de trimestre: 80,7% × 52,3% | Fora do score (não existe para deal aberto) | Visão do manager |
| pipeline | `close_value` | 99,8% do preço de tabela na mediana | Justifica usar o preço como valor | Valor no cartão |

---

## 2. Regra decidida (decisões 28 e 29, FIT absoluto da O-51)

A especificação vigente está no topo de [`regra-lead-score.html`](regra-lead-score.html); abaixo dela fica o histórico (versão anterior). Aqui vai só o resumo.

**NOTA = 0,70 × FIT + 0,30 × HEAT + BONUS.** FIT e HEAT vão de 0 a 100. O BONUS vai de 0 a 20 e soma por fora, então a nota vai de 0 a 120. O valor fica fora da nota e aparece só como contexto no cartão. Decisão do Leandro: "nunca se sabe o valor antes de atender". A exceção, empresa que compra muito e está no período de comprar, virou o BONUS.

### FIT (70%): conversão do vendedor no perfil do lead (FIT absoluto, O-51)
- Usa 7 características do lead: produto, série, setor, porte por receita, porte por funcionários, empresa e sede. "Tempo de venda" fica fora, porque um lead aberto ainda não tem esse dado.
- A janela são os 3 meses de fechamentos do vendedor (hoje, out–dez/2017). Recalcula todo domingo, com os 3 meses que terminam naquele domingo, para a segunda abrir com a lista priorizada. Fica fixo a semana inteira (decisão do Leandro). O HEAT continua dinâmico.
- Conversão ajustada de cada característica = (ganhos + 20 × conversão geral do vendedor) / (fechados + 20). Característica com menos de 10 fechados não entra.
- **FIT = 100 × média das conversões ajustadas do vendedor nas características do lead que contam**, de 0 a 100. Exemplo: FIT 62 = o vendedor fecha 62% dos leads com aquele perfil.
- Casos especiais:
  - **sem característica que conte:** FIT = conversão geral do vendedor;
  - **vendedor sem histórico na janela:** FIT = conversão do time na janela;
  - **lead sem empresa (68%):** usa só produto e série, sem penalidade.
- O destaque (a característica de maior conversão ajustada do vendedor) fica só como informação no motivo: "Ponto forte do vendedor: setor varejo (71%).".
- Distribuição hoje (execuções 15 e 17, mesmas notas): FIT de 47 a 77, mediana de 62. Só 38 leads ficam com FIT de 75 ou mais (30 ativos).
- Histórico: até a execução 13, o FIT era relativo à média de cada vendedor (50 + 50 × desvio ÷ destaque). Ver validacao.md.

### HEAT (30%): tempo de atendimento
- **HEAT = pontos da faixa de idade × fator de contato.**
- O lead mais novo é o mais quente: o lead novo precisa ser atendido rápido, principalmente com FIT alto, "em 0 ou 1 dia" (Leandro). São 8 faixas de dias desde a abertura, com pontos que caem a cada faixa:

  | Faixa | Pontos | Abertos hoje | Fechados com essa duração | Taxa de ganho (só referência) |
  |---|---|---|---|---|
  | ≤ 1 | 100 | 0 | 301 | 52,5% |
  | 2–7 | 85 | 0 | 1.112 | 53,8% |
  | 8–15 | 70 | 7 | 1.464 | 58,5% |
  | 16–30 | 55 | 11 | 286 | 71,3% |
  | 31–60 | 40 | 39 | 569 | 66,3% |
  | 61–90 | 25 | 53 | 1.621 | 66,5% |
  | 91–180 | 10 | 749 | 1.358 | 71,1% |
  | ≥ 181 | 0 | 730 | 0 | — |
  | Prospecting sem data | 50 (decidido) | 500 | — | — |

- Os limites são os do Leandro. O dia 16 aparecia em "8 a 16" e em "16 a 30" e ficou na faixa 16–30.

- A taxa de referência sobe com a duração (quem fecha rápido costuma ser perda rápida) e não define os pontos. Nenhum aberto de hoje tem 7 dias ou menos (o mais novo tem 9): as 2 primeiras faixas valem para leads que chegarem já no CRM.
- Os alertas do cartão não mudam os pontos: risco de esfriar de 107 a 138 dias; "esfriou" acima de 138, o deal mais longo que já fechou. O limite de ativos da semana conta só os deals em Prospecting ou com até 138 dias.
- Fator pelo último contato registrado: 0–7 dias = 1,0 · 8–14 = 0,8 · 15–30 = 0,5 · mais de 30 = 0,2. Nos deals do dataset não há ações, então o fator é 1,0.
- Replies: componente previsto, com peso 0 até haver dado.

### BONUS (0 a 20): histórico e janela de compra da empresa
- Por empresa, recalculado todo domingo junto com o FIT. Deal sem empresa (68% dos abertos): BONUS 0, declarado e sem penalidade.
- Divisão decidida (P3):
  - **(a) tamanho do histórico, 0/5/10:** terços da receita ganha. Cortes de hoje: US$ 90.110 e US$ 127.050.
  - **(b) janela de compra por calendário, 0 ou 10:** a semana cai no período preferido da empresa. Período preferido = aquele em que a empresa compra mais que o calendário geral de todas, além do acaso (permutação, corrigida para o número de empresas). Recorte proposto: semestre (P4).
- Janela por calendário, medida por empresa contra o calendário geral (2.000 permutações; correção de Bonferroni para 85 empresas, p < 0,00059):

  | Recorte | Participação geral | Teste geral (qui-quadrado; p) | Empresas com preferência (p < 0,05 sem correção) | Depois da correção |
  |---|---|---|---|---|
  | Mês do ano (mar–dez/2017) | 6,6% a 12,5% por mês | 794 contra 755 do acaso; 0,16 | 1 (o acaso daria ~4) | 0 |
  | Mês dentro do trimestre | 20,6% / 30,4% / 49,0% | 193 contra 168; 0,09 | 4 | 0 |
  | Trimestre (T1 só tem março) | 12,5% / 29,6% / 29,7% / 28,2% | 279 contra 252; 0,11 | 6 | 0 |
  | Semestre (S1 = mar–jun) | 42,1% / 57,9% | 107 contra 84; 0,037 | 6 | 0 |

  - Nenhum recorte separa empresa nenhuma do calendário geral. O semestre é o único com teste geral abaixo de 0,05, por isso foi o proposto, mas nenhuma empresa sozinha passa da correção.
  - O "período preferido" bruto (o de maior participação, sem teste) fica espalhado de forma quase igual: trimestre 23 / 21 / 21 / 20; semestre 43 / 42; mês no trimestre 27 / 29 / 29.
  - Medição anterior, por intervalo entre compras: o intervalo típico vai de 2 a 11 dias (mediana de 5), e a regularidade é igual à do acaso (CV de 0,92 contra 0,91).
  - A taxa de ganho por terço de receita é 62,8%, 61,6% e 64,5%. A parte (a) mede volume, não chance.
- **Nestes dados, a janela de compra não se distingue do acaso.** Ela fica como regra pronta para dados reais, de preferência com 2 anos ou mais de histórico, para o período se repetir. Hoje só a parte (a) pontua: 438 deals abertos com bônus (208 com +5 e 230 com +10).
- Se a janela usasse o período bruto, sem o teste, na semana de 01/01/2018 (+10 para a empresa cujo período preferido contém a semana):

  | Recorte | Empresas na janela | Deals com +10 | Top 5 muda (contra só o histórico) | Top 5 ativos | Top 5 com 181 dias ou mais |
  |---|---|---|---|---|---|
  | Trimestre (T1) | 23 | 169 | 21 | 77,8% | 10 |
  | Semestre (S1) | 43 | 341 | 34 | 71,9% | 19 |
  | Mês no trimestre (1º) | 27 | 201 | 32 | 73,3% | 13 |

  Sem o teste, o bônus premia empresas escolhidas pelo acaso e puxa deals parados para o topo.
- Efeito no top 5 (135 deals) com a proposta: mudam 30 deals. Os deals com empresa passam de 22,2% para 38,5%, os ativos de 81,5% para 77,8%, e os de 181 dias ou mais de 9 para 6.
- Frases no cartão: "Empresa entre as que mais compram: +10." · "Empresa na época de compra: +10." · "Sem empresa cadastrada: sem bônus."

### Recálculo de domingo: distribuição equilibrada (sem teto fixo)
Decisão do Leandro: "o recálculo sempre divide igual entre vendedores... calculando qual vendedor tem mais chance de fechar aquele lead... mas ponderando pela quantidade de leads de cada um".
- **Escopo (decidido, cenário B):** entram só os leads sem contato registrado. Hoje são os 500 em Prospecting, porque o engajamento já é um contato. Os deals com contato ficam com o dono e só mudam pela regra de repasse.
- **Só equilíbrio (decisão 47, P0):** a redistribuição não obedece às travas do repasse. As travas protegem o trabalho que o vendedor já fez no lead, e o lead sem contato não tem esse trabalho.
- **Método (atribuição gulosa com limite):**
  - limite da semana = leads ativos ÷ vendedores elegíveis, arredondado para cima (hoje 23, com os 35), contando os ativos que cada vendedor já tem;
  - os pares lead × vendedor são ordenados do maior FIT para o menor, e cada lead vai para o primeiro vendedor abaixo do limite;
  - lead travado pelo manager fica fora.
- **Elegíveis (decisão 49):** os 35 vendedores ativos do time. Os 5 sem histórico na janela entram com a conversão do time (60,2%) em todo lead, e o motivo diz "Vendedor sem histórico nos últimos 3 meses: o encaixe usa a conversão do time (60%).".
- A troca é gravada pela função do banco `core_repassar_deal`, com origem `redistribuicao` e motivo "Redistribuição de domingo.". Essa origem não passa pelas travas do repasse (migração 0033).
- **Rodada forçada corrigida (O-45):** 35 elegíveis, limite 23, 257 trocas, execução 13. Foi calculada com o FIT relativo, antes da O-51.
- **Com o FIT absoluto:** sobre a foto de entrada, o plano de domingo moveria 375 leads com os 35 vendedores. Esse plano não foi aplicado: as execuções 15 e 17 mantiveram os donos.

**(versão anterior) Resultado com o FIT relativo e 30 vendedores, que embasou as decisões 47 e 49:**
- 482 dos 500 mudariam de dono, e 29 vendedores receberiam;
- ativos por vendedor passariam de 0–111 para 17–31;
- o FIT médio dos 500 iria de 49,5 para 77,8, e o dos ativos de 50,3 para 68,1;
- os leads com FIT do dono ≥ 75 entre os 500 passariam de 48 para 269;
- redistribuir todos os abertos (cenário A) trocaria o dono de 2.026 dos 2.089 deals toda semana.

**(versão anterior) P0, só equilíbrio × travas do repasse, nos 500 de então:**

| | Só equilíbrio (decidido) | Com as travas do repasse |
|---|---|---|
| Mudam de dono | 482 | 233 |
| Sem vendedor permitido (ficam com o dono atual) | 0 | 95 |
| Ativos por vendedor | 17 a 31 | 0 a 59 |
| FIT médio dos 500 | 49,5 → 77,8 | 49,5 → 70,0 |
| Leads com FIT do dono ≥ 75 | 48 → 269 | 48 → 268 |

### Lead novo durante a semana
- Quem roteia é só a função do banco `core_rotear_lead`: maior FIT do vendedor no cohort do lead em `score_fit_vendedores` (hoje `produto=<produto>`), menos a penalidade ativa, com pelo menos 10 casos. Empate: menos abertos. Ninguém com casos: quem tem menos abertos.
- Com o FIT absoluto, a função continua valendo sem mudança: a comparação entre vendedores passa a ser de conversão real, e a penalidade em pontos vira pontos de conversão.
- O motor em TS não tem mais regra própria de roteamento (o `rotearLeadNovo()` saiu), para não haver duas regras.
- O lead atribuído entra no topo das Prioridades do dia do novo dono.

### Repasse (decisão do Leandro)
- **Quando:** o lead muda de faixa do HEAT sem nenhum contato registrado desde que o dono atual o recebeu.
- **Só repassa se as três condições valem para o novo vendedor:**
  - (a) o lead entra no top 5 das prioridades dele, pela nota com ele;
  - (b) o FIT dele com o lead é 75 ou mais;
  - (c) esse FIT é no máximo 3 pontos menor que o do dono atual.
- Entre vários candidatos, ganha o de maior FIT; no empate, quem tem menos ativos.
- Travas: máximo de repasses por lead em branco, sem valor decidido (P5); ao atingir o máximo, o lead vai para a fila do manager; o manager pode travar o dono.
- Registro e aviso: a linha do tempo registra de quem, para quem, quando, o motivo e os dois FITs; os dois vendedores recebem aviso.
- Os limites (top 5, FIT ≥ 75, 3 pontos) ficam como estão (decisão 51). Com o FIT absoluto, só 38 leads têm FIT ≥ 75, então o repasse fica raro.
- **(versão anterior, FIT relativo)** 873 leads atendiam às três condições (536 ativos), com mediana de 2 candidatos. Sem a condição (a), seriam 1.813. Exemplo: W1XRTUT2 (MG Special, Finhigh), de Versie Hillebrand (FIT 74,4) para Kami Bicknell (FIT 75,8), com nota 68,1 com Kami, acima do 5º da lista dela (60,2).
- Deals do dataset: não têm histórico de contato. Repasse por mudança de faixa só para leads recebidos no CRM.

### Mini penalidade para quem perde lead por repasse
- Valor em branco, sem decisão (P6). Quem aplica é o banco, no roteamento do lead novo.
- Contador "leads perdidos por falta de atendimento" na visão do manager, da semana e acumulado.
- Não mexe no FIT, no HEAT nem no BONUS dos deals do vendedor.
- **(versão anterior)** Proposta: −2 pontos percentuais na conversão usada no roteamento por lead perdido, por 2 semanas, com no máximo −6. Exemplo: Hayden recebe com 71,8% contra 67,9% de James. Com 1 lead perdido, ainda recebe (69,8%). Com 2, o lead vai para James (67,8%).

### Prioridades do dia
1. Topo, acima de tudo: lead novo (aberto há até 1 dia, sem contato registrado) com **FIT de 75 ou mais** (decisão do Leandro). Hoje 38 abertos têm FIT de 75 ou mais (30 ativos). O motivo é a velocidade de atendimento do lead novo de alto encaixe, que deve ser atendido em 0 ou 1 dia. Não há estatística para isso, porque o dataset não tem dados de contato.
   - Se esse lead passar de 1 dia sem contato, continua no topo com a marca "atendimento atrasado", na lista e na visão do manager, até o primeiro contato ou até ser repassado (decidido).
2. Depois, todos pela nota (FIT + HEAT + BONUS).
3. No empate, vem antes o de maior HEAT.
4. Os deals em risco e os esfriados aparecem com alerta.
5. A lista do dia tem 20 leads por vendedor, todos à mostra. O ✗ tira o lead da lista. O ✓ exige tipo de atividade, comentário e horário (decisão 37) e conta como contato: atualiza o último contato e o fator de contato do HEAT.

Hoje (execução 15), o top 5 dos 35 vendedores soma 175 deals, 97,7% ativos.

**(versão anterior, FIT relativo)** Com o BONUS proposto, o top 5 dos 27 vendedores com deals abertos somava 135 deals. Desses, 77,8% estão ativos, 38,5% têm empresa, 35,6% estão em Prospecting e 6 têm 181 dias ou mais. Os 3 exemplos do HTML ficavam com nota 72,8 (+10 de BONUS), 85,0 e 67,1. Com o FIT absoluto, os exemplos dos testes são 4ZQTMS3Z (FIT 63,74, nota 66,62), 1HD5JJM3 (76,58 e 68,60) e F5I33E1I (68,13 e 47,69).

### Motivos (`reasons`)
São 2 ou 3 frases montadas a partir das contas, escritas na 3ª pessoa. Exemplos:
- "O vendedor fecha 62% dos leads com este perfil. Ponto forte do vendedor: série MG (67%)."
- "Vendedor sem histórico nos últimos 3 meses: o encaixe usa a conversão do time (60%)."
- "Aberto há 120 dias: em risco de esfriar."
- "Empresa entre as que mais compram: +10."

---

## 3. Como vamos validar (`scoring/validacao.md`)

Backtest com fotografias no fim de cada mês, de abr a nov/2017. Em cada fotografia, o FIT usa só os 3 meses anteriores e o HEAT só a idade naquela data. **O resultado é publicado como sair, inclusive se o score perder.**

**Filas comparadas:** nota (FIT + HEAT + BONUS) e, à parte, só FIT + HEAT, "por valor" (preço de tabela), "mais novo primeiro" e acaso (média de 1.000 sorteios).

**Medidas** no top 5 de cada vendedor e no top 20%, com intervalo de confiança por bootstrap:
- taxa de ganho;
- deals decididos nos 30 dias seguintes;
- deals que nunca fecharam;
- valor ganho em 90 dias.

**Checagens extras:**
- **FIT sozinho:** o lead com FIT alto fechou acima da média do vendedor? A análise de dados já indica que não (o ponto forte de 3 meses acerta o mês seguinte 45,6% das vezes, contra 49% do acaso).
- **Limite:** o histórico não mede o efeito da ferramenta em levar os leads certos a quem tem o ponto forte. A decisão 28 se apoia justamente nisso, e esse efeito só se mede com uso real.
- **Cada atributo da seção 1.3** contra o resultado real, regerado pelo script.
- **Prospecting (500 deals):** HEAT declarado como "sem dado de tempo".

Saída: `data/scored/deals_scored.json` + `scoring/validacao.md`.

---

## 4. Perguntas decididas

As decisões 28 e 29 substituíram as antigas D1–D4: a chance por segmento saiu, o valor saiu da nota e o tempo virou HEAT. Estão decididos:
- a janela de 3 meses e o recálculo aos domingos;
- o FIT absoluto (O-51): conversão do vendedor no perfil do lead;
- as 8 faixas de HEAT, com Prospecting sem data = 50;
- o BONUS de 0 a 20;
- FIT 75 para furar a fila;
- o atendimento atrasado fica no topo até o contato ou o repasse;
- a distribuição equilibrada sem teto fixo, só com os leads sem contato registrado (cenário B);
- o repasse só para o top 5 do novo vendedor, com FIT ≥ 75 e no máximo 3 pontos abaixo do dono;
- a lista do dia com 20 leads, todos à mostra;
- o ✓ com tipo, comentário e horário.

| | Pergunta | Decisão |
|---|---|---|
| P0 | A redistribuição de domingo obedece às travas do repasse? | Não: só equilíbrio (decisão 47) |
| — | Quem entra na redistribuição | Os 35 vendedores ativos (decisão 49) |
| P1 | Limites do roteamento e do repasse (trava de FIT para o lead novo, FIT ≥ 75, 3 pontos, top 5) | Ficam como estão (decisão 51) |
| P2 | Contrato do app | Em uso: `components` = `{ fit, heat, bonus }`, `score` de 0 a 120, detalhe do FIT, faixa de HEAT, marcas e motivos |
| P3 | Divisão do BONUS | 10 (histórico, terços da receita ganha) + 10 (janela de compra) |
| P4 | Janela de compra | Fica na regra, com teste contra o calendário geral; nestes dados vale 0 para todas as empresas |
| P5 | Máximo de repasses por lead (`max_repasses`) | Em branco, sem valor decidido |
| P6 | Penalidade de quem perde lead por repasse | Em branco, sem valor decidido |
