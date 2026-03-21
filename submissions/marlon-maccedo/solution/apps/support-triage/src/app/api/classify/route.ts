import { NextRequest, NextResponse } from 'next/server'
import { classifyTicket } from '@/lib/classify'

export async function POST(req: NextRequest) {
  try {
    const { text } = await req.json()
    if (!text || typeof text !== 'string') {
      return NextResponse.json({ error: 'text is required' }, { status: 400 })
    }
    const result = await classifyTicket(text.trim())
    return NextResponse.json(result)
  } catch (err) {
    console.error('[api/classify]', err)
    return NextResponse.json({ error: 'Classification failed' }, { status: 500 })
  }
}
