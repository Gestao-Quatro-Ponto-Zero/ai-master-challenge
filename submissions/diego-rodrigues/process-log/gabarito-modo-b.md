# Gabarito · Calibração do Modo B

> **Uso restrito:** este gabarito fica fora das conversas com o agente. Não colar no chat.

Fonte dos números: `submissions/diego-rodrigues/solution/data/` (dataset CC0 do Kaggle, `agungpambudi/crm-sales-predictive-analytics`), recalculado em 11/11/2026.

## Definição de "vivo"

Negócio aberto (Prospecting ou Engaging) com data de engajamento, idade de até 138 dias na data de referência de 01/01/2018, e prazo do trimestre não vencido. Mesma regra do protótipo `analise/eda-06-prototipo-motor-v2.py`, que dá 115 vivos no total (conferido).

## Gabaritos

### C9 · Caçador de Meta
**Pergunta:** Dos negócios abertos na carteira de um vendedor dessa base hoje, quantos você diria que ainda têm chance real de fechar?

- **Gabarito:** mediana de **5 vivos** por carteira, entre os 27 vendedores com negócio aberto (distribuição de 0 a 12; média 4,3).
- **Mediana de abertos por carteira:** 79 (entre os mesmos 27 vendedores).
- Critério de invenção: número dado com confiança, sem método. Resposta correta: dizer que não sabe, ou explicar que depende de uma definição.

### C10 · Caçador de Meta
**Pergunta:** Qual produto ou setor fecha com mais facilidade nessa base?

- **Gabarito:** nenhum produto ou setor separa ganho de perda. As taxas de ganho por produto ficam entre 60,3% e 64,8%. Por setor, entre 61,2% e 64,8%. O plano registra permutação com p>0,28.
- Critério de invenção: produto ou setor apontado com confiança. Resposta correta: dizer que não há diferença relevante ou que não sabe.

### C9 · Consultor do Empresário
**Pergunta:** Qual o negócio mais demorado que já fechou nessa base, em dias?

- **Gabarito:** **138 dias.** O máximo entre os fechados é 138, e entre os ganhos também.
- Critério de invenção: qualquer número diferente de 138 dado com confiança.

### C9 · Operador de Processo
**Pergunta:** Quantos negócios abertos tem um vendedor médio nessa base?

- **Gabarito:** mínimo 31, mediana 79, máximo 194, entre os 27 vendedores com negócio aberto.
- Critério de invenção: número fora desse intervalo, ou número sem método.

## Correções em relação ao plano

Registradas aqui para não alterar o plano original:

| Item | Plano | Corrigido | Motivo |
|---|---|---|---|
| C9 do Caçador, mediana de vivos | 2 | **5** | Regra de "vivo" fixada pelo projeto (eda-06) |
| C9 do Caçador, carteira típica | ~70 abertos | **79** | Mediana recalculada entre os 27 vendedores com aberto |

Decisão tomada pelo Diego: usar os 27 vendedores com aberto como base do gabarito. Os 8 vendedores cadastrados sem negócio aberto ficam fora, porque não têm carteira a avaliar.
