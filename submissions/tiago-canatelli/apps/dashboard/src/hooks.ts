import { useEffect, useState } from 'react'
import { getData, type Row } from './api'

export function useView<T = Row>(view: string, params: Record<string, string> = {}, refreshKey = 0) {
  const [data, setData] = useState<T[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const key = JSON.stringify(params)
  useEffect(() => {
    let alive = true
    setError(null)
    getData<T>(view, JSON.parse(key) as Record<string, string>)
      .then((d) => alive && setData(d))
      .catch((e: Error) => alive && setError(e.message))
    return () => { alive = false }
  }, [view, key, refreshKey])
  return { data, error, loading: data === null && error === null }
}
