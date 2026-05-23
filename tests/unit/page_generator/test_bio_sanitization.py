import pytest
from bs4 import BeautifulSoup
import sys
import os

# Add page-generator to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../page-generator")))
import scraper

def test_bio_sanitization_removes_technical_noise():
    html_with_noise = """
    <div class="entry-content">
        <style>.some-css { color: red; }</style>
        <p>Babe Ruth was a baseball player.</p>
        <script>console.log("noise");</script>
        <noscript>This requires JS</noscript>
        <svg><circle cx="50" cy="50" r="40" /></svg>
        <iframe></iframe>
        <div class="base64-noise">data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==</div>
        <p>He played for the  \n\n  Yankees.</p>
        <div class="metadata">Technical metadata: some-random-data</div>
        <div class="json-noise">{"type":"biography","id":"12345","source":"SABR","metadata":{"author":"John Doe","date":"2023-01-01"}}</div>
        <p>Junk text: LnRiLWhlYWRpbmcuaGFzLWJhY2tncm91bmR7cGFkZGluZzowfQ== LnRiLWZpZWxke21hcmdpbi1ib3R0b206MC43NmVtfS50Yi1maWVsZC0tbGVmdHt0ZXh0LWFsaWduOmxlZnR9LnRiLWZpZWxkLS1jZW50ZXJ7dGV4dC1hbGlnbjpjZW50ZXJ9LnRiLWZpZWxkLS1yaWdodHt0ZXh0LWFsaWduOnJpZ2h0fS50Yi1maWVsZF9fc2t5cGVfcHJldmlld3twYWRkaW5nOjEwcHggMjBweDtib3JkZXItcmFkaXVzOjNweDtjb2xvcjojZmZmO2JhY2tncm91bmQ6IzAwYWZlZTtkaXNwbGF5OmlubGluZS1ibG9ja311bC5nbGlkZV9fc2xpZGVze21hcmdpbjowfQ==</p>
        <p>More Metadata: {"version": "1.0", "encoding": "UTF-8"}</p>
        <p>Random alphanumeric string: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a1b2c3d4e5f6g7h8i9j0</p>
    </div>
    """
    soup = BeautifulSoup(html_with_noise, 'html.parser')
    content = soup.select_one('.entry-content')
    
    # In the actual implementation, we will add _clean_bio_text
    # For now, let's see if we can call it (it should fail as it doesn't exist yet)
    try:
        text = scraper._clean_bio_text(content)
    except AttributeError:
        pytest.fail("_clean_bio_text not implemented in scraper.py")
        
    assert "Babe Ruth" in text
    assert "Yankees" in text
    assert "console.log" not in text
    assert "base64" not in text
    assert ".some-css" not in text
    assert "This requires JS" not in text
    assert "<svg" not in text
    assert "<iframe" not in text
    assert "Technical metadata" not in text
    assert "LnRiLWhlYWRpbmcuaGFzLWJhY2tncm91bmR7cGFkZGluZzowfQ==" not in text
    assert '{"type":"biography"' not in text
    assert 'More Metadata:' not in text
    assert 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a1b2c3d4e5f6g7h8i9j0' not in text
    # Check whitespace normalization
    assert "  " not in text
    assert "\n\n" not in text
