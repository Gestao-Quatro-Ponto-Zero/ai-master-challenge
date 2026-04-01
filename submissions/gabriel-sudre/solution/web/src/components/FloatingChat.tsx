import { useState, useRef, useEffect } from 'react'
import { api } from '../lib/api'
import { MessageSquareText, X, Send, Sparkles } from 'lucide-react'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export function FloatingChat() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMsg: Message = { role: 'user', content: input.trim() }
    const newMessages = [...messages, userMsg]
    setMessages(newMessages)
    setInput('')
    setLoading(true)

    try {
      const data = await api.chat(newMessages)
      setMessages([...newMessages, { role: 'assistant', content: data.response }])
    } catch (err: any) {
      setMessages([...newMessages, { role: 'assistant', content: `Erro: ${err.message}` }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <button
        onClick={() => setOpen(!open)}
        className="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-[var(--g4-gold)] hover:bg-[var(--accent-hover)] text-[var(--g4-deep)] shadow-lg shadow-[var(--g4-gold)]/25 flex items-center justify-center transition-all z-50 hover:scale-110"
      >
        {open ? <X size={22} strokeWidth={2} /> : <MessageSquareText size={22} strokeWidth={2} />}
      </button>

      {open && (
        <div className="fixed bottom-24 right-6 w-96 h-[520px] rounded-2xl bg-[var(--bg-secondary)] border border-[var(--border)] shadow-[var(--shadow-lg)] flex flex-col z-50 overflow-hidden">
          <div className="p-4 border-b border-[var(--border)] bg-[var(--g4-navy)]">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-[var(--g4-gold)]/20 flex items-center justify-center">
                <Sparkles size={16} className="text-[var(--g4-gold)]" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Assistente de Vendas</h3>
                <p className="text-[10px] text-white/50">Pergunte sobre seu pipeline</p>
              </div>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-[var(--bg-primary)]">
            {messages.length === 0 && (
              <div className="text-center mt-6 space-y-3">
                <div className="w-12 h-12 rounded-full bg-[var(--g4-gold)]/10 flex items-center justify-center mx-auto">
                  <Sparkles size={20} className="text-[var(--g4-gold)]" />
                </div>
                <p className="text-sm text-[var(--text-secondary)]">
                  Pergunte sobre suas oportunidades, performance ou estratégias.
                </p>
                <div className="space-y-2">
                  {[
                    'Quais oportunidades devo priorizar?',
                    'Como está minha performance?',
                    'Quais contas têm mais potencial?',
                  ].map((q) => (
                    <button
                      key={q}
                      onClick={() => setInput(q)}
                      className="block w-full text-left px-3 py-2 rounded-lg text-xs bg-[var(--bg-secondary)] border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--g4-gold)]/40 transition-colors shadow-sm"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] px-3.5 py-2.5 rounded-2xl text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-[var(--g4-navy)] text-white rounded-br-md whitespace-pre-wrap'
                    : 'bg-[var(--bg-secondary)] border border-[var(--border)] text-[var(--text-primary)] rounded-bl-md shadow-sm [&_h4]:font-bold [&_h4]:text-[var(--g4-navy)] [&_h4]:mt-2 [&_h4]:mb-1 [&_ul]:ml-4 [&_ul]:list-disc [&_li]:mb-0.5 [&_p]:mb-1.5 [&_strong]:font-semibold'
                }`}>
                  {msg.role === 'user' ? msg.content : (
                    <div dangerouslySetInnerHTML={{ __html: msg.content }} />
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="px-3.5 py-2.5 rounded-2xl rounded-bl-md bg-[var(--bg-secondary)] border border-[var(--border)] text-sm text-[var(--text-secondary)] shadow-sm">
                  <span className="inline-flex gap-1 text-[var(--g4-gold)]">
                    <span className="animate-bounce">•</span>
                    <span className="animate-bounce" style={{ animationDelay: '0.1s' }}>•</span>
                    <span className="animate-bounce" style={{ animationDelay: '0.2s' }}>•</span>
                  </span>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <form onSubmit={handleSubmit} className="p-3 border-t border-[var(--border)] bg-[var(--bg-secondary)] flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Pergunte..."
              className="flex-1 px-3 py-2 rounded-xl bg-[var(--bg-input)] border border-[var(--border)] text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--g4-gold)] transition-all"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="px-3 py-2 rounded-xl bg-[var(--g4-gold)] hover:bg-[var(--accent-hover)] text-[var(--g4-deep)] transition-colors disabled:opacity-50"
            >
              <Send size={16} strokeWidth={2} />
            </button>
          </form>
        </div>
      )}
    </>
  )
}
