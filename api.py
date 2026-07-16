"""Churn Platform — FastAPI entry point (SPEC-10.3).

Uso:
    uvicorn api:app --host 0.0.0.0 --port 8080
    python api.py
"""

from __future__ import annotations

import os

from churn_platform.api import create_app

output_dir = os.getenv("OUTPUT_DIR", "output")
app = create_app(output_dir=output_dir)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=int(os.getenv("PORT", "8080")), reload=True)
