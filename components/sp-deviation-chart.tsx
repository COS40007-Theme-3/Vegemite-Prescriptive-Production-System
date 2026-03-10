'use client'

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from '@/components/ui/chart'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  ReferenceLine,
  Cell,
} from 'recharts'

type SPKey = 'ffteFeedSolidsSP' | 'ffteProductionSolidsSP' | 'ffteSteamPressureSP' |
             'tfeOutFlowSP' | 'tfeProductionSolidsSP' | 'tfeVacuumPressureSP' | 'tfeSteamPressureSP'

type SPEntry = { old: number; new: number }

interface SPDeviationChartProps {
  recommendations: Record<SPKey, SPEntry>
  loading?: boolean
}

// Short display labels for each SP
const SP_LABELS: Record<SPKey, { short: string; unit: string }> = {
  ffteFeedSolidsSP:       { short: 'FFTE Feed',  unit: '%' },
  ffteProductionSolidsSP: { short: 'FFTE Prod',  unit: '%' },
  ffteSteamPressureSP:    { short: 'FFTE Steam', unit: 'kPa' },
  tfeOutFlowSP:           { short: 'TFE Flow',   unit: 'L/h' },
  tfeProductionSolidsSP:  { short: 'TFE Prod',   unit: '%' },
  tfeVacuumPressureSP:    { short: 'TFE Vac',    unit: 'kPa' },
  tfeSteamPressureSP:     { short: 'TFE Steam',  unit: 'kPa' },
}

const SP_KEYS: SPKey[] = [
  'ffteFeedSolidsSP', 'ffteProductionSolidsSP', 'ffteSteamPressureSP',
  'tfeOutFlowSP', 'tfeProductionSolidsSP', 'tfeVacuumPressureSP', 'tfeSteamPressureSP',
]

const chartConfig = {
  deviation: {
    label: 'SP Deviation',
    color: 'hsl(var(--chart-1))',
  },
} satisfies ChartConfig

export function SPDeviationChart({ recommendations, loading }: SPDeviationChartProps) {
  // Build chart data: deviation = ((recommended - current) / |current|) * 100
  const data = SP_KEYS.map((key) => {
    const entry = recommendations[key]
    const current = entry?.old ?? 0
    const recommended = entry?.new ?? 0
    const deviation = current !== 0
      ? ((recommended - current) / Math.abs(current)) * 100
      : 0
    return {
      name: SP_LABELS[key].short,
      unit: SP_LABELS[key].unit,
      deviation: parseFloat(deviation.toFixed(2)),
      current,
      recommended,
    }
  })

  const hasDeviation = data.some((d) => Math.abs(d.deviation) > 0.01)

  return (
    <Card className="h-full flex flex-col min-h-0">
      <CardHeader className="p-4 pb-2 space-y-1.5">
        <CardTitle className="text-sm font-semibold tracking-tight">SP Deviation</CardTitle>
        <CardDescription className="text-xs">
          % change from current to recommended setpoints — positive = increase
        </CardDescription>
      </CardHeader>
      <CardContent className="p-4 pt-0 flex-1 min-h-0">
        {loading || !hasDeviation ? (
          <div className="flex items-center justify-center h-full min-h-[300px] text-muted-foreground text-sm">
            {loading ? 'Waiting for inference…' : 'No SP changes recommended'}
          </div>
        ) : (
          <ChartContainer config={chartConfig} className="aspect-auto h-full min-h-[300px] w-full">
            <BarChart
              data={data}
              margin={{ left: 8, right: 16, top: 8, bottom: 0 }}
              accessibilityLayer
            >
              <CartesianGrid vertical={false} />
              <XAxis
                dataKey="name"
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                tick={{ fontSize: 10 }}
              />
              <YAxis
                tickLine={false}
                axisLine={false}
                tickMargin={4}
                width={40}
                tickFormatter={(v) => `${v > 0 ? '+' : ''}${v}%`}
                tick={{ fontSize: 10 }}
              />
              <ChartTooltip
                cursor={{ fill: 'hsl(var(--muted))' }}
                content={
                  <ChartTooltipContent
                    labelKey="name"
                    formatter={(value, _name, item) => {
                      const d = item.payload as typeof data[0]
                      return (
                        <div className="flex flex-col gap-1 text-xs">
                          <div className="flex justify-between gap-4">
                            <span className="text-muted-foreground">Current</span>
                            <span className="font-mono font-medium">{d.current.toFixed(1)} {d.unit}</span>
                          </div>
                          <div className="flex justify-between gap-4">
                            <span className="text-muted-foreground">Recommended</span>
                            <span className="font-mono font-medium">{d.recommended.toFixed(1)} {d.unit}</span>
                          </div>
                          <div className="flex justify-between gap-4 border-t pt-1">
                            <span className="text-muted-foreground">Change</span>
                            <span className={`font-mono font-bold ${Number(value) > 0 ? 'text-primary' : 'text-orange-500'}`}>
                              {Number(value) > 0 ? '+' : ''}{value}%
                            </span>
                          </div>
                        </div>
                      )
                    }}
                  />
                }
              />
              {/* Zero reference line */}
              <ReferenceLine y={0} stroke="hsl(var(--border))" strokeWidth={1} />
              <Bar dataKey="deviation" radius={[4, 4, 0, 0]} maxBarSize={48}>
                {data.map((entry, index) => (
                  <Cell
                    key={index}
                    fill={
                      Math.abs(entry.deviation) < 0.01
                        ? 'hsl(var(--muted-foreground))'
                        : entry.deviation > 0
                          ? 'hsl(var(--primary))'
                          : 'hsl(var(--chart-2))'
                    }
                    opacity={Math.abs(entry.deviation) < 0.01 ? 0.3 : 1}
                  />
                ))}
              </Bar>
            </BarChart>
          </ChartContainer>
        )}
      </CardContent>
    </Card>
  )
}
