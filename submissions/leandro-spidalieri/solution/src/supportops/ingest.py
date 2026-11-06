"""Ingestão de snapshots fixos, com verificação antes de análise ou treino."""

import hashlib
import io
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen
from zipfile import ZipFile

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
ARTIFACTS = ROOT / "artifacts"
LOCAL = ARTIFACTS / "local"
MAX_BYTES = 32 * 1024 * 1024
ACQUISITION = "2026-11-06"


@dataclass(frozen=True)
class Source:
    slug: str
    file: str
    sha256: str
    zip_sha256: str
    version: int
    last_updated: str

    @property
    def download(self):
        return f"https://www.kaggle.com/api/v1/datasets/download/{self.slug}"

    @property
    def page(self):
        return f"https://www.kaggle.com/datasets/{self.slug}"


SUPPORT = Source(
    "suraj520/customer-support-ticket-dataset",
    "customer_support_tickets.csv",
    "b06a9cde84da65db388bd964d75f88ee1eed96607cf75d0c35f09c3f11bf8bea",
    "99e848c33601eb8863d00f1b8304faa7d1336243b985c2e3ceabe35806149df8",
    1,
    "2023-06-02T01:04:47.673Z",
)
IT = Source(
    "adisongoh/it-service-ticket-classification-dataset",
    "all_tickets_processed_improved_v3.csv",
    "044fdace33fa564e1e60453f2941dafc95539c99878b0d32746950394b9dd4d4",
    "1e6c2508dba84f737ef30f589c2e4f7b2b27a4bbec753e6b5c84183a5f91ed4f",
    1,
    "2024-02-18T17:24:54.847Z",
)

SUPPORT_FIELDS = (
    "Ticket ID",
    "Ticket Type",
    "Ticket Priority",
    "Ticket Channel",
    "Ticket Status",
    "Ticket Description",
    "Ticket Subject",
    "Resolution",
    "First Response Time",
    "Time to Resolution",
    "Customer Satisfaction Rating",
)
IT_FIELDS = ("Document", "Topic_group")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as f:
        tmp = Path(f.name)
        try:
            json.dump(obj, f, indent=2, ensure_ascii=False, allow_nan=False)
            f.write("\n")
            f.close()
            tmp.replace(path)
        finally:
            tmp.unlink(missing_ok=True)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def source_bytes(source: Source) -> bytes:
    path = RAW / source.file
    if not path.is_file():
        raise FileNotFoundError(f"Falta {path.name}. Consulte solution/data/README.md.")
    if path.stat().st_size > MAX_BYTES:
        raise ValueError(f"{path.name} excede o limite de {MAX_BYTES} bytes.")
    data = path.read_bytes()
    if digest(data) != source.sha256:
        raise ValueError(
            f"SHA-256 divergente para {path.name}. Use o snapshot oficial v{source.version}."
        )
    return data


def acquire(source: Source) -> str:
    """Grava somente o CSV esperado, sem extrair caminhos fornecidos pelo ZIP."""
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / source.file
    if path.exists():
        source_bytes(source)
        return "já importado e verificado"
    request = Request(
        source.download,
        headers={
            "User-Agent": "SupportOps-AI/0.1 (public dataset downloader)",
            "Accept": "application/zip",
        },
    )
    with urlopen(request, timeout=40) as response:
        archive = response.read(MAX_BYTES + 1)
    if len(archive) > MAX_BYTES:
        raise ValueError("ZIP excede o tamanho permitido.")
    with ZipFile(io.BytesIO(archive)) as zip_file:
        entry = zip_file.getinfo(source.file)
        if entry.file_size > MAX_BYTES:
            raise ValueError("CSV compactado excede o tamanho permitido.")
        data = zip_file.read(entry)
    if digest(data) != source.sha256:
        raise ValueError("Conteúdo do download diverge do snapshot verificado.")
    # Publica o arquivo completo sem sobrescrever outro original verificado.
    with tempfile.NamedTemporaryFile(dir=RAW, delete=False) as f:
        temp = Path(f.name)
        try:
            f.write(data)
            f.close()
            path.hardlink_to(temp)
        except FileExistsError:
            source_bytes(source)
        finally:
            temp.unlink(missing_ok=True)
    return "baixado e verificado"


def read_csv(data: bytes, required: tuple[str, ...]) -> pd.DataFrame:
    try:
        frame = pd.read_csv(
            io.BytesIO(data), dtype="string", keep_default_na=False, encoding="utf-8-sig"
        )
    except pd.errors.EmptyDataError as exc:
        raise ValueError("CSV vazio.") from exc
    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(missing)}")
    if frame.empty:
        raise ValueError("CSV sem registros.")
    return frame


def load(source: Source, required: tuple[str, ...]):
    data = source_bytes(source)
    frame = read_csv(data, required)
    manifest = {
        "fonte": source.page,
        "api_download": source.download,
        "arquivo": source.file,
        "licenca": "CC0: Public Domain",
        "fonte_licenca": f"https://www.kaggle.com/api/v1/datasets/view/{source.slug}",
        "versao": source.version,
        "publicado_em": source.last_updated,
        "aquisicao_original_em": ACQUISITION,
        "bytes": len(data),
        "sha256": source.sha256,
        "sha256_zip_aquisicao_original": source.zip_sha256,
        "linhas": len(frame),
        "colunas": frame.columns.tolist(),
        "limites": (
            "Sem evento de abertura, esforço ativo ou SLA verificado."
            if source == SUPPORT
            else "Corpus de TI pré-processado, sem origem temporal ou idioma por linha."
        ),
    }
    return frame, manifest
