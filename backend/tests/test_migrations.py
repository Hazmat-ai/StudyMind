import os
import subprocess
import sys
from pathlib import Path
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app


def test_alembic_upgrade_and_schema_match_models(tmp_path):
    root = Path(__file__).resolve().parents[2]
    url = f"sqlite+aiosqlite:///{tmp_path}/migrated.sqlite"
    env = {
        **os.environ,
        "SECRET_KEY": "migration-test-only-secret" * 3,
        "DATABASE_URL": url,
        "APP_ENV": "development",
    }
    command = [sys.executable, "-m", "alembic", "-c", str(root / "backend/alembic.ini")]
    subprocess.run(
        command + ["upgrade", "head"],
        cwd=root,
        env=env,
        check=True,
        capture_output=True,
    )
    checked = subprocess.run(
        command + ["check"], cwd=root, env=env, capture_output=True, text=True
    )
    assert checked.returncode == 0, checked.stdout + checked.stderr
    config = Settings(
        secret_key="migration-test-only-secret" * 3,
        database_url=url,
        app_env="testing",
        require_email_verification=False,
    )
    with TestClient(create_app(config), base_url="http://localhost:8000") as client:
        assert client.get("/api/health").status_code == 200
