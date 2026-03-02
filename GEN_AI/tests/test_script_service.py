"""Tests for backend.services.script_service — OpenAI-based ScriptService."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.services.script_service import ScriptService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def service_no_key(monkeypatch) -> ScriptService:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    return ScriptService()


@pytest.fixture
def service_with_key(monkeypatch) -> ScriptService:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-12345")
    return ScriptService()


# ---------------------------------------------------------------------------
# Fallback (no API key)
# ---------------------------------------------------------------------------


class TestFallbackScript:
    @pytest.mark.asyncio
    async def test_returns_fallback_when_no_key(self, service_no_key):
        result = await service_no_key.generate_script("golden retriever")
        assert "script" in result
        assert "captions" in result
        assert "image_prompt" in result

    @pytest.mark.asyncio
    async def test_fallback_contains_topic(self, service_no_key):
        result = await service_no_key.generate_script("persian cat")
        combined = json.dumps(result)
        assert "persian cat" in combined

    @pytest.mark.asyncio
    async def test_fallback_captions_list(self, service_no_key):
        result = await service_no_key.generate_script("dog")
        assert isinstance(result["captions"], list)
        assert len(result["captions"]) > 0

    @pytest.mark.asyncio
    async def test_fallback_caption_structure(self, service_no_key):
        result = await service_no_key.generate_script("cat")
        for cap in result["captions"]:
            assert "text" in cap
            assert "start" in cap
            assert "end" in cap
            assert cap["end"] >= cap["start"]


# ---------------------------------------------------------------------------
# With API key — mocked OpenAI response
# ---------------------------------------------------------------------------


def _mock_openai_response(content: str):
    """Build a minimal mock of OpenAI chat completion response."""
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


class TestOpenAIScript:
    @pytest.mark.asyncio
    async def test_valid_openai_response(self, service_with_key):
        payload = {
            "script": "Oh wow, that cat is living her best drama queen life!",
            "captions": [
                {"text": "Oh wow, that cat", "start": 0.0, "end": 2.5},
                {"text": "is living her best drama queen life!", "start": 2.5, "end": 6.0},
            ],
            "image_prompt": "A dramatic cat wearing a tiny crown",
        }
        mock_resp = _mock_openai_response(json.dumps(payload))

        with patch.object(
            service_with_key._client.chat.completions,
            "create",
            new=AsyncMock(return_value=mock_resp),
        ):
            result = await service_with_key.generate_script("drama queen cat")

        assert result["script"] == payload["script"]
        assert len(result["captions"]) == 2
        assert result["image_prompt"] == payload["image_prompt"]

    @pytest.mark.asyncio
    async def test_json_decode_error_falls_back(self, service_with_key):
        mock_resp = _mock_openai_response("this is not json {{{")

        with patch.object(
            service_with_key._client.chat.completions,
            "create",
            new=AsyncMock(return_value=mock_resp),
        ):
            result = await service_with_key.generate_script("puppy")

        # Should fall back gracefully
        assert "script" in result
        assert "captions" in result

    @pytest.mark.asyncio
    async def test_api_exception_propagates(self, service_with_key):
        with patch.object(
            service_with_key._client.chat.completions,
            "create",
            new=AsyncMock(side_effect=Exception("API rate limit")),
        ):
            with pytest.raises(Exception, match="API rate limit"):
                await service_with_key.generate_script("any topic")


# ---------------------------------------------------------------------------
# _validate_script_data
# ---------------------------------------------------------------------------


class TestValidateScriptData:
    def test_fills_missing_script(self):
        data = {"captions": [], "image_prompt": "x"}
        ScriptService._validate_script_data(data, "dog")
        assert "script" in data

    def test_fills_missing_captions(self):
        data = {"script": "roast text", "image_prompt": "x"}
        ScriptService._validate_script_data(data, "dog")
        assert isinstance(data["captions"], list)

    def test_replaces_non_list_captions(self):
        data = {"script": "roast", "captions": "not a list", "image_prompt": "x"}
        ScriptService._validate_script_data(data, "dog")
        assert isinstance(data["captions"], list)

    def test_fills_missing_image_prompt(self):
        data = {"script": "roast", "captions": []}
        ScriptService._validate_script_data(data, "cat")
        assert "image_prompt" in data


# ---------------------------------------------------------------------------
# _fallback_script
# ---------------------------------------------------------------------------


class TestFallbackScriptStatic:
    def test_structure(self):
        result = ScriptService._fallback_script("husky dog")
        assert isinstance(result["script"], str)
        assert isinstance(result["captions"], list)
        assert isinstance(result["image_prompt"], str)

    def test_topic_present(self):
        result = ScriptService._fallback_script("my orange cat")
        combined = result["script"] + result["image_prompt"]
        assert "my orange cat" in combined.lower() or "orange cat" in combined.lower()
