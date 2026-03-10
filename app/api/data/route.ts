import { NextRequest, NextResponse } from 'next/server'
import fs from 'node:fs/promises'
import path from 'node:path'

const DATASETS: Record<
  string,
  {
    label: string
    relPath: string
    maxRows?: number
  }
> = {
  good: {
    label: 'Production — good.csv',
    relPath: 'data/Theme3/data_02_07_2019-26-06-2020/good.csv',
    maxRows: 200,
  },
  low_bad: {
    label: 'Production — low bad.csv',
    relPath: 'data/Theme3/data_02_07_2019-26-06-2020/low bad.csv',
    maxRows: 200,
  },
  high_bad: {
    label: 'Production — high bad.csv',
    relPath: 'data/Theme3/data_02_07_2019-26-06-2020/high bad.csv',
    maxRows: 200,
  },
  infinity_yeast: {
    label: 'Infinity — Yeast Processing',
    relPath: 'data/Theme3/Infinity Data 01_05_20 - 30_06_20/Infinity_Yeast Processing 0105 - 3106.csv',
    maxRows: 200,
  },
  infinity_paste: {
    label: 'Infinity — Paste Production',
    relPath: 'data/Theme3/Infinity Data 01_05_20 - 30_06_20/Infinity_Paste Production 0105 - 3106.csv',
    maxRows: 200,
  },
  weekly_ffte: {
    label: 'Weekly — FFTE Trend 22_06 - 26_06',
    relPath: 'data/Theme3/Weekly Data 18_05_20 - 22_05_20/FFTE Trend 22_06 - 26_06.csv',
    maxRows: 200,
  },
  weekly_evap: {
    label: 'Weekly — Evaporator Trends 18_05 - 22_05',
    relPath: 'data/Theme3/Weekly Data 18_05_20 - 22_05_20/Evaporator Trends 18_05 - 22_05.csv',
    maxRows: 200,
  },
}

function parseCsv(content: string, maxRows?: number): { columns: string[]; rows: string[][] } {
  const lines = content.split(/\r?\n/).filter((l) => l.trim().length > 0)
  if (lines.length === 0) {
    return { columns: [], rows: [] }
  }
  const columns = lines[0].split(',')
  const rawRows = lines.slice(1)
  const limited = typeof maxRows === 'number' ? rawRows.slice(0, maxRows) : rawRows
  const rows = limited.map((line) => line.split(','))
  return { columns, rows }
}

export async function GET(request: NextRequest) {
  const dataset = request.nextUrl.searchParams.get('dataset') ?? 'good'
  const cfg = DATASETS[dataset]

  if (!cfg) {
    return NextResponse.json({ error: 'Unknown dataset' }, { status: 400 })
  }

  try {
    const absPath = path.join(process.cwd(), cfg.relPath)
    const buf = await fs.readFile(absPath, 'utf8')
    const { columns, rows } = parseCsv(buf, cfg.maxRows)

    return NextResponse.json({
      id: dataset,
      label: cfg.label,
      columns,
      rows,
      rowCount: rows.length,
    })
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : 'Failed to read dataset' },
      { status: 500 },
    )
  }
}

