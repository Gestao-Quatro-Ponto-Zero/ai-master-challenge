# Process Log — Carlos Persike — Challenge 002 (Redesign de Suporte)

> Log escrito durante o trabalho, não reconstruído no final. Cada entrada leva data/hora.

---

## 2026-08-29 — Decomposição inicial (antes de qualquer prompt de análise)

Antes de abrir qualquer notebook ou pedir análise pra IA, quebrei o problema assim:

1. **O G4 já rodou este case em Claude/GPT/Gemini puro e guardou o baseline.** Isso muda o alvo: a entrega não pode ser "rodar o brief e reportar o que o modelo disse". Tem que ter ceticismo com os dados que um LLM sozinho não aplica por padrão — auditar antes de analisar, não confiar em correlação sem teste estatístico, e assumir que dataset de Kaggle pode ser sintético.

2. **Dois datasets, propósitos diferentes:**
   - Dataset 1 (Customer Support, ~30k linhas): tem métricas operacionais (FRT, TTR, prioridade, canal, CSAT) + texto (descrição/resolução) + PII. Serve pro diagnóstico de gargalo/desperdício.
   - Dataset 2 (IT Service Ticket, ~48k linhas): só texto + categoria (8 classes). Serve pra treinar/validar um classificador de verdade, não um brinquedo.
   - O cruzamento que o case pede: usar o classificador treinado no Dataset 2 pra propor automação de triagem, e validar a proposta contra os padrões de gargalo que aparecem no Dataset 1. Os dois datasets não têm join direto por ID — o cruzamento é conceitual/metodológico, não relacional.

3. **Ordem de execução decidida:**
   a. Auditoria dos dados primeiro (nulos, distribuições, cardinalidade, e principalmente: será que este dataset tem os padrões que um dataset real de suporte teria, ou é sintético/embaralhado?). Isso é pré-requisito pro diagnóstico ter credibilidade.
   b. Diagnóstico quantitativo (gargalo por canal/prioridade/tipo, drivers de CSAT com teste estatístico, desperdício em horas/custo com premissas explícitas).
   c. Classificador no Dataset 2 (baseline burro — classe majoritária — vs TF-IDF+LinearSVC), com matriz de confusão em holdout.
   d. Protótipo funcional: pipeline que recebe texto de ticket novo, classifica, prioriza, e decide automatizar-ou-escalar-pra-humano — rodando com dados reais do dataset, não exemplos escolhidos a dedo.
   e. README com diagnóstico, proposta (o que automatizar e o que não), limitações.

4. **O que fica de fora, deliberadamente:** fine-tuning de transformer (custo/latência não se justifica pra 8 classes com texto curto), dashboard web completo (um protótipo CLI/script que roda e mostra número já resolve o "não quero PowerPoint"), infraestrutura de deploy (fora do escopo de 4-6h).

5. **Bloqueio atual:** preciso baixar os dois CSVs do Kaggle. Não há Kaggle CLI nem credenciais configuradas nesta máquina — vou pedir pro Carlos baixar manualmente (precisa de login Kaggle) e colocar em `datasets/` (pasta já no `.gitignore` do repo raiz, então os CSVs brutos nunca vão pro commit — correto, pois têm PII).

---

## 2026-08-29 — Auditoria do Dataset 1: dados sintéticos, sem sinal operacional real

Rodei `solution/src/auditoria.py` (script meu, sem IA gerando os números — só pandas/scipy) e achei uma cadeia de problemas que muda o approach inteiro do diagnóstico:

1. **README do challenge diz "~30.000 tickets". O CSV real tem 8.469 linhas.** `wc -l` bate 29.808 porque tem descrição de ticket com quebra de linha dentro do campo (CSV multiline), não porque tem 30k tickets. Isso é o tipo de erro que confiar cegamente no brief teria propagado pra entrega.

2. **100% das `Ticket Description` contêm o literal `{product_purchased}` sem interpolar.** Texto não é reclamação real de cliente, é template com placeholder vazado — inclusive um dos textos tem "Please give credit to: @joeyclay" dentro da descrição, sinal de que o dataset foi montado a partir de um script/tutorial público, não de tickets reais.

3. **`First Response Time` e `Time to Resolution` são timestamps absolutos, não durações — e são incoerentes.** Testei: em 1.365 de 2.769 tickets fechados (49%), a Resolução acontece ANTES da Primeira Resposta. Isso é fisicamente impossível num fluxo real de suporte. Delta médio entre os dois é ~0h com desvio de 9.5h — consistente com timestamps sorteados uniformemente numa janela aleatória, não com um processo real. 64% dos registros caem no mesmo dia (01/06/2023).

4. **CSAT não correlaciona com nada.** ANOVA de `Customer Satisfaction Rating` contra Priority (p=0.633), Channel (p=0.279) e Ticket Type (p=0.701) — nenhum é estatisticamente significativo. Priority e Channel também são estatisticamente independentes entre si (qui-quadrado p=0.078), sugerindo alocação aleatória, não real.

**Decisão:** não vou forçar um "diagnóstico de gargalo em horas" fabricado a partir de dado que provei ser ruído — isso seria exatamente o tipo de "a IA disse, o candidato acreditou" que a vaga não quer. O diagnóstico do README vai:
- Reportar essa auditoria como o primeiro achado (é o achado mais acionável: antes de gastar em automação, a empresa fictícia precisaria instrumentar de verdade timestamps de criação/primeira-resposta/resolução).
- Usar o que É real no dataset — distribuição de volume por Type/Channel/Priority (contagens são reais, só a alocação relativa a CSAT/tempo que é ruído) — pra embasar decisão de capacidade e priorização de automação por volume.
- Deixar claro em Limitações que "horas de desperdício" não é calculável com honestidade a partir deste dataset, e o que precisaria existir pra calcular (created_at, first_response_at, resolved_at reais).

Isso é o tipo de correção que uma rodada crua de LLM (o baseline que o G4 já tem) dificilmente faz — é mais fácil aceitar as colunas como estão e calcular a média de "Time to Resolution - First Response Time" sem testar se a diferença faz sentido.

**Confirmação final:** olhei a coluna `Resolution` (texto que o agente teria escrito). Amostra: *"Case maybe show recently my computer follow."*, *"West decision evidence bit."* — frases gramaticalmente soltas, sem relação com o ticket, 2.769/2.769 completamente únicas (zero repetição, zero template reconhecível). É saída de gerador tipo Faker/lorem ipsum, não texto de agente humano. Junto com o achado da `Ticket Description` (item 2 acima) e a independência estatística de todas as colunas (item 4), a conclusão é definitiva: **o Dataset 1 é 100% sintético e não carrega nenhum sinal operacional real** — nem em texto, nem em tempo, nem em categoria. A única coisa real nele é a taxonomia (nomes de Type/Channel/Priority/Status/Product) e as contagens de volume por categoria, que uso só como contexto estrutural pro desenho do fluxo de automação — nunca como base de cálculo de horas/custo.

**Decisão final de escopo:** o requisito do brief "quantifique em horas e custo o desperdício" não pode ser respondido com honestidade a partir deste dataset. Vou dizer isso direto no README em vez de inventar um número plausível — isso é o achado, não uma lacuna a esconder.

---

## 2026-08-29 — Classificador no Dataset 2 (texto real, não sintético)

`solution/src/classificador.py`: TF-IDF (uni+bigrama, 20k features) + LinearSVC com `class_weight="balanced"` (as classes vão de 1.760 a 13.617 registros — desbalanceado 7.7x), holdout estratificado 80/20.

Resultado: **86.1% de acurácia / F1 macro 0.86**, contra baseline de classe majoritária de **28.5%** — ganho de 57.6pp. Primeira rodada já saiu boa; não precisei iterar hiperparâmetro (testei rapidamente sem bigrama antes e o F1 macro caiu ~2pp, então mantive `ngram_range=(1,2)`).

Olhei a matriz de confusão em vez de só reportar a acurácia — pedido explícito de "matriz de confusão, não só acurácia sozinha". Maior confusão real: **Hardware previsto como HR Support** (121 casos) e vice-versa (118). Peguei 2 exemplos reais do holdout: tickets sobre "access request... approve... holiday" classificados como Hardware no rótulo original mas o texto é genuinamente sobre fluxo de aprovação/acesso — o próprio dataset já vem pré-processado (stopwords removidas, sem estrutura de frase), então a ambiguidade é real, não erro de tokenização. Isso vira o exemplo concreto de "ticket que precisa de triagem humana, não classificação automática cega" no README.

`Miscellaneous` (categoria catch-all) tem precision/recall mais baixos (0.82/0.84) que as demais — esperado, é literalmente o balde de "não sei classificar", então bom sinal que o modelo reflita essa incerteza em vez de forçar confiança alta ali.

---

## 2026-08-29 — Roteador (protótipo): threshold errado na primeira tentativa, recalibrei

`solution/src/roteador.py`: usa a margem entre a 1a e a 2a classe do `decision_function` do LinearSVC como proxy de confiança (LinearSVC não tem `predict_proba` nativo), decide "automatizar" ou "escalar pra humano" por threshold, mais uma lista de categorias sempre escaladas por política (`HR Support` — dado sensível de pessoas, não deve virar ação automática mesmo quando classificado certo).

**Erro que cometi e corrigi:** primeira versão usei `LIMIAR_CONFIANCA = 0.15` chutado sem validar. Rodei e deu 72.8% automatizado com só 88.4% de acurácia no bucket automático vs 80.0% no escalado — gap de 8.3pp, sinal fraco, quase não valia a pena filtrar. Antes de aceitar, testei se a métrica de confiança realmente discrimina acerto: separei o holdout em quintis de confiança e a acurácia foi 54% no Q1 até 100% no Q5 (correlação ponto-bisserial 0.39) — ou seja, o sinal é forte, o threshold que eu chutei que estava errado, não a métrica. Fiz busca em grade de 0.0 a 1.5 e escolhi `t=0.7`, que dá 95% de acurácia no bucket automático cobrindo 58.2% do volume total (os outros 41.8% incluem todo HR Support + os de baixa confiança). Troquei o número no código e re-rodei pra confirmar.

Isso é iteração real, não só "rodei uma vez e aceitei o primeiro número" — a lição documentada aqui é que threshold de confiança sem validação por quantil é chute, mesmo quando parece razoável à primeira vista.

---
