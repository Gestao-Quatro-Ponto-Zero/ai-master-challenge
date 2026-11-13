'use client'

import { useState } from 'react'
import { Send, Loader2, FileText } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'

const TEST_CASES = [
  { id: 1, label: '1. Login bloqueado', text: 'I cannot log into my account' },
  { id: 2, label: '2. Tela piscando', text: 'My laptop screen is flickering' },
  { id: 3, label: '3. Compra de monitores', text: 'I need to order 5 new monitors for the team' },
  { id: 4, label: '4. Pasta compartilhada', text: 'I need access to the shared folder for project files' },
  { id: 5, label: '5. Acesso admin', text: 'Please give me admin access to the server' },
  { id: 6, label: '6. Reembolso (financeiro)', text: 'I want a refund for my defective product order #1234' },
  { id: 7, label: '7. Problema ambíguo', text: 'Something is wrong with my setup' },
  { id: 8, label: '8. Texto mínimo', text: 'help' },
  { id: 9, label: '9. Fora do escopo', text: 'What time is the company lunch today?' },
  { id: 10, label: '10. Rede fora do ar', text: 'Our entire network is down — no one can access anything' },
]

const CHANNELS = ['Email', 'Chat', 'Telefone', 'Redes Sociais']

interface TriageFormProps {
  onResult: (result: any) => void
  onLoading: (loading: boolean) => void
  onError: (error: string | null) => void
}

export function TriageForm({ onResult, onLoading, onError }: TriageFormProps) {
  const [text, setText] = useState('')
  const [channel, setChannel] = useState('Email')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    if (!text?.trim()) {
      onError('Por favor, insira o texto do chamado.')
      return
    }
    setLoading(true)
    onLoading(true)
    onError(null)
    onResult(null)

    try {
      const res = await fetch('/api/classify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text.trim(), channel }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Erro desconhecido' }))
        throw new Error(err?.detail || `Erro ${res.status}`)
      }
      const data = await res.json()
      onResult(data)
    } catch (e: any) {
      onError(e?.message || 'Falha ao conectar com o servidor de classificação.')
    } finally {
      setLoading(false)
      onLoading(false)
    }
  }

  return (
    <div className="space-y-5">
      {/* Textarea */}
      <div className="space-y-2">
        <Label htmlFor="ticket-text" className="text-sm font-medium">
          Texto do Chamado
        </Label>
        <Textarea
          id="ticket-text"
          value={text}
          onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setText(e.target.value)}
          placeholder="Ex.: I cannot log into my account and need urgent help..."
          className="min-h-[140px] resize-y text-sm"
        />
      </div>

      {/* Channel */}
      <div className="space-y-2">
        <Label className="text-sm font-medium">Canal de Origem</Label>
        <div className="flex flex-wrap gap-2">
          {CHANNELS.map((ch: string) => (
            <button
              key={ch}
              onClick={() => setChannel(ch)}
              className={cn(
                'rounded-md px-3 py-1.5 text-xs font-medium transition-colors',
                channel === ch
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground hover:bg-muted/80'
              )}
            >
              {ch}
            </button>
          ))}
        </div>
      </div>

      {/* Submit */}
      <Button
        onClick={handleSubmit}
        disabled={loading || !text?.trim()}
        className="w-full"
        size="lg"
      >
        {loading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Analisando...
          </>
        ) : (
          <>
            <Send className="mr-2 h-4 w-4" />
            Analisar Chamado
          </>
        )}
      </Button>

      {/* Test cases */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-muted-foreground" />
          <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            Casos de Teste Rápidos
          </span>
        </div>
        <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-2">
          {TEST_CASES.map((tc: any) => (
            <button
              key={tc.id}
              onClick={() => setText(tc.text)}
              className="rounded-md bg-muted/60 px-2.5 py-1.5 text-left text-[11px] font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              title={tc.text}
            >
              {tc.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
