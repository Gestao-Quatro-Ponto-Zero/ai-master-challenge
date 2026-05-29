"use client";

import Image from "next/image";
import { useRef, useMemo, useState, useEffect } from "react";

import { VoiceRecorder } from "@/components/VoiceRecorder";
import type { RagSource, TicketCategory, TicketPriority } from "@/lib/types";

/* ── Types ──────────────────────────────────────────────────────────────── */
type RagResponse   = { suggestion: string; confidence: number; sources: RagSource[] };
type ClassifyResp  = { category: TicketCategory; priority: TicketPriority; confidence: number };
type KbArticle     = { id: number | string; description: string; resolution: string; category: string };
type QuickCategory = { icon: string; title: string; desc: string; articles: Omit<KbArticle, "id">[] };
type VoiceStatus   = "idle" | "recording" | "transcribing";
type TicketForm    = { description: string; nome: string; email: string };
type CatModal      = { icon: string; title: string; articles: KbArticle[]; loading: boolean } | null;

/* ── Quick categories ─────────────────────────────────────────────────────
 * Fonte de conteúdo (curadoria): G4_Educação_Base_de_Conhecimento (1).pdf
 * Seções utilizadas: 7.1, 7.2, 7.3, 7.4, 2.4 e 3.x
 */
const QUICK_CATEGORIES: QuickCategory[] = [
  {
    icon: "💳",
    title: "Pagamento e Faturamento",
    desc: "Confirmação de compra, pagamento recusado, alteração de método e nota fiscal.",
    articles: [
      {
        category: "Suporte Operacional",
        description: "Paguei e não recebi confirmação ou acesso.",
        resolution:
          "Verifique spam/lixo eletrônico e confirme se o e-mail da compra está correto. Boleto pode levar até 3 dias úteis. Em PIX/cartão, se não liberar acesso, contate o suporte com e-mail de compra e comprovante.",
      },
      {
        category: "Suporte Operacional",
        description: "Pagamento recusado, mas houve débito no cartão.",
        resolution:
          "Geralmente é reserva de limite da operadora. O estorno costuma ocorrer em alguns dias úteis. Se não aparecer na próxima fatura, envie comprovante do débito ao suporte.",
      },
      {
        category: "Suporte Operacional",
        description: "Não recebi a nota fiscal da compra.",
        resolution:
          "A nota fiscal é enviada automaticamente ao e-mail cadastrado alguns dias após a confirmação do pagamento. Se não localizar, solicite segunda via com CPF/CNPJ da compra.",
      },
    ],
  },
  {
    icon: "🔑",
    title: "Acesso à Plataforma",
    desc: "Login, senha, materiais com erro e dúvidas sobre expiração de acesso.",
    articles: [
      {
        category: "Suporte Operacional",
        description: "Comprei o curso, mas não consigo entrar na plataforma.",
        resolution:
          "Use o mesmo e-mail da compra e tente redefinir a senha em 'Esqueci minha senha'. Se persistir, contate o suporte para validação da conta e liberação.",
      },
      {
        category: "Suporte Operacional",
        description: "Vídeo não carrega ou PDF do curso está com erro.",
        resolution:
          "Limpe cache do navegador, teste aba anônima e outro navegador. Se continuar, envie ao suporte o nome do curso, módulo e aula para correção técnica.",
      },
      {
        category: "Suporte Operacional",
        description: "Meu acesso expirou e não terminei o curso.",
        resolution:
          "O prazo depende do programa (ex.: 6 meses em alguns presenciais, vitalício no G4 Pass). Para extensão, consulte a política do curso e peça avaliação do suporte.",
      },
    ],
  },
  {
    icon: "↩️",
    title: "Cancelamento e Reembolso",
    desc: "Direito de arrependimento em 7 dias, fluxo de cancelamento e prazos de estorno.",
    articles: [
      {
        category: "Suporte Operacional",
        description: "Quero solicitar reembolso de curso online.",
        resolution:
          "O direito de arrependimento é de até 7 dias após a compra. Solicite ao suporte informando e-mail de compra e motivo; o estorno segue o meio de pagamento original.",
      },
      {
        category: "Suporte Operacional",
        description: "Como cancelar a assinatura do G4 Pass?",
        resolution:
          "Cancele a renovação automática na área do aluno, em 'Assinaturas'. O cancelamento evita cobranças futuras e mantém o acesso até o fim do período já pago.",
      },
      {
        category: "Suporte Operacional",
        description: "Posso transferir ingresso presencial ou remarcar turma?",
        resolution:
          "Geralmente é possível com antecedência mínima, conforme contrato do programa. Fale com o suporte para validar regras e possíveis taxas.",
      },
    ],
  },
  {
    icon: "🎓",
    title: "Certificados e Dúvidas Gerais",
    desc: "Certificado não emitido, nome incorreto e condições para empresas.",
    articles: [
      {
        category: "Suporte Operacional",
        description: "Concluí o curso e o certificado não apareceu.",
        resolution:
          "Confirme 100% de progresso (aulas e módulos marcados). Se não gerar automaticamente na área do aluno, solicite emissão manual ao suporte.",
      },
      {
        category: "Suporte Operacional",
        description: "Nome incorreto no certificado.",
        resolution:
          "Ajuste o nome em 'Minha Conta' e tente emitir novamente. Se ainda sair incorreto, o suporte realiza a correção.",
      },
      {
        category: "Suporte Operacional",
        description: "Existe condição especial para empresas e compras em grupo?",
        resolution:
          "Sim. O G4 possui condições corporativas para treinar equipes. Solicite atendimento especializado ao suporte/comercial.",
      },
    ],
  },
  {
    icon: "📚",
    title: "G4 Pass",
    desc: "Resumo da assinatura, conteúdo incluído e acesso.",
    articles: [
      {
        category: "Produto",
        description: "O que está incluso no G4 Pass?",
        resolution:
          "Acesso vitalício aos cursos online (atuais e futuros), com mais de 100 cursos, mais de 400 horas de conteúdo e mais de 100 ferramentas.",
      },
      {
        category: "Produto",
        description: "Quais trilhas de conteúdo fazem parte do Pass?",
        resolution:
          "Inclui trilhas de IA, Marketing, Vendas e Gestão, com cursos práticos para aplicação imediata em negócio e operação.",
      },
      {
        category: "Produto",
        description: "Como gerenciar minha assinatura do G4 Pass?",
        resolution:
          "Pela área do aluno, em 'Minha Conta' ou 'Assinaturas', você atualiza método de pagamento e gerencia renovação.",
      },
    ],
  },
  {
    icon: "🛠️",
    title: "G4 Tools",
    desc: "Marketplace com soluções de CRM, ERP, Marketing, Vendas e Gestão.",
    articles: [
      {
        category: "Produto",
        description: "O que é o G4 Tools?",
        resolution:
          "É o marketplace de serviços e tecnologia do G4, com curadoria para conectar empresas às melhores soluções do mercado.",
      },
      {
        category: "Produto",
        description: "Quais áreas de solução o G4 Tools cobre?",
        resolution:
          "CRM, ERP, Marketing, Vendas e Gestão, com foco em eficiência operacional e crescimento sustentável.",
      },
      {
        category: "Produto",
        description: "Quais os diferenciais do G4 Tools?",
        resolution:
          "Curadoria especializada, negociações exclusivas com parceiros e foco em resultados práticos para PMEs e empresas em escala.",
      },
    ],
  },
];

/* ── Shared input style ─────────────────────────────────────────────────── */
const inputCss: React.CSSProperties = {
  width: "100%", padding: "0.625rem 0.875rem", borderRadius: 10,
  border: "1.5px solid #e2e8f0", fontSize: "0.875rem", color: "#0f172a",
  background: "#f8fafc", boxSizing: "border-box", outline: "none", fontFamily: "inherit",
};

/* ── Article expandable card ─────────────────────────────────────────────  */
function ArticleCard({ article }: { article: KbArticle }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="cs-source-card">
      <button type="button" onClick={() => setOpen((p) => !p)}
        style={{ width: "100%", textAlign: "left", background: "none", border: "none", cursor: "pointer", padding: 0 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
          <p style={{ margin: 0, fontSize: "0.875rem", fontWeight: 600, color: "#0f172a", lineHeight: 1.4 }}>
            {article.description.length > 110 ? article.description.slice(0, 110) + "…" : article.description}
          </p>
          <span style={{ flexShrink: 0, fontSize: "0.75rem", color: "#94a3b8", marginTop: 2 }}>{open ? "▲" : "▼"}</span>
        </div>
      </button>
      {open && (
        <p style={{ margin: "0.625rem 0 0", fontSize: "0.8125rem", color: "#475569", lineHeight: 1.65 }}>
          {article.resolution}
        </p>
      )}
    </div>
  );
}

/* ── Category modal ──────────────────────────────────────────────────────── */
function CategoryModal({ modal, onClose, onNeedHelp }: {
  modal: NonNullable<CatModal>;
  onClose: () => void;
  onNeedHelp: () => void;
}) {
  return (
    <div className="cs-modal-overlay" onClick={onClose}>
      <div className="cs-modal-card" style={{ padding: "1.75rem" }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "1.25rem" }}>
          <div>
            <span style={{ fontSize: "2rem" }}>{modal.icon}</span>
            <h2 style={{ margin: "0.4rem 0 0.25rem", fontSize: "1.25rem", fontWeight: 800, color: "#0f172a" }}>{modal.title}</h2>
          </div>
          <button onClick={onClose} style={{ background: "none", border: "none", fontSize: "1.25rem", color: "#94a3b8", cursor: "pointer", padding: "4px 8px", lineHeight: 1 }}>✕</button>
        </div>

        {modal.loading ? (
          <div style={{ padding: "2rem", textAlign: "center" }}>
            <span style={{ display: "inline-block", width: 24, height: 24, borderRadius: "50%", border: "2px solid #B48E5A", borderTopColor: "transparent", animation: "spin 0.7s linear infinite" }} />
            <p style={{ margin: "0.75rem 0 0", fontSize: "0.875rem", color: "#64748b" }}>Buscando artigos…</p>
          </div>
        ) : modal.articles.length > 0 ? (
          <div style={{ marginBottom: "1.25rem" }}>
            <p style={{ margin: "0 0 0.75rem", fontSize: "0.6875rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "#94a3b8" }}>Artigos relacionados</p>
            {modal.articles.map((a, i) => <ArticleCard key={i} article={a} />)}
          </div>
        ) : (
          <p style={{ fontSize: "0.875rem", color: "#64748b", marginBottom: "1.25rem" }}>
            Nenhum artigo encontrado. Nossa equipe pode ajudar!
          </p>
        )}

        <div style={{ display: "flex", gap: "0.75rem" }}>
          <button onClick={onClose} style={{ flex: 1, padding: "0.75rem", borderRadius: 12, fontWeight: 700, fontSize: "0.9rem", border: "none", background: "#10b981", color: "#fff", cursor: "pointer" }}>
            ✓ Entendi
          </button>
          <button onClick={onNeedHelp} style={{ flex: 1, padding: "0.75rem", borderRadius: 12, fontWeight: 700, fontSize: "0.9rem", border: "none", background: "#021E35", color: "#fff", cursor: "pointer" }}>
            Preciso de ajuda
          </button>
        </div>
      </div>
    </div>
  );
}

/* ── RAG modal ───────────────────────────────────────────────────────────── */
function RagModal({ rag, isLoading, onClose, onDeflect, onOpenTicket, defaultDesc }: {
  rag: RagResponse;
  isLoading: boolean;
  onClose: () => void;
  onDeflect: () => Promise<void>;
  onOpenTicket: (form: TicketForm) => Promise<void>;
  defaultDesc: string;
}) {
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<TicketForm>({ description: defaultDesc, nome: "", email: "" });
  const [submitting, setSubmitting] = useState(false);
  const [deflecting, setDeflecting] = useState(false);
  const [err, setErr] = useState("");

  const confPct   = Math.round(rag.confidence * 100);
  const confLabel = rag.confidence >= 0.75 ? "Alta" : rag.confidence >= 0.45 ? "Média" : "Baixa";
  const confColor = rag.confidence >= 0.65 ? "#10b981" : rag.confidence >= 0.4 ? "#f59e0b" : "#94a3b8";

  async function doDeflect() {
    setDeflecting(true);
    try { await onDeflect(); } finally { setDeflecting(false); }
  }

  async function doTicket(e: React.FormEvent) {
    e.preventDefault();
    if (!form.description.trim()) { setErr("Descreva o problema para continuar."); return; }
    setSubmitting(true); setErr("");
    try { await onOpenTicket(form); } catch (ex) { setErr(ex instanceof Error ? ex.message : "Erro ao abrir ticket"); }
    finally { setSubmitting(false); }
  }

  return (
    <div className="cs-modal-overlay" onClick={onClose}>
      <div className="cs-modal-card" onClick={(e) => e.stopPropagation()}>

        {/* Header */}
        <div style={{ padding: "1.5rem 1.75rem 1rem", borderBottom: "1px solid #f1f5f9" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <p style={{ margin: 0, fontSize: "0.6875rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.14em", color: "#B48E5A" }}>Sugestão da IA</p>
              <h2 style={{ margin: "0.3rem 0 0", fontSize: "1.125rem", fontWeight: 800, color: "#0f172a" }}>Encontramos algo que pode ajudar</h2>
            </div>
            <button onClick={onClose} style={{ background: "none", border: "none", fontSize: "1.25rem", color: "#94a3b8", cursor: "pointer", padding: "4px 8px", lineHeight: 1 }}>✕</button>
          </div>
          <div style={{ marginTop: "0.625rem", display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{ width: 8, height: 8, borderRadius: "50%", background: confColor, display: "inline-block" }} />
            <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Confiança {confLabel} — {confPct}%</span>
          </div>
        </div>

        {/* Suggestion */}
        <div style={{ padding: "1rem 1.75rem" }}>
          <p style={{ margin: 0, fontSize: "0.9375rem", lineHeight: 1.7, color: "#334155" }}>{rag.suggestion}</p>
        </div>

        {/* Sources */}
        {rag.sources.length > 0 && (
          <div style={{ padding: "0 1.75rem 1rem" }}>
            <p style={{ margin: "0 0 0.625rem", fontSize: "0.6875rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "#94a3b8" }}>Artigos relacionados</p>
            {rag.sources.map((s, i) => (
              <ArticleCard key={i} article={{ id: s.id, description: s.description, resolution: s.resolution, category: s.category }} />
            ))}
          </div>
        )}

        {/* Action buttons OR ticket form */}
        {!showForm ? (
          <div style={{ padding: "0 1.75rem 1.75rem", display: "flex", flexDirection: "column", gap: "0.625rem" }}>
            <button type="button" onClick={doDeflect} disabled={deflecting || isLoading}
              style={{ padding: "0.9rem", borderRadius: 14, fontWeight: 700, fontSize: "1rem", border: "none", background: "#10b981", color: "#fff", cursor: deflecting ? "not-allowed" : "pointer", opacity: deflecting ? 0.7 : 1 }}>
              {deflecting ? "Registrando…" : "✓ Dúvida esclarecida"}
            </button>
            <button type="button" onClick={() => setShowForm(true)}
              style={{ padding: "0.9rem", borderRadius: 14, fontWeight: 700, fontSize: "1rem", border: "none", background: "#021E35", color: "#fff", cursor: "pointer" }}>
              Encaminhar para abertura de ticket →
            </button>
          </div>
        ) : (
          <form onSubmit={doTicket} style={{ padding: "0 1.75rem 1.75rem", display: "flex", flexDirection: "column", gap: "0.875rem" }}>
            <div style={{ borderTop: "1px solid #f1f5f9", paddingTop: "1rem" }}>
              <p style={{ margin: "0 0 0.875rem", fontSize: "1rem", fontWeight: 800, color: "#0f172a" }}>Abrir ticket de suporte</p>
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "#64748b", marginBottom: 4 }}>Descrição do problema *</label>
              <textarea rows={4} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
                placeholder="Descreva o problema com o máximo de detalhes…" style={{ ...inputCss, resize: "vertical" }} required />
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
              <div>
                <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "#64748b", marginBottom: 4 }}>Seu nome</label>
                <input type="text" value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} placeholder="Nome completo" style={inputCss} />
              </div>
              <div>
                <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "#64748b", marginBottom: 4 }}>E-mail de contato</label>
                <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="seu@email.com" style={inputCss} />
              </div>
            </div>
            {err && <p style={{ margin: 0, fontSize: "0.8125rem", color: "#ef4444" }}>{err}</p>}
            <div style={{ display: "flex", gap: "0.625rem" }}>
              <button type="button" onClick={() => setShowForm(false)}
                style={{ padding: "0.75rem 1.25rem", borderRadius: 12, fontSize: "0.875rem", fontWeight: 600, border: "1.5px solid #e2e8f0", background: "#fff", color: "#475569", cursor: "pointer" }}>
                ← Voltar
              </button>
              <button type="submit" disabled={submitting}
                style={{ flex: 1, padding: "0.75rem", borderRadius: 12, fontWeight: 700, fontSize: "0.9375rem", border: "none", background: "#1d4ed8", color: "#fff", cursor: submitting ? "not-allowed" : "pointer", opacity: submitting ? 0.7 : 1 }}>
                {submitting ? "Enviando…" : "Confirmar abertura de ticket"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

/* ── Page ────────────────────────────────────────────────────────────────── */
export default function CustomerNewPage() {
  const [textInput, setTextInput]         = useState("");
  const [audioTranscript, setAudioTranscript] = useState("");
  const [audioBase64, setAudioBase64]     = useState<string | undefined>();
  const [voiceStatus, setVoiceStatus]     = useState<VoiceStatus>("idle");

  const [rag, setRag]                     = useState<RagResponse | null>(null);
  const [showRagModal, setShowRagModal]   = useState(false);
  const [ragDefaultDesc, setRagDefaultDesc] = useState("");

  const [catModal, setCatModal]           = useState<CatModal>(null);

  const [isLoading, setIsLoading]         = useState(false);
  const [feedback, setFeedback]           = useState("");

  const textareaRef  = useRef<HTMLTextAreaElement>(null);
  const mrRef        = useRef<MediaRecorder | null>(null);
  const streamRef    = useRef<MediaStream | null>(null);
  const chunksRef    = useRef<Blob[]>([]);

  const source    = audioTranscript ? "audio" : "text";
  const finalText = useMemo(() => textInput.trim() || audioTranscript.trim(), [textInput, audioTranscript]);

  // Auto-resize textarea height as content grows
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }, [textInput]);

  /* ── RAG search ─────────────────────────────────────────────────────── */
  async function handleGenerateSuggestion(textOverride?: string) {
    const text = textOverride ?? finalText;
    if (!text) { setFeedback("Escreva ou grave seu problema antes de continuar."); return; }
    setIsLoading(true); setFeedback("");
    try {
      const res = await fetch("/api/rag-search", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      const payload = (await res.json()) as RagResponse & { error?: string };
      if (!res.ok) throw new Error(payload.error ?? "Erro ao buscar sugestão");
      setRag(payload);
      setRagDefaultDesc(text);
      setShowRagModal(true);
    } catch (err) {
      setFeedback(err instanceof Error ? err.message : "Erro inesperado");
    } finally {
      setIsLoading(false);
    }
  }
  /* ── Voice recording (inlined) ───────────────────────────────────────── */
  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mr = new MediaRecorder(stream);
      mrRef.current = mr;
      chunksRef.current = [];

      mr.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };

      mr.onstop = async () => {
        setVoiceStatus("transcribing");
        stream.getTracks().forEach((t) => t.stop());
        const audioBlob = new Blob(chunksRef.current, { type: "audio/webm" });
        const base64 = await new Promise<string>((res, rej) => {
          const reader = new FileReader();
          reader.onloadend = () => typeof reader.result === "string" ? res(reader.result) : rej(new Error());
          reader.onerror = () => rej(new Error());
          reader.readAsDataURL(audioBlob);
        });
        try {
          const resp = await fetch("/api/transcribe", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ audio_base64: base64 }),
          });
          const payload = (await resp.json()) as { text?: string; error?: string };
          if (!resp.ok || !payload.text) {
            setFeedback(payload.error ?? "Falha ao transcrever áudio");
          } else {
            setAudioTranscript(payload.text);
            setTextInput(payload.text);
            setAudioBase64(base64);
            void handleGenerateSuggestion(payload.text);
          }
        } catch {
          setFeedback("Erro de rede ao transcrever");
        } finally {
          setVoiceStatus("idle");
        }
      };

      mr.start();
      setVoiceStatus("recording");
    } catch {
      setFeedback("Permissão de microfone negada ou indisponível");
      setVoiceStatus("idle");
    }
  }

  function handleMicClick() {
    if (voiceStatus === "idle") void startRecording();
  }

  function stopRecording() {
    mrRef.current?.stop();
  }

  function cancelRecording() {
    if (mrRef.current) {
      mrRef.current.onstop = null;
      mrRef.current.stop();
    }
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setVoiceStatus("idle");
  }

  /* ── Deflection ──────────────────────────────────────────────────────── */
  async function handleDeflect() {
    if (!rag) return;
    await fetch("/api/deflection", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ raw_text: finalText, top_matches: rag.sources }),
    });
    setFeedback("Ótimo! Sua dúvida foi marcada como resolvida.");
    resetFlow();
  }

  /* ── Create ticket ───────────────────────────────────────────────────── */
  async function handleCreateTicket(form: TicketForm) {
    const text = form.description || finalText;
    setIsLoading(true);
    try {
      const cr = await fetch("/api/classify", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      const classify = (await cr.json()) as ClassifyResp & { error?: string };
      if (!cr.ok) throw new Error(classify.error ?? "Falha ao classificar");

      const tr = await fetch("/api/tickets", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source, raw_text: text,
          audio_path: source === "audio" ? "ticket-audio/demo.webm" : undefined,
          audio_base64: source === "audio" ? audioBase64 : undefined,
          category: classify.category, priority: classify.priority,
          rag_suggestion: rag?.suggestion, rag_confidence: rag?.confidence,
        }),
      });
      const ticket = (await tr.json()) as { ticket?: { id: number }; error?: string };
      if (!tr.ok) throw new Error(ticket.error ?? "Falha ao criar ticket");

      setFeedback(`Ticket #${ticket.ticket?.id ?? "--"} criado! Nossa equipe entrará em contato.`);
      resetFlow();
    } finally {
      setIsLoading(false);
    }
  }

  /* ── Category card ───────────────────────────────────────────────────── */
  function handleCategoryClick(cat: QuickCategory) {
    const articles: KbArticle[] = cat.articles.map((article, index) => ({
      id: `${cat.title}-${index + 1}`,
      description: article.description,
      resolution: article.resolution,
      category: article.category,
    }));
    setCatModal({ icon: cat.icon, title: cat.title, articles, loading: false });
  }

  function handleCatNeedHelp() {
    const title = catModal?.title ?? "";
    setCatModal(null);
    setTextInput(title + ": ");
    setTimeout(() => textareaRef.current?.focus(), 50);
  }

  function resetFlow() {
    setRag(null); setShowRagModal(false);
    setTextInput(""); setAudioTranscript(""); setAudioBase64(undefined);
    setVoiceStatus("idle");
  }

  const isVoiceActive = voiceStatus !== "idle";

  return (
    <main style={{ minHeight: "100vh", background: "#f8fafc" }}>

      {/* Hero */}
      <section style={{
        background: "linear-gradient(135deg, #0d1b2a 0%, #1a3a5c 40%, #2d1b69 100%)",
        position: "relative", display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center",
        minHeight: 580, padding: "6.5rem 1rem 4.5rem", textAlign: "center",
      }}>
        <div style={{ position: "absolute", inset: 0, overflow: "hidden", pointerEvents: "none" }} aria-hidden>
          <div style={{ position: "absolute", left: -128, top: -128, width: 384, height: 384, borderRadius: "50%", opacity: 0.15, filter: "blur(48px)", background: "radial-gradient(circle, #B48E5A, transparent)" }} />
          <div style={{ position: "absolute", right: -96, bottom: 0, width: 320, height: 320, borderRadius: "50%", opacity: 0.2, filter: "blur(48px)", background: "radial-gradient(circle, #2563eb, transparent)" }} />
        </div>

        <div style={{ position: "relative", zIndex: 1, width: "100%", maxWidth: 1120, margin: "0 auto" }}>
          <div style={{ margin: "0 0 0.85rem", display: "flex", alignItems: "center", justifyContent: "center", gap: 12 }}>
            <Image src="/logo-g4.png" alt="Logo G4" width={40} height={40} />
            <p style={{ margin: 0, fontSize: "1.2rem", fontWeight: 700, letterSpacing: "0.3em", textTransform: "uppercase", color: "#ffffff" }}>
              G4 Help
            </p>
          </div>
          <h1 style={{ marginTop: "2.375rem", margin: "0 0 0.75rem", fontSize: "clamp(1.75rem, 5vw, 3.875rem)", fontWeight: 800, color: "#fff", lineHeight: 1.15, letterSpacing: "-0.025em", textAlign: "center" }}>
            Como podemos ajudar você hoje?
          </h1>
          {/* Input bar */}
          <div style={{
            display: "flex", alignItems: "center", gap: "0.5rem",
            borderRadius: 35,
            border: "1.5px solid rgba(255,255,255,0.15)",
            background: "#fff",
            boxShadow: "0 20px 56px rgba(0,0,0,0.45)",
            padding: "0.44rem 0.45rem 0.44rem 1.1rem",
            minHeight: 36,
            maxWidth: 800,
            margin: "0 auto",
            marginTop: "2.175rem",
          }}>
            {/* Voice waveform OR textarea */}
            <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}>
              {isVoiceActive ? (
                <div style={{ display: "flex", alignItems: "center" }}>
                  <VoiceRecorder status={voiceStatus as "recording" | "transcribing"} />
                </div>
              ) : (
                <>
                  <textarea
                    ref={textareaRef}
                    value={textInput}
                    onChange={(e) => setTextInput(e.target.value.slice(0, 2000))}
                    onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); void handleGenerateSuggestion(); } }}
                    onPaste={(e) => {
                      e.preventDefault();
                      const text = e.clipboardData.getData("text/plain").slice(0, 2000 - textInput.length);
                      setTextInput((prev) => (prev + text).slice(0, 2000));
                    }}
                    rows={1}
                    maxLength={2000}
                    placeholder="Descreva seu problema…"
                    style={{
                      width: "100%", resize: "none", border: "none",
                      padding: "0.15rem 0", fontSize: "0.9375rem", color: "#0f172a",
                      outline: "none", fontFamily: "inherit", background: "transparent",
                      lineHeight: 1.6, overflow: "hidden",
                    }}
                  />
                  {textInput.length > 1600 && (
                    <p style={{ margin: "0.25rem 0 0", fontSize: "0.6875rem", textAlign: "right",
                      color: textInput.length >= 2000 ? "#ef4444" : "#f59e0b" }}>
                      {textInput.length}/2000
                    </p>
                  )}
                </>
              )}
            </div>

            {/* Right-side controls — change based on voice state */}
            {voiceStatus === "recording" ? (
              <>
                {/* Cancel recording */}
                <button
                  type="button"
                  onClick={cancelRecording}
                  title="Cancelar gravação"
                  style={{
                    display: "flex", alignItems: "center", justifyContent: "center",
                    width: 34, height: 34, borderRadius: "50%", border: "none", flexShrink: 0,
                    cursor: "pointer", background: "#fee2e2", color: "#ef4444",
                    fontSize: "1rem", fontWeight: 700, transition: "background 150ms",
                  }}
                >✕</button>
                {/* Confirm / stop recording */}
                <button
                  type="button"
                  onClick={stopRecording}
                  title="Finalizar e transcrever"
                  style={{
                    display: "flex", alignItems: "center", justifyContent: "center",
                    width: 40, height: 40, borderRadius: "50%", border: "none", flexShrink: 0,
                    cursor: "pointer", background: "#021E35", color: "#fff",
                    fontSize: "1.125rem", fontWeight: 700, transition: "background 150ms",
                  }}
                >✓</button>
              </>
            ) : voiceStatus === "transcribing" ? null : (
              <>
                {/* Mic button */}
                <button
                  type="button"
                  onClick={handleMicClick}
                  title="Gravar áudio"
                  style={{
                    display: "flex", alignItems: "center", justifyContent: "center",
                    width: 34, height: 34, borderRadius: "50%", border: "none", flexShrink: 0,
                    cursor: "pointer", background: "#f1f5f9", color: "#64748b",
                    transition: "background 150ms, color 150ms",
                  }}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width={18} height={18}>
                    <path d="M8.25 4.5a3.75 3.75 0 1 1 7.5 0v8.25a3.75 3.75 0 1 1-7.5 0V4.5Z" />
                    <path d="M6 10.5a.75.75 0 0 1 .75.75v1.5a5.25 5.25 0 1 0 10.5 0v-1.5a.75.75 0 0 1 1.5 0v1.5a6.751 6.751 0 0 1-6 6.709v2.291h3a.75.75 0 0 1 0 1.5h-7.5a.75.75 0 0 1 0-1.5h3v-2.291a6.751 6.751 0 0 1-6-6.709v-1.5A.75.75 0 0 1 6 10.5Z" />
                  </svg>
                </button>
                {/* Send button — filled blue circle */}
                <button
                  type="button"
                  onClick={() => void handleGenerateSuggestion()}
                  disabled={isLoading || !finalText}
                  title="Buscar solução"
                  style={{
                    display: "flex", alignItems: "center", justifyContent: "center",
                    width: 40, height: 40, borderRadius: "50%", border: "none", flexShrink: 0,
                    background: isLoading || !finalText ? "rgba(2,30,53,0.35)" : "#021E35",
                    color: "#fff",
                    cursor: isLoading || !finalText ? "not-allowed" : "pointer",
                    transition: "background 150ms",
                  }}
                >
                  {isLoading ? (
                    <span style={{ width: 16, height: 16, borderRadius: "50%", border: "2px solid rgba(255,255,255,0.4)", borderTopColor: "#fff", animation: "spin 0.7s linear infinite", display: "inline-block" }} />
                  ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" width={18} height={18}>
                      <path d="M3.105 2.288a.75.75 0 0 0-.826.95l1.414 4.926A1.5 1.5 0 0 0 5.135 9.25h6.115a.75.75 0 0 1 0 1.5H5.135a1.5 1.5 0 0 0-1.442 1.086l-1.414 4.926a.75.75 0 0 0 .826.95 28.897 28.897 0 0 0 15.293-7.154.75.75 0 0 0 0-1.115A28.897 28.897 0 0 0 3.105 2.288Z" />
                    </svg>
                  )}
                </button>
              </>
            )}
          </div>
          <p style={{ marginTop: "1.175rem", marginBottom: "0.75rem", fontSize: "1.2rem", color: "#94a3b8", lineHeight: 1.6 }}>
            Só gravar um áudio que tiramos sua dúvida. Se mesmo assim não funcionar,
            <br />
            abra um ticket que em até 1h vamos te responder.
          </p>

          {feedback && (
            <p style={{ marginTop: "0.875rem", fontSize: "0.875rem", color: feedback.startsWith("Ticket") || feedback.startsWith("Ótimo") ? "#86efac" : "#94a3b8" }}>
              {feedback}
            </p>
          )}
        </div>
      </section>

      {/* Quick categories */}
      <section style={{ maxWidth: 1100, margin: "0 auto", padding: "3rem 1.25rem 4rem" }}>
        <p style={{ margin: "0 0 0.375rem", fontSize: "0.6875rem", fontWeight: 700, letterSpacing: "0.2em", textTransform: "uppercase", color: "#B48E5A" }}>Atalhos</p>
        <div style={{ margin: "0 0 1.75rem", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 10 }}>
          <h2 style={{ margin: 0, fontSize: "1.5rem", fontWeight: 800, color: "#0f172a", letterSpacing: "-0.02em" }}>Respostas rápidas</h2>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {[
              { href: "/customer/tickets", label: "Meus tickets" },
              { href: "/api/auth/demo?logout=1", label: "Sair" },
            ].map(({ href, label }) => (
              <a
                key={href}
                href={href}
                style={{
                  padding: "6px 16px",
                  borderRadius: 12,
                  fontSize: "0.875rem",
                  fontWeight: 600,
                  background: "#ffffff",
                  color: "#1e293b",
                  border: "1px solid #e2e8f0",
                  textDecoration: "none",
                  boxShadow: "0 1px 3px rgba(2,30,53,0.08)",
                }}
              >
                {label}
              </a>
            ))}
          </div>
        </div>
        <div style={{ display: "grid", gap: "1rem", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))" }}>
          {QUICK_CATEGORIES.map((cat) => (
            <button
              key={cat.title}
              type="button"
              onClick={() => void handleCategoryClick(cat)}
              className="card"
              style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: "0.5rem", padding: "1.25rem 1.5rem", textAlign: "left", cursor: "pointer", transition: "box-shadow 150ms, border-color 150ms" }}
            >
              <p style={{ margin: 0, fontWeight: 700, fontSize: "0.9375rem", color: "#0f172a" }}>{cat.title}</p>
              <p style={{ margin: 0, fontSize: "0.8125rem", color: "#64748b", lineHeight: 1.55 }}>{cat.desc}</p>
              <span style={{ marginTop: "0.25rem", fontSize: "0.75rem", fontWeight: 700, color: "#B48E5A" }}>Ver artigos →</span>
            </button>
          ))}
        </div>
      </section>

      {/* Category modal */}
      {catModal && (
        <CategoryModal modal={catModal} onClose={() => setCatModal(null)} onNeedHelp={handleCatNeedHelp} />
      )}

      {/* RAG modal */}
      {showRagModal && rag && (
        <RagModal
          rag={rag}
          isLoading={isLoading}
          defaultDesc={ragDefaultDesc}
          onClose={() => setShowRagModal(false)}
          onDeflect={handleDeflect}
          onOpenTicket={handleCreateTicket}
        />
      )}
    </main>
  );
}
