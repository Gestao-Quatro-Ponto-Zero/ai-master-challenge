export default function AdminNlpPage() {
  return (
    <>
      <header className="admin-header">
        <nav style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.875rem" }}>
          <span style={{ color: "var(--ad-text-dim)" }}>Painel</span>
          <span style={{ color: "var(--ad-text-dim)" }}>/</span>
          <span style={{ color: "var(--ad-text)", fontWeight: 500 }}>NLP & IA</span>
        </nav>
      </header>

      <div className="admin-content">

        {/* ── Title ──────────────────────────────────────────────────────── */}
        <div style={{ marginBottom: "2rem" }}>
          <h1 style={{ margin: 0, fontSize: "2rem", fontWeight: 800, letterSpacing: "-0.03em", color: "var(--ad-text)", lineHeight: 1.15 }}>
            NLP & Inteligência Artificial
          </h1>
          <p style={{ margin: "0.375rem 0 0", fontSize: "0.9375rem", color: "var(--ad-text-muted)" }}>
            Modelos, custos e racional estratégico da camada de IA do G4 Help
          </p>
        </div>

        {/* ── Pipeline ───────────────────────────────────────────────────── */}
        <section style={{ marginBottom: "2.5rem" }}>
          <h2 style={{ margin: "0 0 1rem", fontSize: "1.125rem", fontWeight: 700, color: "var(--ad-text)", letterSpacing: "-0.02em" }}>
            Pipeline de processamento
          </h2>
          <div style={{ display: "flex", alignItems: "stretch", gap: 0, overflowX: "auto", paddingBottom: "0.25rem" }}>
            {PIPELINE_STEPS.map((step, i) => (
              <div key={step.id} style={{ display: "flex", alignItems: "center", minWidth: 0 }}>
                {/* Card */}
                <div className="ad-card" style={{
                  padding: "1.125rem 1.25rem", minWidth: 160, flex: "0 0 auto",
                  borderLeft: `3px solid ${step.color}`,
                }}>
                  <p style={{ margin: "0 0 0.375rem", fontSize: "0.625rem", fontWeight: 700, letterSpacing: "0.12em", textTransform: "uppercase", color: step.color }}>
                    {step.tag}
                  </p>
                  <p style={{ margin: "0 0 0.25rem", fontSize: "0.875rem", fontWeight: 700, color: "var(--ad-text)", lineHeight: 1.3 }}>
                    {step.title}
                  </p>
                  <p style={{ margin: 0, fontSize: "0.6875rem", color: "var(--ad-text-muted)", lineHeight: 1.5 }}>
                    {step.model}
                  </p>
                </div>
                {/* Arrow */}
                {i < PIPELINE_STEPS.length - 1 && (
                  <div style={{ padding: "0 0.375rem", flexShrink: 0, color: "var(--ad-text-dim)", fontSize: "1rem" }}>›</div>
                )}
              </div>
            ))}
          </div>
          <p style={{ marginTop: "0.75rem", fontSize: "0.75rem", color: "var(--ad-text-dim)" }}>
            * A transcrição de voz (Whisper) só é acionada quando o cliente usa o microfone. Texto digitado entra diretamente na etapa de embedding.
          </p>
        </section>

        {/* ── Strategic rationale ────────────────────────────────────────── */}
        <section style={{ marginBottom: "2.5rem" }}>
          <h2 style={{ margin: "0 0 0.25rem", fontSize: "1.5rem", fontWeight: 800, color: "var(--ad-text)", letterSpacing: "-0.025em" }}>
            Racional estratégico
          </h2>
          <p style={{ margin: "0 0 1.25rem", fontSize: "0.875rem", color: "var(--ad-text-muted)" }}>
            Por que investir em IA no canal de suporte?
          </p>
          <div style={{ display: "grid", gap: "1rem", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))" }}>
            {RATIONALE.map((r) => (
              <article key={r.id} className="ad-card" style={{ padding: "1.75rem" }}>
                <p style={{ margin: "0 0 0.5rem", fontSize: "0.6875rem", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--ad-text-dim)" }}>
                  {r.tag}
                </p>
                <p style={{ margin: "0 0 0.5rem", fontSize: "1.25rem", fontWeight: 800, lineHeight: 1.2, letterSpacing: "-0.025em", color: r.accent ? r.accent : "var(--ad-text)" }}>
                  {r.headline}
                </p>
                <p style={{ margin: "0 0 1.25rem", fontSize: "0.875rem", color: "var(--ad-text-muted)", lineHeight: 1.6 }}>
                  {r.body}
                </p>
                <hr style={{ border: "none", borderTop: "1px solid var(--ad-border)", margin: "0 0 1rem" }} />
                <p style={{ margin: 0, fontSize: "0.75rem", color: "var(--ad-text-dim)", lineHeight: 1.6 }}>
                  <span style={{ fontWeight: 600, color: "var(--ad-text-muted)" }}>Impacto esperado: </span>
                  {r.impact}
                </p>
              </article>
            ))}
          </div>
        </section>

        {/* ── Cost estimate ──────────────────────────────────────────────── */}
        <section style={{ marginBottom: "2.5rem" }}>
          <h2 style={{ margin: "0 0 1rem", fontSize: "1.125rem", fontWeight: 700, color: "var(--ad-text)", letterSpacing: "-0.02em" }}>
            Estimativa de custo
          </h2>
          <div style={{ display: "grid", gap: "1rem", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))" }}>

            {/* Per interaction */}
            <article className="ad-card" style={{ padding: "1.5rem" }}>
              <p style={{ margin: "0 0 1rem", fontSize: "0.875rem", fontWeight: 700, color: "var(--ad-text)" }}>Por interação</p>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                {COST_PER_INTERACTION.map((r) => (
                  <div key={r.label} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.5rem 0", borderBottom: "1px solid var(--ad-border)" }}>
                    <span style={{ fontSize: "0.8125rem", color: "var(--ad-text-muted)" }}>{r.label}</span>
                    <span style={{ fontFamily: "monospace", fontSize: "0.8125rem", fontWeight: 600, color: "var(--ad-text)" }}>{r.value}</span>
                  </div>
                ))}
              </div>
              <p style={{ margin: "0.875rem 0 0", fontSize: "0.6875rem", color: "var(--ad-text-dim)", lineHeight: 1.5 }}>
                Baseado em 80 tokens/query de texto · 30s de áudio (quando voz) · 600 tokens de contexto RAG · 150 tokens de saída
              </p>
            </article>

            {/* At scale */}
            <article className="ad-card" style={{ padding: "1.5rem" }}>
              <p style={{ margin: "0 0 1rem", fontSize: "0.875rem", fontWeight: 700, color: "var(--ad-text)" }}>Projeção · 8.469 tickets</p>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                {COST_AT_SCALE.map((r) => (
                  <div key={r.label} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.5rem 0", borderBottom: "1px solid var(--ad-border)" }}>
                    <span style={{ fontSize: "0.8125rem", color: "var(--ad-text-muted)" }}>{r.label}</span>
                    <span style={{ fontFamily: "monospace", fontSize: "0.8125rem", fontWeight: 600, color: r.highlight ? "var(--ad-success)" : "var(--ad-text)" }}>{r.value}</span>
                  </div>
                ))}
              </div>
              <p style={{ margin: "0.875rem 0 0", fontSize: "0.6875rem", color: "var(--ad-text-dim)", lineHeight: 1.5 }}>
                Cenário misto: 70% texto · 30% voz. Custo marginal por ticket novo: ~$0,003
              </p>
            </article>

          </div>

          {/* ── Bottom-line callout ──────────────────────────────────────── */}
          <article style={{
            marginTop: "1rem",
            padding: "1.75rem 2rem",
            borderRadius: "0.75rem",
            background: "linear-gradient(135deg, #0d3d26 0%, #0f5c40 100%)",
            border: "1px solid #10b98130",
            display: "grid",
            gridTemplateColumns: "1fr auto",
            gap: "2rem",
            alignItems: "center",
          }}>
            <div>
              <p style={{ margin: "0 0 0.375rem", fontSize: "0.6875rem", fontWeight: 700, letterSpacing: "0.12em", textTransform: "uppercase", color: "#34d399" }}>
                Conclusão de custo
              </p>
              <p style={{ margin: "0 0 0.75rem", fontSize: "1.375rem", fontWeight: 800, lineHeight: 1.2, letterSpacing: "-0.025em", color: "#ecfdf5" }}>
                Menos de R$ 5 por mês para atender 700 tickets com IA — o custo é irrelevante perto do valor gerado
              </p>
              <p style={{ margin: 0, fontSize: "0.875rem", color: "#6ee7b7", lineHeight: 1.7 }}>
                Tickets de baixa complexidade — acesso, certificados, dúvidas sobre programas — respondem por{" "}
                <strong style={{ color: "#a7f3d0" }}>mais de 60% do volume</strong> e têm respostas padronizadas que a IA já domina.
                Cada chamado deflexionado poupa ~<strong style={{ color: "#a7f3d0" }}>R$ 35 em esforço humano</strong>.
                Com 15–30% de deflexão, o retorno sobre o investimento em IA supera{" "}
                <strong style={{ color: "#a7f3d0" }}>100× o custo operacional</strong> — em questão de semanas.
              </p>
            </div>
            <div style={{ textAlign: "center", flexShrink: 0 }}>
              <p style={{ margin: 0, fontSize: "2.75rem", fontWeight: 900, letterSpacing: "-0.04em", color: "#10b981", lineHeight: 1 }}>
                &gt;100×
              </p>
              <p style={{ margin: "0.375rem 0 0", fontSize: "0.6875rem", fontWeight: 600, color: "#34d399", textTransform: "uppercase", letterSpacing: "0.08em" }}>
                ROI estimado
              </p>
            </div>
          </article>
        </section>

        {/* ── Model cards ────────────────────────────────────────────────── */}
        <section style={{ marginBottom: "2.5rem" }}>
          <h2 style={{ margin: "0 0 1rem", fontSize: "1.125rem", fontWeight: 700, color: "var(--ad-text)", letterSpacing: "-0.02em" }}>
            Modelos utilizados
          </h2>
          <div style={{ display: "grid", gap: "1rem", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))" }}>
            {MODELS.map((m) => (
              <article key={m.id} className="ad-card" style={{ padding: "1.5rem" }}>
                <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "0.75rem", marginBottom: "0.875rem" }}>
                  <div>
                    <span style={{
                      display: "inline-block", padding: "2px 8px", borderRadius: 99, marginBottom: "0.5rem",
                      fontSize: "0.625rem", fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase",
                      background: `${m.color}20`, color: m.color,
                    }}>
                      {m.provider}
                    </span>
                    <p style={{ margin: 0, fontSize: "1rem", fontWeight: 800, color: "var(--ad-text)", letterSpacing: "-0.02em" }}>
                      {m.name}
                    </p>
                  </div>
                  <div style={{
                    flexShrink: 0, width: 36, height: 36, borderRadius: 8,
                    background: `${m.color}15`, display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: "1.125rem",
                  }}>
                    {m.icon}
                  </div>
                </div>

                <p style={{ margin: "0 0 1rem", fontSize: "0.8125rem", color: "var(--ad-text-muted)", lineHeight: 1.6 }}>
                  {m.description}
                </p>

                <div style={{ borderTop: "1px solid var(--ad-border)", paddingTop: "0.875rem", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  {m.specs.map((s) => (
                    <div key={s.label} style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: "0.5rem" }}>
                      <span style={{ fontSize: "0.6875rem", color: "var(--ad-text-dim)", textTransform: "uppercase", letterSpacing: "0.06em" }}>{s.label}</span>
                      <span style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--ad-text)", fontFamily: "monospace" }}>{s.value}</span>
                    </div>
                  ))}
                </div>

                <div style={{ marginTop: "0.875rem", padding: "0.625rem 0.75rem", borderRadius: 8, background: `${m.color}0d` }}>
                  <p style={{ margin: 0, fontSize: "0.6875rem", color: m.color, fontWeight: 600 }}>Uso no pipeline</p>
                  <p style={{ margin: "0.2rem 0 0", fontSize: "0.75rem", color: "var(--ad-text-muted)" }}>{m.usage}</p>
                </div>
              </article>
            ))}
          </div>
        </section>

      </div>
    </>
  );
}

/* ── Static data ─────────────────────────────────────────────────────────── */

const PIPELINE_STEPS = [
  {
    id: "input",
    tag: "Entrada",
    title: "Descrição do problema",
    model: "Texto digitado ou voz gravada",
    color: "#64748b",
  },
  {
    id: "whisper",
    tag: "Opcional · Voz",
    title: "Transcrição de áudio",
    model: "whisper-1",
    color: "#B48E5A",
  },
  {
    id: "embed",
    tag: "Vetorização",
    title: "Embedding + busca KB",
    model: "text-embedding-3-small · pgvector",
    color: "#0ea5a4",
  },
  {
    id: "rag",
    tag: "Geração",
    title: "Sugestão imediata",
    model: "gpt-4o-mini (RAG)",
    color: "#10b981",
  },
  {
    id: "classify",
    tag: "Triagem",
    title: "Categoria & prioridade",
    model: "Vetor (primário) · gpt-4o-mini (fallback)",
    color: "#f59e0b",
  },
];

const MODELS = [
  {
    id: "whisper",
    name: "whisper-1",
    provider: "OpenAI · STT",
    icon: "🎙️",
    color: "#B48E5A",
    description:
      "Modelo de speech-to-text treinado em 680 mil horas de áudio multilíngue. Converte o áudio gravado pelo cliente em texto com alta precisão em português, eliminando barreiras de digitação.",
    specs: [
      { label: "Preço",         value: "$0,006 / min" },
      { label: "Latência típica", value: "~1–2 s (30 s de áudio)" },
      { label: "Formato aceito",  value: "WebM, MP3, WAV, M4A" },
      { label: "Idioma",         value: "Multilíngue (pt-BR nativo)" },
    ],
    usage: "Acionado exclusivamente quando o cliente usa o microfone. Rota: POST /api/transcribe",
  },
  {
    id: "embedding",
    name: "text-embedding-3-small",
    provider: "OpenAI · Embedding",
    icon: "🔢",
    color: "#0ea5a4",
    description:
      "Gera vetores de 1.536 dimensões para representar semântica do texto. É o núcleo do sistema de busca — permite encontrar artigos da KB e categorias de ticket por similaridade semântica, não por palavras-chave.",
    specs: [
      { label: "Preço",         value: "$0,020 / 1M tokens" },
      { label: "Dimensões",     value: "1.536" },
      { label: "Latência típica", value: "~200 ms" },
      { label: "Threshold KB",   value: "≥ 0,60 similaridade" },
    ],
    usage: "Embeds a query do cliente e busca as 5 resoluções mais próximas na KB via pgvector (Supabase). Também embeds categorias para classificação vetorial (threshold ≥ 0,35).",
  },
  {
    id: "gpt4omini",
    name: "gpt-4o-mini",
    provider: "OpenAI · Chat",
    icon: "🤖",
    color: "#10b981",
    description:
      "Modelo de linguagem compacto e de baixo custo da família GPT-4o. Utilizado em dois momentos: geração da sugestão RAG (resposta imediata ao cliente) e classificação de categoria/prioridade quando a similaridade vetorial é insuficiente.",
    specs: [
      { label: "Input",           value: "$0,150 / 1M tokens" },
      { label: "Output",          value: "$0,600 / 1M tokens" },
      { label: "Latência típica", value: "~800 ms – 1,5 s" },
      { label: "Formato saída",   value: "JSON estruturado" },
    ],
    usage: "RAG: gera sugestão com base nos 5 artigos recuperados. Fallback classify: retorna category, priority, confidence quando vetor < 0,35.",
  },
];

const COST_PER_INTERACTION = [
  { label: "Embedding (80 tokens)",              value: "~$0,0000016" },
  { label: "RAG — gpt-4o-mini input (600 tok)",  value: "~$0,0000900" },
  { label: "RAG — gpt-4o-mini output (150 tok)", value: "~$0,0000900" },
  { label: "Classificação vetorial (fallback)",   value: "~$0,0000600" },
  { label: "Total · só texto",                    value: "~$0,00025" },
  { label: "Whisper · 30 s de voz",               value: "+$0,00300" },
  { label: "Total · com voz",                     value: "~$0,00325" },
];

const COST_AT_SCALE = [
  { label: "8.469 tickets, 100% texto",     value: "~$2,12",   highlight: false },
  { label: "8.469 tickets, 30% voz",        value: "~$9,80",   highlight: false },
  { label: "Custo/ticket (mix 70/30)",      value: "~$0,0012", highlight: false },
  { label: "Custo mensal (~700 tickets/mês)", value: "~$0,84", highlight: true },
  { label: "Economia vs. atendente humano", value: "> 99%",    highlight: true },
];

const RATIONALE = [
  {
    id: "ux",
    tag: "Experiência do cliente",
    headline: "Suporte não precisa ser uma experiência ruim",
    body: "Abrir ticket é uma das interações mais frustrantes numa plataforma de educação — o cliente já está com um problema e ainda precisa navegar formulários. A IA reduz esse atrito: qualquer pessoa, em qualquer dispositivo, descreve o problema na própria linguagem — digitando ou falando — e já recebe uma resposta em segundos.",
    impact: "Redução do esforço percebido pelo cliente ao reportar um problema. Menos abandono de fluxo antes da abertura do ticket.",
    accent: null,
  },
  {
    id: "sentiment",
    tag: "Retenção & sentimento",
    headline: "Cada minuto esperando aumenta o risco de churn",
    body: "Em SaaS de educação, o suporte ruim é uma das principais causas de cancelamento. Quando o cliente recebe uma sugestão imediata — mesmo que precise abrir ticket depois — a percepção de abandono é eliminada. O sistema sinaliza que a plataforma está atenta e proativa, não reativamente.",
    impact: "Prevenção de sentimentos negativos associados à marca G4. O cliente sente que foi atendido antes mesmo de um humano entrar na fila.",
    accent: null,
  },
  {
    id: "deflection",
    tag: "Eficiência operacional",
    headline: "Cada sugestão resolvida é um ticket que nunca abre",
    body: "Se a sugestão da IA resolver o problema do cliente antes da confirmação do ticket, ele simplesmente não abre o chamado. Com os R$ 921 mil em ineficiência mapeados na operação e 26,4% do tempo recuperável, cada ticket deflexado representa ~R$ 35 de esforço humano poupado — direto para a margem operacional.",
    impact: "Potencial de deflexão de 15–30% dos tickets de baixa complexidade (acesso, certificados, pagamentos). Menos intervenção manual, menor backlog, maior CSAT.",
    accent: "var(--ad-success)",
  },
];
