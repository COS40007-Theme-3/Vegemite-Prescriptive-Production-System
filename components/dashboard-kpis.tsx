'use client'

import { Card, CardContent } from '@/components/ui/card'
import { Activity, TrendingUp, AlertCircle } from 'lucide-react'

interface DashboardKPIsProps {
  runsToday: number
  uptimePercent: number
  activeAlerts: number
}

export function DashboardKPIs({ runsToday, uptimePercent, activeAlerts }: DashboardKPIsProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-muted-foreground">Runs today</p>
              <p className="text-2xl font-bold tabular-nums">{runsToday}</p>
            </div>
            <div className="flex size-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Activity className="size-5" />
            </div>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-muted-foreground">Uptime (7d)</p>
              <p className="text-2xl font-bold tabular-nums">{uptimePercent}%</p>
            </div>
            <div className="flex size-10 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
              <TrendingUp className="size-5" />
            </div>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-muted-foreground">Active alerts</p>
              <p className="text-2xl font-bold tabular-nums">{activeAlerts}</p>
            </div>
            <div
              className={`flex size-10 items-center justify-center rounded-lg ${
                activeAlerts > 0
                  ? 'bg-destructive/10 text-destructive'
                  : 'bg-muted text-muted-foreground'
              }`}
            >
              <AlertCircle className="size-5" />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
