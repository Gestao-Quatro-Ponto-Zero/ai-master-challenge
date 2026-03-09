from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def terminate_process(proc: subprocess.Popen[Any], timeout: float = 5.0) -> None:
    if proc.poll() is not None:
        return

    proc.terminate()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    frontend_app = project_root / "frontend" / "app.py"

    python = sys.executable

    api_cmd = [
        python,
        "-m",
        "uvicorn",
        "g4sales.api:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--reload",
    ]
    front_cmd = [
        python,
        "-m",
        "streamlit",
        "run",
        str(frontend_app),
        "--server.headless",
        "true",
    ]

    api_proc = subprocess.Popen(api_cmd, cwd=project_root)
    front_proc = subprocess.Popen(front_cmd, cwd=project_root)

    print("API: http://127.0.0.1:8000")
    print("Front: http://127.0.0.1:8501")
    print("Pressione Ctrl+C para encerrar os dois processos.")

    try:
        while True:
            if api_proc.poll() is not None:
                raise RuntimeError("Processo da API foi encerrado inesperadamente.")
            if front_proc.poll() is not None:
                raise RuntimeError(
                    "Processo do frontend foi encerrado inesperadamente."
                )
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        terminate_process(front_proc)
        terminate_process(api_proc)


if __name__ == "__main__":
    main()
