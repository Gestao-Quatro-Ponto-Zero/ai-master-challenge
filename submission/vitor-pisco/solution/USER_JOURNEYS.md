# USER_JOURNEYS.md — Pipeline Coach AI

## META
All flows described as state machines. Each step includes: action, system response, success path, failure path.

---

## JOURNEY-01: Daily Rep Cycle (PRIMARY — runs every business day)

### Trigger
Automated email sent at 08:00 to all active reps.

### Happy Path
```
STATE: Email delivered
  → Rep opens email
  → Rep clicks CTA link
  → Dashboard loads (target: <2s)
  → Rep sees "Prioridades do dia" block
  → Rep reads Top 5 action items
  → Rep executes Action #1 (real world: makes call / sends email)
  → Rep clicks [Executado] button
  → System records execution timestamp + action type
  → Execution Score updates in real time
  → Rep continues with Actions #2-5
  → Session ends
```

### Failure Paths
| Failure Point | Symptom | Recovery |
|---------------|---------|----------|
| Email not opened | Low DAU | A/B subject lines, send-time optimization |
| Dashboard loads slow | Bounce | CDN, skeleton screens, cached priority list |
| Top 5 not relevant | Low execution rate | Retrain scoring, add rep feedback signal |
| Registration >5s | Score not updating | Simplify to 1-tap, remove all fields |
| Score has no effect | Rep stops registering | Wire score to email content + manager view |

### Exit Conditions
- All 5 actions addressed (executed / rescheduled / ignored)
- Rep closes app
- 23:59 — day resets, new priorities generated for next day

---

## JOURNEY-02: At-Risk Account Response

### Trigger
Rep sees "Contas em risco" block — account with aging > team average.

### Flow
```
Rep views at-risk account card
  → Card shows: account name | product | days over avg | stage
  → Rep taps account
  → Account detail opens with full context
  → Rep chooses action:
      [Ligar agora] → opens phone / copies number → marks as contacted
      [Enviar email] → opens email draft with pre-filled context
      [Marcar reunião] → opens calendar link
      [Ver histórico] → full interaction timeline
  → Rep executes chosen action
  → System updates last_contact_date
  → Account drops off at-risk list (if contact resets clock)
```

---

## JOURNEY-03: Execution Score Registration

### Trigger
Rep completes any pipeline action (call, email, meeting, follow-up).

### Constraint: ≤5 seconds total

### Flow
```
Rep taps [Registrar ação] (or taps action button on priority item)
  → Bottom sheet appears (NOT full screen)
  → Step 1 — Action type (required, 1-tap):
      [📞 Liguei]  [✉️ Email]  [🤝 Reunião]  [🔄 Follow-up]
  → Step 2 — Result (required, 1-tap):
      [✓ Avançou de stage]  [⏳ Aguardando]  [📅 Reagendado]  [✗ Perdido]
  → Auto-submit after Step 2 (no confirm button)
  → Toast: "Ação registrada ✓" (2 seconds)
  → Execution Score updates
  → Priority item marked as done
```

### Validation Rules
- Both steps required
- No free-text fields
- No date pickers (uses current timestamp)
- If [✗ Perdido] selected → trigger deal-lost confirmation flow (separate)

---

## JOURNEY-04: Manager Weekly Review

### Trigger
Manager opens dashboard (no push trigger — manager-initiated).

### Flow
```
Manager opens Manager Dashboard
  → Default view: current week, all reps, all products
  → Block 1: Execution Score ranking (sorted desc)
      → Tap rep → rep detail page
  → Block 2: Avg aging by rep (sorted desc — worst first)
      → Outlier rep highlighted in red (>20% above team avg)
  → Block 3: No-contact ranking
      → Shows which reps have most cold accounts
  → Block 4: Pipeline coverage
      → Rep vs quota, coverage ratio
  → Block 5: Conversion by product/rep
      → Heatmap or sorted table

Manager applies filters:
  → office filter → narrows to regional view
  → product filter → narrows to product line
  → period filter → last 7d / 30d / 90d / custom

Manager finds underperforming rep:
  → Opens rep detail
  → Sees: execution score trend | aging trend | contact frequency
  → Takes action: schedules 1:1 / sends note (outside product scope)
```

---

## JOURNEY-05: New Rep Onboarding

### Trigger
New rep account created in system.

### Flow
```
Day 0:
  → Admin creates rep account
  → System imports rep's deals from CRM (webhook or nightly sync)
  → Initial scoring run executes
  → Onboarding email sent: "Your pipeline is ready"

Day 1 (first use):
  → Rep receives first daily email at 08:00
  → Email includes: intro message + link to 2-min video walkthrough
  → Dashboard has onboarding overlay (dismissible):
      [1/3] "Aqui estão suas prioridades de hoje"
      [2/3] "Registre em 1 clique"
      [3/3] "Acompanhe seu score"
  → After 3 overlays dismissed → normal experience

Day 7:
  → Check: has rep registered ≥3 actions?
  → No → trigger re-engagement email with specific how-to
  → Yes → remove onboarding hints, full experience
```

---

## JOURNEY-06: AI Suggestion Generation (System Flow)

### Trigger
Nightly batch job at 07:00 (before 08:00 email).

### Flow
```
FOR each active rep:
  1. Fetch all open deals (stage IN [Prospecting, Engaging])
  2. Calculate score for each deal (see SCORING_ENGINE.md)
  3. Sort deals by score DESC
  4. Take top 5
  5. For each: generate action_label + context_reason
  6. Persist to daily_priorities table
  7. Mark as "ready" for email job

Email job at 08:00:
  → Reads daily_priorities for each rep
  → Renders email template
  → Sends via email provider
  → Logs delivery status

IF deal score changes intraday (e.g., rep closes a deal):
  → Re-run scoring for that rep
  → Update dashboard in real-time (websocket or polling)
  → Do NOT resend email (email is morning-only)
```

---

## STATE TRANSITIONS: Deal Lifecycle

```
[Lead Created] 
    → stage: Prospecting
    → scoring: active (low urgency weight)
    
[First Contact Made]
    → stage: Engaging  
    → scoring: active (higher urgency weight)
    → triggers: aging clock starts
    
[Won]
    → stage: Won
    → scoring: inactive (removed from priority queue)
    → triggers: updates conversion metrics
    
[Lost]
    → stage: Lost
    → scoring: inactive
    → triggers: updates conversion metrics, loss reason captured
    
[Stale — no contact >N days]
    → stage: unchanged
    → scoring: urgency boost applied
    → triggers: appears in at-risk block + no-contact ranking
```
