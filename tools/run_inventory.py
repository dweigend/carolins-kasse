"""Run the loopback-only product inventory workspace."""

import argparse
import os
import sys
from pathlib import Path

import uvicorn

sys.path.insert(0, str(Path(__file__).parent.parent))


INVENTORY_MODE_ENV_VAR = "CAROLINS_KASSE_INVENTORY_MODE"
LOOPBACK_HOST = "127.0.0.1"


def main() -> None:
    """Start the admin app in explicit local inventory mode."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    os.environ[INVENTORY_MODE_ENV_VAR] = "1"
    uvicorn.run(
        "src.admin.server:app",
        host=LOOPBACK_HOST,
        port=args.port,
    )


if __name__ == "__main__":
    main()
