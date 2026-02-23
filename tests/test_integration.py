"""
Integration tests — require a real OPENAI_API_KEY env variable.
Run with:  OPENAI_API_KEY=sk-... python3 -m pytest tests/test_integration.py -v
Never commit API keys to source control.

Cost strategy: multiple assertions per API call; max_completion_tokens capped on
every completion call that doesn't need a long output; 5 s gap between tests
to stay within tier-1 RPM limits (~3 RPM for newer models).
"""
from __future__ import annotations

import os
import time
import pytest
import httpx

from rankthebot.core.llms.openai import OpenAIClient
from rankthebot.core.parser import parse_mentions
from rankthebot.core.expander import expand_intent

API_KEY = os.environ.get("OPENAI_API_KEY", "")

pytestmark = pytest.mark.skipif(
    not API_KEY,
    reason="OPENAI_API_KEY not set — skipping integration tests",
)


def _has_completion_quota() -> bool:
    """Probe with a 1-token call to confirm billing is active."""
    try:
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hi"}], "max_completion_tokens": 1},
            timeout=15,
        )
        return resp.status_code == 200
    except Exception:
        return False


HAS_QUOTA = _has_completion_quota()
needs_quota = pytest.mark.skipif(
    not HAS_QUOTA,
    reason="Account has no billing quota — add credits at platform.openai.com/billing",
)


@pytest.fixture(scope="module")
def client():
    """gpt-4o-mini client — used for parser/expander tests."""
    return OpenAIClient(api_key=API_KEY, model="gpt-4o-mini")


@pytest.fixture(scope="module")
def gpt5_client():
    """gpt-5-mini client — cheapest GPT-5 model, used for GPT-5 tests."""
    return OpenAIClient(api_key=API_KEY, model="gpt-5-mini")


@pytest.fixture(autouse=True)
def rate_limit_pause():
    """5 s gap between every test to stay inside tier-1 RPM limits."""
    time.sleep(5)
    yield


# ---------------------------------------------------------------------------
# Authentication — GET /models only, costs nothing
# ---------------------------------------------------------------------------

class TestAuthentication:
    def test_key_authenticates_and_models_available(self):
        """Single call: verifies auth + presence of required models."""
        resp = httpx.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=15,
        )
        assert resp.status_code == 200, f"Auth failed: {resp.text[:200]}"
        model_ids = {m["id"] for m in resp.json()["data"]}
        assert "gpt-4o-mini" in model_ids
        assert "gpt-5" in model_ids
        assert "gpt-5-mini" in model_ids

    def test_bad_key_raises_401_and_exception(self):
        """Verifies both the HTTP 401 and that OpenAIClient raises on a bad key."""
        resp = httpx.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": "Bearer sk-bad-key"},
            timeout=15,
        )
        assert resp.status_code == 401

        bad_client = OpenAIClient(api_key="sk-bad-key", model="gpt-4o-mini")
        with pytest.raises(Exception):
            bad_client.complete("hello")


# ---------------------------------------------------------------------------
# OpenAIClient — gpt-4o-mini (1 API call)
# ---------------------------------------------------------------------------

class TestOpenAIClientIntegration:
    @needs_quota
    def test_complete_basic(self, client):
        """One call: non-empty response + deterministic content check."""
        result = client.complete(
            "Reply with the number 42 and nothing else.",
            temperature=0.0,
            max_tokens=10,
        )
        assert isinstance(result, str) and result.strip()
        assert "42" in result


# ---------------------------------------------------------------------------
# parse_mentions — gpt-4o-mini (1 API call)
# ---------------------------------------------------------------------------

class TestParseMentionsIntegration:
    SAMPLE = (
        "When it comes to CRM software, Salesforce is the market leader. "
        "HubSpot is a great option for smaller teams. Zoho CRM offers good value."
    )

    @needs_quota
    def test_parse_mentions_full(self, client):
        """One call: list returned, known brands found, all required fields present."""
        result = parse_mentions(self.SAMPLE, parser_client=client)
        assert isinstance(result, list)
        brands = [r["brand"].lower() for r in result]
        assert any("salesforce" in b or "hubspot" in b or "zoho" in b for b in brands), \
            f"Expected a known brand, got: {brands}"
        for item in result:
            assert {"brand", "position", "sentiment", "context"} <= item.keys()
            assert item["sentiment"] in ("positive", "neutral", "negative", "qualified")
            assert isinstance(item["position"], int)

    def test_parse_mentions_no_client_returns_empty(self):
        """No API call — safe fallback path."""
        assert parse_mentions("", parser_client=None) == []


# ---------------------------------------------------------------------------
# expand_intent — gpt-4o-mini (1 API call)
# ---------------------------------------------------------------------------

class TestExpandIntentIntegration:
    @needs_quota
    def test_expand_intent_full(self, client):
        """One call: list returned, items are unique non-empty strings, count in range."""
        result = expand_intent("best SEO tools", client, count=8)
        assert isinstance(result, list)
        assert 3 <= len(result) <= 20
        for q in result:
            assert isinstance(q, str) and q.strip()
        assert len(result) == len(set(result)), "Duplicate queries returned"


# ---------------------------------------------------------------------------
# GPT-5 — gpt-5-mini with max_completion_tokens caps (3 API calls)
# ---------------------------------------------------------------------------

class TestGPT5Integration:
    """
    All direct GPT-5 calls use gpt-5-mini + tight max_completion_tokens to
    minimise cost. Three tests → three calls.
    """

    @needs_quota
    def test_gpt5_mini_basic_completion(self, gpt5_client):
        """
        One call: verifies gpt-5-mini responds.
        Notes:
        - temperature=None: gpt-5-mini is a reasoning model that only accepts
          the default temperature; explicit values are rejected.
        - No max_tokens: reasoning models consume tokens internally before
          producing output, so a small cap silences the response entirely.
        """
        result = gpt5_client.complete(
            "Reply with the single word: pong",
            temperature=None,
        )
        assert isinstance(result, str) and result.strip()

    @needs_quota
    def test_gpt5_mini_model_override_from_base_client(self, client):
        """
        One call: an existing gpt-4o-mini client can route a single call to
        gpt-5-mini via the model= override on complete().
        """
        result = client.complete(
            "Reply with the number 99 and nothing else.",
            temperature=None,
            model="gpt-5-mini",
        )
        assert isinstance(result, str) and result.strip()
        assert "99" in result

    @needs_quota
    def test_gpt5_parse_mentions(self, gpt5_client):
        """
        One call: parse_mentions works when backed by gpt-5-mini as the parser
        (verifies the full mention-extraction pipeline with the new model).
        """
        sample = "Notion and Linear are popular tools. Asana is also widely used."
        result = parse_mentions(sample, parser_client=gpt5_client)
        assert isinstance(result, list)
        brands = [r["brand"].lower() for r in result]
        assert any("notion" in b or "linear" in b or "asana" in b for b in brands), \
            f"Expected a known brand, got: {brands}"
