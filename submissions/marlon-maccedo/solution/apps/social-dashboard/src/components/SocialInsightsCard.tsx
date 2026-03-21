export function ApiFailureBanner({ context }: { context: string }) {
  return (
    <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 text-sm text-amber-900 flex items-center gap-3">
      <span className="text-lg">⚠️</span>
      <span>
        Não foi possível gerar {context} agora (falha na API OpenRouter ou resposta inválida). Confira
        créditos/key em{' '}
        <a href="https://openrouter.ai" className="underline font-medium" target="_blank" rel="noreferrer">
          openrouter.ai
        </a>{' '}
        e os logs do serviço no Railway.
      </span>
    </div>
  )
}

export function NoApiKeyBanner() {
  return (
    <div className="bg-gray-50 border border-gray-200 rounded-xl p-6 text-sm text-gray-500 flex items-center gap-3">
      <span className="text-gray-400 text-lg">🔑</span>
      <span>
        Configure <code className="bg-gray-100 px-1 rounded text-xs">OPENROUTER_API_KEY</code> para gerar
        análise estratégica via IA. Sem API key, não é possível gerar insights personalizados com base nos dados.
      </span>
    </div>
  )
}

export function InsightsSkeleton() {
  return (
    <div className="space-y-3 animate-pulse">
      {[1, 2, 3, 4].map(i => (
        <div key={i} className="h-12 bg-amber-100 rounded-lg" />
      ))}
    </div>
  )
}

export function StrategySkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="h-5 bg-gray-200 rounded w-48" />
      {[1, 2, 3, 4, 5].map(i => (
        <div key={i} className="bg-white rounded-xl border border-gray-200 p-5 flex gap-4">
          <div className="w-8 h-8 rounded-full bg-gray-200 flex-shrink-0" />
          <div className="flex-1 space-y-2">
            <div className="h-3 bg-gray-200 rounded w-32" />
            <div className="h-4 bg-gray-200 rounded w-3/4" />
            <div className="h-3 bg-gray-200 rounded w-48" />
          </div>
        </div>
      ))}
    </div>
  )
}
