'use client'

import { useState } from 'react'
import { TriageForm } from './triage-form'
import { TriageResult } from './triage-result'
import { AlertCircle } from 'lucide-react'

export function TriagePageClient() {
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Coluna esquerda: Entrada */}
      <div>
        <div className="rounded-lg border border-border/60 bg-card p-5" style={{ boxShadow: 'var(--shadow-md)' }}>
          <h2 className="mb-4 font-display text-lg font-semibold tracking-tight text-foreground">
            Inserir Chamado
          </h2>
          <TriageForm
            onResult={setResult}
            onLoading={setLoading}
            onError={setError}
          />
        </div>
      </div>

      {/* Coluna direita: Resultado */}
      <div>
        {error && (
          <div className="mb-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 dark:border-red-800/50 dark:bg-red-950/20">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-600 dark:text-red-400" />
            <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
          </div>
        )}

        {loading && (
          <div className="flex items-center justify-center rounded-lg border border-border/60 bg-card p-12" style={{ boxShadow: 'var(--shadow-sm)' }}>
            <div className="text-center">
              <div className="mx-auto mb-3 h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              <p className="text-sm text-muted-foreground">Classificando o chamado...</p>
            </div>
          </div>
        )}

        {!loading && result && <TriageResult result={result} />}

        {!loading && !result && !error && (
          <div className="flex items-center justify-center rounded-lg border border-dashed border-border/60 bg-muted/30 p-12">
            <div className="text-center">
              <p className="text-sm text-muted-foreground">
                Insira o texto de um chamado e clique em <strong>"Analisar Chamado"</strong> para ver a classificação.
              </p>
              <p className="mt-2 text-xs text-muted-foreground/70">
                Ou selecione um dos casos de teste rápidos.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
