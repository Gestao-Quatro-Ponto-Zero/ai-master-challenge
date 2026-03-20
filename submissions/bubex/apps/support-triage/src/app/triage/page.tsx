'use client'

import { useState } from 'react'
import type { ClassifyResult } from '@/types'

const SAMPLE_TICKETS = [
  {
    label: 'Acesso bloqueado',
    text: 'Hi, I have been locked out of my corporate account since this morning. I tried resetting my password but the authentication is not working. I need urgent access to my files and email to attend an important meeting.',
  },
  {
    label: 'Problema de hardware',
    text: 'My laptop screen started flickering and now it won\'t turn on at all. I think the display cable might be loose or the screen itself is broken. I have an important presentation tomorrow and need this fixed urgently.',
  },
  {
    label: 'Solicitação de compra',
    text: 'I need to purchase a new software license for Adobe Photoshop for my design work. Please process the procurement request and let me know the approval timeline.',
  },
  {
    label: 'Suporte RH',
    text: 'I need to request 3 days of annual leave starting next Monday. I couldn\'t find the request form on the portal and my manager asked me to submit it through the helpdesk system.',
  },
]

const CATEGORY_COLORS: Record<string, string> = {
  Hardware:                 'bg-orange-100 text-orange-700',
  'HR Support':             'bg-pink-100 text-pink-700',
  Access:                   'bg-blue-100 text-blue-700',
  Storage:                  'bg-indigo-100 text-indigo-700',
  Purchase:                 'bg-green-100 text-green-700',
  'Internal Project':       'bg-purple-100 text-purple-700',
  'Administrative rights':  'bg-red-100 text-red-700',
  Miscellaneous:            'bg-gray-100 text-gray-600',
}

const PRIORITY_COLORS: Record<string, string> = {
  Low:      'bg-gray-100 text-gray-600',
  Medium:   'bg-yellow-100 text-yellow-700',
  High:     'bg-orange-100 text-orange-700',
  Critical: 'bg-red-100 text-red-700',
}

export default function TriagePage() {
  const [text, setText] = useState('')
  const [result, setResult] = useState<ClassifyResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function classify() {
    if (!text.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await fetch('/api/classify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })
      if (!res.ok) throw new Error('Erro na classificação')
      setResult(await res.json())
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro desconhecido')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-8 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Classificador de Tickets</h1>
        <p className="text-gray-500 text-sm mt-1">
          Cole o texto de um ticket de suporte e veja a classificação por IA em tempo real.
        </p>
      </div>

      {/* Input */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
        <textarea
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder="Cole aqui o texto do ticket de suporte..."
          rows={6}
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-1 focus:ring-gray-400"
        />
        <div className="flex items-center justify-between">
          <p className="text-xs text-gray-400">{text.length} caracteres</p>
          <button
            onClick={classify}
            disabled={loading || !text.trim()}
            className="px-5 py-2 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {loading ? 'Classificando…' : 'Classificar'}
          </button>
        </div>
      </div>

      {/* Sample tickets */}
      <div>
        <p className="text-xs text-gray-400 uppercase tracking-wide font-semibold mb-2">Exemplos rápidos</p>
        <div className="flex flex-wrap gap-2">
          {SAMPLE_TICKETS.map(s => (
            <button
              key={s.label}
              onClick={() => { setText(s.text); setResult(null) }}
              className="text-xs px-3 py-1.5 border border-gray-200 rounded-lg hover:bg-gray-50 text-gray-600"
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-3 animate-pulse">
          <div className="h-4 bg-gray-100 rounded w-1/3" />
          <div className="h-2 bg-gray-100 rounded w-full" />
          <div className="h-2 bg-gray-100 rounded w-3/4" />
          <div className="h-4 bg-gray-100 rounded w-1/4 mt-4" />
        </div>
      )}

      {/* Result */}
      {result && !loading && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
          <div className="flex items-center gap-3 flex-wrap">
            <span className={`text-sm font-semibold px-3 py-1 rounded-full ${CATEGORY_COLORS[result.category] ?? 'bg-gray-100 text-gray-700'}`}>
              {result.category}
            </span>
            <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${PRIORITY_COLORS[result.suggestedPriority]}`}>
              {result.suggestedPriority}
            </span>
            {result.mode === 'fallback' && (
              <span className="text-xs text-amber-600 bg-amber-50 border border-amber-200 px-2.5 py-1 rounded-full">
                Modo offline — sem API key
              </span>
            )}
          </div>

          {/* Confidence bar */}
          <div>
            <div className="flex justify-between text-xs text-gray-500 mb-1">
              <span>Confiança</span>
              <span className="font-semibold">{Math.round(result.confidence * 100)}%</span>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${result.confidence >= 0.8 ? 'bg-green-500' : result.confidence >= 0.5 ? 'bg-yellow-400' : 'bg-gray-300'}`}
                style={{ width: `${Math.round(result.confidence * 100)}%` }}
              />
            </div>
          </div>

          <div className="text-sm text-gray-700">
            <span className="font-medium text-gray-500 text-xs uppercase tracking-wide">Raciocínio</span>
            <p className="mt-0.5">{result.reasoning}</p>
          </div>

          <div className={`rounded-lg p-3 text-sm ${result.shouldAutomate ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
            <span className={`font-semibold ${result.shouldAutomate ? 'text-green-700' : 'text-red-700'}`}>
              {result.shouldAutomate ? 'Pode ser automatizado' : 'Requer atenção humana'}
            </span>
            <p className={`text-xs mt-0.5 ${result.shouldAutomate ? 'text-green-600' : 'text-red-600'}`}>
              {result.automationReasoning}
            </p>
          </div>
        </div>
      )}

      {/* Dataset info */}
      <div className="text-xs text-gray-400 space-y-1">
        <p>Categorias: Hardware · HR Support · Access · Storage · Purchase · Internal Project · Administrative rights · Miscellaneous</p>
        <p>Modelo de classificação treinado conceitualmente com Dataset 2 — 47.837 tickets de TI classificados em 8 categorias.</p>
      </div>
    </div>
  )
}
