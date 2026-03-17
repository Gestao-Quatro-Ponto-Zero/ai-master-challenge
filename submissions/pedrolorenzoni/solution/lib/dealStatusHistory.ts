import type { DealStage } from './data'

export interface DealStatusHistoryEntry {
  from: DealStage
  to: DealStage
  changedAt: string
}
