"""Test helpers for importing database modules against a temporary DB path."""

from collections.abc import Iterator
from contextlib import contextmanager
import importlib
import os
from pathlib import Path
import sys
from types import ModuleType


DATABASE_ENV_VAR = "CAROLINS_KASSE_DB_PATH"
DATABASE_MODULES = ("tools.seed_database", "src.utils.database")


@contextmanager
def isolated_database_module(db_path: Path) -> Iterator[ModuleType]:
    """Import the database module with DB_PATH bound to a temporary file."""
    previous_env_value = os.environ.get(DATABASE_ENV_VAR)
    previous_sys_path = sys.path.copy()
    previous_modules = {
        module_name: sys.modules[module_name]
        for module_name in DATABASE_MODULES
        if module_name in sys.modules
    }

    os.environ[DATABASE_ENV_VAR] = str(db_path)
    for module_name in DATABASE_MODULES:
        sys.modules.pop(module_name, None)

    try:
        database = importlib.import_module("src.utils.database")
        if Path(database.DB_PATH) != db_path:
            raise AssertionError(f"Expected temp DB path, got {database.DB_PATH}")
        yield database
    finally:
        for module_name in DATABASE_MODULES:
            sys.modules.pop(module_name, None)

        if previous_env_value is None:
            os.environ.pop(DATABASE_ENV_VAR, None)
        else:
            os.environ[DATABASE_ENV_VAR] = previous_env_value

        sys.path[:] = previous_sys_path
        sys.modules.update(previous_modules)
