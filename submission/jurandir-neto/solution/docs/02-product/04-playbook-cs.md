# Playbook de Customer Success — RavenStack

Esta é a base de conhecimento consultada pelo agente de diagnóstico. Para cada tipo de problema identificado nos dados, o agente recupera a estratégia aplicável, explica o racional e fornece exemplos de execução.

> **Manutenção:** Este documento deve ser atualizado pelo time de CS sempre que novas estratégias forem validadas ou casos relevantes forem documentados.

---

## Categoria 1: Baixo Engajamento com o Produto

**Sinais nos dados:**
- `usage_count` e `usage_duration` abaixo da média do segmento por 2+ semanas
- Poucas features ativas em relação ao plano contratado

**Estratégia: Re-ativação guiada**

O objetivo é reintroduzir o valor da plataforma conectando features específicas ao problema real do cliente.

**Como executar:**
1. Identifique quais features do plano a conta nunca usou ou parou de usar
2. Mapeie o perfil da conta (indústria, tamanho) para encontrar casos de sucesso similares
3. Abordagem: "Vi que vocês não estão usando [feature X]. Clientes do setor [Y] usam ela para [resultado Z] — posso mostrar como?"
4. Ofereça uma sessão de onboarding focada (não genérica)
5. Defina um marco de sucesso com o cliente: o que "bom uso" significa para ele em 30 dias?

---

## Categoria 2: Problemas Técnicos Recorrentes

**Sinais nos dados:**
- `error_count` elevado em `feature_usage` por 3+ dias consecutivos
- Tickets de suporte abertos logo após picos de erros

**Estratégia: Intervenção proativa de suporte técnico**

O cliente não deve precisar abrir ticket para saber que o problema foi identificado.

**Como executar:**
1. Monitore o `error_count` diariamente — qualquer conta com aumento de 50%+ em relação à média merece contato
2. Entre em contato antes que o cliente abra ticket: "Identificamos instabilidade em [feature X] na sua conta — já estamos investigando"
3. Ofereça um canal direto com o time técnico enquanto o problema persiste
4. Após resolução, faça follow-up confirmando que está funcionando e pedindo feedback
5. Se o problema persistir por mais de 5 dias, escale internamente e mantenha o cliente informado

---

## Categoria 3: Experiência Negativa de Suporte

**Sinais nos dados:**
- `satisfaction_score` abaixo de 3 (em escala 1-5)
- `is_escalated = true` em múltiplos tickets
- `first_response_time` ou `resolution_time` acima do SLA

**Estratégia: Recuperação de relacionamento**

Um atendimento ruim não é esquecido — precisa ser reconhecido e corrigido ativamente.

**Como executar:**
1. Após qualquer ticket com CSAT baixo, o CS manager (não o suporte) entra em contato pessoalmente
2. Abertura: "Vimos que sua experiência com o nosso suporte dessa vez não foi boa. Quero entender o que aconteceu."
3. Não defenda o processo — escute. O objetivo é entender a percepção do cliente
4. Ofereça uma solução concreta para o problema original (não apenas um pedido de desculpa)
5. Estabeleça um ponto de contato direto para as próximas 4 semanas

---

## Categoria 4: Sinal de Downgrade

**Sinais nos dados:**
- `has_downgrade = true` em `ravenstack_subscriptions`
- Downgrade ocorrido nos últimos 60 dias

**Estratégia: Entrevista de valor**

Downgrade é a conta dizendo "estou pagando por mais do que uso". O objetivo é entender o gap entre o plano e o uso real.

**Como executar:**
1. Contato em até 48h após o downgrade: "Vi que vocês ajustaram o plano — quero entender se estamos entregando o valor certo para vocês"
2. Faça perguntas abertas: "O que levou à decisão?", "O que deveria estar acontecendo diferente?"
3. Não tente reverter o downgrade imediatamente — isso gera resistência
4. Se o motivo for financeiro, explore opções de plano ou billing anual com desconto
5. Se o motivo for de uso, retorne à estratégia de re-ativação guiada (Categoria 1)
6. Documente o motivo — é dado valioso para o produto

---

## Categoria 5: Conta com Perfil de Alto Risco (score combinado)

**Sinais nos dados:**
- Combinação de 2+ sinais das categorias anteriores
- MRR acima de $1.000/mês (conta de alto impacto)

**Estratégia: Executive Business Review (EBR) acelerado**

Contas de alto valor com múltiplos sinais de risco merecem atenção executiva, não apenas operacional.

**Como executar:**
1. O CS manager sênior (ou o próprio CEO para contas estratégicas) assume o relacionamento
2. Convoque uma EBR — não como "check-in de rotina", mas com pauta clara: "Quero entender se estamos cumprindo o que prometemos"
3. Prepare os dados da conta antes da reunião: uso, tickets, evolução de MRR
4. Na reunião, apresente o que a conta conquistou usando a plataforma (mostre valor realizado)
5. Identifique gaps e construa um plano de sucesso conjunto com marcos claros
6. Defina cadência de acompanhamento por pelo menos 90 dias

---

## Categoria 6: Churn Confirmado — Feedback e Aprendizado

**Sinais nos dados:**
- Registro em `ravenstack_churn_events`

**Estratégia: Entrevista de saída**

Não é sobre reverter — é sobre aprender para não perder a próxima conta.

**Como executar:**
1. Entre em contato em até 72h após o churn confirmado
2. Objetivo declarado: "Não vou tentar te convencer a voltar — quero entender o que poderíamos ter feito diferente"
3. Analise o `feedback_text` antes do contato — use o que já foi dito como ponto de partida
4. Documente os aprendizados no sistema de CS com tags estruturadas
5. Se o motivo for reversível (preço, feature específica, timing), registre como oportunidade de win-back em 3-6 meses
