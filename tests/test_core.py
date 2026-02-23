"""
Tests for rankthebot core logic.
Runs fully offline — no real API calls are made.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# scorer
# ---------------------------------------------------------------------------

from rankthebot.core.scorer import visibility_score


class TestVisibilityScore:
    def test_zero_mention_rate_returns_zero(self):
        assert visibility_score(0.0, None) == 0.0

    def test_negative_mention_rate_returns_zero(self):
        assert visibility_score(-10.0, 1) == 0.0

    def test_no_position_caps_at_mention_rate(self):
        assert visibility_score(60.0, None) == 60.0

    def test_no_position_caps_at_100(self):
        assert visibility_score(150.0, None) == 100.0

    def test_position_1_full_weight(self):
        # position_factor == 1.0 at position 1
        assert visibility_score(100.0, 1.0) == 100.0

    def test_position_2_decays(self):
        score = visibility_score(100.0, 2.0)
        # factor = max(0.25, 1 - 0.18) = 0.82
        assert score == pytest.approx(82.0, abs=0.1)

    def test_high_position_floors_at_25_pct(self):
        # position high enough that factor would go below 0.25
        score = visibility_score(100.0, 10.0)
        assert score >= 25.0

    def test_result_never_exceeds_100(self):
        assert visibility_score(100.0, 1.0) <= 100.0


# ---------------------------------------------------------------------------
# parser — _extract_json_block and _clean_mentions (pure logic, no API)
# ---------------------------------------------------------------------------

from rankthebot.core.parser import _clean_mentions, _extract_json_block, parse_mentions


class TestExtractJsonBlock:
    def test_extracts_fenced_json(self):
        text = '```json\n[{"brand": "Acme"}]\n```'
        result = _extract_json_block(text)
        assert result is not None
        assert "Acme" in result

    def test_extracts_bare_bracket(self):
        text = 'Here is the result: [{"brand": "Beta"}]'
        result = _extract_json_block(text)
        assert result is not None
        assert "Beta" in result

    def test_returns_none_when_no_json(self):
        assert _extract_json_block("no json here") is None

    def test_prefers_fenced_over_bare(self):
        text = '```json\n[{"brand": "Fenced"}]\n```\n[{"brand": "Bare"}]'
        result = _extract_json_block(text)
        assert "Fenced" in result


class TestCleanMentions:
    def test_basic_valid_item(self):
        data = [{"brand": "Acme", "position": 1, "sentiment": "positive", "context": "Acme is great"}]
        result = _clean_mentions(data)
        assert len(result) == 1
        assert result[0]["brand"] == "Acme"
        assert result[0]["sentiment"] == "positive"

    def test_invalid_sentiment_defaults_to_neutral(self):
        data = [{"brand": "X", "sentiment": "awesome"}]
        result = _clean_mentions(data)
        assert result[0]["sentiment"] == "neutral"

    def test_missing_brand_skipped(self):
        data = [{"brand": "", "sentiment": "positive"}]
        result = _clean_mentions(data)
        assert result == []

    def test_non_list_input_returns_empty(self):
        assert _clean_mentions("not a list") == []
        assert _clean_mentions(None) == []

    def test_position_fallback_to_index(self):
        data = [
            {"brand": "A", "sentiment": "neutral"},
            {"brand": "B", "sentiment": "neutral"},
        ]
        result = _clean_mentions(data)
        assert result[0]["position"] == 1
        assert result[1]["position"] == 2

    def test_non_int_position_coerced(self):
        data = [{"brand": "X", "position": "3", "sentiment": "neutral"}]
        result = _clean_mentions(data)
        assert result[0]["position"] == 3

    def test_context_falls_back_to_brand(self):
        data = [{"brand": "MyBrand", "context": "", "sentiment": "neutral"}]
        result = _clean_mentions(data)
        assert result[0]["context"] == "MyBrand"

    def test_all_sentiments_accepted(self):
        for s in ("positive", "neutral", "negative", "qualified"):
            data = [{"brand": "X", "sentiment": s}]
            assert _clean_mentions(data)[0]["sentiment"] == s


class TestParseMentions:
    def test_returns_empty_when_no_client(self):
        result = parse_mentions("some LLM response", parser_client=None)
        assert result == []

    def test_calls_client_and_returns_parsed(self):
        fake_response = '[{"brand": "Acme", "position": 1, "sentiment": "positive", "context": "Acme is great"}]'
        mock_client = MagicMock()
        mock_client.complete.return_value = fake_response
        result = parse_mentions("Acme is a great tool", parser_client=mock_client)
        assert len(result) == 1
        assert result[0]["brand"] == "Acme"

    def test_handles_api_error_gracefully(self):
        mock_client = MagicMock()
        mock_client.complete.side_effect = Exception("API down")
        result = parse_mentions("some text", parser_client=mock_client)
        assert result == []

    def test_handles_malformed_json(self):
        mock_client = MagicMock()
        mock_client.complete.return_value = "[not valid json}"
        result = parse_mentions("some text", parser_client=mock_client)
        assert result == []


# ---------------------------------------------------------------------------
# expander
# ---------------------------------------------------------------------------

from rankthebot.core.expander import expand_intent


class TestExpandIntent:
    def test_returns_list_of_strings(self):
        mock_client = MagicMock()
        mock_client.complete.return_value = '["query one", "query two", "query three"]'
        result = expand_intent("best SEO tools", mock_client, count=3)
        assert isinstance(result, list)
        assert result == ["query one", "query two", "query three"]

    def test_returns_empty_on_no_match(self):
        mock_client = MagicMock()
        mock_client.complete.return_value = "Sorry, I cannot do that."
        result = expand_intent("seo tools", mock_client, count=5)
        assert result == []

    def test_strips_whitespace_from_queries(self):
        mock_client = MagicMock()
        mock_client.complete.return_value = '["  padded query  ", "clean query"]'
        result = expand_intent("test intent", mock_client, count=2)
        assert result[0] == "padded query"

    def test_filters_non_strings(self):
        mock_client = MagicMock()
        mock_client.complete.return_value = '["valid", 42, null, "also valid"]'
        result = expand_intent("test", mock_client, count=4)
        assert result == ["valid", "also valid"]

    def test_handles_malformed_json(self):
        mock_client = MagicMock()
        mock_client.complete.return_value = "[broken json"
        result = expand_intent("test", mock_client, count=3)
        assert result == []


# ---------------------------------------------------------------------------
# db/store — uses a temp file, no real DB on disk after test
# ---------------------------------------------------------------------------

from rankthebot.db.store import Store


@pytest.fixture
def tmp_store(tmp_path):
    return Store(tmp_path / "test.db")


class TestStore:
    def test_add_query_returns_id_and_new_flag(self, tmp_store):
        id1, is_new = tmp_store.add_query("what is SEO?")
        assert isinstance(id1, int)
        assert is_new is True

    def test_duplicate_query_returns_same_id(self, tmp_store):
        id1, _ = tmp_store.add_query("what is SEO?")
        id2, is_new = tmp_store.add_query("what is SEO?")
        assert id1 == id2
        assert is_new is False

    def test_list_queries_empty(self, tmp_store):
        assert tmp_store.list_queries() == []

    def test_list_queries_after_add(self, tmp_store):
        tmp_store.add_query("query A")
        tmp_store.add_query("query B")
        rows = tmp_store.list_queries()
        assert len(rows) == 2
        texts = [r["query_text"] for r in rows]
        assert "query A" in texts
        assert "query B" in texts

    def test_clear_queries(self, tmp_store):
        tmp_store.add_query("q1")
        tmp_store.add_query("q2")
        deleted = tmp_store.clear_queries()
        assert deleted == 2
        assert tmp_store.list_queries() == []

    def test_add_query_run_and_mentions(self, tmp_store):
        qid, _ = tmp_store.add_query("best CRM?")
        run_id = tmp_store.add_query_run(
            query_id=qid,
            query_text="best CRM?",
            llm="chatgpt",
            raw_response="Salesforce is number one.",
        )
        assert isinstance(run_id, int)
        tmp_store.add_mentions(run_id, [
            {"brand": "Salesforce", "position": 1, "sentiment": "positive", "context": "Salesforce is number one"},
        ])

    def test_visibility_for_brand_zero_when_not_mentioned(self, tmp_store):
        tmp_store.add_query_run(
            query_id=None,
            query_text="best tool?",
            llm="claude",
            raw_response="No brand mentioned.",
        )
        rows = tmp_store.visibility_for_brand("MyBrand")
        assert len(rows) == 1
        assert rows[0]["mentioned_runs"] == 0

    def test_visibility_for_brand_counts_correctly(self, tmp_store):
        for i in range(3):
            run_id = tmp_store.add_query_run(
                query_id=None,
                query_text=f"query {i}",
                llm="gpt",
                raw_response="Acme is best",
            )
            tmp_store.add_mentions(run_id, [
                {"brand": "Acme", "position": 1, "sentiment": "positive", "context": "Acme is best"},
            ])
        rows = tmp_store.visibility_for_brand("Acme")
        assert rows[0]["mentioned_runs"] == 3
        assert rows[0]["total_runs"] == 3

    def test_top_competitors_returns_brands(self, tmp_store):
        run_id = tmp_store.add_query_run(
            query_id=None,
            query_text="best tools?",
            llm="gpt",
            raw_response="",
        )
        tmp_store.add_mentions(run_id, [
            {"brand": "Acme", "position": 1, "sentiment": "positive", "context": "Acme"},
            {"brand": "Rival", "position": 2, "sentiment": "neutral", "context": "Rival"},
        ])
        rows = tmp_store.top_competitors(limit=5)
        brands = [r["brand"] for r in rows]
        assert "Acme" in brands
        assert "Rival" in brands

    def test_top_competitors_excludes_brand(self, tmp_store):
        run_id = tmp_store.add_query_run(
            query_id=None,
            query_text="best?",
            llm="gpt",
            raw_response="",
        )
        tmp_store.add_mentions(run_id, [
            {"brand": "MyBrand", "position": 1, "sentiment": "positive", "context": "MyBrand"},
            {"brand": "Competitor", "position": 2, "sentiment": "neutral", "context": "Competitor"},
        ])
        rows = tmp_store.top_competitors(limit=10, exclude="MyBrand")
        brands = [r["brand"] for r in rows]
        assert "MyBrand" not in brands
        assert "Competitor" in brands

    def test_top_zero_visibility_queries(self, tmp_store):
        run_id = tmp_store.add_query_run(
            query_id=None,
            query_text="who is best?",
            llm="gpt",
            raw_response="Not my brand",
        )
        # No mentions for "MyBrand"
        tmp_store.add_mentions(run_id, [
            {"brand": "OtherBrand", "position": 1, "sentiment": "neutral", "context": "Other"},
        ])
        rows = tmp_store.top_zero_visibility_queries("MyBrand")
        texts = [r["query_text"] for r in rows]
        assert "who is best?" in texts
