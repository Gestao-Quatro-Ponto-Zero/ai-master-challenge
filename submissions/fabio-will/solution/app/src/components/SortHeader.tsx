'use client'

import type { SortDir } from '@/lib/sort'
import { InfoTip } from './InfoTip'

interface Props {
  label: string
  /** Current direction when this column is the sorted one, otherwise undefined. */
  dir: SortDir | undefined
  onSort: () => void
  numeric?: boolean
  info?: string
}

function SortIcon({ dir }: { dir: SortDir | undefined }) {
  return (
    <svg className="sort-icon" viewBox="0 0 10 12" aria-hidden="true" focusable="false">
      <path d="M5 0.8 8.6 4.8H1.4z" fill="currentColor" opacity={dir === 'desc' ? 0.25 : 1} />
      <path d="M5 11.2 1.4 7.2h7.2z" fill="currentColor" opacity={dir === 'asc' ? 0.25 : 1} />
    </svg>
  )
}

/** Column header that sorts on click and announces the order through aria-sort. */
export function SortHeader({ label, dir, onSort, numeric, info }: Props) {
  return (
    <th scope="col" className={numeric ? 'num' : undefined} aria-sort={dir ? (dir === 'asc' ? 'ascending' : 'descending') : undefined}>
      <span className="th-inner">
        <button type="button" className="sort-btn" onClick={onSort}>
          {label}
          <SortIcon dir={dir} />
        </button>
        {info && <InfoTip label={label} text={info} />}
      </span>
    </th>
  )
}
