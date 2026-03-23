import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

export type ProspectingHealthDatum = {
  id: string
  label: string
  tooltipTitle: string
  pct: number
  count: number
  total: number
}

type Props = {
  data: ProspectingHealthDatum[]
  /** Cor única das barras horizontais (padrão: vermelho escuro) */
  barColor?: string
}

const DEFAULT_BAR = '#881337'

function formatInt(n: number) {
  return n.toLocaleString('pt-BR', { maximumFractionDigits: 0 })
}

function formatPctOne(n: number) {
  return `${n.toLocaleString('pt-BR', { maximumFractionDigits: 1, minimumFractionDigits: 0 })}%`
}

function BarValueLabel(props: {
  x?: number
  y?: number
  width?: number
  height?: number
  value?: number
  payload?: ProspectingHealthDatum
}) {
  const { x = 0, y = 0, width = 0, height = 0, payload } = props
  if (!payload || payload.total <= 0) return null
  const text = `${formatPctOne(payload.pct)} · ${formatInt(payload.count)}/${formatInt(payload.total)}`
  const tx = x + width + 6
  const ty = y + height / 2
  return (
    <text
      x={tx}
      y={ty}
      dy="0.35em"
      fill="#525252"
      fontSize={11}
      fontWeight={600}
      className="tabular-nums"
    >
      {text}
    </text>
  )
}

export default function ProspectingHealthHorizontalChart({
  data,
  barColor = DEFAULT_BAR,
}: Props) {
  if (data.length === 0) {
    return (
      <div className="flex h-full min-h-[200px] items-center justify-center text-sm text-neutral-400">
        Nenhum vendedor neste recorte
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart
        layout="vertical"
        data={data}
        margin={{ top: 4, right: 108, left: 4, bottom: 4 }}
        barCategoryGap="22%"
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" horizontal={false} />
        <XAxis
          type="number"
          domain={[0, 100]}
          tick={{ fontSize: 11, fill: '#525252' }}
          tickLine={{ stroke: '#d4d4d4' }}
          axisLine={{ stroke: '#d4d4d4' }}
          tickFormatter={(v) => `${v}%`}
        />
        <YAxis
          type="category"
          dataKey="label"
          width={148}
          tick={{ fontSize: 10, fill: '#404040' }}
          tickLine={false}
          axisLine={{ stroke: '#d4d4d4' }}
          interval={0}
        />
        <Tooltip
          cursor={{ fill: 'rgba(245, 245, 245, 0.6)' }}
          contentStyle={{
            borderRadius: '10px',
            border: '1px solid #e5e5e5',
            fontSize: '12px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
          }}
          formatter={(value, _name, item) => {
            const p = item?.payload as ProspectingHealthDatum | undefined
            if (!p) return [String(value ?? ''), '']
            return [
              `${formatInt(p.count)} de ${formatInt(p.total)} (${formatPctOne(p.pct)} do time)`,
              'Vendedores',
            ]
          }}
          labelFormatter={(_, payload) => {
            const p = payload?.[0]?.payload as ProspectingHealthDatum | undefined
            return p?.tooltipTitle ?? ''
          }}
        />
        <Bar
          dataKey="pct"
          name="% do time"
          fill={barColor}
          radius={[0, 4, 4, 0]}
          maxBarSize={22}
        >
          <LabelList dataKey="pct" content={<BarValueLabel />} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
