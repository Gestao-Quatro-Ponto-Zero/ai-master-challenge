'use client';
import { useEffect, useState } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import Sidebar from '@/components/Sidebar';
import DealRow from '@/components/DealRow';
import { Filter, Search, Download } from 'lucide-react';

export default function Home() {
  const [data, setData] = useState<{ metrics: any, deals: any[] } | null>(null);
  const [loading, setLoading] = useState(true);

  const agentName = "Darcel Schlecht";

  useEffect(() => {
    const fetchData = async () => {
      try {
        const dashboardRes = await fetch(`http://localhost:8000/api/dashboard?agent=${encodeURIComponent(agentName)}`);
        const dashboardData = await dashboardRes.json();
        
        const dealsRes = await fetch(`http://localhost:8000/api/deals?agent=${encodeURIComponent(agentName)}`);
        const dealsData = await dealsRes.json();
        
        setData({
          metrics: dashboardData.metrics,
          deals: dealsData.deals
        });
      } catch (err) {
        console.error("Failed to fetch API", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [agentName]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-xl font-medium text-gray-500 animate-pulse">Sincronizando funil de vendas...</div>
      </div>
    );
  }

  // Preparar dados para o Recharts
  const statusColors: Record<string, string> = { "Quentes": "#F97316", "Frios/Estagnados": "#EF4444", "Mornos": "#E5E7EB" };
  const chartStatus = Object.keys(data?.metrics.leads_por_status || {}).map(key => ({
    name: key,
    value: data?.metrics.leads_por_status[key],
    color: statusColors[key] || '#9CA3AF'
  }));

  const sectorColors = ['#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#6366F1'];
  const chartSector = Object.keys(data?.metrics.leads_por_setor || {}).map((key, i) => ({
    name: key,
    value: data?.metrics.leads_por_setor[key],
    color: sectorColors[i % sectorColors.length]
  }));
  
  // Agrupar leads por mês de engajamento simulado para o Gráfico de Tendência (usando os 10 primeiros deals como exemplo de histórico)
  const trendData = [
    { name: '10 Dia(s)', deals: 4, valor: 4500 },
    { name: '20 Dia(s)', deals: 12, valor: 12500 },
    { name: '40 Dia(s)', deals: 8, valor: 8300 },
    { name: '60 Dia(s)', deals: 25, valor: 32000 },
    { name: '80+ Dias', deals: 42, valor: 51000 },
  ];

  return (
    <div className="min-h-screen bg-[#F9FAFB] text-gray-900 font-sans flex">
      <Sidebar />
      
      <main className="ml-64 p-8 w-full">
        {/* Header Superior */}
        <header className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Funil de Vendas</h1>
            <p className="text-gray-500 text-sm mt-1">Inteligência de Vendas Portamento • Consultor: {agentName}</p>
          </div>
          
          <div className="flex gap-3">
            <button className="flex items-center gap-2 bg-white border border-gray-200 px-4 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50 shadow-sm transition-all">
              <Download size={16} /> Exportar CSV
            </button>
            <button className="flex items-center gap-2 bg-blue-600 text-white px-5 py-2 rounded-lg text-sm font-bold hover:bg-blue-700 shadow-sm transition-all">
              Nova Oportunidade
            </button>
          </div>
        </header>

        {/* Abas e Filtros (Mock) */}
        <div className="flex justify-between items-center mb-6 border-b border-gray-200 pb-4">
          <div className="flex gap-6">
            <button className="text-blue-600 font-semibold border-b-2 border-blue-600 pb-4 -mb-[17px]">Todas Oportunidades</button>
            <button className="text-gray-500 font-medium hover:text-gray-800 pb-4">Sinais Quentes</button>
            <button className="text-gray-500 font-medium hover:text-gray-800 pb-4">Risco de Estagnação</button>
          </div>
          <div className="flex gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
              <input type="text" placeholder="Buscar empresa..." className="pl-9 pr-4 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-blue-500 shadow-sm w-64" />
            </div>
            <button className="flex items-center gap-2 bg-white border border-gray-200 px-4 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50 shadow-sm">
              <Filter size={16} /> Filtros
            </button>
          </div>
        </div>

        {/* Linha de Gráficos (SaaS Style) */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          
          {/* Card: Expected Value */}
          <div className="bg-white border border-gray-100 p-6 rounded-2xl shadow-[0_2px_10px_-3px_rgba(6,81,237,0.1)] flex flex-col justify-center relative overflow-hidden">
             <div className="absolute top-0 right-0 w-24 h-24 bg-blue-50 opacity-50 rounded-full blur-2xl -mr-10 -mt-10"></div>
             <h3 className="text-gray-500 text-xs font-bold uppercase tracking-wider mb-2">Valor Esperado AI</h3>
             <p className="text-3xl font-black text-gray-900">R$ {(data?.metrics.valor_esperado_total ?? 0).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}</p>
             <p className="text-xs text-green-600 font-bold mt-2 flex items-center gap-1">
               <span className="bg-green-100 text-green-700 px-1.5 py-0.5 rounded">↑ 14%</span> vs. Valor Bruto
             </p>
          </div>

          {/* Card: Donut Status */}
          <div className="bg-white border border-gray-100 p-6 rounded-2xl shadow-sm flex items-center gap-4">
            <div className="w-24 h-24 relative flex-shrink-0">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={chartStatus} innerRadius={25} outerRadius={40} dataKey="value" stroke="none">
                    {chartStatus.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex items-center justify-center flex-col">
                <span className="text-lg font-bold leading-none">{data?.metrics.oportunidades_ativas}</span>
              </div>
            </div>
            <div className="flex flex-col gap-1 w-full">
              <h3 className="text-gray-900 font-bold text-sm">Saúde do Funil</h3>
              <ul className="text-xs text-gray-500 space-y-1 mt-1">
                <li className="flex justify-between items-center"><span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-orange-500"></div> Quentes</span> <b>{data?.metrics.sinais_quentes}</b></li>
                <li className="flex justify-between items-center"><span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-red-500"></div> Estagnados</span> <b>{data?.metrics.estagnados}</b></li>
                <li className="flex justify-between items-center"><span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-gray-200"></div> Mornos</span> <b>{(data?.metrics.oportunidades_ativas ?? 0) - (data?.metrics.sinais_quentes ?? 0) - (data?.metrics.estagnados ?? 0)}</b></li>
              </ul>
            </div>
          </div>

          {/* Card: Donut Setores */}
          <div className="bg-white border border-gray-100 p-6 rounded-2xl shadow-sm flex items-center gap-4">
            <div className="w-24 h-24 relative flex-shrink-0">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={chartSector} innerRadius={25} outerRadius={40} dataKey="value" stroke="none">
                    {chartSector.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex flex-col gap-1 w-full">
              <h3 className="text-gray-900 font-bold text-sm">Top Setores</h3>
              <ul className="text-xs text-gray-500 space-y-1 mt-1">
                {chartSector.slice(0,3).map((s, i) => (
                  <li key={i} className="flex justify-between items-center truncate">
                    <span className="flex items-center gap-1 truncate"><div className="w-2 h-2 rounded-full flex-shrink-0" style={{backgroundColor: s.color}}></div> <span className="truncate">{s.name}</span></span> <b>{s.value}</b>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Card: Tendência (Bar Chart) */}
          <div className="bg-white border border-gray-100 p-6 rounded-2xl shadow-sm flex flex-col justify-between h-full">
             <h3 className="text-gray-900 font-bold text-sm mb-2">Volume vs Estagnação</h3>
             <div className="h-20 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={trendData}>
                    <Tooltip cursor={{fill: '#f3f4f6'}} contentStyle={{fontSize: '12px', borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'}}/>
                    <Bar dataKey="deals" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
             </div>
          </div>
          
        </div>

        {/* Tabela de Leads (Prioritized Action Board) */}
        <section className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="px-6 py-5 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
            <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
              Pipeline Priorizado 
              <span className="bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded-full font-bold">Ordenado por AI Score</span>
            </h2>
            <span className="text-sm text-gray-500 font-medium">Exibindo os primeiros 50 registros</span>
          </div>
          
          <div className="p-6">
            <div className="grid grid-cols-12 gap-4 px-4 pb-3 mb-2 border-b border-gray-100 text-xs font-bold text-gray-400 uppercase tracking-wider">
              <div className="col-span-3">Cliente / Setor</div>
              <div className="col-span-3">Produto</div>
              <div className="col-span-2">Valor</div>
              <div className="col-span-2">Status AI</div>
              <div className="col-span-1 text-center">Score</div>
              <div className="col-span-1 text-right">Ação</div>
            </div>
            
            <div className="flex flex-col">
              {data?.deals.slice(0, 50).map((deal, idx) => (
                <DealRow key={deal.opportunity_id || idx} deal={deal} />
              ))}
            </div>
          </div>
        </section>

      </main>
    </div>
  );
}
