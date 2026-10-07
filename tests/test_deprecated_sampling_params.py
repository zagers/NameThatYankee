# ABOUTME: Guards Gemini requests against generation parameters Google has deprecated.
# ABOUTME: Fails if source sets temperature/top_p/top_k/thinking_budget or sends them to the API.

import re
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = PROJECT_ROOT / "page-generator"
DEPRECATED_PARAM = re.compile(r"\b(temperature|top_p|top_k|thinking_budget)\s*=")

sys.path.insert(0, str(SOURCE_ROOT))


def test_no_deprecated_generation_parameters_in_source():
    offenders = []
    for path in sorted(SOURCE_ROOT.rglob("*.py")):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if DEPRECATED_PARAM.search(line):
                offenders.append(f"{path.relative_to(PROJECT_ROOT)}:{lineno}: {line.strip()}")
    assert not offenders, (
        "Google rejects these generation parameters with 400 INVALID_ARGUMENT:\n"
        + "\n".join(offenders)
    )


def _assert_config_has_no_deprecated_params(mock_generate):
    config = mock_generate.call_args.kwargs["config"]
    assert config.temperature is None
    assert config.top_p is None
    assert config.top_k is None
    assert getattr(config, "thinking_budget", None) is None


def test_get_facts_config_omits_sampling_params(mocker):
    import ai_services

    mocker.patch("ai_services._respect_free_tier_rate_limit")
    mocker.patch("time.sleep")
    mock_client_cls = mocker.patch("ai_services.genai.Client")
    mock_client = mock_client_cls.return_value
    mock_response = MagicMock()
    mock_response.text = '{"facts": ["Fact 1", "Fact 2", "Fact 3"]}'
    mock_client.models.generate_content.return_value = mock_response

    ai_services.get_facts_from_gemini("Mickey Mantle", "fake_key")

    mock_client.models.generate_content.assert_called()
    _assert_config_has_no_deprecated_params(mock_client.models.generate_content)


def test_grounded_trivia_config_omits_sampling_params(mocker):
    import grounded_ai

    mocker.patch("grounded_ai._respect_free_tier_rate_limit")
    mocker.patch("grounded_ai.genai.Client")
    mock_client = grounded_ai.genai.Client.return_value
    mock_response = MagicMock()
    mock_response.text = (
        '{"facts": ["Fact 1", "Fact 2", "Fact 3"], '
        '"qa": [{"question": "Q1", "answer": "A1"}, '
        '{"question": "Q2", "answer": "A2"}, '
        '{"question": "Q3", "answer": "A3"}], '
        '"claims": ["Claim 1", "Claim 2"]}'
    )
    mock_client.models.generate_content.return_value = mock_response

    dossier = {
        "name": "Tippy Martinez",
        "career_totals": {"ERA": "3.45", "Saves": "115"},
        "yearly_war": [{"year": "1983", "war": 2.5}],
        "transactions": [],
        "awards": ["1x All-Star"],
        "bio": "Known for the pickoff play...",
    }
    grounded_ai.generate_grounded_trivia(dossier, "fake_key")

    mock_client.models.generate_content.assert_called()
    _assert_config_has_no_deprecated_params(mock_client.models.generate_content)
