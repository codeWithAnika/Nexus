"""
Unit tests for NemotronClient using mocked OpenAI client responses.
"""

import json
from unittest.mock import MagicMock
import pytest

from fir_intelligence.config import NemotronConfig
from fir_intelligence.phase1_extraction.llm_client import NemotronClient


@pytest.fixture
def mock_llm_client(tmp_path):
    config = NemotronConfig()
    config.api_key = "mock-key-12345"
    config.enabled = True

    trace_path = tmp_path / "llm_trace.jsonl"
    client = NemotronClient(config=config, trace_file=trace_path)
    client.client = MagicMock()
    return client


def test_llm_client_successful_json_response(mock_llm_client):
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='{"entities": [{"type": "Person", "value": "Vikram Malhotra"}]}'))
    ]
    mock_llm_client.client.chat.completions.create.return_value = mock_response

    result = mock_llm_client.generate_json("Test prompt")
    assert result == {"entities": [{"type": "Person", "value": "Vikram Malhotra"}]}


def test_llm_client_retry_on_malformed_json(mock_llm_client):
    bad_resp = MagicMock(message=MagicMock(content="Invalid json response text"))
    good_resp = MagicMock(message=MagicMock(content='{"status": "ok"}'))

    mock_llm_client.client.chat.completions.create.side_effect = [
        MagicMock(choices=[bad_resp]),
        MagicMock(choices=[good_resp]),
    ]

    result = mock_llm_client.generate_json("Test prompt", max_retries=1)
    assert result == {"status": "ok"}


def test_llm_client_resilient_fallback_on_api_error(mock_llm_client):
    mock_llm_client.client.chat.completions.create.side_effect = Exception("API Error")

    result = mock_llm_client.generate_json("Test prompt")
    assert result is None


def test_extract_narrative_entities_llm(mock_llm_client):
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='{"entities": [{"type": "Person", "value": "Ramesh Sharma", "context": "Suspect"}]}'))
    ]
    mock_llm_client.client.chat.completions.create.return_value = mock_response

    entities = mock_llm_client.extract_narrative_entities("Ramesh Sharma was arrested", "FIR-001")
    assert len(entities) == 1
    assert entities[0]["value"] == "Ramesh Sharma"


def test_evaluate_ambiguous_merge_llm(mock_llm_client):
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='{"should_merge": true, "confidence": 0.92, "reasoning": "Matching name and phone"}'))
    ]
    mock_llm_client.client.chat.completions.create.return_value = mock_response

    res = mock_llm_client.evaluate_ambiguous_merge({"name": "Ramesh"}, {"name": "Ramesh K"}, {})
    assert res["should_merge"] is True
    assert res["confidence"] == 0.92
