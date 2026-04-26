import pytest
from pathlib import Path
import json
from bs4 import BeautifulSoup
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../page-generator')))
from html_generator import rebuild_index_page

def test_rebuild_index_persists_html_without_metadata(tmp_path: Path):
    """
    Tests that a clue image without a corresponding HTML detail page still gets
    added to the index.html gallery, verifying graceful degradation and actual HTML saving.
    """
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    images_dir = project_dir / "images"
    images_dir.mkdir()

    # Create base index.html
    index_path = project_dir / "index.html"
    index_path.write_text('<div class="gallery"></div><footer id="last-updated"></footer>', encoding='utf-8')

    # Create a clue image but NO detail page (missing metadata scenario)
    date_str = "2026-04-20"
    (images_dir / f"clue-{date_str}.webp").write_text("fake image data")

    # Rebuild index
    rebuild_index_page(project_dir)

    # 1. Verify JSON is generated (even if empty/sparse)
    stats_file = project_dir / "stats_summary.json"
    assert stats_file.exists()

    # 2. Verify HTML was actually written and contains the gallery item
    with open(index_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
        
    gallery_div = soup.select_one('.gallery')
    assert gallery_div is not None
    
    # The clue should be present in the HTML even though the JSON data was missing
    gallery_items = gallery_div.find_all('a', class_='gallery-item')
    assert len(gallery_items) == 1
    assert date_str in gallery_items[0]['href']

def test_rebuild_index_handles_missing_index_gracefully(tmp_path: Path, capsys):
    """
    Tests that rebuild_index_page does not throw an error if index.html is missing,
    which is common in sparse test environments.
    """
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    
    # Do NOT create index.html
    
    rebuild_index_page(project_dir)
    
    captured = capsys.readouterr()
    assert "Warning: index.html not found" in captured.out
