# DIAGRAMS.md — Pipeline Coach AI

## META
All system diagrams in Mermaid format. Reference by ID. Agents should use these when generating documentation, architecture decisions, or explanations.

---

## DIAG-01: Daily Rep Cycle (Happy Path)

```mermaid
flowchart TD
    A([🕗 07:00 — Scoring Job]) --> B[Calculate priority scores\nfor all open deals]
    B --> C[Rank Top 5 per rep]
    C --> D[Generate context_reason\nfor each item]
    D --> E([📧 08:00 — Email Sent])
    E --> F{Rep opens email?}
    F -- Yes --> G[Clicks CTA link]
    F -- No --> Z1([❌ Lost session\nRe-engage tomorrow])
    G --> H[Dashboard loads\nPrioridades do Dia]
    H --> I[Rep reads Top 5\nwith context]
    I --> J{Rep acts on item}
    J -- Executado --> K[Opens registration\nbottom sheet]
    J -- Reagendar --> L[Picks new date\nneutral score]
    J -- Ignorar --> M[Item removed\n-0.5 points]
    K --> N[1-tap: action type\n1-tap: result]
    N --> O[Auto-submit\n≤5 seconds total]
    O --> P[Execution Score\nupdates in real-time]
    P --> Q{More items?}
    Q -- Yes --> J
    Q -- No --> R([✅ Day complete\nHabit forming])
```

---

## DIAG-02: Deal Lifecycle State Machine

```mermaid
stateDiagram-v2
    [*] --> Prospecting : Deal created
    
    Prospecting --> Engaging : First contact made
    Prospecting --> Lost : Disqualified early
    
    Engaging --> Won : Contract signed
    Engaging --> Lost : Opportunity closed-lost
    Engaging --> Engaging : Follow-up / activity\n(resets contact clock)
    
    Won --> [*] : Removed from pipeline
    Lost --> [*] : Removed from pipeline
    
    note right of Prospecting
        Scoring: ACTIVE (low weight)
        Stage points: 10
        Aging clock: starts at engage_date
    end note
    
    note right of Engaging
        Scoring: ACTIVE (high weight)
        Stage points: 20
        Contact alerts: active
        Urgency boost: if >team_avg
    end note
    
    note right of Won
        Scoring: INACTIVE
        Feeds: win_rate, cycle_time KPIs
    end note
    
    note right of Lost
        Scoring: INACTIVE
        Feeds: loss_rate, conversion KPIs
    end note
```

---

## DIAG-03: Priority Score Calculation

```mermaid
flowchart LR
    subgraph INPUTS
        I1[days_without_contact]
        I2[days_in_stage]
        I3[deal_value]
        I4[stage]
        I5[team_avg_aging]
    end
    
    subgraph DIMENSIONS
        D1["D1: Tempo Sem Contato\nmax 25pts\nmin(25, days/14×25)"]
        D2["D2: Aging da Oportunidade\nmax 25pts\nmin(25, days/avg×25)"]
        D3["D3: Valor da Oportunidade\nmax 20pts\nvalue/p90_value×20"]
        D4["D4: Stage Atual\n20pts (Engaging)\n10pts (Prospecting)"]
        D5["D5: Benchmark Equipe\nmax 10pts\nclamp(0,10,days_over/7×10)"]
    end
    
    subgraph OUTPUT
        S["Priority Score\n0–100"]
        L["Score Label\nCrítico|Alto|Médio|Baixo"]
        R["context_reason\nstring"]
    end
    
    I1 --> D1
    I2 --> D2
    I2 --> D5
    I3 --> D3
    I4 --> D4
    I5 --> D2
    I5 --> D5
    
    D1 --> S
    D2 --> S
    D3 --> S
    D4 --> S
    D5 --> S
    
    S --> L
    D1 & D2 & D3 --> R
```

---

## DIAG-04: User Roles and System Interactions

```mermaid
graph TD
    subgraph USERS
        U1[👤 Vendedor\nB2B Rep]
        U2[👔 Gestor\nSales Manager]
        U3[📐 RevOps]
    end
    
    subgraph TOUCHPOINTS
        T1[📧 Email 08:00]
        T2[📱 Rep Dashboard]
        T3[🖥️ Manager Dashboard]
        T4[📊 Analytics/Reports]
    end
    
    subgraph CORE_ACTIONS
        A1[View Top 5 priorities]
        A2[Register action\n1-click]
        A3[Check Execution Score]
        A4[View benchmark]
        A5[Review team scores]
        A6[Identify at-risk reps]
        A7[Export pipeline data]
        A8[Configure scoring weights]
    end
    
    U1 --> T1 & T2
    U2 --> T2 & T3
    U3 --> T3 & T4
    
    T1 --> A1
    T2 --> A1 & A2 & A3 & A4
    T3 --> A5 & A6
    T4 --> A7 & A8
```

---

## DIAG-05: Execution Registration Flow (UX Constraint)

```mermaid
flowchart TD
    START([Rep completes action\nin real world]) --> B[Taps priority item\nor Register button]
    B --> C[Bottom sheet appears\nNOT full screen nav]
    
    C --> D{Step 1: Action Type\n1-tap required}
    D --> D1[📞 Liguei]
    D --> D2[✉️ Email]
    D --> D3[🤝 Reunião]
    D --> D4[🔄 Follow-up]
    
    D1 & D2 & D3 & D4 --> E{Step 2: Result\n1-tap required}
    E --> E1[✓ Avançou de stage]
    E --> E2[⏳ Aguardando resposta]
    E --> E3[📅 Reagendado]
    E --> E4[✗ Perdido]
    
    E1 & E2 & E3 --> F[Auto-submit\nno confirm button]
    E4 --> G[Deal-lost confirmation\nseparate flow]
    G --> F
    
    F --> H[Toast: Ação registrada ✓\n2 seconds]
    H --> I[Execution Score updates]
    I --> J[Priority item marked done\nfade + strikethrough]
    
    J --> END([⏱️ Total: ≤5 seconds\nfrom intent to done])
    
    style END fill:#2ac87a,color:#fff
    style C fill:#f0a020,color:#fff
    style F fill:#2a7be8,color:#fff
```

---

## DIAG-06: Rep Dashboard Block Hierarchy

```mermaid
graph TD
    subgraph ABOVE_FOLD["ABOVE FOLD — always visible"]
        B1["🔥 BLOCK 1\nPrioridades do Dia\n[Top 5 · Action buttons]"]
        B2["⚠️ BLOCK 2\nContas em Risco\n[Top 3 · Expand link]"]
        B3["📵 BLOCK 3\nRanking Sem Contato\n[Top 3 · Expand link]"]
        B4["📊 BLOCK 4\nExecution Score\n[Number · Bar · Goal]"]
    end
    
    subgraph BELOW_FOLD["BELOW FOLD — secondary"]
        B5["📈 Benchmark\n[Rep vs Team vs Company]"]
        B6["📋 Pipeline completo\n[Full deal list]"]
        B7["🔄 Conversão por produto"]
        B8["📅 Histórico de ações"]
    end
    
    B1 --> B2 --> B3 --> B4
    B4 -.->|scroll| B5
    B5 --> B6 --> B7 --> B8
    
    style B1 fill:#e84b2a,color:#fff
    style B2 fill:#f0a020,color:#fff
    style B3 fill:#2a7be8,color:#fff
    style B4 fill:#2ac87a,color:#fff
```

---

## DIAG-07: Data Model (Entity Relationship)

```mermaid
erDiagram
    SALES_TEAMS {
        varchar sales_agent PK
        varchar manager
        varchar regional_office
    }
    
    PRODUCTS {
        varchar product PK
        varchar series
        decimal sales_price
    }
    
    ACCOUNTS {
        varchar account PK
        varchar sector
        int year_established
        decimal revenue
        int employees
        varchar office_location
        varchar subsidiary_of
    }
    
    SALES_PIPELINE {
        varchar opportunity_id PK
        varchar sales_agent FK
        varchar product FK
        varchar account FK
        varchar deal_stage
        date engage_date
        date close_date
        decimal close_value
    }
    
    INTERACTIONS {
        uuid interaction_id PK
        varchar opportunity_id FK
        varchar rep_id FK
        varchar interaction_type
        varchar result
        timestamp interaction_date
    }
    
    DAILY_PRIORITIES {
        uuid priority_id PK
        varchar rep_id FK
        date date
        varchar opportunity_id FK
        int rank
        decimal score
        jsonb score_breakdown
        varchar context_reason
        varchar status
    }
    
    SALES_TEAMS ||--o{ SALES_PIPELINE : "rep sells"
    PRODUCTS ||--o{ SALES_PIPELINE : "product sold"
    ACCOUNTS ||--o{ SALES_PIPELINE : "account buys"
    SALES_PIPELINE ||--o{ INTERACTIONS : "interactions logged"
    SALES_TEAMS ||--o{ INTERACTIONS : "rep registers"
    SALES_PIPELINE ||--o{ DAILY_PRIORITIES : "deal prioritized"
    SALES_TEAMS ||--o{ DAILY_PRIORITIES : "rep receives"
```

---

## DIAG-08: System Architecture (High Level)

```mermaid
flowchart TB
    subgraph EXTERNAL
        CRM[CRM System\nexternal]
        EMAIL[Email Provider\nSMTP / SendGrid]
        PUSH[Push Notifications\nFCM / APNs]
    end
    
    subgraph BACKEND
        API[REST API\n/v1/]
        SCORING[Scoring Engine\nnightly batch]
        WS[WebSocket Server\nreal-time updates]
        QUEUE[Job Queue\nbull / redis]
    end
    
    subgraph DATA
        DB[(PostgreSQL\nmain db)]
        CACHE[(Redis\nsessions + cache)]
    end
    
    subgraph FRONTEND
        WEB[Web App\nNext.js]
        MOBILE[Mobile App\nReact Native]
        EMAIL_T[Email Template\nMJML]
    end
    
    CRM -->|nightly sync\nor webhook| API
    API --> DB
    API --> CACHE
    SCORING -->|reads| DB
    SCORING -->|writes daily_priorities| DB
    SCORING -->|triggers| QUEUE
    QUEUE -->|08:00 job| EMAIL
    QUEUE -->|push trigger| PUSH
    API --> WS
    WS --> MOBILE & WEB
    WEB & MOBILE -->|REST calls| API
    EMAIL -->|delivered| EMAIL_T
```

---

## DIAG-09: UX Risk Impact Map

```mermaid
quadrantChart
    title UX Risks — Probability vs Impact on Adoption
    x-axis Low Probability --> High Probability
    y-axis Low Impact --> High Impact
    quadrant-1 Address immediately
    quadrant-2 Monitor closely
    quadrant-3 Low priority
    quadrant-4 Easy wins
    Registration Friction: [0.85, 0.95]
    Cognitive Overload: [0.90, 0.92]
    Score No Impact: [0.75, 0.80]
    No Progress Feedback: [0.65, 0.70]
    No Explainability: [0.55, 0.72]
    Bad Benchmark Framing: [0.45, 0.55]
    Surveillance Perception: [0.40, 0.65]
```

---

## DIAG-10: Benchmark Module — Correct vs Incorrect Framing

```mermaid
flowchart LR
    subgraph WRONG["❌ Wrong — causes demotivation"]
        W1["'Você está pior\nque a equipe'"]
        W2["Rank: 8º de 10\n(without context)"]
        W3["Red color on metric\nno suggestion"]
    end
    
    subgraph RIGHT["✅ Right — motivates action"]
        R1["'Você está 6 dias\nacima da média'"]
        R2["Gap visualization\nwith trend arrow"]
        R3["Suggestion chip:\n'Priorize Engaging > 14d'"]
    end
    
    WRONG -->|reframe as| RIGHT
    
    style WRONG fill:#fde8e4,stroke:#e84b2a
    style RIGHT fill:#e4fdf0,stroke:#2ac87a
```
