/**
 * The Analyses catalog — the questions a revenue org actually runs, grouped by
 * the seat that asks them. Pure data (no React): consumed by the Sidebar
 * accordion AND by scripts/catalog-probe.ts, which asserts every question
 * returns a grounded answer. Curation, not machinery — each item fires the
 * same grounded chat loop as a typed question.
 */
export interface AnalysisGroup {
  role: string;
  items: { id: string; label: string; question: string }[];
}

export const ANALYSES: AnalysisGroup[] = [
  {
    role: "Sales VP",
    items: [
      {
        id: "pipeline-wall",
        label: "Pipeline vs renewal wall",
        question: "How much open pipeline do we have against the ARR that must renew in the next two quarters — are we covered?",
      },
      {
        id: "concentration",
        label: "Concentration risk",
        question: "Which 10 accounts concentrate the most ARR, and how healthy is each of them?",
      },
      {
        id: "winrate",
        label: "Win rate & cycle",
        question: "What is our opportunity win rate and average sales cycle by customer segment over the last four quarters?",
      },
    ],
  },
  {
    role: "Finance",
    items: [
      {
        id: "arr-bridge",
        label: "ARR bridge",
        question: "Build the ARR bridge for the current fiscal year: starting ARR, new business, expansion, contraction, and churn.",
      },
      {
        id: "renewal-cliff",
        label: "Renewal cliff · 90 days",
        question: "How much renewal ARR comes due in the next 90 days, and how much of it is at risk based on account health?",
      },
      {
        id: "product-mix",
        label: "Product ARR mix",
        question: "Which products carry our ARR, and is any product's revenue shrinking quarter over quarter?",
      },
    ],
  },
  {
    role: "Sales Manager",
    items: [
      {
        id: "stuck-deals",
        label: "Stuck deals",
        question: "Which open opportunities have been stuck in the same stage for more than 30 days, ranked by value?",
      },
      {
        id: "funnel",
        label: "Funnel conversion",
        question: "How do opportunities convert stage by stage, and at which stage do we lose the most value?",
      },
      {
        id: "whitespace",
        label: "Whitespace call list",
        question: "Which accounts are using more than 80% of their licensed seats — this week's expansion call list?",
      },
    ],
  },
  {
    role: "Customer Success",
    items: [
      {
        id: "churn-signature",
        label: "Churn signature",
        question: "Which accounts show falling usage AND rising support tickets over the last quarter — the early churn signature?",
      },
      {
        id: "detractor-arr",
        label: "Detractor revenue",
        question: "How much ARR sits with NPS detractors, and what do their verbatim comments complain about?",
      },
      {
        id: "qbr-brief",
        label: "QBR brief",
        question: "Prepare a QBR brief on our largest account by ARR: usage trend, support tickets, NPS, open opportunities, and renewal date.",
      },
    ],
  },
];
