# Sessão 01 — Escolha do desafio

- **Data:** 2026-10-22, início 16:38 UTC
- **Ferramenta:** Claude Code (modelo Claude Opus 5.5), terminal no Windows
- **Pergunta que abriu a sessão:** "vou fazer o teste aqui [repo] — avalie qual agregaria mais valor"
- **Resultado:** escolhido o **Challenge 003 — Lead Scorer**, com base em medição dos 5 datasets, não na leitura dos READMEs

## O que foi feito, em ordem

1. **Leitura do repositório inteiro antes de qualquer opinião.** O Claude clonou o fork, leu o README raiz, o índice, o guia de submissão, o CONTRIBUTING, o template e os 4 READMEs de desafio.
2. **Decisão de não escolher pelo texto.** Os quatro briefs parecem equivalentes no papel. O que muda o valor de cada um é se o dado tem sinal. Por isso, antes de recomendar, baixamos os 5 datasets do Kaggle (API pública de download) e rodamos uma medição rápida de sinal em cada um: `scripts/sinal_datasets.py`, com a saída em `evidencias/sinal-datasets.txt`.
3. **Medição** (números da saída do script):

| Desafio | O que a medição mostrou | Leitura |
|---|---|---|
| 004 Social | Views de 9.676 a 10.551 nos 52.214 posts (praticamente constante). Correlação seguidores×views = 0,005 e likes×views = 0,001. Patrocinado 10.100 views, orgânico 10.100. | Dado sintético sem sinal. Qualquer "insight" seria inventado. |
| 002 Suporte | O dataset tem **8.469** tickets, não os ~30 mil do brief. A satisfação se distribui 20% em cada nota de 1 a 5 e não varia por canal, prioridade ou tipo (2,95 a 3,08). 100% das descrições trazem o placeholder `{product_purchased}` sem preencher. | Sem sinal no diagnóstico. Só o dataset 2 (classificação de TI, 47.837 textos) é aproveitável. |
| 001 Churn | Satisfação, uso e erros quase iguais entre contas que churnaram e as que ficaram (satisfação 4,00 × 3,95; erros 28,2 × 28,2). Há diferença por canal de aquisição (event 30% × partner 15%), setor (DevTools 31%) e país (DE 32%), mas com n = 500. | Sinal fraco e talvez estatisticamente frágil (não testado). |
| 003 Lead Scorer | Win rate de 55% a 70% por vendedor e de 53% a 75% por conta. Deals perdidos morrem cedo (mediana de 14 dias, contra 57 dos ganhos). 2.089 deals abertos para pontuar. | Único com sinal real e com um usuário claro (o vendedor). |

4. **Escolha: 003.** Os motivos:
   - É o único dataset com sinal medido.
   - O entregável é software rodando, onde a distância para o "colei o brief na IA" é maior.
   - Tenho experiência prática com operação comercial (cadência de follow-up e priorização de pipeline), que é o contexto humano que o baseline não tem.
5. **Riscos do 003 levantados antes de construir** (viram critérios de aceite):
   - **Viés no tempo de pipeline:** entre os fechados, mais tempo parece "ganhar mais", mas isso acontece porque os perdidos morrem cedo. Para deal aberto, o sinal certo é a idade comparada ao padrão dos ganhos, não "mais tempo = melhor".
   - **"Hoje" do dataset:** os dados vão até 2017-12-31. A idade dos deals abertos é calculada contra essa data, não contra a data real.
   - **Lacunas:** 1.425 deals sem conta e 500 sem `engage_date` (provavelmente os em Prospecting; a conferir na construção). Vão como limitação declarada.
6. **Alternativa considerada e descartada:** fazer o 002 com a tese "provei que o dataset é ruído + classificador no dataset que presta". Mostra julgamento, mas arrisca ser lido como "não entregou o diagnóstico". Aposta pior que o 003.

## Onde desconfiei e conferi

- **O brief do 002 diz ~30 mil tickets; o arquivo tem 8.469.** Só apareceu porque medimos em vez de confiar no README.
- **Ambiente:** o Python local estava corrompido (sem a biblioteca padrão). Em vez de "consertar" a máquina, rodamos isolado com `uv` (Python 3.12 + pandas 3.1.0 fixado), o que deixa a medição reproduzível. Uma primeira tentativa com pandas 2.2.3 quebrou num `min()` de coluna com nulos, e por isso a versão ficou fixada na 3.1.0.
- **Guarda de processo:** o ambiente tem um hook que exige declarar objetivo, alternativas e reversibilidade antes do primeiro comando e da primeira escrita de cada arquivo. Ele foi respeitado (a leitura do repo e a medição são locais e reversíveis).

## Como reproduzir

```bash
# baixar (API pública do Kaggle; funcionou sem login em 2026-10-22)
for ds in agungpambudi/crm-sales-predictive-analytics rivalytics/saas-subscription-and-churn-analytics-dataset \
          suraj520/customer-support-ticket-dataset omenkj/social-media-sponsorship-and-engagement-dataset \
          adisongoh/it-service-ticket-classification-dataset; do
  n=$(basename $ds); curl -sL -o "$n.zip" "https://www.kaggle.com/api/v1/datasets/download/$ds" && unzip -oq "$n.zip" -d "$n"
done
uv run --no-project --python 3.12 --with pandas==3.1.0 python -X utf8 process-log/scripts/sinal_datasets.py <pasta-dos-dados>
```

## Gestão de contexto ao fim da sessão

Depois de escolhido o desafio, a análise dos outros três vira ruído para a construção do 003. Antes de seguir:

1. Tudo o que só existia na conversa foi gravado em arquivo: este log, a saída da medição e o script.
2. A sessão é fechada e a transcrição passa por uma limpeza com o **Jev (TypeSafe)**. O Jev julga, chamada por chamada, se o retorno de uma ferramenta (leitura de arquivo, saída de comando, retorno de hook) ainda é relevante para o trabalho em andamento. O que não é vira um marcador curto. Ficam as mensagens, as decisões e as respostas.
3. A sessão é retomada com um resumo anexado que aponta para estes arquivos.

O motivo é manter a atenção do modelo no que importa para o 003 (o pipeline de vendas), sem milhares de linhas de READMEs e tabelas dos outros desafios competindo por contexto.

**Rodada r1 (plano aprovado antes do corte):**
- 80 chamadas de ferramenta, todas classificadas para sair; nenhuma passou de 0,6 de relevância para a etapa E2.
- 16 eram negativas do hook de decisão; 6 delas foram forçadas pela regra fixa.
- Simulação: 496 mil → 49 mil caracteres de retornos e entradas, cerca de 73 mil tokens a menos (estimativa por caracteres, não medida).
- Ficam inteiras as mensagens, as respostas e as decisões.
- **Resultado medido:** cortado num fork da sessão (a original ficou intacta), com o plano final de 129 de 131 chamadas. Retomando as duas da mesma forma, o contexto caiu de **370.935 para 235.721 tokens (−36%)**. O fork respondeu corretamente qual desafio foi escolhido e o próximo passo, tirados só do resumo anexado.

## Instrumentação acrescentada no fim da sessão

- **Hook de registro:** avisa quando há trabalho mais novo que o último registro de sessão e, ao escrever um registro, lembra de fechar a etapa e de oferecer o `/clean`.
- **Seção "Metodologia" no README da submissão:** etapas com critério de aceite, decidir antes de agir (ECC modificado com os 8Rs de PMV), medir antes de afirmar, registro fora da conversa, higienização por etapa e evidência revisada.

## Próximo passo

Sessão 02: entender o `sales_pipeline` a fundo (lacunas, distribuição por estágio, o que separa ganho de perdido controlando por produto e vendedor) e definir a lógica de score antes de escrever a interface.
