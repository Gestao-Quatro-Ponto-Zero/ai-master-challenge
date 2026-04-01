"""
API — Documentação e Swagger interativo
"""

from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="API", page_icon="⚡", layout="wide")

st.page_link("pages/Navegacao.py", label="← Navegação", icon=None)

st.title("⚡ API REST")

tab_text, tab_swagger = st.tabs(["📄 Documentação", "🔌 Swagger"])

# =============================================================================
# TAB 1 — Documentação estática (README.api.md)
# =============================================================================
with tab_text:
    md_path = Path(__file__).parent.parent.parent / "docs" / "README.api.md"
    st.markdown(md_path.read_text(encoding="utf-8"))

# =============================================================================
# TAB 2 — Swagger UI embutido (com paleta customizada)
# =============================================================================
with tab_swagger:
    st.info(
        "O Swagger abaixo só carrega se a API correta estiver rodando na porta 8001. "
        "Use o script abaixo — ele encerra qualquer processo que esteja ocupando a porta antes de subir."
    )
    st.code("cd deal-prioritization\nbash run_api.sh", language="bash")
    st.divider()

    swagger_html = """
<!DOCTYPE html>
<html>
<head>
  <title>API Docs</title>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" type="text/css"
        href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
  <style>
    /* ── Reset base ── */
    body {
      margin: 0;
      background: #0e1117;
      font-family: 'Inter', sans-serif;
    }

    /* ── Topbar ── */
    .swagger-ui .topbar { display: none; }

    /* ── Fundo geral ── */
    .swagger-ui,
    .swagger-ui .wrapper,
    .swagger-ui .opblock-tag-section {
      background: #0e1117;
    }

    /* ── Info / título ── */
    .swagger-ui .info .title,
    .swagger-ui .info p,
    .swagger-ui .info li,
    .swagger-ui .info a {
      color: #e0e0e0;
    }

    /* ── Tags (seções de grupo) ── */
    .swagger-ui .opblock-tag {
      background: #1a1f2e;
      border-bottom: 1px solid #2d3748;
      color: #a78bfa;
      font-size: 15px;
      font-weight: 600;
    }
    .swagger-ui .opblock-tag:hover {
      background: #1e2536;
    }

    /* ── Blocos de endpoint ── */
    .swagger-ui .opblock {
      border-radius: 6px;
      border: 1px solid #2d3748;
      margin-bottom: 6px;
      background: #131720;
    }
    .swagger-ui .opblock .opblock-summary {
      background: #131720;
      border-radius: 6px;
    }

    /* ── Método GET ── */
    .swagger-ui .opblock.opblock-get {
      border-color: #3b82f6;
      background: #0f172a;
    }
    .swagger-ui .opblock.opblock-get .opblock-summary-method {
      background: #3b82f6;
    }

    /* ── Método POST ── */
    .swagger-ui .opblock.opblock-post {
      border-color: #10b981;
      background: #052e16;
    }
    .swagger-ui .opblock.opblock-post .opblock-summary-method {
      background: #10b981;
    }

    /* ── Método DELETE ── */
    .swagger-ui .opblock.opblock-delete {
      border-color: #ef4444;
      background: #1c0606;
    }
    .swagger-ui .opblock.opblock-delete .opblock-summary-method {
      background: #ef4444;
    }

    /* ── Summary text ── */
    .swagger-ui .opblock-summary-path,
    .swagger-ui .opblock-summary-description,
    .swagger-ui .opblock-summary-path__deprecated {
      color: #cbd5e1;
    }

    /* ── Expand / conteúdo interno ── */
    .swagger-ui .opblock-body,
    .swagger-ui .opblock-section,
    .swagger-ui .tab,
    .swagger-ui .tabitem {
      background: #131720;
      color: #e2e8f0;
    }

    /* ── Textos genéricos ── */
    .swagger-ui p,
    .swagger-ui td,
    .swagger-ui th,
    .swagger-ui label,
    .swagger-ui .parameter__name,
    .swagger-ui .parameter__type,
    .swagger-ui table thead tr th,
    .swagger-ui .response-col_status {
      color: #cbd5e1;
    }

    /* ── Tabela de parâmetros ── */
    .swagger-ui table tbody tr td {
      background: #1a1f2e;
      border-bottom: 1px solid #2d3748;
      color: #e2e8f0;
    }

    /* ── Inputs ── */
    .swagger-ui input[type=text],
    .swagger-ui textarea,
    .swagger-ui select {
      background: #1e2536;
      color: #e2e8f0;
      border: 1px solid #4b5563;
      border-radius: 4px;
    }

    /* ── Botão "Try it out" / Execute ── */
    .swagger-ui .btn {
      background: #a78bfa;
      color: #fff;
      border: none;
      border-radius: 4px;
    }
    .swagger-ui .btn:hover {
      background: #7c3aed;
    }
    .swagger-ui .btn.execute {
      background: #3b82f6;
    }
    .swagger-ui .btn.execute:hover {
      background: #2563eb;
    }

    /* ── Response code ── */
    .swagger-ui .response-col_status .response-undocumented,
    .swagger-ui .response-col_links {
      color: #94a3b8;
    }

    /* ── Código / schema ── */
    .swagger-ui .highlight-code,
    .swagger-ui .microlight {
      background: #0d1117;
      border-radius: 4px;
      color: #7dd3fc;
    }

    /* ── Model / schema box ── */
    .swagger-ui section.models,
    .swagger-ui .model-box,
    .swagger-ui .model {
      background: #131720;
      color: #e2e8f0;
    }
    .swagger-ui .model-title {
      color: #a78bfa;
    }
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    const EXPECTED_TITLE = "Deal Prioritization API";
    const API_URL = "http://localhost:8001";

    async function init() {
      const container = document.getElementById("swagger-ui");

      // 1. Tenta buscar o openapi.json
      let spec;
      try {
        const res = await fetch(`${API_URL}/openapi.json`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        spec = await res.json();
      } catch (e) {
        container.innerHTML = `
          <div style="padding:40px;color:#f87171;font-family:monospace;font-size:14px;">
            <strong>⚠️ API não encontrada na porta 8001.</strong><br><br>
            Suba a API correta com:<br><br>
            <code style="background:#1e2536;padding:8px 14px;border-radius:4px;display:inline-block;">
              bash run_api.sh
            </code><br><br>
            <span style="color:#94a3b8;">ou: uvicorn api.main:app --reload --port 8001</span>
          </div>`;
        return;
      }

      // 2. Verifica se é a API correta pelo título
      if (spec.info?.title !== EXPECTED_TITLE) {
        container.innerHTML = `
          <div style="padding:40px;font-family:monospace;font-size:14px;">
            <strong style="color:#fbbf24;">⚠️ API errada detectada na porta 8001.</strong><br><br>
            <span style="color:#cbd5e1;">API encontrada: <code style="color:#f87171;">${spec.info?.title || "desconhecida"}</code></span><br>
            <span style="color:#cbd5e1;">API esperada: <code style="color:#34d399;">${EXPECTED_TITLE}</code></span><br><br>
            <span style="color:#94a3b8;">Encerre o processo na porta 8001 e suba a API correta:</span><br><br>
            <code style="background:#1e2536;padding:8px 14px;border-radius:4px;display:inline-block;">
              bash run_api.sh
            </code>
          </div>`;
        return;
      }

      // 3. API correta — renderiza o Swagger
      SwaggerUIBundle({
        spec: spec,
        dom_id: '#swagger-ui',
        presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIBundle.SwaggerUIStandalonePreset
        ],
        layout: "BaseLayout",
        deepLinking: true,
        defaultModelsExpandDepth: -1,
      });
    }

    init();
  </script>
</body>
</html>
"""

    components.html(swagger_html, height=860, scrolling=True)
