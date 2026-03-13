import Dexie, { type Table } from 'dexie'

export interface Account {
  account: string
  sector: string
  year_established: number
  revenue: number
  employees: number
  office_location: string
  subsidiary_of: string
}

export interface Product {
  product: string
  series: string
  sales_price: number
}

export interface SalesTeam {
  sales_agent: string
  manager: string
  regional_office: string
}

export interface PipelineRow {
  opportunity_id: string
  sales_agent: string
  product: string
  account: string
  deal_stage: 'Prospecting' | 'Engaging' | 'Won' | 'Lost'
  engage_date: string
  close_date: string
  close_value: number
}

class SalesDB extends Dexie {
  accounts!: Table<Account, string>
  products!: Table<Product, string>
  sales_teams!: Table<SalesTeam, string>
  pipeline!: Table<PipelineRow, string>

  constructor() {
    super('SalesMasterDB')
    this.version(1).stores({
      accounts: 'account, sector, office_location',
      products: 'product, series',
      sales_teams: 'sales_agent, manager, regional_office',
      pipeline: 'opportunity_id, sales_agent, account, deal_stage, engage_date',
    })
  }
}

export const db = new SalesDB()
