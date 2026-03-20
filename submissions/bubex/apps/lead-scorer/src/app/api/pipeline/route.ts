import { NextResponse } from 'next/server'
import { getPipeline } from '@/lib/queries'

export async function GET() {
  try {
    const deals = await getPipeline()
    return NextResponse.json(deals)
  } catch (err) {
    console.error('[api/pipeline]', err)
    return NextResponse.json({ error: 'Failed to load pipeline' }, { status: 500 })
  }
}
