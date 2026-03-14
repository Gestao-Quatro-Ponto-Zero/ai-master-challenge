import type { PipelineOpportunity, SalesTeam } from '@/types';

interface TeamPageProps {
  pipeline: PipelineOpportunity[];
  salesTeams: SalesTeam[];
}

export function TeamPage({ pipeline, salesTeams }: TeamPageProps) {
  // Calculate metrics per agent
  const agentMetrics = salesTeams.map((team) => {
    const agentDeals = pipeline.filter((d) => d.sales_agent === team.sales_agent);
    const wonDeals = agentDeals.filter((d) => d.deal_stage === 'Won');
    const lostDeals = agentDeals.filter((d) => d.deal_stage === 'Lost');
    const activeDealss = agentDeals.filter(
      (d) => d.deal_stage === 'Engaging' || d.deal_stage === 'Prospecting'
    );

    const winRate =
      wonDeals.length + lostDeals.length > 0
        ? wonDeals.length / (wonDeals.length + lostDeals.length)
        : 0;

    const pipelineValue = activeDealss.reduce((sum, d) => sum + d.close_value, 0);

    return {
      ...team,
      totalDeals: agentDeals.length,
      wonDeals: wonDeals.length,
      lostDeals: lostDeals.length,
      activeDealss: activeDealss.length,
      winRate,
      pipelineValue,
      avgTicket:
        wonDeals.length > 0
          ? wonDeals.reduce((sum, d) => sum + d.close_value, 0) / wonDeals.length
          : 0,
    };
  });

  // Sort by win rate
  const sorted = [...agentMetrics].sort((a, b) => b.winRate - a.winRate);

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="text-[10px] font-black text-hubspot-dark/40 uppercase tracking-[0.2em] ml-1">
        Performance do Time de Vendas ({salesTeams.length} total)
      </div>

      <div className="bg-white rounded-hb border-2 border-hubspot-gray-200 shadow-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-hubspot-gray-100 border-b-2 border-hubspot-gray-200">
              <tr>
                <th className="px-6 py-4 text-left text-[10px] font-black text-hubspot-black uppercase tracking-widest">Posição</th>
                <th className="px-6 py-4 text-left text-[10px] font-black text-hubspot-black uppercase tracking-widest">Vendedor</th>
                <th className="px-6 py-4 text-left text-[10px] font-black text-hubspot-black uppercase tracking-widest">Manager</th>
                <th className="px-6 py-4 text-left text-[10px] font-black text-hubspot-black uppercase tracking-widest">Escritório</th>
                <th className="px-6 py-4 text-left text-[10px] font-black text-hubspot-black uppercase tracking-widest">Win Rate</th>
                <th className="px-6 py-4 text-left text-[10px] font-black text-hubspot-black uppercase tracking-widest">Deals (W/L)</th>
                <th className="px-6 py-4 text-left text-[10px] font-black text-hubspot-black uppercase tracking-widest">Pipeline (K)</th>
                <th className="px-6 py-4 text-left text-[10px] font-black text-hubspot-black uppercase tracking-widest">Ticket Médio</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-hubspot-gray-100">
              {sorted.map((agent, idx) => (
                <tr key={agent.sales_agent} className="hover:bg-hubspot-gray-100/50 transition-colors group">
                  <td className="px-6 py-5">
                    <span className="text-xl font-black text-hubspot-black tracking-tighter">#{idx + 1}</span>
                  </td>
                  <td className="px-6 py-5">
                    <p className="font-bold text-hubspot-black uppercase tracking-wider text-xs">{agent.sales_agent}</p>
                  </td>
                  <td className="px-6 py-5 text-hubspot-dark/70 font-bold text-xs">
                    {agent.manager}
                  </td>
                  <td className="px-6 py-5">
                    <span className="px-2 py-1 bg-hubspot-gray-100 text-[9px] font-black text-hubspot-dark/50 rounded uppercase tracking-tighter">
                      {agent.regional_office}
                    </span>
                  </td>
                  <td className="px-6 py-5">
                    <span className="text-sm font-black text-green-700 bg-green-50 px-3 py-1 rounded-full border border-green-200">
                      {(agent.winRate * 100).toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-6 py-5 font-bold text-hubspot-dark/60 text-xs">
                    {agent.wonDeals}W <span className="text-hubspot-dark/20 mx-1">/</span> {agent.lostDeals}L
                  </td>
                  <td className="px-6 py-5">
                    <span className="font-black text-hubspot-black text-xs">
                      ${(agent.pipelineValue / 1000).toFixed(0)}k
                    </span>
                  </td>
                  <td className="px-6 py-5 text-hubspot-dark/40 font-black text-xs italic">
                    ${agent.avgTicket.toFixed(0)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
