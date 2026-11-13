'use client'

import { useMemo, useState } from 'react'
import { num, pct } from '@/lib/labels'
import { nextSort, sortBy, type SortDir, type SortState } from '@/lib/sort'
import { SortHeader } from './SortHeader'

export type CellFormat = 'text' | 'pct0' | 'pct1' | 'num0' | 'num3' | 'sec1'

export interface DataColumn {
  key: string
  label: string
  format?: CellFormat
  /** Direction of the first click: descending for "more is better" numbers. */
  natural?: SortDir
  info?: string
}

export interface DataRow {
  id: string
  cells: Record<string, string | number>
  highlight?: boolean
}

const FORMAT: Record<CellFormat, (v: number) => string> = {
  text: (v) => String(v),
  pct0: (v) => pct(v, 0),
  pct1: (v) => pct(v, 1),
  num0: (v) => num(v, 0),
  num3: (v) => num(v, 3),
  sec1: (v) => `${num(v, 1)} s`,
}

/** Static data table with sortable columns. The first column is the row header. Props are plain data, so server pages can render it. */
export function DataTable({ columns, rows, highlightClassName }: { columns: DataColumn[]; rows: DataRow[]; highlightClassName?: string }) {
  const [sort, setSort] = useState<SortState<string> | null>(null)
  const sorted = useMemo(() => (sort ? sortBy(rows, (r) => r.cells[sort.key] ?? '', sort.dir) : rows), [rows, sort])

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((c) => (
              <SortHeader
                key={c.key}
                label={c.label}
                numeric={c.format !== undefined && c.format !== 'text'}
                dir={sort?.key === c.key ? sort.dir : undefined}
                onSort={() => setSort((s) => nextSort(s, c.key, c.natural ?? 'asc'))}
                info={c.info}
              />
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((r) => (
            <tr key={r.id} className={r.highlight ? highlightClassName : undefined}>
              {columns.map((c, i) => {
                const v = r.cells[c.key] ?? ''
                const text = typeof v === 'number' ? FORMAT[c.format ?? 'text'](v) : v
                return i === 0 ? (
                  <th key={c.key} scope="row">
                    {text}
                  </th>
                ) : (
                  <td key={c.key} className={c.format && c.format !== 'text' ? 'num' : undefined}>
                    {text}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
