from __future__ import annotations

import os

# Ensure required env defaults for local demo
os.environ.setdefault("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))

try:
    # When executed as a module (python -m ...)
    from .main import app  # type: ignore
except Exception:
    # When executed as a script by file path
    import sys
    sys.path.append(os.path.dirname(__file__))
    import main as _main  # type: ignore
    app = _main.app

if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
