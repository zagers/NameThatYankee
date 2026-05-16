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
        
        assert "Skeptical Copy Editor" in prompt
        assert "Tippy Martinez" in prompt
        assert "ONLY use information provided in the dossier" in prompt
