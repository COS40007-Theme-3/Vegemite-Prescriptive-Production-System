'use client'

import { useEffect, useState } from 'react'

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from '@/components/ui/chart'
import { CartesianGrid, Line, LineChart, ReferenceLine, XAxis, YAxis } from 'recharts'

interface RiskTrendChartProps {
  prediction: 'GOOD' | 'LOW_BAD' | 'HIGH_BAD'
}

type RiskPoint = { time: string; risk: number }

export function RiskTrendChart({ prediction }: RiskTrendChartProps) {
  const [series, setSeries] = useState<RiskPoint[]>([])

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        // Get all available events (live window, not fixed 24h)
        const res = await fetch('/api/history?minutes=1440')
        if (!res.ok) {
          console.warn('Failed to fetch history:', res.status)
          return
        }
        const json = (await res.json()) as { risk: RiskPoint[] }
        if (!cancelled) {
          console.log('Risk chart data:', json.risk.length, 'points')
          setSeries(json.risk || [])
        }
      } catch (e) {
        console.error('Error loading risk chart:', e)
      }
    }
    load()
    const id = setInterval(load, 2000) // Update every 2s for live feel
    return () => {
      cancelled = true
      clearInterval(id)
    }
  }, [])
  const lineColor =
    prediction === 'GOOD'
      ? 'hsl(var(--primary))'
      : prediction === 'LOW_BAD'
        ? 'hsl(var(--warning))'
        : 'hsl(var(--alert))'

  const chartConfig = {
    risk: {
      label: 'Risk',
      color: lineColor,
    },
  } satisfies ChartConfig

  return (
    <Card className="h-full flex flex-col min-h-0">
      <CardHeader className="p-4 pb-2 space-y-1.5">
        <CardTitle className="text-sm font-semibold tracking-tight">Risk Trend</CardTitle>
        <CardDescription className="text-xs">Live downtime risk from model predictions</CardDescription>
      </CardHeader>
      <CardContent className="p-4 pt-0 flex-1 min-h-0">
        {series.length === 0 ? (
          <div className="flex items-center justify-center h-full min-h-[300px] text-muted-foreground text-sm">
            No data available. Waiting for model inference...
          </div>
        ) : (
          <ChartContainer config={chartConfig} className="aspect-auto h-full min-h-[300px] w-full">
            <LineChart
              data={series}
              margin={{ left: 12, right: 12, top: 4, bottom: 0 }}
              accessibilityLayer
            >
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="time"
              tickLine={false}
              axisLine={false}
              tickMargin={8}
            />
            <YAxis tickLine={false} axisLine={false} tickMargin={8} width={28} />
            <ChartTooltip
              cursor={false}
              content={
                <ChartTooltipContent
                  labelKey="time"
                  formatter={(value, _name, item) => (
                    <>
                      <div
                        className="h-2.5 w-2.5 shrink-0 rounded-[2px]"
                        style={{ backgroundColor: item.color ?? lineColor }}
                      />
                      <div className="flex flex-1 justify-between items-center min-w-0 gap-2">
                        <span className="text-muted-foreground">Risk</span>
                        <span className="font-mono font-medium tabular-nums text-foreground">
                          {value}%
                        </span>
                      </div>
                    </>
                  )}
                />
              }
            />
            <ReferenceLine y={20} stroke="hsl(var(--warning))" strokeDasharray="3 3" opacity={0.5} />
            <Line
              type="monotone"
              dataKey="risk"
              stroke={lineColor}
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ChartContainer>
        )}
      </CardContent>
    </Card>
  )
}
