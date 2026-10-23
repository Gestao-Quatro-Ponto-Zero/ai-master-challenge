"""Cria (ou atualiza) a API e o dashboard no Render pela API REST, lendo segredos do .env.

Uso: uv run python scripts/render_deploy.py
Precisa no .env: RENDER_API_KEY, RENDER_DATABASE_URL (pooler IPv4), ANTHROPIC_API_KEY.
Gera AUTH_SECRET e MCP_TOKEN (gravados no .env para você usar no painel e no MCP).
"""

import secrets
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env"
REPO = "https://github.com/tiagocanatelliretechers/ai-master-challenge"
BRANCH = "submission/tiago-canatelli"
API = "https://api.render.com/v1"


def read_env() -> dict[str, str]:
    env = {}
    for line in ENV_FILE.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def ensure_secret(env: dict[str, str], key: str) -> str:
    if not env.get(key):
        env[key] = secrets.token_urlsafe(24)
        with ENV_FILE.open("a") as f:
            f.write(f"\n{key}={env[key]}\n")
    return env[key]


def main() -> None:
    env = read_env()
    client = httpx.Client(
        base_url=API, headers={"Authorization": f"Bearer {env['RENDER_API_KEY']}"}, timeout=60
    )
    owner = client.get("/owners", params={"limit": 1}).raise_for_status().json()[0]["owner"]["id"]
    existing = {
        s["service"]["name"]: s["service"]
        for s in client.get("/services", params={"limit": 50}).json()
    }

    auth_secret = ensure_secret(env, "AUTH_SECRET")
    mcp_token = ensure_secret(env, "MCP_TOKEN")
    cron_token = ensure_secret(env, "CRON_TOKEN")
    api_env = [
        {"key": "PYTHON_VERSION", "value": "3.12.8"},
        {"key": "DATABASE_URL", "value": env["RENDER_DATABASE_URL"]},
        {"key": "ANTHROPIC_API_KEY", "value": env["ANTHROPIC_API_KEY"]},
        {"key": "AUTH_SECRET", "value": auth_secret},
        {"key": "MCP_TOKEN", "value": mcp_token},
        {"key": "CORS_ORIGINS", "value": "*"},
        # ingestão disparada pelo painel (POST /ingest) e pelo cron
        {"key": "CRON_TOKEN", "value": cron_token},
        {"key": "SUPABASE_URL", "value": env["SUPABASE_URL"]},
        {"key": "SUPABASE_SECRET_KEY", "value": env["SUPABASE_SECRET_KEY"]},
    ]

    if "ravenstack-api" in existing:
        api_svc = existing["ravenstack-api"]
        client.put(f"/services/{api_svc['id']}/env-vars", json=api_env).raise_for_status()
        client.post(f"/services/{api_svc['id']}/deploys", json={}).raise_for_status()
    else:
        r = client.post(
            "/services",
            json={
                "type": "web_service",
                "name": "ravenstack-api",
                "ownerId": owner,
                "repo": REPO,
                "branch": BRANCH,
                "rootDir": "submissions/tiago-canatelli",
                "autoDeploy": "yes",
                "envVars": api_env,
                "serviceDetails": {
                    "runtime": "python",
                    "plan": "free",
                    "region": "virginia",
                    "healthCheckPath": "/health",
                    "envSpecificDetails": {
                        "buildCommand": "pip install uv && uv sync --frozen --package api --no-dev",
                        "startCommand": "uv run --no-sync --package api uvicorn api.main:app --host 0.0.0.0 --port $PORT",
                    },
                },
            },
        )
        if r.status_code >= 400:
            raise SystemExit(f"erro ao criar API: {r.status_code} {r.text}")
        api_svc = r.json()["service"]
    api_url = api_svc["serviceDetails"]["url"]
    print("API:", api_url)

    dash_env = [{"key": "VITE_API_URL", "value": api_url}]
    if "ravenstack-dashboard" in existing:
        dash = existing["ravenstack-dashboard"]
        client.put(f"/services/{dash['id']}/env-vars", json=dash_env).raise_for_status()
        client.post(f"/services/{dash['id']}/deploys", json={}).raise_for_status()
    else:
        r = client.post(
            "/services",
            json={
                "type": "static_site",
                "name": "ravenstack-dashboard",
                "ownerId": owner,
                "repo": REPO,
                "branch": BRANCH,
                "rootDir": "submissions/tiago-canatelli/apps/dashboard",
                "autoDeploy": "yes",
                "envVars": dash_env,
                "serviceDetails": {
                    "buildCommand": "npm ci && npm run build",
                    "publishPath": "dist",
                },
            },
        )
        if r.status_code >= 400:
            raise SystemExit(f"erro ao criar dashboard: {r.status_code} {r.text}")
        dash = r.json()["service"]
        client.post(
            f"/services/{dash['id']}/routes",
            json=[{"type": "rewrite", "source": "/*", "destination": "/index.html"}],
        )
    print("Dashboard:", dash["serviceDetails"]["url"])
    print("AUTH_SECRET e MCP_TOKEN estão no .env; códigos dos usuários em .users.local.md.")


if __name__ == "__main__":
    main()
