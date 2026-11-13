export type SortDir = 'asc' | 'desc'

export interface SortState<K extends string> {
  key: K
  dir: SortDir
}

const collator = new Intl.Collator('pt-BR', { sensitivity: 'base', numeric: true })

/** Stable sort by a value getter: numbers numerically, strings in Portuguese collation, ties keep input order. */
export function sortBy<T>(items: readonly T[], value: (item: T) => number | string, dir: SortDir): T[] {
  const sign = dir === 'asc' ? 1 : -1
  return items
    .map((item, index) => ({ item, index, v: value(item) }))
    .sort((a, b) => {
      const c = typeof a.v === 'number' && typeof b.v === 'number' ? a.v - b.v : collator.compare(String(a.v), String(b.v))
      return c !== 0 ? sign * c : a.index - b.index
    })
    .map((x) => x.item)
}

/** Clicking the active column flips direction; a new column starts in its natural direction. */
export function nextSort<K extends string>(current: SortState<K> | null, key: K, natural: SortDir): SortState<K> {
  if (current?.key === key) return { key, dir: current.dir === 'asc' ? 'desc' : 'asc' }
  return { key, dir: natural }
}

export const ariaSort = <K extends string>(state: SortState<K> | null, key: K): 'ascending' | 'descending' | undefined =>
  state?.key === key ? (state.dir === 'asc' ? 'ascending' : 'descending') : undefined
