import json
import uuid
from app.routers.generate import get_generator
from app.schemas.generate import GenerateOptions
from app.services.ai import validate_material
from conftest import login, CONTENT, material


def generate(client, auth, **changes):
    body = {
        "content": CONTENT,
        "options": {
            "num_flashcards": 2,
            "num_questions": 1,
            "difficulty": "university",
        },
        "consent_to_provider": True,
        **changes,
    }
    return client.post(
        "/api/generate",
        json=body,
        headers={**auth, "Idempotency-Key": str(uuid.uuid4())},
    )


def test_private_generation_idempotency_save_reopen_rename_delete(client, application):
    auth = login(client)
    key = str(uuid.uuid4())
    body = {
        "content": CONTENT,
        "options": {"num_flashcards": 2, "num_questions": 1},
        "consent_to_provider": True,
    }
    headers = {**auth, "Idempotency-Key": key}
    first = client.post("/api/generate", json=body, headers=headers)
    assert first.status_code == 200, first.text
    again = client.post("/api/generate", json=body, headers=headers)
    assert again.json()["generation_id"] == first.json()["generation_id"]
    assert (
        client.post(
            "/api/generate",
            json={**body, "content": CONTENT + " Changed."},
            headers=headers,
        ).status_code
        == 409
    )
    draft = first.json()["generation_id"]
    assert client.get("/api/generate/" + draft, headers=auth).status_code == 200
    saved = client.post(
        "/api/studysets",
        json={"generation_id": draft, "title": "Exam review"},
        headers=auth,
    )
    assert saved.status_code == 201, saved.text
    item = saved.json()
    assert item["source_text"] == ""
    assert len(item["flashcards"]) == 2
    duplicate = client.post(
        "/api/studysets", json={"generation_id": draft}, headers=auth
    )
    assert duplicate.status_code == 200
    assert duplicate.json()["id"] == item["id"]
    listing = client.get("/api/studysets", headers=auth).json()
    assert listing["total"] == 1
    assert "source_text" not in listing["items"][0]
    renamed = client.patch(
        "/api/studysets/" + item["id"], headers=auth, json={"title": "Final review"}
    )
    assert renamed.status_code == 200
    assert renamed.json()["title"] == "Final review"
    assert len(client.get("/api/studysets/export", headers=auth).json()["sets"]) == 1
    assert (
        client.delete("/api/studysets/" + item["id"], headers=auth).status_code == 204
    )
    assert client.get("/api/studysets/" + item["id"], headers=auth).status_code == 404


def test_cross_account_isolation_and_account_deletion(client, application):
    auth = login(client)
    first = generate(client, auth).json()
    draft = first["generation_id"]
    item = client.post(
        "/api/studysets",
        headers=auth,
        json={"generation_id": draft, "source_text": CONTENT},
    ).json()
    client.cookies.clear()
    other = login(client, "other@example.com")
    item_id = item["id"]
    assert client.get("/api/generate/" + draft, headers=other).status_code == 404
    assert (
        client.post(
            "/api/studysets", headers=other, json={"generation_id": draft}
        ).status_code
        == 404
    )
    for method in ("get", "delete"):
        assert (
            getattr(client, method)(
                "/api/studysets/" + item_id, headers=other
            ).status_code
            == 404
        )
    assert (
        client.patch(
            "/api/studysets/" + item_id, headers=other, json={"title": "Stolen"}
        ).status_code
        == 404
    )
    assert client.get("/api/studysets/export", headers=other).json()["sets"] == []
    response = client.request(
        "DELETE",
        "/api/auth/account",
        headers=auth,
        json={"password": "a strong test passphrase"},
    )
    assert response.status_code == 200
    assert client.get("/api/auth/me", headers=auth).status_code == 401
    assert client.get("/api/studysets/" + item_id, headers=auth).status_code == 401


def test_unauthenticated_generation_and_pdf_are_rejected(client):
    assert generate(client, {}).status_code == 401
    assert (
        client.post(
            "/api/generate/extract-pdf",
            files={"file": ("notes.pdf", b"%PDF-fake", "application/pdf")},
        ).status_code
        == 401
    )


def test_bounds_and_explicit_consent(client):
    auth = login(client)
    for content in ("short", " " * 100, "x" * 12001):
        assert generate(client, auth, content=content).status_code == 422
    for consent in (False, 1, "true", None):
        assert generate(client, auth, consent_to_provider=consent).status_code == 422
    assert (
        generate(
            client, auth, options={"num_flashcards": True, "num_questions": 1}
        ).status_code
        == 422
    )
    assert (
        generate(
            client, auth, options={"num_flashcards": 31, "num_questions": 1}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/generate",
            json={"content": CONTENT, "consent_to_provider": True},
            headers=auth,
        ).status_code
        == 422
    )


def test_failed_provider_returns_sanitized_error_and_job_is_not_rebilled(
    client, application
):
    auth = login(client)
    calls = []

    async def fail(*args):
        calls.append(1)
        raise RuntimeError("private provider secret /tmp/path")

    application.dependency_overrides[get_generator] = lambda: fail
    body = {"content": CONTENT, "consent_to_provider": True}
    headers = {**auth, "Idempotency-Key": str(uuid.uuid4())}
    response = client.post("/api/generate", headers=headers, json=body)
    assert response.status_code == 503, response.text
    assert "private provider secret" not in response.text
    assert client.post("/api/generate", headers=headers, json=body).status_code == 503
    assert len(calls) == 1


def test_missing_provider_does_not_fabricate_material(client, application):
    auth = login(client)
    application.dependency_overrides.pop(get_generator)
    response = generate(client, auth)
    assert response.status_code == 503
    assert "flashcards" not in response.json()


def test_quota_counts_reservations_and_replay_does_not_consume_another(
    client, application
):
    application.state.settings.generation_daily_limit = 1
    auth = login(client)
    assert generate(client, auth).status_code == 200
    assert generate(client, auth).status_code == 429


def test_provider_schema_counts_and_multiple_choice_validation():
    options = GenerateOptions(num_flashcards=2, num_questions=1)
    data = material(options).model_dump()
    assert validate_material(json.dumps(data), options).title
    data["flashcards"] = []
    try:
        validate_material(json.dumps(data), options)
        assert False
    except ValueError:
        pass
    data = material(options).model_dump()
    data["questions"][0] = {
        "question": "Pick",
        "type": "multiple_choice",
        "answer": "not an option",
        "options": ["one", "two"],
    }
    try:
        validate_material(json.dumps(data), options)
        assert False
    except ValueError:
        pass


def test_request_body_limit_and_cors(client):
    response = client.post(
        "/api/auth/login",
        content=b"x" * 70000,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 413
    allowed = client.options(
        "/api/studysets",
        headers={
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert allowed.status_code == 204
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    rejected = client.options(
        "/api/studysets", headers={"Origin": "https://evil.example"}
    )
    assert rejected.status_code == 403
    assert "access-control-allow-origin" not in rejected.headers


def test_global_budget_applies_across_verified_accounts(client, application):
    application.state.settings.generation_global_daily_limit = 1
    first = login(client, "budget-one@example.com")
    assert generate(client, first).status_code == 200
    second = login(client, "budget-two@example.com")
    assert generate(client, second).status_code == 429


def test_account_deletion_cannot_reset_global_provider_budget(client, application):
    from conftest import PASSWORD

    application.state.settings.generation_global_daily_limit = 1
    auth = login(client, "delete-budget@example.com")
    assert generate(client, auth).status_code == 200
    assert (
        client.request(
            "DELETE", "/api/auth/account", headers=auth, json={"password": PASSWORD}
        ).status_code
        == 200
    )
    other = login(client, "new-budget@example.com")
    assert generate(client, other).status_code == 429
