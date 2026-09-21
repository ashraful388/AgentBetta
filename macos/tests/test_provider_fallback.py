"""Provider fallback, transient retry and error surfacing."""

import pytest

from agentbetta.core.models import ProviderResponse
from agentbetta.providers.base import BaseProvider, LLMRequest
from agentbetta.providers.fallback import FallbackProvider
from agentbetta.providers.http import ProviderHTTPError
from agentbetta.validation.basic import BasicValidator


class _Boom(BaseProvider):
    name = "boom"
    is_cloud = False
    model = "boom"

    def chat(self, request):
        raise RuntimeError("provider exploded")


class _Ok(BaseProvider):
    name = "ok"
    is_cloud = False
    model = "ok"

    def chat(self, request):
        return ProviderResponse("ok")


def test_fallback_used_when_primary_fails():
    provider = FallbackProvider(_Boom(), [_Ok()])
    response = provider.chat(LLMRequest(messages=[]))
    assert response.text == "ok"
    assert provider.used_fallback is True
    assert provider.last_provider_name == "ok"


def test_fallback_raises_when_all_fail():
    provider = FallbackProvider(_Boom(), [_Boom()])
    with pytest.raises(RuntimeError):
        provider.chat(LLMRequest(messages=[]))


def test_result_markdown_discloses_fallback_model():
    from agentbetta.desktop.widgets.report import build_result_markdown

    text = build_result_markdown(
        {
            "output": "done",
            "verified": True,
            "attempts": 1,
            "provider": "ollama",
            "model_id": "qwen3:1.7b",
            "requested_model": "deepseek-v4.1-flash",
            "used_fallback": True,
        }
    )
    assert "Fallback model used" in text
    assert "deepseek-v4.1-flash" in text
    assert "qwen3:1.7b" in text


def test_http_error_transient_classification():
    assert ProviderHTTPError("HTTP 522: x", code=522).transient
    assert ProviderHTTPError("HTTP 503: x", code=503).transient
    assert not ProviderHTTPError("HTTP 400: x", code=400).transient


def test_provider_error_message_is_surfaced():
    verification = BasicValidator().verify(
        ProviderResponse(
            "",
            raw={
                "failure": "provider_error",
                "message": "ProviderHTTPError: HTTP 400: credit insufficient balance",
            },
        )
    )
    assert "credit insufficient balance" in verification.reason
    assert verification.evidence.get("provider_message")
