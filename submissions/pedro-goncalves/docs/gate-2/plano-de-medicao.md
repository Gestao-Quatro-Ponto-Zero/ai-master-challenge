# Plano de medição

## Métricas do piloto

| Dimensão | Métrica | Fórmula | Guardrail |
|---|---|---|---|
| Qualidade | Macro-F1 | Média do F1 por classe | Não esconder classe rara |
| Segurança | Recall de classe sensível | VP / (VP + FN) | Gate por classe |
| Confiança | ECE | Diferença entre confiança e acerto | Recalibrar se degradar |
| Automação | Cobertura | Tickets acima do threshold / elegíveis | Nunca maximizar isoladamente |
| Supervisão | Override humano | Correções / sugestões exibidas | Investigar motivo |
| Operação | Touch time líquido | Tempo ativo antes e depois | Não usar TTR como proxy |
| Qualidade de serviço | Reabertura | Tickets reabertos / resolvidos | Kill criterion |
| Cliente | CSAT elegível | Respostas / pesquisas enviadas | Reportar cobertura |
| Cuidado com o cliente | Reclamações críticas não detectadas | Críticas não sinalizadas / críticas rotuladas | Definir tolerância com Operações |
| Cuidado com o cliente | Encaminhamento desnecessário | Comuns sinalizadas / comuns rotuladas | Não criar fila humana impraticável |
| Privacidade | Incidentes de PII | Eventos confirmados | Tolerância zero |
| Aprendizado | Repetição de erro conhecido | Erros repetidos / erros já documentados | Deve cair com memória ligada |
| Memória | Precisão das lições recuperadas | Lições úteis / lições exibidas | Comparar ligada e desligada |

## Desenho do piloto

1. **Shadow mode:** IA invisível para o agente, comparação com decisão real.
2. **Assistido:** sugestão visível com confirmação obrigatória.
3. **Canário:** pequena parcela de casos reversíveis, após gates anteriores.

## Critérios antes do teste

- Definir custo por erro em cada classe.
- Definir recall mínimo para classes sensíveis.
- Definir janela e tamanho amostral.
- Congelar teste final e versão do modelo.
- Definir critérios de interrupção.
- Registrar mudança de distribuição e incidentes.
- Congelar um conjunto de casos para comparar memória ligada e desligada.
- Exigir aprovação humana antes de uma lição participar das decisões.

## ROI

Capacidade líquida:

`tickets elegíveis x adoção x taxa segura x minutos poupados - minutos de revisão e retrabalho`

Valor líquido:

`capacidade líquida x custo-hora aprovado - implantação - plataforma - manutenção`

Sem touch time e custos aprovados, apresentar apenas sensibilidade, nunca payback.
