// ── Core analysis types (produced by Python + DuckDB) ─────────────────────────

export interface ChurnOverview {
  totalAccounts: number
  churnedAccounts: number
  churnRate: number   // %
  mrrTotal: number
  mrrChurned: number
  mrrRetained: number
  arrTotal: number
  avgMrrChurned: number
  avgMrrRetained: number
}

export interface SegmentBreakdown {
  segment: string
  total: number
  churned: number
  churnRate: number   // %
  mrrLost: number
}

export interface FeatureComparison {
  feature: string
  avgCountChurned: number
  avgCountRetained: number
  delta: number       // retained - churned; positive = retained use more (protective)
  avgErrorChurned: number
  avgErrorRetained: number
  pValue: number | null
}

export interface SupportComparison {
  avgTicketsChurned: number
  avgTicketsRetained: number
  avgResolutionHoursChurned: number
  avgResolutionHoursRetained: number
  avgCsatChurned: number | null
  avgCsatRetained: number | null
  escalationRateChurned: number
  escalationRateRetained: number
}

export interface ChurnReason {
  reasonCode: string
  count: number
  mrrLost: number
  pct: number
}

export interface FeedbackTheme {
  theme: string
  count: number
}

export interface AtRiskAccount {
  accountId: string
  accountName: string
  industry: string
  country: string
  planTier: string
  mrr: number
  riskScore: number
  riskFlags: string[]
}

export interface ChurnByMonth {
  month: string
  count: number
  mrrLost: number
}

// ── Full analysis output (from churn_analysis.json) ───────────────────────────

export interface ChurnAnalysisOutput {
  overview: ChurnOverview
  segments: {
    by_industry: SegmentBreakdown[]
    by_channel: SegmentBreakdown[]
    by_plan: SegmentBreakdown[]
    by_country: SegmentBreakdown[]
  }
  featureAnalysis: {
    features: FeatureComparison[]
    protectiveFeatures: string[]
    warningFeatures: string[]
  }
  supportAnalysis: SupportComparison
  churnReasons: {
    reasonBreakdown: ChurnReason[]
    feedbackThemes: FeedbackTheme[]
  }
  atRiskAccounts: AtRiskAccount[]
  timeline: ChurnByMonth[]
}
