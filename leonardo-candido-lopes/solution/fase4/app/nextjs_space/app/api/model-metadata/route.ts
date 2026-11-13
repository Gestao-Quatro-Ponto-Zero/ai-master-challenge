export const dynamic = 'force-dynamic'

import { NextResponse } from 'next/server'

const API_URL = process.env.CLASSIFIER_API_URL || 'http://localhost:8000'

export async function GET() {
  try {
    const res = await fetch(`${API_URL}/model-metadata`)
    if (!res.ok) throw new Error(`Backend: ${res.status}`)
    const data = await res.json()
    return NextResponse.json(data)
  } catch (error: any) {
    console.error('Model metadata error:', error)
    return NextResponse.json({ error: 'Backend indisponível' }, { status: 503 })
  }
}
