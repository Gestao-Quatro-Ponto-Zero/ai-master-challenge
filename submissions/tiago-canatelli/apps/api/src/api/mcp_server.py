"""Servidor MCP: as mesmas tools do assistente + prompts e perfis lidos do banco.

Remoto: montado em /mcp pela API (streamable HTTP, bearer MCP_TOKEN).
Local:  `uv run ravenstack-mcp` (stdio) para Claude Desktop/Code.
"""

from typing import Any

from mcp.server.mcpserver import MCPServer

from api import db, tools

mcp = MCPServer(
    name="ravenstack-churn",
    instructions=(
        "Análise de churn da RavenStack (dados 2023–2024). Use get_kpi_overview para começar, "
        "list_at_risk_accounts para a fila do CS e query_analytics para SELECTs sobre o schema api. "
        "Responda com Resposta, Por quê (números + view), Confiança e Próxima ação."
    ),
)


@mcp.tool()
def get_kpi_overview() -> dict[str, Any]:
    """Números-chave atuais do churn (painel do CEO)."""
    return tools.get_kpi_overview()


@mcp.tool()
def get_kpi(view: str) -> dict[str, Any]:
    """Lê uma view de KPI do schema api (tenure_hazard, cohort, persona_summary, support_health...)."""
    return tools.get_kpi(view)


@mcp.tool()
def list_at_risk_accounts(limit: int = 10, persona: str | None = None) -> dict[str, Any]:
    """Contas ativas por MRR em risco em 90 dias, com drivers e ação sugerida."""
    return tools.list_at_risk_accounts(limit, persona)


@mcp.tool()
def get_account_health(account_id: str) -> dict[str, Any]:
    """Visão 360 de uma conta (ex.: A-c70870)."""
    return tools.get_account_health(account_id)


@mcp.tool()
def query_analytics(sql: str) -> dict[str, Any]:
    """Um único SELECT (só leitura) sobre views do schema api; máx. 500 linhas."""
    return tools.query_analytics(sql)


def _register_prompts() -> None:
    """Prompts prontos e perfis por área viram prompts MCP (lidos do banco na inicialização)."""
    try:
        prompts = db.rows("select slug, title, body from api.prompts")
        profiles = db.rows("select slug, name, question, instructions from api.profiles")
    except Exception:  # banco indisponível: o MCP sobe só com as tools
        return
    for p in prompts:
        body = p["body"]

        def render(body: str = body, **kwargs: str) -> str:
            for key, value in kwargs.items():
                body = body.replace("{{" + key + "}}", value)
            return body

        mcp.prompt(name=p["slug"], description=p["title"])(lambda body=body: body)
    for pr in profiles:
        text = f"Analise como {pr['name']}. Pergunta central: {pr['question']} {pr['instructions']}"
        mcp.prompt(name=f"perfil-{pr['slug']}", description=pr["name"])(lambda text=text: text)


_register_prompts()


def run_stdio() -> None:
    mcp.run("stdio")
