"""
Shared pytest fixtures.

Points the app at a throwaway database for the whole test session. By default
that's a temp SQLite file (fast, no server). In CI we also run the suite with
``DATABASE_URL`` set to a Postgres service, exercising the exact same code path
to prove the abstraction holds on real Postgres.
"""

import os
import tempfile

import pytest


@pytest.fixture(scope="session", autouse=True)
def _configure_database():
    # If CI hasn't supplied a DATABASE_URL, use an isolated temp SQLite file.
    if not os.environ.get("DATABASE_URL"):
        fd, path = tempfile.mkstemp(suffix=".db", prefix="cc_test_")
        os.close(fd)
        os.environ["COMMAND_CENTER_DB"] = path
        yield
        try:
            os.remove(path)
        except OSError:
            pass
    else:
        yield


@pytest.fixture()
def client():
    """A fresh TestClient (triggers FastAPI startup so the schema exists)."""
    from fastapi.testclient import TestClient

    from app import main

    main.db.init_db()
    with TestClient(main.app) as c:
        yield c


def unique_user(prefix: str = "u") -> str:
    """A unique commander id so tests don't collide on shared state."""
    import uuid

    return f"{prefix}_{uuid.uuid4().hex[:10]}"
