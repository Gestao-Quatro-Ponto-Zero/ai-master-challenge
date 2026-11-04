# Registros por etapa

Cada fase do trabalho termina com um registro neste formato, definido pelo Liberato em 04/11/2026. Há uma regra que vale para todos: **nada aqui é inventado.** O que foi sugerido pela IA e ainda não foi validado aparece separado do que o Liberato decidiu ou conferiu.

---

## Registro 00: Revisão crítica da análise inicial e início do histórico de versões (04/11/2026)

**Objetivo da etapa**
Antes de definir a lógica do score, revisar com olhar crítico a análise feita até aqui (Etapas 0 a 7 do `diario-de-bordo.md`), listar o que ainda precisa ser verificado e começar o histórico de versões no fork do Liberato.

**Ferramentas utilizadas**
- Claude (app Claude, modo agente com terminal): revisão da análise e organização dos arquivos
- git: histórico de versões, na branch `submission/liberato-gouveia` do fork
- GitHub: fork `libegouv/ai-master-challenge`, criado pelo Liberato

**Prompts relevantes** (escritos pelo Liberato, transcritos sem edição)
> "Estamos desenvolvendo o Challenge 003 — Lead Scorer do processo seletivo G4 AI Master. Vou utilizar você (Claude) integrado ao Lovable para construir a aplicação. A partir de agora, quero trabalhar com uma metodologia controlada, transparente e documentada.
> REGRAS DE TRABALHO
> 1. Não avance automaticamente por várias etapas. Antes de executar uma nova fase importante, apresente o plano e aguarde minha autorização.
> 2. Utilize linguagem simples. Quando houver termos técnicos, explique brevemente o significado.
> 3. Antes de gerar código, vamos compreender o problema, analisar os dados e definir a lógica de priorização.
> 4. Ao final de cada etapa, gere um pequeno registro para meu Process Log [...]
> 5. Nunca invente decisões humanas, testes, erros, resultados ou evidências. Identifique claramente o que foi sugerido pela IA e o que foi efetivamente validado por mim.
> 6. Antes de utilizar o Lovable para criar ou modificar a aplicação, explique o que será desenvolvido e por quê.
> 7. Utilize os dados reais do desafio e evite vazamento de informações futuras na lógica de scoring.
> 8. Priorize uma solução funcional, intuitiva e explicável, respeitando a recomendação de 4 a 6 horas de esforço do G4.
> 9. Não faça a submissão final ou abra um Pull Request sem minha autorização.
> [...] Agora, revise a análise inicial que você já realizou, identifique o que ainda precisa ser verificado e apresente somente a primeira etapa do plano. Não inicie a implementação ainda."

**Resultados obtidos**
- O histórico de versões começou: branch `submission/liberato-gouveia`, pasta `submissions/liberato-gouveia/`, primeiro registro salvo no commit `f9d7a75`. Por enquanto ele existe só no ambiente do Claude. Nada foi enviado ao GitHub.
- A revisão separou o que já está sólido do que ainda precisa de verificação:
  - **Sólido:** os dados batem com o README do case. Produto, setor, região, gerente, vendedor e empresa não preveem o resultado, e três métodos diferentes concordam nisso. Nenhum deal fechado levou mais de 138 dias.
  - **A verificar (8 itens):** estão listados na proposta da Fase 1, no fim deste registro.

**Decisões que realmente tomei (Liberato)**
- Confirmei que a versão 2 do diário ficou clara.
- Autorizei o início do histórico de versões.
- Criei o fork `libegouv/ai-master-challenge`.
- Defini as 9 regras de trabalho acima.
- Decidi construir a aplicação com o Claude integrado ao Lovable.

**Sugestões da IA ainda não validadas por mim**
- A divisão em fases e o conteúdo da Fase 1 proposta abaixo.
- Manter o cálculo do score num script separado e testável, com o Lovable cuidando só da tela. Isso vai ser apresentado antes da fase de construção.

**Erros encontrados e correções**

| Erro | Quem encontrou | Correção |
|---|---|---|
| O diário apresentava as 3 "regras de vendas" e as escolhas da Etapa 7 como contribuições do Liberato, mas as opções foram **formuladas pela IA**. Ele selecionou entre elas. | Claude, na revisão pedida pelo Liberato | **Corrigido:** as Etapas 1 e 7 do diário agora dizem quem sugeriu e quem escolheu. A versão anterior está em `versoes/diario-de-bordo_v2_2026-11-04.md`. |
| O Gráfico 3 agrupa os deals pela **duração total**, um dado que só existe depois que o deal termina. Usar isso na nota de um deal aberto seria "vazamento de futuro", ou seja, usar uma informação que ninguém teria no momento da decisão. | Claude, na revisão | **Pendente:** item A da Fase 1. |
| O diário dá a entender que tempo e valor pesam parecido. Os números já calculados (`analises/resultados/eda3.txt`) mostram que, para um deal ainda vivo, a idade muda a chance de fechar só de ~61% para ~70%. O efeito forte do tempo é o limite de 138 dias. | Claude, na revisão | **Pendente:** corrigir o texto do diário depois da Fase 1. |
| O `.gitignore` do repositório do G4 manda ignorar a pasta `submissions/`. Seguindo o passo a passo do CONTRIBUTING ao pé da letra, a entrega não seria salva. | Claude, ao criar o primeiro registro | **Resolvido:** os arquivos foram adicionados com `git add -f`, sem alterar nenhum arquivo fora da nossa pasta (regra do G4). |

**Testes ou evidências disponíveis**
- Commit `f9d7a75` (registro inicial) e o commit desta etapa
- `versoes/diario-de-bordo_v2_2026-11-04.md`: o diário antes da correção de atribuição
- `analises/resultados/eda3.txt`: chance de ganhar para deals que continuam vivos depois de X dias (números usados na revisão)

**Tempo aproximado**
Não informado pelo Liberato.

---

## Proposta: Fase 1, Verificação da análise (autorizada pelo Liberato em 04/11/2026 às 18:08; resultado no Registro 02)

**Objetivo:** confirmar ou corrigir cada conclusão antes de definir a lógica do score. Esta fase não tem código da ferramenta, não usa o Lovable e não envia nada ao GitHub.

| # | O que verificar | Por que importa |
|---|---|---|
| A | Refazer a "chance de fechar" usando só o que se sabe **hoje** sobre um deal aberto: a idade dele. A pergunta é: "dos deals que chegaram vivos a X dias, quantos foram ganhos?" | Evita vazamento de futuro. Essa tabela vira a base oficial da nota. |
| B | Checar se o limite de 138 dias é real ou se é efeito da janela da base, olhando por mês de início: deals que começaram em março tiveram até ~300 dias para fechar. | Se o limite não se sustentar, a regra dos zumbis muda. |
| C | Ajustar a linguagem sobre os zumbis: os dados dizem "nunca houve fechamento depois de 138 dias", não "o deal está morto". | Não afirmar mais do que os dados mostram. |
| D | Contar quantos deals **vivos** não têm empresa cadastrada antes de aplicar a regra "sem conta = sem dono". | 68% dos abertos não têm empresa. A regra pode esvaziar a lista de foco. |
| E | Deals em prospecção (500): confirmar que não existe dado nenhum para estimar a chance deles. | Para não inventar uma probabilidade. |
| F | Repetir o teste de machine learning separando por **tempo**: treinar com os deals mais antigos e testar com os mais novos, como na vida real. | É uma prova mais rigorosa contra vazamento de futuro. |
| G | Investigar o padrão de fim de trimestre (meses 3, 6, 9 e 12 têm ~80% de ganho, contra ~50% nos outros meses). | Um avaliador pode perguntar sobre isso. Precisamos saber se é útil sem vazamento ou se é só um efeito da base. |
| H | (Opcional, depende do Liberato) Comparar os nossos dados com o arquivo oficial do Kaggle. | Fecha a única dúvida que ainda existe sobre a origem dos dados. |

**Entregas da Fase 1:** o resultado de cada item (confirmado ou corrigido), a tabela oficial de chance por idade, o diário corrigido, o registro da fase neste arquivo e o commit.

**Decisões que vão ficar para o Liberato ao final:** como tratar deals sem empresa cadastrada (depende do item D), como tratar deals em prospecção (item E) e se o padrão de fim de trimestre entra ou não (item G).

---

## Registro 01: Preparação do ambiente e organização da entrega (04/11/2026)

**Objetivo da etapa**
Preparar o GitHub para a entrega, criando a branch de submissão no fork, e obter o arquivo oficial dos dados no Kaggle. Nesta etapa não houve implementação de código nem teste da aplicação.

**Ferramentas utilizadas**
- GitHub (interface web): criação da branch, feita pelo Liberato
- ChatGPT: orientou passo a passo a criação da branch (segundo o Liberato)
- Kaggle: download do arquivo oficial dos dados, feito pelo Liberato
- Claude: conferiu no GitHub que a branch existe (comando `git ls-remote`, que lista as branches de um repositório)

**Prompts relevantes**
Texto que o Liberato colou na conversa com o Claude, identificado por ele como "prompt do chatgpt" (transcrito sem edição):
> "Atualize meu Process Log do Challenge 003 — Lead Scorer do G4 AI Master. Em 04/11/2026, concluí a criação da branch `submission/liberato-gouveia` no meu Fork do GitHub: https://github.com/libegouv/ai-master-challenge. A branch foi criada a partir da `main`, e o GitHub confirmou que está sincronizada com a branch principal do repositório original do G4. Realizei essa etapa manualmente, seguindo as orientações passo a passo do ChatGPT. Registre essa atividade como preparação do ambiente de desenvolvimento e organização da entrega. Não registre implementação de código ou testes da aplicação, pois essas etapas ainda não aconteceram. Após atualizar o diário, apresente o trecho registrado e aguarde minha autorização para continuar."

A conversa com o ChatGPT que orientou a criação da branch não faz parte deste registro (ver Evidências).

**Resultados obtidos**
- A branch `submission/liberato-gouveia` existe no fork `libegouv/ai-master-challenge`.
- Ela aponta para a versão `4aed364`, a mesma da `main` do fork e da `main` do repositório original do G4. O Claude conferiu, e isso confirma o que o GitHub informou ao Liberato.
- O arquivo oficial do Kaggle (`archive.zip`, com 5 arquivos) foi baixado pelo Liberato e enviado na conversa. A comparação com os nossos dados está no Registro 02, item H.

**Decisões que realmente tomei (Liberato)**
- Criei a branch `submission/liberato-gouveia` manualmente, a partir da `main`, seguindo a orientação do ChatGPT.
- Baixei os dados oficiais no Kaggle e enviei ao Claude para comparação.

**Sugestões da IA ainda não validadas por mim**
- Nenhuma nesta etapa.
- Observação técnica: o histórico de versões que o Claude mantém (Registro 00) partiu do mesmo ponto (`4aed364`). Quando o envio for autorizado, ele entra nesta branch sem conflito. Nada foi enviado ao GitHub até agora.

**Erros encontrados e correções**
Nenhum erro foi relatado pelo Liberato nesta etapa.

**Validação do Liberato:** em 04/11 às 19:31 ele confirmou: "sim, o registro 01 está correto".

**Testes ou evidências disponíveis**
- `analises/resultados/registro01_branch_github.txt`: saída da conferência da branch no GitHub
- Prints da conversa com o ChatGPT: **pendente**, se o Liberato quiser anexar

**Tempo aproximado**
Cerca de 3 horas acumuladas no challenge até 04/11/2026 às 18:08, segundo o Liberato. O número inclui todas as etapas feitas até aqui, não só esta.

---

## Registro 02: Fase 1, Verificação da análise (04/11/2026)

**Objetivo da etapa**
Confirmar ou corrigir cada conclusão da análise inicial antes de definir a lógica do score, usando só informações que existem no momento da decisão (sem vazamento de futuro). Nesta etapa não houve código da ferramenta nem uso do Lovable.

**Ferramentas utilizadas**
- Claude (Python com as bibliotecas pandas, scikit-learn e matplotlib): verificações e gráfico
- Arquivo oficial do Kaggle, enviado pelo Liberato
- git: histórico de versões

**Prompts relevantes** (escritos pelo Liberato, transcritos sem edição)
> "1. autorizo a fase 1
> 2. vou mandar o arquivo que eu baixei e documente isso
> 3. ja estou trabalhando nisso tem umas 3 horas"

**Resultados obtidos**

| # | Verificação | Resultado |
|---|---|---|
| A | Chance de ser ganho usando só a **idade atual** do deal (safra mar–jun/2017, acompanhada por pelo menos 184 dias) | **Cai com a idade:** 53% (novo), 52% (14 dias), 48% (60 dias), 37% (90 dias), 5% (120 dias), 0% (138 dias). Isso **inverte** a conclusão da análise inicial (Gráfico 6). |
| B | O limite de 138 dias é real? | **Sim.** Em todas as safras, até nas que tiveram 300 a 450 dias para fechar, o maior ciclo ficou entre 119 e 138 dias. Nenhum dos 6.711 deals fechados passou de 138. |
| C | Linguagem sobre os "zumbis" | **Ajustada.** O diário agora diz "nunca houve fechamento depois de 138 dias; não sabemos o destino real", em vez de "deals mortos". |
| D | Deals sem empresa cadastrada | **Nenhum dos 6.711 deals fechados está sem empresa.** Entre os 298 deals vivos (até 138 dias), 209 (70%) não têm. A proporção é parecida em todas as idades (61–79%) e varia por vendedor (50–90%). Hipótese: a empresa só é preenchida no fechamento, ou a base foi gerada assim. Não dá para dizer que um deal sem empresa é pior. |
| E | Deals em prospecção (500, US$ 1,07 milhão em preço de tabela) | **Não há nenhum dado para estimar a chance deles.** Nenhum deal em prospecção tem data de início, e todos os deals fechados têm, então a base não guarda nenhum histórico de quantos deals saem da prospecção nem de quanto tempo isso leva. Qualquer % seria inventado. |
| F | Machine learning separando por tempo (treina com deals iniciados até 16/08/2017 e testa com os posteriores) | **AUC 0,48 e 0,52.** Equivale a cara ou coroa e confirma, de forma mais rigorosa, que as características do deal não preveem o resultado. |
| G | Padrão de fim de trimestre | **É real, mas não pode entrar na nota.** 49% dos ganhos são registrados em mar/jun/set/dez, contra só 20% das perdas. O padrão depende da data de fechamento, que é informação futura. O mês de início, que é conhecido no começo, também varia, mas as safras das pontas são distorcidas pelo período coberto pela base. |
| H | Dados x arquivo oficial do Kaggle | **Idênticos byte a byte** nos 5 arquivos (impressão digital MD5 igual). O arquivo oficial também tem o erro "GTXPro" em 1.480 linhas. |

Outro número que importa para a tela: só **298 deals estão vivos em negociação**, espalhados por 21 vendedores (média de 14 por vendedor, variando de 1 a 31). Os outros 9 vendedores com pipeline aberto têm só deals fora do padrão ou em prospecção.

**Decisões que realmente tomei (Liberato)**
- Autorizei a Fase 1.
- Baixei e enviei o arquivo oficial do Kaggle.

**Sugestões da IA ainda não validadas por mim** (aguardam decisão do Liberato)
1. **"Janela de ouro (14 a 138 dias)":** os dados não sustentam essa regra (item A). A sugestão é retirá-la, porque a curva de chance por idade já entra na nota.
2. **"Sem conta = sem dono":** aplicada como está, tiraria 70% dos deals vivos da lista de foco (item D). A sugestão é manter esses deals na lista, com o aviso "cadastrar empresa".
3. **Prospecção:** a sugestão é uma lista separada, "Iniciar contato", ordenada só pelo valor e **sem % de chance**, porque não há dado para estimar (item E).
4. **Fim de trimestre:** a sugestão é não usar na nota (exige informação futura) e citar como observação no README (item G).

**Erros encontrados e correções**

| Erro | Quem encontrou | Correção |
|---|---|---|
| A análise inicial concluiu que "deal com mais de 14 dias fecha mais (65–75%)". A conta ignorava os deals que nunca fecham e usava a duração total (vazamento de futuro). | Claude, na revisão crítica (Registro 00), motivado pela regra 7 do Liberato. Confirmado na Fase 1. | **Corrigido:** a Etapa 5 do diário foi reescrita com o Gráfico 6. O Gráfico 3 ficou como registro histórico, e a versão anterior está em `versoes/diario-de-bordo_v3_2026-11-04.md`. |
| A regra "janela de ouro", sugerida pelo Claude e selecionada pelo Liberato, não se sustenta nos dados. | Claude, na Fase 1 (item A) | **Pendente:** decisão do Liberato (sugestão 1). |
| A regra "sem conta = sem dono", sugerida pelo Claude e selecionada pelo Liberato, esvaziaria a lista de foco. | Claude, na Fase 1 (item D) | **Pendente:** decisão do Liberato (sugestão 2). |
| O diário chamava os deals antigos de "mortos", afirmando mais do que os dados mostram. | Claude, na revisão crítica | **Corrigido** (item C). |

**Testes ou evidências disponíveis**
- `analises/fase1_verificacao.py` e a saída em `analises/resultados/fase1_verificacao.txt` (itens A, B, D, E, F e G)
- `analises/resultados/fase1_item_H_kaggle.txt`: comparação com o arquivo do Kaggle
- `graficos/grafico6_chance_por_idade.png`: o novo gráfico, gerado por `analises/graficos.py`. Os 5 gráficos anteriores foram regerados e continuaram idênticos.
- `versoes/diario-de-bordo_v3_2026-11-04.md`: o diário antes das correções desta fase

**Tempo aproximado**
Não informado para esta fase. O Liberato informou cerca de 3 horas acumuladas até o início dela.

---

## Registro 03: Decisões do Liberato depois da Fase 1 (04/11/2026, 19:18)

**Objetivo da etapa**
Registrar as decisões do Liberato sobre as 4 sugestões que saíram da Fase 1. Nesta etapa não houve código nem análise nova.

**Ferramentas utilizadas**
- Conversa com o Claude

**Prompts relevantes** (escritos pelo Liberato, transcritos sem edição)
> "1. sim tire
> 2. mantenha
> 3. faça a lista separada
> 4. ok faça"

**Resultados obtidos**
As decisões abaixo passam a valer para a lógica do score, que é a Fase 2.

**Decisões que realmente tomei (Liberato)**

| # | Tema | Decisão |
|---|---|---|
| 1 | Regra "janela de ouro (14 a 138 dias)" | **Retirar.** A chance por idade (Gráfico 6) já entra na nota. |
| 2 | Deals sem empresa cadastrada | Resposta: "mantenha". **Interpretação do Claude:** manter esses deals na lista de foco, com o aviso "cadastrar empresa", conforme a sugestão 2 do Registro 02. **Confirmada pelo Liberato em 04/11 às 19:31:** "confirmo a interpretação da decisao 2". |
| 3 | Deals em prospecção (500) | **Lista separada**, ordenada só por valor e sem % de chance. |
| 4 | Padrão de fim de trimestre | **Não usar na nota** (exige informação futura) e citar como observação no README. |

Para ficar registrado: as 4 decisões aceitaram sugestões que foram formuladas pela IA no Registro 02.

**Sugestões da IA ainda não validadas por mim**
- Nenhuma pendente. A interpretação da decisão 2 foi confirmada em 04/11 às 19:31, e o plano da Fase 2 foi autorizado no mesmo horário.

**Erros encontrados e correções**
Nenhum nesta etapa.

**Testes ou evidências disponíveis**
- Este registro e o commit correspondente

**Tempo aproximado**
Não informado.

---

## Proposta: Fase 2, Lógica do score (autorizada pelo Liberato em 04/11/2026 às 19:31; resultado no Registro 04)

**Objetivo:** definir e testar, nos dados reais, como a ferramenta vai priorizar os deals, **antes de construir qualquer tela.** Esta fase não usa o Lovable nem envia nada ao GitHub. Os cálculos rodam num script de análise, que ainda não é a ferramenta.

**Rascunho da lógica (sugerido pela IA, para o Liberato aprovar ou ajustar)**

| Lista | Quais deals entram | Como são ordenados | Ação sugerida na tela |
|---|---|---|---|
| **1. Foco** | Em negociação, com até 138 dias e valor acima do mínimo | **Valor esperado = chance pela idade (Gráfico 6) × preço de tabela** | "Avançar este deal", com o motivo explicado. Se não houver empresa cadastrada, mostra o aviso "cadastrar empresa". |
| **2. Requalificar ou encerrar** | Em negociação há mais de 138 dias | Valor | Deal grande: "ligar para requalificar". Deal pequeno: "encerrar no CRM". |
| **3. Iniciar contato** | Em prospecção | Só pelo valor, sem % de chance | "Fazer o primeiro contato" |
| **4. Automatizar** | Em negociação, com até 138 dias e valor abaixo do mínimo | Valor esperado | "Incluir na cadência automática" |

Cada deal mostra o seu "porquê" em linguagem simples. Exemplo: *"Valor esperado US$ 2.410 = US$ 4.821 (preço do GTX Pro) × 50% (chance de um deal com 32 dias)"*.

Os limites ficam como **configuração**, nunca escritos no código com nome de produto. São eles: o valor mínimo para entrar no foco, o valor que define "deal grande" na requalificação e o limite de 138 dias.

**O que será feito nesta fase**
1. **Ficha da lógica:** 1 página em linguagem simples com as 4 listas, a fórmula, os textos de "porquê" e de ação e os parâmetros.
2. **Curva oficial de chance por idade:** a mesma conta do Gráfico 6, em faixas mais finas, para ser usada na nota.
3. **Simulação nos dados reais:** quantos deals caem em cada lista e o top 5 de um vendedor de exemplo, com o "porquê".
4. **Teste de volta no tempo (backtest):** fingir que hoje é 30/09/2017, montar a lógica só com dados até essa data e conferir o que aconteceu de fato até 31/12/2017. O resultado será comparado com duas alternativas: (a) ordenar só pelo valor e (b) uma lógica "óbvia" baseada em produto e setor, parecida com o que uma IA faria sozinha. Isso mostra, com números, se a nossa lógica é melhor.
5. **Registro 04** no formato do Liberato e commit.

**Decisões que vão ficar para o Liberato ao final:** aprovar a lógica, os valores dos limites (mínimo do foco e "deal grande") e o formato da nota (valor esperado em US$, nota de 0 a 100 ou os dois).

---

## Registro 04: Fase 2, Lógica do score (04/11/2026)

**Objetivo da etapa**
Definir e testar nos dados reais como a ferramenta vai priorizar os deals, antes de construir qualquer tela. Nesta etapa não houve tela, uso do Lovable nem envio ao GitHub.

**Ferramentas utilizadas**
- Claude (Python com pandas, numpy e matplotlib): curva de chance, simulação, teste de volta no tempo e gráfico
- git: histórico de versões

**Prompts relevantes** (escritos pelo Liberato, transcritos sem edição)
> "1. sim
> 2. confirmo a interpretação da decisao 2
> 3. sim, o registro 01 está correto
>
> tudo isso deve ser documentado no documento de log para ser apresentado ao G4"

**Resultados obtidos**
1. **Ficha da lógica** em `docs/ficha-da-logica.md`: as 4 listas, a fórmula, os textos que o vendedor lê e os parâmetros.
2. **Curva oficial de chance pela idade**, dia a dia (`analises/resultados/fase2_curva_chance.csv`): 47% para um deal novo, 42% aos 30 dias, 39% aos 60, 26% aos 90, 5% aos 120 e 0% aos 138.
3. **Simulação em 31/12/2017**, com os limites provisórios: Foco com 236 deals (165 sem empresa), Requalificar ou encerrar com 1.291 (766 "ligar" e 525 "encerrar"), Iniciar contato com 500 e Automatizar com 62. Cada vendedor com deals no Foco tem, em média, 12. O top 5 de um vendedor de exemplo saiu com o "porquê" de cada deal (`analises/resultados/fase2_resultados.txt`).
4. **Teste de volta no tempo** (Gráfico 7): com dados só até 30/09/2017, os 20% de deals com maior nota na nossa lógica concentravam **68%** da receita ganha em out–dez. As alternativas ficaram em 47% (só valor), 49% ("óbvia" × valor) e 15% ("óbvia" sem valor). Nenhum deal fora do padrão entrou no nosso top 20%; nas alternativas, foram de 21% a 24%.

**Decisões que realmente tomei (Liberato)**
- Autorizei a Fase 2.
- Confirmei a interpretação da decisão 2 (deals sem empresa ficam no Foco, com aviso).
- Confirmei que o Registro 01 está correto.
- Pedi que tudo fosse documentado no log para ser apresentado ao G4.

**Sugestões da IA ainda não validadas por mim**
- A lógica inteira descrita na ficha.
- Os limites provisórios: valor mínimo do Foco de US$ 100 e "deal grande" de US$ 1.000.
- O formato da nota: em US$, de 0 a 100 ou os dois.
- Usar na curva o período mais recente possível (mar–ago/2017), e não o do Gráfico 6 (mar–jun/2017).
- Mostrar o aviso "cadastrar empresa" também nas listas 2, 3 e 4.

**Erros encontrados e correções**

| Erro | Quem encontrou | Correção |
|---|---|---|
| **Vazamento no próprio teste de volta no tempo.** A primeira versão do script usava o limite de 138 dias calculado com dados até 31/12, mas o teste "finge" que hoje é 30/09. | Claude, durante a fase, antes de mostrar o resultado | **Corrigido:** o limite agora é calculado só com o que se sabia em cada data. Com dados até 30/09, ele também dá 138 dias, então o resultado não mudou, mas o teste ficou correto. A versão com o erro está em `versoes/fase2_logica_v1_com_vazamento.py`. |
| **Números diferentes entre o Gráfico 6 e a curva oficial.** Para um deal novo, a curva oficial dá 47% e o Gráfico 6 dá 53%. A causa: os deals iniciados em jul–ago/2017 terminaram sem fechar cerca de duas vezes mais do que os de mar–jun (32–34% contra 14–19%, ver `fase1_verificacao.txt`, item B). | Claude, durante a fase | **Documentado:** a ordem dos deals praticamente não muda entre as duas curvas (correlação 0,997). Ficou registrado como limitação na ficha e no diário. Qual período usar é uma decisão pendente. |

**Testes ou evidências disponíveis**
- `analises/fase2_logica.py` e as saídas `analises/resultados/fase2_resultados.txt`, `fase2_curva_chance.csv`, `fase2_backtest.csv` e `fase2_deals_classificados.csv`
- `graficos/grafico7_backtest.png`
- `docs/ficha-da-logica.md`
- `versoes/fase2_logica_v1_com_vazamento.py` e `versoes/diario-de-bordo_v4_2026-11-04.md`

**Tempo aproximado**
Não informado para esta fase. O Liberato informou cerca de 3 horas acumuladas até 18:08.

---

## Registro 05: Aprovação da lógica e dos parâmetros (04/11/2026, 20:00)

**Objetivo da etapa**
Registrar as decisões do Liberato sobre a lógica proposta na Fase 2. Nesta etapa não houve código novo nem tela.

**Ferramentas utilizadas**
- Conversa com o Claude, com perguntas de múltipla escolha

**Prompts relevantes** (escritos pelo Liberato, transcritos sem edição)
> "o que eu preciso responder?"

Esse foi o retorno do Liberato à lista de 5 decisões escritas em texto corrido no fim do Registro 04. O Claude reorganizou as decisões em 4 perguntas de múltipla escolha (juntou "aprovar a lógica" e "período da curva" numa só), e o Liberato respondeu selecionando opções.

**Resultados obtidos**
A lógica foi aprovada. A ficha `docs/ficha-da-logica.md` foi atualizada com o status "aprovada", os valores escolhidos e o formato da nota. A simulação foi rodada de novo com a configuração aprovada: na lista 2, ficaram 350 deals para "ligar para requalificar" e 941 para "encerrar no CRM".

**Decisões que realmente tomei (Liberato)**

| Pergunta | Opção selecionada |
|---|---|
| Lógica da ficha, com a curva do período mais recente (mar–ago/2017) | "Aprovo (Recomendado)" |
| Preço mínimo para a lista Foco | "US$ 100 (Recomendado)" |
| "Deal grande", que ganha ligação antes de ser encerrado | "US$ 4.000 (Recomendado)" |
| Formato da nota | "Os dois (Recomendado)": 0 a 100 + valor em US$ no "porquê" |

Para ficar registrado: em todas as 4 perguntas, o Liberato escolheu a opção que a IA tinha marcado como recomendada.

**Sugestões da IA ainda não validadas por mim**
- Mostrar o aviso "cadastrar empresa" também nas listas 2, 3 e 4.
- O plano da Fase 3, mais abaixo.

**Erros encontrados e correções**

| Erro | Quem encontrou | Correção |
|---|---|---|
| As 5 decisões do fim do Registro 04 foram apresentadas em texto corrido, e o Liberato não entendeu o que precisava responder. | Liberato ("o que eu preciso responder?") | **Corrigido:** as decisões viraram 4 perguntas de múltipla escolha, com o impacto de cada opção. |

**Testes ou evidências disponíveis**
- `docs/ficha-da-logica.md` (aprovada) e `versoes/ficha-da-logica_v1_proposta.md` (a versão anterior)
- `analises/resultados/fase2_resultados.txt`, rodado de novo com a configuração aprovada. A primeira execução, com o limite provisório de US$ 1.000, gerou 766 "ligar" e 525 "encerrar" e está descrita no Registro 04.

**Tempo aproximado**
Não informado para esta etapa.

---

## Proposta: Fase 3, Construção da ferramenta (aguardando autorização)

**Objetivo:** construir a ferramenta funcionando. O vendedor abre, escolhe o próprio nome e vê onde focar, com o motivo de cada deal.

**Arquitetura sugerida pela IA: duas partes separadas**
1. **Motor do score (Python, feito pelo Claude):** um programa que lê os 4 arquivos de dados e um arquivo de configuração com os limites aprovados, e gera um arquivo com todos os deals abertos já classificados, com nota e "porquê". Ele vem com **testes automáticos**, que são verificações que rodam sozinhas a cada execução. Por exemplo: nenhum deal com mais de 138 dias no Foco; as 4 listas somam exatamente os 2.089 deals abertos; os números batem com a ficha aprovada; e o motor não usa data nem valor de fechamento para dar nota a um deal aberto.
2. **Tela (Lovable):** um app web que **só mostra** o arquivo gerado pelo motor. Nenhum cálculo fica dentro do Lovable.

**Por que separar:** a conta fica num lugar só, testada e fácil de auditar, e o avaliador pode rodar o motor e conferir. O agente de IA do Lovable não consegue alterar a fórmula sem querer. E se a lógica mudar, basta rodar o motor de novo.

**O que o Lovable vai construir (1 tela, em português):**
- Seletor de vendedor, mais filtros de gerente e região para a visão do gerente
- Um resumo no topo, por exemplo: "Hoje: X deals no Foco, Y para requalificar…"
- 4 abas, uma para cada lista. Cada deal mostra o produto, a empresa (ou o aviso), a idade, a nota de 0 a 100, a ação sugerida e o "porquê" com a conta em US$
- Uma aba "Como a nota funciona", com uma explicação curta e o resultado do teste de volta no tempo
- Sem login e sem banco de dados: os dados vêm de um arquivo. É mais simples e não tem custo extra
- Publicação com link público

**Passos (com paradas para aprovação):**
- **3a.** Construir e testar o motor, ainda sem Lovable. Resultado apresentado ao Liberato.
- **3b.** Mostrar ao Liberato o prompt exato que será enviado ao Lovable, para aprovação. Esse prompt vira evidência no log.
- **3c.** Criar o projeto no workspace "Liberato's Lovable" (o único da conta, plano Pro), enviar os dados e o prompt, com no máximo 3 mensagens de ajuste.
- **3d.** Conferir a tela: comparar os números da tela com os do motor (por exemplo, o top 5 do vendedor Zane Levy) e tirar prints para o log.
- **3e.** Copiar o código do Lovable para `solution/app/` e o motor para `solution/motor/`, escrever o Registro 06 e fazer o commit.

**Fora da Fase 3:** o README final, o envio ao GitHub e o Pull Request. Isso fica para a Fase 4, sempre com autorização do Liberato.

**Custo:** cada mensagem enviada ao Lovable consome créditos do workspace do Liberato. A meta é 1 mensagem de criação e no máximo 3 de ajuste.

**Decisões antes de começar:** aprovar a arquitetura, autorizar o gasto de créditos no Lovable e decidir sobre o aviso "cadastrar empresa" nas listas 2, 3 e 4.
