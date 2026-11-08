"""lead-api: sobe o servidor (uvicorn)."""
from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> int:
    import uvicorn

    p = argparse.ArgumentParser(prog="lead-api")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    args = p.parse_args(argv)
    uvicorn.run("lead_api.main:create_app", factory=True, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
