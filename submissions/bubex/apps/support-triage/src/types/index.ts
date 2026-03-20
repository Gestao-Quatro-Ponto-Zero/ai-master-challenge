export interface DiagnosticOverview {
  totalTickets: number
  openTickets: number
  closedTickets: number
  pendingTickets: number
  avgResolutionHours: number
  avgCsat: number
  backlogRate: number // % not closed
}

export interface Bottleneck {
  channel: string
  type: string
  n: number
  avgHours: number
  avgCsat: number
}

export interface ChannelStats {
  channel: string
  total: number
  closed: number
  avgCsat: number
  avgHours: number
}

export interface TypeStats {
  type: string
  total: number
  open: number
  closed: number
  pending: number
  avgCsat: number
  avgHours: number
}

export interface PriorityStats {
  priority: string
  total: number
  avgCsat: number
  avgHours: number
}

export interface ClassifyResult {
  category: string
  confidence: number
  reasoning: string
  suggestedPriority: 'Low' | 'Medium' | 'High' | 'Critical'
  shouldAutomate: boolean
  automationReasoning: string
  mode: 'ai' | 'fallback'
}

// IT ticket categories from Dataset 2
export type ItCategory =
  | 'Hardware'
  | 'HR Support'
  | 'Access'
  | 'Storage'
  | 'Purchase'
  | 'Internal Project'
  | 'Administrative rights'
  | 'Miscellaneous'
