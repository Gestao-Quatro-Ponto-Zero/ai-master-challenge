# Diagnóstico Operacional - Challenge 002

## Metodologia
1) Padronização de colunas e limpeza de nulos; 2) Conversão de tempos a partir de timestamps para proxies em horas relativas ao menor registro (comparação entre grupos, não SLA absoluto); 3) Análises de volume, TTR/FRT e satisfação por canal/tipo/prioridade; 4) Detecção de gargalos (mediana de TTR + volume); 5) Estimativa comparativa de desperdício versus benchmark interno P25; 6) Amostragem qualitativa apenas para ilustração, dada a baixa confiabilidade semântica dos textos.

## Principais achados
- Gargalo mais crítico (comparativo): Chat / Refund Request / High com mediana de TTR 16.7 h e volume 41.
- Não há associação monotônica relevante entre satisfação e TTR/FRT (Spearman TTR -0.01, FRT -0.04); diferenças aparecem mais entre segmentos.
- Pior satisfação média em ticket_channel: Phone (2.95).
- Desperdício comparativo estimado: 5337.5 h sobre 37098.1 h totais, usando benchmark interno P25 (proxy, não SLA real).

## Gargalos operacionais
Grupos com alto volume e TTR acima do P75 das respectivas distribuições:
```

ticket_channel  volume  frt_mean  frt_median  ttr_mean  ttr_median  satisfaction_mean          ticket_type ticket_priority
         Email     154 13.346975   13.132361 14.115817   14.827639           2.863636 Cancellation Request             NaN
         Phone     147 13.701260   13.874167 13.467706   14.503889           3.095238      Product Inquiry             NaN
  Social Media     144 13.295328   13.333056 14.187527   14.492917           2.958333      Product Inquiry             NaN
           NaN     147 12.889110   12.336944 13.719388   13.753889           3.068027      Technical Issue        Critical
           NaN     145 14.391287   14.587500 13.545741   13.729444           2.903448 Cancellation Request        Critical
          Chat      41 12.363415   11.869722 15.374451   16.684444           3.146341       Refund Request            High
          Chat      35 12.331929   12.265556 15.623952   16.386667           3.085714      Billing Inquiry             Low
  Social Media      35 14.177413   15.398056 13.930389   16.305556           3.285714      Billing Inquiry             Low
  Social Media      37 12.098183   10.745000 14.581764   15.553611           2.783784      Product Inquiry             Low
          Chat      39 13.431154   14.707222 14.140491   15.392500           3.564103      Technical Issue        Critical

```

## Impacto na satisfação
Correlação (Spearman) satisfação ~ FRT: -0.04; satisfação ~ TTR: -0.01. As correlações são próximas de zero, indicando ausência de associação monotônica relevante; diferenças de satisfação aparecem mais entre segmentos operacionais.

**Satisfação média por ticket_channel:**
```

ticket_channel  mean_satisfaction  volume
          Chat           3.083086    2073
  Social Media           2.969298    2121
         Email           2.963889    2143
         Phone           2.952243    2132

```

**Satisfação média por ticket_type:**
```

         ticket_type  mean_satisfaction  volume
Cancellation Request           3.029070    1695
     Billing Inquiry           3.027574    1634
     Product Inquiry           3.016886    1641
     Technical Issue           2.958621    1747
      Refund Request           2.934564    1752

```

**Satisfação média por ticket_priority:**
```

ticket_priority  mean_satisfaction  volume
            Low           3.052795    2063
           High           2.982979    2085
         Medium           2.976945    2192
       Critical           2.958678    2129

```

**Satisfação média por ticket_status:**
```

            ticket_status  mean_satisfaction  volume
                   Closed           2.991333    2769
                     Open                NaN    2819
Pending Customer Response                NaN    2881

```

## Desperdício operacional (horas)
Benchmark interno (comparativo): mediana P25 dos grupos (11.66 h). Horas totais consumidas (proxy TTR): 37098.1. Horas excedentes recuperáveis (proxy comparativa): 5337.5.
Top grupos por desperdício recuperável:
```

ticket_channel          ticket_type ticket_priority  ttr_median  volume  recoverable_hours
          Chat       Refund Request            High   16.684444      41         205.812882
          Chat      Product Inquiry             Low   18.471111      28         190.581806
  Social Media      Product Inquiry            High   17.171389      32         176.216667
          Chat      Billing Inquiry             Low   16.386667      35         165.271701
  Social Media      Billing Inquiry             Low   16.305556      35         162.432812
         Email Cancellation Request             Low   16.330278      33         153.966771
          Chat      Technical Issue        Critical   15.392500      39         145.387396
  Social Media      Product Inquiry             Low   15.553611      37         143.892743

```

## Leitura qualitativa
Os campos textuais apresentam baixo sinal semântico (muitos placeholders/sentenças genéricas). Servem apenas como ilustração do ruído e não sustentam inferências causais.
### Amostras do grupo 1: ticket_channel=Chat, ticket_type=Refund Request, ticket_priority=High
- Assunto (ruidoso): Display issue
  - Descrição (ilustrativa): I'm facing a problem with my {product_purchased}. The {product_purchased} is not turning on. It was working fine until yesterday, but now it doesn't respond....
  - Resolução (ilustrativa): Mind ask amount huge late.
  - TTR (h) proxy: 26.4
- Assunto (ruidoso): Installation support
  - Descrição (ilustrativa): I'm having an issue with the {product_purchased}. Please assist. 1 2 3 4 5 6 7 8 9 10 11 I need assistance as soon as possible because it's affecting my work...
  - Resolução (ilustrativa): Care nice thus decide.
  - TTR (h) proxy: 25.7
- Assunto (ruidoso): Account access
  - Descrição (ilustrativa): I've accidentally deleted important data from my {product_purchased}. Is there any way to recover the deleted files? I need them urgently. I have been unable...
  - Resolução (ilustrativa): If method as likely make.
  - TTR (h) proxy: 25.6
### Amostras do grupo 2: ticket_channel=Chat, ticket_type=Billing Inquiry, ticket_priority=Low
- Assunto (ruidoso): Software bug
  - Descrição (ilustrativa): I've accidentally deleted important data from my {product_purchased}. Is there any way to recover the deleted files? I need them urgently. Sorry to hear all....
  - Resolução (ilustrativa): Memory tough a memory their.
  - TTR (h) proxy: 26.7
- Assunto (ruidoso): Product compatibility
  - Descrição (ilustrativa): I'm having an issue with the {product_purchased}. Please assist. Please help further by reviewing our FAQ If there are any questions or suggestions please...
  - Resolução (ilustrativa): Water wish staff best my wall the church.
  - TTR (h) proxy: 24.8
- Assunto (ruidoso): Installation support
  - Descrição (ilustrativa): I'm having an issue with the {product_purchased}. Please assist. I have had to cancel my account at least once (my refund card is still available after an...
  - Resolução (ilustrativa): Recent develop seat bar decision region discussion.
  - TTR (h) proxy: 23.3
### Amostras do grupo 3: ticket_channel=Social Media, ticket_type=Billing Inquiry, ticket_priority=Low
- Assunto (ruidoso): Network problem
  - Descrição (ilustrativa): I'm having an issue with the {product_purchased}. Please assist. {Product_purchased} may not be paid. You cannot buy item as {product_type}. Please assist....
  - Resolução (ilustrativa): Animal meeting road.
  - TTR (h) proxy: 25.6
- Assunto (ruidoso): Product compatibility
  - Descrição (ilustrativa): I'm having an issue with the {product_purchased}. Please assist. 1) If you purchased the product you were given the gift, please do not enter the gift in the...
  - Resolução (ilustrativa): Yet laugh safe claim.
  - TTR (h) proxy: 23.9
- Assunto (ruidoso): Hardware issue
  - Descrição (ilustrativa): I've forgotten my password for my {product_purchased} account, and the password reset option is not working. How can I recover my account? I can use an...
  - Resolução (ilustrativa): Care medical brother until.
  - TTR (h) proxy: 23.8

## Limitações
- TTR/FRT são proxies derivadas de timestamps relativos; não representam duração operacional exata ou SLA real.
- Ratings ausentes em grande parte da base reduzem a confiança das associações de satisfação.
- Desperdício é estimativa comparativa baseada em benchmark interno (P25); não é mensuração financeira ou de esforço real.