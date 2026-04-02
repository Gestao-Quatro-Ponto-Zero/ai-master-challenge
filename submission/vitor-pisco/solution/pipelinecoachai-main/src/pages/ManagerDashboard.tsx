import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePipelineStore } from '@/store/pipeline-store';
import { REFERENCE_DATE, safeFloat, daysBetween, displayAccount, formatCurrency, normalizeProduct } from '@/lib/csv-utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Home } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const ManagerDashboard = () => {
  const navigate = useNavigate();
  const { pipeline, teams, products, selectedManager, setSelectedManager } = usePipelineStore();

  const managers = useMemo(() => {
    return Array.from(new Set(teams.map(t => t.manager))).sort();
  }, [teams]);

  const currentManager = selectedManager || managers[0] || '';

  const managerReps = useMemo(() => {
    return teams.filter(t => t.manager === currentManager).map(t => t.sales_agent);
  }, [teams, currentManager]);

  const productPriceMap = useMemo(() => {
    const map: Record<string, number> = {};
    products.forEach(p => { map[p.product] = safeFloat(p.sales_price); });
    return map;
  }, [products]);

  const productNames = useMemo(() => {
    return Array.from(new Set(products.map(p => p.product))).sort();
  }, [products]);

  // M1 — Team Execution Ranking
  const teamRanking = useMemo(() => {
    return managerReps.map(rep => {
      const repDeals = pipeline.filter(d => d.sales_agent === rep);
      const won = repDeals.filter(d => d.deal_stage === 'Won').length;
      const lost = repDeals.filter(d => d.deal_stage === 'Lost').length;
      const openDeals = repDeals.filter(d => d.deal_stage === 'Prospecting' || d.deal_stage === 'Engaging');
      const staleDeals = openDeals.filter(d => daysBetween(d.engage_date, REFERENCE_DATE) > 60).length;
      const score = (won + lost) > 0 ? Math.round((won / (won + lost)) * 100) : 0;
      return { rep, score, openCount: openDeals.length, staleCount: staleDeals };
    }).sort((a, b) => b.score - a.score);
  }, [pipeline, managerReps]);

  // M2 — Aging by rep
  const agingData = useMemo(() => {
    const data = managerReps.map(rep => {
      const wonDeals = pipeline.filter(d =>
        d.sales_agent === rep && d.deal_stage === 'Won' && d.close_date && d.engage_date
      );
      const avg = wonDeals.length > 0
        ? Math.round(wonDeals.reduce((s, d) => s + daysBetween(d.engage_date, new Date(d.close_date)), 0) / wonDeals.length)
        : 0;
      return { rep, avg };
    }).filter(d => d.avg > 0).sort((a, b) => b.avg - a.avg);

    const teamAvg = data.length > 0 ? Math.round(data.reduce((s, d) => s + d.avg, 0) / data.length) : 0;
    return { data, teamAvg };
  }, [pipeline, managerReps]);

  // M3 — No contact ranking
  const noContactRanking = useMemo(() => {
    return managerReps.map(rep => {
      const openDeals = pipeline.filter(d =>
        d.sales_agent === rep && (d.deal_stage === 'Prospecting' || d.deal_stage === 'Engaging')
      );
      const days = openDeals.map(d => daysBetween(d.engage_date, REFERENCE_DATE));
      const avgDays = days.length > 0 ? Math.round(days.reduce((a, b) => a + b, 0) / days.length) : 0;
      return { rep, count: openDeals.length, avgDays };
    }).sort((a, b) => b.avgDays - a.avgDays);
  }, [pipeline, managerReps]);

  // M4 — Pipeline Coverage
  const coverageData = useMemo(() => {
    const data = managerReps.map(rep => {
      const openDeals = pipeline.filter(d =>
        d.sales_agent === rep && (d.deal_stage === 'Prospecting' || d.deal_stage === 'Engaging')
      );
      const totalValue = openDeals.reduce((s, d) => s + (productPriceMap[d.product] || 0), 0);
      return { rep, value: totalValue };
    });
    const avg = data.length > 0 ? data.reduce((s, d) => s + d.value, 0) / data.length : 0;
    return { data: data.sort((a, b) => b.value - a.value), avg };
  }, [pipeline, managerReps, productPriceMap]);

  // M5 — Product conversion matrix
  const conversionMatrix = useMemo(() => {
    return managerReps
      .filter(rep => rep && rep.trim() !== '')
      .map(rep => {
        const products: Record<string, number | null> = {};
        productNames.forEach(prod => {
          const deals = pipeline.filter(d =>
            d.sales_agent === rep && d.product === prod && (d.deal_stage === 'Won' || d.deal_stage === 'Lost')
          );
          if (deals.length === 0) { products[prod] = null; return; }
          const won = deals.filter(d => d.deal_stage === 'Won').length;
          products[prod] = Math.round((won / deals.length) * 100);
        });
        return { rep, products };
      });
  }, [pipeline, managerReps, productNames]);

  if (pipeline.length === 0) {
    return (
      <div className="flex min-h-screen items-center justify-center flex-col gap-4">
        <p className="text-muted-foreground">Nenhum dado carregado.</p>
        <Button onClick={() => navigate('/upload')}>Carregar CSVs</Button>
      </div>
    );
  }

  return (
    <div className="min-h-screen pb-20">
      {/* Header */}
      <div className="sticky top-0 z-30 bg-background/95 backdrop-blur border-b border-border px-4 py-3">
        <div className="max-w-6xl mx-auto flex items-center justify-between gap-3">
          <Button variant="ghost" size="icon" onClick={() => navigate('/')}>
            <Home className="h-5 w-5" />
          </Button>
          <h1 className="font-display text-lg font-700 text-primary">Pipeline Coach — Gestão</h1>
          <Select value={currentManager} onValueChange={setSelectedManager}>
            <SelectTrigger className="w-48 text-xs h-8">
              <SelectValue placeholder="Gestor" />
            </SelectTrigger>
            <SelectContent>
              {managers.map(m => (
                <SelectItem key={m} value={m} className="text-xs">{m}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-6 space-y-6">
        {/* M1 — Team Ranking */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="font-display text-lg">🏅 Ranking de Execução da Equipe</CardTitle>
            <p className="text-xs text-muted-foreground">Apoie o time a melhorar suas taxas de conversão</p>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-xs">Vendedor</TableHead>
                  <TableHead className="text-xs">Score (Win Rate)</TableHead>
                  <TableHead className="text-xs">Deals Abertos</TableHead>
                  <TableHead className="text-xs">Deals Parados</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {teamRanking.map(r => (
                  <TableRow key={r.rep} className="cursor-pointer hover:bg-muted/30" onClick={() => { usePipelineStore.getState().setSelectedAgent(r.rep); navigate('/rep'); }}>
                    <TableCell className="text-sm font-mono">{r.rep}</TableCell>
                    <TableCell>
                      <span className={`font-mono text-sm ${r.score < 40 ? 'text-lost' : r.score >= 60 ? 'text-won' : ''}`}>
                        {r.score}%
                      </span>
                    </TableCell>
                    <TableCell className="text-sm font-mono">{r.openCount}</TableCell>
                    <TableCell className="text-sm font-mono">{r.staleCount}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <div className="grid md:grid-cols-2 gap-6">
          {/* M2 — Aging */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="font-display text-lg">⏱️ Aging Médio por Vendedor</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={Math.max(200, agingData.data.length * 40)}>
                <BarChart data={agingData.data} layout="vertical" margin={{ left: 80 }}>
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="rep" tick={{ fontSize: 11 }} width={80} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', color: '#1e293b', borderRadius: 8, fontSize: 12 }}
                    formatter={(value: number) => [`${value}d`, 'Aging']}
                  />
                  <Bar dataKey="avg" radius={[0, 4, 4, 0]}>
                    {agingData.data.map((entry, i) => (
                      <Cell key={i} fill={entry.avg > agingData.teamAvg * 1.2 ? 'hsl(0 84% 60%)' : 'hsl(217 91% 60%)'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <p className="text-xs text-muted-foreground mt-2">Média do time: {agingData.teamAvg}d</p>
            </CardContent>
          </Card>

          {/* M4 — Pipeline Coverage */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="font-display text-lg">💰 Pipeline Coverage</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={Math.max(200, coverageData.data.length * 40)}>
                <BarChart data={coverageData.data} layout="vertical" margin={{ left: 80 }}>
                  <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={(v) => formatCurrency(v)} />
                  <YAxis type="category" dataKey="rep" tick={{ fontSize: 11 }} width={80} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', color: '#1e293b', borderRadius: 8, fontSize: 12 }}
                    formatter={(value: number) => [formatCurrency(value), 'Pipeline']}
                  />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                    {coverageData.data.map((entry, i) => (
                      <Cell
                        key={i}
                        fill={
                          entry.value > coverageData.avg * 1.1 ? 'hsl(160 100% 45%)' :
                          entry.value < coverageData.avg * 0.9 ? 'hsl(0 84% 60%)' : 'hsl(38 92% 50%)'
                        }
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <p className="text-xs text-muted-foreground mt-2">Média: {formatCurrency(coverageData.avg)}</p>
            </CardContent>
          </Card>
        </div>

        {/* M3 — No Contact Ranking */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="font-display text-lg">📵 Ranking Sem Contato</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-xs">Vendedor</TableHead>
                  <TableHead className="text-xs">Contas</TableHead>
                  <TableHead className="text-xs">Média de dias</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {noContactRanking.map(r => (
                  <TableRow key={r.rep}>
                    <TableCell className="text-sm font-mono">{r.rep}</TableCell>
                    <TableCell className="text-sm font-mono">{r.count}</TableCell>
                    <TableCell className="text-sm font-mono">{r.avgDays}d</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* M5 — Product Conversion Matrix */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="font-display text-lg">🎯 Conversão por Produto</CardTitle>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-xs">Vendedor</TableHead>
                  {productNames.map(p => (
                    <TableHead key={p} className="text-xs text-center">{p}</TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {conversionMatrix.map((row) => (
                  <TableRow key={row.rep}>
                    <TableCell className="text-sm font-mono">{row.rep}</TableCell>
                    {productNames.map(p => {
                      const val = row.products[p];
                      if (val === null || val === undefined) return <TableCell key={p} className="text-center text-xs text-muted-foreground">—</TableCell>;
                      const hue = Math.round((val / 100) * 120);
                      return (
                        <TableCell
                          key={p}
                          className="text-center text-xs font-mono font-500"
                          style={{ backgroundColor: `hsla(${hue}, 70%, 40%, 0.2)`, color: `hsl(${hue}, 70%, 60%)` }}
                        >
                          {val}%
                        </TableCell>
                      );
                    })}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ManagerDashboard;
