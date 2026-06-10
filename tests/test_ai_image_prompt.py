# ABOUTME: Verifies the integrity and content of the Gemini AI image analysis prompt.
# ABOUTME: Ensures that recent improvements to the search strategy are reflected in the prompt text.
import pytest
from unittest.mock import MagicMock
import ai_services

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
    
    # Mock the rate limiter and Image.open
    mocker.patch("ai_services._respect_free_tier_rate_limit")
    mocker.patch("ai_services.Image.open")
    
    return mock_generate

def test_prompt_contains_new_criteria(mock_genai_client):
    # Setup mock response to avoid errors during the call
    mock_response = MagicMock()
    mock_response.text = '{"priority_level": 0}'
    mock_genai_client.return_value = mock_response

    # Trigger the function that uses the prompt
    ai_services.analyze_player_image("fake_path.webp", "Mickey Mantle", "fake_key")
    
    # Extract the prompt from the call arguments
    args, kwargs = mock_genai_client.call_args
    contents = kwargs.get('contents')
    if contents is None:
        # If not in kwargs, it must be in args. 
        # In analyze_player_image, it's called with model=MODEL, contents=[prompt, verification_image]
        # which means contents is a keyword argument.
        # But let's be safe.
        contents = args[1]
    
    prompt = contents[0] # contents is a list [prompt, image]
    
    # Check for Orientation update
    assert "If the image is in landscape orientation (width > height), you MUST determine if a clear, portrait-oriented baseball card or player is present that can be cropped out." in prompt
    assert "If a crop is possible, provide the `crop_box` and continue." in prompt
    
    # Check for Autographs update
    assert "factory design (common on vintage cards) are" in prompt
    assert "considered autographs for this check and should be" in prompt
    assert "ACCEPTED" in prompt
    assert "REJECT (Priority 0) only if the image contains a HAND-WRITTEN signature" in prompt
    
    # Check for Unofficial Uniforms update
    assert "Relax rejection for players from before 1990 if the uniform is a standard road/home pinstripe or gray uniform from that era, even if branding is subtle." in prompt

def test_prompt_contains_rotation_criteria(mock_genai_client):
    # Setup mock response
    mock_response = MagicMock()
    mock_response.text = '{"priority_level": 0}'
    mock_genai_client.return_value = mock_response

    # Trigger the function
    ai_services.analyze_player_image("fake_path.webp", "Mickey Mantle", "fake_key")
    
    args, kwargs = mock_genai_client.call_args
    prompt = kwargs.get('contents')[0]
    
    # Verify Rotation rejection rule
    assert "Rotation/Sideways/Upside Down" in prompt
    assert "REJECT (Priority 0) any image that is rotated sideways or upside down" in prompt
    assert "is_upside_down" in prompt
    assert "Even if the image file itself is in portrait orientation" in prompt
    assert "if the content (the player or the card) is turned on its side" in prompt

def test_analyze_player_image_rejects_upside_down(mock_genai_client):
    # Setup mock response where AI says it is upside down
    mock_response = MagicMock()
    mock_response.text = '{"priority_level": 1, "confidence": "high", "is_upside_down": true, "reasoning": "Upside down"}'
    mock_genai_client.return_value = mock_response

    result = ai_services.analyze_player_image("fake_path.webp", "Mickey Mantle", "fake_key")
    
    # Even if Priority is 1, the override logic should set it to 0
    assert result["priority"] == 0
    assert "upside down/sideways" in result["reasoning"].lower()
