"""Fontes dos CSVs: MCP remoto do Kaggle (padrão) ou uma pasta local."""

import asyncio
import io
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client

DATASETS = ("accounts", "subscriptions", "feature_usage", "support_tickets", "churn_events")


def file_name(dataset: str) -> str:
    return f"ravenstack_{dataset}.csv"


@dataclass(frozen=True)
class Snapshot:
    """Os 5 CSVs de uma versão do dataset."""

    source: str  # kaggle_mcp | local
    source_ref: str
    version: int | None
    files: dict[str, bytes]  # dataset -> conteúdo do CSV


def from_local(path: Path) -> Snapshot:
    files = {d: (path / file_name(d)).read_bytes() for d in DATASETS}
    return Snapshot(source="local", source_ref=str(path), version=None, files=files)


async def _call_tool(session: ClientSession, name: str, request: dict[str, Any]) -> dict[str, Any]:
    result = await session.call_tool(name, {"request": request})
    if result.is_error:
        raise RuntimeError(f"Kaggle MCP {name} falhou: {result.content}")
    text = "".join(getattr(block, "text", "") for block in result.content)
    data: dict[str, Any] = json.loads(text)
    return data


async def _kaggle_info_and_url(url: str, dataset: str, token: str | None) -> tuple[int | None, str]:
    owner, slug = dataset.split("/", 1)
    ref = {"ownerSlug": owner, "datasetSlug": slug}
    headers = {"Authorization": f"Bearer {token}"} if token else None
    async with (
        create_mcp_http_client(headers=headers) as http_client,
        streamable_http_client(url, http_client=http_client) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        info = await _call_tool(session, "get_dataset_info", ref)
        download = await _call_tool(session, "download_dataset", ref)
    version = info.get("current_version_number") or info.get("currentVersionNumber")
    return (int(version) if version is not None else None), str(download["url"])


def kaggle_version(url: str, dataset: str, token: str | None) -> int | None:
    version, _ = asyncio.run(_kaggle_info_and_url(url, dataset, token))
    return version


def from_kaggle(url: str, dataset: str, token: str | None) -> Snapshot:
    version, download_url = asyncio.run(_kaggle_info_and_url(url, dataset, token))
    response = httpx.get(download_url, timeout=120, follow_redirects=True)
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        files = {d: archive.read(file_name(d)) for d in DATASETS}
    return Snapshot(source="kaggle_mcp", source_ref=dataset, version=version, files=files)
