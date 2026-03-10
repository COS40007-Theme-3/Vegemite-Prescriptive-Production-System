import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface QualityResultProps {
  prediction: 'GOOD' | 'LOW_BAD' | 'HIGH_BAD'
  confidence: number
  loading?: boolean
}

export function QualityResult({ prediction, confidence, loading }: QualityResultProps) {
  const variant = prediction === 'GOOD' ? 'default' : prediction === 'LOW_BAD' ? 'secondary' : 'destructive'
  const label = prediction === 'LOW_BAD' ? 'LOW RISK' : prediction === 'HIGH_BAD' ? 'HIGH RISK' : 'GOOD'

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="p-4 pb-2 space-y-1.5">
        <CardTitle className="text-sm font-semibold tracking-tight">Quality Result</CardTitle>
        <CardDescription className="text-xs">Prediction & confidence</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-1 flex-col justify-center gap-3 p-4 pt-0">
        {loading ? (
          <p className="text-xs text-muted-foreground animate-pulse">Running inference…</p>
        ) : (
          <>
            <Badge variant={variant} className="w-fit text-xs font-semibold">{label}</Badge>
            <div className="flex items-baseline gap-1.5">
              <span className="text-2xl font-bold tabular-nums tracking-tight">{(confidence * 100).toFixed(0)}</span>
              <span className="text-lg font-semibold text-muted-foreground">%</span>
            </div>
            <span className="text-xs uppercase tracking-wider text-muted-foreground">confidence</span>
          </>
        )}
      </CardContent>
    </Card>
  )
}
