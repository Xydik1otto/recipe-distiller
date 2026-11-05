"""Console entry point: `recipe-distiller` starts the local server.

Installed by `pip install -e .` (see INSTALL.md); equivalent to
`python -m uvicorn app.main:app`.
"""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="recipe-distiller",
        description="Run the local Recipe Distiller server (URL → just the recipe).",
    )
    parser.add_argument("--host", default="127.0.0.1", help="bind address (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="port (default 8000)")
    args = parser.parse_args()
    import uvicorn

    uvicorn.run("app.main:app", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
