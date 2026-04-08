'use client'

import { useEffect, useState } from 'react'

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

type DatasetId =
  | 'good'
  | 'low_bad'
  | 'high_bad'
  | 'infinity_yeast'
  | 'infinity_paste'
  | 'weekly_ffte'
  | 'weekly_evap'

const DATASETS: { id: DatasetId; label: string }[] = [
  { id: 'good', label: 'Production — good.csv' },
  { id: 'low_bad', label: 'Production — low bad.csv' },
  { id: 'high_bad', label: 'Production — high bad.csv' },
  { id: 'infinity_yeast', label: 'Infinity — Yeast Processing' },
  { id: 'infinity_paste', label: 'Infinity — Paste Production' },
  { id: 'weekly_ffte', label: 'Weekly — FFTE Trend 22_06 - 26_06' },
  { id: 'weekly_evap', label: 'Weekly — Evaporator Trends 18_05 - 22_05' },
]

type DataResponse = {
  id: string
  label: string
  columns: string[]
  rows: string[][]
  rowCount: number
  error?: string
}

export default function DataPage() {
  const [dataset, setDataset] = useState<DatasetId>('good')
  const [data, setData] = useState<DataResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch(`/api/data?dataset=${dataset}`)
        if (!res.ok) {
          const msg = await res.text()
          throw new Error(msg || 'Failed to load dataset')
        }
        const json = (await res.json()) as DataResponse
        if (!cancelled) {
          setData(json)
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : 'Failed to load dataset')
          setData(null)
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [dataset])

  return (
    <main className="flex h-full min-h-0 flex-col gap-4 p-4 lg:p-6">
      <div className="flex shrink-0 flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-foreground">Data</h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            Inspect production, Infinity and weekly CSV feeds behind the models.
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <span className="text-xs text-muted-foreground">Dataset</span>
          <Select value={dataset} onValueChange={(v) => setDataset(v as DatasetId)}>
            <SelectTrigger className="h-8 w-[260px] text-xs">
              <SelectValue placeholder="Select dataset" />
            </SelectTrigger>
            <SelectContent>
              {DATASETS.map((d) => (
                <SelectItem key={d.id} value={d.id} className="text-xs">
                  {d.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <Card className="flex min-h-0 flex-1 flex-col overflow-hidden border">
        <CardHeader className="shrink-0 p-4 pb-2">
          <CardTitle className="text-sm font-semibold tracking-tight">
            {DATASETS.find((d) => d.id === dataset)?.label ?? 'Dataset'}
          </CardTitle>
          <CardDescription className="text-xs">
            Showing up to 200 rows. Use this view to understand raw inputs to the Vegemite models.
          </CardDescription>
        </CardHeader>
        <CardContent className="min-h-0 flex-1 overflow-hidden p-0 relative">
          {error ? (
            <div className="p-4 text-xs text-destructive">{error}</div>
          ) : loading || !data ? (
            <div className="p-4 text-xs text-muted-foreground">Loading dataset…</div>
          ) : data.rows.length === 0 ? (
            <div className="p-4 text-xs text-muted-foreground">No rows found in this dataset.</div>
          ) : (
            <div className="absolute inset-0 overflow-auto">
              <Table className="w-max border-separate border-spacing-0">
                <TableHeader className="sticky top-0 z-10 bg-card shadow-[0_1px_0_0_hsl(var(--border))]">
                  <TableRow>
                    {data.columns.map((col) => (
                      <TableHead key={col} className="h-11 whitespace-nowrap bg-card px-4 border-b text-xs">
                        {col}
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.rows.map((row, idx) => (
                    <TableRow key={idx} className="hover:bg-muted/40">
                      {row.map((cell, i) => (
                        <TableCell key={i} className="whitespace-nowrap px-4 py-4 text-xs tabular-nums">
                          {cell}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </main>
  )
}
