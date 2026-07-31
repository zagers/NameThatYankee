# ABOUTME: Tests for the automated puzzle workflow content generation.
# ABOUTME: Verifies that the stats fallback produces facts when grounded AI generation fails.

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "page-generator"))

from automation.automated_workflow import AutomatedWorkflow


def _make_workflow():
    workflow = object.__new__(AutomatedWorkflow)
    workflow.api_key = "fake_api_key"
    return workflow


def test_fallback_facts_are_kept_when_grounded_ai_returns_empty():
    workflow = _make_workflow()
    player_info = {"name": "Dámaso Marte", "scraped_data": {}}

    player_dossier = {
        "name": "Dámaso Marte",
        "career_totals": {},
        "yearly_war": [],
        "transactions": [],
        "awards": [],
        "positions": {},
        "bio": "",
    }

    empty_result = {"facts": [], "qa": [], "claims": []}
    fallback_facts = [
        "Veteran major league pitcher with a multi-season career in the big leagues.",
        "Featured primarily as a defensive presence at the pitcher position.",
        "Wore the pinstripes in New York during his career as a valuable veteran contributor.",
    ]

    with patch("automation.automated_workflow.grounded_ai.generate_grounded_trivia", return_value=empty_result) as mock_generate, \
         patch("automation.automated_workflow.fact_verifier.verify_claims", return_value=True) as mock_verify, \
         patch("automation.automated_workflow.scraper.generate_stats_fallback", return_value=fallback_facts) as mock_fallback, \
         patch("automation.automated_workflow.ai_services.get_followup_qa_from_gemini", return_value=[{"question": "Q", "answer": "A"}]) as mock_qa:
        workflow._generate_ai_content(player_info)

        assert mock_generate.call_count == 3
        assert mock_verify.call_count == 3
        mock_fallback.assert_called_once_with(player_dossier)
        mock_qa.assert_called_once()
        assert player_info["facts"] == fallback_facts
        assert player_info["followup_qa"] == [{"question": "Q", "answer": "A"}]


def test_fallback_facts_are_kept_when_verification_fails():
    workflow = _make_workflow()
    player_info = {"name": "Dámaso Marte", "scraped_data": {}}

    player_dossier = {
        "name": "Dámaso Marte",
        "career_totals": {},
        "yearly_war": [],
        "transactions": [],
        "awards": [],
        "positions": {},
        "bio": "",
    }

    generated_result = {
        "facts": ["Some fact."],
        "qa": [{"question": "Q1", "answer": "A1"}],
        "claims": ["Some claim."],
    }
    fallback_facts = ["Fallback fact 1.", "Fallback fact 2.", "Fallback fact 3."]

    with patch("automation.automated_workflow.grounded_ai.generate_grounded_trivia", return_value=generated_result) as mock_generate, \
         patch("automation.automated_workflow.fact_verifier.verify_claims", return_value=False) as mock_verify, \
         patch("automation.automated_workflow.scraper.generate_stats_fallback", return_value=fallback_facts) as mock_fallback, \
         patch("automation.automated_workflow.ai_services.get_followup_qa_from_gemini", return_value=[]) as mock_qa:
        workflow._generate_ai_content(player_info)

        assert mock_generate.call_count == 3
        assert mock_verify.call_count == 3
        mock_fallback.assert_called_once_with(player_dossier)
        mock_qa.assert_called_once()
        assert player_info["facts"] == fallback_facts
