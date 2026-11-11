# Lead score: versão anterior (histórico)

> **ATENÇÃO: versão anterior, mantida só como registro. Está DESATUALIZADA.** Usa o FIT relativo à média do vendedor (50 + 50 × desvio ÷ destaque), que valeu até a execução 13, e números das execuções 5 a 11. Não usar como referência. A regra vigente está em [`../scoring/regra-lead-score.html`](../scoring/regra-lead-score.html), com o resumo em [`../scoring/desenho.md`](../scoring/desenho.md) e os números atuais (execução 17) em [`../scoring/validacao.md`](../scoring/validacao.md).

Trechos retirados dos documentos vigentes na ordem O-55, sem mudança de conteúdo.

## Do desenho.md

**desenho.md, FIT**

- Histórico: até a execução 13, o FIT era relativo à média de cada vendedor (50 + 50 × desvio ÷ destaque). Ver validacao.md.

**desenho.md, BONUS: janela bruta e efeito no top 5 (top 5 do FIT relativo)**

- Se a janela usasse o período bruto, sem o teste, na semana de 01/01/2018 (+10 para a empresa cujo período preferido contém a semana):

  | Recorte | Empresas na janela | Deals com +10 | Top 5 muda (contra só o histórico) | Top 5 ativos | Top 5 com 181 dias ou mais |
  |---|---|---|---|---|---|
  | Trimestre (T1) | 23 | 169 | 21 | 77,8% | 10 |
  | Semestre (S1) | 43 | 341 | 34 | 71,9% | 19 |
  | Mês no trimestre (1º) | 27 | 201 | 32 | 73,3% | 13 |

  Sem o teste, o bônus premia empresas escolhidas pelo acaso e puxa deals parados para o topo.
- Efeito no top 5 (135 deals) com a proposta: mudam 30 deals. Os deals com empresa passam de 22,2% para 38,5%, os ativos de 81,5% para 77,8%, e os de 181 dias ou mais de 9 para 6.

**desenho.md, Recálculo de domingo**

**Resultado com o FIT relativo e 30 vendedores, que embasou as decisões 47 e 49:**
- 482 dos 500 mudariam de dono, e 29 vendedores receberiam;
- ativos por vendedor passariam de 0–111 para 17–31;
- o FIT médio dos 500 iria de 49,5 para 77,8, e o dos ativos de 50,3 para 68,1;
- os leads com FIT do dono ≥ 75 entre os 500 passariam de 48 para 269;
- redistribuir todos os abertos (cenário A) trocaria o dono de 2.026 dos 2.089 deals toda semana.

**P0, só equilíbrio × travas do repasse, nos 500 de então:**

| | Só equilíbrio (decidido) | Com as travas do repasse |
|---|---|---|
| Mudam de dono | 482 | 233 |
| Sem vendedor permitido (ficam com o dono atual) | 0 | 95 |
| Ativos por vendedor | 17 a 31 | 0 a 59 |
| FIT médio dos 500 | 49,5 → 77,8 | 49,5 → 70,0 |
| Leads com FIT do dono ≥ 75 | 48 → 269 | 48 → 268 |

**desenho.md, Repasse: se valesse hoje**

- 873 leads atendiam às três condições (536 ativos), com mediana de 2 candidatos. Sem a condição (a), seriam 1.813. Exemplo: W1XRTUT2 (MG Special, Finhigh), de Versie Hillebrand (FIT 74,4) para Kami Bicknell (FIT 75,8), com nota 68,1 com Kami, acima do 5º da lista dela (60,2).

**desenho.md, Mini penalidade**

- Proposta: −2 pontos percentuais na conversão usada no roteamento por lead perdido, por 2 semanas, com no máximo −6. Exemplo: Hayden recebe com 71,8% contra 67,9% de James. Com 1 lead perdido, ainda recebe (69,8%). Com 2, o lead vai para James (67,8%).

**desenho.md, Prioridades do dia**

Com o BONUS proposto, o top 5 dos 27 vendedores com deals abertos somava 135 deals. Desses, 77,8% estão ativos, 38,5% têm empresa, 35,6% estão em Prospecting e 6 têm 181 dias ou mais. Os 3 exemplos do HTML ficavam com nota 72,8 (+10 de BONUS), 85,0 e 67,1.

## Do validacao.md

**validacao.md, tabela da execução carregada**

| Item | Valor |
|---|---|
| Execução 9 | sha256 `de9f5962d01a271fc0ddaa4728bea830f242472c0841282b1dbe851d25d59858` (redistribuição com 30 vendedores). O id 10 foi gasto pelo ensaio |
| Execução 7 | sha256 `f3aab6b5606d0cc2d1f8194e181eb79ca9e61c2f46f7031adf0af57e943e018f` (donos antes da redistribuição). Os ids 6 e 8 foram gastos pelos ensaios, que não deixaram linha |
| Execução anterior | `id = 5`, sha256 `73ce4a8934a172fe352c0bf3156d5941ae778cccf888d97c303fe899fee8aa32` (mesmas notas, texto antigo dos motivos). O id 6 foi gasto pelo ensaio, que não deixou linha |

**validacao.md, O-51**

- Saiu "50 + 50 × desvio ÷ destaque". O destaque ficou só no motivo.

### Decisão 49: os 35 vendedores na redistribuição (execução 11, versão anterior)

Com o FIT absoluto, quem não tem histórico entra com a conversão do time (60,2%), não com FIT 50. O texto abaixo é o da execução 11.

- **Regra:**
  - elegíveis = os 35 vendedores ativos do time;
  - quem não tem histórico na janela (Mei-Mei Johns, Elizabeth Anderson, Natalya Ivanova, Carol Thompson, Carl Lin) vale FIT 50 em todo lead, como os sem destaque;
  - motivo: "Vendedor sem histórico: encaixe neutro (50).";
  - limite da semana = ativos ÷ 35, arredondado para cima = 23.
  - Mesma regra no Python (`regra.py`, `redistribuir.py`) e no TS (`src/lib/score/`), com teste de paridade do plano.
- **Proteção nova:** a carga e a redistribuição param se a data de negócio do banco (`system_data_negocio()`) for diferente da data do cálculo.
- **Gravação:**
  - a 1ª tentativa caiu no meio do ensaio (conexão perdida) e não gravou nada;
  - depois: ensaio com ROLLBACK (261 de 261) e COMMIT com 261 trocas, 0 recusadas e o motivo "Redistribuição de domingo.";
  - `acao_reatribuicoes` com esse motivo: 475 → 736;
  - `core_deals`: 8.801 deals (2.089 abertos).

| | Antes (execução 9) | Depois (execução 11) |
|---|---|---|
| Trocas | — | 261 |
| Leads de cada um dos 5 sem histórico | 0 | 23 (Mei-Mei Johns, Elizabeth Anderson, Natalya Ivanova, Carol Thompson, Carl Lin) |
| Ativos por vendedor | 0 a 31 (35 vendedores) | 9 a 31 |
| FIT médio dos leads sem contato | 77,8 | 73,4 |
| Leads sem contato com FIT ≥ 75 | 265 | 235 |

- **Nas pontas:**
  - Wilburn Farren (sem destaque) fica com 9;
  - Rosalina Dieter, com 19;
  - Vicki Laflamme, Kami Bicknell e Zane Levy ficam acima de 23 (24, 25 e 31), por causa dos ativos em Engaging que não mudam.
- **Execução 11:**
  - 2.089 deals, nota de 0 a 89, 0 donos diferentes;
  - componentes 17.791, motivos 6.041 (115 com "Vendedor sem histórico");
  - top 5: 175 deals (35 vendedores), 94,9% ativos;
  - FIT ≥ 75: 479.

### Redistribuição de domingo (31/12/2017) e execução 9 (versão anterior)

Regra decidida (cenário B, só equilíbrio, decisão 47): entram só os leads abertos sem contato registrado. O limite da semana é ativos ÷ vendedores elegíveis, arredondado para cima. Os pares lead × vendedor são ordenados por FIT, do maior para o menor.

- **Scripts:**
  - `scoring/redistribuir.py` calcula o plano, só lendo o banco;
  - `scoring/aplicar_redistribuicao.py` grava pelo papel de carga, com uma chamada de `core_repassar_deal(..., 'redistribuicao', ...)` por troca (versão da migration 0033: sem as travas do repasse, recusa lead com contato).
  - O plano é refeito com o estado do banco na hora de gravar.
- **Escopo:** 499 leads sem contato. Dos 500 em Prospecting, 1 ganhou contato nos testes e ficou com o dono.
- **Elegíveis:** 30 vendedores com fechamentos na janela, inclusive Garret Kinder (35 fechados), Donn Cantrell (73) e Reed Clapper (60). Os 5 sem nenhum deal ficam fora, porque não têm FIT.
- **Gravação:**
  - ensaio com ROLLBACK: 475 de 475 sem recusa;
  - depois, COMMIT: 475 trocas, 0 recusadas, 475 linhas em `acao_reatribuicoes` com o motivo "Redistribuição de domingo." e a linha do tempo de cada lead;
  - nenhum UPDATE direto e nenhum DELETE;
  - `core_deals` continua com 8.801 deals (2.089 abertos).

| | Antes | Depois |
|---|---|---|
| Leads que mudaram de dono | — | 475 |
| Ativos por vendedor (com leads) | 6 a 111 (27 vendedores) | 11 a 31 (30 vendedores) |
| FIT médio dos leads sem contato | 49,5 | 77,8 |
| Leads sem contato com FIT ≥ 75 | 48 | 265 |

- **Nas pontas:**
  - Wilburn Farren fica com 11 ativos: sem destaque, FIT 50 para tudo, recebe o que sobra;
  - Zane Levy fica com 31: já tinha 31 ativos em Engaging, que não mudam.
- **Sem lead:** só os 5 sem nenhum deal no dataset (Mei-Mei Johns, Elizabeth Anderson, Natalya Ivanova, Carol Thompson, Carl Lin), porque não têm FIT. Garret, Donn e Reed passaram de 0 para 27 ativos.
- **Execução 9:**
  - o score foi recalculado com os donos novos;
  - 2.089 deals, nota de 0 a 89, 0 donos diferentes;
  - componentes 18.064 (menos que 18.255, porque o FIT do novo dono usa menos características com 10+ fechados);
  - motivos 6.041;
  - top 5: 150 deals (30 vendedores), 94,7% ativos, 0 com 181 dias ou mais;
  - deals com FIT ≥ 75: 509.

### Execução 7: só o texto dos motivos (versão anterior)

A 7 troca o texto dos motivos. A regra e os números são os mesmos da 5.

- **Rótulos em português, como na tela:**
  - produto X;
  - série X;
  - setor varejo, saúde e os demais traduzidos pela tabela SETORES do app;
  - empresa de receita pequena, média ou grande;
  - empresa pequena, média ou grande em funcionários;
  - empresa X;
  - sede nos EUA ou fora dos EUA.
- **Terceira pessoa:** "destaque do vendedor", "média do vendedor", "o vendedor não tem um destaque". A mesma frase serve para o vendedor e para o manager.
- **Conferência no banco, 5 × 7, deal a deal:** 2.089 de 2.089 iguais em nota, FIT, HEAT, BONUS, ação, dono, marcadores, valor e dias. Também ficam iguais os pontos dos componentes, o FIT por vendedor e os padrões de conta. Na execução ativa, 0 motivos com "você", "seu" ou "sua" e 0 com rótulo cru.
- **Testes:** dois novos em `test_regra.py` (texto dos motivos e rótulos), 13 no total, todos passando.
- **No ar:** a lista do dia de Anna Snelling segue a nota (70, 69, 67, 67, 64) e mostra o 1º motivo no texto novo.

| Antes (5) | Depois (7) |
|---|---|
| Encaixa no seu destaque: receita media (11 de 15 ganhos nos últimos 3 meses). | Encaixa no destaque do vendedor: empresa de receita média (11 de 15 ganhos nos últimos 3 meses). |
| Encaixe acima da sua média: funcionários pequena (26 de 35 ganhos nos últimos 3 meses). | Encaixe acima da média do vendedor: empresa pequena em funcionários (26 de 35 ganhos nos últimos 3 meses). |
| Encaixe acima da sua média: setor retail (10 de 13 ganhos nos últimos 3 meses). | Encaixe acima da média do vendedor: setor varejo (10 de 13 ganhos nos últimos 3 meses). |
| Encaixe acima da sua média: sede EUA (49 de 74 ganhos nos últimos 3 meses). | Encaixe acima da média do vendedor: sede nos EUA (49 de 74 ganhos nos últimos 3 meses). |
| Você não tem um destaque com casos suficientes nos últimos 3 meses: o encaixe fica neutro (50). | O vendedor não tem um destaque com casos suficientes nos últimos 3 meses: o encaixe fica neutro (50). |
| Fora do seu forte: série GTX (35 de 70 ganhos nos últimos 3 meses, abaixo da sua média). | Fora do forte do vendedor: série GTX (35 de 70 ganhos nos últimos 3 meses, abaixo da média dele). |

### Conferência contra o desenho (versão anterior, FIT relativo; dataset limpo, `python -m unittest scoring/test_regra.py`)

Os exemplos do FIT absoluto estão em [`../scoring/validacao.md`](../scoring/validacao.md).

13 testes, todos passando.

| Item | Desenho | Obtido |
|---|---|---|
| Exemplo 4ZQTMS3Z | FIT 72,6 · HEAT 40 · BONUS 10 · nota 72,8 | 72,6 · 40 · 10 · 72,8 |
| Exemplo 1HD5JJM3 | 100 · 50 · 0 · 85,0 | 100 · 50 · 0 · 85,0 |
| Exemplo F5I33E1I | 95,8 · 0 · 0 · 67,1 | 95,8 · 0 · 0 · 67,1 |
| FIT por faixa (0–20 / 20–40 / 40–50 / 50 / 50–60 / 60–75 / 75+) | 174 / 423 / 353 / 98 / 349 / 400 / 292 | igual |
| HEAT por faixa (0 / 10 / 25 / 40 / 50 / 55 / 70) | 730 / 749 / 53 / 39 / 500 / 11 / 7 | igual |
| BONUS (0 / 5 / 10) | 1.651 / 208 / 230 | igual |
| Empresas na janela de compra | 0 | 0 |
| Top 5 por vendedor | 135 deals; 77,8% ativos; 38,5% com empresa; 6 com 181 dias ou mais | igual |
| Vendedores sem destaque | Rosalina Dieter, Wilburn Farren | igual |

### Distribuições da carga (versão anterior: execução 5, FIT relativo; valores gravados, inteiros)

A distribuição do FIT absoluto está na seção da O-51.

| Nota | Deals |
|---|---|
| 0–20 | 186 |
| 21–40 | 784 |
| 41–60 | 822 |
| 61–80 | 273 |
| 81–100 | 24 |
| acima de 100 | 0 |

| FIT | Deals |
|---|---|
| 0–20 | 173 |
| 21–40 | 429 |
| 41–49 | 313 |
| 50 | 167 |
| 51–60 | 320 |
| 61–74 | 394 |
| 75 ou mais | 293 |

O 50 inclui o arredondamento de 49,5 a 50,4.

**HEAT** = 0: 730 · 10: 749 · 25: 53 · 40: 39 · 50: 500 · 55: 11 · 70: 7.

**BONUS** = 0: 1.651 · 5: 208 · 10: 230. A janela de compra vale 0 para todas as empresas, porque nenhuma passou no teste contra o calendário geral.

**Ação sugerida:** focar 798 · requalificar 951 (mais de 138 dias) · desistir 340 (mais de 276 dias, valor proposto).

**Marcadores:** esfriou 1.291 · risco_esfriar 141 · atendimento_atrasado 0. Nenhum deal aberto foi criado no CRM, então o atendimento atrasado ainda não se aplica.

Na tela, pela view `core_deals_visao`: faixa de nota alta 98, média 1.063, baixa 928.

### Top 5 por nota (versão anterior: execução 7, igual à 5)

| Vendedor | Deal | Nota | FIT | HEAT | BONUS | Produto · empresa |
|---|---|---|---|---|---|---|
| Violet Mclelland | T6MPH7JC | 89 | 97 | 70 | 0 | MG Special · sem empresa |
| | 07GUKIG3 | 84 | 97 | 55 | 0 | MG Special · sem empresa |
| | 1BW8S7JD | 80 | 97 | 40 | 0 | MG Special · sem empresa |
| | 854QZNWK | 80 | 97 | 40 | 0 | MG Special · sem empresa |
| | PQ84ANKD | 80 | 97 | 40 | 0 | MG Special · sem empresa |
| Moses Frase | 0E8D6TCQ | 85 | 100 | 50 | 0 | GTX Plus Basic · sem empresa |
| | 1HD5JJM3 | 85 | 100 | 50 | 0 | GTX Plus Basic · sem empresa |
| | 7MKYTX69 | 85 | 100 | 50 | 0 | GTX Plus Pro · sem empresa |
| | NWPSEF2I | 85 | 100 | 50 | 0 | GTX Plus Basic · sem empresa |
| | H046CU4Z | 81 | 94 | 50 | 0 | GTX Basic · sem empresa |

**validacao.md, Banco × dataset (medido na execução 5)**

- **88UBTBQ8:** criado no CRM e perdido em 31/12 (Anna Snelling, MG Special, sem empresa). Ele entra na janela de 3 meses de Anna, e por isso as notas dos 112 deals abertos dela mudam de 1 a 3 pontos em relação ao dataset. Nenhum outro vendedor muda.

**validacao.md, Banco × dataset (medido na execução 5)**

Os totais por faixa e o top 5 ficam iguais aos do dataset.

**validacao.md, Valores usados**

- **Vendedor sem destaque:** destaque a menos de 3 pontos da média dele. Com o FIT absoluto, o destaque só aparece no motivo.
