# ABOUTME: Tests for the grounded AI generation service.
# ABOUTME: Verifies trivia generation anchored to player dossiers using mocked Gemini API.

import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

# Add the page-generator directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "page-generator"))

from grounded_ai import generate_grounded_trivia

def test_generate_grounded_trivia():
    dossier = {
        "name": "Tippy Martinez",
        "career_totals": {"ERA": "3.45", "Saves": "115"},
        "yearly_war": [{"year": "1983", "war": 2.5}],
        "transactions": ["Traded by the New York Yankees... to the Baltimore Orioles... 1976"],
        "awards": ["1x All-Star", "1983 World Series"],
        "bio": "Known for the pickoff play..."
    }
    
    mock_response_content = {
        "facts": ["Fact 1", "Fact 2", "Fact 3"],
        "qa": [
            {"question": "Q1", "answer": "A1"},
            {"question": "Q2", "answer": "A2"},
            {"question": "Q3", "answer": "A3"}
        ],
        "claims": ["Claim 1", "Claim 2"]
    }

    with patch("grounded_ai.genai.Client") as mock_genai_client:
        mock_client = MagicMock()
        mock_genai_client.return_value = mock_client
        
        mock_model = MagicMock()
        mock_client.models = MagicMock()
        # The code uses client.models.generate_content
        
        mock_response = MagicMock()
        mock_response.text = '{"facts": ["Fact 1", "Fact 2", "Fact 3"], "qa": [{"question": "Q1", "answer": "A1"}, {"question": "Q2", "answer": "A2"}, {"question": "Q3", "answer": "A3"}], "claims": ["Claim 1", "Claim 2"]}'
        mock_client.models.generate_content.return_value = mock_response

        result = generate_grounded_trivia(dossier, "fake_api_key")

        assert result == mock_response_content
        assert len(result["facts"]) == 3
        assert len(result["qa"]) == 3
        assert "claims" in result
        
        # Verify prompt constraints
        args, kwargs = mock_client.models.generate_content.call_args
        prompt = kwargs.get('contents', args[0] if args else "")
        if isinstance(prompt, list):
            prompt = prompt[0]
        
        assert "Yankees historian and fan" in prompt
        assert "Tippy Martinez" in prompt
        assert "THE SOURCE OF TRUTH" in prompt

def test_is_invalid_hint():
    from grounded_ai import is_invalid_hint
    
    # 1. Spoilers with player name
    assert is_invalid_hint("Played with Tippy Martinez", "Tippy Martinez") is True
    assert is_invalid_hint("A great catcher named Martinez", "Tippy Martinez") is True
    
    # 2. Years (4-digit starting with 19 or 20)
    assert is_invalid_hint("Won the MVP in 1999", "Tippy Martinez") is True
    assert is_invalid_hint("Made debut in 2005", "Tippy Martinez") is True
    assert is_invalid_hint("Had 30 saves in 1983", "Tippy Martinez") is True
    
    # 3. Geographical or team names
    assert is_invalid_hint("Played for the Yankees in his career", "Tippy Martinez") is True
    assert is_invalid_hint("Spent a season in the Bronx", "Tippy Martinez") is True
    assert is_invalid_hint("Born in Brooklyn", "Tippy Martinez") is True
    assert is_invalid_hint("Wore the famous pinstripes", "Tippy Martinez") is True
    
    # 4. Team count or stint counts
    assert is_invalid_hint("Played for 9 different franchises", "Tippy Martinez") is True
    assert is_invalid_hint("Played for 9 teams during his career", "Tippy Martinez") is True
    assert is_invalid_hint("Spent two separate stints with the team", "Tippy Martinez") is True
    assert is_invalid_hint("A member of the organization", "Tippy Martinez") is True
    assert is_invalid_hint("Had multiple stints with the franchise", "Tippy Martinez") is True
    
    # 5. Valid facts
    assert is_invalid_hint("Known for a signature thick handlebar mustache", "Tippy Martinez") is False
    assert is_invalid_hint("Won the World Series as a backup catcher", "Tippy Martinez") is False

