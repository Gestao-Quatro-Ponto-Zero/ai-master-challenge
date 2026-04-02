# UX_RISKS.md — Pipeline Coach AI

## META
7 adoption risks identified through UX analysis. Each has: severity, failure mode, detection signal, and required mitigation. These are non-negotiable design constraints.

---

## RISK SEVERITY SCALE
- **P0 — Blocker**: Ships broken without this fixed. Will kill adoption.
- **P1 — Critical**: Will cause significant churn in first 30 days if not addressed.
- **P2 — Important**: Degrades retention but not immediate.
- **P3 — Monitor**: Low probability but worth tracking.

---

## RISK-01: Cognitive Overload on Main Screen
- **Severity**: P0
- **Probability**: Very High
- **Failure mode**: Rep opens dashboard, sees 8+ modules simultaneously, closes app within 10 seconds, never returns.
- **Detection signal**: Session duration <15s on first open; DAU drops after day 3.
- **Root cause**: Product tries to show everything at once to demonstrate value.
- **Required mitigation**:
  - Main screen: maximum 4 blocks visible above fold (no scroll)
  - Block order is fixed: Priorities → At-Risk → No-Contact → Execution Score
  - Everything else (benchmark, forecast, full history) lives in secondary navigation
  - Use progressive disclosure: "Ver mais" links, not full panels
- **Validation**: First-time rep should reach their first actionable item in <10 seconds from app open.

---

## RISK-02: Registration Friction
- **Severity**: P0
- **Probability**: Very High
- **Failure mode**: Execution Score never has data. Product loses its core differentiator. Becomes another unread dashboard.
- **Detection signal**: Execution Score <10% for >50% of active reps after week 1.
- **Root cause**: Registration flow requires form fill, navigation, or >2 taps.
- **Required mitigation**:
  - Maximum flow: 1 tap (action type) + 1 tap (result) = done
  - Bottom sheet UI, not navigation
  - No text fields
  - No date pickers (always uses current time)
  - Auto-submit after second selection (no confirm button)
  - Target: ≤5 seconds from intent to confirmation
- **Validation**: Time registration flow with 10 real reps. Median must be ≤5s.

---

## RISK-03: Execution Score Without Downstream Impact
- **Severity**: P1
- **Probability**: High
- **Failure mode**: Reps check score once, notice it changes nothing, stop caring. Registration drops to 0 within 2 weeks.
- **Detection signal**: Registration rate drops week-over-week despite onboarding.
- **Root cause**: Score is computed but not wired to any consequential system.
- **Required mitigation**:
  Score must visibly affect ≥3 of these:
  1. Email content (high score → different tone/content)
  2. Manager dashboard ranking (score is primary sort)
  3. Priority item urgency (low score rep → extra nudge)
  4. Weekly digest with score trend
  5. Gamification / badge system (optional but effective)
- **Validation**: Rep should be able to articulate "my score matters because ___" within 7 days of first use.

---

## RISK-04: No Visible Progress Feedback
- **Severity**: P1
- **Probability**: Medium-High
- **Failure mode**: Rep executes consistently but feels no sense of improvement. Motivation decays by week 3.
- **Detection signal**: Execution rate drops after initial spike; qualitative feedback: "I'm using it but don't feel it's working."
- **Root cause**: Product shows current state but not delta/trend.
- **Required mitigation**:
  - Show week-over-week delta: "Aging: 58d → 52d this week ↓6 days ✓"
  - Show small wins: "Pipeline coverage increased 22% this month"
  - Weekly summary in Friday email: "Here's what changed this week"
  - Progress indicators on benchmark (not just absolute position)
- **Validation**: After 2 weeks, rep can name at least 1 metric that improved.

---

## RISK-05: AI Recommendations Without Context (Explainability)
- **Severity**: P1
- **Probability**: Medium
- **Failure mode**: Rep ignores AI recommendations because they don't understand the reasoning. Trust never forms.
- **Detection signal**: High "Ignorar" rate on AI-recommended items vs "Executado".
- **Root cause**: Black-box recommendation without transparent reasoning.
- **Required mitigation**:
  - Every priority item must show context_reason (see SCORING_ENGINE.md)
  - Context shown inline: "14 dias sem contato · Engaging · $5.4K"
  - No recommendation without at least 1 reason tag
  - Optional: "Por que isso?" expansion with full score breakdown
- **Validation**: "Ignorar" rate should be <20% of all recommended items (reps trust most suggestions).

---

## RISK-06: Benchmark Framing Causing Demotivation
- **Severity**: P2
- **Probability**: Medium
- **Failure mode**: Reps who are below average disengage when comparison feels punitive. May also create unhealthy competition undermining team culture.
- **Detection signal**: Below-average reps have lower execution rates than above-average reps (when it should be the opposite).
- **Root cause**: Raw comparison without action path or empathetic framing.
- **Required mitigation**:

  **FORBIDDEN patterns:**
  ```
  ✗ "Você está pior que a equipe"
  ✗ "Ranking: 8º de 10"  (without context)
  ✗ Red color on below-average metric without suggestion
  ```

  **REQUIRED patterns:**
  ```
  ✓ "Você está 6 dias acima da média da equipe"
  ✓ "Sugestão: priorize follow-ups em Engaging > 14 dias"
  ✓ Comparison always followed by 1 specific action suggestion
  ```

  - Frame as gap-to-close, not rank
  - Always pair comparison with actionable suggestion
  - Use neutral language for below-average (informative, not judgmental)

---

## RISK-07: Manager Dashboard Perceived as Surveillance
- **Severity**: P2
- **Probability**: Medium (politically sensitive)
- **Failure mode**: Reps learn that manager can see their execution score in detail → reps avoid using product to avoid "being watched". Adoption collapses from social pressure.
- **Detection signal**: Rep adoption drops after team meeting where manager mentions the dashboard. Qualitative: "I don't want my boss seeing my every move."
- **Root cause**: Product design, onboarding, and positioning frame the tool as a monitoring system.
- **Required mitigation**:

  **Copy/language rules:**
  ```
  ✗ "Monitore sua equipe"
  ✗ "Veja o que cada vendedor está fazendo"
  ✓ "Ajude sua equipe a performar melhor"
  ✓ "Identifique onde o time precisa de apoio"
  ```

  - Manager dashboard headline: "Apoio à equipe", never "monitoramento"
  - Rep-facing comms: "Your score helps you improve" — not "your manager sees this"
  - Onboarding: explain what managers CAN see and CANNOT see
  - Consider: aggregate-first views for manager (team averages before individual)

---

## RISK SUMMARY TABLE

| Risk | Severity | Probability | Ships Blocked? |
|------|----------|-------------|---------------|
| RISK-01: Cognitive Overload | P0 | Very High | YES |
| RISK-02: Registration Friction | P0 | Very High | YES |
| RISK-03: Score No Impact | P1 | High | Soft block |
| RISK-04: No Progress Feedback | P1 | Med-High | No |
| RISK-05: No Explainability | P1 | Medium | No |
| RISK-06: Bad Benchmark Framing | P2 | Medium | No |
| RISK-07: Surveillance Perception | P2 | Medium | No |

**P0 risks must be resolved before any public launch.**
