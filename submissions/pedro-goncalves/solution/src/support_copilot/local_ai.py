from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_MODEL = "ibm/granite4.1:8b"
DEFAULT_HOST = "http://127.0.0.1:11434"


@dataclass(frozen=True)
class LocalAIResult:
    available: bool
    model: str
    payload: dict[str, Any]
    error: str | None = None


def _host() -> str:
    return os.getenv("OSS_OLLAMA_HOST", DEFAULT_HOST).rstrip("/")


def model_name() -> str:
    return os.getenv("OSS_LOCAL_MODEL", DEFAULT_MODEL)


def _request_json(
    path: str,
    *,
    payload: dict[str, Any] | None = None,
    timeout: float = 60,
) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        f"{_host()}{path}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="GET" if payload is None else "POST",
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def local_model_available() -> tuple[bool, str | None]:
    try:
        installed = _request_json("/api/tags", timeout=2).get("models", [])
    except (OSError, HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return False, "Ollama local não respondeu."
    names = {
        str(item.get("name") or item.get("model") or "")
        for item in installed
    }
    selected = model_name()
    if selected not in names:
        return False, f"Modelo local não instalado: {selected}."
    return True, None


def _generate_json(prompt: str) -> LocalAIResult:
    selected = model_name()
    available, error = local_model_available()
    if not available:
        return LocalAIResult(False, selected, {}, error)
    try:
        response = _request_json(
            "/api/generate",
            payload={
                "model": selected,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0,
                    "seed": 42,
                    "num_predict": 420,
                    "num_ctx": 4096,
                },
            },
        )
        parsed = json.loads(response.get("response", "{}"))
        if not isinstance(parsed, dict):
            raise ValueError("A resposta local não é um objeto JSON.")
        return LocalAIResult(True, selected, parsed)
    except (
        OSError,
        HTTPError,
        URLError,
        TimeoutError,
        json.JSONDecodeError,
        ValueError,
    ) as exception:
        return LocalAIResult(
            False,
            selected,
            {},
            f"Revisão local indisponível: {exception}",
        )


def _normalized_review(
    result: LocalAIResult,
    *,
    kind: str,
) -> LocalAIResult:
    if not result.available:
        return result
    payload = result.payload
    if kind == "structure":
        verdict = payload.get("veredito") or payload.get("verdict")
        observations = payload.get("observacoes") or payload.get("observations") or []
        human_check = (
            payload.get("checagem_humana")
            or payload.get("human_check")
            or payload.get("human_review")
            or ""
        )
        if verdict not in {"apto_para_aprovacao", "revisar_estrutura"}:
            verdict = "revisar_estrutura"
        normalized = {
            "veredito": verdict,
            "observacoes": [str(item)[:240] for item in observations[:3]],
            "checagem_humana": str(human_check)[:300],
        }
    else:
        status = payload.get("status")
        checks = (
            payload.get("checagens")
            or payload.get("checkpoints")
            or payload.get("checks")
            or []
        )
        limit = payload.get("limite") or payload.get("limit") or ""
        if status not in {"coerente", "revisao_humana"}:
            status = "revisao_humana"
        normalized = {
            "status": status,
            "checagens": [str(item)[:240] for item in checks[:3]],
            "limite": str(limit)[:300],
        }
    return LocalAIResult(True, result.model, normalized)


def review_structure(
    *,
    source_profiles: list[dict[str, Any]],
    approved_lessons: list[dict[str, Any]],
) -> LocalAIResult:
    prompt = f"""
Você é o revisor local do OSS, um sistema de suporte em modo de observação.
Analise somente metadados estruturais. Não invente métricas, não recomende
automação total e não modifique dados. As lições abaixo foram aprovadas por
humanos e podem orientar a revisão.

FONTES:
{json.dumps(source_profiles, ensure_ascii=False)}

LIÇÕES APROVADAS:
{json.dumps(approved_lessons, ensure_ascii=False)}

Responda exclusivamente em JSON:
{{
  "veredito": "apto_para_aprovacao" ou "revisar_estrutura",
  "observacoes": ["no máximo 3 observações curtas"],
  "checagem_humana": "uma pergunta objetiva antes da aprovação"
}}
"""
    return _normalized_review(_generate_json(prompt), kind="structure")


def review_deterministic_opinion(
    *,
    opinion_facts: dict[str, Any],
    approved_lessons: list[dict[str, Any]],
) -> LocalAIResult:
    prompt = f"""
Você é o segundo revisor local do OSS. O parecer foi calculado por código
determinístico. Você não pode recalcular, substituir, corrigir silenciosamente
ou criar números. Compare os fatos com as lições humanas aprovadas e procure
contradições, omissões ou excesso de confiança.

FATOS DO PARECER:
{json.dumps(opinion_facts, ensure_ascii=False)}

LIÇÕES APROVADAS:
{json.dumps(approved_lessons, ensure_ascii=False)}

Responda exclusivamente em JSON:
{{
  "status": "coerente" ou "revisao_humana",
  "checagens": ["no máximo 3 checagens curtas"],
  "limite": "uma limitação que deve permanecer visível"
}}
"""
    return _normalized_review(_generate_json(prompt), kind="opinion")
