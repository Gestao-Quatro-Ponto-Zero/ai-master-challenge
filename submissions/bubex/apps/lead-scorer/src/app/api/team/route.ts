import { NextResponse } from 'next/server'
import { getTeamStats } from '@/lib/queries'

export async function GET() {
  try {
    const stats = await getTeamStats()
    return NextResponse.json(stats)
  } catch (err) {
    console.error('[api/team]', err)
    return NextResponse.json({ error: 'Failed to load team stats' }, { status: 500 })
  }
}
