import Papa from 'papaparse'
import { db, type Account, type Product, type SalesTeam, type PipelineRow } from './db'

async function parseCsv<T>(path: string): Promise<T[]> {
  const response = await fetch(path)
  const text = await response.text()
  const result = Papa.parse<T>(text, { header: true, skipEmptyLines: true, dynamicTyping: true })
  return result.data
}

export async function loadDataIfNeeded(): Promise<void> {
  const existing = await db.pipeline.count()
  if (existing > 0) return // Already loaded

  const [accounts, products, teams, pipeline] = await Promise.all([
    parseCsv<Account>('/data/accounts.csv'),
    parseCsv<Product>('/data/products.csv'),
    parseCsv<SalesTeam>('/data/sales_teams.csv'),
    parseCsv<PipelineRow>('/data/sales_pipeline.csv'),
  ])

  await db.transaction('rw', [db.accounts, db.products, db.sales_teams, db.pipeline], async () => {
    await db.accounts.bulkPut(accounts)
    await db.products.bulkPut(products)
    await db.sales_teams.bulkPut(teams)
    await db.pipeline.bulkPut(pipeline)
  })
}
