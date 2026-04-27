import sys
from pathlib import Path
import pytest

# Add page-generator to path
sys.path.append(str(Path(__file__).parent.parent / "page-generator"))

from html_generator import generate_gallery_snippet

def test_generate_gallery_snippet_includes_reveal_flag():
    date_str = "2026-04-26"
    formatted_date = "April 26, 2026"
    search_terms = "test terms"
    
    snippet = generate_gallery_snippet(0, date_str, formatted_date, search_terms)
    
    # Check that the link to the answer page includes ?reveal=true
    assert f'href="{date_str}?reveal=true"' in snippet
    assert 'class="gallery-item"' in snippet
    assert 'class="action-link reveal-link"' in snippet
    
    # The quiz link should NOT have reveal=true
    assert f'href="quiz?date={date_str}"' in snippet
