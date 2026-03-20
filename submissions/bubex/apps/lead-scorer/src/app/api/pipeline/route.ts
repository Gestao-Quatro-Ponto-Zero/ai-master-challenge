import { NextRequest, NextResponse } from 'next/server'
import { queryPipeline } from '@/lib/queries'
import type { Deal } from '@/types'

function safeJson(data: unknown): NextResponse {
  return new NextResponse(
    JSON.stringify(data, (_, v) => (typeof v === 'bigint' ? Number(v) : v)),
    { headers: { 'Content-Type': 'application/json' } }
  )
}

export async function GET(req: NextRequest) {
  const p = req.nextUrl.searchParams

  try {
    const result = await queryPipeline({
      page:     Number(p.get('page')     ?? 1),
      pageSize: Number(p.get('pageSize') ?? 50),
      sort:     (p.get('sort')  ?? 'score') as keyof Deal,
      order:    (p.get('order') ?? 'desc') as 'asc' | 'desc',
      q:        p.get('q')      ?? '',
      stage:    p.get('stage')  ?? 'all',
      region:   p.get('region') ?? 'all',
      agent:    p.get('agent')  ?? 'all',
    })
    return safeJson(result)
  } catch (err) {
    console.error('[api/pipeline]', err)
    return NextResponse.json({ error: 'Failed to load pipeline' }, { status: 500 })
  }
}
