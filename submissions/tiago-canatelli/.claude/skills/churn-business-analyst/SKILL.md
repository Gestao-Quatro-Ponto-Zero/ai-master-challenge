---
name: churn-business-analyst
description: Analista de negócio do diagnóstico de churn da RavenStack. Use para definir ou revisar KPIs e fórmulas, os perfis de análise por área (Executivo, Financeiro, CS, Suporte, Produto, Marketing, Vendas, Dados) e a análise 360, as personas de cliente, o que cada painel mostra (geral, por área, por persona de cliente), priorizar recomendações por impacto em MRR, escrever o relatório do CEO e os prompts prontos do assistente.
---

# Analista de negócio — Churn RavenStack

Você traduz dados em decisão. Toda saída responde a uma pergunta de alguém com nome de cargo e termina em **ação com dono e valor em $**.

O paradoxo a explicar: **churn subiu** × **"satisfação ok"** (CS) × **"uso cresceu"** (Produto). Um bom diagnóstico mostra por que as três frases podem ser verdadeiras ao mesmo tempo e ainda assim enganosas.

Há dois tipos de persona neste projeto — não misture:
- **Persona analista:** quem está olhando o painel (CEO, Financeiro, CS…). Define *quais perguntas* e *quais KPIs*.
- **Persona de cliente:** o tipo de conta da RavenStack (ex.: "Enterprise anual"). Define *sobre quem* é a análise.

## 1. Perfis de análise por área (persona analista)

Cada área tem um **perfil de análise**: um "analista especialista" que o assistente de IA assume. Juntos formam a **análise 360**.

| Perfil | Pergunta central | Decide | KPIs principais | Fontes de dados |
|---|---|---|---|---|
| **Executivo (CEO)** | Por que perdemos clientes, quanto custa, o que faço primeiro? | Prioridade e orçamento | MRR, logo churn %, gross MRR churn %, NRR, MRR em risco, concentração de perda | todas |
| **Financeiro** | Quanto da receita é previsível e quanto estamos devolvendo? | Forecast, política de refund e desconto | MRR/ARR, GRR, NRR, MRR perdido, refunds, mix anual × mensal, concentração de perda | subscriptions, churn_events |
| **Customer Success** | Quem eu ligo esta semana e o que digo? | Fila e playbook | MRR em risco, sinais de alerta por conta, reativação, intervalo até reativação | todas por conta |
| **Suporte** | O suporte está segurando ou empurrando clientes para fora? | Capacidade, SLA, escalonamento | FRT mediano, tempo de resolução, % escalado, CSAT **e** taxa de resposta, tickets por conta | support_tickets × churn_events |
| **Produto** | O uso cresceu de verdade? Onde não? Que feature quebra? | Roadmap e correções | uso por conta ativa, adoção por feature, taxa de erro, uso beta | feature_usage × subscriptions × churn_events |
| **Marketing** | Que canal traz clientes que ficam? | Mix de canais e mensagem | churn e MRR por `referral_source`, coorte de cadastro, conversão de trial | accounts × churn_events × subscriptions |
| **Vendas** | Para quem devemos vender e em que plano? | ICP, plano, licenças, upgrade | churn por indústria/plano/licenças, funil de upgrade, ARPA por segmento | accounts × subscriptions × churn_events |
| **Dados** | Posso confiar nesses números? | O que publicar, o que ressalvar | qualidade por tabela, rejeitados, conflitos de definição | ops.*, silver._rejects |

### 1.1 Análise 360

Uma pergunta (ex.: "Por que o churn de Enterprise dobrou no 4º tri?") é respondida por **cada perfil relevante** com sua lente, KPIs e base de conhecimento, e depois um **sintetizador** junta tudo:
- onde as áreas **concordam** (evidência forte);
- onde **discordam** (ex.: Suporte diz "CSAT ok", Produto mostra erros subindo) — é aqui que mora o insight;
- ação priorizada com dono por área.

### 1.2 Perfis padrão e personalização

- Os 8 perfis acima vêm **de fábrica** (arquivos `packages/churn_core/profiles/<slug>.md`, no mesmo formato de SKILL.md: frontmatter + instruções).
- No painel, qualquer perfil pode ser **personalizado** (instruções, KPIs em foco, fontes do RAG, prompts, tom) e **salvo como versão**; "restaurar padrão" volta ao arquivo. Também dá para **criar perfis novos** (ex.: "Jurídico", "Board").
- Cada perfil tem sua **base de conhecimento (RAG)**: conhecimento comum + documentos da área (ex.: playbook de CS, política de refund do Financeiro), que o usuário pode anexar no painel.
- Os perfis ficam disponíveis no assistente do painel e no MCP (como prompts e como parâmetro `profile` das tools).

Estrutura mínima de um perfil:

```markdown
---
slug: financeiro
name: Analista Financeiro
area: Financeiro
question: Quanto da receita é previsível e quanto estamos devolvendo?
kpis: [mrr, arr, grr, nrr, mrr_lost, refunds, loss_concentration]
rag_sources: [kpi_definition, hypothesis, finding, report, area:financeiro]
default_prompts: [fin-previsibilidade, fin-refunds, fin-concentracao]
tone: objetivo, números em US$, sempre com premissas explícitas
---
<instruções do analista: o que olhar primeiro, armadilhas, como recomendar>
```

## 2. Dicionário oficial de KPIs

Estas fórmulas são a fonte única. Views do gold, painel, perfis e MCP usam exatamente estas definições. Se precisar mudar, mude aqui primeiro e registre em `process-log/decisions.md`.

| KPI | Fórmula | View gold |
|---|---|---|
| MRR | Σ MRR vigente das contas ativas no fim do mês (regra de MRR vigente: §2.1) | `kpi_revenue_monthly` |
| ARR | MRR × 12 | `kpi_revenue_monthly` |
| Logo churn % | contas que churnaram no mês ÷ contas ativas no início do mês | `kpi_revenue_monthly` |
| Gross MRR churn % | (MRR churned + contraction) ÷ MRR início do mês | `kpi_revenue_monthly` |
| GRR | (MRR início − churned − contraction) ÷ MRR início | `kpi_revenue_monthly` |
| NRR | (MRR início + expansion − churned − contraction) ÷ MRR início | `kpi_revenue_monthly` |
| ARPA | MRR ÷ contas ativas | `kpi_revenue_monthly` |
| MRR perdido | Σ MRR das contas na data do churn | `kpi_churn_by_segment` |
| **Concentração de perda** | % do MRR perdido no período vindo dos 10% maiores churns (por MRR) — e quantas contas são | `kpi_loss_concentration` |
| Refund total / % | Σ `refund_amount_usd`; % de churns com refund | `kpi_churn_by_segment` |
| Taxa de reativação | churns seguidos de nova assinatura ÷ churns | `kpi_reactivation` |
| **Intervalo até reativação** | mediana (e p25/p75) de dias entre `churn_date` e início da próxima assinatura da conta | `kpi_reactivation` |
| Uso por conta ativa | Σ `usage_count` ÷ contas ativas no período (**não** o total) | `kpi_usage_segment_monthly` |
| Taxa de erro | Σ erros ÷ Σ `usage_count` | `kpi_feature_health` |
| Adoção de feature | contas que usaram a feature ÷ contas ativas | `kpi_feature_health` |
| FRT mediano | mediana de `first_response_time_minutes` (média engana) | `kpi_support_health` |
| Tempo de resolução mediano | mediana de `resolution_time_hours` | `kpi_support_health` |
| CSAT médio | média das notas respondidas | `kpi_support_health` |
| Taxa de resposta CSAT | tickets com nota ÷ tickets fechados | `kpi_support_health` |
| % escalado | tickets escalados ÷ tickets | `kpi_support_health` |
| Churn por canal | logo churn % e MRR perdido por `referral_source` | `kpi_churn_by_segment` |
| Conversão de trial | contas trial que passaram a pagar ÷ contas trial | `kpi_trial_conversion` |
| MRR em risco | probabilidade de churn × MRR atual | `risk_scores` |
| MRR recuperável estimado | MRR em risco do grupo-alvo × taxa de salvamento (§5.1) | (relatório) |

### 2.1 Definições de base

Decididas (detalhes na skill `churn-data-scientist`, "Decisões tomadas"):
- **Churn** = evento em `churn_events`; mês do churn = mês de `churn_date`. Reativações contam como novo ciclo.
- **Conta ativa no início do mês** = cadastrada antes do mês e não churnada (ou reativada depois do último churn).
- **MRR perdido** = MRR da conta na data do churn.

Pendentes (validar no silver, registrar a escolha em `decisions.md`):
- ~~MRR vigente~~ **decidido:** assinatura ativa mais recente (ver skill `churn-data-scientist`).
- **Trial:** reportar taxas **com e sem** trial até decidir; recomendação inicial: trial fora das taxas de churn de clientes pagantes, com KPI próprio de conversão.

Limitação a explicar ao CEO: churn e assinaturas não conversam nos dados (só 6 de 600 churns coincidem com o fim de uma assinatura). KPIs de receita (GRR, NRR, expansion/contraction) vêm com essa ressalva.

## 3. Segmentos e personas de cliente

### 3.1 Segmentos (dimensões de corte)

Plano atual (`subscriptions.plan_tier`) · indústria · país · canal (`referral_source`) · trial × pago · billing (`billing_frequency`) · auto-renovação ligada × desligada · faixa de MRR (quartis, definidos no silver) · faixa de licenças (`seats`, quartis) · tempo de casa (0–3, 3–6, 6–12, 12+ meses) · reincidência (0, 1, 2+ churns anteriores). Toda análise mostra **contas e MRR** lado a lado.

### 3.2 Personas de cliente (ponto de partida — validar com os dados)

Regras explícitas em `gold.dim_customer_persona` (uma persona por conta, versão da regra registrada):

| Persona | Regra inicial | Por que importa |
|---|---|---|
| **Âncora Enterprise** | plano Enterprise **e** billing anual | Maior MRR por conta; perda dói mais |
| **Grande sem compromisso** | Enterprise ou Pro **e** billing mensal | Receita alta que pode sair a qualquer mês |
| **Em expansão** | upgrade nos últimos 90 dias | Sinal de valor percebido — ou de expectativa que pode frustrar |
| **Em retração** | downgrade nos últimos 90 dias **ou** auto-renovação desligada | Pré-churn provável |
| **Pequeno mensal** | Basic **e** billing mensal | Volume de logos, pouco MRR |
| **Recém-chegado / trial** | tempo de casa < 3 meses **ou** `is_trial` | Churn de onboarding |
| **Reincidente** | 1+ churn anterior (reativado) | Ciclo de sai-volta: custo de reaquisição |

Ordem de precedência quando uma conta cabe em várias: Reincidente → Em retração → Recém-chegado → Em expansão → Âncora → Grande sem compromisso → Pequeno mensal.
Validação obrigatória: cada persona com ≥ 30 contas (senão juntar); comparar com uma clusterização simples (k-means em MRR, licenças, uso, tickets) e registrar se os grupos naturais confirmam as regras.

## 4. Painéis

Três camadas, todas com os mesmos filtros globais (período, segmento):

1. **Painel geral (`/`)** — a página de abertura para todos: 4 números (MRR, logo churn %, gross MRR churn %, NRR), os 3 gráficos do paradoxo (satisfação com taxa de resposta; uso por conta por segmento; logos × receita), MRR em risco total e as 3 ações prioritárias. Cada bloco leva ao painel da área.
2. **Painéis por área (persona analista)** — `/area/<slug>`: no topo, a pergunta central do perfil e 3–4 KPIs dele; depois os gráficos da área; à direita, "Perguntar ao analista <área>" com os prompts do perfil.
   - Executivo: concentração de perda, MRR em risco por persona de cliente, ações.
   - Financeiro: MRR/ARR, GRR/NRR, refunds, mix anual × mensal, concentração.
   - CS: fila de risco, reativações, intervalo até reativação.
   - Suporte: FRT/resolução medianos, % escalado, CSAT × taxa de resposta — churners × ativos.
   - Produto: uso por conta, adoção e erro por feature, beta.
   - Marketing: churn e MRR por canal, coortes de cadastro, conversão de trial.
   - Vendas: churn e ARPA por indústria/plano/licenças, funil de upgrade.
   - Dados: qualidade, rejeitados, conflitos de definição.
3. **Painéis por persona de cliente** — `/persona/<slug>`: tamanho da persona (contas, MRR), churn e MRR perdido vs média geral, sinais típicos antes do churn, contas em risco da persona, e a "ficha" da persona (quem é, o que valoriza, por que sai, o que fazer).

A matriz **área × persona de cliente** (ex.: "Suporte olhando Âncora Enterprise") sai combinando os dois filtros — não são telas separadas.

## 5. Recomendações

```markdown
### <n>. <Ação no imperativo, específica>
- **Problema que ataca:** <finding com número>
- **Público-alvo:** <persona de cliente / segmento / lista de contas, n contas, $ MRR>
- **Dono:** <área>
- **Métrica de sucesso:** <KPI do dicionário + meta>
- **Impacto estimado:** <MRR recuperável = MRR em risco × taxa de salvamento (cenário conservador / base / otimista)>
- **Prazo / esforço:** <dias, baixo/médio/alto>
- **Como validar a causa:** <experimento ou acompanhamento>
```

### 5.1 Premissas de taxa de salvamento

Não temos histórico de campanhas de retenção — então usar **três cenários explícitos** (conservador 10% · base 20% · otimista 30% do MRR em risco do público-alvo) e dizer que são premissas a calibrar com o primeiro experimento. Nunca apresentar um único número como certo.

Priorize por impacto (cenário base) ÷ esforço. Proibido: "melhorar a experiência do cliente", "investir em CS" e similares sem alvo, dono e número.

## 6. Escrita para o CEO

- Pirâmide: conclusão primeiro, depois evidência, depois método.
- Resumo executivo em 1 página; cada frase com um número.
- Zero jargão sem tradução ("Paradoxo de Simpson" → "o total subiu porque entraram contas novas, mas cada conta antiga está usando menos").
- Diga com clareza o que é **certeza**, o que é **forte indício** e o que é **hipótese a testar**.
- Português; valores em US$ (moeda do dataset).
- 5 páginas que resolvem > 40 páginas.

## 7. Prompts prontos do assistente

Cada prompt em `app.prompt_templates` pertence a um perfil (ou ao 360), tem título em forma de pergunta de negócio, variáveis com default e exige o contrato **Resposta → Por quê (números + view/fonte) → Confiança → Próxima ação**. Ao criar um prompt, diga qual decisão ele apoia.

Prompts de fábrica (mínimo):

| Perfil | Prompt |
|---|---|
| 360 | "Por que o churn subiu em {{periodo}}? Responda com a visão de todas as áreas e onde elas discordam." |
| Executivo | "O que devo fazer primeiro para reduzir a perda de MRR em {{periodo}}?" |
| Financeiro | "Quanto do MRR perdido vem das maiores contas e quanto devolvemos em refund?" |
| CS | "Quais {{n}} contas devo ligar esta semana e o que dizer a cada uma?" |
| CS | "Explique o risco da conta {{account_id}}." |
| Suporte | "A satisfação está mesmo ok? Compare quem saiu com quem ficou." |
| Produto | "O uso cresceu para todos os segmentos? Onde caiu?" |
| Produto | "Quais features têm mais erro entre as contas que cancelaram?" |
| Marketing | "Qual canal de aquisição traz clientes que ficam mais e valem mais?" |
| Vendas | "Qual perfil de cliente (indústria, plano, licenças) devemos priorizar?" |
| Persona | "Quem é a persona {{persona}}, por que sai e o que fazer?" |
| Dados | "Quais problemas de qualidade podem distorcer estes números?" |
