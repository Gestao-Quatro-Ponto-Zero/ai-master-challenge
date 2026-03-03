/**
 * @module usePipelineData
 *
 * React hook that manages the full pipeline data lifecycle:
 * CSV loading → IndexedDB population → score computation → state.
 *
 * Separates all data-fetching concerns from the view layer so components
 * only need to declare what data they need, not how to obtain it.
 */

import { useEffect, useState } from 'react'
import { loadDataIfNeeded } from '../loader'
import { computeScoredDeals, type ScoredDeal } from '../scoring'

/** Represents the async lifecycle of the pipeline data load. */
export type LoadState = 'idle' | 'loading' | 'ready' | 'error'

/**
 * Loads CSV data into IndexedDB on first use, then computes scored deals.
 *
 * On subsequent renders the IndexedDB check in `loadDataIfNeeded` short-circuits,
 * so reloading the page skips the CSV parse step entirely.
 *
 * @returns
 *   - `deals`  — sorted array of scored active deals (empty while loading)
 *   - `state`  — current lifecycle state for rendering load/error screens
 */
export function usePipelineData(): { deals: ScoredDeal[]; state: LoadState } {
  const [state, setState] = useState<LoadState>('idle')
  const [deals, setDeals] = useState<ScoredDeal[]>([])

  useEffect(() => {
    setState('loading')
    loadDataIfNeeded()
      .then(() => computeScoredDeals())
      .then((scored) => {
        setDeals(scored)
        setState('ready')
      })
      .catch(() => setState('error'))
  }, [])

  return { deals, state }
}
