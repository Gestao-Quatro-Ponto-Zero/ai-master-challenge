# Automation Policy — CX Triage Copilot

## Princípio

A automação não deve maximizar volume automatizado. Ela deve maximizar **segurança operacional, precisão e economia de tempo em casos repetitivos**, preservando julgamento humano nos casos de risco.

---

## Rotas

### 1. AUTO_RESOLVE

Usar apenas quando todas as condições forem verdadeiras:

- domínio `B2E_IT`;
- confiança do classificador ≥ 0.80;
- prioridade `Low` ou `Medium`;
- categoria elegível: `Access`, `Hardware`, `Storage` ou `Purchase`;
- sem termos de risco financeiro, jurídico, privacidade, fraude, cancelamento ou emoção forte.

No teste do Dataset 2, o gate de 0.80 cobre 61.5% dos tickets B2E/IT com 97.3% de acurácia dentro do gate.

### 2. AGENT_ASSIST

Usar quando:

- domínio `B2C_EXTERNAL` sem risco crítico;
- confiança entre 0.50 e 0.80;
- categoria exige revisão;
- o ticket é longo, ambíguo ou precisa de resposta rascunho;
- há risco moderado.

A IA pode:

- resumir o ticket;
- sugerir categoria;
- sugerir próxima ação;
- sugerir resposta;
- listar evidências;
- recomendar artigo/checklist.

A IA não envia resposta automaticamente.

### 3. HUMAN_ESCALATION

Usar sempre que houver:

- prioridade `Critical`;
- confiança < 0.50;
- refund/reembolso;
- cancellation/cancelamento;
- fraude, jurídico, privacidade, LGPD;
- Administrative rights;
- HR Support;
- linguagem emocional forte;
- reclamação explícita ou risco de churn.

---

## Guardrails implementados no código

| Guardrail | Implementação |
|---|---|
| Critical nunca é auto-resolvido | `triage.py` retorna `HUMAN_ESCALATION` |
| B2C externo não é auto-resolvido | domínio B2C retorna `AGENT_ASSIST` ou `HUMAN_ESCALATION` |
| Baixa confiança bloqueia automação | threshold < 0.50 escala |
| Confiança alta não basta | categoria e prioridade também precisam ser elegíveis |
| Termos de risco bloqueiam automação | lista `HIGH_RISK_TERMS` |
| Categorias sensíveis de IT não são auto | `Administrative rights`, `HR Support`, `Internal Project` |

---

## Política de rollout

1. Rodar em modo shadow por 2 semanas.
2. Medir taxa de acerto por categoria.
3. Medir taxa de aceite das sugestões pelos agentes.
4. Liberar auto-roteamento apenas para categorias com precisão alta.
5. Revisar semanalmente erros críticos e falsos positivos.
6. Manter auditoria humana amostral mesmo nos casos `AUTO_RESOLVE`.
