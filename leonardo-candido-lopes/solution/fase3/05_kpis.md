# 05 — KPIs e Instrumentação

**Desafio 002 · Fase 3** · Autor: Leonardo Candido Lopes · 08/11/2026

> **Importante.** Hoje **nenhum** destes KPIs pode ser medido com os dados recebidos. O D1 não tem `created_at` e tem timestamps incoerentes (49,3% de resoluções antes da 1ª resposta). O D2 não tem datas nem eventos. Os KPIs abaixo só passam a existir depois do **Pilar 3 (Instrumentação)**. **Todas as metas são "proposta inicial para validação"**: devem ser recalibradas com a linha de base medida nas semanas 1–4 do piloto. Não são resultado comprovado.

Campos de evento citados: ver Pilar 3 em `02_redesign_operacional.md`.

## 1. Tabela de KPIs

| # | Nome | Definição | Fórmula | Finalidade | Dados necessários | Frequência |
|---|---|---|---|---|---|---|
| 1 | **Volume de chamados** | Tickets abertos no período, no total e por categoria, domínio, canal e prioridade | `COUNT(ticket_id)` agrupado por categoria / canal / domínio | Dimensionar equipe e alimentar o volume (V) do ROI | `created_at`, `channel`, `predicted_category`, `domain` | Diária (painel) · mensal (gestão) |
| 2 | **Taxa de classificação automática** | % de tickets classificados e roteados sem confirmação humana | `tickets com confidence ≥ τ_alto / total de tickets` | Medir a cobertura do Pilar 1 | `confidence`, `classification_mode` | Semanal |
| 3 | **Confiança média e distribuição** | Mediana e percentis (P10, P50) da confiança do classificador, por categoria | `MEDIAN(confidence)`, `P10(confidence)` por categoria | Detectar degradação do modelo (drift) e categorias frágeis (esperado: Hardware, Misc) | `confidence`, `predicted_category`, `model_version` | Semanal |
| 4 | **Taxa de erro de classificação** | % de tickets cuja categoria ou domínio foi corrigido por humano | `tickets com category_corrected = 1 / tickets classificados` (por categoria e faixa de confiança) | Precisão real em produção; gatilho de retreino | `predicted_category`, `final_category`, `corrected_by` | Semanal |
| 5 | **Taxa de automação bem-sucedida** | % das tentativas de autoatendimento concluídas sem humano e sem reabertura em 7 dias | `self_service_resolved sem reopen_7d / self_service_attempted` | Substituir a premissa ts do ROI (36/50/65%) por dado medido | `self_service_attempted`, `self_service_resolved`, `reopened_at` | Semanal |
| 6 | **Tempo de primeira resposta (TPR)** | Tempo entre abertura e primeira resposta (humana ou automática, com flag) | `MEDIAN(first_response_at − created_at)` + P90; separado por automático/humano | Medir agilidade percebida | `created_at`, `first_response_at`, `response_type` | Diária |
| 7 | **Tempo de resolução (TR)** | Tempo entre abertura e resolução, por categoria e prioridade | `MEDIAN(resolved_at − created_at)` + P90 por categoria × prioridade | Identificar gargalos reais (o que o D1 não permitiu) | `created_at`, `resolved_at`, `category`, `priority_final` | Semanal |
| 8 | **Cumprimento de SLA** | % de tickets resolvidos dentro do alvo da sua prioridade e categoria | `tickets com TR ≤ SLA_alvo(prioridade) / tickets resolvidos` | Compromisso com o cliente interno; meta contratual | TR, `priority_final`, tabela de SLA-alvo | Semanal · mensal |
| 9 | **Resolução no primeiro contato (FCR)** | % resolvidos na primeira interação, sem transferência, escalonamento ou reabertura | `tickets com reassign_count = 0 E escalated = 0 E reopen = 0 E interactions = 1 / resolvidos` | Eficiência e experiência do usuário | `reassign_count`, `escalated_n2_at`, `reopened_at`, `interaction_count` | Mensal |
| 10 | **Taxa de escalonamento N2** | % de tickets escalados para N2, por categoria e motivo | `tickets com escalated_n2_at preenchido / total` | Calibrar o N1 e identificar lacunas da base de conhecimento | `escalated_n2_at`, `escalation_reason` | Semanal |
| 11 | **Taxa de reabertura** | % de tickets resolvidos e reabertos em até 7 dias; separar autoatendimento de humano | `tickets reopened ≤ 7d / resolvidos` | Qualidade da resolução; alimenta a premissa r do ROI | `resolved_at`, `reopened_at`, `resolution_type` | Semanal |
| 12 | **Satisfação (CSAT)** | % de respostas 4–5 numa escala de 1–5, mais a taxa de resposta | `respostas ∈ {4,5} / total de respostas` e `respostas / tickets fechados` | Experiência; detectar autoatendimento que frustra (Gartner: 45% das falhas vêm de "não entendeu minha intenção") | `csat`, `resolution_type`, `category` | Mensal |
| 13 | **Capacidade operacional liberada (KPI derivado)** | Horas de agente poupadas por mês | `[S × (1−r) × TMA_cat − S × r × k × TMA_cat + V × tri − F × tf] / 60`, com valores **medidos** (mesma fórmula de `06_roi_model.md`) | Transformar o ROI projetado em ROI medido; separar capacidade de economia | KPIs 1, 5, 11 + tempo médio de atendimento (TMA) por categoria + tempo de triagem medido na linha de base | Mensal |
| 14 | **Taxa de reatribuição de fila** | % de tickets que mudaram de fila depois do roteamento inicial | `tickets com reassign_count ≥ 1 / total` | Medir o gargalo G2 (roteamento errado) | `queue_initial`, `queue_final`, `reassign_count` | Semanal |
| 15 | **Taxa de override de prioridade** | % de tickets com prioridade alterada pelo humano, por direção (subiu/desceu) | `priority_final ≠ priority_auto / total` | Controlar o risco de "crítico tratado como baixo" | `priority_auto`, `priority_final`, `override_reason` | Semanal |
| 16 | **Volume e tempo da fila Financeiro/Comercial** | Volume, TPR e TR da fila B2C separada | Mesmas fórmulas dos KPIs 1, 6 e 7 filtradas por `domain = financeiro_comercial` | Dimensionar a fila que o D1 sugere ter 31,5% dos tickets (sintético, a validar) | `domain`, tempos | Semanal |
| 17 | **Completude da instrumentação** | % de tickets fechados com todos os timestamps obrigatórios e consistentes | `tickets com created ≤ first_response ≤ resolved e sem nulos / fechados` | Garantir que não se repita o problema do D1 | Todos os timestamps | Semanal |

## 2. Metas iniciais (proposta inicial para validação)

| KPI | Meta proposta (piloto, 90 dias) | Racional | Status |
|---|---|---|---|
| 17 Completude da instrumentação | ≥ 98% | Sem isso, nenhum outro KPI é confiável | Proposta para validação |
| 2 Classificação automática | Medir em modo sombra; meta definida depois da calibração de τ | Depende do F1 real do modelo, ainda não treinado | Proposta para validação |
| 4 Erro de classificação (faixa de confiança alta) | ≤ 5% | O limiar τ_alto deve ser escolhido para garantir isso | Proposta para validação |
| 5 Automação bem-sucedida | ≥ 36% nas categorias elegíveis | Piso = benchmark Gartner para casos "muito simples" | Proposta para validação |
| 11 Reabertura (autoatendimento) | ≤ 10% | Igual à premissa base do ROI | Proposta para validação |
| 15 Override de prioridade para cima em tickets marcados como baixa | Monitorar; cada caso de Crítica subpriorizada é revisado | Risco alto (`07_riscos.md`) | Proposta para validação |
| 6, 7, 8 TPR, TR, SLA | **Sem meta até existir linha de base** | O D1 não permite estimar o ponto de partida | Definir na semana 5 |
| 12 CSAT | Não piorar em relação à linha de base, nem no autoatendimento | Evitar "desvio" que frustra o usuário | Proposta para validação |

## 3. Regras de apuração

- Para tempos, usar **mediana e P90**, e não média: distribuições de tempo têm caudas longas. Reportar sempre o n.
- Separar **automático × humano** e **TI × Financeiro/Comercial** em todo KPI de tempo e qualidade.
- Tickets com timestamps inconsistentes ficam fora do KPI e **entram no KPI 17**, sem descarte silencioso.
- Cada KPI tem um dono (ver `07_riscos.md`, governança) e uma versão do modelo associada.
