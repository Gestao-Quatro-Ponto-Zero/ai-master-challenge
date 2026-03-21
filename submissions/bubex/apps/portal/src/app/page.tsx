export const dynamic = 'force-dynamic'

type Color = 'blue' | 'amber' | 'emerald' | 'violet'

interface Challenge {
  id: string
  title: string
  domain: string
  description: string
  url: string
  color: Color
}

const colorMap: Record<Color, { badge: string; border: string; button: string }> = {
  blue: {
    badge: 'bg-blue-100 text-blue-700',
    border: 'border-l-blue-500',
    button: 'bg-blue-600 hover:bg-blue-700 text-white',
  },
  amber: {
    badge: 'bg-amber-100 text-amber-700',
    border: 'border-l-amber-500',
    button: 'bg-amber-600 hover:bg-amber-700 text-white',
  },
  emerald: {
    badge: 'bg-emerald-100 text-emerald-700',
    border: 'border-l-emerald-500',
    button: 'bg-emerald-600 hover:bg-emerald-700 text-white',
  },
  violet: {
    badge: 'bg-violet-100 text-violet-700',
    border: 'border-l-violet-500',
    button: 'bg-violet-600 hover:bg-violet-700 text-white',
  },
}

export default function Home() {
  const challenges: Challenge[] = [
    {
      id: 'data-001',
      title: 'Diagnóstico de Churn',
      domain: 'Data / Analytics',
      description:
        'Análise preditiva de churn em base SaaS: segmentação de risco, diagnóstico de causas e plano de ação com retenção direcionada.',
      url: process.env.URL_CHURN ?? 'http://localhost:3002',
      color: 'blue',
    },
    {
      id: 'process-002',
      title: 'Redesign de Suporte',
      domain: 'Operations / CX',
      description:
        'Triagem inteligente de tickets com classificador de prioridade, análise de sentimento e proposta de automação do fluxo de atendimento.',
      url: process.env.URL_SUPPORT ?? 'http://localhost:3003',
      color: 'amber',
    },
    {
      id: 'build-003',
      title: 'Lead Scorer',
      domain: 'Sales / RevOps',
      description:
        'Modelo preditivo de score de leads com dados de CRM, ranqueamento de oportunidades e recomendações de priorização para o time comercial.',
      url: process.env.URL_LEAD_SCORER ?? 'http://localhost:3001',
      color: 'emerald',
    },
    {
      id: 'marketing-004',
      title: 'Estratégia Social Media',
      domain: 'Marketing',
      description:
        'Dashboard de performance em redes sociais: engajamento, ROI de patrocínios, segmentação de audiência e estratégia de conteúdo orientada a dados.',
      url: process.env.URL_SOCIAL ?? 'http://localhost:3004',
      color: 'violet',
    },
  ]

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-gray-900 text-white">
        <div className="max-w-5xl mx-auto px-6 py-14">
          <p className="text-xs font-semibold tracking-widest uppercase text-gray-500 mb-3">
            G4 Educação — AI Master Challenge
          </p>
          <h1 className="text-4xl font-bold tracking-tight mb-3">Portfólio de Soluções</h1>
          <p className="text-gray-400 text-base max-w-xl">
            Quatro desafios de negócio resolvidos com uso estratégico de inteligência artificial — da
            análise de dados à automação de processos.
          </p>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-12 flex-1 w-full">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {challenges.map((c) => {
            const colors = colorMap[c.color]
            return (
              <div
                key={c.id}
                className={`bg-white rounded-xl border-l-4 ${colors.border} shadow-sm hover:shadow-md transition-shadow p-6 flex flex-col gap-4`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <span
                      className={`inline-block text-xs font-mono font-semibold px-2 py-0.5 rounded ${colors.badge} mb-2`}
                    >
                      {c.id}
                    </span>
                    <h2 className="text-xl font-bold text-gray-900 leading-tight">{c.title}</h2>
                  </div>
                  <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded whitespace-nowrap shrink-0">
                    {c.domain}
                  </span>
                </div>

                <p className="text-sm text-gray-600 leading-relaxed flex-1">{c.description}</p>

                <a
                  href={c.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`inline-flex items-center gap-2 self-start text-sm font-semibold px-4 py-2 rounded-lg transition-colors ${colors.button}`}
                >
                  Abrir Dashboard
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                    />
                  </svg>
                </a>
              </div>
            )
          })}
        </div>
      </main>

      <footer className="py-8 text-center text-xs text-gray-400">
        Submissão — bubex · AI Master Challenge 2025
      </footer>
    </div>
  )
}
