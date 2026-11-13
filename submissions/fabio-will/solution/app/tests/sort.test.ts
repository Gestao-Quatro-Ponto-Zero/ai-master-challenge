import { describe, expect, it } from 'vitest'
import { ariaSort, nextSort, sortBy } from '../src/lib/sort'

const rows = [
  { id: 'T-3', q: 'Diversos', p: 0.5 },
  { id: 'T-1', q: 'Acesso', p: 0.9 },
  { id: 'T-2', q: 'Armazenamento', p: 0.9 },
  { id: 'T-10', q: 'Ábaco', p: 0.1 },
]

describe('sortBy', () => {
  it('sorts numbers numerically and keeps ties in input order (stable)', () => {
    expect(sortBy(rows, (r) => r.p, 'desc').map((r) => r.id)).toEqual(['T-1', 'T-2', 'T-3', 'T-10'])
    expect(sortBy(rows, (r) => r.p, 'asc').map((r) => r.id)).toEqual(['T-10', 'T-3', 'T-1', 'T-2'])
  })

  it('sorts text in Portuguese order, accents included, and ids naturally', () => {
    expect(sortBy(rows, (r) => r.q, 'asc').map((r) => r.q)).toEqual(['Ábaco', 'Acesso', 'Armazenamento', 'Diversos'])
    expect(sortBy(rows, (r) => r.id, 'asc').map((r) => r.id)).toEqual(['T-1', 'T-2', 'T-3', 'T-10'])
  })

  it('does not mutate the input', () => {
    const before = rows.map((r) => r.id)
    sortBy(rows, (r) => r.p, 'asc')
    expect(rows.map((r) => r.id)).toEqual(before)
  })
})

describe('nextSort and ariaSort', () => {
  it('starts a new column in its natural direction and flips the active one', () => {
    const first = nextSort(null, 'conf', 'desc')
    expect(first).toEqual({ key: 'conf', dir: 'desc' })
    expect(nextSort(first, 'conf', 'desc')).toEqual({ key: 'conf', dir: 'asc' })
    expect(nextSort(first, 'id', 'asc')).toEqual({ key: 'id', dir: 'asc' })
  })

  it('announces only the sorted column', () => {
    expect(ariaSort({ key: 'conf', dir: 'desc' }, 'conf')).toBe('descending')
    expect(ariaSort({ key: 'conf', dir: 'desc' }, 'id')).toBeUndefined()
  })
})
