import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'

interface DowntimeRiskProps {
  risk: number
  affectedSystem: string
  loading?: boolean
}

export function DowntimeRisk({ risk, affectedSystem, loading }: DowntimeRiskProps) {
  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="p-4 pb-2 space-y-1.5">
        <CardTitle className="text-sm font-semibold tracking-tight">Downtime Risk</CardTitle>
        <CardDescription className="text-xs">Anomaly estimate from current settings</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-1 flex-col justify-center gap-3 p-4 pt-0">
        {loading ? (
          <p className="text-xs text-muted-foreground animate-pulse">Running inference…</p>
        ) : (
          <>
            <div className="flex items-baseline gap-1.5">
              <span className="text-2xl font-bold tabular-nums tracking-tight">{risk}</span>
              <span className="text-sm font-semibold text-muted-foreground">%</span>
            </div>
            <Progress value={risk} max={100} className="h-2" />
            <span className="block truncate text-xs text-muted-foreground">{affectedSystem}</span>
          </>
        )}
      </CardContent>
    </Card>
  )
}
