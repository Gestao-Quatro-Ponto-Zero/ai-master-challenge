# Diário de decisões — Challenge 001 (Churn)

## D1 — Decomposição antes de qualquer conclusão (2026-11-14)
- **Humano definiu:** começar pela análise do dataset e produzir um artifact visual que responda ao CEO.
- **IA decompôs:** (1) integridade e chaves; (2) checar cada uma das três afirmações (churn subiu, satisfação ok, uso cresceu) contra os dados; (3) comparar quem deu churn com quem ficou nas 5 tabelas; (4) testar causalidade e sinal (timing, comportamento pré-churn, modelo com placebo); (5) receita e lista acionável.
- **Ferramenta:** Python (pandas, scipy, scikit-learn) via `uv`, um script numerado por etapa, todas as saídas em `verification/outputs/`.

## D2 — Achado central: o "churn" não é perda de cliente
- Todas as 500 contas têm assinatura ativa em 31/12/2024. 284 das 352 contas com evento de churn abriram assinatura nova depois do evento (`04`).
- Os eventos de churn caem perto do fim de uma assinatura em 21% dos casos, contra 22% com datas sorteadas (`05`).
- Existem três definições de churn na base que não batem: 110 contas, 352 contas e 486 assinaturas (`01`).

## D3 — Nada prevê o churn
- 23 variáveis por conta: todas com AUC entre 0,45 e 0,54. Modelos com CV: 0,44 a 0,53, e o placebo dá 0,56 (`03`, `04`).
- Decisão: não apresentar "segmento em risco" com base em perfil. A lista do CS é ordenada por exposição (MRR ativo), não por risco previsto.

## D4 — IA errou, verificação corrigiu
- **IA afirmou** no gráfico do artifact: "0 contas sem assinatura em todos os trimestres". Só tinha verificado a data de 31/12/2024.
- **Como verifiquei:** `07_contas_sem_assinatura.py`, uma contagem a cada fim de trimestre.
- **Resultado:** havia no máximo 1 ex-cliente sem nenhuma assinatura num trimestre. Considerando só assinaturas pagas, até 12 contas ficaram temporariamente sem pagar, e todas voltaram.
- **Veredito:** corrigido antes de publicar. O gráfico e a legenda agora mostram os números por trimestre.

## D5 — Revisão humana da 1ª versão (contestação em 6 pontos)
- **Humano contestou:** (1) há 110 contas com `churn_flag` = TRUE, então como dizer que as 500 estão ativas? (2) o churn tem impacto financeiro real; (3) só 61 eventos são `is_reactivation`; (4) o uso não está estagnado: é retrabalho, com 14 mil erros (5,6%) e sessões acima de 50 min sugerindo fricção técnica; (5) 123 cancelamentos vêm logo depois de um upgrade, o que indica fricção pós-upgrade; (6) o CSAT de 3,98 pode ter viés, porque mais de 40% dos tickets não têm nota.
- **Como foi verificado:** `08_hipoteses_humanas.py`, com a saída em `outputs/08_hipoteses_humanas.txt`.
- **Onde o humano estava certo e a IA errou:**
  - (1) "500 de 500 ativas" usou a tabela de assinaturas como verdade. As 110 contas canceladas têm 420 assinaturas abertas antes do último evento e nunca fechadas, somando US$ 2,07 mi de MRR (20% do MRR ativo). Há duas leituras possíveis: ou o faturamento não fecha as assinaturas de quem cancelou, e nesse caso a receita está superestimada, ou o CRM marca como cancelado quem ainda paga. A IA tinha escolhido uma delas sem prova.
  - (2) Existe perda de receita real: US$ 1,18 mi de MRR em 486 assinaturas encerradas. A frase "não conversa com o faturamento" generalizou demais. O que os dados sustentam é mais estreito: a data do evento de churn não coincide com o fim das assinaturas.
  - (3) "Comprou de novo" não pode ser afirmado como fato. 86% dos eventos são seguidos de uma assinatura paga nova (mediana de 20 dias), mas isso vale igualmente com o flag de reativação ligado ou desligado (84% contra 87%). O flag e a tabela de assinaturas contam histórias diferentes.
- **Onde os dados não sustentaram a hipótese humana:**
  - (4) Os números do humano conferem (250.525 ações, 25 mil sessões, 14.107 erros, 5,63%). Mas a correlação entre erros e duração é zero (−0,001), as sessões longas têm taxa de erro MENOR (4,9% contra 6,4%), a taxa de erro fica estável entre 4,7% e 6,6% nas 40 features e no tempo, e erros e duração não diferem entre quem deu churn e quem ficou (AUC de 0,45 a 0,52).
  - (5) Os 123 eventos com `preceding_upgrade_flag` conferem. Mas um upgrade de fato registrado nos 30 dias anteriores aparece em 11,7% dos eventos, contra 14,3% com datas sorteadas. Contas com upgrade não cancelam mais (20,8% contra 23,8%), e o motivo informado não muda depois de um upgrade (p = 0,36).
  - (6) A preocupação procede como risco, mas a não resposta não se relaciona com prioridade, tempo de resolução nem churn (60% contra 58%). O viés não é detectável nas variáveis observáveis, e isso não descarta viés nas não observáveis.
- **Decisão:** revisar o artifact.

## D6 — Texto "Redirecionamento Diagnóstico" proposto pelo humano
- **Humano propôs:** descartar a hipótese de churn pós-upgrade e redirecionar o foco para dois pontos: a fricção de produto (feature 4 com 383 erros, feature 9 com 374) e o ponto cego do suporte (41,2% dos chamados sem nota, cerca de 36 h de resolução nos urgentes). Também afirmou que o upgrade indica maior engajamento.
- **Como foi verificado:** `09_checa_redirecionamento.py`.
- **Confere:** 307 contas com upgrade e 20,8% de cancelamento; 193 sem upgrade e 23,8%. 41,2% sem nota. Os números 383 e 374 batem quando se excluem as features beta (com as beta, são 418 e 404). As taxas de erro variam entre features de forma real (qui-quadrado p < 0,001), e as features 4 e 9 têm as maiores (6,6% e 6,5%). Resolução dos urgentes: 34,6 h em média.
- **Não confere:**
  - "Upgrade é indicador de engajamento": a diferença não é significativa (p = 0,44). No Enterprise, a retenção com upgrade (76,5%) fica abaixo da retenção sem upgrade (80,4%) e da média geral (78%). O upgrade é neutro.
  - "Causas de maior impacto": os erros nas features 4 e 9 não diferem entre contas canceladas e ativas (p = 0,90 e 0,86). O tempo de resolução também não prevê churn (AUC 0,50).
- **Achado novo, que surgiu da proposta:** a prioridade do chamado não muda o atendimento. A resolução fica entre 34,6 h e 37,0 h e a primeira resposta entre 81 e 95 min, em todas as prioridades (Kruskal p = 0,33).
- **Recomendação da IA:** manter o descarte do pós-upgrade. Apresentar os erros e o suporte como problemas operacionais confirmados, com dono e meta, sem chamá-los de causa do churn. A conclusão principal passa a ser "as tabelas se contradizem, e qualquer das duas leituras custa dinheiro", não mais "nenhum cliente saiu".

## D7 — Hipótese humana: maturidade das contas (Alemanha → França) e barreira de idioma
- **Humano observou:** a Alemanha tem o maior churn (32%) e é o único país com idade média acima de 12 meses (14,7). A França, outro país que não fala inglês, tem churn menor e contas jovens (9,6 meses). Daí duas hipóteses: (a) os países vão convergir para o churn alemão conforme amadurecem; (b) uma barreira de idioma no suporte eleva o churn. O humano também trouxe uma análise comparativa DE × FR que prevê um surto de não renovação anual na França.
- **Como foi verificado:** `10_pais_maturidade.py`, com a saída em `outputs/10_pais_maturidade.txt`.
- **Confere:** DE 8/25 (32%) com 14,7 meses; FR 5/22 (22,7%) com 9,6 meses; 13 das 22 contas francesas com 12 meses ou menos; 3/6 canceladas na faixa de 13 a 18 meses.
- **Não confere:**
  - O país não é significativo (qui-quadrado p = 0,66; DE × resto p = 0,22; IC95% da DE de 15% a 54%). Entre os países, idade e churn não se correlacionam (rho = −0,04).
  - Normalizado por exposição (churn por conta-mês), DE (2,3%) e FR (2,5%) ficam iguais aos EUA (2,2%). O 32% da Alemanha é tempo acumulado de exposição, não risco maior.
  - A maturidade não aumenta o risco mensal: em 2024, contas com 12+ meses cancelam 2,17%/mês contra 1,83% das mais novas (p = 0,53). Uma primeira leitura mostrava efeito, mas ele vinha das 35 contas canceladas sem data de evento, que eu tinha datado em 31/12. **IA quase errou; a checagem de sensibilidade corrigiu.**
  - Não há pico de renovação: só 6% das contas anuais canceladas saem entre 11 e 13 meses de vida (o esperado sem efeito seria 8%), e a mediana é 6,5 meses.
  - A análise colada usa a idade da conta hoje como "vida no cancelamento". As 5 francesas canceladas saíram com 12,2 / 7,7 / 9,0 / 5,7 / 2,1 meses, não "exatamente no término do contrato anual". O "pico de 50%" é 3 de 6 (IC95% de 12% a 88%).
  - Idioma: o suporte de DE/FR é igual ao dos anglófonos em resolução (35,3 h × 35,9 h), primeira resposta (88 × 89 min), CSAT (4,03 × 3,98) e escalação (4,1% × 4,8%), todos com p > 0,4. A base não tem campo de idioma.
- **Achado lateral:** contas cuja última assinatura paga é anual cancelam 25,2% contra 18,4% das mensais (p = 0,08). É fraco e fica como pista, não como conclusão.
- **Decisão:** não apresentar o país nem a maturidade como fator de churn. A previsão de surto na França sai do texto.
- **Réplica humana:** os fatos descritivos não podem ser contestados (DE > 30% e é o único país nessa faixa; FR pouco acima de 20% com contas jovens; canceladas com idade média entre 12 e 15 meses).
- **Verificado em `11_idade_canceladas.py`:** os fatos procedem. A idade média de hoje das canceladas é 12,2 meses no geral (DE 15,1; US 12,0; IN 12,2; FR 11,1; CA 10,5). Só que, no último evento de churn, essas contas tinham 8,2 meses em média (mediana 6,8; DE 11,6; FR 7,3). As canceladas são mais velhas hoje que as ativas (12,2 × 10,8 m, p = 0,06), o que é o esperado: quem existe há mais tempo teve mais tempo para cancelar.
- **Ajuste de comunicação (IA):** separar o fato (o número é verdadeiro) da inferência (o número indica uma causa ou uma tendência). A resposta anterior juntou os dois.

## D8 — Preocupação humana: não renovação dos contratos anuais
- **Humano propôs:** o risco está no vencimento. No contrato anual, que tem valor e compromisso maiores, o cliente racionaliza a renovação. Conforme os outros países amadurecerem, o sintoma da Alemanha aparece neles também.
- **Como foi verificado:** `12_renovacao.py`, com a saída em `outputs/12_renovacao.txt`.
- **O que os dados mostram:**
  - Na base, a assinatura "anual" não dura um ano. As anuais pagas encerradas duram 34 dias na mediana, e só 1% termina entre 330 e 400 dias. Não existe o momento de renovação para observar.
  - Depois que uma assinatura paga termina, a conta abre outra em até 60 dias em 77% a 88% dos casos, sem diferença entre anual e mensal nem entre com e sem auto-renew (p = 1,00). O auto-renew também não prevê churn (p = 0,49).
- **Veredito:** os dados não confirmam nem refutam a hipótese, porque a estrutura deles não contém o evento de renovação. A hipótese é boa lógica de negócio e entra como **controle preventivo**, não como achado.
- **O que o humano acrescentou:** uma ação que a análise sozinha não gerou. É um calendário de renovações: 131 contas com aniversário de contrato nos próximos 90 dias (US$ 5,7 mi de ARR), sendo 33 sem auto-renew (US$ 1,08 mi), em `outputs/12_renovacoes_90d_sem_autorenew.csv`. O aniversário supõe um ciclo de 12 meses a partir do início.
- **Detalhe:** a Alemanha tem só US$ 66 mil de ARR vencendo em 90 dias. A exposição de curto prazo está nos EUA (US$ 4,0 mi).
- **Humano pediu prova (planilha):** `outputs/13_prova_nova_assinatura.xlsx`, gerada por `13_planilha_renovacao.py`. As fórmulas são vivas (MINIFS e COUNTIFS) e os parâmetros da janela são editáveis. Uma coluna de conferência foi calculada em Python. As fórmulas foram avaliadas com a biblioteca `formulas` (LibreOffice ausente): 77,3% / 84,4% / 88,2% / 80,0%, total de 82,0% (146/178), com 0 divergências em relação ao Python.
- **IA errou na frase, e a planilha mostrou:** em 95,5% dos casos a conta **já tinha outra assinatura paga ativa** quando aquela terminou. Contando só as assinaturas que começam depois do fim (janela 0/+60), a taxa cai para 69,7%. Ou seja, "o cliente costuma abrir outra" sugeria renovação, e os dados não sustentam isso. O correto é: as contas mantêm várias assinaturas em paralelo, e o fim de uma raramente significa que o cliente parou.

## D10 — Insight humano: separar a identidade da conta da identidade da assinatura
- **Humano observou:** o `Historico_Crescimento_Churn` compara assinaturas ativas com assinaturas encerradas, e isso não mede cliente perdido. Uma conta segue ativa com mais ou menos assinaturas.
- **IA aplicou:** uma ponte de MRR por conta, trimestral, em `15_ponte_mrr_conta.py` (saída em `outputs/15_ponte_mrr_conta.txt`). Ela separa o MRR em novo, expansão, contração (a conta perde MRR mas continua) e perda total (a conta vai a zero).
- **Resultado:**
  - Pela tabela de faturamento, em 7 trimestres só 2 contas zeraram o MRR em algum fechamento de trimestre (US$ 18,5 mil), e as duas voltaram. As 500 contas terminam 2024 com MRR ativo (mediana de 8 assinaturas por conta).
  - A contração dentro das contas ativas soma US$ 258 mil de MRR. A expansão soma US$ 6,3 mi. GRR trimestral entre 95% e 100%, NRR entre 140% e 158%.
  - O US$ 1,18 mi de MRR das 486 assinaturas encerradas quase todo se compensa com assinaturas novas na mesma conta, dentro do mesmo trimestre.
- **Conclusão:** medido por conta, o faturamento não mostra perda de clientes, enquanto o CRM marca 110 contas como canceladas, todas ainda com MRR ativo (US$ 2,07 mi). Isso reforça o achado central: as tabelas se contradizem. O "churn crescente" do gráfico V2 é a contagem acumulada de linhas de assinatura encerradas, numa base de assinaturas que cresceu 7 vezes.
- **Ressalva:** um NRR de 140% é atípico para SaaS B2B e pode ser mais um traço do gerador sintético.

## D11 — Réplica humana: o churn ratio de assinaturas sobe historicamente
- **Humano afirmou:** o churn ratio sobe de forma consistente (1,6% em abr/23, 3,76% em jan/24, 5,3% em ago/24 e 10,7% em dez/24). Portanto não dá para dizer que entram assinaturas no mesmo ritmo em que saem.
- **Como foi verificado:** `16_taxa_mensal_assinaturas.py`, com a saída em `outputs/16_taxa_mensal_assinaturas.txt`.
- **Confere:** os números do humano batem exatamente (ratio = encerradas acumuladas ÷ ativas no fim do mês).
- **Ajuste de método:** o numerador é acumulado desde o início e o denominador é um retrato do mês, o que mistura períodos. A taxa mensal padrão (encerradas no mês ÷ ativas no início do mês) dá menos que o ratio, mas **sobe também**: 0,86% ao mês em 2023, 1,5% em 2024 até novembro, e depois 2,1% em outubro, 2,3% em novembro e 5,1% em dezembro. A receita mensal perdida sobe de 0,9% para 6,8% em dezembro.
- **Onde o humano estava certo e a IA errou:** o D10 juntou trimestres inteiros e escreveu "quase toda assinatura encerrada é compensada". Isso escondeu a aceleração. Em volume, as novas ainda superam as encerradas em dez/24 (953 × 193), mas a folga caiu de cerca de 20 novas por encerrada para 4,9. A tendência é o alerta.
- **Decisão:** o artifact v2 passa a mostrar a taxa mensal de assinaturas e de MRR perdido como o "churn subiu" verificado, separado do churn de contas (o CRM contra o faturamento).

## D12 — Concentração do ARR perdido em dez/2024 (trazida pelo humano, a partir do export do Gemini)
- **Humano afirmou:** o Reino Unido concentra cerca de 55% do ARR perdido, Cybersecurity cerca de 31,5% e Enterprise mais de 82% no pico de dezembro de 2024.
- **Como foi verificado:** `17_concentracao_dez24.py`, com a saída em `outputs/17_concentracao_dez24.txt`. Cada fatia do ARR perdido foi comparada com a fatia da exposição (o ARR ativo em 30/11) e com a taxa de perda dentro do grupo.
- **Confere:** Cybersecurity com 31,4% e Enterprise com 82,4% (US$ 5,68 mi de US$ 6,90 mi).
- **Não confere:** os ~55% são dos **EUA** (54,8%), não do Reino Unido (16,7%). Os EUA detêm 57,3% do ARR exposto, então perdem na proporção do tamanho.
- **Leitura contra a exposição:**
  - Enterprise detém 75% do ARR exposto e uma assinatura Enterprise vale cerca de 10 vezes uma Basic (US$ 58,5 mil × 5,6 mil). A maior parte dos 82% é peso de preço. Mesmo assim, a taxa de assinaturas perdidas difere por plano (p = 0,02): Enterprise 3,0%, Pro 2,7%, **Basic 1,4%**. É o único corte significativo.
  - Cybersecurity perde 3,5% das assinaturas contra 1,8% a 2,5% dos outros setores, mas o setor não é significativo (p = 0,23). Fica como algo a monitorar.
  - País: p = 0,56.
- **Achado novo:** das 193 assinaturas encerradas em dezembro, **103 começaram e terminaram dentro do próprio mês**. Só 90 estavam ativas em 30/11. Mais da metade do pico é de assinaturas com menos de 31 dias, o que pede checagem antes de virar narrativa.

## D13 — As 103 assinaturas que nasceram e morreram em dez/2024 (pedido do humano)
- **Como foi verificado:** `18_dez24_vida_curta.py`, com a saída em `outputs/18_dez24_vida_curta.txt`.
- **Perfil:** 103 assinaturas com mediana de 7 dias de vida, em 86 contas. 100% delas tinham outra assinatura ativa na mesma conta no dia do fim. Só 17% das contas têm churn_flag, 15% das assinaturas eram trial, e todos os planos e frequências aparecem. Nenhum perfil se destaca.
- **Mecanismo encontrado:** em todas as safras de início (jan/23 a dez/24), cerca de 10% das assinaturas aparecem encerradas até 31/12/2024, quer tenham tido 1 mês de observação, quer 23 (Spearman 0,25). A data de fim cai uniformemente entre o início e 31/12/2024: os quartis da posição são 0,24 / 0,50 / 0,75, e o KS contra a distribuição uniforme dá p = 0,30.
- **Consequência:** numa base real, uma safra de junho teria muito mais assinaturas encerradas do que uma de dezembro. Aqui são iguais. Como as assinaturas novas cresceram de 134/mês para 953/mês, os fins das safras recentes se espremem nas últimas semanas. Isso produz o pico de dezembro e boa parte da subida da taxa mensal do D11.
- **IA revisa o D11:** a aceleração da taxa mensal é compatível com um artefato de como a `end_date` foi gerada ou extraída. Não dá para tratá-la como comportamento de cliente comprovado.
- **Recomendação ao CEO:** antes de agir sobre o pico de dezembro, confirmar com o time de dados como a `end_date` é preenchida. A métrica que resiste é a probabilidade de uma assinatura terminar (cerca de 10%), e ela é estável entre as safras.

## D14 — Recomeço: camada SQL de confiança antes de qualquer análise (decisão humana)
- **Humano decidiu:** recomeçar a partir de uma base relacional validada em SQL. Ele definiu as relações (conta → assinatura → uso; conta → tickets; conta → eventos de churn) e a regra de datas: data sem hora recebe 00:00, data com hora mantém a hora.
- **IA construiu:** SQLite em duas camadas, em `solution/sql/`.
  - `raw_*`: o texto exato do CSV, com o número do registro e o SHA-256 de cada arquivo.
  - Tabelas tipadas (STRICT) com chave primária, chave estrangeira, domínios e datas no formato `YYYY-MM-DD HH:MM:SS`. Toda a transformação está em SQL legível (`02_tipagem.sql`).
  - Falha **estrutural bloqueia** a carga. Inconsistência entre campos é só **contada** em `dq_checks`, e nenhum dado é alterado.
- **Como foi verificado:** `build_db.py`, com a saída em `verification/outputs/19_camada_sql.txt`. Rodado duas vezes, com saída idêntica, e `PRAGMA integrity_check` = ok.
- **Resultado estrutural:** 0 bloqueantes.
  - 33.100 registros carregados sem perda.
  - Nenhum valor não vazio virou nulo.
  - Nenhuma data mudou de dia ou de hora (35.586 datas).
  - 0 chaves estrangeiras órfãs.
- **usage_id:** 21 ids aparecem 2 vezes, com conteúdo diferente nas duas linhas. Nenhuma linha é idêntica. Como a PK não aceita repetição, as 42 linhas ficam com a chave substituta `usage_pk` e a chave natural `(usage_id, subscription_id)`. O humano avaliou o impacto como pequeno (21 em 25 mil).
- **Inconsistências contadas, sem interpretação nesta etapa:** 20 checagens bloqueantes (todas em 0), 15 de alerta e 8 de info, todas em `19_camada_sql.txt`.
- **Correção humana:** a primeira versão desta entrada e do relatório trazia inferências sobre o que as inconsistências significam (o que é medível, o que o CRM indica, a origem das colisões de id). O humano pediu apenas checagens determinísticas nesta etapa. Os textos interpretativos saíram do SQL, do relatório e deste diário, e as contagens ficaram.
- **O banco fica fora do repositório** (6 MB, em `data/db/`) e é recriado por `build_db.py`.

## D15 — O que "FK sem órfãs" valida, e o teste de consulta multi-tabela (pergunta humana)
- **Humano perguntou:** se 0 FKs órfãs significa que toda a relação está validada, e se já dá para cruzar tabelas como numa tabela dinâmica.
- **Como foi verificado:** `20_relacoes_e_pivo.sql`, com a saída em `outputs/20_relacoes_e_pivo.txt`.
- **O que a FK valida:** a integridade referencial das 4 relações declaradas. Todo filho aponta para um pai que existe (0 órfãs, checado de novo fora da carga).
- **O que ela não valida:** a coerência de datas e de flags entre as tabelas. Essas checagens são as 15 de alerta do D14.
- **Cardinalidade medida (filhos por pai):**
  - Conta → assinaturas: de 2 a 19.
  - Assinatura → uso: de 0 a 16 (33 assinaturas sem uso).
  - Conta → tickets: de 0 a 11 (8 contas sem ticket).
  - Conta → eventos de churn: de 0 a 5 (148 contas sem evento).
- **Fato estrutural:** tickets e eventos de churn ligam só à conta, não à assinatura.
- **Armadilha documentada:** o JOIN direto de assinaturas com tickets pela conta gera 19.898 linhas e soma um MRR de 44,9 mi, contra 11,3 mi reais. Agregando cada tabela filha no grão da conta antes de juntar, todos os 7 totais batem com as tabelas de origem.

## D16 — Views da camada analítica (escopo escolhido pelo humano)
- **Humano decidiu:** criar quatro grupos de view: detalhe enriquecido, assinatura, conta e qualidade. A view mensal fica para depois, até ele definir o que é "ativa no mês".
- **IA construiu:** `solution/sql/04_views.sql`, executado pelo `build_db.py`.
  - Detalhe: `vw_uso_detalhe`, `vw_ticket_detalhe` e `vw_churn_detalhe`.
  - Agregadas: `vw_assinatura` e `vw_conta`.
  - Qualidade: `vw_dq_ocorrencias`, uma linha por ocorrência de cada uma das 24 checagens de linha.
  - Regra de construção: só junta de filho para pai, ou agrega a tabela filha no grão do pai antes de juntar.
- **Como foi verificado:** 6 checagens bloqueantes novas (V01–V06) comparam 47 medidas das views com as tabelas de origem, e todas batem. A V06 confirma que a contagem de ocorrências por checagem é igual à de `dq_checks`. Duas execuções deram saída idêntica.

## D17 — Data de corte fixada (decisão humana)
- **Humano decidiu:** a data de corte é 31/12/2024. A definição de churn fica para quando o dado aparecer na exploração, porque o humano já tinha notado nos CSVs que as três fontes de churn não coincidem.
- **IA implementou:** a tabela `parametros` no schema, com `data_corte = 2024-12-31 00:00:00`. O dia 31/12 entra inteiro na janela. Consultas leem o valor da tabela e não o repetem no SQL.
- **Correção de entendimento:** o humano associou o T06 a tickets anteriores à assinatura. O T06 é **uso** (`feature_usage`) com data fora do período da própria assinatura: 19.142 registros antes do `start_date`, 290 depois do `end_date` e 5.568 dentro. Os tickets anteriores ao cadastro da conta são o T08 (1.077).

## D18 — Qual data de referência o T06 e o T08 usam (pergunta humana)
- **Humano perguntou:** se os alertas de uso e de ticket "antes do início" comparam com o `signup_date` da conta ou com o `start_date` da assinatura.
- **Resposta:** as duas checagens usavam referências diferentes.
  - O T06 compara o uso com o período da **própria assinatura** (`start_date`/`end_date`).
  - O T08 compara o ticket com o **`signup_date` da conta**, porque ticket não tem vínculo com assinatura.
- **Matriz com as três referências (consulta ad hoc, saída abaixo):**

  | Tabela | Antes do start da própria assinatura | Antes do 1º start da conta | Antes do signup da conta |
  |---|---|---|---|
  | Uso (25.000) | 19.142 | 14.216 | 13.198 |
  | Tickets (2.000) | não se aplica | 1.170 | 1.077 |

- **Fato complementar:** a primeira assinatura de cada conta começa de 0 a 432 dias depois do `signup_date`. Em 25 contas é no mesmo dia, e em nenhuma é antes (T07 = 0).

## D19 — As datas de uso e ticket ficam destacadas, e o trabalho passa a partir do dashboard (decisão humana)
- **Humano perguntou:** se há algo errado no banco, dada a quantidade de ocorrências fora da data lógica.
- **Fatos verificados:**
  - A carga não altera datas: o E03 compara o texto do CSV com o banco e dá 0 diferenças.
  - O README do dataset (Kaggle) declara que os dados são **sintéticos** e que a lógica temporal validada é "signup ≤ subscription ≤ churn". As duas regras declaradas se confirmam no banco: T07 = 0 e T09 = 0.
  - O README não declara regra temporal para uso nem para tickets, e é exatamente aí que estão as ocorrências (T06, T08 e D18).
- **Decisão humana:** manter as ocorrências só destacadas e não tratá-las agora. Antes da análise exploratória, o humano vai desenhar o dashboard (o que é importante apresentar) e trabalhar de trás para frente: dashboard → análises → engenharia de dados.

## D20 — Churn é o que está em `churn_events` (decisão humana)
- **Humano decidiu:** ao desenhar o dashboard, fixou que churn é o que consta em `ravenstack_churn_events.csv`, para manter a consistência com o enunciado e a proposta do desafio. O `churn_flag` da conta e o `end_date`/`churn_flag` da assinatura deixam de ser fonte da definição.
- **Fatos da tabela sob essa definição (consulta ad hoc no banco):**
  - 600 eventos em 352 contas, de 2023-01-25 a 2024-12-31 (o último cai no próprio dia de corte).
  - Por ano: 2023 tem 73 eventos (64 contas) e 2024 tem 527 eventos (327 contas).
  - Eventos por conta: 177 contas com 1, 116 com 2, 47 com 3, 10 com 4 e 2 com 5.
  - `is_reactivation = 1` em 61 eventos.
  - Uma conta tem dois eventos na mesma data.
- **Consequência direta nas checagens:** as 277 contas com evento e `churn_flag = 0` (N05) entram como churn. As 35 contas com `churn_flag = 1` e sem evento (N04) ficam fora.
- **Ainda em aberto (humano):**
  - A unidade de contagem: evento ou conta.
  - O tratamento de contas com mais de um evento.
  - O denominador de uma taxa, se houver taxa.

## D21 — Contagem, repetição, "ativa no mês" e alertas (decisão humana sobre propostas da IA)
- **IA levantou os fatos antes da pergunta (consulta ad hoc):**
  - Só 6 dos 600 eventos têm `churn_date` igual a um `end_date` de assinatura da conta.
  - 545 eventos ocorrem com a conta tendo assinatura vigente na data, e 524 têm uma assinatura da conta iniciada depois do evento.
  - As 500 contas, inclusive as 352 com evento, têm ao menos uma assinatura sem `end_date`.
  - O intervalo entre eventos consecutivos da mesma conta vai de 0 a 640 dias (média de 102, em 248 pares).
- **Humano decidiu, entre opções apresentadas com uma recomendada:**
  1. **Unidade:** o número principal é o de contas com evento (352), e o volume no tempo é o de eventos (600). Os dois sempre rotulados.
  2. **Repetição:** todo evento vale. Cada evento conta no seu mês. Na contagem por conta, a conta entra uma vez em cada mês em que teve evento.
  3. **Ativa no mês:** a conta tem ao menos uma assinatura com `start_date` ≤ fim do mês e `end_date` nula ou ≥ início do mês. A base vai de 2 contas (jan/2023) a 500 (dez/2024).
  4. **Alertas:** tudo entra por padrão. Quando um alerta muda o resultado, mostram-se os dois números, com e sem os registros afetados.
- **IA implementou:** a `vw_mes` em `solution/sql/04_views.sql`, com uma linha por mês de jan/2023 a dez/2024 (parâmetros `data_inicio` e `data_corte`).
  - Colunas: contas ativas, eventos, contas com evento, contas com evento fora da base e as duas taxas.
  - Reconciliação bloqueante V07: 4 medidas, todas iguais à origem.
- **Fato que a decisão 4 já cobre:** 30 dos 547 pares conta-mês com evento são de contas sem assinatura vigente naquele mês, todos até jun/2024. Por isso a view traz `taxa_churn_contas` (todas) e `taxa_churn_contas_na_base` (só as que estão na base). Elas diferem em 14 dos 24 meses e são iguais de jul a dez/2024.

## D22 — Desenho do dashboard (humano, no whiteboard do Claude)
- **Humano desenhou:** cinco telas, uma por pergunta, com os blocos B1.0 a B5.4. Cada bloco traz a pergunta, o nível do dado, o visual, o limite e a origem da ideia. A imagem está em `process-log/dashboard/desenho-dashboard-v1.png`.
  - Tela 1: as três afirmações.
  - Tela 2: as causas.
  - Tela 3: segmentos e contas em risco.
  - Tela 4: ações.
  - Tela 5: a base e a confiança nos números.
- **Decisões novas no desenho:**
  - D1b: MRR e ARR vêm de `mrr_amount` e `arr_amount`.
  - D1c: as 61 reativações entram.
- **IA conferiu no banco os números citados no desenho, e todos batem:**
  - 352 contas com evento, 110 com `churn_flag` e 312 com assinatura encerrada (486 assinaturas).
  - As três fontes coincidem em 50 contas, e 50 contas não têm nenhum sinal.
  - O `churn_flag` da assinatura é igual a ter `end_date` nas 5.000 assinaturas.
- **Lacuna apontada pela IA na D1b:** o evento de churn liga só à conta. Na data do evento, 478 dos 600 eventos têm 2 ou mais assinaturas vigentes na conta, e 55 não têm nenhuma. Falta a regra de qual `mrr_amount` atribuir a cada evento.

## D23 — Cada número fica no identificador ao qual pertence (decisão humana)
- **Humano decidiu, em resposta à lacuna da D22:** as análises ficam sempre separadas no dashboard. Toda demonstração filtra primeiro pelos dois identificadores principais, `account_id` e `subscription_id`. Cada número aparece no identificador ao qual está atrelado.
- **Consequência:** nenhum `mrr_amount` é atribuído a evento de churn, e a regra da lacuna da D22 deixa de ser necessária.
  - Evento de churn, ticket e seus campos ficam no nível de **conta**.
  - MRR, ARR, plano, cobrança, trial e uso ficam no nível de **assinatura**.
- **Leitura da IA, confirmada pelo humano:** na tela de conta, entram os totais das assinaturas da conta, como a soma de MRR da `vw_conta`, porque o vínculo assinatura → conta é direto (N:1). Nas palavras do humano, o MRR e o ARR se identificam pela conexão entre o ID da conta e o ID da assinatura. Os blocos B1.1, B2.2 e B3.1 ("MRR perdido" e "pesado por MRR") passam a usar esse total por conta, sem data de evento.

## D24 — Features por identificador (lista do humano no desenho, implementação da IA)
- **IA implementou em `04_views.sql`:** as features da tabela "De trás para frente" do desenho, cada uma na view do seu identificador.
- **`vw_assinatura`, uma linha por `subscription_id`:**
  - MRR e ARR por seat.
  - Taxa de erro (erros / `usage_count`). Fica nula nas 33 assinaturas sem uso.
  - `conta_churn_rotulo`: atributo da conta, só para filtro.
- **`vw_conta`, uma linha por `account_id`:**
  - Rótulo de churn (`churn_rotulo`, que é ter evento, D20), com `churn_sinal_flag_conta` e `churn_sinal_fim_assinatura` ao lado, só para reconciliar.
  - Seats, MRR e ARR das assinaturas sem `end_date`, e MRR e ARR por seat.
  - Registros beta, recursos distintos e taxa de erro.
  - Taxa de escalação, média de satisfação, tickets sem nota e médias de resolução e de primeira resposta.
- **Como foi verificado:**
  - Nova reconciliação bloqueante V08, com 10 medidas, todas iguais à origem.
  - V01 a V07 continuam em 0.
  - Fora das duas views alteradas, o relatório de carga ficou idêntico ao anterior.

## D25 — A exploração e a interface nascem dentro do Veta (decisão humana)
- **Humano propôs:** fazer a análise exploratória já dentro da estrutura do Veta, um projeto anterior dele: um analista em chat em que todo número vem de uma consulta SQL que se pode inspecionar. Assim a interface visual vai sendo adaptada ao desafio enquanto os dados são explorados.
- **IA avaliou:** o princípio do Veta é o mesmo da camada SQL. O modelo só narra, os números vêm de SQL e o banco abre somente para leitura. Três pontos estão acoplados ao dataset original:
  - O esquema enviado ao agente lista só tabelas, sem as views.
  - O relógio de dados ancora numa tabela de uso diário.
  - As métricas, o feed e o resumo executivo são do dataset original.
- **Humano decidiu:**
  - **Origem do código:** o Veta é trazido para dentro do diretório do desafio como exemplo, sem ser branch do programa original. O código fica em `solution/app`, sem o histórico git.
  - **Modelo:** fica o DeepSeek. O agent loop do Veta segue o padrão da OpenAI e não o da Anthropic, então trocar de modelo exigiria refatorar. O DeepSeek também tem custo menor. (Correção humana: a IA tinha dito que bastava trocar o endpoint.)
  - **Ambiente:** todo o desenvolvimento roda localmente.
  - **Deploy:** depois, na Vercel ou na Railway, com autenticação e um usuário e senha padrão informados ao avaliador.
- **IA copiou:** todo o código e a documentação para `solution/app`, menos quatro itens:
  - O `.git`.
  - Os arquivos `.env`.
  - A base comprimida do dataset do desafio anterior (`data/seed/aurelia.sqlite.gz`, 17 MB), que é dado de outro concurso e será substituída pela RavenStack.
  - O vídeo de demonstração daquele desafio (`docs/demo/`).
  - Resultado: 13 MB.

## D26 — Refatoração do Veta para a RavenStack, fase 1 (humano decidiu refatorar, IA implementou)
- **Humano decidiu:**
  - Refatorar o Veta para absorver a estrutura da RavenStack, sem reescrever o sistema.
  - Os arquivos `.env` foram escritos do zero, sem nada do dataset anterior. (Correção humana: a IA tinha só remendado os comentários antigos.)
- **IA implementou:**
  - **Banco:** o app abre o `ravenstack.db` só para leitura.
  - **Esquema:** o agente recebe tabelas e views, sem as cópias `raw_*`.
  - **Relógio:** lido da tabela `parametros`, de 2023-01-01 a 2024-12-31.
  - **Métricas:** 8 métricas, cada uma ligada a um bloco do desenho.
  - **Analista:** o prompt traz as definições D20 a D24 e responde em português.
  - **Tela inicial:** 4 indicadores descritivos e o churn por mês.
  - **Painel desligado:** o feed de "histórias descobertas" pelo modelo, para que nenhuma conclusão apareça antes da análise.
- **Como foi verificado:**
  - A checagem de tipos passou.
  - As 18 checagens do painel batem com o banco: 500 contas, 352 com evento, 600 eventos e taxa de 19,2% em dez/2024.
  - A tela inicial abre com o usuário do avaliador.
  - Nenhuma menção à Aurelia ficou no código do app.
- **Onde a IA (o modelo do app) errou, e a correção:** ao perguntar quantas contas tiveram evento em 2024, o DeepSeek respondeu 326 contas e 522 eventos. O certo é 327 e 527.
  - **Causa 1:** filtrou com `churn_date <= '2024-12-31'`. Como as datas têm hora, a comparação de texto exclui os 5 eventos de `2024-12-31 00:00:00`.
  - **Causa 2:** somou os meses de cabeça e afirmou 522.
  - **Correção:** duas regras no prompt. Datas se filtram por `substr` ou por `<` no dia seguinte. Nenhuma conta é feita no texto, toda soma ou percentual vem do SQL.
  - **Reteste:** 527 eventos e 327 contas, com as contagens feitas no SQL.

## D27 — Navegação, filtro de plano e MRR perdido na Tela 1 (humano escolheu entre propostas da IA)
- **Navegação:** as cinco telas do desenho ficam no menu lateral, uma página cada. O chat do analista abre num painel ao lado, em qualquer tela. Assim o avaliador pergunta sem sair da tela que está vendo.
- **Filtro de plano:** segue a D23. Números de conta (churn, tickets) usam o plano da conta. Números de assinatura (MRR, uso) usam o plano da assinatura. A IA tinha apontado que os dois planos diferem em 3.365 das 5.000 assinaturas (alerta N07).
- **MRR perdido no B1.1:** aparece como número ao lado da linha mensal, sem série no tempo. É a soma do MRR das assinaturas das contas com evento, como total da conta e sem data de evento (D23). Sem filtro, são 352 contas e US$ 7.990.982 (consulta na `vw_conta`).
- **Leitura da IA sobre os alertas da Tela 1:** nenhum alerta de linha muda o churn por evento. Os alertas da reconciliação de `churn_flag` (N04 a N06) não entram na D20. Mudam o resultado o T08 no B1.2 (1.077 tickets antes do cadastro) e o T06 e o E13 no B1.3 (19.432 e 21 registros de uso). Por isso, esses dois blocos mostram os dois números (D21).

## D28 — Visão geral executiva como primeira tela (humano decidiu, IA propôs duas definições)
- **Humano decidiu:**
  - Os cartões do B1.0 (as três afirmações com veredito pendente) saem. Só ocupavam espaço e não traziam valor ao usuário.
  - A primeira tela vira uma visão geral executiva mais simples. No topo ficam os números gerais: contas, assinaturas, contas com churn, churn rate, receita e receita em risco.
  - Abaixo vêm os gráficos de alto nível: receita por indústria, por plano e por país, os principais motivos de churn e o churn por indústria.
  - Nessa tela, gráficos de barra, coluna ou donut, porque as linhas estavam pequenas demais.
- **IA implementou:**
  - **Visão geral em `/`:** 6 números e 8 gráficos, todos com os filtros globais e com o SQL de cada um à mão.
  - **Gráficos sugeridos pela IA:** contas com churn por mês (colunas), churn por plano e churn por origem.
  - **Tela das afirmações:** os blocos B1.1 a B1.3 passaram para `/tela/1`, sem o B1.0.
- **Definições propostas pela IA, à espera da confirmação do humano:**
  - **Churn rate:** é a taxa do último mês do período (dez/2024: 19,2%), contando as contas com evento sobre as contas ativas no mês, pela regra da `vw_mes`. A nota do número traz a média mensal de 2024, de 10,5%. A alternativa seria a fatia das contas com evento em 24 meses (352 de 500, ou 70,4%), mas ela já aparece no número de contas com churn.
  - **Receita em risco:** é o MRR ativo das contas que já tiveram evento de churn, US$ 7.139.868, ou 70,3% do MRR ativo, em 352 contas. É um fato descritivo, não um modelo de risco. Todas as 352 contas com evento ainda têm assinatura ativa. O risco por modelo (B3.4) pode substituir esse número depois.
- **Como foi verificado (D28):** 15 checagens contra consultas independentes (`visao-test`), todas iguais: 500 contas, 5.000 assinaturas, 352 contas com churn, 600 eventos, 19,2% em dez/2024 e o MRR ativo. As quebras por motivo, indústria, plano e país somam o total, e o filtro FinTech dá 112 contas e 76 com churn.

## D29 — Todo número diz de qual tabela vem (decisão humana)
- **Humano observou:** "352 contas com churn" confunde. Na tabela `accounts`, o `churn_flag` marca 110 contas, e os 352 vêm de `churn_events`.
- **Humano decidiu:** todo o material apresentado separa os dados por origem. Cada número diz se representa contas (`accounts`), eventos de churn (`churn_events`) ou assinaturas (`subscriptions`).
- **IA implementou:**
  - **Visão geral:** os números do topo foram agrupados por tabela, em três cartões.
    - `accounts`, com 500 linhas: 500 contas e 110 com `churn_flag = 1`.
    - `churn_events`, com 600 linhas: 600 eventos, 352 contas distintas com evento e o churn rate.
    - `subscriptions`, com 5.000 linhas: 5.000 assinaturas, 486 com `end_date` em 312 contas, o MRR ativo e a receita em risco.
  - **Números que cruzam tabelas:** levam a etiqueta das duas. O churn rate é `churn_events` sobre `subscriptions` vigentes, e a receita em risco é `subscriptions` de contas com `churn_events`.
  - **Gráficos e blocos:** cada um tem no cabeçalho uma etiqueta colorida com a tabela de origem. Os títulos agora dizem a unidade, como "Contas com evento, por indústria" e "MRR ativo por país".
  - **Analista (chat):** ganhou no prompt a regra de sempre nomear a tabela de origem, com os três números de referência.
- **Como foi verificado:** o `visao-test` ganhou duas checagens, 110 com `accounts.churn_flag` e 486 assinaturas com `end_date` em 312 contas. Todas passam, e a captura da tela foi conferida.

## D30 — Cara de ferramenta executiva, e crescimento mês a mês no lugar do churn por mês (decisão humana)
- **Humano observou:** o dashboard vai para a mão de um executivo e estava com cara de ferramenta de desenvolvedor: nomes de tabela, `churn_flag = 1`, `end_date`, códigos de decisão (D20) na tela. E o gráfico de churn por mês não diz muito sozinho: se a base cresce, o churn também cresce.
- **Humano decidiu:**
  - Menos é mais. Rótulos simples ("Total de contas", "Contas com churn" para os 110 do `churn_flag`, "Total de assinaturas" sem nota), sem taxonomia de tabelas e views na tela.
  - Trocar o gráfico de churn por mês por um gráfico de linhas que compara, mês a mês, quanto a base de contas cresceu e quanto o churn cresceu, sempre em % sobre o mês anterior.
- **IA implementou:**
  - **Números do topo:** três grupos com títulos simples (Contas, Eventos de churn, Assinaturas e receita), sem etiquetas de tabela e com no máximo uma nota curta por número. A separação de D29 continua, agora dita em palavras: "Contas com churn" (110) fica em Contas; "Contas com evento de churn" (352) fica em Eventos de churn.
  - **Etiquetas de tabela:** saíram de todos os gráficos e blocos. A origem continua no SQL de cada gráfico, atrás do botão SQL.
  - **Códigos na tela:** saíram os (D20), (D27), T06, T08 e E13 dos textos visíveis da visão geral, da tela 1, do filtro e do chat.
  - **Gráfico novo:** "Crescimento mês a mês: contas × churn". Contas = contas ativas no mês (assinatura vigente, D21). Churn = contas com evento de churn no mês. A variação % vem do SQL (`lag`). O gráfico começa em abr/2023, o primeiro mês cujo mês anterior teve pelo menos 5 contas com evento: antes disso a base era tão pequena que 1 para 5 contas virava +400%.
- **Nota da IA:** no exemplo do humano, 5 para 10 churns é +100%, não +50%. O gráfico usa a conta correta.
- **Como foi verificado:** o `visao-test` ganhou três checagens (começa em 2023-04; dez/2024 com contas +5,3% e churn +60%; fev/2024 com churn −44,4%). Todos os testes passam, e a captura da tela foi conferida.
- **Complemento (humano):** incluir uma linha de tendência linear em cada série, da mesma cor e pontilhada. **IA implementou** a regressão por mínimos quadrados no próprio SQL do gráfico; o `visao-test` confere contra uma regressão independente em TypeScript. **Nota da IA:** como o crescimento da base desacelera (de +71% para +5%), a reta das contas termina em −3,1% em dez/2024, embora o crescimento real nunca tenha ficado negativo. A reta do churn sobe de +12,3% para +30,3%.

## D31 — Receita nova × receita perdida, com previsão do cruzamento (decisão humana; definições propostas pela IA)
- **Humano decidiu:** mover "Eventos de churn por motivo" para baixo e pôr no lugar um gráfico de linhas, mês a mês, com o incremento de receita das contas novas e a perda de receita pelo churn. O CEO precisa ver a distância entre as linhas e prever em quanto tempo a aquisição é neutralizada pela perda, se o cenário continuar igual.
- **IA propôs as definições (a confirmar pelo humano):**
  - **Receita nova:** MRR das assinaturas que a conta começa no mês da sua primeira assinatura (cliente novo). Não conta upgrades nem novas assinaturas de quem já era cliente.
  - **Receita perdida:** MRR das assinaturas com `end_date` no mês, a receita que de fato parou (nível de assinatura, D23). A alternativa pelo evento, o MRR das assinaturas vigentes da conta na data do evento em `churn_events`, foi descartada: as contas seguem com assinaturas ativas depois do evento (é o que infla a receita em risco), e ela daria US$ 1,88 mi só em dez/2024.
  - **Previsão:** reta de mínimos quadrados sobre os 12 meses de 2024, projetada até as retas se encontrarem (no máximo 36 meses), toda calculada no SQL do gráfico.
- **Resultado:** no ritmo de 2024, a receita perdida alcança a de contas novas em **mar/2026, 15 meses depois de dez/2024**. Em 2024 entraram US$ 1.867.254 de contas novas e saíram US$ 1.127.644 em cancelamentos.
- **Nota da IA, sensibilidade:** a resposta depende do modelo de tendência.
  - O mês real de dez/2024 já teve mais perda (US$ 574.643) do que receita nova (US$ 516.066).
  - Uma tendência exponencial sobre 2024 (receita nova +15%/mês, perdida +34%/mês) cruzaria em fev/2025.
  - Uma reta sobre os 24 meses não cruza nunca, porque 2023 quase não teve perda.
  - A reta de 2024 é a leitura mais conservadora das que cruzam.
- **Como foi verificado:** o `visao-test` confere os totais de 2024 contra consultas independentes, as retas contra uma regressão em TypeScript e o cruzamento (2026-03, 15 meses). A captura da tela foi conferida.

## D32 — Visão geral numa tela só, sem receita em risco (decisão humana)
- **Humano decidiu:**
  - Os números do topo vão para um único cabeçalho, sem os dois níveis de grupos, sem espaço lateral sobrando, e o conjunto sobe na tela.
  - Sai a **receita em risco**: o cálculo não estava correto, e uma receita em risco de verdade envolve muito mais do que o MRR das contas que tiveram algum churn.
  - "Receita por indústria" desce, e no lugar entra um donut de **contas pagas × trial**.
  - Gráficos com cinco ou mais barras viram gráficos de coluna. Os demais seguem como barras, encolhidos. Mais gráficos por linha, e o usuário não precisa rolar a tela.
- **IA implementou:**
  - **Cabeçalho único:** oito números numa linha (contas, contas com churn, eventos, contas com evento, churn rate, assinaturas, assinaturas encerradas, MRR). O MRR aparece compacto (US$ 10,2 mi).
  - **Receita em risco:** saiu da tela, do cálculo (`indicadores`) e do teste.
  - **Contas pagas × trial:** vem de `accounts.is_trial`, 403 pagas e 97 trial.
  - **Layout em três faixas:** os dois gráficos de linha; os dois donuts e as colunas de receita por indústria e por país; as colunas de churn por indústria, por origem e por motivo, mais as barras de churn por plano (três barras).
  - **Gráficos na medida do painel:** cada gráfico mede o próprio painel e desenha no tamanho real em pixels. O texto não encolhe em painéis estreitos, e a tela preenche a altura da janela sem rolar.
  - **Colunas:** o valor fica em cima de cada coluna, os nomes longos alternam em duas linhas em vez de girar, e a coluna mais alta ocupa a altura toda.
  - **Botão do analista:** saiu do canto inferior, onde cobria um gráfico, e foi para a linha do título.
- **Como foi verificado:**
  - Capturas em 1440×900 e 1280×800 sem rolagem (altura de rolagem igual à altura visível) e sem painel transbordando.
  - O `visao-test` confere pagas + trial = 500.
  - Typecheck, lint e os quatro testes passam.
- **Limite:** com o chat aberto (440px a menos), a tela ainda cabe sem rolar, mas os donuts e os rótulos do cabeçalho ficam pequenos.

## D33 — Telas 2 a 5 no padrão executivo; risco por exposição; Tela 4 depois da análise (decisão humana)
- **Humano decidiu, entre opções da IA com recomendação:**
  - **Estilo:** as telas 2 a 5 seguem o padrão da visão geral, ou seja, uma tela sem rolagem, rótulos simples e sem os códigos B2.1 e "nível:" na tela. A Tela 1 é ajustada junto.
  - **Tela 3:** as contas são ordenadas por exposição (MRR em jogo), não por score de risco. O humano acrescentou um gráfico de linha com a idade média das assinaturas, mês a mês.
  - **Tela 4 (ações):** fica para depois, quando o humano tiver as outras telas e fizer a própria análise.
  - **Ordem:** 2 → 3 → 5 → 4, com revisão humana ao fim de cada tela.
- **IA construiu a Tela 2, "O que está causando o churn?":**
  - **Quem saiu × quem ficou (B2.1):** halteres com 16 indicadores, média por conta. Saiu = conta com evento de churn (352); ficou = sem evento (148).
  - **Motivos pesados pela receita (B2.2):** eventos por motivo e o MRR atual das contas que deram cada motivo, com refund e reativações ao lado. Uma conta com dois motivos entra nos dois.
  - **Suporte (B2.3):** % dos tickets de cada grupo por prioridade, resolução e 1ª resposta, e um resumo de tickets, escalados, satisfação e sem nota.
  - **Recursos (B2.4):** uso × taxa de erro por recurso.
- **Escolhas da IA (a revisar pelo humano):**
  - **"Pesado por MRR":** usa o MRR das assinaturas ativas das contas (D23), não o total histórico usado no B1.1.
  - **Beta:** `is_beta_feature` marca o registro de uso, não o recurso. Os 40 recursos têm registros beta, então cada recurso vira dois pontos, uso estável e uso beta.
  - **Alertas:** com "sem registros em alerta", os tickets T08 e os usos T06/E13 saem de todos os blocos.
- **O que a tela mostra (nenhuma conclusão escrita na tela):** os dois grupos são quase idênticos nos 16 indicadores.
  - As maiores diferenças são downgrade (+5,2 p.p. para quem saiu) e upgrade (+2,8 p.p.).
  - Os motivos têm pesos parecidos em eventos e em MRR (de 15% a 20% cada).
  - O suporte tem distribuições iguais. A satisfação é 3,98 nos dois grupos.
  - O uso beta erra de 3,1% a 9,5%, contra 4,7% a 6,9% no uso estável.
  - Isso é coerente com a D3: nenhuma variável separa quem sai de quem fica.
- **Como foi verificado:**
  - O `tela2-test` faz 16 checagens: 352 + 148 = 500, motivos = 600 eventos, refund total, 61 reativações, MRR de um motivo por consulta independente, 2.000 tickets (923 sem T08), 80 pontos com o total de usos e o filtro FinTech.
  - Capturas em 1440×900 e 1280×800 sem rolagem.

## D34 — Tela 2 refeita: churn quebrado por atributo; suporte e uso vão para a Tela 3 (decisão humana)
- **Humano revisou a Tela 2 da D33 e rejeitou quase tudo:** "tá mais fácil olhar o banco de dados do que entender esses gráficos". Só o gráfico de recursos (uso × taxa de erro) ficou, "mais ou menos".
- **Humano decidiu:**
  - Os quatro gráficos de churn da visão geral (indústria, origem, motivo, plano) saem de lá e vêm para a Tela 2. A visão geral não fala mais de churn por atributo.
  - A Tela 2 ganha churn por país, por tipo de cobrança (mensal ou anual) e no período de teste × no período pago.
  - Suporte sai da Tela 2. A Tela 3 passa a ser sobre tickets e uso do produto.
- **IA construiu:** Tela 2 com sete gráficos numa tela sem rolagem. Os quatro de cinco ou mais barras ficam em colunas na linha de cima; plano, cobrança e teste × pago ficam em barras na linha de baixo (D32). A visão geral ficou com três faixas (cabeçalho, as duas linhas do tempo e a linha de receita).
- **Escolha da IA (a revisar pelo humano):** cobrança e teste existem só na assinatura (`billing_frequency`, `is_trial`). Na conta, 497 das 500 têm cobrança mista. Por isso esses dois gráficos medem "% das assinaturas encerradas", e os outros cinco medem "% das contas com evento de churn" (D23). Cada nota de painel diz qual é a unidade.
- **O que a tela mostra:** cobrança mensal 9,4% × anual 10%; teste 10% × pago 9,7%; país de 56% (DE) a 77,6% (UK, 58 contas).
- **Removido:** os halteres de 16 indicadores e a tabela de motivos pesados por MRR. O código de suporte e de recursos foi para `src/engine/tela3.ts`, à espera do desenho da Tela 3.
- **Como foi verificado:**
  - `tela2-test` com 15 checagens: cada quebra confere com uma consulta independente, os motivos somam 600 eventos e os filtros de setor e de plano chegam aos dois tipos de gráfico.
  - `tela3-test` com 7 checagens para suporte e recursos.
  - Capturas da Tela 2 e da visão geral em 1440×900 e 1280×800, sem rolagem e sem painel transbordando.

## D35 — Tela 2 com gradiente nas colunas e anéis de donut nos gráficos de 2 ou 3 grupos (decisão humana)
- **Humano decidiu:** "essa tela 2 tá muito sem graça".
  - Os gráficos com dois ou três rótulos viram pizza ou donut.
  - As colunas ganham um gradiente de cor que separa os grupos de maior incidência dos de menor.
  - Os gráficos são redistribuídos para acabar com os espaços vazios.
- **IA construiu:**
  - **Anéis:** plano, cobrança e teste × pago viraram um anel de donut por grupo. O arco laranja é a taxa de churn do grupo; a trilha escura é o resto. Embaixo vêm o nome e a base ("de 178 contas", "de 2.461 assinaturas").
  - **Gradiente:** nas quatro colunas, laranja de uma só cor. O menor valor do gráfico fica no tom escuro e o maior no tom claro. As pontas escuras passam 2:1 de contraste contra o painel.
  - **Redistribuição:** a linha de baixo divide a largura em 3:2:2, então todo anel tem o mesmo tamanho. A linha de cima fica com 60% da altura.
- **Escolhas da IA (a revisar pelo humano):**
  - **Taxa, não fatias:** um donut de fatias (por exemplo, Mensal × Anual como partes de um todo) mostraria a composição da base, não a taxa de churn. Por isso cada grupo ganhou o próprio anel.
  - **Escala do gradiente:** vai do mínimo ao máximo de cada gráfico, então destaca diferenças pequenas: na indústria vai de 66,7% a 73,5%. Os números em cima das colunas dão a escala real.
- **Como foi verificado:**
  - `tela2-test` e `visao-test` passam, typecheck e lint limpos.
  - Capturas em 1440×900 e 1280×800 sem rolagem e sem painel transbordando.

## D36 — A taxa de churn por conta é o `churn_flag` da conta (decisão humana, revê a D20 para taxas)
- **O que aconteceu:** o humano estranhou os números da Tela 2 (DevTools 73,5%, EdTech 72,2%) e perguntou de onde vinham. Ele tinha DevTools perto de 30% e FinTech perto de 22%.
- **De onde vinham (IA verificou):** da view `vw_conta`, coluna `churn_rotulo`, que vale "a conta tem pelo menos um evento em `churn_events`" (D20): 352 de 500 contas, 70,4%. Não havia divisão de assinatura por conta. Os números do humano são o `churn_flag` da conta: 110 de 500, 22%; DevTools 31%, FinTech 22,3%. 277 das 352 contas com evento têm `churn_flag = 0`.
- **Humano decidiu, entre opções da IA com recomendação:** as taxas por conta usam `churn_flag`. Os eventos de churn seguem como volume e motivo.
- **IA mudou:**
  - `churnPor` (indústria, origem, plano, país) passou a usar `sum(churn_flag) / count(*)`. A nota dos painéis diz "% das contas com churn".
  - O rótulo de categoria das colunas não corta mais na borda.
- **Fica como estava (a revisar pelo humano):**
  - As séries mês a mês (crescimento, churn rate dez/2024) seguem nos eventos, porque `churn_flag` não tem data.
  - O card "Contas com evento de churn" e as contagens da Tela 1 também seguem nos eventos.
  - Cobrança e teste × pago seguem em "% das assinaturas encerradas".
- **O que a tela mostra agora:**
  - Indústria: DevTools 31%, FinTech 22,3%, HealthTech 21,9%, EdTech 16,5%, Cybersecurity 16%.
  - País: DE 32% (25 contas), AU 12,5%.
  - Origem: event 30,2%, partner 14,6%.
  - Plano: 21,9% a 22,1%, praticamente igual.
- **Como foi verificado:**
  - `tela2-test` com 17 checagens, incluindo DevTools 31%, FinTech 22,3% e contas com churn por plano somando 110.
  - `visao-test`, `tela1-test`, `dashboard-test` e `axis-test` passam.
  - Capturas em 1440×900 e 1280×800 sem rolagem.

## D37 — Os donuts da Tela 2 mostram a composição do churn, não a taxa de cada grupo (decisão humana)
- **Humano decidiu:**
  - Os três anéis da D35 não servem: cada um mostrava a taxa isolada do grupo, e plano (por conta) ficava ao lado de cobrança (por assinatura).
  - O que importa é quanto cada grupo representa do total do churn ("se eu tive 600 churns e cada um teve 200, cada um teve 33%").
  - A unidade de cada donut:
    - **Plano:** contas com `churn_flag = 1`, pelo plano da conta.
    - **Teste × pago:** contas com `churn_flag = 1`, pelo `is_trial` da conta.
    - **Tipo de cobrança:** assinaturas com `churn_flag = 1`, pelo `billing_frequency`, porque a cobrança só existe na assinatura.
- **IA construiu:**
  - `composicaoPlano`, `composicaoTrial` e `composicaoCobranca` em `tela2.ts`, desenhados com o mesmo donut da visão geral (total no centro, % na legenda). A nota de cada painel diz qual é o total.
  - O componente de anéis foi removido.
- **O que a tela mostra:**
  - **Plano (110 contas):** Pro 39 (35%), Basic 37 (34%), Enterprise 34 (31%).
  - **Teste × pago (110 contas):** pagas 85 (77%), trial 25 (23%).
  - **Cobrança (486 assinaturas):** anual 247 (51%), mensal 239 (49%).
- **Como foi verificado:**
  - `tela2-test` com 16 checagens: somas de 110 e de 486, contagem de cada grupo, filtro FinTech nos três tipos de gráfico e filtro de plano usando o plano da assinatura na cobrança.
  - Typecheck, lint e `visao-test` passam.
  - Capturas em 1440×900 e 1280×800 sem rolagem.

## D38 — Rótulos das colunas: todos numa linha ou todos inclinados, sem sobreposição (decisão humana)
- **Humano decidiu:**
  - Os caracteres dos rótulos não podem se sobrepor.
  - Quando os rótulos não cabem lado a lado, todos ficam inclinados e com o mesmo alinhamento. Isso substitui os rótulos alternados em duas alturas, que ficavam desalinhados (o gráfico de motivos).
- **IA mudou (`BarChart`, modo `fit`):**
  - **Rótulos de categoria:** em 10px, todos na horizontal se o maior couber na coluna; senão, todos a −45°. O espaço dos inclinados sai de baixo do gráfico, e a margem esquerda cresce para o primeiro rótulo, sem encolher o gráfico.
  - **Valores em cima das colunas:** um único tamanho por gráfico, calculado para o valor mais longo caber na coluna com folga (de 7 a 10px). Antes, cada valor tinha o seu tamanho e vizinhos quase se tocavam.
  - **Atributo inválido:** saiu o `height="auto"` do SVG, que gerava erro no console.
- **Como foi verificado:**
  - Capturas da Tela 2 e da visão geral em 1440×900 e 1280×800, sem rolagem e sem rótulos sobrepostos.
  - `axis-test`, typecheck e lint passam.

## D39 — Legenda do donut medida pelo texto, sem sobreposição (pedido humano)
- **Humano apontou:** na legenda do donut de plano, o nome e o número se sobrepunham ("Basic" com "37", "Enterprise" com "31%").
- **Causa (IA):** o `PieChart` punha a legenda numa posição fixa (x = 330) e alinhava o número à borda direita. Em painéis entre 420 e uns 520 de largura, as duas colunas se cruzavam. As capturas de 1440 e 1280 não pegavam esse caso: lá o painel caía no modo estreito, que mostra só o %.
- **IA mudou:**
  - **Largura medida:** a largura da legenda sai do nome mais longo e do número mais longo.
  - **Encaixe:** o donut ocupa o que sobra, e o conjunto donut + legenda fica centralizado.
  - **Contagem:** sai antes que o donut fique pequeno demais, e aí a legenda mostra só o %.
  - **Fonte:** encolhe só em último caso.
  - **Atributo inválido:** saiu o `height="auto"` do SVG.
- **Como foi verificado:**
  - Capturas da Tela 2 em 1280×800, 1440×900, 1512×945 e 1728×1080, e da visão geral em 1280×800, todas sem sobreposição e sem rolagem.
  - Typecheck e lint passam.

## D40 — Idade média da base, mês a mês, na visão geral (decisão humana)
- **Humano decidiu:** um gráfico de linha na visão geral com a idade média das contas ativas, mês a mês, de jan/2023 a dez/2024. Para cada mês, pega todas as contas ativas, calcula a idade média e plota. O objetivo é ver se a base está envelhecendo (mantendo contas) ou rejuvenescendo (perdendo mais contas do que mantém ou ganha).
- **IA definiu (a revisar pelo humano):**
  - **Conta ativa no mês:** tem uma assinatura em vigor no mês (D21, a mesma regra do B1.1).
  - **Idade da conta:** do `signup_date` até o fim do mês, em meses de 30,4375 dias.
  - **Segunda linha:** o pedido fala em "idade média das assinaturas" e em "contas ativas", então a IA desenhou as duas: contas ativas, desde o cadastro, e assinaturas em vigor, desde o `start_date`. Mesma unidade, um eixo só.
  - **Filtros:** os de conta chegam às duas linhas; o de plano usa o plano de cada identificador (D27).
- **O que o gráfico mostra (sem conclusão na tela):**
  - **Contas:** a idade média sobe todo mês, de 1 mês em jan/2023 para 11,2 meses em dez/2024. As 500 contas ainda estão ativas em dez/2024, então nenhuma saiu de vez.
  - **Assinaturas:** a idade média sobe até 5,6 meses em nov/2024 e cai para 5,4 em dez/2024, quando as assinaturas em vigor passam de 3.827 para 4.707.
  - **Limite:** a base começa vazia em jan/2023, então parte da subida das contas é a própria idade dos dados.
- **Layout:** a segunda faixa da visão geral passou de duas para três colunas: crescimento, receita nova × perdida e idade média. A nota da previsão de receita agora começa pelo mês do cruzamento, para não ser cortada.
- **Como foi verificado:**
  - `visao-test` ganhou 4 checagens: 24 meses, idade das contas em dez/2024 = 11,16 e das assinaturas = 5,44 (por consultas independentes), e o filtro de setor chegando às duas linhas.
  - Capturas em 1440×900 e 1280×800 sem rolagem.

## D41 — Layout da visão geral em quatro faixas, com a idade média de ponta a ponta (decisão humana)
- **Humano decidiu (com um desenho sobre a captura):**
  - No topo, crescimento mês a mês e receita nova × perdida, lado a lado.
  - No centro, o gráfico de idade média, atravessando a tela de um lado ao outro.
  - Embaixo, os quatro gráficos de receita e de contas.
- **IA mudou:**
  - A grade da visão geral passou a ter quatro faixas: cabeçalho, as duas linhas do tempo, a idade média em largura total e os quatro gráficos. As alturas ficam em 1,1 : 1 : 0,95.
  - Os gráficos de linha dentro de painel (`bare`) perderam margem de sobra: 12px em cima e 24px embaixo, antes 20 e 40. Sem isso, a faixa do meio deixava só uns 45px de gráfico.
  - A nota da idade média ficou curta ("em meses, no fim de cada mês, de jan/2023 a dez/2024"), porque a legenda já nomeia as duas linhas.
- **Como foi verificado:**
  - Capturas em 1440×900 e 1280×800 sem rolagem e sem painel transbordando.
  - `visao-test`, `axis-test`, typecheck e lint passam.
- **Observação:** a Tela 1 ainda rola em 1440×900, como já rolava, porque ainda não foi passada para o padrão de uma tela só.

## D42 — Eixo vertical dos gráficos de linha ajustado à escala do dado (pedido humano)
- **Humano perguntou:** por que o eixo da idade média ia até 20 meses se o dado chega a 11. Pediu um eixo adequado à escala do dado.
- **Causa (IA):** o `LineChart` arredondava o máximo para 1, 2 ou 5 × 10ⁿ, então 11,2 virava 20 e metade da altura ficava vazia.
- **IA mudou:** para séries positivas, o eixo escolhe o menor passo redondo (1, 2, 2,5, 3 ou 5 × 10ⁿ) que cubra o máximo em até quatro intervalos. As linhas de tendência e as projeções entram no cálculo, então nada é cortado. Eixos com valores negativos (o crescimento mês a mês) não mudaram.
- **Efeito:**
  - **Idade média:** 0 a 12 meses, de 3 em 3.
  - **Receita nova × perdida:** 0 a US$ 800 mil, de 200 em 200. O máximo é US$ 779 mil, na projeção.
- **Como foi verificado:**
  - Capturas em 1440×900 e 1280×800 sem rolagem.
  - O máximo da receita foi conferido, com as projeções incluídas.
  - Typecheck e lint passam.

## D43 — Tela 3: suporte e uso do produto (decisão humana; desenho da IA)
- **Humano decidiu:** a Tela 3 deixa de tratar de segmentos e risco e passa a mostrar o suporte (tickets) e como os clientes usam o produto (recursos).
- **IA desenhou, no padrão da visão geral (uma tela, sem rolagem):**
  - **Cabeçalho:**
    - Tickets (2.000, em 492 contas) e escalados (95, 4,8%).
    - Satisfação média (3,98, com 41,3% sem nota), resolução média (35,9 h) e 1ª resposta média (88 min).
    - Usos do produto (250,5 mil, 21.126 horas), erros (14.107) e taxa de erro (5,63%).
  - **Linhas mês a mês:** tickets com os escalados, satisfação média (eixo fixo de 0 a 5) e usos.
  - **Composição dos tickets:** donuts de prioridade e de notas (com "sem nota" como fatia), e barras de faixas de tempo de resolução e de 1ª resposta.
  - **Recursos:** o gráfico de uso × taxa de erro que o humano aprovou na D33 (estável e beta separados) e os 10 recursos mais usados, em colunas com gradiente.
- **Escolhas da IA (a revisar pelo humano):**
  - **Unidades:** tickets seguem os filtros de conta. Usos seguem os de assinatura, com o plano da assinatura (D27).
  - **Alertas:** com "sem registros em alerta", saem os 1.077 tickets abertos antes do cadastro (T08) e os usos fora da assinatura ou repetidos (T06/E13). Sobram 923 tickets.
  - **Cores:** os donuts ganharam a 4ª cor da paleta (amarelo `#c98500`), porque prioridade e notas têm 4 fatias. O validador de paleta passa as 4 cores em modo escuro.
  - **O que saiu:** a comparação saiu × ficou do suporte da D33, que o humano rejeitou na D34.
- **O que a tela mostra (sem conclusão na tela):**
  - Os tickets ficam em 60 a 98 por mês.
  - A satisfação oscila entre 3,7 e 4,4.
  - O uso fica em torno de 10 mil por mês nos 24 meses, enquanto a base passa de 2 para 500 contas ativas.
  - As prioridades se dividem quase por igual (24% a 26%).
  - Mais da metade dos tickets leva mais de 24 h para fechar.
  - O uso beta tem taxa de erro mais espalhada (3% a 10%) que o estável.
- **Junto:**
  - `Indicador` e `Cabecalho` foram extraídos para `components/telas/Indicador.tsx`, compartilhados pela visão geral e pela Tela 3.
  - `LinhasMensais` é o componente genérico de linhas.
  - O `LineChart` ganhou `yMax`.
  - Saíram os `height="auto"` que restavam nos SVGs.
  - O menu lateral agora diz "3 · Suporte e uso do produto".
  - A palavra REPLACE é recusada pela trava de somente leitura, então o nome "Recurso N" é montado no TypeScript.
- **Como foi verificado:**
  - `tela3-test` com 23 checagens contra consultas independentes: totais, meses, composições, filtros de setor e de plano, e o filtro sem alertas (923 tickets).
  - Capturas em 1440×900 e 1280×800 sem rolagem e sem erro no console.
  - Typecheck, lint e `visao-test` passam.

## D44 — Três telas; diagnóstico no relatório; gráficos marcados para o deck (decisão humana; desenho da IA)
- **Humano decidiu:**
  - Bastam as três telas e a visão geral.
  - O diagnóstico vai num documento escrito, uma das formas de entrega aceitas pelo desafio.
  - "O que fazer" (Tela 4) e "Base e confiança" (Tela 5) saem do app e entram no relatório.
  - Faltava nas telas um jeito de marcar gráficos para levá-los aos slides do deck.
  - Entre as opções que a IA apresentou, o humano escolheu a **cópia fiel**: o gráfico marcado é guardado como aparece na tela, e a narrativa dos slides fica com a gente. Ficaram de fora o deck automático herdado do Veta, que redesenha os gráficos num estilo genérico e escreve os títulos com IA, e a exportação avulsa sem lista.
- **IA desenhou:**
  - **Marcar:** cada painel (e cada bloco da Tela 1) ganhou um marcador ao lado do botão SQL. Ao marcar, o navegador monta um SVG único da área do gráfico, no tamanho em que ele está na tela: o SVG do gráfico com os estilos escritos por extenso, a legenda em HTML convertida em texto e caixas SVG, e 12 px de margem. Depois desenha um PNG em 3× a partir dele.
  - **O que se guarda:** a tela, os filtros do momento, o título e a nota do painel, o SVG e o PNG. Ficam numa tabela nova do banco do app (`graficos_marcados`), nunca na base RavenStack, que é só de leitura. O mesmo gráfico com outro filtro é outra marca. Marcar de novo atualiza a cópia.
  - **Gráficos marcados:** item novo no menu, com a contagem, no lugar de "Decks". Mostra as cópias numa moldura 16:9, com tela e filtros, PNG e SVG para baixar e um botão para desmarcar.
  - **.pptx:** um slide 16:9 por gráfico, na ordem em que foram marcados. Cada slide tem o título e a nota do painel, a imagem centrada num painel escuro sem distorcer a proporção, e um rodapé com a tela, o filtro e a fonte.
  - **Segurança:** a API recusa SVG com script, `foreignObject`, eventos ou `javascript:`, e PNG que não seja PNG. Cada usuário só vê e apaga as próprias marcas.
- **Escolhas da IA (a revisar pelo humano):**
  - O fundo escuro das telas foi mantido nos slides, para a cópia ser fiel.
  - Os títulos dos slides são os títulos dos painéis. A mensagem de cada slide fica para o humano escrever.
  - O código do deck do Veta (`deck.ts`, `/decks`) saiu do menu, mas continua no código (ISC-23).
- **Como foi verificado:**
  - `marcados-test` com 17 checagens num banco descartável.
  - No navegador: 6 gráficos marcados na visão geral e nas Telas 1, 2 (filtro FinTech) e 3. As cópias foram conferidas uma a uma, e o .pptx tem 6 slides com a imagem centrada e a proporção mantida.
  - As telas seguem sem rolagem em 1440×900 e 1280×800. `/tela/4` e `/tela/5` respondem 404.
  - Typecheck, lint e os testes visao, tela1, tela2, tela3, dashboard e axis passam.
  - As marcas de teste foram apagadas depois.

## D45 — Apresentação em pirâmide de Minto a partir dos gráficos marcados (pedido humano; desenho da IA)
- **Humano pediu:**
  - Um gráfico por slide não é uma apresentação pronta.
  - O Veta preparava os slides com uma estrutura de pirâmide de Minto (a da McKinsey), e a mesma estrutura deve vir para cá.
  - O botão "Desmarcar" da lista deve ficar vermelho, para chamar a atenção.
- **IA encontrou no Veta:**
  - `deck.ts` tinha um "arranjador": um LLM instruído como analista treinado na McKinsey, que transformava os achados marcados numa pirâmide (ideia central, SCQA, ordem MECE, títulos de ação, recomendações).
  - O código preenchia os números a partir do SQL.
  - Esse fluxo estava preso aos pins do chat e a texturas de fundo de 2 MB que não entraram no git.
- **IA desenhou (`engine/deckMarcados.ts`):**
  - **Estrutura dos slides:**
    - Capa com a ideia central.
    - Resumo executivo: a pirâmide numa página, com a ideia central e, abaixo, as seções com os títulos de ação.
    - Contexto em SCQA, com a ideia central como resposta.
    - Uma divisória por seção da linha-chave (2 a 4 seções MECE, com títulos que são afirmações).
    - Um slide por gráfico: título de ação, 1 ou 2 linhas de apoio, a imagem fiel e o rodapé com tela, filtro e fonte.
    - Ações recomendadas no fim.
  - **Visual:** o do Veta, com obsidiana e dourado nas capas e papel nos slides de argumento, mas sem as texturas.
  - **Divisão de trabalho, como no Veta:** o LLM do app escreve a narrativa e o código confere os números.
    - A marca agora guarda o SQL do painel.
    - Ao montar, o SQL de cada gráfico roda de novo, e cada número escrito é conferido contra essas linhas, na precisão em que foi escrito.
    - Porcentagem só confere com coluna de porcentagem ou com a fatia de uma composição, que o código calcula e entrega ao LLM. Assim, uma contagem de 85 não vira 85%.
    - O que não confere sai, ou é trocado pelo título do painel, e aparece listado em "Conferência dos números".
  - **Regras do arranjador:**
    - Não afirmar causa ("associação, não causa"; motivos são o que o cliente declarou).
    - Distinguir a taxa de um grupo da fatia do churn total.
    - Usar os rótulos em português das telas.
    - O briefing opcional orienta a ideia central.
  - **Garantias:**
    - Todo gráfico marcado vai para algum slide.
    - Sem LLM, um arranjo por regra (uma seção por tela) ainda monta uma apresentação correta.
    - Se as marcas mudarem, é preciso montar de novo antes de baixar.
  - **Na página "Gráficos marcados":** painel "Apresentação" com o briefing, os botões montar e baixar, e a pirâmide para revisar antes do .pptx.
- **Escolhas da IA (a revisar pelo humano):**
  - **Quem escreve:** o texto é da IA e varia de uma montagem para outra (temperatura 0,3). O humano revisa a pirâmide na tela antes de baixar.
  - **Edição:** ainda não dá para editar os textos dentro do app.
  - **Pontos fracos vistos nas montagens:**
    - "Dois terços dos tickets" não é conferido, porque é número escrito por extenso.
    - Uma seção chegou a afirmar causa antes da regra ser reforçada.
    - "DevTools concentra 31% das contas com churn" confundiu taxa com fatia. Foi corrigido com uma regra no prompt, e o caso 85% com a separação entre porcentagem e contagem.
- **Como foi verificado:**
  - `deck-marcados-test` com 28 checagens, usando SQL real e um arranjador roteirizado, num banco descartável.
  - Três montagens reais com 10 gráficos (7 a 8 s cada); a última sem nenhum ajuste de número.
  - Typecheck, lint e todos os testes passam.
  - **Não verificado:** os slides renderizados. Não há LibreOffice nesta máquina, e a exportação do Keynote por script falhou. A estrutura foi conferida pelo XML do .pptx.

## D46 — De painel para ferramenta de trabalho: drill-down, telas próprias com o analista e apresentação pelo contexto (pedido humano; desenho e código da IA)

- **Pedido do humano (2026-11-17, palavras dele):**
  > "A apresentação precisa ser montada com base nos gráficos que foram marcados, ou ela precisa ser montada com base no chat ocorrido junto ao agente do DeepSeek. Nós também precisamos adicionar o recurso de o usuário poder criar a sua própria tela, pedir para o DeepSeek fazer algumas análises de dados, produzir gráficos e jogar esse gráfico numa tela. O usuário pode pegar esse gráfico, marcar e jogar na apresentação. A apresentação deve ser executada com base no contexto do que está marcado nela, no contexto que o usuário pediu, não uma apresentação genérica [...]. Por mais que seja um desafio, estamos criando uma ferramenta de trabalho. Outro ponto que está faltando também é o drill down. [...] se eu estou na tela 2 e eu vou ver eventos de churn por motivo, eu vejo que recursos estão representando 114 churns. Eu quero clicar em cima desse recurso e poder entender um pouco mais esse dado, poder mergulhar dentro do contexto da informação do dado, eventualmente cruzar outros dados e criar informações novas."
  > "Eu quero que isso seja colocado no [Vercel] ou no Railway [...]. Tem que estar hospedado em algum lugar." Depois: "Se você já está autenticado no Vercel, então esquece o Railway."
  > "Lembre de fazer commit e push conforme você for evoluindo. Faça as anotações necessárias também."
- **Contexto:** o humano deu o pedido e foi dormir; a IA trabalhou sozinha durante a noite. Cada parte abaixo diz o que foi escolha da IA, para o humano revisar de manhã.

### D46.1 — Drill-down (ISC-40)
- **IA desenhou (`engine/recorte.ts`, `components/telas/Recorte.tsx`, `api/recorte`):**
  - Clicar numa barra ou fatia abre um painel com aquele recorte. No exemplo do humano: motivo declarado = Recursos → 114 eventos, 104 contas, 19% dos 600 eventos.
  - **Cinco universos, um por identificador (D23):** eventos de churn, contas, assinaturas, tickets e uso. Cada gráfico das telas diz em qual universo e dimensão ele abre; as rosquinhas de composição já entram com a condição delas (por exemplo, só contas com churn_flag = 1).
  - **O que o painel mostra:**
    - O tamanho do recorte e a parte que ele é do total no filtro.
    - As contas do recorte contra o resto da base (receita, assentos, tickets, satisfação, escalação, resolução, uso, erro, eventos de churn por conta, de `vw_conta`). É aqui que o recorte cruza com outros dados.
    - O recorte quebrado por cada outro atributo. Clicar numa barra desce mais um nível; o caminho aparece no topo e dá para voltar.
    - Um cruzamento de dois atributos escolhidos pelo usuário (tabela com intensidade).
    - Os registros do recorte (até 200).
    - "Perguntar ao analista sobre este recorte" manda o recorte para o chat do DeepSeek.
  - Nas contas e assinaturas, as quebras mostram a taxa de churn de cada grupo (D36), com troca para contagem.
  - Cada bloco é um painel normal: mostra o SQL e pode ser marcado para a apresentação.
  - **Segurança:** as dimensões são fixas no código; um valor do caminho só entra no SQL depois de conferido contra o banco (a regra dos filtros globais). Valor inventado ou injetado é recusado.
- **Achado que apareceu no próprio drill:** nos 114 eventos com motivo "Recursos", os comentários dos clientes são "too expensive" (32), "missing features" (27) e "switched to competitor" (23), além de 32 sem comentário. O motivo declarado e o comentário não batem; vale para o relatório.
- **Como foi verificado:** `recorte-test` (28 checagens: total = SQL independente, cada quebra soma o recorte, segundo nível = barra clicada, valor injetado recusado, cruzamento soma o recorte, filtro global aplicado, tickets e uso). No navegador: Tela 2 (motivo → Recursos → mês), Tela 3 (prioridade, recursos mais usados) e visão geral com filtro de país, sem erro no console.

### D46.2 — Telas próprias com o analista (ISC-41)
- **IA desenhou (`engine/telasUsuario.ts`, `api/telas/*`, `/telas`, `/telas/[id]`, `TelaPropria.tsx`, "Minhas telas" no menu):**
  - O usuário cria uma tela com um nome e escreve um pedido em português. O analista (o mesmo agente DeepSeek do chat, com as mesmas regras de D20–D24) consulta o banco e faz os gráficos; cada gráfico vira um painel da tela.
  - **Cada painel guarda o SQL de onde vieram as linhas dele:** a última consulta que o analista rodou antes de desenhar o gráfico. Assim o painel mostra o SQL, pode ser marcado, e a apresentação consegue rodar de novo e conferir os números (D45).
  - **Pedidos em sequência:** o analista vê os pedidos anteriores da tela e as respostas, e sabe quais painéis já existem ("agora só as contas Enterprise" funciona).
  - As respostas escritas do analista ficam em "Notas do analista", na própria tela.
  - Painéis podem ser tirados da tela; a tela pode ser renomeada e apagada (botão em vermelho, com confirmação).
  - **Marcar:** a marcação aceita as telas próprias (`/telas/<id>`), conferindo que a tela é do usuário. A origem no slide fica "Minha tela · <nome>".
- **Junto:** o chat lateral passou a mandar as perguntas e respostas anteriores da conversa para o analista. Antes, cada pergunta chegava sozinha, sem contexto.
- **Como foi verificado:** `telas-test` (15 checagens com um analista roteirizado, sem LLM). Ao vivo com o DeepSeek no navegador: tela "Recursos e churn", dois pedidos em sequência (13 s e 6 s), três painéis, um marcado e listado em "Gráficos marcados", tudo mantido depois de recarregar, sem erro no console.
- **Escolhas da IA (a revisar):** de 1 a 3 gráficos por pedido; o analista escolhe o tipo de gráfico; a definição de taxa que ele usa vem do prompt (churn = churn_events), por isso pode diferir das telas fixas que usam churn_flag (D36). O SQL de cada painel deixa isso visível.

### D46.4 — Hospedagem no Vercel com o estado salvo no Blob (pedido humano; desenho da IA)
- **Pedido do humano:** "Tem que estar hospedado em algum lugar." e "Se você já está autenticado no Vercel, então esquece o Railway."
- **Endereço:** https://ravenstack-churn.vercel.app (região gru1, São Paulo).
- **Problema que a IA resolveu:** no Vercel o disco das funções não dura e há várias instâncias. O banco do app (logins, conversas, marcas, telas próprias, apresentações) não pode ficar num arquivo local.
- **IA desenhou (`engine/estado.ts`):**
  - O banco do app vira uma cópia SQLite única, cifrada (AES-256-GCM com `STATE_KEY`), guardada num Blob **privado** do Vercel. O caminho do arquivo também é derivado da chave.
  - Antes de cada requisição, a instância pergunta ao Blob se há versão nova (GET condicional, cerca de 80 ms, 304 quando nada mudou) e carrega se outra instância gravou.
  - Toda rota que grava sobe a cópia **antes** de responder, para a próxima tela (talvez em outra instância) já ver a mudança. Isso foi achado num teste: criar uma tela e abri-la logo em seguida dava "não encontrada".
  - Localmente nada disso roda; o banco continua sendo o arquivo `data/app.sqlite`.
  - O banco da RavenStack (só leitura) vai dentro de cada função (`outputFileTracingIncludes`), como pedia o ISC-24.
- **Primeira versão e correção de desempenho:** a checagem com `head()` levava cerca de 550 ms por chamada e cada página demorava 1 a 3 s; com o GET condicional as chamadas caíram para cerca de 150 ms.
- **Limite conhecido:** duas instâncias gravando no mesmo instante — a última gravação vence. Para um avaliador por vez isso não aparece; para uso com muita gente ao mesmo tempo o certo é um banco de verdade (Postgres/Turso).
- **Segredos:** chave do DeepSeek, segredo da sessão, `STATE_KEY` e senha do avaliador estão só nas variáveis do Vercel; nenhum valor foi impresso nem entrou no git. A senha do avaliador do deploy é nova (não é a local) e está em `solution/app/.env.deploy`, fora do git. **Falta o humano decidir** se a senha vai no README público (ISC-26): quem tiver a senha usa a chave do DeepSeek.
- **Como foi verificado:** `estado-test` (cifra e adulteração; e, com um Blob de teste, um processo grava e outro lê). Em produção, no navegador: login do avaliador, as seis páginas com 200, drill de Recursos = 114, marcação, tela própria com o DeepSeek (16 s, dois painéis) que continua lá ao abrir de novo, sem erro no console.

### D46.3 — Apresentação pelo contexto, não por roteiro fixo (ISC-42)
- **Pedido do humano:** "A apresentação deve ser executada com base no contexto do que está marcado nela, no contexto que o usuário pediu, não uma apresentação genérica que você faz uma vez e é sempre a mesma coisa."
- **IA desenhou (`engine/deckMarcados.ts`, `Apresentacao.tsx`, `api/marcados/deck`, `api/marcados/pptx?id=`):**
  - Além dos gráficos marcados e do briefing, o usuário escolhe:
    - o **público** (Diretoria, Customer Success, Produto, Investidores), que muda a ênfase pedida ao arranjador;
    - as **conversas com o analista** e as **telas próprias** que a apresentação deve levar em conta.
  - O arranjador (o LLM do app) lê o que o usuário perguntou e o que o analista respondeu, e a ideia central, a ordem das seções, os títulos de ação e as recomendações seguem essa investigação.
  - **Números:** o SQL por trás das respostas escolhidas roda de novo e os números dessas linhas passam a valer na conferência (D45). Um número que só aparece no texto de uma conversa, sem estar no SQL, continua sendo apagado.
  - Cada montagem fica guardada ("Montagens anteriores"), com público e fontes, e o .pptx de uma montagem antiga ainda pode ser baixado. Slides de gráficos desmarcados depois ficam de fora.
- **Como foi verificado:**
  - `deck-marcados-test` subiu para 35 checagens: o arranjador recebe a tela, o pedido e a resposta; o número 514 que vem do SQL da tela fica e, sem esse contexto, o mesmo 514 sai; tela de outro usuário não entra; o histórico é por usuário.
  - Duas montagens reais com o DeepSeek, mesmos 10 gráficos: "Diretoria, decidir onde agir" deu a ideia central "O churn já supera a receita nova [...] a prioridade é reter a base atual antes de crescer"; "Produto + tela Recursos e churn" deu "O churn é difuso na base [...] o uso do produto é o que o time pode mudar", com seções e ações diferentes.

### D46.5 — Gráficos do chat vão para a apresentação ou para uma tela (ISC-43)
- **IA fez:** embaixo de cada gráfico que o analista desenha no chat há "Marcar para a apresentação" (a origem no slide é "Chat do analista", com o SQL que gerou as linhas) e "Enviar para uma tela" (uma tela existente ou uma nova).
- **Limpeza junto:** os botões de "pin" do Veta (que levavam ao deck antigo, fora do menu) foram escondidos no chat. Eles confundiam com a marcação nova; um teste automático chegou a clicar no pin errado por isso.
- **Como foi verificado:** no navegador, pergunta no chat → gráfico de colunas → marcado (POST 201, rota `/chat`, com SQL) e enviado para uma tela nova, sem erro no console.

## D47 — Assinaturas e receita por conta, ao lado da idade média (pedido humano; código da IA)
- **Pedido do humano (17/11):** reduzir "Idade média da base, por mês" para a metade esquerda e, à direita, "um outro gráfico de linha [...] a quantidade média de assinaturas por conta ao longo do tempo, e também a receita média por conta ao longo do tempo. [...] duas escalas no eixo vertical [...] a escala da quantidade de assinaturas no eixo vertical do lado esquerdo [...] e a receita média no eixo vertical do lado direito. Cada linha deve obedecer à sua escala." Pediu para fazer só no local e publicar depois de aprovar.
- **Definição (humano confirmou):** em cada mês, as contas com pelo menos uma assinatura em vigor no mês (a regra de mês ativo da D21); para cada uma, quantas assinaturas em vigor ela tem e a soma do MRR delas; o gráfico mostra a média sobre essas contas. O humano perguntou se a linha azul era "a quantidade de assinaturas ativas por conta"; a IA confirmou e corrigiu a nota do painel, que dizia "no fim de cada mês" (contar só as do último dia dá 9,08 em vez de 9,41 em dez/2024).
- **IA fez:** `porConta()` em `engine/visaoGeral.ts`; um eixo direito opcional por série no `LineChart` (mesmo número de intervalos dos dois lados, para as linhas de grade servirem aos dois). Junto, a caixa do mouse dos gráficos de linha abre para o lado com espaço e, se o ponto está no alto, para baixo; antes ela saía pela borda ou era cortada no topo.
- **Aviso da IA:** com essas escalas as duas linhas quase se sobrepõem; isso vem da escala escolhida, não quer dizer que as duas medidas crescem na mesma proporção.
- **Como foi verificado:** dez/2024 recalculado direto no banco (500 contas, 9,41 assinaturas, US$ 21.469 por conta); com filtro de plano Basic, 3,15 e US$ 1.501; typecheck, lint e os testes de eixo, visão e das três telas passam; print no navegador com a caixa do mouse nos dois lados do gráfico, sem erro no console.

## D48 — O banco gerado dos CSVs vai para o repositório; deploy automático pelo GitHub (decisão humana)
- **Pedido do humano (17/11):** depois de saber que o push não atualizava o Vercel: "Não vamos deixar como está, mas, na hora de fazer o request, é importante que a gente coloque o SQL junto do repositório para que eles possam ter acesso ao material que foi produzido a partir do CSV também."
- **O que muda:** `solution/app/data/ravenstack.db` (5,8 MB), o banco que `solution/sql/build_db.py` monta dos CSVs do desafio, passa a ser versionado. Ele tem as tabelas brutas, as tipadas, as checagens de qualidade e as views; não tem nada do app (logins, conversas e marcas ficam em outro banco, fora do git). Os scripts SQL (`01_schema` a `04_views`) já estavam no repositório.
- **Deploy:** até aqui cada versão foi publicada da máquina com `vercel deploy --prod`; o projeto do Vercel não estava ligado ao GitHub (a IA confirmou: o push não disparou build). Com o banco no repositório, um build feito pelo GitHub tem tudo de que precisa. Ligar o projeto ao repositório pede a instalação do app do Vercel no GitHub, que só o humano pode autorizar.
- **Pipeline ligado (17/11):** o humano instalou o app do Vercel no GitHub. A IA ligou o projeto `ravenstack-churn` ao repositório `ronaldomt/ai-master-challenge`, com Root Directory `submissions/ronaldo-tkotz/001-churn/solution/app`, framework Next.js e branch de produção `submission/ronaldo-tkotz`. Daqui em diante, cada push nesse branch publica a produção; o primeiro teste é o commit que registra esta linha.
- **Primeiro build pelo GitHub falhou, e foi corrigido (17/11):** o Vercel mandou e-mail de "build failed" (`ENOENT ... /vercel/path0/.next/package.json`). O Next compilava, mas a publicação procurava o `.next` na raiz do repositório: o `next.config.ts` fixava a raiz de rastreamento na pasta do app, o que servia ao deploy pela máquina (só a pasta sobe) e não ao build pelo GitHub (o repositório inteiro é clonado). A IA passou a fixar essa raiz só fora do Vercel (d8bc3ba). O push desse commit publicou a produção sozinho, Ready em 43 s, com o banco respondendo e o painel da D47 no ar.

## D49 — Sai a Tela 1; acabamento da Tela 3 (decisão humana; código da IA)
- **Pedido do humano (17/11), Tela 1:** "Vamos remover a tela 1 e as três afirmações. Essa tela pode ser produzida a partir de um slide deck. Como essas são as respostas que o CEO está buscando neste exato momento, a gente produz um slide deck para isso. Quando ele buscar outras respostas, ele também pode utilizar um slide deck que vise trazer outras respostas."
- **Pedido do humano, Tela 3 (com print marcado):**
  - no lugar de "Tickets por mês": "um gráfico de coluna com três colunas um pouco mais largas, mostrando o volume de uso total por tipo de plano (básico, pro ou enterprise). Em cima dessas colunas [...] uma linha, que mostra a taxa % de erro por tipo de plano [...] uma escala de volume de uso, que vai ser nominal, e uma escala percentual";
  - sair "Satisfação média por mês" e "Uso do produto por mês"; no lugar, "um gráfico de barras apresentando a taxa de escalação por prioridade de ticket [...] quantos tickets de prioridade baixa, média, alta e urgente foram escalados";
  - nos 10 recursos mais usados, "plotar uma linha com a taxa de erro de cada um".
- **Leituras da IA, avisadas antes de executar:** o plano do uso é o da assinatura (D27); taxa de erro = erros ÷ usos; a barra de escalação é a % escalada de cada prioridade e o rótulo traz "N de M"; marcas antigas da Tela 1 continuam nomeando a origem.
- **IA fez:**
  - `/tela/1` agora leva à visão geral; saíram do menu a Tela 1 e os números "2 ·" e "3 ·" das outras (o menu começaria em 2); saíram `Bloco.tsx`, `Tela1Graficos.tsx` e os blocos B1.2 e B1.3 do motor. `b11` e `MESES_CTE` ficam, porque a visão geral usa. O teste da Tela 1 virou `churn-mensal-test` (9 checagens: o B1.1 e os filtros).
  - Tela 3: `usoPorPlano`, `escalacaoPorPrioridade`, taxa de erro nos 10 recursos (`tela3.ts`); um gráfico novo de colunas com linha (`charts/ColunasLinha.tsx`), com eixo de volume à esquerda e de % à direita, as duas escalas começando em zero e dividindo as mesmas linhas de grade. Clicar numa coluna abre o recorte (plano ou recurso); clicar numa barra de escalação abre os tickets daquela prioridade.
- **O que os dados mostram:** tudo é plano. Taxa de erro de 5,55% (Basic), 5,70% (Pro) e 5,64% (Enterprise); escalação de 4,5% (urgente) a 5,1% (média), com urgente escalando menos que média. Nos 10 recursos mais usados, a taxa vai de 4,71% a 6,45%. Os eixos começam em zero, então a diferença aparece do tamanho que tem.
- **Como foi verificado:** `tela3-test` (29 checagens, cada número contra consulta independente: usos e taxa por plano, filtro de plano, escalados 95 de 2.000, urgente 23 de 514 = 4,5%, taxa do Recurso 32); `churn-mensal-test`, `visao-test`, `tela2-test`, `recorte-test`, `marcados-test`, `deck-marcados-test` e `axis-test` passam; typecheck e lint limpos; no navegador, `/tela/1` leva a `/`, a Tela 3 cabe numa tela só e a caixa do mouse mostra usos e taxa nos dois gráficos novos, sem erro no console.
