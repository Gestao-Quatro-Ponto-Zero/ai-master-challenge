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
