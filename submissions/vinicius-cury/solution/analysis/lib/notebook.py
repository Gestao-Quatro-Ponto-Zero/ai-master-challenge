"""
Notebook creation and execution helper.
Allows Claude Code to create and run notebooks entirely from the command line.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Union

ANALYSIS_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ANALYSIS_DIR / "output"
VENV_PYTHON = ANALYSIS_DIR / ".venv" / "bin" / "python3"


def create_notebook(name: str, cells: list[dict]) -> Path:
    """
    Create an .ipynb file programmatically.

    cells: list of {"type": "code"|"markdown", "source": "..."}
    Returns the path to the created notebook.
    """
    notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "OptiFlow (Python)",
                "language": "python",
                "name": "optiflow",
            },
            "language_info": {
                "name": "python",
                "version": "3.9.6",
            },
        },
        "cells": [],
    }

    for i, cell in enumerate(cells):
        nb_cell = {
            "id": f"cell-{i}",
            "cell_type": cell["type"],
            "metadata": {},
            "source": cell["source"] if isinstance(cell["source"], list) else [cell["source"]],
        }
        if cell["type"] == "code":
            nb_cell["execution_count"] = None
            nb_cell["outputs"] = []
        notebook["cells"].append(nb_cell)

    path = ANALYSIS_DIR / f"{name}.ipynb"
    with open(path, "w") as f:
        json.dump(notebook, f, indent=1)

    return path


def add_cell(notebook_path: str | Path, cell_type: str, content: str) -> None:
    """Append a cell to an existing notebook."""
    path = Path(notebook_path)
    with open(path) as f:
        nb = json.load(f)

    cell_id = f"cell-{len(nb['cells'])}"
    cell = {
        "id": cell_id,
        "cell_type": cell_type,
        "metadata": {},
        "source": [content],
    }
    if cell_type == "code":
        cell["execution_count"] = None
        cell["outputs"] = []
    nb["cells"].append(cell)

    with open(path, "w") as f:
        json.dump(nb, f, indent=1)


def execute_notebook(notebook_path: str | Path, parameters: dict = None) -> Path:
    """
    Execute a notebook via papermill.
    Returns the path to the output notebook.
    """
    path = Path(notebook_path)
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / f"{path.stem}_output.ipynb"

    cmd = [
        str(VENV_PYTHON), "-m", "papermill",
        str(path), str(output_path),
        "--kernel", "optiflow",
        "--log-output",
    ]

    if parameters:
        for key, value in parameters.items():
            cmd.extend(["-p", key, str(value)])

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"STDERR:\n{result.stderr}")
        raise RuntimeError(f"Notebook execution failed:\n{result.stderr[-500:]}")

    if result.stdout:
        print(result.stdout[-1000:])

    return output_path


def read_output(notebook_path: str | Path, cell_index: int = None) -> list[dict]:
    """
    Read outputs from an executed notebook.
    If cell_index is provided, returns outputs for that cell only.
    Otherwise returns all cell outputs.
    """
    path = Path(notebook_path)
    with open(path) as f:
        nb = json.load(f)

    results = []
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "code":
            continue
        if cell_index is not None and i != cell_index:
            continue

        outputs = []
        for output in cell.get("outputs", []):
            if output.get("output_type") == "stream":
                outputs.append({"type": "text", "text": "".join(output.get("text", []))})
            elif output.get("output_type") in ("execute_result", "display_data"):
                data = output.get("data", {})
                if "text/plain" in data:
                    outputs.append({"type": "text", "text": "".join(data["text/plain"])})
                if "text/html" in data:
                    outputs.append({"type": "html", "text": "".join(data["text/html"])})
                if "image/png" in data:
                    outputs.append({"type": "image", "data": data["image/png"]})
            elif output.get("output_type") == "error":
                outputs.append({
                    "type": "error",
                    "ename": output.get("ename", ""),
                    "evalue": output.get("evalue", ""),
                    "traceback": output.get("traceback", []),
                })

        results.append({"cell_index": i, "source": "".join(cell["source"]), "outputs": outputs})

    return results
