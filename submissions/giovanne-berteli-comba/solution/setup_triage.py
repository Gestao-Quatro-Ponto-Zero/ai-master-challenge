#!/usr/bin/env python3
"""Prepare verified data, frozen membership and a reusable training bundle."""

import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from triage.artifacts import ROOT, check_environment, sha256


def run_step(name, script):
    print(name, flush=True)
    result = subprocess.run([sys.executable, "-I", str(ROOT / script)], cwd=ROOT, capture_output=True, text=True)
    log = ROOT / ".runtime/setup.log"
    with log.open("a") as handle:
        handle.write(f"\n{script}\n{result.stdout}\n{result.stderr}")
    if result.returncode:
        raise ValueError(f"Etapa não concluída: {name}. Consulte {log}. Verifique conexão/permissões e os arquivos indicados; nenhuma tentativa anterior será apagada.")
    if result.stdout:
        print(result.stdout.rstrip(), flush=True)


def prepare():
    if sys.version_info[:3] != (3, 12, 3):
        raise ValueError("É necessário Python 3.12.3. Execute bash run.sh para preparar o runtime local.")
    check_environment(ROOT)
    (ROOT / ".runtime").mkdir(exist_ok=True)
    run_step("[2/4] Conferindo os dados versionados…", "solution/acquire_data.py")
    manifest = json.loads((ROOT / "data/evaluation-manifest.json").read_text())
    for name, expected in manifest["input_sha256"].items():
        if sha256(ROOT / name) != expected:
            raise ValueError(f"Preparação V00 incompatível: {name}. Os parâmetros congelados não serão alterados automaticamente.")
    membership = ROOT / manifest["membership"]["path"]
    if membership.exists():
        if sha256(membership) != manifest["membership"]["sha256"]:
            raise ValueError("Membership local alterada. Não será sobrescrita; confira os dados da tentativa anterior.")
        print("[3/4] Separação de dados já válida; reutilizando.", flush=True)
    else:
        run_step("[3/4] Preparando os conjuntos congelados…", "solution/prepare_evaluation.py")
        if sha256(membership) != manifest["membership"]["sha256"]:
            raise ValueError("Membership regenerada difere da versão congelada.")
    run_step("[4/4] Preparando ou reutilizando o modelo…", "solution/train_triage.py")
    print("Preparação concluída. O teste final permanece reservado.", flush=True)


if __name__ == "__main__":
    try:
        prepare()
    except (OSError, ValueError, KeyError) as error:
        print(f"Não foi possível iniciar: {error}", file=sys.stderr)
        sys.exit(1)
