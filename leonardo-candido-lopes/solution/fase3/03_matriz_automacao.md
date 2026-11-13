# 03 — Matriz de Automação

**Desafio 002 · Fase 3** · Autor: Leonardo Candido Lopes · 08/11/2026

Tratamentos: **AUTO** = automático, sem humano no caminho · **ASSISTIDO** = IA sugere, humano confirma · **HUMANO** = decisão humana, a IA só organiza o contexto.
Risco de automatizar: **Alto / Médio / Baixo**.

| # | Tipo de atividade | Domínio | Tratamento proposto | Justificativa (dados) | Intervenção humana | Risco de automatizar |
|---|---|---|---|---|---|---|
| 1 | Classificação inicial do domínio (TI × Financeiro/Comercial × Fora do escopo) | Todos | **AUTO** com saída para humano quando o domínio é incerto | 31,5% do D1 (2.667) sem categoria de TI; só 98 das top-300 palavras em comum entre D1 e D2 | Revisa os casos de domínio incerto | Médio: um ticket financeiro classificado como TI atrasa reembolso |
| 2 | Classificação nas 8 categorias de TI | TI interna | **AUTO** se confiança ≥ τ_alto; **ASSISTIDO** na faixa média | 47.602 exemplos após limpeza; ≥ 1.753 por categoria; 5 de 8 categorias com vocabulário distintivo | Confirma ou corrige na faixa média; a correção é registrada | Médio: concentrado em Hardware × Misc (0,625) |
| 3 | Roteamento para a fila correta | Todos | **AUTO** | Consequência direta da classificação; o motivo da decisão é gravado | Pode reatribuir (o `reassign_count` mede isso) | Baixo, se o 1 e o 2 forem controlados |
| 4 | Priorização | Todos | **ASSISTIDO**: regras impacto × urgência + sinais no texto | A prioridade do D1 é aleatória (Priority × tudo com V ≤ 0,04), então não há rótulo confiável para treino | O agente pode sobrescrever; obrigatório em Crítica | **Alto**: subpriorizar um crítico tem custo alto |
| 5 | Sugestão de resposta (FAQ / base de conhecimento) | TI interna | **ASSISTIDO**: o agente edita antes de enviar | Categorias com textos repetidos (Purchase, Storage, Access) | Revisa e envia | Baixo |
| 6 | Resolução autônoma de acesso/senha (reset, desbloqueio) | TI · Access | **AUTO** com verificação de identidade (MFA) | "password": 70,8% de 1.646 tickets em Access; "reset" em 10,3% da categoria | Só se o reset falhar ou a conta for privilegiada | Médio: risco de segurança (engenharia social) se não houver MFA |
| 7 | Pedidos de compra (status de PO, recebimento) | TI · Purchase | **AUTO** (consulta e instrução) | "po" em 70,6% (vs 0,6% fora); categoria mais separada (≤ 0,24) | Aprovação de compra continua humana | Baixo |
| 8 | Acesso a pasta / cota de mailbox | TI · Storage | **AUTO** via fluxo de aprovação do dono da pasta | "folder" em 28,8%, "accept" em 27,2%, "decline" em 25,7% | O dono da pasta aprova; exceções de cota vão para humano | Baixo-médio (vazamento se aprovar a pessoa errada) |
| 9 | Tickets de Hardware: diagnóstico | TI · Hardware | **ASSISTIDO**: coleta guiada (modelo, sintoma, passos já tentados) | 28,5% do volume; termos distintivos fracos (≤ 4,5%) | O técnico analisa | Médio |
| 10 | Tickets de Hardware: substituição ou reparo físico | TI · Hardware | **HUMANO** | Ação física; custo do ativo | Integral | Alto |
| 11 | Concessão de direitos de administrador | TI · Admin rights | **HUMANO** (a IA só classifica e reúne a justificativa) | A menor categoria (1.760); risco de segurança | Integral, com aprovação | Alto |
| 12 | Reembolso / pagamento / cancelamento | **Financeiro/Comercial (B2C)** | **HUMANO** em fila dedicada; a IA só identifica o domínio e resume | Fora das 8 categorias; 576 Refund + 526 Payment + 487 Cancellation no D1 | Integral: decisão financeira e risco de chargeback | **Alto** |
| 13 | Problema de entrega / recomendação de produto | **Financeiro/Comercial (B2C)** | **ASSISTIDO**: consulta de rastreio e sugestão de resposta | 561 Delivery + 517 Recommendation no D1 | Confirma a resposta | Médio |
| 14 | Tickets com baixa confiança de classificação | Todos | **HUMANO** (triagem manual) | Pares ambíguos; 38 grupos de quase-duplicatas com categorias conflitantes | Integral; a categoria escolhida vira dado de treino | Alto, se fosse automatizado |
| 15 | Escalonamento para N2 | TI interna | **ASSISTIDO**: gatilhos automáticos (tempo, reabertura, palavras "all users") + decisão humana | Sem dado histórico de escalonamento ([HIPÓTESE] sobre os gatilhos) | O N1 decide, o N2 aceita | Médio |
| 16 | Conflito de rótulo / ambiguidade entre categorias | TI interna | **HUMANO** (curadoria periódica) | 38 grupos conflitantes; 19,9% dos tickets com "password" estão em Hardware | Revisão por amostragem e atualização do guia de categorias | Alto, se fosse automatizado (o modelo aprende o erro) |
| 17 | Miscellaneous (categoria-coringa) | TI interna | **ASSISTIDO**, com fila de revisão | 14,8% do volume; similaridade de 0,625 com Hardware | Reclassifica e propõe nova categoria se surgir um padrão | Médio |
| 18 | Follow-up de ticket "aguardando cliente" | Todos | **AUTO**: lembrete + fechamento por inatividade com aviso | 34,0% do D1 em "Pending" ([HIPÓTESE]: dado sintético) | Define a política de prazos | Baixo |
| 19 | Coleta de feedback pós-resolução (CSAT) | Todos | **AUTO** | A satisfação do D1 é plana (sintética), então é preciso coletar dado real | Analisa comentários negativos | Baixo |
| 20 | Registro de eventos e tempos (Pilar 3) | Todos | **AUTO** (obrigatório) | O D1 não tem `created_at`; 49,3% das resoluções vêm antes da 1ª resposta | Auditoria mensal da qualidade do registro | Baixo |

---

### Legenda e critérios de decisão

**AUTO** só quando **as quatro** condições valem:
1. **Sinal textual forte** no D2: termo distintivo com frequência na categoria pelo menos 10× maior que fora dela, ou categoria com similaridade ≤ 0,3 com as outras.
2. **Ação reversível ou de baixo impacto** (consulta, link, fluxo com aprovação do dono).
3. **Confiança ≥ τ_alto** (proposta: 0,85, calibrar no piloto) e **prioridade diferente de Crítica**.
4. **Registro completo** do evento (Pilar 3).

**ASSISTIDO** quando há sinal, mas a ação tem custo de erro moderado ou a categoria é ambígua.

**HUMANO** quando há qualquer um destes:
- dinheiro envolvido (fila Financeiro/Comercial);
- privilégio ou segurança;
- ação física;
- confiança baixa;
- conflito de rótulo;
- domínio fora do treino.

**Sobre a fila Financeiro/Comercial:** fica **separada das 8 categorias de TI**. O classificador de TI não foi treinado nesses temas (o D2 é TI interna). Por isso, a IA só reconhece o domínio e encaminha.

**Limites:** as frequências citadas vêm do D2 (TI interna) e do D1 (sintético, usado só para contar assuntos). As taxas de acerto reais só existirão depois do treino e do piloto.
