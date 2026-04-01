import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

export type WonLostBucketDatum = {
  faixa: string
  won: number
  lost: number
}

type Props = {
  data: WonLostBucketDatum[]
  /** Cor das barras “Ganho” (padrão: verde esmeralda) */
  wonColor?: string
  /** Cor das barras “Perdido” (padrão: rosa/vermelho) */
  lostColor?: string
}

function formatInt(n: number) {
  return n.toLocaleString('pt-BR', { maximumFractionDigits: 0 })
}

const DEFAULT_WON = '#059669'
const DEFAULT_LOST = '#e11d48'

export default function WonLostByTimeBucketChart({
  data,
  wonColor = DEFAULT_WON,
  lostColor = DEFAULT_LOST,
}: Props) {
  if (data.length === 0) {
    return (
      <div className="flex h-full min-h-[200px] items-center justify-center text-sm text-neutral-400">
        Nenhuma faixa com deals fechados neste recorte
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart
        data={data}
        barGap={2}
        barCategoryGap="18%"
        margin={{ top: 4, right: 8, left: 4, bottom: 0 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical />
        <XAxis
          dataKey="faixa"
          tick={{ fontSize: 11, fill: '#525252' }}
          tickLine={{ stroke: '#d4d4d4' }}
          axisLine={{ stroke: '#d4d4d4' }}
          interval={0}
          angle={data.length > 4 ? -18 : 0}
          textAnchor={data.length > 4 ? 'end' : 'middle'}
          height={data.length > 4 ? 48 : 28}
        />
        <YAxis
          tick={{ fontSize: 11, fill: '#525252' }}
          tickLine={{ stroke: '#d4d4d4' }}
          axisLine={{ stroke: '#d4d4d4' }}
          tickFormatter={(v) => formatInt(Number(v))}
          width={44}
        />
        <Tooltip
          cursor={{ fill: 'rgba(245, 245, 245, 0.6)' }}
          contentStyle={{
            borderRadius: '10px',
            border: '1px solid #e5e5e5',
            fontSize: '12px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
          }}
          formatter={(value, name) => [
            formatInt(Number(value ?? 0)),
            name === 'won' ? 'Ganho' : 'Perdido',
          ]}
          labelFormatter={(label) => `Faixa: ${label}`}
        />
        <Legend
          wrapperStyle={{ fontSize: '12px', paddingTop: 8 }}
          formatter={(value) => (value === 'won' ? 'Ganho' : 'Perdido')}
        />
        <Bar dataKey="won" name="won" fill={wonColor} radius={[4, 4, 0, 0]} maxBarSize={36} />
        <Bar dataKey="lost" name="lost" fill={lostColor} radius={[4, 4, 0, 0]} maxBarSize={36} />
      </BarChart>
    </ResponsiveContainer>
  )
}
