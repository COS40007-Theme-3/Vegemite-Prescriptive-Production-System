import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import type { AllSPInputs } from '@/components/machine-input'

type SPKey = keyof Omit<AllSPInputs, 'part'>

interface RecommendedSPProps {
  recommendations: Record<SPKey, { old: number; new: number }>
  prescriptive?: {
    current: Omit<AllSPInputs, 'part'>
    recommended: Omit<AllSPInputs, 'part'>
    pGood: number
    pDowntime: number
  }
}

const SP_ROWS: { key: SPKey; label: string; unit: string }[] = [
  { key: 'ffteFeedSolidsSP',       label: 'FFTE Feed Solids',       unit: '%' },
  { key: 'ffteProductionSolidsSP', label: 'FFTE Prod. Solids',      unit: '%' },
  { key: 'ffteSteamPressureSP',    label: 'FFTE Steam Press.',      unit: 'kPa' },
  { key: 'tfeOutFlowSP',           label: 'TFE Out Flow',           unit: 'L/h' },
  { key: 'tfeProductionSolidsSP',  label: 'TFE Prod. Solids',       unit: '%' },
  { key: 'tfeVacuumPressureSP',    label: 'TFE Vacuum Press.',      unit: 'kPa' },
  { key: 'tfeSteamPressureSP',     label: 'TFE Steam Press.',       unit: 'kPa' },
]

export function RecommendedSP({ recommendations, prescriptive }: RecommendedSPProps) {
  const showPrescriptive = prescriptive != null

  const recs = SP_ROWS.map(({ key }) => ({
    key,
    old: showPrescriptive ? prescriptive!.current[key] : recommendations[key].old,
    rec: showPrescriptive ? prescriptive!.recommended[key] : recommendations[key].new,
  }))

  const anyChanged = recs.some((r) => Math.abs(r.rec - r.old) > 0.05)

  return (
    <Card className="flex h-full flex-col">
      <CardHeader className="p-4 pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold tracking-tight">Recommended SP</CardTitle>
          {showPrescriptive && (
            <Badge variant="default" className="text-xs font-semibold">
              P(good) {(prescriptive!.pGood * 100).toFixed(0)}%
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="flex flex-1 flex-col p-4 pt-2">
        <div className="flex flex-1 flex-col justify-between gap-3">
          {/* SP rows: current → recommended */}
          <div className="space-y-1.5">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Setpoints</p>
            {SP_ROWS.map(({ key, label, unit }) => {
              const r = recs.find((x) => x.key === key)!
              const changed = Math.abs(r.rec - r.old) > 0.05
              return (
                <div key={key} className="flex items-center justify-between gap-2 text-xs">
                  <span className="truncate text-muted-foreground">{label}</span>
                  <div className="flex shrink-0 items-center gap-1 tabular-nums">
                    <span className="text-muted-foreground">{r.old.toFixed(1)}</span>
                    <span className="text-muted-foreground">→</span>
                    <span className={`font-semibold ${changed ? 'text-foreground' : 'text-muted-foreground'}`}>
                      {r.rec.toFixed(1)}
                    </span>
                    <span className="text-muted-foreground">{unit}</span>
                  </div>
                </div>
              )
            })}
          </div>

          {showPrescriptive ? (
            <>
              <Separator />
              <div className="space-y-2">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">After applying</p>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">P(good)</span>
                  <span className="font-semibold tabular-nums">{(prescriptive!.pGood * 100).toFixed(0)}%</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">P(downtime)</span>
                  <span className="font-semibold tabular-nums">{(prescriptive!.pDowntime * 100).toFixed(0)}%</span>
                </div>
                <p className="text-[10px] text-muted-foreground">
                  {anyChanged
                    ? 'Apply recommended SPs to improve quality'
                    : 'Current SPs are already optimal'}
                </p>
              </div>
            </>
          ) : (
            <p className="text-[10px] text-muted-foreground">
              Run inference to get recommendations
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
