# Batch API Client Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a `BatchClient` to interact with the Google GenAI Batch API for upgrading historical trivia quizzes.

**Architecture:** A thin wrapper around `google.genai` to manage file uploads, batch job creation, and status monitoring.

**Tech Stack:** Python, `google-genai` library.

---

### Task 1: Implement BatchClient

**Files:**
- Create: `page-generator/batch/client.py`

- [ ] **Step 1: Create the file with basic structure and imports**
```python
# ABOUTME: Client for interacting with the Google GenAI Batch API.
# ABOUTME: Manages file uploads, job creation, and status tracking for batch processing.

from google import genai
from google.genai import types
import os

class BatchClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment or passed to constructor")
        self.client = genai.Client(api_key=self.api_key)
```

- [ ] **Step 2: Implement `submit_batch` method**
```python
    def submit_batch(self, jsonl_path, model="gemini-3.1-flash-lite"):
        # Upload the file
        f = self.client.files.upload(path=jsonl_path)
        
        # Create the batch job
        job = self.client.batches.create(
            model=model,
            src=f.name
        )
        return job
```

- [ ] **Step 3: Implement `get_job` (or `get_status`) method**
```python
    def get_job(self, job_name):
        return self.client.batches.get(name=job_name)
```

- [ ] **Step 4: Implement `download_results` method**
```python
    def download_results(self, job_name, output_path):
        job = self.get_job(job_name)
        if job.state != "SUCCEEDED":
            raise ValueError(f"Job {job_name} is not in SUCCEEDED state (current state: {job.state})")
        
        # In Gemini Developer API, results are in job.output_config.dest
        # Or more simply, the library might provide a way to download.
        # Based on typical genai client:
        result_file = job.results_file
        if not result_file:
             raise ValueError(f"Job {job_name} has no results_file")
             
        self.client.files.download(name=result_file, path=output_path)
```

---

### Task 2: Unit Testing with Mocking

**Files:**
- Create: `tests/unit/page_generator/batch/test_client.py`

- [ ] **Step 1: Write failing test (RED)**
```python
import pytest
from unittest.mock import MagicMock, patch
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
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/unit/page_generator/batch/test_client.py`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Implement minimal code**

- [ ] **Step 4: Run test to verify it passes (GREEN)**
Run: `pytest tests/unit/page_generator/batch/test_client.py`

- [ ] **Step 5: Commit**
```bash
git add page-generator/batch/client.py tests/unit/page_generator/batch/test_client.py
git commit -m "feat: implement Gemini Batch API client"
```
