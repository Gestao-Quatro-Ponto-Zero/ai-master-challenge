# ROI Model — abordagem honesta

## Por que não usei ROI baseado em Time to Resolution do Dataset 1

O Dataset 1 tem sinais fortes de geração sintética:

- 49,3% dos tickets fechados têm resolução antes da primeira resposta;
- os deltas positivos restantes não diferem por canal de forma significativa;
- CSAT é praticamente uniforme;
- status é independente de canal.

Por isso, qualquer ROI do tipo “canal X desperdiça Y horas” seria precisão falsa.

---

## Modelo de ROI recomendado

Em produção, o ROI deve ser calculado com dados reais usando:

```text
economia_mensal =
  tickets_mês
  × %_tickets_elegíveis_para_auto_roteamento
  × minutos_economizados_por_ticket
  ÷ 60
  × custo_hora_agente
```

Para este protótipo, a única variável medida com confiança é a cobertura do gate no Dataset 2.

Exemplo parametrizado:

```text
tickets_mês = 2.500
% elegível = 61,5%  # gate 0.80 no Dataset 2
minutos economizados/ticket = variável, ex. 3 a 8
custo hora agente = variável
```

## Sensibilidade

| Minutos economizados por ticket | Tickets elegíveis/mês | Horas economizadas/mês |
|---:|---:|---:|
| 3 | 1.538 | 76,9 |
| 5 | 1.538 | 128,2 |
| 8 | 1.538 | 205,1 |

## Métricas a coletar no piloto

- taxa de aceite da sugestão pelo agente;
- tempo de triagem antes/depois;
- taxa de reabertura;
- erro por categoria;
- CSAT real;
- tickets que precisaram de fallback humano;
- custo por ticket antes/depois.

## Decisão

O ROI da submissão é propositalmente parametrizado. Isso evita usar dados sintéticos para criar uma estimativa financeira falsa.
