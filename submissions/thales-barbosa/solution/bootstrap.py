# -*- coding: utf-8 -*-
"""Prepara todos os artefatos necessários para executar o protótipo PAUTA.

Uso:
    python bootstrap.py          # gera somente o que estiver faltando
    python bootstrap.py --check  # apenas verifica a instalação

Ordem intencional: dados -> embeddings EN -> baseline/metrics -> embeddings
multilíngues -> modelo servido multilíngue. O último passo não pode vir antes
de ``train_models.py``, pois o treino do baseline sobrescreve os artefatos
servidos.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROCESSED = ROOT / "data" / "processed"
MODELS = ROOT / "models"

PROCESSED_FILES = (
    PROCESSED / "tickets_features.parquet",
    PROCESSED / "it_tickets_clean.parquet",
)

FINAL_MODEL_FILES = (
    MODELS / "classifier.joblib",
    MODELS / "faiss.index",
    MODELS / "corpus.parquet",
    MODELS / "metadata.json",
    MODELS / "metrics.json",
    MODELS / "metrics_ml.json",
)


def _configure_console() -> None:
    """Evita UnicodeEncodeError nos consoles cp1252 do Windows."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def _run(script: str) -> None:
    env = os.environ.copy()
    env.update({"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})
    print(f"\n→ {Path(sys.executable).name} {script}", flush=True)
    completed = subprocess.run(
        [sys.executable, str(ROOT / script)],
        cwd=ROOT,
        env=env,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(f"{script} terminou com código {completed.returncode}")


def _read_progress(marker: Path) -> tuple[int, int]:
    if not marker.exists():
        return 0, 0
    try:
        state = json.loads(marker.read_text(encoding="utf-8"))
        return int(state.get("done", 0)), int(state.get("total", 0))
    except (OSError, ValueError, TypeError):
        return 0, 0


def _progress_complete(marker: Path, output: Path) -> bool:
    done, total = _read_progress(marker)
    return output.exists() and total > 0 and done >= total


def _run_until_complete(script: str, marker: Path, output: Path) -> None:
    previous = -1
    while not _progress_complete(marker, output):
        before, _ = _read_progress(marker)
        _run(script)
        after, total = _read_progress(marker)
        print(f"  progresso confirmado: {after:,}/{total:,}", flush=True)
        if after <= max(before, previous) and not _progress_complete(marker, output):
            raise RuntimeError(
                f"{script} não avançou. Verifique conexão, espaço em disco e logs acima."
            )
        previous = after


def _served_model_is_multilingual(metadata: Path) -> bool:
    if not metadata.exists():
        return False
    try:
        meta = json.loads(metadata.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return False
    return (
        meta.get("classifier_type") == "embed_logreg"
        and "multilingual" in str(meta.get("embedder", "")).lower()
    )


def _validation_errors() -> list[str]:
    errors = [f"ausente: {p.relative_to(ROOT)}" for p in (*PROCESSED_FILES, *FINAL_MODEL_FILES)
              if not p.exists()]
    if not _progress_complete(MODELS / "embed_progress.json", MODELS / "embeddings_d2.npy"):
        errors.append("embeddings EN incompletos")
    if not _progress_complete(
        MODELS / "embed_progress_ml.json", MODELS / "embeddings_d2_ml.npy"
    ):
        errors.append("embeddings multilíngues incompletos")
    if (MODELS / "metadata.json").exists() and not _served_model_is_multilingual(
        MODELS / "metadata.json"
    ):
        errors.append("modelo servido não é o multilíngue final")
    return errors


def check() -> bool:
    errors = _validation_errors()
    if errors:
        print("Bootstrap incompleto:")
        for error in errors:
            print(f"  - {error}")
        return False
    print("Bootstrap OK — dados processados e modelo multilíngue prontos.")
    print("Próximo passo: python app.py  →  http://localhost:8502")
    return True


def bootstrap() -> None:
    if check():
        return

    if not all(p.exists() for p in PROCESSED_FILES):
        _run("src/data_prep.py")

    _run_until_complete(
        "src/embed_corpus.py",
        MODELS / "embed_progress.json",
        MODELS / "embeddings_d2.npy",
    )

    # Gera métricas comparativas e corpus; também cria o baseline inglês.
    if not (MODELS / "metrics.json").exists() or not (MODELS / "corpus.parquet").exists():
        _run("src/train_models.py")

    _run_until_complete(
        "src/embed_corpus_ml.py",
        MODELS / "embed_progress_ml.json",
        MODELS / "embeddings_d2_ml.npy",
    )

    # Sempre por último: substitui os artefatos servidos pelo modelo multilíngue.
    if not _served_model_is_multilingual(MODELS / "metadata.json"):
        _run("src/train_multilingual.py")

    if not check():
        raise RuntimeError("bootstrap terminou sem produzir todos os artefatos esperados")


def main() -> int:
    _configure_console()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="não gera arquivos; apenas verifica")
    args = parser.parse_args()
    if args.check:
        return 0 if check() else 1
    bootstrap()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
