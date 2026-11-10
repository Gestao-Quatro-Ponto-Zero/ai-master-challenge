# 0012 — Decisões de construção dos fluxos n8n (nível 1, bloqueio, modelo, idioma, heartbeat)

- **Status:** Aceita (decisões do Daniel em 2026-11-09; lista de bloqueio adotada a partir da medição)
- **Data:** 2026-11-09
- **Origem:** Daniel (decisões) · IA (medição de falsos positivos e custo)
- **Evidência:** `solution/analysis/10_blocklist_eval.py` → `output/blocklist_eval.json`; preços oficiais da OpenAI (consultados em 09/11/2026)

## Contexto
O rascunho dos fluxos (`docs/n8n-flows.md`) deixou 6 pontos para o Daniel decidir antes da construção.

## Decisão
1. **Nível 1 = LLM adapta a solução validada ao ticket** (não envia o texto validado cru). Guarda-corpos: o LLM não acrescenta passo, prazo, promessa nem exceção; se a solução não se aplica (`fits: false`), o ticket vai para o nível 2. O texto validado de origem fica registrado (`resolution_id`) para auditoria amostral.
2. **Nível 1 só com solução validada da categoria.** Torna obrigatório o playbook-semente de `validated_resolutions` (IA rascunha, Daniel revisa).
3. **Lista de bloqueio estreita** (salary, payroll, bonus, termination, dismissal, resignation, lawsuit, legal, harassment, sick leave, maternity): **6 falsos positivos em 2.983 tickets do nível 1 (0,2%)**. A lista ampla, com termos de TI (administrator, password, contract, leaver…), rebaixaria 21,4% do nível 1 e foi descartada. A preocupação do Daniel com falsos positivos se confirmou para termos amplos, mas não para os estreitos.
4. **`gpt-5.4-mini`** com raciocínio `low` e teto de tokens por nó: ~US$ 0,003 por ticket → ~1.600 tickets com os US$ 5 de crédito. `gpt-5.4-nano` fica como alternativa mais barata.
5. **Idioma:** a demo principal sorteia do holdout; o texto livre do console é em inglês, a mesma língua da base. A resposta ao cliente sai no idioma do ticket; o material para o agente sai em pt-BR.
6. **Heartbeat do n8n às 06:00 (America/Sao_Paulo)**; o cron da Vercel fica em outro horário.

## Alternativas consideradas
- Enviar a solução validada sem LLM no nível 1: mais seguro (texto 100% revisado), porém menos natural. Daniel preferiu a adaptação.
- Traduzir automaticamente o texto livre antes do embedding: uma chamada de LLM a mais por ticket; desnecessária com o console pedindo inglês.

## Consequências
- O nível 1 passa a ter texto gerado por LLM indo ao cliente → o "fits" e a auditoria amostral viram parte do argumento de segurança no README.
- O playbook-semente entra no caminho crítico da demo (sem ele, nenhum ticket chega ao nível 1).
- Os 15 sensíveis que escapam para o nível 1 no holdout parecem ruído de rótulo: a lista pega só 1. Ela protege tickets novos com linguagem de RH/jurídico, e não esses casos.
