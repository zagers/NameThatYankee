import pytest
import json
import typing
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
    
    assert result["priority"] == 3
    # Reasoning should explain it was demoted
    assert "Priority 3" in result["reasoning"]

def test_analyze_player_image_landscape_with_crop(mock_genai_client, mocker):
    mocker.patch("ai_services.Image.open")
    
    # Gemini returns priority 1, is landscape, but provides a crop_box
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "is_yankee_uniform": True,
        "is_official_uniform": True,
        "is_baseball_card": True,
        "is_front_of_card": True,
        "is_rectangular": True,
        "is_clean_scan": True,
        "is_in_holder": False,
        "is_portrait": False, # Landscape
        "crop_box": [100, 100, 900, 900], # Valid crop box
        "is_single_player": True,
        "has_transient_text": False,
        "priority_level": 1,
        "confidence": "high",
        "reasoning": "Landscape but can be cropped."
    })
    mock_genai_client.return_value = mock_response

    result = ai_services.analyze_player_image("fake.jpg", "Jeter", "key")
    
    # Should NOT be priority 0
    assert result["priority"] == 1
    assert result["crop_box"] == [100, 100, 900, 900]

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

def test_analyze_player_image_rejection_autograph(mock_genai_client, mocker):
    mocker.patch("ai_services.Image.open")
    
    # Gemini returns priority 1, but says it's autographed
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "is_yankee_uniform": True,
        "is_official_uniform": True,
        "is_baseball_card": True,
        "is_front_of_card": True,
        "is_rectangular": True,
        "is_clean_scan": True,
        "is_in_holder": False,
        "is_autographed": True, # Autographed!
        "is_portrait": True,
        "is_single_player": True,
        "has_transient_text": False,
        "priority_level": 1,
        "confidence": "high",
        "reasoning": "Great card but it is signed by the player."
    })
    mock_genai_client.return_value = mock_response

    result = ai_services.analyze_player_image("fake.jpg", "Jeter", "key")
    
    assert result["priority"] == 0
    assert "REJECTED due to autographed" in result["reasoning"]

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

def test_analyze_player_image_annotations_resolve():
    """Test that career_span annotation types resolve (no NameError on Python < 3.14)."""
    hints = typing.get_type_hints(ai_services.analyze_player_image)
    assert "career_span" in hints

def _era_response(**overrides):
    """Build a Gemini response with modern provenance fields enabled."""
    payload = {
        "is_yankee_uniform": True,
        "is_official_uniform": True,
        "is_baseball_card": True,
        "is_front_of_card": True,
        "is_rectangular": True,
        "is_clean_scan": True,
        "is_in_holder": False,
        "is_autographed": False,
        "is_portrait": True,
        "is_single_player": True,
        "has_transient_text": False,
        "is_upside_down": False,
        "priority_level": 1,
        "confidence": "high",
        "reasoning": "Clean card.",
        "is_playing_era_card": True,
        "printed_copyright_year": 1952,
        "appears_as_player": True,
        "is_modern_reissue": False,
    }
    payload.update(overrides)
    return payload

def test_analyze_player_image_modern_reissue_demoted(mock_genai_client, mocker):
    mocker.patch("ai_services.Image.open")
    mock_response = MagicMock()
    mock_response.text = json.dumps(_era_response(is_modern_reissue=True))
    mock_genai_client.return_value = mock_response

    result = ai_services.analyze_player_image("fake.jpg", "Berra", "key", career_span=[1946, 1963])

    assert result["priority"] == 3
    assert "modern reissue" in result["reasoning"]

def test_analyze_player_image_not_playing_era_demoted(mock_genai_client, mocker):
    mocker.patch("ai_services.Image.open")
    mock_response = MagicMock()
    mock_response.text = json.dumps(_era_response(is_playing_era_card=False, is_modern_reissue=False))
    mock_genai_client.return_value = mock_response

    result = ai_services.analyze_player_image("fake.jpg", "Berra", "key", career_span=[1946, 1963])

    assert result["priority"] == 3
    assert "playing era" in result["reasoning"]

def test_analyze_player_image_not_as_player_demoted(mock_genai_client, mocker):
    mocker.patch("ai_services.Image.open")
    mock_response = MagicMock()
    mock_response.text = json.dumps(_era_response(appears_as_player=False, is_modern_reissue=False))
    mock_genai_client.return_value = mock_response

    result = ai_services.analyze_player_image("fake.jpg", "Berra", "key", career_span=[1946, 1963])

    assert result["priority"] == 3
    assert "as a player" in result["reasoning"]

def test_analyze_player_image_no_career_span_no_demotion(mock_genai_client, mocker):
    mocker.patch("ai_services.Image.open")
    mock_response = MagicMock()
    mock_response.text = json.dumps(_era_response(is_modern_reissue=True))
    mock_genai_client.return_value = mock_response

    result = ai_services.analyze_player_image("fake.jpg", "Berra", "key")

    assert result["priority"] == 1

def test_analyze_player_image_missing_era_fields_no_demotion(mock_genai_client, mocker):
    mocker.patch("ai_services.Image.open")
    mock_response = MagicMock()
    mock_response.text = json.dumps(_era_response(is_modern_reissue=None, is_playing_era_card=None, appears_as_player=None))
    mock_genai_client.return_value = mock_response

    result = ai_services.analyze_player_image("fake.jpg", "Berra", "key", career_span=[1946, 1963])

    assert result["priority"] == 1

def test_analyze_player_image_era_clean_keeps_priority(mock_genai_client, mocker):
    mocker.patch("ai_services.Image.open")
    mock_response = MagicMock()
    mock_response.text = json.dumps(_era_response())
    mock_genai_client.return_value = mock_response

    result = ai_services.analyze_player_image("fake.jpg", "Berra", "key", career_span=[1946, 1963])

    assert result["priority"] == 1

def test_analyze_player_image_photo_not_demoted_for_no_copyright_year(mock_genai_client, mocker):
    """Test that a Priority 2 photo is NOT demoted because is_playing_era_card is False.

    is_playing_era_card is a card-only field (it asks about a printed copyright year).
    A clean action photo has no printed year, so the model may say False; that must not
    penalize a legitimate Priority 2 photo.
    """
    mocker.patch("ai_services.Image.open")
    payload = _era_response(
        is_baseball_card=False,
        is_playing_era_card=False,
        printed_copyright_year=None,
        priority_level=2,
    )
    mock_response = MagicMock()
    mock_response.text = json.dumps(payload)
    mock_genai_client.return_value = mock_response

    result = ai_services.analyze_player_image("fake.jpg", "Berra", "key", career_span=[1946, 1963])

    assert result["priority"] == 2

def test_analyze_player_image_non_rectangular_rejected(mock_genai_client, mocker):
    mocker.patch("ai_services.Image.open")
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "is_yankee_uniform": True,
        "is_official_uniform": True,
        "is_baseball_card": True,
        "is_front_of_card": True,
        "is_rectangular": False,  # Non-rectangular / angled
        "is_clean_scan": True,
        "is_in_holder": False,
        "is_portrait": True,
        "is_single_player": True,
        "has_transient_text": False,
        "priority_level": 1,
        "confidence": "high",
        "reasoning": "Card on a table at an angle."
    })
    mock_genai_client.return_value = mock_response

    result = ai_services.analyze_player_image("fake.jpg", "Jeter", "key")

    assert result["priority"] == 0
    assert "REJECTED" in result["reasoning"]

def test_analyze_player_image_non_rectangular_cannot_be_saved_by_crop(mock_genai_client, mocker):
    mocker.patch("ai_services.Image.open")
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "is_yankee_uniform": True,
        "is_official_uniform": True,
        "is_baseball_card": True,
        "is_front_of_card": True,
        "is_rectangular": False,  # Non-rectangular / angled
        "is_clean_scan": False,
        "is_in_holder": False,
        "is_portrait": False,
        "is_single_player": True,
        "has_transient_text": False,
        "crop_box": [100, 100, 900, 900],  # AI suggests a crop, but card is not rectangular
        "priority_level": 1,
        "confidence": "high",
        "reasoning": "Angled photo, trying a crop."
    })
    mock_genai_client.return_value = mock_response

    result = ai_services.analyze_player_image("fake.jpg", "Jeter", "key")

    assert result["priority"] == 0
    assert "REJECTED" in result["reasoning"]
