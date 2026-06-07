# ABOUTME: Unit tests for clue quality filters in grounded_ai.py.
# ABOUTME: Verifies that spoilers, generic filler, and boring phrases are correctly rejected.

import sys
from pathlib import Path
import pytest

# Add the page-generator directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "page-generator"))

from grounded_ai import is_invalid_hint, contains_hall_of_boredom, contains_spoiler

def test_is_invalid_hint_generic_phrases():
    """Test that generic phrases like 'utility player' are rejected."""
    player = "Eduardo Nunez"
    assert is_invalid_hint("He was a versatile utility player for the club.", player) is True
    assert is_invalid_hint("Signed as an amateur free agent in 2004.", player) is True
    assert is_invalid_hint("Played for multiple organizations during his career.", player) is True
    assert is_invalid_hint("Filling gaps at multiple infield positions.", player) is True
    assert is_invalid_hint("His professional journey took him to many cities.", player) is True

def test_is_invalid_hint_distinctive_phrases():
    """Test that distinctive phrases (narrative hooks) are accepted."""
    player = "Eduardo Nunez"
    # These should be valid as they are specific/narrative
    assert is_invalid_hint("Known for frequently losing his helmet while running the bases.", player) is False
    assert is_invalid_hint("Served as the primary backup to the legendary Captain.", player) is False
    assert is_invalid_hint("Once hit a walk-off home run in a critical September game.", player) is False

def test_is_invalid_hint_spoilers():
    """Test that spoilers (names, years, teams) are rejected."""
    player = "Eduardo Nunez"
    # Name parts
    assert is_invalid_hint("Eduardo was a great player.", player) is True
    assert is_invalid_hint("Nunez played well.", player) is True
    
    # Years
    assert is_invalid_hint("In 2010, he made his debut.", player) is True
    assert is_invalid_hint("He won a ring in 2018.", player) is True
    
    # Team names
    assert is_invalid_hint("He played for the Yankees.", player) is True
    assert is_invalid_hint("He was traded to the Red Sox.", player) is True
    assert is_invalid_hint("He spent time in San Francisco.", player) is True
    assert is_invalid_hint("He played for the Giants.", player) is True

def test_contains_hall_of_boredom():
    """Test that meta-commentary and low-quality filler are detected."""
    # Case 1: SABR mention
    result_sabr = {
        "facts": ["A great player."],
        "qa": [{"question": "What does SABR say?", "answer": "He was good."}]
    }
    has_junk, word = contains_hall_of_boredom(result_sabr)
    assert has_junk is True
    assert word == "sabr"
    
    # Case 2: Biography remains
    result_bio = {
        "facts": ["The biography remains unassigned."],
        "qa": []
    }
    has_junk, word = contains_hall_of_boredom(result_bio)
    assert has_junk is True
    assert word == "biography remains"
    
    # Case 3: Born on
    result_born = {
        "facts": ["Born on June 15th."],
        "qa": []
    }
    has_junk, word = contains_hall_of_boredom(result_born)
    assert has_junk is True
    assert word == "born on"
    
    # Case 4: Generic phrase from list
    result_generic = {
        "facts": ["He was a utility player."],
        "qa": []
    }
    has_junk, word = contains_hall_of_boredom(result_generic)
    assert has_junk is True
    assert word == "utility player"
    
    # Case 5: Clean result
    result_clean = {
        "facts": ["Losing his helmet was his signature."],
        "qa": [{"question": "Who did he backup?", "answer": "The Captain."}]
    }
    has_junk, word = contains_hall_of_boredom(result_clean)
    assert has_junk is False
    assert word is None

def test_contains_spoiler():
    """Test the separate spoiler check used in the main loop."""
    result = {"facts": ["Eduardo was here."]}
    assert contains_spoiler(result, "Eduardo Nunez") is True
    
    result_clean = {"facts": ["The player was here."]}
    assert contains_spoiler(result_clean, "Eduardo Nunez") is False
    
    # Check parts
    result_part = {"facts": ["Nunez was here."]}
    assert contains_spoiler(result_part, "Eduardo Nunez") is True
