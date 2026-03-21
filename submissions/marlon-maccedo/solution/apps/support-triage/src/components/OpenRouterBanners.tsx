/** Banner quando a chave existe mas a API falhou ou resposta inválida. */
export function ApiFailureBanner({ context }: { context: string }) {
  return (
    <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-900 flex items-center gap-3">
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

export function NoApiKeyBanner({ context }: { context: string }) {
  return (
    <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 text-sm text-gray-500 flex items-center gap-3">
      <span className="text-gray-400 text-lg">🔑</span>
      <span>
        Configure <code className="bg-gray-100 px-1 rounded text-xs">OPENROUTER_API_KEY</code> para ativar {context}.
      </span>
    </div>
  )
}
