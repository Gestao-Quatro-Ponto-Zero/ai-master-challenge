export function DashboardSimple() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-white via-blue-50 to-blue-100">
      {/* Hero Section - NOVO VISUAL */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-12 rounded-b-3xl shadow-xl">
        <h2 className="text-5xl font-bold mb-4">🔥 Bem-vindo de volta!</h2>
        <p className="text-xl text-blue-100">
          Novo Dashboard Minimalista com Design Profissional
        </p>
      </div>

      {/* Conteúdo Principal */}
      <div className="max-w-7xl mx-auto p-8 space-y-8">
        {/* TOP 5 Leads HOT */}
        <div>
          <h3 className="text-3xl font-bold text-slate-900 mb-6">
            ⭐ Seus Leads Prioritários
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {[
              { company: "Tech Innovations", score: 94, tier: "HOT" },
              { company: "Digital Solutions", score: 89, tier: "HOT" },
              { company: "Cloud Systems", score: 87, tier: "HOT" },
              { company: "Data Analytics", score: 85, tier: "HOT" },
              { company: "AI Ventures", score: 82, tier: "HOT" },
            ].map((lead, idx) => (
              <div
                key={idx}
                className="bg-white rounded-2xl p-6 shadow-md hover:shadow-xl transition-all border-2 border-blue-200 hover:border-blue-600 cursor-pointer"
              >
                <div className="flex items-center justify-between mb-4">
                  <span className="text-3xl font-bold text-blue-600">
                    {lead.score}
                  </span>
                  <span className="text-2xl">🔥</span>
                </div>
                <h4 className="font-bold text-slate-900 mb-2">{lead.company}</h4>
                <p className="text-sm text-slate-600">
                  Prontos para ação
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { label: "Deals Ativos", value: "24", emoji: "📊" },
            { label: "Leads HOT", value: "5", emoji: "🔥" },
            { label: "Win Rate", value: "68%", emoji: "✅" },
            { label: "Pipeline", value: "$2.5M", emoji: "💰" },
          ].map((kpi, idx) => (
            <div
              key={idx}
              className="bg-white rounded-xl p-6 shadow-sm border border-slate-200 hover:shadow-md transition-all"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-600 text-sm font-medium">
                    {kpi.label}
                  </p>
                  <p className="text-3xl font-bold text-blue-600 mt-2">
                    {kpi.value}
                  </p>
                </div>
                <div className="text-4xl">{kpi.emoji}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-2xl p-8 shadow-md border-l-4 border-blue-600">
            <h4 className="text-2xl font-bold text-slate-900 mb-4">
              ✨ Novo Design Minimalista
            </h4>
            <ul className="space-y-2 text-slate-700">
              <li>✓ Cores profissionais: Azul + Cinza + Branco</li>
              <li>✓ Sidebar branca e limpa (esquerda)</li>
              <li>✓ Header com filtros modernos (topo)</li>
              <li>✓ Dashboard visual e intuitivo</li>
            </ul>
          </div>

          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-2xl p-8 shadow-md border-l-4 border-blue-600">
            <h4 className="text-2xl font-bold text-blue-900 mb-4">
              🎨 Paleta de Cores
            </h4>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded bg-blue-600"></div>
                <span className="text-slate-700">Azul 600 - Ação Principal</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded bg-slate-200"></div>
                <span className="text-slate-700">Cinza - Texto & Borders</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded bg-white border-2 border-slate-300"></div>
                <span className="text-slate-700">Branco - Fundo Cards</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Message */}
        <div className="bg-blue-50 border-2 border-blue-300 rounded-2xl p-8 text-center">
          <p className="text-xl text-blue-900 font-semibold">
            🎉 Layout redesenhado com sucesso!
          </p>
          <p className="text-slate-600 mt-2">
            Sidebar branca • Header azul • Dashboard minimalista
          </p>
        </div>
      </div>
    </div>
  );
}
