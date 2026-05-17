# ABOUTME: Unit tests for the Gemini Batch API client.
# ABOUTME: Verifies file upload, job creation, and results downloading using mocks.

import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Ensure we can import from page-generator
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root / "page-generator"))

from batch.client import BatchClient

def test_submit_batch():
    mock_client = MagicMock()
    with patch('google.genai.Client', return_value=mock_client):
        client = BatchClient(api_key="test_key")
        
        mock_file = MagicMock()
        mock_file.name = "files/test-file"
        mock_client.files.upload.return_value = mock_file
        
        mock_job = MagicMock()
        mock_job.name = "batches/test-job"
        mock_client.batches.create.return_value = mock_job
        
        job = client.submit_batch("test.jsonl")
        
        assert job.name == "batches/test-job"
        mock_client.files.upload.assert_called_once_with(path="test.jsonl")
        mock_client.batches.create.assert_called_once_with(
            model="gemini-3.1-flash-lite",
            src="files/test-file"
        )

def test_download_results():
    mock_client = MagicMock()
    with patch('google.genai.Client', return_value=mock_client):
        client = BatchClient(api_key="test_key")
        
        mock_job = MagicMock()
        mock_job.state = "SUCCEEDED"
        mock_job.results_file = "files/results-file"
        mock_client.batches.get.return_value = mock_job
        
        client.download_results("batches/test-job", "output.jsonl")
        
        mock_client.batches.get.assert_called_once_with(name="batches/test-job")
        mock_client.files.download.assert_called_once_with(
            name="files/results-file",
            path="output.jsonl"
        )
