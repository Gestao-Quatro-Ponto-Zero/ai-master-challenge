import fs from 'fs'
import path from 'path'
import type { SocialAnalysisOutput } from '@/types'

const OUTPUT_PATH = path.join(process.cwd(), 'data', 'social_analysis.json')

let cached: SocialAnalysisOutput | null = null

export function getAnalysisOutput(): SocialAnalysisOutput | null {
  if (cached) return cached
  try {
    const raw = fs.readFileSync(OUTPUT_PATH, 'utf-8')
    cached = JSON.parse(raw) as SocialAnalysisOutput
    return cached
  } catch {
    return null
  }
}
