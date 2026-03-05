import pytest  # type: ignore
import json
from unittest.mock import MagicMock
import ai_services  # type: ignore
from google.genai import errors  # type: ignore

# We mock `_respect_free_tier_rate_limit` globally for all tests in this file
@pytest.fixture(autouse=True)
def disable_rate_limiting(mocker):
    mocker.patch("ai_services._respect_free_tier_rate_limit")
    mocker.patch("time.sleep") # To avoid actually sleeping during retry loops

@pytest.fixture
def mock_genai_client(mocker):
    # Mock the Client constructor
    mock_client_cls = mocker.patch("ai_services.genai.Client")
    
    # Create a mock instance
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    
    # Mock the generate_content method wrapper
    mock_generate = MagicMock()
    mock_client.models.generate_content = mock_generate
    
    return mock_generate

def test_get_player_info_from_image_success(mock_genai_client, mocker):
    mocker.patch("ai_services.Image.open")  # Don't try to open a real image
    
    # Setup mock response
    mock_response = MagicMock()
    mock_response.text = '```json\n{"name": "Derek Jeter", "nickname": "The Captain"}\n```'
    mock_genai_client.return_value = mock_response

    result = ai_services.get_player_info_from_image("fake_path.webp", "fake_key")
    
    assert result is not None
    assert result["name"] == "Derek Jeter"
    assert result["nickname"] == "The Captain"
    mock_genai_client.assert_called_once()

def test_get_player_info_from_image_retry(mock_genai_client, mocker):
    mocker.patch("ai_services.Image.open")
    
    # First response is bad JSON (raises ValueError), second is good
    bad_response = MagicMock()
    bad_response.text_property = "" # empty text
    
    good_response = MagicMock()
    good_response.text = '{"name": "Babe Ruth", "nickname": "The Bambino"}'
    
    # Side effect sequence
    mock_genai_client.side_effect = [ValueError("Bad parse"), good_response]

    result = ai_services.get_player_info_from_image("fake_path.webp", "fake_key")
    
    assert result is not None
    assert result["name"] == "Babe Ruth"
    assert mock_genai_client.call_count == 2

def test_get_facts_from_gemini_success(mock_genai_client):
    mock_response = MagicMock()
    mock_response.text = '{"facts": ["Fact 1", "Fact 2", "Fact 3"]}'
    mock_genai_client.return_value = mock_response

    result = ai_services.get_facts_from_gemini("Mickey Mantle", "fake_key")
    
    assert len(result) == 3
    assert result[0] == "Fact 1"

def test_get_facts_and_followup_success(mock_genai_client):
    mock_response = MagicMock()
    expected_data = {
        "facts": ["Fact A", "Fact B", "Fact C"],
        "qa": [
            {"question": "Q1?", "answer": "A1."},
            {"question": "Q2?", "answer": "A2."},
            {"question": "Q3?", "answer": "A3."}
        ]
    }
    mock_response.text = json.dumps(expected_data)
    mock_genai_client.return_value = mock_response

    result = ai_services.get_facts_and_followup_from_gemini("Aaron Judge", "fake_key")
    
    assert result["facts"] == expected_data["facts"]
    assert result["qa"] == expected_data["qa"]

def test_get_facts_and_followup_quota_exceeded(mock_genai_client):
    # Setup error exactly matching the string 'quota_value: 50'
    api_error = errors.APIError("quota_value: 50", response_json={})
    api_error.code = 429
    mock_genai_client.side_effect = api_error

    with pytest.raises(ai_services.GeminiDailyQuotaExceeded):
        ai_services.get_facts_and_followup_from_gemini("Mariano Rivera", "fake_key")
