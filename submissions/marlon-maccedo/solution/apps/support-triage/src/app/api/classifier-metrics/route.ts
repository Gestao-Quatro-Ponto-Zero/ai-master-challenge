import { NextResponse } from 'next/server'
import { getClassifierOutput } from '@/lib/notebook-output'

export async function GET() {
  const data = getClassifierOutput()
  if (!data) {
    return NextResponse.json({ error: 'notebook not executed yet' }, { status: 404 })
  }
  return NextResponse.json(data)
}
