# ABOUTME: Unit tests for the batch preparation phase.
# ABOUTME: Verifies the construction of Gemini Batch API requests.

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure page-generator is in sys.path
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "page-generator"))

def test_build_request():
    from batch.prepare import build_request
    dossier = {
        "name": "Test Player",
        "career_totals": {"WAR": "10.5"},
        "yearly_war": [],
        "transactions": [],
        "awards": [],
        "bio": "A long SABR bio..."
    }
    request = build_request(dossier, "2025-04-01")
    
    assert "contents" in request
    assert "Test Player" in str(request)
    assert "Skeptical Storyteller" in str(request)
    assert "2025-04-01" in str(request)
