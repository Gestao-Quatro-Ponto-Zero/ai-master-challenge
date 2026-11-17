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
- Cenário conservador (IA só tria o que não é dinheiro): ~377 h/ano (~31 h/mês) ≈ R$ 5.897/ano
- Cenário ampliado (IA também encaminha dinheiro para a fila do financeiro; a decisão continua humana): ~943 h/ano (~79 h/mês) ≈ R$ 14.740/ano
- Custo/hora usado: R$ 15.64 (custo empresa de R$ 3.440 por mês ÷ 220 h; Operador de Suporte Técnico. Portal Salário 2026)
- Leitura: a economia direta de triagem é modesta. O ganho principal é tempo: o ticket chega na fila certa na hora, sem esperar alguém ler e encaminhar.
- Premissas: 30 mil chamados/ano (informado pelo diretor), 3 min de triagem manual por chamado, cobertura efetiva de 62.8% (limiar de 70% + regras de passagem para humano). A distribuição de tipos vem de um dataset que parece sintético.

## 4. As regras de passagem para humano funcionam?
- Dataset de suporte: as palavras-chave de dinheiro pegam 7.4% dos chamados de reembolso/cancelamento/cobrança e disparam em 7.5% dos outros.
  Leitura: no dataset de suporte o texto não tem relação com o tipo do chamado (dado sintético), então a regra por palavra-chave não pode ser validada ali. Em produção, a regra de dinheiro deve usar o campo estruturado do chamado (tipo/assunto escolhido pelo cliente) e as palavras-chave só como reforço.
- Dataset de TI: com todas as regras ligadas, a IA decide sozinha 62.8% dos tickets de teste (só o limiar daria 71.7%), com acerto de 95.8% nesses.
- Motivos extras de passagem para humano no TI: palavra-chave em 9.4% dos tickets; categoria sensível prevista em 3.8%.