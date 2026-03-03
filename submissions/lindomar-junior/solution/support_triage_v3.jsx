import { useState } from "react";

// ─── DADOS ────────────────────────────────────────────────────────────────────

const EXAMPLES = [
  {
    label: "Conta bloqueada",
    channel: "Chat",
    priority_original: "High",
    text: "I'm unable to access my account. It keeps displaying an 'Invalid Credentials' error, even though I'm entering the correct password. I've tried resetting it twice but the email never arrives. I need to access my billing history for a tax document due tomorrow.",
  },
  {
    label: "Reembolso urgente",
    channel: "Phone",
    priority_original: "High",
    text: "I purchased a GoPro Hero 3 weeks ago and it stopped working after the first use. The lens scratched on its own and the battery drains in 20 minutes. I want a full refund immediately. I've been a customer for 5 years and this is unacceptable. I already sent photos twice with no response.",
  },
  {
    label: "Cobrança duplicada",
    channel: "Email",
    priority_original: "Medium",
    text: "I was charged twice for my subscription this month — once on the 3rd and again on the 17th. My bank statement shows two transactions of $49.99. I didn't make any plan changes. Please confirm what happened and when I'll receive the refund for the duplicate charge.",
  },
  {
    label: "TV com defeito (garantia)",
    channel: "Social media",
    priority_original: "Medium",
    text: "My LG OLED TV started showing a green vertical line on the right side of the screen after only 8 months of use. I haven't dropped it or damaged it. The TV is still under warranty. I need a technician or a replacement unit. This is unacceptable for a $2,000 TV.",
  },
  {
    label: "Configuração de produto",
    channel: "Chat",
    priority_original: "Low",
    text: "Just got my Nest Thermostat and I'm having trouble connecting it to my Wi-Fi. The app keeps showing 'Device not found' even though I followed the instructions step by step. My router is 2.4GHz. Do I need to change anything in my settings?",
  },
];

const CHANNELS = ["Email", "Chat", "Phone", "Social media"];
const PRIORITIES = ["Critical", "High", "Medium", "Low"];

const CH_COLOR = {
  Email: "#4f46e5",
  Chat: "#059669",
  Phone: "#d97706",
  "Social media": "#7c3aed",
};

const PR_COLOR = {
  Critical: { text: "#b91c1c", bg: "#fef2f2", border: "#fecaca" },
  High:     { text: "#c2410c", bg: "#fff7ed", border: "#fed7aa" },
  Medium:   { text: "#92400e", bg: "#fefce8", border: "#fde68a" },
  Low:      { text: "#374151", bg: "#f9fafb", border: "#e5e7eb" },
};

const ROUTING = {
  "Auto-resolve": {
    icon: "⚡", label: "Resolução Automática",
    desc: "IA responde e fecha sem intervenção humana",
    color: "#065f46", bg: "#ecfdf5", border: "#a7f3d0", badge: "#059669",
  },
  "Agent assist": {
    icon: "🤝", label: "Assistência ao Agente",
    desc: "IA gera rascunho — agente revisa antes de enviar",
    color: "#92400e", bg: "#fffbeb", border: "#fde68a", badge: "#d97706",
  },
  "Human required": {
    icon: "👤", label: "Agente Obrigatório",
    desc: "Decisão humana necessária — IA não intervém na resolução",
    color: "#991b1b", bg: "#fff5f5", border: "#fecaca", badge: "#dc2626",
  },
  "Supervisor escalation": {
    icon: "🚨", label: "Escalação para Supervisor",
    desc: "Risco financeiro crítico — aprovação gerencial obrigatória",
    color: "#4c1d95", bg: "#faf5ff", border: "#ddd6fe", badge: "#7c3aed",
  },
};

const RISK = {
  Alto:  { text: "#b91c1c", bg: "#fef2f2", bar: "#ef4444", pct: 88 },
  Médio: { text: "#92400e", bg: "#fefce8", bar: "#f59e0b", pct: 52 },
  Baixo: { text: "#065f46", bg: "#ecfdf5", bar: "#10b981", pct: 18 },
};

// ─── SYSTEM PROMPT ────────────────────────────────────────────────────────────

const SYSTEM = `Você é o motor de triagem de um sistema de suporte ao cliente B2C.
Retorne SOMENTE JSON válido, sem markdown, sem texto adicional.

TIPOS DE TICKET: Technical issue | Billing inquiry | Product inquiry | Refund request | Cancellation request
CATEGORIAS IT: Hardware | Access | HR Support | Storage | Purchase | Administrative rights | Miscellaneous | Internal Project

REGRAS DE ROTEAMENTO (aplique nesta ordem de precedência):
1. Supervisor escalation → Refund >$200 OU chargeback/processo legal mencionado OU cliente VIP com histórico de frustração múltipla OU exposição pública nas redes sociais com nome da marca
2. Human required → Refund request simples | Cancellation request | reclamação com falha anterior do suporte mencionada ("já entrei em contato X vezes", "sem resposta")
3. Agent assist → Technical issue | problema com diagnóstico contextual | garantia/troca de produto | configuração avançada
4. Auto-resolve → Product inquiry FAQ | reset de senha/conta | dúvida de cobrança SEM disputa financeira | configuração básica documentada (passo a passo disponível)

RISCO FINANCEIRO: Alto = reembolso, chargeback, cancelamento de contrato | Médio = cobrança duplicada, upgrade/downgrade | Baixo = FAQ, acesso, configuração

RESPOSTA SUGERIDA: português do Brasil, 2-3 frases MÁXIMO. Direta e empática.
Fórmula: [reconheça o sentimento em 1 frase] + [explique O QUE vai acontecer agora, não o que o cliente precisa fazer] + [prazo ou confirmação].
NUNCA diga "Lamentamos", "Sinto muito", "Prezado cliente". Use "Entendo", "Compreendo", nomes concretos de ação.

PRÓXIMOS PASSOS DO CLIENTE: 2-3 ações simples e concretas que o CLIENTE deve fazer (não o agente).
Exemplos bons: "Aguarde o e-mail de confirmação em até 2h", "Acesse configurações > Rede > 2.4GHz e ative 'modo compatibilidade'"
Exemplos ruins: "Aguarde nosso contato", "Entre em contato novamente"

JSON obrigatório (exatamente estes campos):
{
  "ticket_type": "...",
  "type_confidence": 0.00,
  "it_category": "...",
  "category_confidence": 0.00,
  "priority": "Critical|High|Medium|Low",
  "priority_rationale": "frase curta explicando a prioridade",
  "routing": "Auto-resolve|Agent assist|Human required|Supervisor escalation",
  "financial_risk": "Alto|Médio|Baixo",
  "tags": ["tag1", "tag2"],
  "suggested_response": "...",
  "next_steps": ["passo 1", "passo 2"],
  "justification": "2 frases: por que esse tipo/categoria, e por que esse roteamento."
}`;

// ─── COMPONENTES ──────────────────────────────────────────────────────────────

function Badge({ label, color, bg, border }) {
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", padding: "3px 10px",
      borderRadius: 20, fontSize: 11, fontWeight: 700, letterSpacing: "0.05em",
      textTransform: "uppercase", color, background: bg,
      border: `1px solid ${border || color + "30"}`,
      whiteSpace: "nowrap",
    }}>{label}</span>
  );
}

function ConfBar({ value, color }) {
  const pct = Math.round((value || 0) * 100);
  const c = color || (pct >= 75 ? "#059669" : pct >= 50 ? "#d97706" : "#dc2626");
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div style={{ flex: 1, height: 5, background: "#e5e7eb", borderRadius: 99, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: c, borderRadius: 99, transition: "width 0.9s cubic-bezier(.4,0,.2,1)" }} />
      </div>
      <span style={{ fontSize: 12, fontFamily: "monospace", color: "#6b7280", minWidth: 28 }}>{pct}%</span>
    </div>
  );
}

function RiskBar({ level }) {
  const m = RISK[level] || RISK["Baixo"];
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <div style={{ flex: 1, height: 5, background: "#e5e7eb", borderRadius: 99, overflow: "hidden" }}>
        <div style={{ width: `${m.pct}%`, height: "100%", background: m.bar, borderRadius: 99, transition: "width 0.9s ease" }} />
      </div>
      <Badge label={level} color={m.text} bg={m.bg} />
    </div>
  );
}

function Section({ title, children, accent }) {
  return (
    <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 12, overflow: "hidden" }}>
      <div style={{
        padding: "11px 18px", borderBottom: "1px solid #f3f4f6",
        display: "flex", alignItems: "center", gap: 8,
        background: "#fafafa",
      }}>
        {accent && <div style={{ width: 3, height: 14, borderRadius: 2, background: accent }} />}
        <span style={{ fontSize: 11, fontFamily: "monospace", fontWeight: 600, letterSpacing: "0.07em", textTransform: "uppercase", color: "#6b7280" }}>
          {title}
        </span>
      </div>
      <div style={{ padding: 18 }}>{children}</div>
    </div>
  );
}

function ResultView({ result, originalPriority }) {
  const r = ROUTING[result.routing] || ROUTING["Agent assist"];
  const pr = PR_COLOR[result.priority] || PR_COLOR["Medium"];
  const origPr = PR_COLOR[originalPriority] || PR_COLOR["Medium"];
  const changed = result.priority !== originalPriority;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14, animation: "up 0.4s ease" }}>

      {/* ROUTING HERO */}
      <div style={{
        background: r.bg, border: `2px solid ${r.border}`, borderRadius: 14,
        padding: "20px 22px", display: "flex", alignItems: "center", gap: 16,
      }}>
        <div style={{
          width: 52, height: 52, borderRadius: 12, flexShrink: 0, fontSize: 24,
          background: "#fff", border: `1.5px solid ${r.border}`,
          display: "flex", alignItems: "center", justifyContent: "center",
          boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
        }}>{r.icon}</div>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 800, fontSize: 17, color: r.color, letterSpacing: "-0.02em", marginBottom: 3 }}>{r.label}</div>
          <div style={{ color: r.color, fontSize: 13, opacity: 0.75 }}>{r.desc}</div>
        </div>
        <Badge label={result.routing} color={r.color} bg="#fff" border={r.border} />
      </div>

      {/* CLASSIFICATION */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        {[
          { title: "Tipo de Ticket", val: result.ticket_type, conf: result.type_confidence, color: "#4f46e5" },
          { title: "Categoria IT",   val: result.it_category,  conf: result.category_confidence, color: "#7c3aed" },
        ].map(({ title, val, conf, color }) => (
          <div key={title} style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 12, padding: 16 }}>
            <div style={{ fontSize: 11, fontFamily: "monospace", fontWeight: 600, letterSpacing: "0.07em", textTransform: "uppercase", color: "#9ca3af", marginBottom: 8 }}>{title}</div>
            <div style={{ fontWeight: 700, fontSize: 15, color: "#111827", marginBottom: 10 }}>{val}</div>
            <ConfBar value={conf} color={color} />
          </div>
        ))}
      </div>

      {/* PRIORITY + RISK */}
      <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 12, padding: 18 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>

          <div>
            <div style={{ fontSize: 11, fontFamily: "monospace", fontWeight: 600, letterSpacing: "0.07em", textTransform: "uppercase", color: "#9ca3af", marginBottom: 10 }}>Prioridade Recalibrada</div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
              {changed && <>
                <span style={{ background: origPr.bg, color: origPr.text, padding: "3px 10px", borderRadius: 20, fontSize: 11, fontWeight: 700, textDecoration: "line-through", opacity: 0.55, border: `1px solid ${origPr.border}` }}>{originalPriority}</span>
                <span style={{ color: "#d1d5db", fontSize: 13 }}>→</span>
              </>}
              <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
                <div style={{ width: 10, height: 10, borderRadius: "50%", background: PR_COLOR[result.priority]?.text || "#6b7280", boxShadow: `0 0 0 3px ${PR_COLOR[result.priority]?.bg || "#f3f4f6"}` }} />
                <span style={{ fontWeight: 800, fontSize: 16, color: pr.text }}>{result.priority}</span>
              </div>
              {changed && <Badge label="↑ Recalibrado" color={pr.text} bg={pr.bg} border={pr.border} />}
            </div>
            {result.priority_rationale && (
              <div style={{ fontSize: 12, color: "#9ca3af", fontStyle: "italic" }}>{result.priority_rationale}</div>
            )}
          </div>

          <div>
            <div style={{ fontSize: 11, fontFamily: "monospace", fontWeight: 600, letterSpacing: "0.07em", textTransform: "uppercase", color: "#9ca3af", marginBottom: 10 }}>Risco Financeiro</div>
            <RiskBar level={result.financial_risk || "Baixo"} />
          </div>
        </div>

        {result.tags?.length > 0 && (
          <div style={{ marginTop: 14, paddingTop: 14, borderTop: "1px solid #f3f4f6", display: "flex", gap: 6, flexWrap: "wrap" }}>
            {result.tags.map(t => <Badge key={t} label={t} color="#6b7280" bg="#f9fafb" border="#e5e7eb" />)}
          </div>
        )}
      </div>

      {/* SUGGESTED RESPONSE */}
      <Section title="Resposta Sugerida" accent={r.badge}>
        <div style={{
          background: r.bg, borderLeft: `3px solid ${r.badge}`,
          borderRadius: "0 8px 8px 0", padding: "14px 16px", marginBottom: 12,
          color: "#1f2937", fontSize: 14, lineHeight: 1.75,
          fontFamily: "'Lora', Georgia, serif",
        }}>
          {result.suggested_response}
        </div>
        <Badge
          label={
            result.routing === "Auto-resolve"          ? "✓ Pode enviar automaticamente" :
            result.routing === "Agent assist"          ? "⏸ Aguarda revisão do agente" :
            result.routing === "Supervisor escalation" ? "🚨 Aguarda aprovação gerencial" :
                                                         "✏ Edição obrigatória pelo agente"
          }
          color={r.color} bg={r.bg} border={r.border}
        />
      </Section>

      {/* NEXT STEPS (client-facing) */}
      {result.next_steps?.length > 0 && (
        <Section title="Próximos Passos para o Cliente" accent="#4f46e5">
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {result.next_steps.map((step, i) => (
              <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
                <div style={{
                  width: 26, height: 26, borderRadius: "50%", flexShrink: 0,
                  background: "#eff6ff", border: "1.5px solid #bfdbfe",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 12, fontWeight: 800, color: "#3b82f6",
                }}>{i + 1}</div>
                <span style={{ color: "#374151", fontSize: 13.5, lineHeight: 1.65, paddingTop: 3 }}>{step}</span>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* JUSTIFICATION */}
      <div style={{ background: "#f9fafb", border: "1px solid #f3f4f6", borderRadius: 12, padding: 16 }}>
        <div style={{ fontSize: 11, fontFamily: "monospace", fontWeight: 600, letterSpacing: "0.07em", textTransform: "uppercase", color: "#9ca3af", marginBottom: 8 }}>Raciocínio da IA</div>
        <p style={{ color: "#6b7280", fontSize: 13, lineHeight: 1.65, margin: 0 }}>{result.justification}</p>
      </div>

    </div>
  );
}

// ─── APP ──────────────────────────────────────────────────────────────────────

export default function App() {
  const [text, setText]           = useState("");
  const [channel, setChannel]     = useState("Email");
  const [priority, setPriority]   = useState("Medium");
  const [loading, setLoading]     = useState(false);
  const [result, setResult]       = useState(null);
  const [error, setError]         = useState(null);

  const loadExample = (ex) => {
    setText(ex.text);
    setChannel(ex.channel);
    setPriority(ex.priority_original);
    setResult(null);
    setError(null);
  };

  const analyze = async () => {
    if (!text.trim() || loading) return;
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const res = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1024,
          system: SYSTEM,
          messages: [{ role: "user", content: `Canal: ${channel}\nPrioridade declarada: ${priority}\n\nTicket:\n${text}` }],
        }),
      });
      if (!res.ok) throw new Error(`API ${res.status}`);
      const data = await res.json();
      const raw  = data.content?.[0]?.text || "";
      setResult(JSON.parse(raw.replace(/```json|```/g, "").trim()));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "#f1f5f9", fontFamily: "'DM Sans','Segoe UI',sans-serif", color: "#111827" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,400;0,500;0,600;0,700;0,800&family=DM+Mono:wght@400;500&family=Lora:ital,wght@0,400;1,400&display=swap');
        *{box-sizing:border-box;margin:0;padding:0;}
        button{cursor:pointer;transition:all .15s;}
        button:hover{opacity:.87;}
        textarea:focus{outline:none;}
        @keyframes spin{to{transform:rotate(360deg)}}
        @keyframes blink{0%,100%{opacity:1}50%{opacity:.35}}
        @keyframes up{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
      `}</style>

      {/* ── HEADER ── */}
      <header style={{
        background: "#fff", borderBottom: "1px solid #e5e7eb",
        padding: "13px 40px", display: "flex", alignItems: "center", justifyContent: "space-between",
        position: "sticky", top: 0, zIndex: 30, boxShadow: "0 1px 4px rgba(0,0,0,.05)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{
            width: 38, height: 38, borderRadius: 10,
            background: "linear-gradient(135deg,#6366f1,#8b5cf6)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 18, boxShadow: "0 2px 10px #6366f125",
          }}>⚡</div>
          <div>
            <div style={{ fontWeight: 800, fontSize: 15.5, letterSpacing: "-0.025em" }}>Support Triage AI</div>
            <div style={{ color: "#9ca3af", fontSize: 11, fontFamily: "monospace", letterSpacing: ".05em" }}>Challenge 002 · Redesign de Suporte · Protótipo v3</div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          {Object.entries(ROUTING).map(([k, v]) => (
            <div key={k} style={{
              display: "flex", alignItems: "center", gap: 5,
              background: v.bg, border: `1px solid ${v.border}`,
              borderRadius: 20, padding: "4px 11px", fontSize: 11, color: v.color, fontWeight: 700,
            }}>
              <span>{v.icon}</span>
              <span style={{ fontFamily: "monospace" }}>{k}</span>
            </div>
          ))}
        </div>
      </header>

      {/* ── MAIN — coluna única ── */}
      <main style={{ maxWidth: 780, margin: "0 auto", padding: "36px 24px 80px" }}>

        {/* STEP 1 — examples */}
        <div style={{ marginBottom: 10, display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 24, height: 24, borderRadius: "50%", background: "#6366f1", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 800, flexShrink: 0 }}>1</div>
          <span style={{ fontWeight: 700, fontSize: 14, color: "#374151" }}>Selecione um ticket de exemplo ou escreva abaixo</span>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(5,1fr)", gap: 8, marginBottom: 28 }}>
          {EXAMPLES.map(ex => {
            const active = text === ex.text;
            return (
              <button key={ex.label} onClick={() => loadExample(ex)} style={{
                background: active ? "#eff6ff" : "#fff",
                border: `1.5px solid ${active ? "#93c5fd" : "#e5e7eb"}`,
                borderRadius: 10, padding: "12px 10px",
                display: "flex", flexDirection: "column", alignItems: "center", gap: 8,
              }}>
                <span style={{ fontSize: 11, fontWeight: active ? 700 : 500, color: active ? "#1d4ed8" : "#374151", textAlign: "center", lineHeight: 1.4 }}>{ex.label}</span>
                <div style={{ display: "flex", flexDirection: "column", gap: 4, width: "100%" }}>
                  <Badge label={ex.channel} color={CH_COLOR[ex.channel]} bg={CH_COLOR[ex.channel] + "12"} border={CH_COLOR[ex.channel] + "25"} />
                  <Badge label={ex.priority_original} color={PR_COLOR[ex.priority_original].text} bg={PR_COLOR[ex.priority_original].bg} border={PR_COLOR[ex.priority_original].border} />
                </div>
              </button>
            );
          })}
        </div>

        {/* STEP 2 — input */}
        <div style={{ marginBottom: 10, display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 24, height: 24, borderRadius: "50%", background: "#6366f1", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 800, flexShrink: 0 }}>2</div>
          <span style={{ fontWeight: 700, fontSize: 14, color: "#374151" }}>Configure canal, prioridade e texto</span>
        </div>

        <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 14, padding: 20, marginBottom: 28 }}>
          {/* channel + priority */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 18 }}>
            <div>
              <div style={{ fontSize: 11, fontFamily: "monospace", fontWeight: 600, letterSpacing: "0.07em", textTransform: "uppercase", color: "#9ca3af", marginBottom: 8 }}>Canal de Entrada</div>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                {CHANNELS.map(ch => (
                  <button key={ch} onClick={() => setChannel(ch)} style={{
                    padding: "6px 14px", borderRadius: 20,
                    border: `1.5px solid ${channel === ch ? CH_COLOR[ch] : "#e5e7eb"}`,
                    background: channel === ch ? CH_COLOR[ch] + "10" : "transparent",
                    color: channel === ch ? CH_COLOR[ch] : "#6b7280",
                    fontSize: 12, fontWeight: channel === ch ? 700 : 400,
                  }}>{ch}</button>
                ))}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 11, fontFamily: "monospace", fontWeight: 600, letterSpacing: "0.07em", textTransform: "uppercase", color: "#9ca3af", marginBottom: 8 }}>Prioridade Declarada pelo Cliente</div>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                {PRIORITIES.map(p => (
                  <button key={p} onClick={() => setPriority(p)} style={{
                    padding: "6px 14px", borderRadius: 20,
                    border: `1.5px solid ${priority === p ? PR_COLOR[p].text : "#e5e7eb"}`,
                    background: priority === p ? PR_COLOR[p].bg : "transparent",
                    color: priority === p ? PR_COLOR[p].text : "#6b7280",
                    fontSize: 12, fontWeight: priority === p ? 700 : 400,
                  }}>{p}</button>
                ))}
              </div>
            </div>
          </div>

          <textarea
            value={text}
            onChange={e => { setText(e.target.value); setResult(null); }}
            placeholder="Cole ou escreva o texto do ticket aqui..."
            style={{
              width: "100%", minHeight: 120, background: "#f9fafb",
              border: "1px solid #e5e7eb", borderRadius: 8, padding: "12px 14px",
              color: "#111827", fontSize: 13.5, lineHeight: 1.7, resize: "vertical",
              fontFamily: "'DM Sans',sans-serif",
            }}
          />
        </div>

        {/* STEP 3 — analyze */}
        <div style={{ marginBottom: 10, display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 24, height: 24, borderRadius: "50%", background: "#6366f1", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 800, flexShrink: 0 }}>3</div>
          <span style={{ fontWeight: 700, fontSize: 14, color: "#374151" }}>Analisar</span>
        </div>

        <button
          onClick={analyze}
          disabled={loading || !text.trim()}
          style={{
            width: "100%", padding: "15px 24px", borderRadius: 12, border: "none", marginBottom: 28,
            background: loading || !text.trim()
              ? "#e5e7eb"
              : "linear-gradient(135deg,#6366f1 0%,#8b5cf6 100%)",
            color: loading || !text.trim() ? "#9ca3af" : "#fff",
            fontSize: 15, fontWeight: 800, letterSpacing: "-0.01em",
            display: "flex", alignItems: "center", justifyContent: "center", gap: 10,
            boxShadow: loading || !text.trim() ? "none" : "0 4px 16px #6366f128",
          }}
        >
          {loading ? (
            <>
              <div style={{ width: 17, height: 17, border: "2.5px solid #c4b5fd", borderTopColor: "#fff", borderRadius: "50%", animation: "spin .7s linear infinite" }} />
              <span style={{ animation: "blink 1.2s infinite" }}>Classificando ticket...</span>
            </>
          ) : "⚡ Analisar Ticket"}
        </button>

        {error && (
          <div style={{ background: "#fff5f5", border: "1px solid #fecaca", borderRadius: 10, padding: 14, color: "#b91c1c", fontSize: 13, fontFamily: "monospace", marginBottom: 24 }}>
            {error}
          </div>
        )}

        {/* RESULT */}
        {result && (
          <>
            <div style={{ borderTop: "1px solid #e5e7eb", paddingTop: 28, marginBottom: 20, display: "flex", alignItems: "center", gap: 10 }}>
              <div style={{ width: 24, height: 24, borderRadius: "50%", background: "#059669", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 800, flexShrink: 0 }}>✓</div>
              <span style={{ fontWeight: 700, fontSize: 14, color: "#374151" }}>Resultado da triagem</span>
            </div>
            <ResultView result={result} originalPriority={priority} />
          </>
        )}
      </main>
    </div>
  );
}
