import { NextRequest, NextResponse } from 'next/server'
import { getRecentEvents } from '@/lib/activity-log'

export async function GET(request: NextRequest) {
  try {
    const limit = Number(request.nextUrl.searchParams.get('limit') || '50')
    const events = getRecentEvents(limit)
    return NextResponse.json({ events })
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : 'Failed to load activity' },
      { status: 500 },
    )
  }
}

