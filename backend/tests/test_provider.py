import asyncio
from types import SimpleNamespace
import pytest
from app.services import ai
from app.schemas.generate import GenerateOptions
from app.config import Settings
from conftest import material

OPTIONS = GenerateOptions(num_flashcards=2, num_questions=1)


def test_adapter_retries_invalid_structure_once(monkeypatch):
    calls = []

    class Client:
        def __init__(self, **kwargs):
            self.messages = self
            assert kwargs["max_retries"] == 0

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def create(self, **kwargs):
            calls.append(kwargs)
            raw = "not json" if len(calls) == 1 else material(OPTIONS).model_dump_json()
            return SimpleNamespace(
                stop_reason="end_turn", content=[SimpleNamespace(type="text", text=raw)]
            )

    monkeypatch.setattr(ai.anthropic, "AsyncAnthropic", Client)
    config = SimpleNamespace(anthropic_api_key="test-key", anthropic_model="test-model")
    result = asyncio.run(
        ai.generate_study_set("Academic source material", OPTIONS, config)
    )
    assert len(result.flashcards) == 2
    assert len(calls) == 2
    assert calls[0]["model"] == "test-model"
    assert "untrusted SOURCE DATA" in calls[0]["system"]


def test_truncated_or_refused_output_never_becomes_fake_material(monkeypatch):
    calls = []

    class Client:
        def __init__(self, **kwargs):
            self.messages = self

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def create(self, **kwargs):
            calls.append(1)
            return SimpleNamespace(stop_reason="max_tokens", content=[])

    monkeypatch.setattr(ai.anthropic, "AsyncAnthropic", Client)
    with pytest.raises(ai.GenerationUnavailable):
        asyncio.run(
            ai.generate_study_set(
                "Academic source",
                OPTIONS,
                SimpleNamespace(anthropic_api_key="test", anthropic_model="test-model"),
            )
        )
    assert len(calls) == 2


@pytest.mark.parametrize(
    "override",
    [
        {"secret_key": "short"},
        {
            "secret_key": "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
        },
        {"app_env": "production", "database_url": "sqlite+aiosqlite:///bad.sqlite"},
        {"anthropic_api_key": "test-key", "anthropic_model": ""},
        {"proxy_token": "bad"},
    ],
)
def test_unsafe_configuration_fails_closed(override):
    with pytest.raises(ValueError):
        Settings(
            secret_key="safe-test-secret" * 4,
            **{k: v for k, v in override.items() if k != "secret_key"},
        ) if "secret_key" not in override else Settings(**override)


def test_provider_database_urls_are_normalized():
    config = Settings(
        secret_key="safe-test-secret" * 4,
        database_url="postgresql://user:pass@db/studymind?sslmode=require",
    )
    assert (
        config.database_url == "postgresql+asyncpg://user:pass@db/studymind?ssl=require"
    )
