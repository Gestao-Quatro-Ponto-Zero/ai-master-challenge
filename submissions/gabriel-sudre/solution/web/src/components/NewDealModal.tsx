import { useState, useEffect } from 'react'
import { api } from '../lib/api'
import { X } from 'lucide-react'

interface Props {
  onClose: () => void
  onCreated: () => void
}

interface Option {
  id: number
  name: string
  price?: number
}

export function NewDealModal({ onClose, onCreated }: Props) {
  const [options, setOptions] = useState<{
    agents: Option[]
    products: Option[]
    accounts: Option[]
  } | null>(null)

  const [agentId, setAgentId] = useState<number>(0)
  const [productId, setProductId] = useState<number>(0)
  const [accountId, setAccountId] = useState<number>(0)
  const [stage, setStage] = useState('Prospecting')
  const [engageDate, setEngageDate] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.getOptions().then(setOptions).catch(console.error)
  }, [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!agentId || !productId || !accountId) {
      setError('Preencha todos os campos obrigatórios')
      return
    }
    setError('')
    setLoading(true)
    try {
      await api.createDeal({
        sales_agent_id: agentId,
        product_id: productId,
        account_id: accountId,
        deal_stage: stage,
        engage_date: stage === 'Engaging' ? engageDate || undefined : undefined,
      })
      onCreated()
    } catch (err: any) {
      setError(err.message || 'Erro ao criar oportunidade')
    } finally {
      setLoading(false)
    }
  }

  const selectedProduct = options?.products.find((p) => p.id === productId)

  const inputClass = "w-full px-3 py-2.5 rounded-lg bg-[var(--bg-input)] border border-[var(--border)] text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--g4-gold)] focus:ring-2 focus:ring-[var(--g4-gold)]/20 transition-all"
  const labelClass = "block text-xs font-semibold text-[var(--text-secondary)] mb-1.5 uppercase tracking-wider"

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="w-full max-w-lg bg-[var(--bg-secondary)] rounded-2xl shadow-[var(--shadow-lg)] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-[var(--border)]">
          <h3 className="text-lg font-bold text-[var(--g4-navy)]">Nova Oportunidade</h3>
          <button onClick={onClose} className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Form */}
        {!options ? (
          <div className="p-8 text-center text-sm text-[var(--text-secondary)]">Carregando opções...</div>
        ) : (
          <form onSubmit={handleSubmit} className="p-5 space-y-4">
            {error && (
              <div className="p-3 rounded-lg bg-[var(--danger)]/10 border border-[var(--danger)]/30 text-[var(--danger)] text-sm">{error}</div>
            )}

            <div>
              <label className={labelClass}>Vendedor *</label>
              <select value={agentId} onChange={(e) => setAgentId(Number(e.target.value))} className={inputClass}>
                <option value={0}>Selecione o vendedor</option>
                {options.agents.map((a) => (
                  <option key={a.id} value={a.id}>{a.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className={labelClass}>Produto *</label>
              <select value={productId} onChange={(e) => setProductId(Number(e.target.value))} className={inputClass}>
                <option value={0}>Selecione o produto</option>
                {options.products.map((p) => (
                  <option key={p.id} value={p.id}>{p.name} — R${p.price?.toLocaleString('pt-BR')}</option>
                ))}
              </select>
            </div>

            <div>
              <label className={labelClass}>Conta *</label>
              <select value={accountId} onChange={(e) => setAccountId(Number(e.target.value))} className={inputClass}>
                <option value={0}>Selecione a conta</option>
                {options.accounts.map((a) => (
                  <option key={a.id} value={a.id}>{a.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className={labelClass}>Etapa</label>
              <div className="flex gap-2">
                {['Prospecting', 'Engaging'].map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setStage(s)}
                    className={`flex-1 py-2 rounded-lg text-sm font-medium border transition-colors ${
                      stage === s
                        ? 'border-[var(--g4-gold)] bg-[var(--g4-gold)]/10 text-[var(--g4-gold)]'
                        : 'border-[var(--border)] text-[var(--text-secondary)]'
                    }`}
                  >
                    {s === 'Prospecting' ? 'Prospecção' : 'Em Negociação'}
                  </button>
                ))}
              </div>
            </div>

            {stage === 'Engaging' && (
              <div>
                <label className={labelClass}>Data de Engajamento</label>
                <input
                  type="date"
                  value={engageDate}
                  onChange={(e) => setEngageDate(e.target.value)}
                  className={inputClass}
                />
              </div>
            )}

            {selectedProduct && (
              <div className="p-3 rounded-lg bg-[var(--bg-primary)] border border-[var(--border)]">
                <p className="text-xs text-[var(--text-secondary)]">Valor potencial</p>
                <p className="text-lg font-bold text-[var(--g4-gold)]">
                  R${selectedProduct.price?.toLocaleString('pt-BR')}
                </p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-lg bg-[var(--g4-gold)] hover:bg-[var(--accent-hover)] text-[var(--g4-deep)] font-semibold transition-all disabled:opacity-50 shadow-sm"
            >
              {loading ? 'Criando...' : 'Criar Oportunidade'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
