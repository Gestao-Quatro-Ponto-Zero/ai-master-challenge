import React, { useState, useMemo, useRef } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  PieChart, Pie, Cell, Legend, ComposedChart, Line, ReferenceLine
} from 'recharts';
import axios from 'axios';
import { 
  Target, Users, Package, Building2, AlertCircle, CheckCircle2, 
  Clock, TrendingUp, Filter, Search, ChevronDown, ChevronUp,
  FileSpreadsheet, LayoutDashboard, ListFilter, Upload, X,
  Sun, Moon, HelpCircle, ArrowRight, ArrowLeft, Globe, Key, Link as LinkIcon, Loader2
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import Papa from 'papaparse';

import { Account, SalesTeam, Product, Deal, ScoredDeal, ScoreExplanation } from './types';
import { calculateDealScore, WEIGHT_MATURITY, WEIGHT_AGENT, WEIGHT_PRODUCT, WEIGHT_FIRMOGRAPHICS } from './utils/scoring';
import { sampleAccounts, sampleSalesTeams, sampleProducts, samplePipeline } from './sampleData';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export default function App() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [salesTeams, setSalesTeams] = useState<SalesTeam[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [pipeline, setPipeline] = useState<Deal[]>([]);

  const hasData = pipeline.length > 0;

  const [selectedAgent, setSelectedAgent] = useState('Todos');
  const [selectedStage, setSelectedStage] = useState('Todos');
  const [minScore, setMinScore] = useState(0);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isTutorialOpen, setIsTutorialOpen] = useState(false);
  const [tutorialStep, setTutorialStep] = useState(0);

  // API State
  const [importMethod, setImportMethod] = useState<'csv' | 'api'>('csv');
  const [apiUrl, setApiUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [apiLoading, setApiLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const fetchDataFromAPI = async () => {
    if (!apiUrl) {
      setApiError('Por favor, insira uma URL válida.');
      return;
    }

    setApiLoading(true);
    setApiError(null);

    try {
      const response = await axios.get(apiUrl, {
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'X-API-Key': apiKey, // Common variants
        }
      });

      const data = response.data;

      // Validation
      if (!data || typeof data !== 'object') {
        throw new Error('Formato de resposta inválido. Esperado um objeto JSON.');
      }

      const requiredKeys = ['accounts', 'teams', 'products', 'pipeline'];
      const missingKeys = requiredKeys.filter(key => !Array.isArray(data[key]));

      if (missingKeys.length > 0) {
        throw new Error(`O JSON da API está faltando as seguintes chaves obrigatórias: ${missingKeys.join(', ')}`);
      }

      // Validate pipeline structure
      if (data.pipeline.length > 0) {
        const firstDeal = data.pipeline[0];
        const requiredDealFields = ['opportunity_id', 'deal_stage', 'engage_date'];
        const missingFields = requiredDealFields.filter(f => !(f in firstDeal));
        if (missingFields.length > 0) {
          throw new Error(`Estrutura de Deal inválida. Campos obrigatórios ausentes: ${missingFields.join(', ')}`);
        }
      }

      // Update state
      setAccounts(data.accounts);
      setSalesTeams(data.teams);
      setProducts(data.products);
      setPipeline(data.pipeline);
      
      setIsUploadOpen(false);
      alert('Dados sincronizados via API com sucesso!');
    } catch (err: any) {
      console.error('API Fetch Error:', err);
      setApiError(err.response?.data?.message || err.message || 'Erro ao conectar com a API.');
    } finally {
      setApiLoading(false);
    }
  };

  // Calculate scores
  const scoredPipeline = useMemo(() => {
    if (pipeline.length === 0) return [];

    // Detect the most recent engage_date in the dataset to use as "Today"
    let latestEngageDate = new Date(0);
    pipeline.forEach(d => {
      if (d.engage_date) {
        const dDate = new Date(d.engage_date);
        if (dDate > latestEngageDate) latestEngageDate = dDate;
      }
    });

    // Use the latest engage_date as the reference date (Today)
    // Fallback to current date only if no engage_date is found
    const referenceDate = latestEngageDate.getTime() > 0 ? latestEngageDate : new Date();

    return pipeline.map(deal => {
      const { score, explanation } = calculateDealScore(deal, accounts, salesTeams, products, pipeline, referenceDate);
      return { ...deal, score, explanation };
    });
  }, [pipeline, accounts, salesTeams, products]);

  // Apply filters
  const filteredPipeline = useMemo(() => {
    // Strictly focus on active deals for prioritization (Engaging and Prospecting)
    let result = scoredPipeline.filter(d => ['Engaging', 'Prospecting'].includes(d.deal_stage));

    if (selectedStage !== 'Todos') {
      result = result.filter(d => d.deal_stage === selectedStage);
    }

    if (selectedAgent !== 'Todos') {
      result = result.filter(d => d.sales_agent === selectedAgent);
    }

    result = result.filter(d => d.score >= minScore);

    return result.sort((a, b) => b.score - a.score);
  }, [scoredPipeline, selectedAgent, selectedStage, minScore]);

  const activeDeals = filteredPipeline; 

  // Metrics
  const avgScore = activeDeals.length > 0 
    ? activeDeals.reduce((acc, d) => acc + d.score, 0) / activeDeals.length 
    : 0;
  const highPriorityCount = activeDeals.filter(d => d.score >= 75).length;
  const attentionCount = activeDeals.filter(d => d.score < 30).length;

  // Chart Data: Distribution
  const distributionData = useMemo(() => {
    const binCount = 20;
    const bins = Array(binCount).fill(0);
    activeDeals.forEach(d => {
      const binIdx = Math.min(Math.floor(d.score / (100 / binCount)), binCount - 1);
      bins[binIdx]++;
    });
    return bins.map((count, i) => ({
      range: `${i * (100 / binCount)}-${(i + 1) * (100 / binCount)}`,
      count
    }));
  }, [activeDeals]);

  // Chart Data: Stages
  const stageData = useMemo(() => {
    const counts: Record<string, number> = {};
    activeDeals.forEach(d => {
      counts[d.deal_stage] = (counts[d.deal_stage] || 0) + 1;
    });
    return Object.entries(counts).map(([name, value]) => ({ name, value }));
  }, [activeDeals]);

  const COLORS = ['#3b82f6', '#8b5cf6', '#22c55e', '#f59e0b', '#ef4444'];

  const handleFileUpload = (type: 'accounts' | 'teams' | 'products' | 'pipeline', file: File) => {
    Papa.parse(file, {
      header: true,
      dynamicTyping: true,
      complete: (results) => {
        const data = results.data as any[];
        if (type === 'accounts') setAccounts(data);
        else if (type === 'teams') setSalesTeams(data);
        else if (type === 'products') setProducts(data);
        else if (type === 'pipeline') setPipeline(data);
      }
    });
  };

  return (
    <div className={cn(
      "min-h-screen transition-colors duration-300 font-sans pb-20",
      theme === 'light' ? "bg-g4-bg-light text-g4-navy" : "bg-slate-900 text-white"
    )}>
      {/* Header / Banner Principal */}
      <header className={cn(
        "sticky top-0 z-50 border-b transition-colors duration-300",
        theme === 'light' ? "bg-g4-navy text-white border-g4-gray-blue/20" : "bg-slate-950 text-white border-white/10"
      )} style={{ borderLeft: '12px solid #476382' }}>
        <div className="max-w-7xl mx-auto px-4 h-20 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-g4-gray-blue rounded-xl flex items-center justify-center text-white shadow-lg">
              <Target size={28} />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white">G4 AI MASTER</h1>
              <p className="text-sm text-g4-ice-blue font-medium uppercase tracking-wider">Lead Scorer: Priorização Estratégica para Escala de Vendas</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button 
              onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
              className={cn(
                "p-2.5 rounded-xl transition-all duration-200 border",
                theme === 'light' 
                  ? "bg-white/10 hover:bg-white/20 border-white/20 text-white" 
                  : "bg-slate-800 hover:bg-slate-700 border-white/10 text-yellow-400"
              )}
              title={theme === 'light' ? "Mudar para modo escuro" : "Mudar para modo claro"}
            >
              {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
            </button>

            <button 
              onClick={() => setIsTutorialOpen(true)}
              className={cn(
                "flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold transition-all duration-200 border",
                theme === 'light'
                  ? "bg-white hover:bg-gray-50 text-g4-navy border-g4-border"
                  : "bg-slate-800 hover:bg-slate-700 text-white border-white/10"
              )}
            >
              <HelpCircle size={18} className="text-g4-gray-blue" />
              Tutorial
            </button>

            <button 
              onClick={() => setIsUploadOpen(true)}
              className={cn(
                "flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold transition-all duration-200 border shadow-sm",
                theme === 'light'
                  ? "bg-g4-gray-blue hover:bg-g4-gray-blue/80 text-white border-transparent"
                  : "bg-slate-800 hover:bg-slate-700 text-white border-white/10"
              )}
            >
              <Upload size={18} />
              Conectar Dados CRM
            </button>
            <div className="h-8 w-px bg-white/20" />
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-g4-ice-blue flex items-center justify-center text-g4-navy font-bold text-sm shadow-inner">
                FM
              </div>
              <span className="text-sm font-semibold hidden md:block text-white">Fernando Machado</span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {!hasData ? (
          <WelcomeView theme={theme} onConnect={() => setIsUploadOpen(true)} onTutorial={() => setIsTutorialOpen(true)} />
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
            
            {/* Sidebar Filters - Permanent Dark Mode as per guidelines */}
            <aside className="lg:col-span-1 space-y-6">
            <div className="bg-g4-navy text-white rounded-2xl p-6 shadow-xl border border-g4-gray-blue/30">
              <div className="flex items-center gap-2 mb-6">
                <Filter size={18} className="text-g4-ice-blue" />
                <h2 className="font-bold text-lg">Filtros</h2>
              </div>

              <div className="space-y-5">
                <div>
                  <label className="text-[10px] font-bold text-g4-ice-blue/60 uppercase tracking-widest mb-2 block">Vendedor</label>
                  <select 
                    value={selectedAgent}
                    onChange={(e) => setSelectedAgent(e.target.value)}
                    className="w-full bg-slate-800/50 border border-white/10 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-g4-gray-blue outline-none transition-all"
                  >
                    <option value="Todos">Todos os Agentes</option>
                    {Array.from(new Set(salesTeams.map(t => t.sales_agent))).sort().map(agent => (
                      <option key={agent} value={agent}>{agent}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-[10px] font-bold text-g4-ice-blue/60 uppercase tracking-widest mb-2 block">Stage do Deal</label>
                  <select 
                    value={selectedStage}
                    onChange={(e) => setSelectedStage(e.target.value)}
                    className="w-full bg-slate-800/50 border border-white/10 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-g4-gray-blue outline-none transition-all"
                  >
                    <option value="Todos">Todos os Stages Ativos</option>
                    <option value="Engaging">Engaging</option>
                    <option value="Prospecting">Prospecting</option>
                  </select>
                </div>

                <div>
                  <div className="flex justify-between items-center mb-2">
                    <label className="text-[10px] font-bold text-g4-ice-blue/60 uppercase tracking-widest block">Score Mínimo</label>
                    <span className="text-xs font-bold text-g4-ice-blue">{minScore}</span>
                  </div>
                  <input 
                    type="range" 
                    min="0" max="100" step="5"
                    value={minScore}
                    onChange={(e) => setMinScore(parseInt(e.target.value))}
                    className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-g4-gray-blue"
                  />
                </div>
              </div>

              <div className="mt-8 pt-8 border-t border-white/10">
                <h3 className="text-[10px] font-bold text-g4-ice-blue/60 uppercase tracking-widest mb-4">Pesos do Algoritmo</h3>
                <div className="space-y-4">
                  <WeightBar label="Maturidade" weight={WEIGHT_MATURITY * 100} color="bg-blue-500" />
                  <WeightBar label="Agente" weight={WEIGHT_AGENT * 100} color="bg-purple-500" />
                  <WeightBar label="Produto" weight={WEIGHT_PRODUCT * 100} color="bg-emerald-500" />
                  <WeightBar label="Firmographics" weight={WEIGHT_FIRMOGRAPHICS * 100} color="bg-amber-500" />
                </div>
              </div>
            </div>

            <div className="bg-g4-gray-blue rounded-2xl p-6 text-white shadow-lg shadow-g4-gray-blue/20">
              <TrendingUp className="mb-4 text-g4-ice-blue" size={24} />
              <h3 className="font-bold text-lg mb-2">Insight do Dia</h3>
              <p className="text-g4-ice-blue text-sm leading-relaxed">
                Deals na "Zona de Ouro" (30-120 dias) têm 75% mais chance de fechamento. Priorize os leads marcados em verde hoje.
              </p>
            </div>
          </aside>

          {/* Main Content */}
          <div className="lg:col-span-3 space-y-8">
            
            {/* Metrics Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
              <MetricCard 
                label="Total de Deals" 
                value={activeDeals.length} 
                icon={<LayoutDashboard size={20} />} 
                color="blue"
                theme={theme}
              />
              <MetricCard 
                label="Score Médio" 
                value={avgScore.toFixed(1)} 
                icon={<TrendingUp size={20} />} 
                color="yellow"
                theme={theme}
              />
              <MetricCard 
                label="Alta Prioridade" 
                value={highPriorityCount} 
                icon={<CheckCircle2 size={20} />} 
                color="emerald"
                theme={theme}
              />
              <MetricCard 
                label="Requer Atenção" 
                value={attentionCount} 
                icon={<AlertCircle size={20} />} 
                color="rose"
                theme={theme}
              />
            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              <div className={cn(
                "rounded-2xl p-6 shadow-sm border transition-colors duration-300",
                theme === 'light' ? "bg-white border-g4-border" : "bg-slate-800 border-white/10"
              )}>
                <h3 className="font-bold mb-6 flex items-center gap-2">
                  <TrendingUp size={18} className="text-g4-gray-blue" />
                  Distribuição de Probabilidade
                </h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={distributionData}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={theme === 'light' ? "#f0f0f0" : "#334155"} />
                      <XAxis 
                        dataKey="range" 
                        axisLine={false} 
                        tickLine={false} 
                        tick={{fontSize: 10, fill: theme === 'light' ? '#64748b' : '#94a3b8'}} 
                      />
                      <YAxis 
                        axisLine={false} 
                        tickLine={false} 
                        tick={{fontSize: 12, fill: theme === 'light' ? '#64748b' : '#94a3b8'}} 
                      />
                      <Tooltip 
                        contentStyle={{ 
                          borderRadius: '12px', 
                          border: 'none', 
                          boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)',
                          backgroundColor: theme === 'light' ? '#ffffff' : '#1e293b',
                          color: theme === 'light' ? '#1e293b' : '#ffffff'
                        }}
                        cursor={{ fill: theme === 'light' ? '#f8fafc' : '#334155' }}
                      />
                      <Bar dataKey="count" fill="#476382" radius={[2, 2, 0, 0]} />
                      
                      {/* Reference Lines from Python logic */}
                      <ReferenceLine x="50-55" stroke="#fbbf24" strokeDasharray="3 3" label={{ position: 'top', value: 'Médio', fill: '#fbbf24', fontSize: 10 }} />
                      <ReferenceLine x="75-80" stroke="#22c55e" strokeDasharray="3 3" label={{ position: 'top', value: 'Alta', fill: '#22c55e', fontSize: 10 }} />
                      <ReferenceLine x="30-35" stroke="#ef4444" strokeDasharray="3 3" label={{ position: 'top', value: 'Atenção', fill: '#ef4444', fontSize: 10 }} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className={cn(
                "rounded-2xl p-6 shadow-sm border transition-colors duration-300",
                theme === 'light' ? "bg-white border-g4-border" : "bg-slate-800 border-white/10"
              )}>
                <h3 className="font-bold mb-6 flex items-center gap-2">
                  <ListFilter size={18} className="text-g4-gray-blue" />
                  Distribuição por Stage
                </h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={stageData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={80}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {stageData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip 
                        contentStyle={{ 
                          borderRadius: '12px', 
                          border: 'none', 
                          boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)',
                          backgroundColor: theme === 'light' ? '#ffffff' : '#1e293b',
                          color: theme === 'light' ? '#1e293b' : '#ffffff'
                        }}
                      />
                      <Legend 
                        verticalAlign="bottom" 
                        height={36}
                        formatter={(value) => <span className={theme === 'light' ? "text-slate-600" : "text-slate-300"}>{value}</span>}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            {/* Top 10 List */}
            <section>
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold tracking-tight">🏆 Top Deals para Focar Hoje</h2>
                  <p className={cn(
                    "text-sm transition-colors duration-300",
                    theme === 'light' ? "text-g4-soft-gray" : "text-slate-400"
                  )}>Ordenados pelo score de probabilidade de fechamento</p>
                </div>
              </div>

              <div className="space-y-4">
                {activeDeals.slice(0, 10).map((deal: ScoredDeal) => (
                  <div key={deal.opportunity_id}>
                    <DealExpandable deal={deal} accounts={accounts} theme={theme} />
                  </div>
                ))}
                {activeDeals.length === 0 && (
                  <div className={cn(
                    "rounded-2xl p-12 text-center border border-dashed transition-colors duration-300",
                    theme === 'light' ? "bg-white border-g4-border" : "bg-slate-800 border-white/20"
                  )}>
                    <Search size={48} className="mx-auto text-g4-soft-gray mb-4" />
                    <p className="text-g4-soft-gray font-medium">Nenhum deal encontrado com os filtros atuais.</p>
                  </div>
                )}
              </div>
            </section>

            {/* Full Table */}
            <section className={cn(
              "rounded-2xl shadow-sm border transition-colors duration-300 overflow-hidden",
              theme === 'light' ? "bg-white border-g4-border" : "bg-slate-800 border-white/10"
            )}>
              <div className={cn(
                "p-6 border-b flex items-center justify-between",
                theme === 'light' ? "border-g4-border" : "border-white/10"
              )}>
                <h2 className="font-bold">📋 Todos os Deals</h2>
                <span className={cn(
                  "text-xs font-bold px-2 py-1 rounded",
                  theme === 'light' ? "bg-g4-bg-light text-g4-soft-gray" : "bg-slate-700 text-slate-400"
                )}>{filteredPipeline.length} Total</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className={cn(
                    "font-bold uppercase tracking-widest text-[10px]",
                    theme === 'light' ? "bg-g4-bg-light text-g4-soft-gray" : "bg-slate-900/50 text-slate-500"
                  )}>
                    <tr>
                      <th className="px-6 py-4">Prioridade</th>
                      <th className="px-6 py-4">ID</th>
                      <th className="px-6 py-4">Vendedor</th>
                      <th className="px-6 py-4">Produto</th>
                      <th className="px-6 py-4">Cliente</th>
                      <th className="px-6 py-4">Stage</th>
                      <th className="px-6 py-4">Score</th>
                      <th className="px-6 py-4">Valor</th>
                    </tr>
                  </thead>
                  <tbody className={cn(
                    "divide-y",
                    theme === 'light' ? "divide-g4-border" : "divide-white/5"
                  )}>
                    {filteredPipeline.map((deal) => {
                      const { icon, color } = getPriorityInfo(deal.score);
                      return (
                        <tr key={deal.opportunity_id} className={cn(
                          "transition-colors",
                          theme === 'light' ? "hover:bg-g4-bg-light" : "hover:bg-white/5"
                        )}>
                          <td className="px-6 py-4">
                            <span className={cn("inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold", color)}>
                              {icon} {deal.score >= 75 ? 'Alta' : deal.score >= 50 ? 'Média' : 'Baixa'}
                            </span>
                          </td>
                          <td className="px-6 py-4 font-mono font-medium text-g4-gray-blue">{deal.opportunity_id}</td>
                          <td className="px-6 py-4 font-medium">{deal.sales_agent}</td>
                          <td className="px-6 py-4">{deal.product}</td>
                          <td className={cn(
                            "px-6 py-4",
                            theme === 'light' ? "text-g4-soft-gray" : "text-slate-400"
                          )}>{deal.account || '---'}</td>
                          <td className="px-6 py-4">
                            <span className={cn(
                              "px-2 py-1 rounded text-xs font-medium",
                              theme === 'light' ? "bg-g4-bg-light text-g4-navy" : "bg-slate-700 text-slate-300"
                            )}>{deal.deal_stage}</span>
                          </td>
                          <td className="px-6 py-4 font-bold">{deal.score.toFixed(1)}</td>
                          <td className="px-6 py-4 font-medium">
                            {deal.close_value ? `R$ ${deal.close_value.toLocaleString()}` : '---'}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        </div>
      )}
    </main>

      {/* Tutorial Modal */}
      {isTutorialOpen && (
        <TutorialModal 
          step={tutorialStep} 
          setStep={setTutorialStep} 
          onClose={() => {
            setIsTutorialOpen(false);
            setTutorialStep(0);
          }} 
          theme={theme}
          onOpenUpload={() => {
            setIsTutorialOpen(false);
            setIsUploadOpen(true);
          }}
        />
      )}

      {/* Upload Modal */}
      {isUploadOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
          <div className={cn(
            "rounded-3xl w-full max-w-md p-8 shadow-2xl border transition-colors duration-300",
            theme === 'light' ? "bg-white border-g4-border" : "bg-slate-900 border-white/10"
          )}>
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold">Conectar Dados CRM</h3>
              <button 
                onClick={() => setIsUploadOpen(false)} 
                className={cn(
                  "p-2 rounded-full transition-colors",
                  theme === 'light' ? "hover:bg-g4-bg-light" : "hover:bg-white/10"
                )}
              >
                <X size={20} />
              </button>
            </div>

            {/* Toggle Switch */}
            <div className="flex p-1 bg-slate-100 dark:bg-slate-800 rounded-xl mb-8">
              <button 
                onClick={() => setImportMethod('csv')}
                className={cn(
                  "flex-1 flex items-center justify-center gap-2 py-2 text-xs font-bold rounded-lg transition-all",
                  importMethod === 'csv' 
                    ? "bg-white dark:bg-slate-700 shadow-sm text-g4-navy dark:text-white" 
                    : "text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
                )}
              >
                <FileSpreadsheet size={14} />
                Upload CSV
              </button>
              <button 
                onClick={() => setImportMethod('api')}
                className={cn(
                  "flex-1 flex items-center justify-center gap-2 py-2 text-xs font-bold rounded-lg transition-all",
                  importMethod === 'api' 
                    ? "bg-white dark:bg-slate-700 shadow-sm text-g4-navy dark:text-white" 
                    : "text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
                )}
              >
                <Globe size={14} />
                Conectar API
              </button>
            </div>
            
            {importMethod === 'csv' ? (
              <div className="space-y-6">
                <UploadField label="Accounts (accounts.csv)" onUpload={(f) => handleFileUpload('accounts', f)} theme={theme} />
                <UploadField label="Sales Teams (sales_teams.csv)" onUpload={(f) => handleFileUpload('teams', f)} theme={theme} />
                <UploadField label="Products (products.csv)" onUpload={(f) => handleFileUpload('products', f)} theme={theme} />
                <UploadField label="Pipeline (sales_pipeline.csv)" onUpload={(f) => handleFileUpload('pipeline', f)} theme={theme} />
                
                <button 
                  onClick={() => setIsUploadOpen(false)}
                  className="w-full mt-8 py-3.5 bg-g4-gray-blue text-white font-bold rounded-xl hover:bg-g4-navy transition-all shadow-lg"
                >
                  Concluir
                </button>
              </div>
            ) : (
              <div className="space-y-5">
                <div className="space-y-2">
                  <label className="text-[10px] font-bold uppercase tracking-widest text-slate-500">URL da API</label>
                  <div className="relative">
                    <LinkIcon size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input 
                      type="text" 
                      placeholder="https://api.exemplo.com/v1/data"
                      value={apiUrl}
                      onChange={(e) => setApiUrl(e.target.value)}
                      className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-white/10 rounded-xl pl-11 pr-4 py-3 text-sm focus:ring-2 focus:ring-g4-gray-blue outline-none transition-all"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-[10px] font-bold uppercase tracking-widest text-slate-500">API Key / Token</label>
                  <div className="relative">
                    <Key size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input 
                      type="password" 
                      placeholder="Sua chave de acesso"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-white/10 rounded-xl pl-11 pr-4 py-3 text-sm focus:ring-2 focus:ring-g4-gray-blue outline-none transition-all"
                    />
                  </div>
                </div>

                {apiError && (
                  <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-start gap-3">
                    <AlertCircle size={16} className="text-rose-500 shrink-0 mt-0.5" />
                    <p className="text-xs text-rose-600 dark:text-rose-400 font-medium">{apiError}</p>
                  </div>
                )}

                <div className="pt-4">
                  <button 
                    onClick={fetchDataFromAPI}
                    disabled={apiLoading}
                    className="w-full py-3.5 bg-g4-gray-blue text-white font-bold rounded-xl hover:bg-g4-navy transition-all shadow-lg flex items-center justify-center gap-2 disabled:opacity-70"
                  >
                    {apiLoading ? (
                      <>
                        <Loader2 size={18} className="animate-spin" />
                        Sincronizando...
                      </>
                    ) : (
                      <>
                        Sincronizar Agora
                      </>
                    )}
                  </button>
                  <p className="text-[10px] text-center text-slate-500 mt-4 leading-relaxed">
                    A API deve retornar um JSON com as chaves: <br/>
                    <code className="text-g4-gray-blue">accounts, teams, products, pipeline</code>
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Footer Methodology */}
      <footer className="max-w-7xl mx-auto px-4 mt-12 mb-20">
        <div className={cn(
          "rounded-2xl p-8 border transition-colors duration-300",
          theme === 'light' ? "bg-white border-g4-border" : "bg-slate-800 border-white/10"
        )}>
          <h3 className="font-bold text-lg mb-6 flex items-center gap-2">
            <AlertCircle size={20} className="text-g4-gray-blue" />
            Metodologia
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <MethodologyItem 
              title="Zona da Morte" 
              desc="0-15 dias: 56% de conversão - maior volume de perdas históricas."
              icon={<Clock className="text-rose-500" />}
              theme={theme}
            />
            <MethodologyItem 
              title="Zona de Maturidade" 
              desc="16-120 dias: 71-75% de conversão - melhor performance de fechamento."
              icon={<TrendingUp className="text-emerald-500" />}
              theme={theme}
            />
            <MethodologyItem 
              title="Morte Súbita" 
              desc="150+ dias: 0% de conversão - nenhum deal histórico ganhou após 5 meses."
              icon={<AlertCircle className="text-rose-600" />}
              theme={theme}
            />
            <MethodologyItem 
              title="Account Fantasma" 
              desc="68% do pipeline sem account linkado - não penalizado no score final."
              icon={<Building2 className="text-amber-500" />}
              theme={theme}
            />
            <MethodologyItem 
              title="Variação por Agente" 
              desc="55%-70% de conversão - fator de alto peso (30%) no cálculo preditivo."
              icon={<Users className="text-indigo-500" />}
              theme={theme}
            />
          </div>
        </div>
      </footer>
    </div>
  );
}

function MetricCard({ label, value, icon, color, theme }: { label: string, value: string | number, icon: React.ReactNode, color: string, theme: 'light' | 'dark' }) {
  const colorClasses: Record<string, string> = {
    blue: "bg-blue-500/10 text-blue-500",
    yellow: "bg-yellow-500/10 text-yellow-500",
    emerald: "bg-emerald-500/10 text-emerald-500",
    rose: "bg-rose-500/10 text-rose-500",
  };

  return (
    <div className={cn(
      "rounded-2xl p-6 shadow-sm border transition-colors duration-300",
      theme === 'light' ? "bg-white border-g4-border" : "bg-slate-800 border-white/10"
    )}>
      <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center mb-4", colorClasses[color])}>
        {icon}
      </div>
      <p className={cn(
        "text-[10px] font-bold uppercase tracking-widest mb-1",
        theme === 'light' ? "text-g4-soft-gray" : "text-slate-500"
      )}>{label}</p>
      <h4 className="text-2xl font-bold">{value}</h4>
    </div>
  );
}

function WeightBar({ label, weight, color }: { label: string, weight: number, color: string }) {
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-[10px] font-bold uppercase tracking-wider">
        <span className="text-g4-ice-blue/60">{label}</span>
        <span className="text-white">{weight}%</span>
      </div>
      <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
        <div className={cn("h-full rounded-full", color)} style={{ width: `${weight}%` }} />
      </div>
    </div>
  );
}

function DealExpandable({ deal, accounts, theme }: { deal: ScoredDeal, accounts: Account[], theme: 'light' | 'dark' }) {
  const [isOpen, setIsOpen] = useState(false);
  const { icon, color, bg } = getPriorityInfo(deal.score);
  const accountInfo = accounts.find(a => a.account === deal.account);

  return (
    <div className={cn(
      "rounded-2xl shadow-sm border transition-all duration-300 overflow-hidden",
      theme === 'light' ? "bg-white border-g4-border" : "bg-slate-800 border-white/10",
      isOpen && (theme === 'light' ? "border-g4-gray-blue ring-4 ring-g4-gray-blue/5" : "border-g4-gray-blue ring-4 ring-g4-gray-blue/10")
    )}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-6 py-5 flex items-center justify-between text-left"
      >
        <div className="flex items-center gap-4">
          <div className={cn("w-12 h-12 rounded-xl flex items-center justify-center text-xl shadow-inner", bg)}>
            {icon}
          </div>
          <div>
            <div className="flex items-center gap-2 mb-0.5">
              <span className="font-bold text-lg">{deal.opportunity_id}</span>
              <span className={theme === 'light' ? "text-g4-soft-gray" : "text-slate-600"}>—</span>
              <span className={theme === 'light' ? "text-g4-gray-blue font-semibold" : "text-slate-300 font-semibold"}>{deal.product}</span>
            </div>
            <div className="flex items-center gap-3 text-xs font-medium">
              <span className={cn("flex items-center gap-1", theme === 'light' ? "text-g4-soft-gray" : "text-slate-400")}>
                <Users size={12} /> {deal.sales_agent}
              </span>
              <span className={cn("w-1 h-1 rounded-full", theme === 'light' ? "bg-g4-border" : "bg-slate-700")} />
              <span className={cn("flex items-center gap-1", theme === 'light' ? "text-g4-soft-gray" : "text-slate-400")}>
                <Building2 size={12} /> {deal.account || 'Sem Account'}
              </span>
              {accountInfo?.office_location && (
                <>
                  <span className={cn("w-1 h-1 rounded-full", theme === 'light' ? "bg-g4-border" : "bg-slate-700")} />
                  <span className={theme === 'light' ? "text-g4-soft-gray" : "text-slate-400"}>📍 {accountInfo.office_location}</span>
                </>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-6">
          <div className="text-right">
            <p className={cn("text-[10px] font-bold uppercase tracking-widest mb-0.5", theme === 'light' ? "text-g4-soft-gray" : "text-slate-500")}>Score</p>
            <p className={cn("text-2xl font-black", color.split(' ')[0])}>{deal.score.toFixed(1)}</p>
          </div>
          {isOpen ? <ChevronUp className="text-g4-soft-gray" /> : <ChevronDown className="text-g4-soft-gray" />}
        </div>
      </button>

      {isOpen && (
        <div className={cn(
          "px-6 pb-6 pt-2 border-t transition-colors duration-300",
          theme === 'light' ? "border-g4-bg-light" : "border-white/5"
        )}>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-6">
              <div className="flex flex-wrap gap-4 mb-2">
                {accountInfo?.subsidiary_of && (
                  <div className={cn(
                    "px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-tight",
                    theme === 'light' ? "bg-g4-bg-light text-g4-soft-gray" : "bg-slate-900 text-slate-500"
                  )}>
                    Subsidiary of: {accountInfo.subsidiary_of}
                  </div>
                )}
                {accountInfo?.year_established && (
                  <div className={cn(
                    "px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-tight",
                    theme === 'light' ? "bg-g4-bg-light text-g4-soft-gray" : "bg-slate-900 text-slate-500"
                  )}>
                    Est. {accountInfo.year_established}
                  </div>
                )}
              </div>
              <div>
                <h4 className={cn(
                  "text-[10px] font-bold uppercase tracking-widest mb-4",
                  theme === 'light' ? "text-g4-soft-gray" : "text-slate-500"
                )}>🧠 Explicação do Score</h4>
                <div className="space-y-3">
                  <ScoreComponent label="Maturidade" data={deal.explanation.maturity} color="blue" theme={theme} />
                  <ScoreComponent label="Agente" data={deal.explanation.agent} color="purple" theme={theme} />
                  <ScoreComponent label="Produto" data={deal.explanation.product} color="emerald" theme={theme} />
                  <ScoreComponent label="Firmographics" data={deal.explanation.firmographics} color="amber" theme={theme} />
                </div>
              </div>
            </div>
            <div className="space-y-6">
              <div>
                <h4 className={cn(
                  "text-[10px] font-bold uppercase tracking-widest mb-4",
                  theme === 'light' ? "text-g4-soft-gray" : "text-slate-500"
                )}>📊 Composição</h4>
                <div className="h-48">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={[
                      { name: 'Mat', val: deal.explanation.maturity.score, fill: '#3b82f6' },
                      { name: 'Age', val: deal.explanation.agent.score, fill: '#8b5cf6' },
                      { name: 'Prd', val: deal.explanation.product.score, fill: '#10b981' },
                      { name: 'Fir', val: deal.explanation.firmographics.score, fill: '#f59e0b' },
                    ]}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={theme === 'light' ? "#f0f0f0" : "#334155"} />
                      <XAxis 
                        dataKey="name" 
                        axisLine={false} 
                        tickLine={false} 
                        tick={{fontSize: 10, fill: theme === 'light' ? '#64748b' : '#94a3b8'}} 
                      />
                      <YAxis hide domain={[0, 100]} />
                      <Bar dataKey="val" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ScoreComponent({ label, data, color, theme }: { label: string, data: any, color: string, theme: 'light' | 'dark' }) {
  const colors: Record<string, string> = {
    blue: "text-blue-500 bg-blue-500/10",
    purple: "text-purple-500 bg-purple-500/10",
    emerald: "text-emerald-500 bg-emerald-500/10",
    amber: "text-amber-500 bg-amber-500/10",
  };

  return (
    <div className={cn(
      "flex items-start gap-4 p-3 rounded-xl border transition-colors duration-300",
      theme === 'light' ? "bg-g4-bg-light border-g4-border" : "bg-slate-900 border-white/5"
    )}>
      <div className={cn("px-2 py-1 rounded-lg font-bold text-sm min-w-[45px] text-center", colors[color])}>
        {data.score}
      </div>
      <div className="flex-1">
        <div className="flex justify-between items-center mb-1">
          <span className={cn("text-xs font-bold", theme === 'light' ? "text-g4-navy" : "text-white")}>{label}</span>
          <span className="text-[10px] font-bold text-g4-soft-gray uppercase">{data.weight}</span>
        </div>
        <p className={cn("text-xs leading-relaxed", theme === 'light' ? "text-slate-600" : "text-slate-400")}>{data.explanation}</p>
      </div>
    </div>
  );
}

function MethodologyItem({ title, desc, icon, theme }: { title: string, desc: string, icon: React.ReactNode, theme: 'light' | 'dark' }) {
  return (
    <div className="flex gap-4">
      <div className="mt-1">{icon}</div>
      <div>
        <h4 className={cn("font-bold text-sm mb-1", theme === 'light' ? "text-g4-navy" : "text-white")}>{title}</h4>
        <p className={cn("text-xs leading-relaxed", theme === 'light' ? "text-g4-soft-gray" : "text-slate-400")}>{desc}</p>
      </div>
    </div>
  );
}

function TutorialModal({ step, setStep, onClose, theme, onOpenUpload }: { 
  step: number, 
  setStep: (s: number) => void, 
  onClose: () => void, 
  theme: 'light' | 'dark',
  onOpenUpload: () => void
}) {
  const steps = [
    {
      title: "Bem-vindo ao G4 AI MASTER",
      content: "Esta ferramenta utiliza Inteligência Artificial e análise histórica para priorizar seu pipeline de vendas. Vamos aprender como tirar o melhor proveito dela?",
      icon: <LayoutDashboard className="text-g4-gray-blue" size={40} />,
      action: "Próximo"
    },
    {
      title: "1. Conectar Dados CRM",
      content: "O primeiro passo é conectar seus dados. Você pode fazer o upload de planilhas CSV ou conectar diretamente via API para automação.",
      icon: <Upload className="text-blue-500" size={40} />,
      action: "Entendi",
      secondaryAction: { label: "Ir para Conexão", onClick: onOpenUpload }
    },
    {
      title: "2. Filtros Inteligentes",
      content: "Na barra lateral, você pode filtrar o dashboard por Vendedor, Estágio do Funil ou Score Mínimo. Isso ajuda a focar nos deals que realmente importam hoje.",
      icon: <Filter className="text-purple-500" size={40} />,
      action: "Próximo"
    },
    {
      title: "3. Os 4 Pilares do Score",
      content: "Nosso algoritmo avalia: Maturidade (tempo de vida), Performance do Agente (histórico), Fit de Produto (preço vs tabela) e Firmographics (setor e tamanho da empresa).",
      icon: <Target className="text-emerald-500" size={40} />,
      action: "Próximo"
    },
    {
      title: "4. Métricas de Prioridade",
      content: "O dashboard destaca 'Alta Prioridade' (Score > 75) para fechamento imediato e 'Requer Atenção' (Score < 30) para deals em risco de expiração.",
      icon: <CheckCircle2 className="text-amber-500" size={40} />,
      action: "Próximo"
    },
    {
      title: "5. Metodologia G4",
      content: "Baseamos a lógica em Zonas: 'Morte' (0-15 dias), 'Maturidade' (16-120 dias) e 'Morte Súbita' (150+ dias). O tempo é o maior inimigo ou aliado do seu deal.",
      icon: <Clock className="text-rose-500" size={40} />,
      action: "Finalizar Tour"
    }
  ];

  const currentStep = steps[step];

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-[200] flex items-center justify-center p-4">
      <div className={cn(
        "w-full max-w-lg rounded-3xl overflow-hidden shadow-2xl border animate-in fade-in zoom-in duration-300",
        theme === 'light' ? "bg-white border-g4-border" : "bg-slate-900 border-white/10"
      )}>
        <div className="p-8">
          <div className="flex justify-between items-start mb-8">
            <div className="w-16 h-16 rounded-2xl bg-g4-gray-blue/10 flex items-center justify-center">
              {currentStep.icon}
            </div>
            <button onClick={onClose} className="p-2 hover:bg-black/5 rounded-lg transition-colors">
              <X size={20} className="text-slate-400" />
            </button>
          </div>

          <h2 className="text-2xl font-bold mb-4">{currentStep.title}</h2>
          <p className={cn(
            "text-lg leading-relaxed mb-8",
            theme === 'light' ? "text-g4-soft-gray" : "text-slate-400"
          )}>
            {currentStep.content}
          </p>

          <div className="flex items-center justify-between mt-12">
            <div className="flex gap-1.5">
              {steps.map((_, i) => (
                <div 
                  key={i} 
                  className={cn(
                    "h-1.5 rounded-full transition-all duration-300",
                    i === step ? "w-8 bg-g4-gray-blue" : "w-2 bg-slate-700"
                  )}
                />
              ))}
            </div>

            <div className="flex gap-3">
              {step > 0 && (
                <button 
                  onClick={() => setStep(step - 1)}
                  className="flex items-center gap-2 px-4 py-2 text-sm font-bold hover:text-g4-gray-blue transition-colors"
                >
                  <ArrowLeft size={16} /> Voltar
                </button>
              )}
              
              {currentStep.secondaryAction && (
                <button 
                  onClick={currentStep.secondaryAction.onClick}
                  className="px-6 py-2.5 bg-slate-800 text-white text-sm font-bold rounded-xl hover:bg-slate-700 transition-all"
                >
                  {currentStep.secondaryAction.label}
                </button>
              )}

              <button 
                onClick={() => {
                  if (step < steps.length - 1) {
                    setStep(step + 1);
                  } else {
                    onClose();
                  }
                }}
                className="flex items-center gap-2 px-8 py-2.5 bg-g4-gray-blue text-white text-sm font-bold rounded-xl hover:bg-g4-navy transition-all shadow-lg shadow-g4-gray-blue/20"
              >
                {currentStep.action} <ArrowRight size={16} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function UploadField({ label, onUpload, theme }: { label: string, onUpload: (file: File) => void, theme: 'light' | 'dark' }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState<string | null>(null);

  return (
    <div>
      <label className={cn(
        "text-[10px] font-bold uppercase tracking-widest mb-2 block",
        theme === 'light' ? "text-g4-soft-gray" : "text-slate-500"
      )}>{label}</label>
      <div 
        onClick={() => inputRef.current?.click()}
        className={cn(
          "border-2 border-dashed rounded-2xl p-4 flex items-center justify-between cursor-pointer transition-all",
          theme === 'light' 
            ? "border-g4-border bg-g4-bg-light hover:border-g4-gray-blue hover:bg-g4-ice-blue/30" 
            : "border-white/10 bg-slate-800/50 hover:border-g4-gray-blue hover:bg-slate-800"
        )}
      >
        <div className="flex items-center gap-3">
          <FileSpreadsheet size={20} className="text-g4-soft-gray" />
          <span className={cn("text-sm font-medium", theme === 'light' ? "text-slate-600" : "text-slate-300")}>
            {fileName || 'Selecionar arquivo...'}
          </span>
        </div>
        <input 
          ref={inputRef}
          type="file" 
          accept=".csv" 
          className="hidden" 
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) {
              setFileName(file.name);
              onUpload(file);
            }
          }}
        />
      </div>
    </div>
  );
}

function getPriorityInfo(score: number) {
  if (score >= 75) return { icon: "🟢", color: "text-emerald-600 bg-emerald-50", bg: "bg-emerald-50" };
  if (score >= 50) return { icon: "🟡", color: "text-amber-600 bg-amber-50", bg: "bg-amber-50" };
  if (score >= 30) return { icon: "🟠", color: "text-orange-600 bg-orange-50", bg: "bg-orange-50" };
  return { icon: "🔴", color: "text-rose-600 bg-rose-50", bg: "bg-rose-50" };
}

function WelcomeView({ theme, onConnect, onTutorial }: { theme: 'light' | 'dark', onConnect: () => void, onTutorial: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center max-w-3xl mx-auto">
      <div className="w-24 h-24 bg-g4-gray-blue/10 rounded-3xl flex items-center justify-center text-g4-gray-blue mb-8 animate-bounce">
        <Target size={48} />
      </div>
      
      <h2 className={cn(
        "text-4xl font-black mb-4 tracking-tight",
        theme === 'light' ? "text-g4-navy" : "text-white"
      )}>
        Bem-vindo ao <span className="text-g4-gray-blue">G4 AI MASTER</span>
      </h2>
      
      <p className={cn(
        "text-lg mb-10 leading-relaxed",
        theme === 'light' ? "text-slate-600" : "text-slate-400"
      )}>
        Sua central de inteligência para priorização de vendas. 
        Para começar a visualizar seus insights e scores, conecte seus dados do CRM via CSV ou API.
      </p>
      
      <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
        <button 
          onClick={onConnect}
          className="flex items-center justify-center gap-3 px-8 py-4 bg-g4-gray-blue text-white font-bold rounded-2xl hover:bg-g4-navy transition-all shadow-xl shadow-g4-gray-blue/20 group"
        >
          <Upload size={20} className="group-hover:scale-110 transition-transform" />
          Conectar Dados CRM
        </button>
        
        <button 
          onClick={onTutorial}
          className={cn(
            "flex items-center justify-center gap-3 px-8 py-4 font-bold rounded-2xl transition-all border",
            theme === 'light' 
              ? "bg-white text-g4-navy border-g4-border hover:bg-slate-50" 
              : "bg-slate-800 text-white border-white/10 hover:bg-slate-700"
          )}
        >
          <HelpCircle size={20} className="text-g4-gray-blue" />
          Ver Tutorial
        </button>
      </div>
      
      <div className="mt-16 grid grid-cols-1 sm:grid-cols-3 gap-8 w-full">
        <WelcomeFeature 
          icon={<Globe className="text-blue-500" />} 
          title="Conexão API" 
          desc="Integre diretamente com seu CRM para dados em tempo real."
          theme={theme}
        />
        <WelcomeFeature 
          icon={<FileSpreadsheet className="text-emerald-500" />} 
          title="Upload CSV" 
          desc="Importe suas planilhas rapidamente para análise imediata."
          theme={theme}
        />
        <WelcomeFeature 
          icon={<TrendingUp className="text-purple-500" />} 
          title="IA Scoring" 
          desc="Algoritmo avançado para identificar os deals mais quentes."
          theme={theme}
        />
      </div>
    </div>
  );
}

function WelcomeFeature({ icon, title, desc, theme }: { icon: React.ReactNode, title: string, desc: string, theme: 'light' | 'dark' }) {
  return (
    <div className={cn(
      "p-6 rounded-2xl border transition-all",
      theme === 'light' ? "bg-white border-g4-border" : "bg-slate-900 border-white/5"
    )}>
      <div className="w-10 h-10 bg-slate-100 dark:bg-slate-800 rounded-xl flex items-center justify-center mb-4 mx-auto">
        {icon}
      </div>
      <h4 className={cn("font-bold text-sm mb-2", theme === 'light' ? "text-g4-navy" : "text-white")}>{title}</h4>
      <p className="text-xs text-slate-500 leading-relaxed">{desc}</p>
    </div>
  );
}


