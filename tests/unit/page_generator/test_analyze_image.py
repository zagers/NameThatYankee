import pytest
import json
from unittest.mock import MagicMock
import ai_services

@pytest.fixture(autouse=True)
def disable_rate_limiting(mocker):
    mocker.patch("ai_services._respect_free_tier_rate_limit")
    mocker.patch("time.sleep")

@pytest.fixture
def mock_genai_client(mocker):
    mock_client_cls = mocker.patch("ai_services.genai.Client")
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_generate = MagicMock()
    mock_client.models.generate_content = mock_generate
    return mock_generate

def test_analyze_player_image_rejection_landscape(mock_genai_client, mocker):
    mocker.patch("ai_services.Image.open")
    
    # Gemini returns priority 1, but says it's landscape
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "is_yankee_uniform": True,
        "is_official_uniform": True,
        "is_baseball_card": True,
        "is_front_of_card": True,
        "is_rectangular": True,
        "is_clean_scan": True,
        "is_in_holder": False,
        "is_portrait": False, # Landscape!
        "is_single_player": True,
        "has_transient_text": False,
        "priority_level": 1,
        "confidence": "high",
        "reasoning": "Looks good but it is landscape."
    })
    mock_genai_client.return_value = mock_response

    result = ai_services.analyze_player_image("fake.jpg", "Jeter", "key")
    
    assert result["priority"] == 0
    assert "REJECTED due to landscape" in result["reasoning"]

def test_analyze_player_image_rejection_multiple_players(mock_genai_client, mocker):
    mocker.patch("ai_services.Image.open")
    
    # Gemini returns priority 1, but says it has multiple players
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "is_yankee_uniform": True,
        "is_official_uniform": True,
        "is_baseball_card": True,
        "is_front_of_card": True,
        "is_rectangular": True,
        "is_clean_scan": True,
        "is_in_holder": False,
        "is_portrait": True,
        "is_single_player": False, # Multiple!
        "has_transient_text": False,
        "priority_level": 1,
        "confidence": "high",
        "reasoning": "Good card but shows two players."
    })
    mock_genai_client.return_value = mock_response

    result = ai_services.analyze_player_image("fake.jpg", "Jeter", "key")
    
    assert result["priority"] == 0
    assert "REJECTED due to multiple players/collage" in result["reasoning"]

def test_analyze_player_image_priority_3_fallback(mock_genai_client, mocker):
    mocker.patch("ai_services.Image.open")
    
    # Gemini returns priority 1 but low confidence
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "is_yankee_uniform": True,
        "is_official_uniform": True,
        "is_baseball_card": True,
        "is_front_of_card": True,
        "is_rectangular": True,
        "is_clean_scan": True,
        "is_in_holder": False,
        "is_portrait": True,
        "is_single_player": True,
        "has_transient_text": False,
        "priority_level": 1,
        "confidence": "low", # Low confidence!
        "reasoning": "Not sure if it is a card."
    })
    mock_genai_client.return_value = mock_response

    result = ai_services.analyze_player_image("fake.jpg", "Jeter", "key")
    
    assert result["priority"] == 3
    assert "Low confidence" in result["reasoning"]
