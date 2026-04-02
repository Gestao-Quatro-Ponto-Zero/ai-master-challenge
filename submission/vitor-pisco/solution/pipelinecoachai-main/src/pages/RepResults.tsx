import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePipelineStore } from '@/store/pipeline-store';
import { safeFloat, displayAccount, formatCurrency, normalizeProduct } from '@/lib/csv-utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Home, TrendingUp, Target, DollarSign, Clock } from 'lucide-react';
import {
  ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
  BarChart, AreaChart, Area, PieChart, Pie, Cell, ReferenceLine
} from 'recharts';

const MONTH_LABELS: Record<string, string> = {
  '2017-03': 'Mar', '2017-04': 'Abr', '2017-05': 'Mai', '2017-06': 'Jun',
  '2017-07': 'Jul', '2017-08': 'Ago', '2017-09': 'Set', '2017-10': 'Out',
  '2017-11': 'Nov', '2017-12': 'Dez',
};
const MONTHS = Object.keys(MONTH_LABELS);

const PRODUCT_COLORS: Record<string, string> = {
  'GTXPro': '#3b82f6',
  'GTX Plus Pro': '#6366f1',
  'MG Advanced': '#00e5a0',
  'GTX Plus Basic': '#8b5cf6',
  'GTX Basic': '#a78bfa',
  'GTK 500': '#f59e0b',
  'MG Special': '#34d399',
};

const CYCLE_COLORS = ['#00e5a0', '#3b82f6', '#f59e0b', '#ef4444'];

function daysBetweenDates(a: string, b: string): number {
  if (!a || !b) return 0;
  const da = new Date(a);
  const db = new Date(b);
  if (isNaN(da.getTime()) || isNaN(db.getTime())) return 0;
  return Math.round((db.getTime() - da.getTime()) / (1000 * 60 * 60 * 24));
}

const RepResults = () => {
  const navigate = useNavigate();
  const { pipeline, teams, products: storeProducts, accounts: storeAccounts, selectedAgent, setSelectedAgent } = usePipelineStore();

  const [monthFilter, setMonthFilter] = useState<string>('all');
  const [productFilter, setProductFilter] = useState<string>('all');
  const [accountSortCol, setAccountSortCol] = useState<string>('revenue');
  const [accountSortDir, setAccountSortDir] = useState<'asc' | 'desc'>('desc');

  const agents = useMemo(() => {
    const set = new Set(pipeline.map(d => d.sales_agent));
    return Array.from(set).sort();
  }, [pipeline]);

  const currentAgent = selectedAgent || agents[0] || '';

  // Normalize product map for joining
  const productNameMap = useMemo(() => {
    const map: Record<string, string> = {};
    storeProducts.forEach(p => {
      map[normalizeProduct(p.product)] = p.product;
    });
    return map;
  }, [storeProducts]);

  // All unique product names from pipeline for this rep
  const allProductNames = useMemo(() => {
    const set = new Set<string>();
    storeProducts.forEach(p => set.add(p.product));
    return Array.from(set).sort();
  }, [storeProducts]);

  // Account sector map
  const accountSectorMap = useMemo(() => {
    const map: Record<string, string> = {};
    storeAccounts.forEach(a => { map[a.account] = a.sector || '—'; });
    return map;
  }, [storeAccounts]);

  // Core computed data — memoized by agent
  const repData = useMemo(() => {
    if (!currentAgent) return null;

    const repDeals = pipeline.filter(d => d.sales_agent === currentAgent);
    const wonDeals = repDeals.filter(d => d.deal_stage === 'Won');
    const lostDeals = repDeals.filter(d => d.deal_stage === 'Lost');

    // Normalize product names in deals
    const normalizedWon = wonDeals.map(d => ({
      ...d,
      product: productNameMap[normalizeProduct(d.product)] || d.product,
    }));
    const normalizedLost = lostDeals.map(d => ({
      ...d,
      product: productNameMap[normalizeProduct(d.product)] || d.product,
    }));

    return { repDeals, wonDeals: normalizedWon, lostDeals: normalizedLost };
  }, [pipeline, currentAgent, productNameMap]);

  // Filtered deals by month and product
  const filteredData = useMemo(() => {
    if (!repData) return { won: [], lost: [] };
    let won = repData.wonDeals;
    let lost = repData.lostDeals;

    if (monthFilter !== 'all') {
      won = won.filter(d => d.close_date && d.close_date.startsWith(monthFilter));
      lost = lost.filter(d => d.close_date && d.close_date.startsWith(monthFilter));
    }
    if (productFilter !== 'all') {
      won = won.filter(d => d.product === productFilter);
      lost = lost.filter(d => d.product === productFilter);
    }
    return { won, lost };
  }, [repData, monthFilter, productFilter]);

  // KPIs
  const kpis = useMemo(() => {
    const { won, lost } = filteredData;
    const totalRevenue = won.reduce((s, d) => s + safeFloat(d.close_value), 0);
    const wonCount = won.length;
    const lostCount = lost.length;
    const winRate = (wonCount + lostCount) > 0 ? (wonCount / (wonCount + lostCount)) * 100 : 0;
    const avgTicket = wonCount > 0 ? totalRevenue / wonCount : 0;

    const wonWithDates = won.filter(d => d.engage_date && d.close_date);
    const cycles = wonWithDates.map(d => daysBetweenDates(d.engage_date, d.close_date));
    const avgCycle = cycles.length > 0 ? Math.round(cycles.reduce((a, b) => a + b, 0) / cycles.length) : 0;

    return { totalRevenue, wonCount, lostCount, winRate, avgTicket, avgCycle };
  }, [filteredData]);

  // Monthly data (always unfiltered by month for charts)
  const monthlyData = useMemo(() => {
    if (!repData) return [];
    let won = repData.wonDeals;
    let lost = repData.lostDeals;
    if (productFilter !== 'all') {
      won = won.filter(d => d.product === productFilter);
      lost = lost.filter(d => d.product === productFilter);
    }

    return MONTHS.map(mk => {
      const mWon = won.filter(d => d.close_date && d.close_date.startsWith(mk));
      const mLost = lost.filter(d => d.close_date && d.close_date.startsWith(mk));
      const revenue = mWon.reduce((s, d) => s + safeFloat(d.close_value), 0);
      const wr = (mWon.length + mLost.length) > 0 ? (mWon.length / (mWon.length + mLost.length)) * 100 : 0;
      return { month: MONTH_LABELS[mk], monthKey: mk, revenue, deals: mWon.length, lost: mLost.length, winRate: Math.round(wr) };
    });
  }, [repData, productFilter]);

  // Product timeline data
  const productTimelineData = useMemo(() => {
    if (!repData) return [];
    const won = monthFilter !== 'all'
      ? repData.wonDeals.filter(d => d.close_date && d.close_date.startsWith(monthFilter))
      : repData.wonDeals;

    return MONTHS.map(mk => {
      const row: Record<string, number | string> = { month: MONTH_LABELS[mk] };
      allProductNames.forEach(p => {
        row[p] = won
          .filter(d => d.close_date && d.close_date.startsWith(mk) && d.product === p)
          .reduce((s, d) => s + safeFloat(d.close_value), 0);
      });
      return row;
    });
  }, [repData, allProductNames, monthFilter]);

  // Cycle distribution
  const cycleData = useMemo(() => {
    const { won } = filteredData;
    const wonWithDates = won.filter(d => d.engage_date && d.close_date);
    const buckets = [
      { name: '< 30 dias', label: 'Fechamento rápido', count: 0 },
      { name: '30–60 dias', label: 'Ciclo normal', count: 0 },
      { name: '60–90 dias', label: 'Ciclo longo', count: 0 },
      { name: '> 90 dias', label: 'Ciclo crítico', count: 0 },
    ];
    wonWithDates.forEach(d => {
      const days = daysBetweenDates(d.engage_date, d.close_date);
      if (days < 30) buckets[0].count++;
      else if (days < 60) buckets[1].count++;
      else if (days < 90) buckets[2].count++;
      else buckets[3].count++;
    });
    const total = wonWithDates.length || 1;
    return buckets.map((b, i) => ({
      ...b,
      pct: Math.round((b.count / total) * 100),
      fill: CYCLE_COLORS[i],
    }));
  }, [filteredData]);

  // Cumulative revenue
  const cumulativeData = useMemo(() => {
    let cum = 0;
    return monthlyData.map(m => {
      cum += m.revenue;
      return { month: m.month, monthRevenue: m.revenue, cumulative: cum };
    });
  }, [monthlyData]);

  // Top accounts
  const topAccounts = useMemo(() => {
    const { won } = filteredData;
    const map: Record<string, { deals: number; revenue: number; lastClose: string }> = {};
    won.forEach(d => {
      const acc = d.account || '';
      if (!map[acc]) map[acc] = { deals: 0, revenue: 0, lastClose: '' };
      map[acc].deals++;
      map[acc].revenue += safeFloat(d.close_value);
      if (d.close_date > map[acc].lastClose) map[acc].lastClose = d.close_date;
    });
    return Object.entries(map).map(([account, data]) => ({
      account: displayAccount(account),
      sector: accountSectorMap[account] || '—',
      deals: data.deals,
      revenue: data.revenue,
      avgTicket: data.deals > 0 ? data.revenue / data.deals : 0,
      lastClose: data.lastClose,
    }));
  }, [filteredData, accountSectorMap]);

  const sortedAccounts = useMemo(() => {
    return [...topAccounts].sort((a, b) => {
      let cmp = 0;
      switch (accountSortCol) {
        case 'account': cmp = a.account.localeCompare(b.account); break;
        case 'sector': cmp = a.sector.localeCompare(b.sector); break;
        case 'deals': cmp = a.deals - b.deals; break;
        case 'revenue': cmp = a.revenue - b.revenue; break;
        case 'avgTicket': cmp = a.avgTicket - b.avgTicket; break;
        case 'lastClose': cmp = a.lastClose.localeCompare(b.lastClose); break;
      }
      return accountSortDir === 'desc' ? -cmp : cmp;
    });
  }, [topAccounts, accountSortCol, accountSortDir]);

  // Product mix donut
  const productMix = useMemo(() => {
    const { won } = filteredData;
    const map: Record<string, { revenue: number; deals: number }> = {};
    won.forEach(d => {
      if (!map[d.product]) map[d.product] = { revenue: 0, deals: 0 };
      map[d.product].revenue += safeFloat(d.close_value);
      map[d.product].deals++;
    });
    const totalRev = Object.values(map).reduce((s, v) => s + v.revenue, 0) || 1;
    return Object.entries(map)
      .map(([name, v]) => ({ name, ...v, pct: Math.round((v.revenue / totalRev) * 100) }))
      .filter(p => p.revenue > 0)
      .sort((a, b) => b.revenue - a.revenue);
  }, [filteredData]);

  // Insights
  const insights = useMemo(() => {
    const best = monthlyData.reduce((a, b) => a.revenue > b.revenue ? a : b, monthlyData[0]);
    const worst = monthlyData.reduce((a, b) => a.revenue < b.revenue && b.revenue > 0 ? a : b, monthlyData[0]);
    const delta = worst && worst.revenue > 0 ? Math.round(((best.revenue - worst.revenue) / worst.revenue) * 100) : 0;

    const topProduct = productMix[0];
    const topProductShare = topProduct ? topProduct.pct : 0;

    const fastRate = cycleData[0]?.pct || 0;
    const gt90Count = cycleData[3]?.count || 0;

    return { best, worst, delta, topProduct, topProductShare, fastRate, gt90Count };
  }, [monthlyData, productMix, cycleData]);

  const formatRevenue = (v: number) => {
    if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(2)}M`;
    if (v >= 1000) return `$${(v / 1000).toFixed(0)}K`;
    return `$${v.toFixed(0)}`;
  };

  const formatMonth = (dateStr: string) => {
    if (!dateStr) return '—';
    const [y, m] = dateStr.split('-');
    const labels = ['', 'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
    return `${labels[parseInt(m)] || m}/${y?.slice(2)}`;
  };

  const toggleAccountSort = (col: string) => {
    if (accountSortCol === col) setAccountSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setAccountSortCol(col); setAccountSortDir('desc'); }
  };

  const bestMonthIdx = monthlyData.findIndex(m => m === insights.best);

  if (pipeline.length === 0) {
    return (
      <div className="flex min-h-screen items-center justify-center flex-col gap-4">
        <p className="text-muted-foreground">Nenhum dado carregado.</p>
        <Button onClick={() => navigate('/upload')}>Carregar CSVs</Button>
      </div>
    );
  }

  const hasData = filteredData.won.length > 0 || filteredData.lost.length > 0;

  return (
    <div className="min-h-screen pb-20">
      {/* Header */}
      <div className="sticky top-0 z-30 bg-background/95 backdrop-blur border-b border-border px-4 py-3">
        <div className="max-w-5xl mx-auto flex items-center justify-between gap-3">
          <Button variant="ghost" size="icon" onClick={() => navigate('/')}>
            <Home className="h-5 w-5" />
          </Button>
          <h1 className="font-display text-lg font-700 text-primary flex-shrink-0">Pipeline Coach</h1>
          <Select value={currentAgent} onValueChange={setSelectedAgent}>
            <SelectTrigger className="w-48 text-xs h-8">
              <SelectValue placeholder="Vendedor" />
            </SelectTrigger>
            <SelectContent>
              {agents.map(a => (
                <SelectItem key={a} value={a} className="text-xs">{a}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        {/* Tab bar */}
        <div className="max-w-5xl mx-auto flex gap-4 mt-2">
          <button
            onClick={() => navigate('/rep')}
            className="text-sm pb-2 text-muted-foreground hover:text-foreground transition-colors"
          >
            🔥 Atividades
          </button>
          <button
            className="text-sm pb-2 text-primary border-b-2 border-primary font-medium"
          >
            📊 Resultados
          </button>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 py-6 space-y-6">
        {/* Filters */}
        <div className="flex flex-wrap gap-2 items-center">
          <div className="flex gap-1 flex-wrap">
            <Button size="sm" variant={monthFilter === 'all' ? 'default' : 'outline'} className="text-xs h-7" onClick={() => setMonthFilter('all')}>Todos</Button>
            {MONTHS.map(mk => (
              <Button key={mk} size="sm" variant={monthFilter === mk ? 'default' : 'outline'} className="text-xs h-7" onClick={() => setMonthFilter(mk)}>
                {MONTH_LABELS[mk]}
              </Button>
            ))}
          </div>
          <Select value={productFilter} onValueChange={setProductFilter}>
            <SelectTrigger className="w-48 text-xs h-7">
              <SelectValue placeholder="Todos os produtos" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all" className="text-xs">Todos os produtos</SelectItem>
              {allProductNames.map(p => (
                <SelectItem key={p} value={p} className="text-xs">{p}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {!hasData ? (
          <div className="text-center py-20 text-muted-foreground">
            <p className="font-display text-lg">
              {monthFilter !== 'all' ? `Sem fechamentos em ${MONTH_LABELS[monthFilter]}. Selecione outro período.` : 'Nenhum deal registrado para este vendedor no período analisado.'}
            </p>
          </div>
        ) : (
          <>
            {/* KPIs */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardContent className="pt-4 pb-3 text-center">
                  <DollarSign className="h-4 w-4 mx-auto mb-1 text-won" />
                  <p className="font-display text-2xl font-800 text-won">{formatRevenue(kpis.totalRevenue)}</p>
                  <p className="text-xs text-muted-foreground mt-1">{kpis.wonCount} deals fechados</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4 pb-3 text-center">
                  <Target className="h-4 w-4 mx-auto mb-1" style={{ color: kpis.winRate >= 65 ? '#00e5a0' : kpis.winRate >= 60 ? '#3b82f6' : '#f59e0b' }} />
                  <p className="font-display text-2xl font-800" style={{ color: kpis.winRate >= 65 ? '#00e5a0' : kpis.winRate >= 60 ? '#3b82f6' : '#f59e0b' }}>
                    {kpis.winRate.toFixed(1)}%
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">{kpis.wonCount}W / {kpis.lostCount}L</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4 pb-3 text-center">
                  <TrendingUp className="h-4 w-4 mx-auto mb-1 text-muted-foreground" />
                  <p className="font-display text-2xl font-800">${kpis.avgTicket.toLocaleString('en', { maximumFractionDigits: 0 })}</p>
                  <p className="text-xs text-muted-foreground mt-1">por deal fechado</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4 pb-3 text-center">
                  <Clock className="h-4 w-4 mx-auto mb-1" style={{ color: kpis.avgCycle < 51.8 ? '#00e5a0' : '#f59e0b' }} />
                  <p className="font-display text-2xl font-800" style={{ color: kpis.avgCycle < 51.8 ? '#00e5a0' : '#f59e0b' }}>
                    {kpis.avgCycle}d
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">Empresa: 51,8d</p>
                </CardContent>
              </Card>
            </div>

            {/* Chart 1 — Monthly Revenue */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="font-display text-base">Receita Mensal</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={monthlyData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(220 14% 16%)" />
                      <XAxis dataKey="month" tick={{ fill: 'hsl(215 16% 47%)', fontSize: 11 }} />
                      <YAxis yAxisId="left" tickFormatter={v => `$${(v / 1000).toFixed(0)}K`} tick={{ fill: 'hsl(215 16% 47%)', fontSize: 11 }} />
                      <YAxis yAxisId="right" orientation="right" domain={[0, 100]} tickFormatter={v => `${v}%`} tick={{ fill: 'hsl(215 16% 47%)', fontSize: 11 }} />
                      <Tooltip
                        contentStyle={{ background: '#ffffff', border: '1px solid #e2e8f0', color: '#1e293b', borderRadius: 8, fontSize: 12 }}
                        formatter={(value: number, name: string) => {
                          if (name === 'revenue') return [formatRevenue(value), 'Receita'];
                          if (name === 'winRate') return [`${value}%`, 'Win Rate'];
                          return [value, name];
                        }}
                        labelFormatter={l => `${l}/17`}
                      />
                      <Bar yAxisId="left" dataKey="revenue" radius={[4, 4, 0, 0]}>
                        {monthlyData.map((_, i) => (
                          <Cell key={i} fill={i === bestMonthIdx ? '#00e5a0' : '#3b82f6'} />
                        ))}
                      </Bar>
                      <Line yAxisId="right" type="monotone" dataKey="winRate" stroke="#f59e0b" strokeWidth={2} dot={{ fill: '#f59e0b', r: 3 }} />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
                {insights.best && insights.worst && (
                  <p className="text-xs text-muted-foreground mt-3">
                    📈 Melhor mês: {insights.best.month}/17 ({formatRevenue(insights.best.revenue)}). Pior mês: {insights.worst.month}/17 ({formatRevenue(insights.worst.revenue)}). Variação de {insights.delta}% entre o melhor e o pior mês.
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Row: Product Timeline + Cycle Distribution */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Chart 2 — Product Revenue Timeline */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="font-display text-base">Receita por Produto</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={productTimelineData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(220 14% 16%)" />
                        <XAxis dataKey="month" tick={{ fill: 'hsl(215 16% 47%)', fontSize: 11 }} />
                        <YAxis tickFormatter={v => `$${(v / 1000).toFixed(0)}K`} tick={{ fill: 'hsl(215 16% 47%)', fontSize: 11 }} />
                        <Tooltip
                          contentStyle={{ background: '#ffffff', border: '1px solid #e2e8f0', color: '#1e293b', borderRadius: 8, fontSize: 12 }}
                          formatter={(value: number, name: string) => [formatRevenue(value), name]}
                        />
                        <Legend wrapperStyle={{ fontSize: 11 }} />
                        {allProductNames.map(p => (
                          <Bar key={p} dataKey={p} stackId="products" fill={PRODUCT_COLORS[p] || '#666'} />
                        ))}
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  {insights.topProduct && (
                    <p className="text-xs text-muted-foreground mt-3">
                      💡 {insights.topProduct.name} representa {insights.topProductShare}% da receita total.
                      {insights.topProductShare > 50 && ' Diversificar pode reduzir concentração de risco.'}
                    </p>
                  )}
                </CardContent>
              </Card>

              {/* Chart 3 — Cycle Distribution */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="font-display text-base">Ciclo de Fechamento</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={cycleData} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(220 14% 16%)" />
                        <XAxis type="number" tick={{ fill: 'hsl(215 16% 47%)', fontSize: 11 }} />
                        <YAxis type="category" dataKey="name" width={90} tick={{ fill: 'hsl(215 16% 47%)', fontSize: 11 }} />
                        <Tooltip
                          contentStyle={{ background: '#ffffff', border: '1px solid #e2e8f0', color: '#1e293b', borderRadius: 8, fontSize: 12 }}
                          formatter={(value: number, _: string, props: any) => [`${value} deals (${props.payload.pct}%)`, props.payload.label]}
                        />
                        <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                          {cycleData.map((entry, i) => (
                            <Cell key={i} fill={entry.fill} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  <p className="text-xs text-muted-foreground mt-3">
                    ⚡ {insights.fastRate}% dos deals fecham em menos de 30 dias. {insights.gt90Count > 0 && `${insights.gt90Count} deals levaram mais de 90 dias — revisar abordagem nesses casos.`}
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Chart 4 — Cumulative Revenue */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="font-display text-base">Receita Acumulada</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={cumulativeData}>
                      <defs>
                        <linearGradient id="cumGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#00e5a0" stopOpacity={0.3} />
                          <stop offset="100%" stopColor="#00e5a0" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(220 14% 16%)" />
                      <XAxis dataKey="month" tick={{ fill: 'hsl(215 16% 47%)', fontSize: 11 }} />
                      <YAxis tickFormatter={v => formatRevenue(v)} tick={{ fill: 'hsl(215 16% 47%)', fontSize: 11 }} />
                      <Tooltip
                        contentStyle={{ background: '#ffffff', border: '1px solid #e2e8f0', color: '#1e293b', borderRadius: 8, fontSize: 12 }}
                        formatter={(value: number, name: string) => [formatRevenue(value), name === 'cumulative' ? 'Acumulado' : 'Mensal']}
                      />
                      {cumulativeData.length > 0 && (
                        <ReferenceLine y={cumulativeData[cumulativeData.length - 1]?.cumulative} stroke="#00e5a0" strokeDasharray="5 5" label={{ value: `Total: ${formatRevenue(cumulativeData[cumulativeData.length - 1]?.cumulative || 0)}`, fill: '#00e5a0', fontSize: 11, position: 'right' }} />
                      )}
                      <Area type="monotone" dataKey="cumulative" stroke="#00e5a0" strokeWidth={2} fill="url(#cumGrad)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Row: Top Accounts + Product Mix */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Table — Top Accounts */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="font-display text-base">Top Contas Fechadas</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          {[
                            { key: 'account', label: 'Conta' },
                            { key: 'sector', label: 'Setor' },
                            { key: 'deals', label: 'Deals' },
                            { key: 'revenue', label: 'Receita' },
                            { key: 'avgTicket', label: 'Ticket' },
                            { key: 'lastClose', label: 'Último' },
                          ].map(col => (
                            <TableHead key={col.key} className="cursor-pointer hover:text-foreground text-xs" onClick={() => toggleAccountSort(col.key)}>
                              {col.label} {accountSortCol === col.key ? (accountSortDir === 'desc' ? '↓' : '↑') : ''}
                            </TableHead>
                          ))}
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {sortedAccounts.slice(0, 10).map((acc, i) => (
                          <TableRow key={i}>
                            <TableCell className="text-xs font-mono">{acc.account}</TableCell>
                            <TableCell className="text-xs">{acc.sector}</TableCell>
                            <TableCell className="text-xs font-mono">{acc.deals}</TableCell>
                            <TableCell className="text-xs font-mono">{formatRevenue(acc.revenue)}</TableCell>
                            <TableCell className="text-xs font-mono">${acc.avgTicket.toLocaleString('en', { maximumFractionDigits: 0 })}</TableCell>
                            <TableCell className="text-xs font-mono">{formatMonth(acc.lastClose)}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                  {topAccounts.length > 10 && (
                    <Dialog>
                      <DialogTrigger asChild>
                        <button className="text-xs text-primary mt-2 hover:underline">Ver todas ({topAccounts.length}) →</button>
                      </DialogTrigger>
                      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                        <DialogHeader>
                          <DialogTitle className="font-display">Todas as Contas</DialogTitle>
                        </DialogHeader>
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead className="text-xs">Conta</TableHead>
                              <TableHead className="text-xs">Setor</TableHead>
                              <TableHead className="text-xs">Deals</TableHead>
                              <TableHead className="text-xs">Receita</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {sortedAccounts.map((acc, i) => (
                              <TableRow key={i}>
                                <TableCell className="text-xs font-mono">{acc.account}</TableCell>
                                <TableCell className="text-xs">{acc.sector}</TableCell>
                                <TableCell className="text-xs font-mono">{acc.deals}</TableCell>
                                <TableCell className="text-xs font-mono">{formatRevenue(acc.revenue)}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </DialogContent>
                    </Dialog>
                  )}
                </CardContent>
              </Card>

              {/* Donut — Product Mix */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="font-display text-base">Mix de Produtos</CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col items-center">
                  <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={productMix}
                          dataKey="revenue"
                          nameKey="name"
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={100}
                          paddingAngle={2}
                          label={({ name, pct }) => `${name} ${pct}%`}
                          labelLine={false}
                        >
                          {productMix.map((entry) => (
                            <Cell key={entry.name} fill={PRODUCT_COLORS[entry.name] || '#666'} />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{ background: '#ffffff', border: '1px solid #e2e8f0', color: '#1e293b', borderRadius: 8, fontSize: 12 }}
                          formatter={(value: number, name: string, props: any) => [
                            `${formatRevenue(value)} · ${props.payload.deals} deals · ${props.payload.pct}%`,
                            name,
                          ]}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <p className="font-display text-lg font-700 text-primary -mt-4">{formatRevenue(kpis.totalRevenue)}</p>
                  <div className="flex flex-wrap gap-2 mt-3 justify-center">
                    {productMix.map(p => (
                      <Badge key={p.name} variant="outline" className="text-xs gap-1">
                        <span className="w-2 h-2 rounded-full inline-block" style={{ background: PRODUCT_COLORS[p.name] || '#666' }} />
                        {p.name} · {p.pct}%
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default RepResults;
