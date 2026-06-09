# Fluxo operacional — RotaDesk

Ticket → classificação → roteamento → humano / IA

Base: relatórios DS1 (`diagnostico/output/`) e DS2 (`automacao/ds2_metrics.json`).

---

## Visão geral

```mermaid
flowchart TD
    subgraph entrada [Entrada]
        A[Ticket criado<br/>canal: Email, Chat, Phone, Social]
    end

    subgraph ack [1. Ack automático]
        B{Status inicial}
        B -->|novo| C[Envia ack imediato<br/>registra first_response_at]
        C --> D[Status: Triagem]
    end

    subgraph regras_ds1 [2. Regras DS1 - humano obrigatório]
        E{Tipo ou prioridade?}
        E -->|Refund request| HUM[ Fila HUMANA prioritária ]
        E -->|Cancellation request| HUM
        E -->|Critical| HUM
        E -->|demais| F[Segue para classificação]
    end

    subgraph classificacao [3. Classificação DS2]
        F --> G[TF-IDF + Logistic Regression<br/>8 Topic_group]
        G --> I{confidence ≥ 85%?}
        I -->|Não| REV[Fila Revisão de triagem<br/>agente confirma categoria]
        I -->|Sim| J{Categoria =<br/>Administrative rights?}
        J -->|Sim| REV
        J -->|Não| K[Auto-roteamento<br/>para fila mapeada]
    end

    subgraph filas [4. Filas Supabase]
        K --> L1[Hardware]
        K --> L2[HR Support]
        K --> L3[Access]
        K --> L4[Storage / Purchase / ...]
        REV --> M[Agente corrige rota]
        M --> L1
        HUM --> N[Atendimento humano<br/>sem auto-resolução]
    end

    subgraph pending [5. Pending Customer Response]
        N --> O{Aguardando cliente?}
        O -->|Sim| P[Status: Pending]
        P --> Q[Follow-up automático D+1, D+3]
        Q --> R{Cliente respondeu?}
        R -->|Sim| D
        R -->|Não, D+7| S[Lembrete final + alerta agente]
        R -->|Não, D+14| T[Encerramento sugerido<br/>revisão humana]
    end

    subgraph ia_opcional [6. IA opcional - baixa confiança]
        REV --> U[Segunda opinião IA<br/>fine-tuned / LLM - fase 2]
        U --> M
    end

    A --> B
    D --> E
```

---

## Estados do ticket (Supabase)

| Status | Descrição | Origem no DS1 |
|--------|-----------|---------------|
| `open` | Criado, sem ack | Open (2.819 no baseline) |
| `triagem` | Ack enviado, aguardando classificação | — |
| `pending_review` | Conf &lt; 85% ou Admin rights | — |
| `routed` | Na fila especializada | — |
| `human_required` | Refund / Cancel / Critical | Regra DS1 |
| `pending_customer` | Aguardando cliente | Pending (2.881 no baseline) |
| `closed` | Resolvido | Closed (2.769 no baseline) |

---

## Decisões de roteamento (ordem de avaliação)

```mermaid
flowchart LR
    R1[1. Refund?] -->|sim| H[Humano]
    R2[2. Cancellation?] -->|sim| H
    R3[3. Critical?] -->|sim| H
    R4[4. Classificar texto] --> R5{conf ≥ 85%?}
    R5 -->|não| REV[Revisão humana]
    R5 -->|sim| R6{Admin rights?}
    R6 -->|sim| REV
    R6 -->|não| AUTO[Fila automática]
```

A ordem garante que **metadados DS1** (tipo/prioridade) prevalecem sobre o classificador DS2.

---

## Pontos de integração Next.js + Supabase

| Etapa | Componente | Persistência |
|-------|------------|--------------|
| Criação | API Route / Server Action | `tickets` insert |
| Ack | Edge Function + email/template | `tickets.first_response_at`, `events` |
| Classificação | API Route (modelo serializado) | `tickets.topic_group`, `confidence` |
| Router | Postgres function ou app logic | `tickets.queue_id`, `status` |
| Follow-up | Supabase cron / pg_cron | `pending_reminders` |
| Painel | Next.js dashboard | views agregadas |

---

## O que este fluxo não faz

- Não fecha ticket automaticamente em Refund/Cancellation/Critical.
- Não promete reduzir `cycle_hours` como objetivo — foco em ack, Pending e triagem.
- Não une datasets DS1 e DS2 em treino; o classificador usa apenas o artefato do DS2.

---

## Referência de volumes (baseline DS1)

Para calibrar filas e capacidade no protótipo:

- **8.469** tickets no recorte analisado.
- **67,3%** sem resolução no snapshot.
- Ack ataca os **2.819 Open**; follow-up ataca os **2.881 Pending**.
