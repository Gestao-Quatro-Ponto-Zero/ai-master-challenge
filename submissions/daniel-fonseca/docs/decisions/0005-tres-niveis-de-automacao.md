# 0005 — Política de 3 níveis: automático / revisão humana / só humano

- **Status:** Aceita (validada pelo Daniel em 2026-11-09)
- **Data:** 2026-11-09
- **Origem:** Daniel (os três níveis e o canal WhatsApp) · IA (critérios e calibração)

## Proposta
| Nível | Quando | O que acontece |
|---|---|---|
| **1 — Automático** | Confiança da classificação ≥ limiar **e** precedente validado com similaridade alta **e** categoria/tipo de baixo risco | Resposta enviada sem revisão; amostragem posterior para auditoria |
| **2 — Human in the loop** | Confiança média, ou sem precedente validado próximo | IA rascunha resposta + mostra casos similares; atendente aprova/edita/rejeita no console; aprovação alimenta `validated_resolutions` |
| **3 — Só humano** | Categorias sensíveis (ex.: HR Support, Administrative rights; no DS1: cancelamento, reembolso, prioridade Critical), baixa confiança, ou sinais de risco (sentimento muito negativo, menção legal) | IA **não responde**; só classifica, resume e notifica um humano (WhatsApp/WAHA ou alternativa) |

- Os **limiares não são chutados**: saem da curva cobertura × precisão do classificador (ADR-0004). Ex.: "com confiança ≥ 0,9 cobrimos X% dos tickets com Y% de precisão".
- A lista de categorias sensíveis é **decisão humana** (Daniel), justificada com exemplos dos dados.
- O % final de automação é um *output* medido, não uma meta — o challenge alerta que "automatizar 100% é red flag".
