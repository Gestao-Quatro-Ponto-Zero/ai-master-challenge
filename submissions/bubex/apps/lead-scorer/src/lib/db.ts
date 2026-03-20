import path from 'path'
import { DuckDBInstance } from '@duckdb/node-api'

let instance: DuckDBInstance | null = null

async function getInstance(): Promise<DuckDBInstance> {
  if (!instance) {
    instance = await DuckDBInstance.create(':memory:')
  }
  return instance
}

const DATA = path.join(process.cwd(), 'data')

/** Returns a DuckDB read_csv_auto() expression for a file in /data */
export function csv(filename: string): string {
  const p = path.join(DATA, filename).replace(/\\/g, '/')
  return `read_csv_auto('${p}')`
}

// DuckDB returns some integer columns as BigInt — convert to Number for JSON safety
function sanitize(rows: Record<string, unknown>[]): Record<string, unknown>[] {
  return rows.map(row =>
    Object.fromEntries(
      Object.entries(row).map(([k, v]) => [k, typeof v === 'bigint' ? Number(v) : v])
    )
  )
}

export async function query<T = Record<string, unknown>>(sql: string): Promise<T[]> {
  const db = await getInstance()
  const conn = await db.connect()
  try {
    const reader = await conn.runAndReadAll(sql)
    return sanitize(reader.getRowObjectsJS() as Record<string, unknown>[]) as T[]
  } finally {
    conn.closeSync()
  }
}
