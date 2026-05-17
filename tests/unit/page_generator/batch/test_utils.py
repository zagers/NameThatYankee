# ABOUTME: Unit tests for batch processing utilities.
# ABOUTME: Verifies state management and progress tracking logic.

import pytest
import tempfile
from pathlib import Path
import json

def test_state_management():
    from batch.utils import StateManager
    
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "progress.json"
        manager = StateManager(state_path)
        
        # Initial state should be empty
        assert manager.get_status("2025-04-01") is None
        
        # Set and save
        manager.set_status("2025-04-01", "scraped", {"player": "Don Mattingly"})
        manager.save()
        
        # Load in new instance
        new_manager = StateManager(state_path)
        assert new_manager.get_status("2025-04-01") == "scraped"
        assert new_manager.get_data("2025-04-01")["player"] == "Don Mattingly"
