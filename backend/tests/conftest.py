import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.routers.generate import get_generator
from app.schemas.generate import StudyMaterial

ORIGIN = "http://localhost:5173"
PASSWORD = "a strong test passphrase"
CONTENT = "Relational databases organize data into tables. Primary keys identify rows and foreign keys express references. Normalization reduces redundancy."


def material(options):
    return StudyMaterial(
        title="Relational databases",
        summary="Tables organize records. Keys connect related records.",
        flashcards=[
            {
                "term": f"Key {i + 1}",
                "definition": "A key identifies or references a record.",
            }
            for i in range(options.num_flashcards)
        ],
        questions=[
            {
                "question": f"What is a key? ({i + 1})",
                "answer": "It identifies a record.",
                "type": "short_answer",
                "options": [],
            }
            for i in range(options.num_questions)
        ],
        concepts=[{"term": "Keys", "related": ["Tables"]}],
    )


@pytest.fixture(autouse=True)
def isolate_credentials_and_block_external_services(monkeypatch):
    # Local developer .env files must never turn a QA run into paid AI or real mail.
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    for field in Settings.model_fields:
        monkeypatch.delenv(field.upper(), raising=False)

    def blocked(*args, **kwargs):
        raise AssertionError("External AI/email is disabled in automated tests")

    monkeypatch.setattr("anthropic.AsyncAnthropic", blocked)
    monkeypatch.setattr("smtplib.SMTP", blocked)
    monkeypatch.setattr("smtplib.SMTP_SSL", blocked)


@pytest.fixture
def application(tmp_path):
    settings = Settings(
        app_env="testing",
        secret_key="s" * 64,
        database_url=f"sqlite+aiosqlite:///{tmp_path}/test.sqlite",
        require_email_verification=False,
        test_auto_schema=True,
    )
    app = create_app(settings)

    async def generator(content, options, config):
        return material(options)

    app.dependency_overrides[get_generator] = lambda: generator
    return app


@pytest.fixture
def client(application):
    with TestClient(
        application, base_url="http://localhost:8000", headers={"Origin": ORIGIN}
    ) as client:
        yield client


def csrf(client):
    return {"X-CSRF-Token": client.get("/api/auth/csrf").json()["csrf_token"]}


def login(client, email="student@example.com", password=PASSWORD):
    nonce = csrf(client)
    registration = client.post(
        "/api/auth/register", json={"email": email, "password": password}, headers=nonce
    )
    assert registration.status_code == 202, registration.text
    response = client.post(
        "/api/auth/login", json={"email": email, "password": password}, headers=nonce
    )
    assert response.status_code == 200, response.text
    return {"Authorization": "Bearer " + response.json()["access_token"]}
