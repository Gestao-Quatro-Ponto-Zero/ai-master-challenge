import { useMemo, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePipelineStore } from '@/store/pipeline-store';
import { calcPriorityScore } from '@/lib/scoring';
import { REFERENCE_DATE, safeFloat, daysBetween, displayAccount, formatCurrency, percentile } from '@/lib/csv-utils';
import type { ScoredDeal, ActionRecord } from '@/types/csv';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from '@/hooks/use-toast';
import { Home, Phone, Mail, Handshake, RefreshCw, Check, Clock, Calendar, X, AlertTriangle, Info } from 'lucide-react';

const scoreBadgeClass: Record<string, string> = {
  'Crítico': 'bg-score-critico-bg text-score-critico',
  'Alto': 'bg-score-alto-bg text-score-alto',
  'Médio': 'bg-score-medio-bg text-score-medio',
  'Baixo': 'bg-score-baixo-bg text-score-baixo',
};

const stageBadgeClass: Record<string, string> = {
  'Engaging': 'bg-engaging/20 text-engaging',
  'Prospecting': 'bg-prospecting/20 text-prospecting',
};

const RepDashboard = () => {
  const navigate = useNavigate();
  const { pipeline, teams, products, selectedAgent, setSelectedAgent, actions, addAction, dismissedDeals, dismissDeal } = usePipelineStore();

  const [sheetOpen, setSheetOpen] = useState(false);
  const [sheetDealId, setSheetDealId] = useState('');
  const [sheetStep, setSheetStep] = useState<1 | 2>(1);
  const [sheetActionType, setSheetActionType] = useState<ActionRecord['actionType'] | null>(null);
  const [fadingDeals, setFadingDeals] = useState<Set<string>>(new Set());
  const [pipelineSortCol, setPipelineSortCol] = useState<string>('score');
  const [pipelineSortDir, setPipelineSortDir] = useState<'asc' | 'desc'>('desc');
  const [stageFilter, setStageFilter] = useState<string>('all');

  const agents = useMemo(() => {
    const set = new Set(pipeline.map(d => d.sales_agent));
    return Array.from(set).sort();
  }, [pipeline]);

  const currentAgent = selectedAgent || agents[0] || '';

  const productPriceMap = useMemo(() => {
    const map: Record<string, number> = {};
    products.forEach(p => { map[p.product] = safeFloat(p.sales_price); });
    return map;
  }, [products]);

  const agentOffice = useMemo(() => {
    const team = teams.find(t => t.sales_agent === currentAgent);
    return team?.regional_office || '';
  }, [teams, currentAgent]);

  const teamAvgDays = useMemo(() => {
    const officeAgents = new Set(teams.filter(t => t.regional_office === agentOffice).map(t => t.sales_agent));
    const closedDeals = pipeline.filter(d =>
      officeAgents.has(d.sales_agent) &&
      (d.deal_stage === 'Won' || d.deal_stage === 'Lost') &&
      d.close_date && d.close_date.trim() !== '' &&
      d.engage_date
    );
    if (closedDeals.length === 0) return 30;
    const totalDays = closedDeals.reduce((sum, d) => {
      return sum + daysBetween(d.engage_date, new Date(d.close_date));
    }, 0);
    return totalDays / closedDeals.length;
  }, [pipeline, teams, agentOffice]);

  const openDeals = useMemo(() => {
    return pipeline.filter(d =>
      d.sales_agent === currentAgent &&
      (d.deal_stage === 'Prospecting' || d.deal_stage === 'Engaging') &&
      !dismissedDeals.includes(d.opportunity_id)
    );
  }, [pipeline, currentAgent, dismissedDeals]);

  const scoredDeals: ScoredDeal[] = useMemo(() => {
    const values = openDeals.map(d => productPriceMap[d.product] || 0);
    const p90 = percentile(values, 90);

    return openDeals.map(d => {
      const est_value = productPriceMap[d.product] || 0;
      const scoreResult = calcPriorityScore(
        { deal_stage: d.deal_stage, engage_date: d.engage_date, est_value, account: d.account },
        REFERENCE_DATE,
        teamAvgDays,
        p90
      );
      return { ...d, est_value, scoreResult };
    }).sort((a, b) => {
      if (b.scoreResult.score !== a.scoreResult.score) return b.scoreResult.score - a.scoreResult.score;
      if (b.est_value !== a.est_value) return b.est_value - a.est_value;
      if (a.engage_date !== b.engage_date) return a.engage_date.localeCompare(b.engage_date);
      return displayAccount(a.account).localeCompare(displayAccount(b.account));
    });
  }, [openDeals, productPriceMap, teamAvgDays]);

  const top5 = scoredDeals.filter(d => !actions.some(a => a.dealId === d.opportunity_id)).slice(0, 5);
  const recommendedCount = Math.min(5, scoredDeals.length);
  const executionScore = recommendedCount > 0 ? Math.round((actions.length / recommendedCount) * 100) : 0;

  // At-risk deals
  const atRiskDeals = useMemo(() => {
    return scoredDeals
      .filter(d => daysBetween(d.engage_date, REFERENCE_DATE) > teamAvgDays * 1.2)
      .sort((a, b) => {
        const aDays = daysBetween(a.engage_date, REFERENCE_DATE) - teamAvgDays;
        const bDays = daysBetween(b.engage_date, REFERENCE_DATE) - teamAvgDays;
        return bDays - aDays;
      });
  }, [scoredDeals, teamAvgDays]);

  // No contact ranking
  const noContactDeals = useMemo(() => {
    return [...scoredDeals].sort((a, b) =>
      daysBetween(a.engage_date, REFERENCE_DATE) - daysBetween(b.engage_date, REFERENCE_DATE)
    ).reverse();
  }, [scoredDeals]);

  const handleExecute = (dealId: string) => {
    setSheetDealId(dealId);
    setSheetStep(1);
    setSheetActionType(null);
    setSheetOpen(true);
  };

  const handleActionType = (type: ActionRecord['actionType']) => {
    setSheetActionType(type);
    setSheetStep(2);
  };

  const handleResult = useCallback((result: ActionRecord['result']) => {
    if (!sheetActionType) return;
    addAction({ dealId: sheetDealId, actionType: sheetActionType, result });
    setSheetOpen(false);
    setFadingDeals(prev => new Set(prev).add(sheetDealId));
    setTimeout(() => {
      setFadingDeals(prev => { const n = new Set(prev); n.delete(sheetDealId); return n; });
    }, 600);
    toast({ title: 'Ação registrada ✓' });
  }, [sheetActionType, sheetDealId, addAction]);

  const handleReschedule = (dealId: string) => {
    addAction({ dealId, actionType: 'followup', result: 'rescheduled' });
    toast({ title: 'Reagendado ✓' });
  };

  const handleIgnore = (dealId: string) => {
    dismissDeal(dealId);
    toast({ title: 'Removido da lista' });
  };

  const executionMessage = executionScore >= 80
    ? { text: 'Excelente consistência! 🏆', color: 'text-won' }
    : executionScore >= 60
    ? { text: 'Boa sessão, continue!', color: 'text-engaging' }
    : executionScore >= 40
    ? { text: 'Registre mais ações para subir o score', color: 'text-prospecting' }
    : { text: 'Score baixo — tente registrar hoje', color: 'text-lost' };

  const toggleSort = (col: string) => {
    if (pipelineSortCol === col) {
      setPipelineSortDir(d => d === 'asc' ? 'desc' : 'asc');
    } else {
      setPipelineSortCol(col);
      setPipelineSortDir('desc');
    }
  };

  const sortedPipeline = useMemo(() => {
    let filtered = stageFilter === 'all' ? scoredDeals : scoredDeals.filter(d => d.deal_stage === stageFilter);
    return [...filtered].sort((a, b) => {
      let cmp = 0;
      switch (pipelineSortCol) {
        case 'account': cmp = displayAccount(a.account).localeCompare(displayAccount(b.account)); break;
        case 'product': cmp = a.product.localeCompare(b.product); break;
        case 'stage': cmp = a.deal_stage.localeCompare(b.deal_stage); break;
        case 'value': cmp = a.est_value - b.est_value; break;
        case 'score': cmp = a.scoreResult.score - b.scoreResult.score; break;
        case 'engage': cmp = a.engage_date.localeCompare(b.engage_date); break;
        default: cmp = 0;
      }
      return pipelineSortDir === 'desc' ? -cmp : cmp;
    });
  }, [scoredDeals, stageFilter, pipelineSortCol, pipelineSortDir]);

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
        <div className="max-w-2xl mx-auto flex items-center justify-between gap-3">
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
        <div className="max-w-2xl mx-auto flex gap-4 mt-2">
          <button className="text-sm pb-2 text-primary border-b-2 border-primary font-medium">
            🔥 Atividades
          </button>
          <button onClick={() => navigate('/rep/results')} className="text-sm pb-2 text-muted-foreground hover:text-foreground transition-colors">
            📊 Resultados
          </button>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
        <Tabs defaultValue="main">
          <TabsList className="w-full grid grid-cols-3 mb-6">
            <TabsTrigger value="main">Prioridades</TabsTrigger>
            <TabsTrigger value="benchmark">Benchmark</TabsTrigger>
            <TabsTrigger value="pipeline">Pipeline</TabsTrigger>
          </TabsList>

          <TabsContent value="main" className="space-y-6">
            {/* Block 1 — Day Priorities */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="font-display text-lg flex items-center gap-2">
                  🎯 Prioridades do Dia
                  <Badge variant="secondary" className="text-xs font-mono">{top5.length}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {top5.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    <p className="font-display text-lg">Todas as prioridades de hoje foram tratadas 🎉</p>
                    <p className="text-sm mt-2">Execution Score: {executionScore}% — Continue amanhã!</p>
                  </div>
                )}
                {top5.map(deal => (
                  <div
                    key={deal.opportunity_id}
                    className={`rounded-lg border border-border bg-card p-4 space-y-3 transition-all ${
                      fadingDeals.has(deal.opportunity_id) ? 'animate-fade-out line-through opacity-50' : ''
                    } ${actions.some(a => a.dealId === deal.opportunity_id) ? 'hidden' : ''}`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="space-y-1 min-w-0">
                        <p className="font-mono text-sm font-500 truncate">{displayAccount(deal.account)}</p>
                        <p className="text-xs text-muted-foreground">{deal.product}</p>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <span className={`px-2 py-0.5 rounded text-xs font-mono font-500 ${scoreBadgeClass[deal.scoreResult.label]}`}>
                          {deal.scoreResult.score} {deal.scoreResult.label}
                        </span>
                      </div>
                    </div>
                    <p className="text-xs text-muted-foreground">{deal.scoreResult.context_reason}</p>
                    <div className="flex items-center gap-2">
                      <Badge className={`text-xs ${stageBadgeClass[deal.deal_stage] || ''}`} variant="outline">
                        {deal.deal_stage}
                      </Badge>
                      <span className="text-xs text-muted-foreground">{formatCurrency(deal.est_value)}</span>
                    </div>
                    <div className="flex gap-2 pt-1">
                      <Button size="sm" className="flex-1 h-8 text-xs gap-1" onClick={() => handleExecute(deal.opportunity_id)}>
                        <Check className="h-3 w-3" /> Executado
                      </Button>
                      <Button size="sm" variant="outline" className="flex-1 h-8 text-xs gap-1" onClick={() => handleReschedule(deal.opportunity_id)}>
                        <Calendar className="h-3 w-3" /> Reagendar
                      </Button>
                      <Button size="sm" variant="ghost" className="h-8 text-xs gap-1 text-muted-foreground" onClick={() => handleIgnore(deal.opportunity_id)}>
                        <X className="h-3 w-3" /> Ignorar
                      </Button>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Block 2 — At-Risk */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="font-display text-lg flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-lost" /> Contas em Risco
                  <Badge variant="secondary" className="text-xs font-mono">{atRiskDeals.length}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {atRiskDeals.slice(0, 3).map(deal => {
                  const daysOver = Math.round(daysBetween(deal.engage_date, REFERENCE_DATE) - teamAvgDays);
                  return (
                    <div key={deal.opportunity_id} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                      <div className="min-w-0">
                        <p className="text-sm font-mono truncate">{displayAccount(deal.account)}</p>
                        <p className="text-xs text-muted-foreground">{deal.product}</p>
                      </div>
                      <span className="text-xs text-lost font-mono flex-shrink-0">{daysOver}d acima da média</span>
                    </div>
                  );
                })}
                {atRiskDeals.length > 3 && (
                  <p className="text-xs text-muted-foreground text-center pt-1">Ver todas ({atRiskDeals.length}) →</p>
                )}
                {atRiskDeals.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-4">Nenhuma conta em risco 👍</p>
                )}
              </CardContent>
            </Card>

            {/* Block 3 — No Contact */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="font-display text-lg">📵 Sem Contato</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex items-center gap-2 text-xs text-muted-foreground bg-muted/50 rounded px-3 py-2 mb-2">
                  <Info className="h-3 w-3 flex-shrink-0" />
                  <span>Calculado a partir da data de engajamento — interações reais serão registradas pelo app</span>
                </div>
                {noContactDeals.slice(0, 3).map(deal => (
                  <div key={deal.opportunity_id} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                    <div className="min-w-0">
                      <p className="text-sm font-mono truncate">{displayAccount(deal.account)}</p>
                      <p className="text-xs text-muted-foreground">{deal.product}</p>
                    </div>
                    <span className="text-xs text-prospecting font-mono flex-shrink-0">
                      {daysBetween(deal.engage_date, REFERENCE_DATE)}d
                    </span>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Block 4 — Execution Score */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="font-display text-lg">⚡ Execution Score</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col items-center gap-3 py-4">
                <span className="font-display text-5xl font-800">{Math.min(100, executionScore)}%</span>
                <span className="text-xs text-muted-foreground">Esta sessão</span>
                <Progress value={Math.min(100, executionScore)} className="w-full h-2" />
                <p className="text-xs text-muted-foreground">Meta: registre {recommendedCount} ações hoje</p>
                <p className={`text-sm font-500 ${executionMessage.color}`}>{executionMessage.text}</p>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Tab: Benchmark */}
          <TabsContent value="benchmark">
            <BenchmarkBlock currentAgent={currentAgent} />
          </TabsContent>

          {/* Tab: Full Pipeline */}
          <TabsContent value="pipeline" className="space-y-4">
            <div className="flex gap-2">
              {['all', 'Engaging', 'Prospecting'].map(s => (
                <Button
                  key={s}
                  size="sm"
                  variant={stageFilter === s ? 'default' : 'outline'}
                  className="text-xs h-7"
                  onClick={() => setStageFilter(s)}
                >
                  {s === 'all' ? 'Todos' : s}
                </Button>
              ))}
            </div>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    {[
                      { key: 'account', label: 'Conta' },
                      { key: 'product', label: 'Produto' },
                      { key: 'stage', label: 'Stage' },
                      { key: 'value', label: 'Valor' },
                      { key: 'score', label: 'Score' },
                      { key: 'engage', label: 'Engage' },
                    ].map(col => (
                      <TableHead
                        key={col.key}
                        className="cursor-pointer hover:text-foreground text-xs"
                        onClick={() => toggleSort(col.key)}
                      >
                        {col.label} {pipelineSortCol === col.key ? (pipelineSortDir === 'desc' ? '↓' : '↑') : ''}
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedPipeline.map(deal => (
                    <TableRow key={deal.opportunity_id}>
                      <TableCell className="text-xs font-mono">{displayAccount(deal.account)}</TableCell>
                      <TableCell className="text-xs">{deal.product}</TableCell>
                      <TableCell>
                        <Badge className={`text-xs ${stageBadgeClass[deal.deal_stage] || ''}`} variant="outline">{deal.deal_stage}</Badge>
                      </TableCell>
                      <TableCell className="text-xs font-mono">{formatCurrency(deal.est_value)}</TableCell>
                      <TableCell>
                        <span className={`px-1.5 py-0.5 rounded text-xs font-mono ${scoreBadgeClass[deal.scoreResult.label]}`}>
                          {deal.scoreResult.score}
                        </span>
                      </TableCell>
                      <TableCell className="text-xs font-mono">{deal.engage_date}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </TabsContent>
        </Tabs>
      </div>

      {/* Bottom Sheet */}
      <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
        <SheetContent side="bottom" className="rounded-t-2xl">
          <SheetHeader>
            <SheetTitle className="font-display">
              {sheetStep === 1 ? 'Tipo de ação' : 'Resultado'}
            </SheetTitle>
          </SheetHeader>
          <div className="py-6">
            {sheetStep === 1 && (
              <div className="grid grid-cols-2 gap-3">
                {[
                  { type: 'call' as const, icon: Phone, label: 'Liguei' },
                  { type: 'email' as const, icon: Mail, label: 'Email' },
                  { type: 'meeting' as const, icon: Handshake, label: 'Reunião' },
                  { type: 'followup' as const, icon: RefreshCw, label: 'Follow-up' },
                ].map(({ type, icon: Icon, label }) => (
                  <Button
                    key={type}
                    variant="outline"
                    className="h-16 flex flex-col gap-1"
                    onClick={() => handleActionType(type)}
                  >
                    <Icon className="h-5 w-5" />
                    <span className="text-xs">{label}</span>
                  </Button>
                ))}
              </div>
            )}
            {sheetStep === 2 && (
              <div className="grid grid-cols-2 gap-3">
                {[
                  { result: 'advanced' as const, icon: Check, label: 'Avançou de stage' },
                  { result: 'waiting' as const, icon: Clock, label: 'Aguardando' },
                  { result: 'rescheduled' as const, icon: Calendar, label: 'Reagendado' },
                  { result: 'lost' as const, icon: X, label: 'Perdido' },
                ].map(({ result, icon: Icon, label }) => (
                  <Button
                    key={result}
                    variant="outline"
                    className="h-16 flex flex-col gap-1"
                    onClick={() => handleResult(result)}
                  >
                    <Icon className="h-5 w-5" />
                    <span className="text-xs">{label}</span>
                  </Button>
                ))}
              </div>
            )}
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
};

// Benchmark sub-component
function BenchmarkBlock({ currentAgent }: { currentAgent: string }) {
  const { pipeline, teams, products } = usePipelineStore();

  const agentTeam = teams.find(t => t.sales_agent === currentAgent);
  const office = agentTeam?.regional_office || '';
  const officeAgents = new Set(teams.filter(t => t.regional_office === office).map(t => t.sales_agent));

  const calcAvgLeadTime = (agentSet: Set<string>) => {
    const closed = pipeline.filter(d =>
      agentSet.has(d.sales_agent) && d.deal_stage === 'Won' && d.close_date && d.engage_date
    );
    if (closed.length === 0) return 0;
    return Math.round(closed.reduce((s, d) => s + daysBetween(d.engage_date, new Date(d.close_date)), 0) / closed.length);
  };

  const allAgents = new Set(pipeline.map(d => d.sales_agent));
  const repAvg = calcAvgLeadTime(new Set([currentAgent]));
  const teamAvg = calcAvgLeadTime(officeAgents);
  const companyAvg = calcAvgLeadTime(allAgents);

  const maxVal = Math.max(repAvg, teamAvg, companyAvg, 1);

  const suggestion = repAvg > teamAvg
    ? `Você está ${repAvg - teamAvg}d acima da média do time. Sugestão: priorize follow-ups em Engaging > 14 dias.`
    : 'Seu lead time está na média ou abaixo — boa performance!';

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="font-display text-lg">📊 Benchmark — Lead Time</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {[
          { label: 'Você', value: repAvg, color: 'bg-primary' },
          { label: 'Equipe', value: teamAvg, color: 'bg-engaging' },
          { label: 'Empresa', value: companyAvg, color: 'bg-muted-foreground' },
        ].map(({ label, value, color }) => (
          <div key={label} className="space-y-1">
            <div className="flex justify-between text-xs">
              <span>{label}</span>
              <span className="font-mono">{value}d</span>
            </div>
            <div className="h-2 rounded-full bg-muted overflow-hidden">
              <div className={`h-full rounded-full ${color}`} style={{ width: `${(value / maxVal) * 100}%` }} />
            </div>
          </div>
        ))}
        <p className="text-xs text-muted-foreground mt-3">{suggestion}</p>
      </CardContent>
    </Card>
  );
}

export default RepDashboard;
