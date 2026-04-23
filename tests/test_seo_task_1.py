# ABOUTME: Test for SEO Remediation Task 1: Static noindex in quiz.html
import pytest
from bs4 import BeautifulSoup
import os

def test_quiz_has_static_noindex():
    quiz_path = os.path.join(os.path.dirname(__file__), '..', 'quiz.html')
    with open(quiz_path, 'r') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    robots_meta = soup.find('meta', attrs={'name': 'robots', 'content': 'noindex'})
    
    assert robots_meta is not None, "quiz.html should have a static <meta name='robots' content='noindex'>"
    assert robots_meta.parent.name == 'head', "robots meta tag should be in the head section"

def test_quiz_has_simplified_canonical_script():
    quiz_path = os.path.join(os.path.dirname(__file__), '..', 'quiz.html')
    with open(quiz_path, 'r') as f:
        html = f.read()
    
    # Check if the old JS-based noindex injection is gone
    assert 'const meta = document.createElement(\'meta\');' not in html
    assert 'meta.name = \'robots\';' not in html
    assert 'meta.content = \'noindex\';' not in html
    
    # Check for the presence of the canonical script
    assert 'const canonical = document.createElement(\'link\');' in html
    assert 'canonical.rel = \'canonical\';' in html
