# Sales Pipeline Scoring Formula

## Overview

The Sales Pipeline Scorecard uses a comprehensive scoring algorithm to help sales teams prioritize deals by success probability. The score ranges from 0-100 and is calculated from five key factors.

## Scoring Components

### 1. **Deal Stage Score** (0-25 points)
**What it measures:** How far along the deal is in the sales pipeline

- **Prospecting** (5 points): Initial contact stage
- **Engaging** (15 points): Active negotiation stage
- **Won** (25 points): Closed won
- **Lost** (0 points): Closed lost

**Why it matters:** Deals further along the pipeline are more likely to close. Moving from Prospecting to Engaging is a significant milestone.

---

### 2. **Account Size Score** (0-20 points)
**What it measures:** The quality and stability of the customer company

Calculated as average of:
- **Employee Count** (0-10 points): More employees = larger company = more stable
- **Annual Revenue** (0-10 points): Higher revenue = better financial health

**Formula:**
```
Account Score = (normalized_employee_count + normalized_revenue) / 2
```

**Examples:**
- Startup (< 100 employees): 1-3 points
- Small business (100-500 employees): 5-8 points
- Enterprise (10,000+ employees): 18-20 points

**Why it matters:** Larger, more established companies are more likely to:
- Follow through on commitments
- Have budgets approved
- Close within expected timeframes

---

### 3. **Seller Performance Score** (0-20 points)
**What it measures:** The sales agent's historical success with similar deals

Calculated from:
- **Historical Win Rate**: Percentage of deals this agent has won
- **Average Deal Value**: Size of typical deals this agent closes

**Formula:**
```
Seller Score = (win_rate × 20) + (agent_avg_deal_value / portfolio_avg × 5)
```

**Examples:**
- New agent (20% win rate): 4-8 points
- Average agent (50% win rate): 10-12 points
- Top agent (80% win rate): 16-20 points

**Why it matters:** Experience and track record strongly predict future success. Top performers close more deals.

---

### 4. **Product Performance Score** (0-20 points)
**What it measures:** How well this specific product performs in the market

Calculated from:
- **Historical Win Rate**: What percentage of this product's sales close
- **Market Performance**: How often customers choose this product tier

**Formula:**
```
Product Score = (product_win_rate × 20)
```

**Examples:**
- Struggling product (25% win rate): 5 points
- Standard product (50% win rate): 10 points
- Popular product (80% win rate): 16 points

**Why it matters:** Some products have stronger market demand and easier sales paths than others.

---

### 5. **Time on Pipeline Score** (0-15 points)
**What it measures:** Deal velocity - how long the deal stays in pipeline

**Formula:** Rewards deals in "sweet spot" of 100-120 days:
```
if (days_on_pipeline <= 120):
    score = (days_on_pipeline / 120) × 15
else:
    score = max(0, 15 - ((days_on_pipeline - 120) / 50))
```

**Examples:**
- New deal (10 days): 1.3 points
- Optimal deal (100 days): 12.5 points
- Optimal deal (120 days): 15 points
- Stalled deal (200 days): 4.2 points
- Very stalled deal (300 days): 0 points

**Why it matters:**
- **Too short**: Might close on impulse (high risk)
- **100-120 days**: Proper due diligence done (low risk)
- **Too long**: May indicate problems - buyer changed mind, stalled negotiations, etc.

---

## Total Score Calculation

### Formula:
```
TOTAL SCORE = Stage Score + Account Score + Seller Score + Product Score + Time Score
            = (0-25) + (0-20) + (0-20) + (0-20) + (0-15)
            = 0-100
```

### Success Probability:
```
SUCCESS PROBABILITY = TOTAL SCORE / 100
```

---

## Score Ranges & Interpretation

| Score Range | Category | Win Probability | Recommended Action |
|-----------|----------|-----------------|-------------------|
| 75-100 | 🟢 Excellent | 75-100% | **Priority 1**: Focus resources, likely to close |
| 60-74 | 🔵 Good | 60-74% | **Priority 2**: Monitor closely, support as needed |
| 45-59 | 🟡 Fair | 45-59% | **Priority 3**: Check on status, may need intervention |
| 0-44 | 🔴 Poor | 0-44% | **Priority 4**: Low probability, consider revisiting |

---

## Example Scorecard

### Deal: ABC Corp - GTX Pro

| Component | Points | Reason |
|-----------|--------|---------|
| Deal Stage | 15 | In Engaging stage |
| Account Size | 18 | 5,000 employees, $200M revenue |
| Seller Performance | 16 | Agent has 75% win rate |
| Product Performance | 14 | GTX Pro has 70% close rate |
| Time on Pipeline | 12 | 100 days - optimal duration |
| **TOTAL** | **75** | **Excellent - 75% success probability** |

**Interpretation:** This is a high-priority deal. The seller is experienced, the account is solid, and the deal has been in pipeline for the right amount of time. This should close.

---

## Example Scorecard 2

### Deal: XYZ Corp - MG Special

| Component | Points | Reason |
|-----------|--------|---------|
| Deal Stage | 5 | Still in Prospecting stage |
| Account Size | 8 | 200 employees, $15M revenue - small company |
| Seller Performance | 6 | Agent has 30% win rate |
| Product Performance | 6 | MG Special has 30% close rate |
| Time on Pipeline | 2 | Only 5 days - too early to tell |
| **TOTAL** | **27** | **Poor - 27% success probability** |

**Interpretation:** This deal is very early stage. The seller has weak history, the product underperforms, and the company is small. This needs significant attention and nurturing before it's likely to close.

---

## Using This Information

### For Sales Managers:
1. Focus resources on high-scoring deals (75+)
2. Support team on medium-scoring deals (45-74)
3. Provide coaching on low-scoring opportunities
4. Review why team members score high/low
5. Analyze which products sell best

### For Sales Agents:
1. Prioritize your pipeline by score
2. Focus on high-score opportunities first
3. Understand which factors help your score
4. Learn from top performers' approaches
5. Identify products that sell for you

### For Sales Leaders:
1. Forecast revenue based on score probabilities
2. Identify coaching opportunities by score gaps
3. Optimize product portfolio
4. Set realistic targets
5. Celebrate high-performer patterns

---

## Data Sources

All calculations use actual historical data from your sales pipeline:
- **Past wins/losses**: Calculate success rates
- **Deal dates**: Measure optimal cycle times
- **Company information**: Assess account size
- **Agent history**: Evaluate seller performance
- **Product history**: Judge product viability

The algorithm adapts as new data is added - scores update automatically!

---

## Technical Notes

- Scores are recalculated daily (or when data is updated)
- Only open deals (Prospecting/Engaging) are scored
- Historical closed deals inform the scoring algorithm
- No manual adjustments - pure data-driven
- Scores can change if seller history improves/worsens

---

## Questions?

For more information, see:
- `README.md` - Full documentation
- `QUICK_START.md` - Getting started guide
- Dashboard "Score Breakdown" - Click any score to see details

