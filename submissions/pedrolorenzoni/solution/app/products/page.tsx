'use client'

import { useMemo } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
  PieChart, Pie, Legend,
} from 'recharts'
import DashboardNavbar from '@/components/DashboardNavbar'
import { useAuth } from '@/context/AuthContext'
import { PRODUCTS, DEALS } from '@/lib/data'

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatPrice(n: number): string {
  return '$' + n.toLocaleString('en-US')
}

function formatRevenue(n: number): string {
  return '$' + n.toLocaleString('en-US')
}

function getPositioning(price: number): string {
  if (price >= 6000) return 'Enterprise'
  if (price >= 500) return 'Mid-Market'
  return 'SMB'
}

function getPositioningColor(pos: string): string {
  if (pos === 'Enterprise') return '#0f1a45'
  if (pos === 'Mid-Market') return '#b9915b'
  return '#60708a'
}

const SERIES_COLORS: Record<string, string> = {
  GTX: '#0f1a45',
  MG: '#af4332',
  GTK: '#b9915b',
}

// Deduplicate products (GTX Pro / GTXPro are same)
const UNIQUE_PRODUCTS = PRODUCTS.filter(p => p.product !== 'GTXPro')

// ─── Product Card ─────────────────────────────────────────────────────────────

function ProductCard({
  product,
  wonCount,
  totalCount,
  revenue,
}: {
  product: typeof PRODUCTS[0]
  wonCount: number
  totalCount: number
  revenue: number
}) {
  const pos = getPositioning(product.sales_price)
  const winRate = totalCount > 0 ? Math.round((wonCount / totalCount) * 100) : 0
  const isStrategic = product.product === 'GTK 500'
  const seriesColor = SERIES_COLORS[product.series] ?? '#60708a'

  return (
    <div
      style={{
        background: '#ffffff',
        border: isStrategic ? '2px solid #b9915b' : '1px solid rgba(0,31,53,0.12)',
        borderRadius: '16px',
        padding: '22px 20px',
        boxShadow: isStrategic ? '0 0 28px rgba(185,145,91,0.2)' : '0 0 22px rgba(0,0,0,0.07)',
        position: 'relative',
        transition: 'box-shadow 0.2s ease, border-color 0.2s ease',
      }}
      onMouseEnter={e => {
        const el = e.currentTarget as HTMLDivElement
        if (!isStrategic) {
          el.style.borderColor = '#b9915b'
          el.style.borderWidth = '2px'
        }
        el.style.boxShadow = '6px 6px 9px rgba(0,0,0,0.12)'
      }}
      onMouseLeave={e => {
        const el = e.currentTarget as HTMLDivElement
        if (!isStrategic) {
          el.style.borderColor = 'rgba(0,31,53,0.12)'
          el.style.borderWidth = '1px'
        }
        el.style.boxShadow = isStrategic ? '0 0 28px rgba(185,145,91,0.2)' : '0 0 22px rgba(0,0,0,0.07)'
      }}
    >
      {/* Strategic badge */}
      {isStrategic && (
        <div
          style={{
            position: 'absolute',
            top: '-10px',
            right: '16px',
            background: 'linear-gradient(135deg, #b9915b, #d4a96a)',
            color: '#ffffff',
            borderRadius: '9999px',
            padding: '3px 12px',
            fontSize: '11px',
            fontWeight: 700,
            letterSpacing: '0.06em',
            textTransform: 'uppercase',
            fontFamily: 'Inter, sans-serif',
            boxShadow: '0 2px 8px rgba(185,145,91,0.4)',
          }}
        >
          Strategic
        </div>
      )}

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '12px' }}>
        <h3
          style={{
            fontSize: '17px',
            fontWeight: 700,
            color: '#001f35',
            fontFamily: 'Manrope, sans-serif',
            lineHeight: 1.2,
          }}
        >
          {product.product}
        </h3>
        <span
          style={{
            background: `${seriesColor}18`,
            color: seriesColor,
            borderRadius: '9999px',
            padding: '3px 10px',
            fontSize: '11px',
            fontWeight: 700,
            fontFamily: 'Inter, sans-serif',
            flexShrink: 0,
            marginLeft: '8px',
          }}
        >
          {product.series}
        </span>
      </div>

      {/* Price */}
      <p
        style={{
          fontSize: '26px',
          fontWeight: 800,
          color: '#001f35',
          fontFamily: 'Manrope, sans-serif',
          lineHeight: 1,
          marginBottom: '6px',
        }}
      >
        {formatPrice(product.sales_price)}
      </p>

      {/* Positioning */}
      <span
        style={{
          display: 'inline-block',
          background: `${getPositioningColor(pos)}12`,
          color: getPositioningColor(pos),
          borderRadius: '9999px',
          padding: '3px 10px',
          fontSize: '11px',
          fontWeight: 600,
          fontFamily: 'Inter, sans-serif',
          marginBottom: '16px',
        }}
      >
        {pos}
      </span>

      {/* Stats */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '10px',
          borderTop: '1px solid rgba(0,31,53,0.07)',
          paddingTop: '14px',
        }}
      >
        <div>
          <p style={{ fontSize: '11px', color: '#60708a', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', fontFamily: 'Inter, sans-serif', marginBottom: '2px' }}>
            Deals Won
          </p>
          <p style={{ fontSize: '20px', fontWeight: 800, color: '#16a34a', fontFamily: 'Manrope, sans-serif' }}>
            {wonCount}
          </p>
        </div>
        <div>
          <p style={{ fontSize: '11px', color: '#60708a', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', fontFamily: 'Inter, sans-serif', marginBottom: '2px' }}>
            Win Rate
          </p>
          <p style={{ fontSize: '20px', fontWeight: 800, color: '#b9915b', fontFamily: 'Manrope, sans-serif' }}>
            {winRate}%
          </p>
        </div>
        <div style={{ gridColumn: '1 / -1' }}>
          <p style={{ fontSize: '11px', color: '#60708a', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', fontFamily: 'Inter, sans-serif', marginBottom: '2px' }}>
            Receita Gerada
          </p>
          <p style={{ fontSize: '16px', fontWeight: 700, color: '#0f1a45', fontFamily: 'Manrope, sans-serif' }}>
            {formatRevenue(revenue)}
          </p>
        </div>
      </div>
    </div>
  )
}

// ─── Custom Tooltip ───────────────────────────────────────────────────────────

function CustomBarTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: { product: string; price: number } }> }) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div style={{ background: '#0f1a45', color: '#fff', borderRadius: '10px', padding: '10px 14px', fontSize: '13px', fontFamily: 'Manrope, sans-serif' }}>
      <p style={{ fontWeight: 700 }}>{d.product}</p>
      <p style={{ color: '#b9915b' }}>{formatPrice(d.price)}</p>
    </div>
  )
}

function CustomPieTooltip({ active, payload }: { active?: boolean; payload?: Array<{ name: string; value: number }> }) {
  if (!active || !payload?.length) return null
  const d = payload[0]
  return (
    <div style={{ background: '#0f1a45', color: '#fff', borderRadius: '10px', padding: '10px 14px', fontSize: '13px', fontFamily: 'Manrope, sans-serif' }}>
      <p style={{ fontWeight: 700 }}>{d.name}</p>
      <p style={{ color: '#b9915b' }}>{formatRevenue(d.value)}</p>
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function ProductsPage() {
  const { role, agent } = useAuth()

  const dealsInScope = useMemo(() => {
    if (role === 'admin') return DEALS
    if (role === 'seller' && agent) return DEALS.filter(d => d.sales_agent === agent)
    return []
  }, [role, agent])

  const dealsWon = useMemo(() => dealsInScope.filter(d => d.deal_stage === 'Won'), [dealsInScope])
  const dealsLost = useMemo(() => dealsInScope.filter(d => d.deal_stage === 'Lost'), [dealsInScope])

  const productStats = useMemo(() => {
    return UNIQUE_PRODUCTS.map(product => {
      // normalize product names (GTX Pro / GTXPro)
      const productNames = [product.product]
      if (product.product === 'GTX Pro') productNames.push('GTXPro')
      if (product.product === 'GTXPro') productNames.push('GTX Pro')

      const wonDeals = dealsWon.filter(d => productNames.includes(d.product))
      const lostDeals = dealsLost.filter(d => productNames.includes(d.product))
      const totalDeals = wonDeals.length + lostDeals.length
      const revenue = wonDeals.reduce((s, d) => s + d.close_value, 0)

      return {
        product,
        wonCount: wonDeals.length,
        totalCount: totalDeals,
        revenue,
      }
    })
  }, [dealsWon, dealsLost])

  // Bar chart data: sorted by price ascending
  const barData = useMemo(() =>
    [...UNIQUE_PRODUCTS]
      .sort((a, b) => a.sales_price - b.sales_price)
      .map(p => ({ product: p.product, price: p.sales_price, series: p.series })),
    []
  )

  // Pie data: revenue by series
  const pieData = useMemo(() => {
    const bySeriesMap = new Map<string, number>()
    for (const stat of productStats) {
      const s = stat.product.series
      bySeriesMap.set(s, (bySeriesMap.get(s) ?? 0) + stat.revenue)
    }
    return Array.from(bySeriesMap.entries()).map(([name, value]) => ({ name, value }))
  }, [productStats])

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f8f9fa' }}>
      <DashboardNavbar />

      <main
        style={{
          paddingTop: '94px',
          paddingLeft: '24px',
          paddingRight: '24px',
          paddingBottom: '48px',
          maxWidth: '1400px',
          margin: '0 auto',
        }}
      >
        {/* Page header */}
        <div style={{ marginBottom: '28px' }}>
          <h1
            style={{
              fontSize: '28px',
              fontWeight: 800,
              color: '#001f35',
              fontFamily: 'Manrope, sans-serif',
              marginBottom: '4px',
            }}
          >
            Catálogo de Produtos
          </h1>
          <p style={{ fontSize: '14px', color: '#60708a', fontFamily: 'Inter, sans-serif' }}>
            G4 Business Product Line — {UNIQUE_PRODUCTS.length} produtos
          </p>
        </div>

        {/* Product grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
            gap: '20px',
            marginBottom: '48px',
          }}
        >
          {productStats.map(({ product, wonCount, totalCount, revenue }) => (
            <ProductCard
              key={product.product}
              product={product}
              wonCount={wonCount}
              totalCount={totalCount}
              revenue={revenue}
            />
          ))}
        </div>

        {/* Charts section */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '24px',
          }}
        >
          {/* Value Staircase */}
          <div
            style={{
              background: '#ffffff',
              border: '1px solid rgba(0,31,53,0.1)',
              borderRadius: '16px',
              padding: '28px',
              boxShadow: '0 0 22px rgba(0,0,0,0.07)',
            }}
          >
            <h2
              style={{
                fontSize: '16px',
                fontWeight: 700,
                color: '#001f35',
                fontFamily: 'Manrope, sans-serif',
                marginBottom: '4px',
              }}
            >
              Escada de Valor
            </h2>
            <p style={{ fontSize: '12px', color: '#60708a', fontFamily: 'Inter, sans-serif', marginBottom: '24px' }}>
              Posicionamento por preço — do menor ao maior
            </p>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={barData} layout="vertical" margin={{ top: 0, right: 16, left: 8, bottom: 0 }}>
                <XAxis
                  type="number"
                  tickFormatter={v => `$${(v / 1000).toFixed(0)}K`}
                  tick={{ fontSize: 11, fill: '#60708a', fontFamily: 'Inter, sans-serif' }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  type="category"
                  dataKey="product"
                  width={90}
                  tick={{ fontSize: 11, fill: '#001f35', fontFamily: 'Manrope, sans-serif' }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip content={<CustomBarTooltip />} cursor={{ fill: 'rgba(0,31,53,0.04)' }} />
                <Bar dataKey="price" radius={[0, 6, 6, 0]}>
                  {barData.map(entry => (
                    <Cell
                      key={entry.product}
                      fill={SERIES_COLORS[entry.series] ?? '#60708a'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Product Mix */}
          <div
            style={{
              background: '#ffffff',
              border: '1px solid rgba(0,31,53,0.1)',
              borderRadius: '16px',
              padding: '28px',
              boxShadow: '0 0 22px rgba(0,0,0,0.07)',
            }}
          >
            <h2
              style={{
                fontSize: '16px',
                fontWeight: 700,
                color: '#001f35',
                fontFamily: 'Manrope, sans-serif',
                marginBottom: '4px',
              }}
            >
              Mix de Receita por Série
            </h2>
            <p style={{ fontSize: '12px', color: '#60708a', fontFamily: 'Inter, sans-serif', marginBottom: '16px' }}>
              Participação no revenue total de deals ganhos
            </p>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="45%"
                  innerRadius={72}
                  outerRadius={110}
                  paddingAngle={3}
                  dataKey="value"
                  nameKey="name"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(1)}%`}
                  labelLine={{ stroke: '#e5e7eb' }}
                >
                  {pieData.map(entry => (
                    <Cell key={entry.name} fill={SERIES_COLORS[entry.name] ?? '#60708a'} />
                  ))}
                </Pie>
                <Tooltip content={<CustomPieTooltip />} />
                <Legend
                  formatter={(value: string) => (
                    <span style={{ fontSize: '12px', color: '#001f35', fontFamily: 'Manrope, sans-serif' }}>{value}</span>
                  )}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </main>
    </div>
  )
}
