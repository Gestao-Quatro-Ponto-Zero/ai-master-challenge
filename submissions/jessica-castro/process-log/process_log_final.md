# DealSignal — Process Log (Uso de IA no desenvolvimento)

Este documento registra momentos importantes do desenvolvimento do DealSignal onde ferramentas de IA foram utilizadas para acelerar decisões técnicas, investigar problemas ou evoluir a arquitetura do sistema.

O objetivo não é registrar toda a conversa, mas destacar **interações que influenciaram diretamente o design do produto**.

---

# 1. Definição do modelo de priorização

## Prompt

Quero fazer um lead scoring similar ao rating bancário para ter mais precisão. Quais critérios devo analisar?

## Resposta resumida da IA

A IA sugeriu estruturar o scoring com múltiplos fatores, inspirados em modelos de risco:

- histórico de conversão do vendedor
- performance do produto
- velocidade do pipeline
- características da conta
- valor do deal

Também sugeriu a criação de **ratings em faixas**, semelhante a ratings financeiros.

Exemplo:

AAA  
AA  
A  
BBB  
BB  
B  
CCC  

## Impacto no projeto

Essa sugestão levou à criação do conceito central do produto:

**Deal Rating Engine**

O DealSignal passou a classificar oportunidades em ratings, facilitando leitura rápida do pipeline.

---

# 2. Investigação do modelo preditivo

## Prompt

Existe uma inconsistência: deals com muitos dias no pipeline ainda aparecem com alta probabilidade de fechamento.

## Resposta da IA

A IA ajudou a identificar possíveis causas:

- multicolinearidade entre variáveis
- distribuição histórica dos dados
- uso de Weight of Evidence
- impacto da calibração isotônica

Foi realizada uma auditoria detalhada do modelo.

## Descoberta

O modelo aprendeu que:

deals com ciclos de venda longos tinham maior taxa de sucesso no histórico.

Isso gerava previsões positivas mesmo quando o deal estava parado.

## Impacto no projeto

Essa descoberta levou a duas decisões importantes:

1. Separar **predição estatística** de **diagnóstico operacional**  
2. Criar motores determinísticos de análise.

---

# 3. Criação da arquitetura híbrida

## Prompt

Não quero que a IA tome decisões no sistema.

## Resposta da IA

Foi sugerida uma arquitetura híbrida:

Predictive Model → estima probabilidade  
Decision Engine → diagnostica o deal  
Next Best Action Engine → define ação  
AI Layer → explica em linguagem natural

## Impacto no projeto

Esse conceito se tornou o princípio central do DealSignal:

**"O sistema decide, a IA explica."**

---

# 4. Diagnóstico de fricção no pipeline

## Prompt

Quero identificar o que está bloqueando um deal.

## Resposta da IA

Foi sugerido criar um **Friction Engine**, capaz de identificar padrões de bloqueio.

Fricções principais:

- decisão
- urgência
- valor
- execução

Cada fricção representa um tipo de problema comum em vendas.

## Impacto no projeto

Essa camada passou a explicar **por que um deal não avança**.

Isso transformou o produto de um simples scoring em um sistema de **diagnóstico de vendas**.

---

# 5. Next Best Action Engine

## Prompt

Quero que o sistema recomende a próxima ação para o vendedor.

## Resposta da IA

Foi sugerido criar um catálogo fixo de ações e selecionar a melhor com base na fricção detectada.

Exemplos de ações:

confirmar decisor  
validar orçamento  
agendar reunião  
reengajar cliente  
enviar proposta  
negociar condições

## Impacto no projeto

Isso permitiu responder a pergunta mais importante para o vendedor:

**"O que eu devo fazer agora?"**

---

# 6. Uso de IA para interpretação do pipeline

## Prompt

Quero que a IA gere insights úteis para vendedores, mas sem inventar dados.

## Resposta da IA

Foi estruturado um prompt com três partes:

Observação  
Próximo passo  
Leitura

Com regras:

- linguagem simples
- sem termos técnicos
- sem repetir probabilidade numérica
- sem inventar dados

## Impacto no projeto

A IA passou a funcionar como uma camada de **interpretação**, não de decisão.

---

# 7. Melhoria da visualização do pipeline

## Prompt

O gráfico de velocidade do pipeline não está claro para vendedores.

## Resposta da IA

Foi sugerido substituir o scatter tradicional por um **Quadrante de Prioridade**.

Eixos:

Probabilidade de fechamento  
Dias desde engajamento

Quadrantes:

Foco do vendedor  
Oportunidade esquecida  
Baixa prioridade  
Em risco

## Impacto no projeto

Essa mudança tornou o dashboard muito mais fácil de interpretar.

---

# Conclusão

A IA foi utilizada em três níveis durante o desenvolvimento do DealSignal:

1. Exploração de soluções
2. Diagnóstico de problemas técnicos
3. Apoio no design de produto

No entanto, as decisões finais de arquitetura foram tomadas manualmente, garantindo que o sistema fosse:

- interpretável
- confiável
- orientado à tomada de decisão real de vendedores.
