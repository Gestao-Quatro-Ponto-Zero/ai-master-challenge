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

---
