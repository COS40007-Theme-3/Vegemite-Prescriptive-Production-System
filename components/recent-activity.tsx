'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Zap, Settings2, AlertTriangle, CheckCircle2, TrendingUp } from 'lucide-react'

export type ActivityItem = {
  id: string
  type: 'analysis' | 'recommend' | 'alert' | 'quality' | 'trend'
  message: string
  detail?: string
  status: 'success' | 'warning' | 'info'
  time: string
}

function getIcon(item: ActivityItem) {
  const cls = 'size-3.5 shrink-0'
  switch (item.type) {
    case 'analysis':  return <Zap className={cls} />
    case 'recommend': return <Settings2 className={cls} />
    case 'alert':     return <AlertTriangle className={cls} />
    case 'quality':   return <CheckCircle2 className={cls} />
    case 'trend':     return <TrendingUp className={cls} />
    default:          return <Zap className={cls} />
  }
}

const STATUS_STYLES: Record<ActivityItem['status'], string> = {
  success: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
  warning: 'bg-amber-500/10 text-amber-600 dark:text-amber-400',
  info:    'bg-muted text-muted-foreground',
}

const BADGE_VARIANTS: Record<ActivityItem['status'], 'default' | 'secondary' | 'destructive' | 'outline'> = {
  success: 'secondary',
  warning: 'outline',
  info:    'secondary',
}

export function RecentActivity() {
  const [items, setItems] = useState<ActivityItem[]>([])

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const res = await fetch('/api/activity?limit=50')
        if (!res.ok) return
        const json = (await res.json()) as {
          events: {
            id: string
            timestamp: string
            prediction: 'GOOD' | 'LOW_BAD' | 'HIGH_BAD'
            pGood: number
            pDowntime: number
            downtimeRisk: number
            ffteSP: number
            tfeSP: number
            extractTankSP: number
            recommended: { ffteSP: number; tfeSP: number; extractTankSP: number }
          }[]
        }
        if (cancelled) return
        const mapped: ActivityItem[] = json.events.map((e) => {
          const ts = new Date(e.timestamp)
          const diffSecs = Math.floor((Date.now() - ts.getTime()) / 1000)
          const diffMins = Math.floor(diffSecs / 60)
          const time =
            diffSecs < 60
              ? `${diffSecs}s ago`
              : diffMins < 60
              ? `${diffMins}m ago`
              : ts.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

          const isHighRisk = e.prediction === 'HIGH_BAD' || e.pDowntime >= 0.3
          return {
            id: e.id,
            type: isHighRisk ? 'alert' : e.prediction === 'GOOD' ? 'quality' : 'analysis',
            message:
              e.prediction === 'HIGH_BAD'
                ? 'High-risk prediction'
                : e.prediction === 'LOW_BAD'
                ? 'Low-quality prediction'
                : 'Good quality prediction',
            detail: `pGood ${(e.pGood * 100).toFixed(0)}% · pDT ${(e.pDowntime * 100).toFixed(0)}% · SP [${e.ffteSP.toFixed(1)}, ${e.tfeSP.toFixed(1)}, ${e.extractTankSP.toFixed(1)}]`,
            status: isHighRisk ? 'warning' : e.prediction === 'GOOD' ? 'success' : 'info',
            time,
          }
        })
        setItems(mapped)
      } catch (e) {
        console.error('Error loading activity:', e)
      }
    }
    load()
    const id = setInterval(load, 2000)
    return () => { cancelled = true; clearInterval(id) }
  }, [])

  return (
    <Card className="flex h-full min-h-0 flex-col">
      <CardHeader className="p-4 pb-3">
        <CardTitle className="text-sm font-semibold tracking-tight">Recent activity</CardTitle>
        <p className="text-xs text-muted-foreground">Live inference events</p>
      </CardHeader>
      <CardContent className="flex min-h-0 flex-1 flex-col p-0">
        {items.length === 0 ? (
          <div className="flex flex-1 items-center justify-center p-8 text-sm text-muted-foreground">
            No activity yet. Waiting for model inference…
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto">
            {items.map((item, i) => (
              <div
                key={item.id}
                className={`flex items-start gap-3 px-4 py-3 ${i < items.length - 1 ? 'border-b' : ''}`}
              >
                <span
                  className={`mt-0.5 inline-flex size-6 shrink-0 items-center justify-center rounded-full ${STATUS_STYLES[item.status]}`}
                >
                  {getIcon(item)}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="truncate text-sm font-medium">{item.message}</span>
                    <Badge
                      variant={BADGE_VARIANTS[item.status]}
                      className="shrink-0 px-1.5 py-0 text-[10px]"
                    >
                      {item.status === 'success' ? 'GOOD' : item.status === 'warning' ? 'RISK' : 'INFO'}
                    </Badge>
                  </div>
                  {item.detail && (
                    <p className="mt-0.5 truncate text-xs text-muted-foreground">{item.detail}</p>
                  )}
                </div>
                <span className="shrink-0 text-xs tabular-nums text-muted-foreground">{item.time}</span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
