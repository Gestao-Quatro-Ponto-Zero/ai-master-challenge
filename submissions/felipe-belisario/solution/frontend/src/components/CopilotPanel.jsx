import { useState } from 'react'
import axios from 'axios'

export function CopilotPanel({ suggestions, manager }) {
  const [open, setOpen]         = useState(false)
  const [question, setQuestion] = useState('')
  const [answer, setAnswer]     = useState(null)
  const [loading, setLoading]   = useState(false)

  const send = async () => {
    const q = question.trim()
    if (!q || loading) return
    setLoading(true)
    setAnswer(null)
    try {
      const r = await axios.post('/api/copilot', { question: q, manager: manager ?? null })
      setAnswer(r.data.answer)
    } catch {
      setAnswer('Erro ao contatar o Gemini. Tente novamente.')
    }
    setLoading(false)
  }

  return (
    <>
      {/* Botão fixo */}
      <button
        onClick={() => setOpen(true)}
        style={{
          position: 'fixed', bottom: 28, right: 28, zIndex: 900,
          padding: '12px 20px', borderRadius: 50,
          background: '#4F8EF7', border: 'none',
          fontSize: 14, fontWeight: 700, color: '#FFFFFF',
          cursor: 'pointer', boxShadow: '0 4px 20px rgba(79,142,247,0.45)',
          display: 'flex', alignItems: 'center', gap: 8,
          whiteSpace: 'nowrap',
        }}
      >
        ✦ Perguntar ao Gemini
      </button>

      {/* Painel lateral */}
      {open && (
        <div
          style={{
            position: 'fixed', inset: 0, zIndex: 1000,
            display: 'flex', justifyContent: 'flex-end',
          }}
          onClick={() => setOpen(false)}
        >
          <div
            style={{
              width: 400, maxWidth: '95vw', height: '100%',
              background: '#13151F',
              borderLeft: '0.5px solid #2A2D3E',
              display: 'flex', flexDirection: 'column',
              padding: 24, gap: 16,
              overflowY: 'auto',
            }}
            onClick={e => e.stopPropagation()}
          >
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontSize: 15, fontWeight: 800, color: '#E8E9ED' }}>
                ✦ Gemini
              </div>
              <button
                onClick={() => setOpen(false)}
                style={{
                  background: 'none', border: 'none',
                  color: '#8B8FA8', fontSize: 18, cursor: 'pointer',
                  lineHeight: 1,
                }}
              >
                ✕
              </button>
            </div>

            {/* Sugestões contextuais */}
            {suggestions && suggestions.length > 0 && (
              <div>
                <div style={{
                  fontSize: 11, color: '#555870', marginBottom: 8,
                  textTransform: 'uppercase', letterSpacing: '0.06em',
                }}>
                  Perguntas sugeridas
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {suggestions.map((s, i) => (
                    <button
                      key={i}
                      onClick={() => setQuestion(s)}
                      style={{
                        textAlign: 'left', padding: '10px 12px',
                        borderRadius: 8, border: '0.5px solid #2A2D3E',
                        background: '#1C1F2E', color: '#8B8FA8',
                        fontSize: 12, cursor: 'pointer',
                      }}
                      onMouseEnter={e => e.currentTarget.style.borderColor = '#4F8EF7'}
                      onMouseLeave={e => e.currentTarget.style.borderColor = '#2A2D3E'}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Campo de pergunta */}
            <textarea
              value={question}
              onChange={e => setQuestion(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
              placeholder="Pergunte sobre o pipeline..."
              rows={3}
              style={{
                width: '100%', padding: '10px 12px',
                borderRadius: 8, border: '0.5px solid #2A2D3E',
                background: '#1C1F2E', color: '#E8E9ED',
                fontSize: 13, lineHeight: 1.6, resize: 'vertical',
                outline: 'none', boxSizing: 'border-box',
              }}
            />

            <button
              onClick={send}
              disabled={loading || !question.trim()}
              style={{
                padding: '10px 0', borderRadius: 8,
                background: loading || !question.trim() ? '#2A2D3E' : '#4F8EF7',
                border: 'none', fontSize: 13, fontWeight: 700,
                color: loading || !question.trim() ? '#555870' : '#FFFFFF',
                cursor: loading || !question.trim() ? 'default' : 'pointer',
              }}
            >
              {loading ? 'Consultando Gemini...' : 'Enviar'}
            </button>

            {/* Resposta */}
            {answer && (
              <div style={{
                background: '#1C1F2E', borderRadius: 10,
                border: '0.5px solid #2A2D3E', padding: '16px',
                fontSize: 13, color: '#E8E9ED', lineHeight: 1.7,
                whiteSpace: 'pre-wrap',
              }}>
                {answer}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}
