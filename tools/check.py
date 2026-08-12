#!/usr/bin/env python3
"""Run the complete local quality check."""

import subprocess
import sys

CHECKS = (
    ("ruff", "format", "--check", "."),
    ("ruff", "check", "."),
    ("ty", "check", "--respect-ignore-files"),
    (
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "tests",
        "-p",
        "test_*.py",
    ),
)


def main() -> int:
    """Run each check in order and return the first failing exit code."""
    for command in CHECKS:
        print(f"\n==> {' '.join(command)}", flush=True)
        completed_process = subprocess.run(command, check=False)
        if completed_process.returncode:
            return completed_process.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
