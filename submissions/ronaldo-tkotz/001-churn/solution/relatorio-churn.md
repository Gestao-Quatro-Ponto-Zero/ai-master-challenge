# RavenStack: diagnóstico de churn

**Para:** CEO · **Base:** 5 tabelas (500 contas, 5.000 assinaturas, 25.000 registros de uso, 2.000 tickets, 600 eventos de churn), jan/2023 a dez/2024 · **Data de corte:** 31/12/2024

Cada número deste relatório sai de uma consulta que pode ser refeita: os scripts estão em `process-log/verification/` (o `21_sinais_e_contas.py` reúne os números desta versão) e o banco está em `solution/app/data/ravenstack.db`.

---

## Em uma página

1. **O churn não tem uma causa única.** Plano, uso, erros, suporte, satisfação, país e trial, olhados um de cada vez, mudam pouco a chance de uma conta cancelar. O que aparece é uma colcha de retalhos: várias diferenças pequenas que, somadas, contam a história.
2. **A causa raiz é que a empresa não registra o churn de um jeito que permita explicá-lo.** O motivo do cancelamento não tem relação com o que o cliente escreveu (p = 0,955), um quarto dos cancelamentos não deixa comentário, nenhum ticket tem hora de abertura, milhares de registros de uso e ticket têm data anterior ao cadastro da conta, e o CRM e o faturamento discordam sobre quem saiu (110 contas "canceladas" ainda pagam US$ 2,07 mi de MRR, 20% do MRR ativo).
3. **O segmento mais exposto é DevTools:** 31% das contas canceladas, contra 19% no resto da base. É a única diferença que passa no teste estatístico. Também pedem atenção as contas em trial (19% da base, 23% do churn) e cinco recursos beta com taxa de erro bem acima da versão estável.
4. **Ações, em ordem:**
   1. conciliar o CRM com o faturamento (US$ 2,07 mi de MRR em dúvida);
   2. corrigir a captura de dados, com um agente que classifica o motivo pelo texto do cliente;
   3. pôr o CS nas 72 contas com 3 sinais ou mais (US$ 1,46 mi de MRR) e nas 33 renovações anuais sem auto-renew (US$ 1,08 mi de ARR);
   4. revisar o onboarding de DevTools;
   5. montar um monitor de engajamento com um programa de retenção.

   O modelo preditivo vem por último, quando o dado deixar.

---

## 1. O que está causando o churn

### Nenhum fator isolado explica

Comparamos quem cancelou com quem ficou em cada tabela. A medida de churn por conta é o `churn_flag`: 110 de 500 contas, ou 22%.

| Fator | O que os dados mostram | Peso |
|---|---|---|
| Plano | Basic 22,0%, Pro 21,9%, Enterprise 22,1% | nenhum |
| Trial × pago | 25,8% × 21,1%. O trial é 19,4% da base e 22,7% do churn (p = 0,32) | pequeno |
| Setor | DevTools 31,0% × resto 19,4% (p = 0,009; 0,044 corrigido para 5 testes) | **o único significativo** |
| Taxa de erro da conta | Por quartil: 20,8% / 27,2% / 25,6% / 14,4%. O quartil com mais erro cancela *menos* | não vai na direção esperada |
| Adoção (recursos distintos usados) | Por quartil: 16,8% / 22,4% / 26,4% / 22,4% | não protege |
| Volume de tickets | 0–2: 25,0% · 3–4: 22,6% · 5–6: 16,9% · 7+: 27,5% | sem padrão |
| Escalação e erro alto juntos | 25,0% × 21,7% no resto (p = 0,60) | pequeno |
| País e tempo de casa | Normalizado pela exposição, a Alemanha fica igual aos EUA (D7) | nenhum |

Em análises anteriores (D3), 23 variáveis por conta separaram canceladas e ativas com AUC entre 0,45 e 0,54, e um placebo com rótulos embaralhados chegou a 0,56. Nenhum modelo treinado nesta base faz melhor que o acaso. **Isso não quer dizer que o churn é aleatório.** Quer dizer que o que o causa não está bem medido nas tabelas.

Mesmo assim, os pequenos sinais se somam. Contando quantos de sete sinais observáveis cada conta tem, a taxa de churn sobe devagar: 18,9% sem nenhum, 22,7% com 1, 23,6% com 2, 23,4% com 3 e 33,3% com 4 ou mais. Esse último grupo tem só 6 contas. O gradiente é fraco, e é coerente com a leitura de colcha de retalhos: cada retalho pesa pouco, juntos começam a desenhar um padrão.

### A causa raiz: o churn não é registrado de forma que dê para explicá-lo

A pergunta "por que o cliente sai" não tem resposta confiável na base. As evidências:

- **O motivo registrado não conversa com o que o cliente escreveu.** O cruzamento entre o `reason_code` e o comentário dá p = 0,955: as duas colunas variam de forma independente. Só 101 dos 452 comentários (22%) batem com o motivo registrado; por exemplo, "too expensive" aparece com o motivo `features` 32 vezes. Os comentários têm só três textos possíveis ("too expensive", "missing features", "switched to competitor"), então funcionam como um segundo menu, não como a voz do cliente.
- **Um quarto do churn é silencioso.** 148 dos 600 eventos (131 contas) não têm comentário nenhum. O volume é parecido com o de cada um dos três comentários (136 a 161), e nada é aprendido com ele.
- **O suporte não tem relógio.** Os 2.000 tickets foram abertos exatamente à 00:00:00. O SLA medido em horas fica sem base.
- **As datas não fecham.** 1.077 tickets e 13.198 registros de uso têm data anterior ao cadastro da própria conta, e 19.142 registros de uso são anteriores ao início da assinatura a que pertencem.
- **As tabelas discordam sobre quem saiu.** O CRM marca 110 contas como canceladas, e todas elas têm assinatura paga em aberto, somando US$ 2,07 mi de MRR. Ao mesmo tempo, 277 contas têm evento de churn e continuam marcadas como ativas. As 97 contas marcadas como trial também têm assinatura paga ativa (US$ 2,06 mi de MRR).
- **O pico de dezembro/2024 é, provavelmente, um artefato.** 103 das 193 assinaturas encerradas em dezembro nasceram e morreram dentro do próprio mês. Em toda safra, cerca de 10% das assinaturas aparecem encerradas, com a data de fim espalhada uniformemente até 31/12/2024 (D13). Antes de agir sobre esse pico, é preciso confirmar como a `end_date` é preenchida.
- **A satisfação mede o atendimento, não o produto.** A nota média da conta é a mesma com pouco ou muito erro no produto (4,00 / 3,93 / 3,96 por tercil de erro). Ela também não acompanha os tempos de resposta e resolução, só usa as notas 3, 4 e 5, e falta em 41% dos tickets. Hoje não há nenhuma medida da experiência do cliente com o produto, e esse é o ponto cego mais provável para prever quem vai sair.

O dado existe, mas está pulverizado. Cada tabela conta uma parte, e as partes não se encaixam. Essa é a causa raiz, e é por isso que a ferramenta entregue (seção 4) junta as cinco tabelas num lugar só.

---

## 2. Quais segmentos estão mais em risco

### DevTools

Com 113 contas e 35 canceladas (31,0%, contra 19,4% no resto), DevTools é o único segmento cuja diferença resiste ao teste estatístico, mesmo depois da correção para comparações múltiplas.

O curioso é que **nada nas tabelas explica a diferença**:

- a taxa de erro é igual (5,53% × 5,5 a 5,9% nos outros setores);
- a escalação é igual (4,7% dos tickets);
- a satisfação é igual (3,96);
- os tickets por conta são até menos (3,83);
- os motivos de cancelamento se dividem por igual.

O que separa DevTools está fora da base. As hipóteses mais prováveis são o encaixe do produto com um público técnico e a jornada de ativação. Daí a recomendação de revisar o onboarding desse setor.

### Contas em trial

São 19,4% da base e 22,7% do churn. Sozinha, a diferença não é significativa (p = 0,32), mas, numa causa feita de várias diferenças pequenas, ela entra na soma.

O impacto financeiro também se mede de outro jeito. Uma conta em trial vale pelo potencial, e esse potencial se estima pelo MRR médio das contas pagas com o mesmo perfil (plano, setor e assentos).

Nesta base há um obstáculo antes disso: as 97 contas marcadas como trial já têm assinatura paga ativa. O flag de trial da conta precisa ser corrigido antes de servir para essa conta.

### Fricção concentrada em alguns recursos beta

No total, o beta erra tanto quanto o estável (5,53% × 5,64%). A fricção aparece quando se olha recurso por recurso: em 18 dos 40, o beta erra mais. Em cinco deles, a diferença é grande:

| Recurso | Erro no beta | Erro no estável | Usos beta |
|---|---|---|---|
| Recurso 28 | 9,52% | 5,48% | 504 |
| Recurso 25 | 8,58% | 5,40% | 478 |
| Recurso 38 | 7,66% | 5,22% | 731 |
| Recurso 18 | 8,39% | 6,07% | 608 |
| Recurso 21 | 7,46% | 5,69% | 590 |

É um sinal de qualidade que existe e merece dono. Ainda não é um motor do churn: no nível da conta, mais erro não leva a mais cancelamento.

### Suporte

Contas com algum ticket escalado cancelam um pouco mais (25,3% × 21,3%). O suporte traz bom contexto do negócio, mas não é um motor do churn. Cruzado com a fricção de produto, nesta base, o sinal não fica mais forte: escalou e erra muito dá 25,0%, contra 21,7% no resto (p = 0,60).

A prioridade do ticket também não muda o atendimento: a resolução fica entre 34,6 h e 37,0 h em todas as prioridades (D6). Esse é um problema operacional por si só.

### Contas específicas: `solution/contas-em-risco.csv`

A lista **não é uma probabilidade de churn**: nenhum modelo nesta base faz melhor que o acaso. Ela diz onde o CS deve olhar primeiro, cruzando sinais observáveis com receita exposta. Cada linha diz quais sinais a conta tem. Os sete sinais são:

- setor DevTools;
- conta em trial;
- evento de churn nos últimos 90 dias;
- ticket escalado;
- taxa de erro no quartil mais alto;
- uso do 4º tri/2024 abaixo da metade do 3º;
- 7 tickets ou mais.

Um oitavo sinal é o aniversário de contrato anual em 90 dias sem auto-renew.

**Lista A, agir:** 72 contas ainda ativas no CRM, com 3 sinais ou mais, somando US$ 1,46 mi de MRR. As dez primeiras:

| Conta | Setor | Plano | MRR ativo | Sinais |
|---|---|---|---|---|
| Company_36 | DevTools | Pro | US$ 8.805 | 6: DevTools, trial, escalação, erro alto, renovação sem auto-renew, 7+ tickets |
| Company_191 | HealthTech | Pro | US$ 23.145 | 5: churn recente, escalação, erro alto, queda de uso, renovação sem auto-renew |
| Company_205 | DevTools | Enterprise | US$ 48.804 | 4: DevTools, trial, churn recente, erro alto |
| Company_281 | FinTech | Basic | US$ 46.912 | 4: trial, erro alto, queda de uso, 7+ tickets |
| Company_267 | DevTools | Pro | US$ 30.429 | 4: DevTools, churn recente, escalação, erro alto |
| Company_452 | Cybersecurity | Enterprise | US$ 21.666 | 4: churn recente, escalação, erro alto, 7+ tickets |
| Company_209 | DevTools | Pro | US$ 21.075 | 4: DevTools, trial, churn recente, 7+ tickets |
| Company_279 | DevTools | Pro | US$ 20.223 | 4: DevTools, churn recente, erro alto, queda de uso |
| Company_136 | EdTech | Enterprise | US$ 19.006 | 4: trial, escalação, erro alto, renovação sem auto-renew |
| Company_446 | FinTech | Pro | US$ 17.334 | 4: trial, churn recente, escalação, erro alto |

**Lista B, conciliar:** 110 contas que o CRM marca como canceladas e que o faturamento ainda cobra (US$ 2,07 mi de MRR). Antes de qualquer ação de retenção, é preciso saber qual das duas tabelas está certa.

**Renovações:** 33 contas com contrato anual que faz aniversário até 31/03/2025 sem auto-renew, somando US$ 1,08 mi de ARR. A lista está em `process-log/verification/outputs/12_renovacoes_90d_sem_autorenew.csv` (D8), e as mesmas contas estão marcadas na coluna `renova_sem_auto` do CSV.

---

## 3. O que a empresa deveria fazer

As ações estão em ordem de prioridade. As estimativas de impacto são ordens de grandeza com a conta à vista, não promessas.

| # | Ação | Dono | Prazo | Impacto estimado |
|---|---|---|---|---|
| 1 | **Conciliar o CRM com o faturamento** nas 110 contas da lista B e corrigir o flag de trial | Financeiro + RevOps | 2 semanas | Dá certeza sobre US$ 2,07 mi de MRR (20% do ativo). Se o faturamento estiver errado, a receita está superestimada nesse valor; se o CRM estiver errado, 110 contas saem da conta do churn. |
| 2 | **Corrigir a captura de dados:** hora de abertura do ticket; validação de datas (nada antes do cadastro); comentário obrigatório no cancelamento; um **agente classificador** que lê o texto do cliente e propõe o motivo | Dados + Produto | 30 dias | Não gera receita direta. É o que torna o churn explicável: hoje 78% dos motivos não batem com o comentário e 25% dos cancelamentos são silenciosos. |
| 3 | **CS nas contas da lista A e nas renovações sem auto-renew**, uma ligação por conta, começando pelas de mais sinais e mais MRR | CS | começa já, 60 dias | US$ 1,46 mi de MRR na lista A e US$ 1,08 mi de ARR nas renovações. Com o churn histórico de ~23% dessas contas, salvar um quarto delas preserva cerca de US$ 85 mil de MRR (~US$ 1 mi de ARR). |
| 4 | **Revisar o onboarding de DevTools**, começando pelas reclamações de suporte desse público e pela jornada de ativação | Produto + CS | 60–90 dias | Se o churn do setor cair ao nível do resto da base (de 31% para 19%), são ~13 contas a menos por ciclo, ~US$ 196 mil de MRR (~US$ 2,3 mi de ARR), pelo MRR médio das DevTools canceladas (US$ 15 mil). É um teto. |
| 5 | **Monitor de engajamento com programa de retenção periódico:** alerta automático para queda de uso, conta com muitos tickets, escalação e churn silencioso, com contato do CS ou do suporte antes da renovação | CS + Dados | 90 dias | Transforma a lista A em rotina. Em 90 dias, medir se as contas com alerta cancelam mais que as sem alerta e recalibrar os sinais. |
| 6 | **Levar para a ativação os recursos das assinaturas que duram mais.** Os recursos 9, 35 e 30 são 19% a 37% mais usados nas assinaturas longas que nas curtas. | Produto | 90 dias | Hipótese a testar em grupo de controle: o uso pode ser efeito da duração, não causa. |
| 7 | **Baixar o erro dos cinco recursos beta** (28, 25, 38, 18 e 21) ao nível da versão estável | Engenharia | próximo ciclo | Qualidade, não receita comprovada: o erro não prevê churn nesta base. |
| 8 | **Medir a experiência com o produto** (uma pesquisa curta dentro do produto, separada da nota do ticket) | Produto | 60 dias | Cobre o ponto cego: hoje a única nota mede o atendimento. |
| 9 | **Só então, o modelo preditivo**, treinado com o dado corrigido nos itens 1, 2 e 8 | Dados | depois de 2 trimestres de dado limpo | A ferramenta já junta as cinco tabelas e está pronta para receber o modelo. |

---

## 4. A ferramenta (opcional, já no ar)

https://ravenstack-churn.vercel.app. O login de avaliador e a senha estão na descrição do pull request.

O que a ferramenta tem:

- Uma visão geral e duas telas: o que se associa ao churn, e suporte e uso do produto. Todo gráfico mostra o SQL que o gerou.
- Drill-down em qualquer fatia, com filtros que valem para todas as telas.
- Um analista conversacional que cita o SQL de cada resposta.
- Telas próprias criadas por pergunta.
- Uma apresentação montada a partir dos gráficos marcados.

Um vídeo de 2 minutos mostra a ferramenta em uso: [assistir no Google Drive](https://drive.google.com/file/d/14ctMS_deoJNzGt1KyqubhB7UHZZSIxQn/view?usp=sharing) (cópia no repositório em `solution/demo/ravenstack-demo.mp4`).

A ideia é que o churn possa ser visto antes de acontecer. Ela só funciona com toda a capacidade quando os itens 1 e 2 forem resolvidos.

## 5. Limitações

- **Os dados são sintéticos** (o README do dataset no Kaggle declara isso). Alguns padrões parecem do gerador, e não de clientes: o pico de dezembro, um NRR de 140% a 158% e textos de comentário fixos.
- **Correlação não é causa.** O único segmento significativo (DevTools) não tem explicação dentro da base. As ações 4 e 6 são hipóteses a testar com grupo de controle.
- **Os grupos são pequenos e foram feitos muitos testes.** Com 110 contas canceladas, diferenças de 3 a 5 pontos não se distinguem do acaso. Só DevTools sobrevive à correção.
- **Os sinais da lista dependem de datas** com as inconsistências da seção 1: queda de uso e churn recente. Por isso, a lista é uma fila de atenção, não uma previsão.
- **As estimativas de impacto** usam taxas históricas desta base e premissas declaradas na tabela. Elas servem para ordenar as ações, não para orçamento.
