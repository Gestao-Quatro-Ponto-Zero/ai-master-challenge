import { NextResponse } from 'next/server';
import { loadAndScoreDeals } from '@/lib/lead-scorer';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const data = loadAndScoreDeals();
    return NextResponse.json(data);
  } catch (err) {
    console.error('Lead scorer error:', err);
    return NextResponse.json({ error: 'Failed to load deals' }, { status: 500 });
  }
}
