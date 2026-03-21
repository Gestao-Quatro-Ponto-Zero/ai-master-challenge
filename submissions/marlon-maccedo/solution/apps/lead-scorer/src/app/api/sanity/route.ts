import { NextResponse } from 'next/server'
import { queryPipeline, getDashboardStats } from '@/lib/queries'

export async function GET() {
  const failures: string[] = []

  try {
    const { deals, total } = await queryPipeline({ pageSize: 9999 })
    const stats = await getDashboardStats()

    // 1. Total de deals entre 1000–5000
    if (total < 1000 || total > 5000) {
      failures.push(`total_deals out of range: ${total} (expected 1000–5000)`)
    }

    // 2. Score entre 0–100 em todos os deals
    const badScore = deals.filter(d => d.score < 0 || d.score > 100)
    if (badScore.length > 0) {
      failures.push(`${badScore.length} deals with score out of 0–100 range`)
    }

    // 3. Média de score de Engaging > média de Prospecting
    const engaging    = deals.filter(d => d.deal_stage === 'Engaging')
    const prospecting = deals.filter(d => d.deal_stage === 'Prospecting')
    if (engaging.length > 0 && prospecting.length > 0) {
      const avgEngage  = engaging.reduce((s, d) => s + d.score, 0) / engaging.length
      const avgProspec = prospecting.reduce((s, d) => s + d.score, 0) / prospecting.length
      if (avgEngage <= avgProspec) {
        failures.push(`avg score Engaging (${avgEngage.toFixed(1)}) should be > Prospecting (${avgProspec.toFixed(1)})`)
      }
    }

    // 4. Soma dos componentes nunca ultrapassa 101 (margem de arredondamento)
    const overflowDeals = deals.filter(d => {
      const componentSum = d.score_stage + d.score_value + d.score_account + d.score_time + d.score_series + d.score_agent
      return componentSum > 101
    })
    if (overflowDeals.length > 0) {
      failures.push(`${overflowDeals.length} deals with component sum > 101`)
    }

    const ok = failures.length === 0
    return NextResponse.json({
      ok,
      total_deals: total,
      avg_score: stats.avgScore,
      hot: stats.hot,
      warm: stats.warm,
      cold: stats.cold,
      checks: {
        total_in_range:             total >= 1000 && total <= 5000,
        all_scores_in_range:        badScore.length === 0,
        engaging_score_gt_prospec:  engaging.length > 0 && prospecting.length > 0
          ? (engaging.reduce((s, d) => s + d.score, 0) / engaging.length) >
            (prospecting.reduce((s, d) => s + d.score, 0) / prospecting.length)
          : null,
        no_component_overflow:      overflowDeals.length === 0,
      },
      failures,
    }, { status: ok ? 200 : 500 })
  } catch (err) {
    return NextResponse.json({ ok: false, error: String(err) }, { status: 500 })
  }
}
