"""Inspect training state without fitting or deleting existing artifacts."""

import json

from .artifacts import BUNDLE, load_metadata


def reuse_completed(root):
    directory = root / BUNDLE
    attempt_path = directory / "training-attempt.json"
    if not attempt_path.exists():
        if directory.exists() and any(directory.iterdir()):
            raise ValueError("Há artefatos sem registro de treino. Preserve a pasta e confira sua origem; não será sobrescrita.")
        return False
    try:
        attempt = json.loads(attempt_path.read_text())
    except (OSError, ValueError) as error:
        raise ValueError("Registro de treino inválido. Preserve os arquivos e confira a tentativa anterior.") from error
    protocol = json.loads((root / "data/evaluation-protocol.json").read_text())
    expected = [item["id"] for item in protocol["model_selection"]["candidates"]]
    if (attempt.get("state") != "completed" or attempt.get("fits_started") != expected or
            attempt.get("final_test_predictions") != 0):
        raise ValueError("Existe um treino incompleto ou incompatível. Não será repetido automaticamente; confira training-attempt.json antes de continuar.")
    try:
        load_metadata(root)
    except ValueError as error:
        if str(error) != "No quality-qualified model":
            raise ValueError("O treino terminou, mas seus artefatos/configuração estão incompatíveis. Preserve-os para revisão; não haverá novo ajuste automático.") from error
        print("Treino já concluído sem modelo elegível. Mantido o encaminhamento para revisão humana.")
    except (OSError, KeyError, TypeError) as error:
        raise ValueError("O treino terminou, mas faltam artefatos válidos. Preserve a tentativa anterior; não será sobrescrita.") from error
    else:
        print("Treino já concluído e validado. Reutilizando os modelos existentes, sem novo ajuste.")
    return True
