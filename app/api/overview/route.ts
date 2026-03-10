import { NextResponse } from 'next/server'
import { getEventsSince } from '@/lib/activity-log'

// Simple production-like overview metrics derived from recent inference events.
// In real factory: would come from historian / SCADA / MES; here we use model logs.

export async function GET() {
  try {
    const last24h = getEventsSince(24 * 60 * 60 * 1000)
    const last7d = getEventsSince(7 * 24 * 60 * 60 * 1000)
    const last1h = getEventsSince(60 * 60 * 1000)

    const runsToday = last24h.length

    const avgRisk7d =
      last7d.length > 0 ? last7d.reduce((acc, e) => acc + e.pDowntime, 0) / last7d.length : 0
    const uptimePercent = Math.max(0, Math.min(100, 100 - avgRisk7d * 100))

    const activeAlerts = last1h.filter(
      (e) => e.prediction === 'HIGH_BAD' || e.pDowntime >= 0.3,
    ).length

    return NextResponse.json({
      runsToday,
      uptimePercent: Number(uptimePercent.toFixed(1)),
      activeAlerts,
    })
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : 'Failed to compute overview' },
      { status: 500 },
    )
  }
}

