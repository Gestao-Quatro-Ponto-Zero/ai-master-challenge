# 02 — Redesign Operacional · 3 Pilares

**Desafio 002 · Fase 3** · Autor: Leonardo Candido Lopes · 08/11/2026
Legenda: **[EVIDÊNCIA]** medido nos dados · **[INTERPRETAÇÃO]** leitura dos números · **[HIPÓTESE]** comportamento operacional plausível · **[PROJEÇÃO]** melhoria esperada.

---

## 1. Visão geral do modelo proposto

O modelo atual, como os dados o deixam ver, tem três problemas:
- a categoria do ticket não descreve o problema (G2);
- a prioridade não muda o atendimento (G3);
- o tempo não é medido (G1).

O modelo proposto troca "todo ticket passa por triagem humana" por **"todo ticket passa por triagem automática auditável, e o humano entra onde agrega valor"**.

```
 Entrada (qualquer canal)
   └─► PILAR 1 — Triagem Inteligente: domínio → categoria → confiança → prioridade → fila
          ├─► PILAR 2 — Autoatendimento (só categorias padronizadas + confiança alta)
          └─► Agente humano (contexto enriquecido) → N2 se necessário
   PILAR 3 — Instrumentação de SLA: registra cada etapa acima e realimenta o modelo
```

**Princípios do desenho:**
1. **Nenhuma automação sem registro.** O Pilar 3 entra antes e é condição para os outros dois.
2. **A automação é proporcional à evidência.** Só ganha autoatendimento a categoria com padrão textual forte nos dados.
3. **Fora do domínio, a decisão é humana.** Temas B2C vão para a fila Financeiro/Comercial.
4. **Nada crítico é fechado automaticamente.**

---

## 2. Os 3 pilares

### Pilar 1 — Triagem Inteligente

| Etapa | O que faz | Base nos dados | Natureza |
|---|---|---|---|
| 1. Pré-processamento | Converte para minúsculas, remove pontuação, números e boilerplate de e-mail | O D2 já vem nesse formato; 38,1% das palavras são boilerplate | [EVIDÊNCIA] |
| 2. Detecção de domínio | Separa **TI interna**, **Financeiro/Comercial** (reembolso, pagamento, entrega, cancelamento, recomendação) e **Fora do escopo** | 31,5% do D1 sem categoria de TI correspondente; só 98 das top-300 palavras em comum entre D1 e D2 | [EVIDÊNCIA] + [HIPÓTESE] sobre o método (palavras-chave + classificador de domínio) |
| 3. Classificação de TI | Hardware, HR Support, Access, Miscellaneous, Storage, Purchase, Internal Project, Administrative rights | 47.602 exemplos após a limpeza; pesos por categoria; métrica F1-macro | [EVIDÊNCIA] base · [PROJEÇÃO] desempenho (não treinado ainda) |
| 4. Avaliação de confiança | **Alta** (≥ τ_alto) → segue no automático · **Média** → sugestão para o agente confirmar · **Baixa** (< τ_baixo) → triagem humana | Pares ambíguos: Hardware × Misc 0,625; Hardware × Access 0,560 | Limiares iniciais de **τ_alto = 0,85 e τ_baixo = 0,60, como proposta para calibrar no piloto** |
| 5. Priorização | Matriz impacto × urgência (padrão ITIL) + sinais no texto ("down", "cannot work", "all users") + regras de negócio (VIP, prazo). O agente pode sobrescrever | A prioridade do D1 não tem relação com nada (aleatória), então **não serve como rótulo de treino** | [HIPÓTESE] desenho baseado em regras, auditável |
| 6. Roteamento | Fila = f(domínio, categoria, prioridade, confiança). Registra o motivo da decisão | — | [PROJEÇÃO] menos transferências entre filas |

### Pilar 2 — Autoatendimento

Critério de elegibilidade: **(a)** vocabulário distintivo e padronizado, **(b)** baixa sobreposição com outras categorias, **(c)** ação de resolução repetível e de baixo risco.

| Categoria | % do D2 | Evidência de padronização | Ação automatizável | Elegibilidade |
|---|---:|---|---|---|
| **Purchase** | 5,2% | "po" em 70,6% (vs 0,6% fora); "purchased" em 65,3%; "receipts" em 47,3%; similaridade ≤ 0,24 com todas as outras | Status de pedido de compra (PO), confirmação de recebimento, instruções do sistema de compras | **Alta**, no cenário conservador |
| **Storage** | 5,8% | "folder" em 28,8% (vs 0,6%); "accept" em 27,2%; "decline" em 25,7%; "wants" em 26,8% | Fluxo de aprovação de acesso a pasta (aprovar/recusar pelo dono) e aumento de cota de mailbox dentro da política | **Alta**, no cenário conservador |
| **Access** (parte) | 14,9% | "confluence" em 19,6%; "reset" em 10,3%; "password" (70,8% dos 1.646 tickets com a palavra estão em Access) | Reset de senha, desbloqueio de conta, licença/acesso padrão via catálogo | **Média-alta.** Só os subtipos repetíveis: 50% de Access no cenário base é [HIPÓTESE] |
| Administrative rights | 3,7% | "outlook" em 28,2%; "upgrade" em 37,7% | Base de conhecimento para upgrade e instalação; concessão de privilégio **sempre humana** | Baixa (risco de segurança) |
| Hardware | 28,5% | Termos distintivos fracos (≤ 4,5% da categoria); a categoria mais ambígua | Coleta guiada de diagnóstico; a solução fica com o técnico | Assistida, não autônoma |
| HR Support · Internal Project · Miscellaneous | 42,0% | Sinal médio ou fraco; Misc é coringa | Sugestão de artigo ao agente | Não elegível nesta fase |

**[PROJEÇÃO]** Elegibilidade estimada:
- 11,0% do volume no conservador (Purchase + Storage);
- 18,4% no base (+ metade de Access);
- 25,9% no otimista (+ Access inteiro).

Taxa de sucesso: **Gartner (2024)** mede só 14% de resolução total em self-service no geral e 36% nos casos "muito simples". Por isso o autoatendimento fica restrito às categorias mais padronizadas.

### Pilar 3 — Instrumentação de SLA

| O que registrar (evento) | Por quê | Lacuna que fecha |
|---|---|---|
| `created_at` (abertura, em qualquer canal) | Âncora de todo cálculo de tempo | **O D1 não tem esse campo** (G1) |
| `classified_at`, `predicted_domain`, `predicted_category`, `confidence`, `model_version` | Auditoria da decisão automática | Rastreabilidade |
| `priority_auto`, `priority_final`, `priority_override_reason` | Medir se a prioridade muda o atendimento | G3 |
| `queue_initial`, `queue_final`, `reassign_count` | Medir erro de roteamento | G2 |
| `first_response_at` (humana ou automática, com flag) | Tempo de primeira resposta real | G1 |
| `self_service_attempted`, `self_service_resolved` | Taxa de sucesso do autoatendimento | Premissa ts do ROI |
| `escalated_n2_at`, `escalation_reason` | Taxa e motivo de escalonamento | — |
| `resolved_at`, `closed_at`, `reopened_at` | Tempo de resolução, reabertura | G1 |
| `category_corrected_by_agent` (de → para) | Erro de classificação, base de retreino | Ciclo de feedback |
| `csat`, `csat_comment` | Satisfação real | O D1 tem satisfação plana (sintética) |

Regras de validação na gravação (as falhas que o D1 tem):
- `first_response_at ≥ created_at`;
- `resolved_at ≥ first_response_at`;
- tempos em uma única fonte de relógio (UTC);
- campo obrigatório para fechar o ticket.

KPIs, fórmulas e frequência estão em `05_kpis.md`.

---

## 3. Como um chamado percorre o sistema

Exemplo hipotético, ilustrativo: *"hi please reset my confluence password account locked thanks"*.

1. **Entrada.** Chega por e-mail. O sistema grava `created_at` e o canal. **O relógio de SLA começa aqui.**
2. **NLP.** Remove saudações e boilerplate e normaliza o texto como no D2. Sobra: *reset confluence password account locked*.
3. **Domínio.** Nenhum termo financeiro (refund, payment, delivery, cancel) → **TI interna**. Se aparecesse "refund", o ticket iria para a **fila Financeiro/Comercial** e nunca seria classificado como TI.
4. **Categoria.** O classificador sugere **Access** (termos confluence/password/reset, todos distintivos de Access no D2).
5. **Confiança.** Supondo 0,93 ≥ τ_alto, a decisão é automática. Entre 0,60 e 0,85, o agente veria a sugestão e confirmaria. Abaixo de 0,60, iria para triagem humana.
6. **Prioridade.** "account locked" + usuário único → **Média**. Se o texto indicasse "all users" ou "production down", seria **Crítica**, e Crítica **nunca** entra no autoatendimento.
7. **Roteamento.** Fila Access, subtipo "reset de senha", que é elegível ao autoatendimento.
8. **Autoatendimento.** Envia o link de reset com verificação de identidade (MFA) e grava `first_response_at` com a flag de resposta automática.
9. **Confirmação.** O usuário confirma que resolveu → `resolved_at`. Se não responder em X horas, o sistema manda um lembrete e, depois, fecha por inatividade com aviso (regra para validar).
10. **Falha.** Se o usuário disser que não funcionou, o ticket vai para um **agente N1 com contexto enriquecido**: texto, categoria, confiança, ação já tentada e histórico. O usuário não repete nada.
11. **N2.** Se o N1 identificar bloqueio de política, conta privilegiada ou incidente que afeta vários usuários → escalonamento N2 com motivo registrado.
12. **Registro e aprendizado.** Correção de categoria, reabertura e nota de satisfação voltam para o conjunto de retreino e para o painel de KPIs.

O fluxograma visual completo está em `04_fluxograma.html`.

---

## 4. Onde o humano é insubstituível

| Situação | Justificativa nos dados | Natureza |
|---|---|---|
| **Fila Financeiro/Comercial** (reembolso, pagamento, entrega, cancelamento) | 31,5% do D1 está fora do domínio de treino; há envolvimento de dinheiro e risco de chargeback | [EVIDÊNCIA] escopo · [HIPÓTESE] risco |
| **Confiança baixa ou média** | Hardware × Misc com similaridade de 0,625; Misc é coringa com 14,8% do volume; 38 grupos de quase-duplicatas com categorias conflitantes mostram que **nem os rotuladores humanos concordam** | [EVIDÊNCIA] |
| **Hardware (solução física)** | Termos distintivos fracos; "disk" aparece 46,9% em Hardware e só 10,3% em Storage; a troca de peça exige técnico | [EVIDÊNCIA] + [INTERPRETAÇÃO] |
| **Concessão de direitos de administrador** | Risco de segurança; a categoria tem só 1.760 exemplos (a menor) | [EVIDÊNCIA] volume · [HIPÓTESE] risco |
| **Tickets críticos** | A prioridade do D1 é aleatória, então não há base de treino confiável para priorização automática | [EVIDÊNCIA] |
| **Escalonamento N2 e incidentes que afetam vários usuários** | Exige diagnóstico e coordenação | [HIPÓTESE] |
| **Revisão de amostras e curadoria da base** | O ruído nos rótulos (19,9% dos tickets com "password" em Hardware) só se resolve com julgamento humano | [EVIDÊNCIA] |

Não automatizar 100% é uma escolha de desenho. O alvo é automação seletiva, entre 11% e 26% do volume em autoatendimento, com o humano focado no que é ambíguo, sensível ou crítico.

---

## 5. Integração entre os pilares

| De → Para | O que flui |
|---|---|
| Pilar 3 → Pilar 1 | Correções de categoria e reaberturas viram dados de retreino; a calibração dos limiares usa a taxa real de erro por faixa de confiança |
| Pilar 1 → Pilar 2 | Só tickets com confiança alta, categoria elegível e prioridade diferente de Crítica entram no autoatendimento |
| Pilar 2 → Pilar 3 | Taxa de sucesso, tempo até resolver e satisfação do autoatendimento substituem as premissas de benchmark do ROI |
| Pilar 3 → Gestão | Painel de SLA real; decisão de expandir a elegibilidade (ex.: de metade para todo o Access) só com dados do piloto |
| Humano → todos | Overrides e escalonamentos registrados alimentam a governança (`07_riscos.md`) |

Sequência recomendada:
1. **Pilar 3** (semanas 1–4) — medir a linha de base.
2. **Pilar 1 em modo sombra** (semanas 3–8) — o modelo sugere, o humano decide, mede-se a concordância.
3. **Pilar 1 ativo + Pilar 2 em Purchase e Storage** (semanas 9–12).
4. Expansão para Access, condicionada aos KPIs.

> *Contexto profissional externo:* a ordem "instrumentar → simplificar → automatizar" segue a experiência do autor no redesign do "Link de Análise Especial" (de 2–5 dias para tempo real). Não é evidência dos datasets.
