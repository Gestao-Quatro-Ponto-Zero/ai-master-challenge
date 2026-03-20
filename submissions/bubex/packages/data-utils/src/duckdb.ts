import { Database, Connection } from '@duckdb/node-api'
import path from 'path'

let db: Database | null = null

async function getDB(): Promise<Database> {
  if (!db) {
    db = await Database.create(':memory:')
  }
  return db
}

export function dataPath(appDir: string, filename: string): string {
  return path.join(appDir, 'data', filename).replace(/\\/g, '/')
}

export async function query<T = Record<string, unknown>>(sql: string): Promise<T[]> {
  const database = await getDB()
  const conn: Connection = await database.connect()
  try {
    const result = await conn.run(sql)
    return result.getRowsJson() as T[]
  } finally {
    await conn.close()
  }
}
