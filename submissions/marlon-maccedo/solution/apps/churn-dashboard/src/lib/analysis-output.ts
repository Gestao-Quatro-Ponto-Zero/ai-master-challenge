import fs from 'fs'
import path from 'path'
import type { ChurnAnalysisOutput } from '@/types'

const OUTPUT_PATH = path.join(process.cwd(), 'data', 'churn_analysis.json')

let cached: ChurnAnalysisOutput | null = null

export function getAnalysisOutput(): ChurnAnalysisOutput | null {
  if (cached) return cached
  try {
    const raw = fs.readFileSync(OUTPUT_PATH, 'utf-8')
    cached = JSON.parse(raw) as ChurnAnalysisOutput
    return cached
  } catch {
    return null
  }
}
