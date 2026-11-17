# Checagens extras de robustez

## 1. Vazamento entre treino e teste
- Chamados de teste com um 'gêmeo' no treino (similaridade ≥ 90%): 6.0%
- Acerto sem esses chamados: 86.0% (geral: 86.6%)
- Conclusão: o acerto não está inflado por chamados repetidos.

## 2. O modelo cola pela assinatura/cargo?
- Acerto usando só as 3 últimas palavras: 39.9%
- Acerto sem as 3 últimas palavras: 86.1%
- Conclusão: o modelo aprende pelo problema descrito, não pela assinatura.

## 3. Mix de chamados e impacto no ROI
- Refund request: 1752, Technical issue: 1747, Cancellation request: 1695, Product inquiry: 1641, Billing inquiry: 1634
- Chamados que envolvem dinheiro (reembolso, cancelamento, cobrança): 60%
- Cenário conservador (IA só tria o que não é dinheiro): ~430 h/ano (~36 h/mês)
- Cenário ampliado (IA também encaminha dinheiro para a fila do financeiro; a decisão continua humana): ~1.076 h/ano (~90 h/mês)
- Premissas: 30 mil chamados/ano (informado pelo diretor), 3 min de triagem manual por chamado, cobertura de 71,7% (limiar de 70%). A distribuição de tipos vem de um dataset que parece sintético.