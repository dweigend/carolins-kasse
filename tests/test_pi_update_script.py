"""Smoke tests for the Raspberry Pi update script."""

from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "tools" / "pi_update.sh"
OLD_COMMIT = "1111111111111111111111111111111111111111"
NEW_COMMIT = "2222222222222222222222222222222222222222"


@dataclass(frozen=True)
class PiUpdateRun:
    returncode: int
    stdout: str
    stderr: str
    git_log: str
    systemctl_log: str
    uv_log: str
    python_log: str
    backup_log: str
    event_log: str
    current_commit: str
    worktree_dirty: bool

    @property
    def combined_output(self) -> str:
        return f"{self.stdout}\n{self.stderr}"

    @property
    def events(self) -> list[str]:
        return self.event_log.splitlines()


class PiUpdateScriptTests(unittest.TestCase):
    def test_successful_update_does_not_rollback(self) -> None:
        run = run_pi_update_script()

        self.assertEqual(run.returncode, 0, run.combined_output)
        self.assertEqual(run.current_commit, NEW_COMMIT)
        self.assertNotIn("git reset", run.git_log)
        self.assertIn("systemctl stop carolins-kasse.service", run.systemctl_log)
        self.assertIn("systemctl restart carolins-kasse.service", run.systemctl_log)
        self.assertIn("backup", run.backup_log)
        self.assertIn("Update finished", run.stdout)
        self.assert_events_in_order(
            run,
            [
                "systemctl stop carolins-kasse.service",
                "backup",
                "git pull --ff-only",
                "uv sync --frozen --no-dev",
                "python tools/generate_printables.py",
                "systemctl restart carolins-kasse.service",
            ],
        )

    def test_failure_after_pull_rolls_back_to_previous_commit(self) -> None:
        run = run_pi_update_script(fail_step="uv")

        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(run.current_commit, OLD_COMMIT)
        self.assertIn(f"git reset --hard {OLD_COMMIT}", run.git_log)
        self.assertIn(
            f"Rolling back source checkout from {NEW_COMMIT} to {OLD_COMMIT}.",
            run.stdout,
        )
        self.assertIn("Rollback completed.", run.stdout)
        self.assertIn("systemctl restart carolins-kasse.service", run.systemctl_log)
        self.assertIn("Restarting kiosk service.", run.stdout)
        self.assert_events_in_order(
            run,
            [
                "git pull --ff-only",
                "uv sync --frozen --no-dev",
                f"git reset --hard {OLD_COMMIT}",
                "systemctl restart carolins-kasse.service",
            ],
        )

    def test_noop_pull_failure_resets_dirty_worktree_before_restart(self) -> None:
        run = run_pi_update_script(
            fail_step="printables",
            mutate_worktree_step="barcodes",
            new_commit=OLD_COMMIT,
        )

        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(run.current_commit, OLD_COMMIT)
        self.assertFalse(run.worktree_dirty)
        self.assertIn(f"git reset --hard {OLD_COMMIT}", run.git_log)
        self.assertIn(
            "Checkout is already at "
            f"{OLD_COMMIT}; resetting source checkout to discard post-pull changes.",
            run.stdout,
        )
        self.assertIn("Rollback completed.", run.stdout)
        self.assert_events_in_order(
            run,
            [
                "git pull --ff-only",
                "python tools/generate_barcodes.py",
                "worktree mutated after tools/generate_barcodes.py",
                "python tools/generate_printables.py",
                f"git reset --hard {OLD_COMMIT}",
                "systemctl restart carolins-kasse.service",
            ],
        )

    def test_failed_rollback_leaves_kiosk_stopped_with_clear_log(self) -> None:
        run = run_pi_update_script(fail_step="uv", fail_rollback=True)

        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(run.current_commit, NEW_COMMIT)
        self.assertIn(f"git reset --hard {OLD_COMMIT}", run.git_log)
        self.assertIn("Rollback command failed.", run.stderr)
        self.assertIn(
            "Leaving kiosk service stopped so it does not start a half-validated "
            "checkout.",
            run.stderr,
        )
        self.assertIn("systemctl stop carolins-kasse.service", run.systemctl_log)
        self.assertNotIn("systemctl restart carolins-kasse.service", run.systemctl_log)
        self.assertNotIn("systemctl restart carolins-kasse.service", run.events)

    def assert_events_in_order(
        self, run: PiUpdateRun, expected_events: list[str]
    ) -> None:
        start_at = 0
        for expected_event in expected_events:
            try:
                event_index = run.events.index(expected_event, start_at)
            except ValueError:
                self.fail(
                    f"Expected event {expected_event!r} after index {start_at}; "
                    f"events were: {run.events!r}"
                )
            start_at = event_index + 1


def run_pi_update_script(
    *,
    fail_step: str | None = None,
    fail_rollback: bool = False,
    mutate_worktree_step: str | None = None,
    new_commit: str = NEW_COMMIT,
) -> PiUpdateRun:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        fake_bin = temp_root / "bin"
        app_dir = temp_root / "app"
        tools_dir = app_dir / "tools"
        venv_bin = app_dir / ".venv" / "bin"
        state_dir = temp_root / "state"
        log_dir = temp_root / "logs"

        fake_bin.mkdir()
        tools_dir.mkdir(parents=True)
        venv_bin.mkdir(parents=True)
        state_dir.mkdir()
        log_dir.mkdir()
        (state_dir / "current_commit").write_text(OLD_COMMIT)

        write_fake_commands(fake_bin)
        write_fake_app_commands(tools_dir, venv_bin)

        env = os.environ.copy()
        env.update(
            {
                "PATH": f"{fake_bin}{os.pathsep}{env['PATH']}",
                "CAROLINS_KASSE_USER": "kasse",
                "CAROLINS_KASSE_APP_DIR": str(app_dir),
                "CAROLINS_KASSE_DB_PATH": str(temp_root / "kasse.db"),
                "CAROLINS_KASSE_BACKUP_DIR": str(temp_root / "backups"),
                "CAROLINS_KASSE_UV_BIN": str(fake_bin / "uv"),
                "FAKE_LOG_DIR": str(log_dir),
                "FAKE_STATE_DIR": str(state_dir),
                "FAKE_NEW_COMMIT": new_commit,
                "FAIL_STEP": fail_step or "",
                "FAIL_ROLLBACK": "1" if fail_rollback else "",
                "MUTATE_WORKTREE_STEP": mutate_worktree_step or "",
            }
        )

        result = subprocess.run(
            ["bash", str(SCRIPT_PATH)],
            cwd=REPO_ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )

        return PiUpdateRun(
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            git_log=read_log(log_dir / "git.log"),
            systemctl_log=read_log(log_dir / "systemctl.log"),
            uv_log=read_log(log_dir / "uv.log"),
            python_log=read_log(log_dir / "python.log"),
            backup_log=read_log(log_dir / "backup.log"),
            event_log=read_log(log_dir / "events.log"),
            current_commit=(state_dir / "current_commit").read_text().strip(),
            worktree_dirty=(state_dir / "worktree_dirty").exists(),
        )


def write_fake_commands(fake_bin: Path) -> None:
    write_executable(
        fake_bin / "id",
        """
        #!/bin/bash
        set -euo pipefail
        if [ "${1:-}" = "-u" ]; then
            echo "0"
            exit 0
        fi
        /usr/bin/id "$@"
        """,
    )
    write_executable(
        fake_bin / "systemctl",
        """
        #!/bin/bash
        set -euo pipefail
        echo "systemctl $*" >> "${FAKE_LOG_DIR}/systemctl.log"
        echo "systemctl $*" >> "${FAKE_LOG_DIR}/events.log"
        """,
    )
    write_executable(
        fake_bin / "runuser",
        """
        #!/bin/bash
        set -euo pipefail
        if [ "${1:-}" = "-u" ]; then
            shift 2
        fi
        if [ "${1:-}" = "--" ]; then
            shift
        fi
        exec "$@"
        """,
    )
    write_executable(
        fake_bin / "git",
        """
        #!/bin/bash
        set -euo pipefail
        if [ "${1:-}" = "-C" ]; then
            shift 2
        fi

        command="${1:-}"
        shift || true
        state_file="${FAKE_STATE_DIR}/current_commit"

        case "${command}" in
            status)
                if [ -n "${FAKE_GIT_DIRTY:-}" ]; then
                    echo " M tools/pi_update.sh"
                elif [ -f "${FAKE_STATE_DIR}/worktree_dirty" ]; then
                    echo " M generated-file"
                fi
                ;;
            rev-parse)
                if [ "${1:-}" = "HEAD" ]; then
                    cat "${state_file}"
                fi
                ;;
            fetch)
                echo "git fetch $*" >> "${FAKE_LOG_DIR}/git.log"
                echo "git fetch $*" >> "${FAKE_LOG_DIR}/events.log"
                ;;
            pull)
                echo "git pull $*" >> "${FAKE_LOG_DIR}/git.log"
                echo "git pull $*" >> "${FAKE_LOG_DIR}/events.log"
                echo "${FAKE_NEW_COMMIT}" > "${state_file}"
                ;;
            reset)
                echo "git reset $*" >> "${FAKE_LOG_DIR}/git.log"
                echo "git reset $*" >> "${FAKE_LOG_DIR}/events.log"
                if [ -n "${FAIL_ROLLBACK:-}" ]; then
                    exit 77
                fi
                if [ "${1:-}" = "--hard" ]; then
                    echo "${2:-}" > "${state_file}"
                    rm -f "${FAKE_STATE_DIR}/worktree_dirty"
                fi
                ;;
            *)
                echo "Unexpected git command: ${command}" >&2
                exit 2
                ;;
        esac
        """,
    )
    write_executable(
        fake_bin / "uv",
        """
        #!/bin/bash
        set -euo pipefail
        echo "uv $*" >> "${FAKE_LOG_DIR}/uv.log"
        echo "uv $*" >> "${FAKE_LOG_DIR}/events.log"
        if [ "${FAIL_STEP:-}" = "uv" ]; then
            exit 42
        fi
        """,
    )
    write_executable(
        fake_bin / "date",
        """
        #!/bin/bash
        set -euo pipefail
        echo "2026-07-04T12:00:00+02:00"
        """,
    )


def write_fake_app_commands(tools_dir: Path, venv_bin: Path) -> None:
    write_executable(
        tools_dir / "pi_backup.sh",
        """
        #!/bin/bash
        set -euo pipefail
        echo "backup" >> "${FAKE_LOG_DIR}/backup.log"
        echo "backup" >> "${FAKE_LOG_DIR}/events.log"
        """,
    )
    write_executable(
        venv_bin / "python",
        """
        #!/bin/bash
        set -euo pipefail
        echo "python $*" >> "${FAKE_LOG_DIR}/python.log"
        echo "python $*" >> "${FAKE_LOG_DIR}/events.log"
        case "$*" in
            "-m compileall src tools")
                if [ "${FAIL_STEP:-}" = "compileall" ]; then
                    exit 43
                fi
                ;;
            "tools/seed_database.py")
                if [ "${FAIL_STEP:-}" = "seed" ]; then
                    exit 44
                fi
                if [ "${FAIL_STEP:-}" = "seed-refusal" ]; then
                    exit 1
                fi
                ;;
            "tools/generate_barcodes.py")
                if [ "${FAIL_STEP:-}" = "barcodes" ]; then
                    exit 45
                fi
                if [ "${MUTATE_WORKTREE_STEP:-}" = "barcodes" ]; then
                    echo "dirty" > "${FAKE_STATE_DIR}/worktree_dirty"
                    echo "worktree mutated after $*" >> "${FAKE_LOG_DIR}/events.log"
                fi
                ;;
            "tools/generate_printables.py")
                if [ "${FAIL_STEP:-}" = "printables" ]; then
                    exit 46
                fi
                ;;
        esac
        """,
    )


def write_executable(path: Path, content: str) -> None:
    path.write_text(textwrap.dedent(content).lstrip())
    path.chmod(0o755)


def read_log(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text()


if __name__ == "__main__":
    unittest.main()
