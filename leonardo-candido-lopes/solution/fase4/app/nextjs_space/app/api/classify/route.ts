export const dynamic = 'force-dynamic'

import { NextRequest, NextResponse } from 'next/server'

const API_URL = process.env.CLASSIFIER_API_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    if (!body?.text?.trim?.()) {
      return NextResponse.json(
        { detail: 'Texto do chamado não pode ser vazio.' },
        { status: 400 }
      )
    }

    const res = await fetch(`${API_URL}/classify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: body.text, channel: body.channel || 'Email' }),
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      return NextResponse.json(
        { detail: err?.detail || `Erro do backend: ${res.status}` },
        { status: res.status }
      )
    }

    const data = await res.json()
    return NextResponse.json(data)
  } catch (error: any) {
    console.error('Classify API error:', error)
    return NextResponse.json(
      { detail: 'Servidor de classificação indisponível. Verifique se o backend Python está rodando.' },
      { status: 503 }
    )
  }
}
