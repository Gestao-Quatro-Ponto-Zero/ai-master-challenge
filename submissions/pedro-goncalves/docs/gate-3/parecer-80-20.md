# Parecer 80/20 da operação

## Decisão

O próximo ciclo deve priorizar **cliente reincidente** e **qualidade dos horários**. Esses dois
pontos atacam a operação atual. Cobertura e acerto do classificador comprovam viabilidade técnica
somente na fila interna de TI e sustentam um piloto em observação, não automação em produção.

## Quatro indicadores comprovados

| Indicador | A + B | Resultado | Tipo | Leitura |
|---|---|---:|---|---|
| Cliente reincidente | contagem exata da frase de contatos repetidos sem solução nas 8.469 descrições | 460 casos, 5,43% da base | Medido | 152 desses casos estão encerrados e precisam de auditoria prioritária |
| Horários inválidos | 1.365 resoluções anteriores à primeira resposta ÷ 2.769 pares preenchidos | 49,30% | Calculado sobre dado medido | FRT, TTR e ROI observado ficam vetados até corrigir a semântica dos campos |
| Cobertura segura | 5.003 mensagens acima do limite de 75% ÷ 7.176 mensagens do teste final | 69,72% | Calculado no Dataset 2 | Cerca de 30% da fila de TI ainda exige abstenção ou revisão |
| Acerto nos cobertos | 4.834 previsões corretas ÷ 5.003 previsões cobertas | 96,62% | Calculado no Dataset 2 | O classificador pode apoiar triagem de TI em observação, sem executar ações |

## Pareto dos quatro

1. **Revisar os 460 casos reincidentes**, começando pelos 152 encerrados. Motivo: há voz direta do
   cliente indicando falha ainda não resolvida.
2. **Corrigir os 1.365 pares temporais inválidos**. Motivo: sem essa base, qualquer promessa de
   eficiência, tempo economizado ou ROI seria matematicamente frágil.

Os outros dois indicadores entram depois, como gate técnico do piloto: cobertura define o volume
que a IA pode sugerir; acerto mede a qualidade apenas dentro desse volume.

## Regra para eficiência e produtividade

O dataset não contém tempo ativo do agente antes e depois da assistência. Portanto, **não existe
redução observada comprovável nesta entrega**. O protótipo oferece uma simulação editável:

`capacidade líquida = horas manuais - horas assistidas - horas de retrabalho`

Volume vem do arquivo. Elegibilidade, adoção, minutos manuais, minutos assistidos e taxa segura
são hipóteses declaradas pelo usuário. O resultado só vira KPI real depois de um piloto medir
esses campos no mesmo período e na mesma população.

## Parecer final

Operacionalmente, a dor mais urgente é o cliente que retorna sem solução. Gerencialmente, a
qualidade temporal impede cobrança séria de desempenho. Tecnicamente, o classificador de TI é
viável com abstenção. A recomendação é corrigir dados, revisar reincidências e rodar um piloto
assistido antes de ampliar autonomia.
