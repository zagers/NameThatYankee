import pytest  # type: ignore
import errno
import json
import socket
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


# The exact failure observed on a captive-portal network (airplane wifi), where the
# resolver intermittently exceeds glibc's 5s timeout and raises gaierror(EAI_AGAIN).
# NOTE: EAI_* constants are exposed by `socket`, not `errno`, on this platform.
DNS_ERROR = socket.gaierror(socket.EAI_AGAIN, "Temporary failure in name resolution")


def test_get_player_info_from_image_retries_on_dns_failure(mock_genai_client, mocker):
    mocker.patch("ai_services.Image.open")

    good_response = MagicMock()
    good_response.text = '{"name": "Lou Gehrig", "nickname": "The Iron Horse"}'
    mock_genai_client.side_effect = [DNS_ERROR, good_response]

    result = ai_services.get_player_info_from_image("fake_path.webp", "fake_key")

    assert result is not None, "DNS failure must not abort identification; it must be retried"
    assert result["name"] == "Lou Gehrig"
    assert mock_genai_client.call_count == 2


def test_get_facts_from_gemini_retries_on_dns_failure(mock_genai_client):
    good_response = MagicMock()
    good_response.text = '{"facts": ["Fact 1", "Fact 2"]}'
    mock_genai_client.side_effect = [DNS_ERROR, good_response]

    result = ai_services.get_facts_from_gemini("Mickey Mantle", "fake_key")

    assert result == ["Fact 1", "Fact 2"], "DNS failure must not abort facts; it must be retried"
    assert mock_genai_client.call_count == 2


def _api_error(code, message="boom"):
    err = errors.APIError(message, response_json={})
    err.code = code
    return err


@pytest.mark.parametrize("exc", [
    socket.gaierror(socket.EAI_AGAIN, "Temporary failure in name resolution"),
    socket.gaierror(socket.EAI_NONAME, "Name or service not known"),
    ConnectionResetError(errno.ECONNRESET, "Connection reset by peer"),
    TimeoutError(errno.ETIMEDOUT, "timed out"),
    _api_error(429, "Resource exhausted"),
    _api_error(503, "Service unavailable"),
    RuntimeError("Server disconnected without sending a response."),
    RuntimeError("All connection attempts failed"),
], ids=[
    "dns_eaiagain", "dns_eainoname", "conn_reset", "timed_out",
    "api_429", "api_503", "msg_server_disconnected", "msg_all_conn_failed",
])
def test_is_retryable_error_true_for_transient_failures(exc):
    assert ai_services._is_retryable_error(exc) is True


@pytest.mark.parametrize("exc", [
    _api_error(400, "Invalid argument"),
    _api_error(401, "Unauthorized"),
    _api_error(403, "Permission denied"),
    ValueError("Expecting value: line 1 column 1"),
    PermissionError(errno.EACCES, "Permission denied"),
    FileNotFoundError(errno.ENOENT, "No such file or directory"),
], ids=[
    "api_400", "api_401", "api_403", "malformed_json", "permission_denied", "missing_file",
])
def test_is_retryable_error_false_for_permanent_failures(exc):
    assert ai_services._is_retryable_error(exc) is False

