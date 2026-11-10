# Desenho do score

Status: **regra decidida pelo Leandro (decisões 28 e 29)**, com as perguntas da seção 4 em aberto. A seção 1 é o diagnóstico dos dados que embasou a regra.
Data de referência ("hoje"): **2017-12-31**, último dia com registro no dataset.
Números medidos sobre `data/raw/` com as regras de limpeza de `data/clean.py`. O script de validação vai reproduzir todos eles.

---

## 1. O que os dados mostram

### 1.1 A chance de ganhar é praticamente a mesma em todo lugar

Win rate geral: **63,2%** (4.238 Won / 6.711 fechados).

| Variável | Menor win rate | Maior win rate | Diferença |
|---|---|---|---|
| Produto (7) | 60,0% (GTK 500, n=25) | 64,8% (MG Special) | 4,8 pts |
| Setor (10) | 61,2% (finance) | 64,8% (marketing) | 3,6 pts |
| Porte por receita (tercis) | 63,0% | 63,2% | 0,2 pt |
| Porte por funcionários (tercis) | 62,4% | 63,6% | 1,2 pt |
| Escritório regional (3) | 62,6% | 63,9% | 1,3 pt |
| Manager (6) | 62,1% | 64,4% | 2,3 pts |

- **Vendedor:** win rate vai de 55% a 70%, mas o desvio entre vendedores (3,7 pts) é quase igual ao que o acaso sozinho produziria (3,2 pts com ~220 deals por vendedor).
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
| products | `product` / `sales_price` | Win 60,3%–64,8% (4,5 pts); preço de US$ 55 a US$ 26.768; valor fechado = 97%–100% da tabela (mediana por produto) | Chance geral: ruído. **Entra no FIT** (por vendedor, 3 meses). Valor: contexto (P6) | Detalhe do FIT + valor no cartão |
| products | `series` | 62,7%–63,4% (0,7 pt) | Chance geral: ruído. **Entra no FIT** | Detalhe do FIT |
| accounts | `sector` | 61,2%–64,8% (3,7 pts) | Chance geral: ruído. **Entra no FIT** | Detalhe do FIT |
| accounts | `revenue` (tercis) | 63,0%–63,2% (0,2 pt) | Chance geral: ruído. **Entra no FIT** | Detalhe do FIT |
| accounts | `employees` (tercis) | 62,4%–63,6% (1,2 pt) | Chance geral: ruído. **Entra no FIT** | Detalhe do FIT |
| accounts | `year_established` (tercis de idade) | 62,6%–64,2% (1,6 pt) | Ruído | Detalhe do deal |
| accounts | `subsidiary_of` (tem empresa-mãe) | 63,1% × 63,6% (0,6 pt) | Ruído | Detalhe do deal (grupo da conta) |
| accounts | `office_location` | 56%–75% (19 pts), mas cada país fora dos EUA é **uma conta só**; EUA 63,3% (n=5.555) × resto 62,6% (n=1.156) | Ruído (é o mesmo da conta). **Entra no FIT** como sede EUA × fora | Detalhe do FIT |
| accounts | histórico da conta | 53%–75% (22 pts), desvio 4,8 pts contra 5,4 pts do acaso; win rate passado não prevê o seguinte (quintis 60%–65%, sem ordem) | Ruído. **Entra no FIT** como empresa (só com 10+ fechados do vendedor na janela) | Detalhe do FIT |
| sales_teams | `sales_agent` | 55%–70% (15 pts), desvio 3,7 pts contra 3,2 pts do acaso; win rate passado não prevê o seguinte | Ruído | Visão do manager: win rate por vendedor com a faixa do acaso desenhada |
| sales_teams | `manager` | 62,1%–64,4% (2,3 pts) | Ruído | Filtro + visão do manager |
| sales_teams | `regional_office` | 62,6%–63,9% (1,4 pt) | Ruído | Filtro + visão do manager |
| pipeline | `account` vazia | 0 de 6.711 fechados sem conta; 68% dos abertos sem | Sem penalidade: o FIT usa só produto e série | Flag `sem_conta` + tarefa |
| pipeline | `engage_date` (idade) | Não muda a chance; muda quando o deal se decide e se ainda está vivo (tabela da seção 1.2) | **Entra no score** | Componente HEAT + alertas |
| pipeline | `deal_stage` | Prospecting não tem data de engajamento: não há como medir idade | Sem sinal | HEAT 50 declarado "sem dado de tempo" |
| pipeline | `close_date` | Fim de trimestre: 80,7% × 52,3% | Fora do score (não existe para deal aberto) | Visão do manager |
| pipeline | `close_value` | 99,8% do preço de tabela na mediana | Justifica usar o preço como valor | Valor no cartão |

---

## 2. Regra decidida (decisões 28 e 29)

A especificação completa, com as contas, os 3 exemplos reais e as simulações de roteamento, está em [`regra-lead-score.html`](regra-lead-score.html). Abaixo vai só o resumo.

**SCORE = 0,70 × FIT + 0,30 × HEAT** (0 a 100). O valor fica fora da nota e aparece como contexto (pergunta P6).

### FIT (70%): encaixe do lead no ponto forte do vendedor dono
- Usa 7 características do lead: produto, série, setor, porte por receita, porte por funcionários, empresa e sede. "Tempo de venda" fica fora, porque um lead aberto ainda não tem esse dado.
- A janela são os 3 meses de fechamentos do vendedor (hoje, out–dez/2017). Recalcula todo dia 1º e fica fixo até a rodada seguinte.
- Taxa encolhida de cada característica = (ganhos + 20 × taxa do vendedor) / (fechados + 20). Desvio = taxa encolhida − taxa do vendedor. Característica com menos de 10 fechados vale desvio 0 e fica fora da média.
- Destaque = a característica de maior taxa encolhida, entre as que têm 10 ou mais fechados.
- **FIT = 50 + 50 × (média dos desvios do lead) / (desvio do destaque)**, limitado entre 0 e 100.
  - 50 = na média do vendedor; 100 = tão bom quanto o destaque.
- Casos especiais:
  - **Lead sem empresa (68%):** usa só produto e série, sem penalidade.
  - **Vendedor sem destaque** (nenhuma característica com 10+ fechados, ou destaque a menos de 3 pontos da média dele): FIT 50 para todos os leads dele. Hoje são 2 vendedores, com 81 deals.
- Distribuição hoje: 15 deals em 100, 86 em 0 e 98 exatamente em 50.

### HEAT (30%): tempo de atendimento
- **HEAT = pontos da faixa de idade × fator de contato.**
- O lead mais novo é o mais quente (decisão do Leandro). São 8 faixas de dias desde a abertura, com pontos que caem a cada faixa:

  | Faixa | Pontos | Abertos hoje | Fechados com essa duração | Taxa de ganho (só referência) |
  |---|---|---|---|---|
  | < 1 | 100 | 0 | 0 | — |
  | 1–6 | 85 | 0 | 1.112 | 52,9% |
  | 7–14 | 70 | 7 | 1.694 | 57,2% |
  | 15–29 | 55 | 10 | 349 | 73,1% |
  | 30–59 | 40 | 39 | 540 | 65,6% |
  | 60–89 | 25 | 54 | 1.600 | 66,4% |
  | 90–179 | 10 | 746 | 1.416 | 71,3% |
  | ≥ 180 | 0 | 733 | 0 | — |
  | Prospecting sem data | 50 (P1) | 500 | — | — |

- A taxa de referência sobe com a duração (quem fecha rápido costuma ser perda rápida) e não define os pontos. Nenhum aberto de hoje tem menos de 7 dias: as 2 primeiras faixas valem para leads que chegarem já no CRM.
- Os alertas do cartão não mudam os pontos: risco de esfriar de 107 a 138 dias; "esfriou" acima de 138, o deal mais longo que já fechou. O teto do roteamento conta como ativos só os deals em Prospecting ou com até 138 dias.
- Fator pelo último contato registrado: 0–7 dias = 1,0 · 8–14 = 0,8 · 15–30 = 0,5 · mais de 30 = 0,2. Nos deals do dataset não há ações, então o fator é 1,0.
- Replies: componente previsto, com peso 0 até haver dado.

### Roteamento de lead novo
- Vai para o vendedor com a maior conversão no perfil do lead (taxa dele + média dos desvios nas características do lead).
- Travas:
  - teto de **40 deals ativos** (hoje 7 dos 27 passam disso);
  - pelo menos 1 característica do lead com 10+ fechados do vendedor;
  - FIT do vendedor com o lead de 50 ou mais.
- Empate: vai para quem tem menos ativos. Se ninguém passar nas travas, vai para a fila do manager.
- Reatribuição pelo manager fica registrada na linha do tempo.
- O lead atribuído entra no topo das Prioridades do dia do novo dono.

### Prioridades do dia
1. Lead novo (sem contato registrado) com FIT de 60 ou mais vem primeiro.
2. Depois, todos pelo score.
3. No empate, vem antes o de maior HEAT.
4. Os deals em risco e os esfriados aparecem com alerta.
5. A tela mostra 5 por vez, e o ✓ ou ✗ faz a lista andar (decisão 27).

Hoje, o top 5 dos 27 vendedores com deals abertos soma 135 deals. Desses, 81,5% estão ativos, 37% estão em Prospecting e 9 (6,7%) têm 180 dias ou mais. Os 3 exemplos do HTML ficam com score 62,8, 85,0 e 67,1.

### Motivos (`reasons`)
São 2 ou 3 frases montadas a partir das contas. Exemplos:
- "Encaixa no seu destaque: série MG (27 de 39 nos últimos 3 meses)."
- "Sem empresa cadastrada: o encaixe usa só o produto. Identifique a empresa."
- "Parado há 293 dias: nenhum deal fechou depois de 138. Requalifique ou encerre."

---

## 3. Como vamos validar (`scoring/validacao.md`)

Backtest com fotografias no fim de cada mês, de abr a nov/2017. Em cada fotografia, o FIT usa só os 3 meses anteriores e o HEAT só a idade naquela data. **O resultado é publicado como sair, inclusive se o score perder.**

**Filas comparadas:** score, "por valor" (preço de tabela), "mais novo primeiro" e acaso (média de 1.000 sorteios).

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

Saída: `data/scored/deals_scored.json` + `scoring/validacao.md`. Só serão gerados depois das respostas às perguntas abaixo.

---

## 4. Perguntas em aberto

As decisões 28 e 29 substituíram as antigas D1–D4: a chance por segmento saiu, o valor saiu da nota e o tempo virou HEAT. A janela de 3 meses e as 8 faixas de HEAT estão decididas. Ficam abertas:

- **P1.** Prospecting sem data no HEAT: 50, o meio da escala (proposta); 100, tratar como lead novo; ou 0, tratar como esquecido.
- **P2.** Teto de 40 ativos por vendedor.
- **P3.** Roteamento pela conversão no perfil, com a trava de FIT ≥ 50.
- **P4.** Requisito do lead novo: FIT ≥ 60.
- **P5.** Rodada do FIT todo dia 1º.
- **P6.** Valor fora da nota: só contexto no cartão ou também desempate. Hoje deals de US$ 55 ficam acima de deals de US$ 4.821.
- **P7.** Mudança do contrato:
  - `components` vira `{ fit, heat }`;
  - entram o detalhe do FIT e a faixa de HEAT.

  O contrato só muda depois do sim, com aviso antes à #1 e à #4.
