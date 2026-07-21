# Diagnóstico Operacional — Suporte ao Cliente

Analisei os 8.469 tickets para responder às suas três perguntas: onde se perde tempo, o que afeta a satisfação, e onde está o gargalo.

**Uma delas tem resposta clara e imediata: dois em cada três tickets não chegam a ser resolvidos.** As outras duas esbarram no mesmo ponto — o sistema hoje registra *o que* acontece, mas não *quanto tempo* leva nem *com que qualidade* termina. Não é um problema de time; é que essas perguntas são novas para os dados que a operação vinha guardando. E esse, na prática, é o primeiro problema a resolver.

---

## As três perguntas, uma a uma

Testei cada pergunta com os dados reais (n = 8.469). O que eles dizem:

| Pergunta | O que os dados respondem |
|---|---|
| **1. Onde perdemos tempo?** | Ainda não é possível medir. Em quase metade dos tickets resolvidos, o registro de resolução aparece *antes* do de primeira resposta, e não existe data de abertura para reconstruir o tempo de espera. A duração, hoje, não é confiável. → *ver gráfico "Tempo"* |
| **2. O que afeta a satisfação?** | Nenhuma das variáveis que capturamos. Canal, prioridade e tipo de ticket explicam praticamente 0% da nota (R² = 0,003); todas as médias ficam coladas em ~3,0. Quem responde por chat, telefone ou e-mail sai igualmente satisfeito — ou igualmente insatisfeito. |
| **3. Qual o gargalo?** | Não há um ponto de concentração. O volume é estatisticamente equilibrado entre todos os canais, tipos e prioridades (p > 0,11). Não existe um "canal que trava" ou "tipo que emperra" — a carga está distribuída por igual. |

## O fato sólido, para levar à diretoria

> **Só 32,7% dos tickets chegam a "Resolvido".** Os outros **67,3% — 5.700 tickets — seguem em "Aberto" ou "Aguardando cliente".** → *ver gráfico "Fila"*

Esse é o número que importa: a fila cresce mais rápido do que fecha. É aqui que a dor do time e a queda de satisfação encontram sua explicação mais provável.

---

## O que está por trás das perguntas sem resposta

Os três resultados apontam para a mesma origem. O sistema atual foi desenhado para **operar** o suporte — quem abriu, qual produto, por qual canal. Ele não foi desenhado para **diagnosticá-lo**: faltam os campos que transformam registro em análise. As perguntas do Diretor são exatamente as certas; elas só precisam de quatro dados que hoje não são capturados de forma confiável:

1. **Data de abertura do ticket** (`created_at`) — sem ela, nenhum tempo de espera ou SLA pode ser calculado.
2. **Validação da ordem dos horários** na entrada — uma resolução nunca deveria ser registrada antes da primeira resposta.
3. **CSAT amarrado ao ticket e ao agente**, coletado logo após o fechamento — para a satisfação virar algo que se pode explicar e melhorar.
4. **Campo de resolução padronizado** (o que foi feito para resolver) — hoje em texto livre sem estrutura.

Com esses quatro campos, a próxima leitura desta operação deixa de ser opinião e passa a ser evidência.

---

## Onde já há valor, mesmo antes de corrigir os dados

O diagnóstico fecha uma porta e abre outra. Os registros operacionais têm esse limite — mas o **texto** dos tickets é uma matéria-prima rica e ainda pouco aproveitada: é volume alto, repetitivo e classificável. É exatamente aí que a IA gera retorno agora, sem depender de reconstruir o histórico.

→ **Continua na Proposta de Automação:** um classificador que funciona sobre texto real, decidindo sozinho o que pode rotear e o que precisa de um humano — com métrica honesta do que dá e do que não dá para automatizar.

---

*Números provenientes de testes estatísticos reproduzíveis (ANOVA, regressão, qui-quadrado). Análise completa e evidência visual dos quatro testes em `exploration/` e `solution-draft/figures/`.*
