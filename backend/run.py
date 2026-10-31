"""Dev entrypoint: `python run.py`."""
import os
import sys

if __name__ == "__main__":
    try:
        import uvicorn
    except ImportError:
        sys.exit(
            "uvicorn is not installed for this Python.\n"
            "Run: python -m venv .venv && .venv\\Scripts\\python -m pip install -r requirements.txt\n"
            "Then: .venv\\Scripts\\python run.py"
        )

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    print(f"🔥 RoastScribe API starting on http://{host}:{port}  (docs: /docs)", flush=True)
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
