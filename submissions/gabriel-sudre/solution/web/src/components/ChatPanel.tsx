import { useState, useRef, useEffect } from 'react'
import { api } from '../lib/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export function ChatPanel() {
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
    <div className="flex flex-col h-[600px] rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
      <div className="p-4 border-b border-[var(--border)]">
        <h3 className="font-semibold">Chat IA</h3>
        <p className="text-xs text-[var(--text-secondary)]">Pergunte sobre seus deals e pipeline</p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <p className="text-center text-[var(--text-secondary)] text-sm mt-8">
            Pergunte sobre seus deals, performance ou estratégias de vendas.
          </p>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm whitespace-pre-wrap ${
              msg.role === 'user'
                ? 'bg-[var(--accent)] text-white rounded-br-md'
                : 'bg-[var(--bg-primary)] border border-[var(--border)] rounded-bl-md'
            }`}>
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="px-4 py-3 rounded-2xl rounded-bl-md bg-[var(--bg-primary)] border border-[var(--border)] text-sm text-[var(--text-secondary)]">
              Pensando...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="p-4 border-t border-[var(--border)] flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Pergunte sobre seus deals..."
          className="flex-1 px-4 py-2 rounded-lg bg-[var(--bg-primary)] border border-[var(--border)] text-sm text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] focus:outline-none focus:border-[var(--accent)]"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="px-4 py-2 rounded-lg bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white text-sm font-medium transition-colors disabled:opacity-50"
        >
          Enviar
        </button>
      </form>
    </div>
  )
}
