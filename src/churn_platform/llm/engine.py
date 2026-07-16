"""SPEC-12: LLMExplainer — gera narrativas em linguagem natural via OpenCode.

Uso:
    explainer = LLMExplainer(cache_dir="/app/output/cache")
    narrative = await explainer.explain(account_data)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
from datetime import date, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Você é um analista de Customer Success especializado em churn para SaaS B2B.
Sua função é gerar explicações claras e acionáveis para o time de CS sobre por que uma conta específica está em risco de churn.

Regras:
1. Seja específico com dados, não genérico
2. Destaque o que MUDOU (tendência), não apenas o estado atual
3. Termine com a ação mais importante que o CSM deve tomar
4. Use linguagem que um CSM (não data scientist) entenda
5. NÃO invente dados — use apenas o que foi fornecido
6. Seja direto: máximo 4 parágrafos"""

PROMPT_TEMPLATE = """## Dados da Conta
- ID: {account_id}
- Indústria: {industry}
- Plano: {plan_tier_account}
- MRR: ${mrr_amount}/mês
- Seats: {seats_account} usuários

## Health Score: {health_score:.0f}/100 ({health_tier})

## Pilares
- Usage:   {pillar_usage:.0f}/100
- Support: {pillar_support:.0f}/100
- Engagement: {pillar_engagement:.0f}/100
- Financial: {pillar_financial:.0f}/100

## Tendências
- Uso total: {total_usage_count}
- Erros: {total_error_count}
- Tickets de suporte: {total_tickets}
- Escalações: {escalation_count}
- Satisfação média: {avg_satisfaction}

Gere uma análise de 2-3 parágrafos explicando:
1. Por que esta conta está em risco
2. O que mudou nas últimas semanas
3. Ação recomendada com justificativa"""

FALLBACK_TEMPLATE = (
    "Conta {account_id} ({industry}, {plan_tier_account}) — Health Score {health_score:.0f}/100 ({health_tier}). "
    "Pilares: Usage {pillar_usage:.0f}, Support {pillar_support:.0f}, "
    "Engagement {pillar_engagement:.0f}, Financial {pillar_financial:.0f}. "
    "Recomendação: revisar plano de ação baseado nos pilares mais baixos."
)


class LLMExplainer:
    """Gera explicações narrativas para contas via OpenCode on-demand."""

    def __init__(
        self,
        cache_ttl: int = 86400,
        cache_dir: str | None = None,
        timeout: int = 30,
    ):
        self.cache: dict[str, dict] = {}
        self.cache_ttl = cache_ttl
        self.cache_dir = Path(cache_dir) if cache_dir else Path("/tmp/churn_llm_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self._load_cache()

    def _cache_key(self, account_id: str) -> str:
        return f"explain:{account_id}:{date.today().isoformat()}"

    def _load_cache(self) -> None:
        cache_file = self.cache_dir / "explanations.json"
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    self.cache = json.load(f)
                logger.info("Cache LLM carregado: %s entradas", len(self.cache))
            except (json.JSONDecodeError, OSError):
                self.cache = {}

    def _save_cache(self) -> None:
        cache_file = self.cache_dir / "explanations.json"
        try:
            with open(cache_file, "w") as f:
                json.dump(self.cache, f, indent=2, default=str)
        except OSError:
            pass

    async def explain(
        self,
        account: dict[str, Any],
        depth: str = "detailed",
    ) -> dict[str, Any]:
        account_id = account.get("account_id", "unknown")
        key = self._cache_key(account_id)

        cached = self.cache.get(key)
        if cached:
            logger.info("Cache hit para %s (até %s)", account_id, date.today().isoformat())
            return cached

        if depth == "short":
            narrative = self._fallback_explain(account)
        else:
            narrative = await self._call_opencode(self._build_prompt(account))

        result = {
            "account_id": account_id,
            "narrative": narrative,
            "risk_factors": self._extract_risk_factors(account),
            "recommended_actions": self._recommend_actions(account),
            "model": "deepseek-v4-flash-free",
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }

        self.cache[key] = result
        self._save_cache()
        return result

    def _build_prompt(self, account: dict[str, Any]) -> str:
        fields = {
            "account_id": account.get("account_id", "N/A"),
            "industry": account.get("industry", "N/A"),
            "plan_tier_account": account.get("plan_tier_account", account.get("plan_tier", "N/A")),
            "mrr_amount": account.get("mrr_amount", 0),
            "seats_account": account.get("seats_account", account.get("seats", 0)),
            "health_score": account.get("health_score", 50),
            "health_tier": account.get("health_tier", "Unknown"),
            "pillar_usage": account.get("pillar_usage", 50),
            "pillar_support": account.get("pillar_support", 50),
            "pillar_engagement": account.get("pillar_engagement", 50),
            "pillar_financial": account.get("pillar_financial", 50),
            "total_usage_count": account.get("total_usage_count", 0),
            "total_error_count": account.get("total_error_count", 0),
            "total_tickets": account.get("total_tickets", 0),
            "escalation_count": account.get("escalation_count", 0),
            "avg_satisfaction": account.get("avg_satisfaction", 0),
        }
        return PROMPT_TEMPLATE.format(**fields)

    async def _call_opencode(self, prompt: str) -> str:
        try:
            proc = await asyncio.create_subprocess_exec(
                "opencode",
                "--prompt", prompt,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(
                proc.communicate(),
                timeout=self.timeout,
            )
            output = stdout.decode().strip()
            if not output or len(output) < 20:
                return self._fallback_explain_raw(prompt)
            return output
        except asyncio.TimeoutError:
            logger.warning("OpenCode timeout após %ss", self.timeout)
            return self._fallback_explain_raw(prompt)
        except FileNotFoundError:
            logger.warning("OpenCode não encontrado no PATH — usando fallback")
            return self._fallback_explain_raw(prompt)

    def _fallback_explain(self, account: dict[str, Any]) -> str:
        return FALLBACK_TEMPLATE.format(**account)

    def _fallback_explain_raw(self, prompt: str) -> str:
        return (
            "Indisponível no momento. Tente novamente mais tarde.\n\n"
            "Diagnóstico baseado em regras disponível no relatório HTML."
        )

    def _extract_risk_factors(self, account: dict) -> list[str]:
        factors = []
        if account.get("pillar_usage", 50) < 40:
            factors.append("usage_drop_significant")
        if account.get("escalation_count", 0) > 2:
            factors.append("multiple_escalations")
        if account.get("total_error_count", 0) > account.get("total_usage_count", 1) * 0.2:
            factors.append("high_error_rate")
        if account.get("downgrade_flag", False):
            factors.append("recent_downgrade")
        if account.get("avg_satisfaction", 5) < 3:
            factors.append("low_satisfaction")
        if account.get("health_score", 100) < 41:
            factors.append("critical_health")
        return factors[:5] or ["no_immediate_risk"]

    def _recommend_actions(self, account: dict) -> list[dict]:
        actions = []
        if account.get("pillar_usage", 50) < 40:
            actions.append({"action": "INT-001", "description": "Reengajamento de uso — treinamento dedicado"})
        if account.get("escalation_count", 0) > 2:
            actions.append({"action": "INT-002", "description": "Reunião executiva para resolver escalações pendentes"})
        if account.get("avg_satisfaction", 5) < 3:
            actions.append({"action": "INT-003", "description": "Survey de satisfação seguido de action plan"})
        if account.get("pillar_financial", 50) < 40:
            actions.append({"action": "INT-004", "description": "Revisão de contrato — renegociação de plano"})
        if not actions:
            actions.append({"action": "INT-000", "description": "Monitoramento padrão — nenhuma ação urgente"})
        return actions

    def invalidate_cache(self) -> None:
        self.cache.clear()
        cache_file = self.cache_dir / "explanations.json"
        if cache_file.exists():
            cache_file.unlink()
        logger.info("Cache LLM invalidado")
