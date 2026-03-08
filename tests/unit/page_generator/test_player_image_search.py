#!/usr/bin/env python3
"""
Tests for the PlayerImageSearch class in the automation module.
"""

import pytest
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw
from unittest.mock import Mock, patch, MagicMock
import sys
import base64

# Add the page-generator directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "page-generator"))

from automation.player_image_search import PlayerImageSearch
from automation.image_processor import ImageProcessor


class TestPlayerImageSearch:
    """Test cases for PlayerImageSearch functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def images_dir(self, temp_dir):
        """Create an images directory."""
        images_dir = temp_dir / "images"
        images_dir.mkdir()
        return images_dir

    @pytest.fixture
    def player_search(self, images_dir, temp_dir):
        """Create a PlayerImageSearch instance."""
        return PlayerImageSearch(images_dir, temp_dir)

    @pytest.fixture
    def sample_image_data(self):
        """Create sample image data for testing."""
        img = Image.new('RGB', (400, 600), color='blue')
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 50, 150, 150], fill='red')
        return img

    def test_init(self, images_dir, temp_dir):
        """Test PlayerImageSearch initialization."""
        search = PlayerImageSearch(images_dir, temp_dir)
        
        assert search.images_dir == images_dir
        assert search.temp_dir == temp_dir
        assert isinstance(search.image_processor, ImageProcessor)
        assert 'User-Agent' in search.headers

    def test_find_first_yankee_image_basic(self, player_search, temp_dir):
        """Test finding images with prioritization logic."""
        # Create a mock temp file
        test_img = temp_dir / "test.jpg"
        test_img.touch()

        with patch.object(player_search, '_get_image_candidates_from_google') as mock_google, \
             patch.object(player_search, '_download_full_size_image') as mock_download, \
             patch.object(player_search.image_processor, 'get_image_info') as mock_info, \
             patch('ai_services.analyze_player_image') as mock_analyze:
            
            # Mock candidate
            mock_google.return_value = [{'direct_url': 'http://ex.com/1.jpg', 'source_page': 'http://ex.com/1'}]
            mock_download.return_value = test_img
            mock_info.return_value = {'width': 400, 'height': 600}
            
            # Mock Priority 1 find
            mock_analyze.return_value = {'priority': 1, 'reasoning': 'Perfect'}
            
            results = player_search.find_first_yankee_image("Test Player", "fake_key")
            
            assert len(results) == 1
            assert results[0]['priority'] == 1
            assert results[0]['temp_file'] == test_img

    def test_find_first_yankee_image_collects_three(self, player_search, temp_dir):
        """Test that it collects up to 3 high-priority matches."""
        with patch.object(player_search, '_get_image_candidates_from_google') as mock_google, \
             patch.object(player_search, '_download_full_size_image') as mock_download, \
             patch.object(player_search.image_processor, 'get_image_info') as mock_info, \
             patch('ai_services.analyze_player_image') as mock_analyze:
            
            # 5 candidates
            mock_google.return_value = [{'direct_url': f'http://ex.com/{i}.jpg', 'source_page': 'url'} for i in range(5)]
            
            # Mock files
            files = []
            for i in range(5):
                f = temp_dir / f"test_{i}.jpg"
                f.touch()
                files.append(f)
            
            mock_download.side_effect = files
            mock_info.return_value = {'width': 400, 'height': 600}
            
            # First 3 are Priority 1
            mock_analyze.side_effect = [
                {'priority': 1}, {'priority': 1}, {'priority': 1}, {'priority': 1}, {'priority': 1}
            ]
            
            results = player_search.find_first_yankee_image("Test Player", "fake_key")
            
            # Should stop at 3 Priority 1s
            assert len(results) == 3
            assert all(r['priority'] == 1 for r in results)

    def test_archiving_logic(self, player_search, temp_dir):
        """Test that old candidates are archived to /old subdirectory."""
        staging_dir = temp_dir / "temp_player_images"
        staging_dir.mkdir(exist_ok=True)
        
        # Create an old webp
        old_file = staging_dir / "answer-2025-01-01-1.webp"
        old_file.touch()
        
        # Mock finding 0 new results to focus on the cleanup/archive part
        with patch.object(player_search, 'find_first_yankee_image') as mock_find:
            mock_find.return_value = []
            
            player_search.download_and_process_player_image("Test", "2026-03-07")
            
            # The old file should have been moved
            archive_dir = staging_dir / "old"
            assert archive_dir.exists()
            assert (archive_dir / old_file.name).exists()
            assert not old_file.exists()

    def test_cleanup_temp_files(self, player_search, temp_dir):
        """Test cleanup of temporary download files."""
        # Create some temporary files
        temp_file1 = temp_dir / "download_123.jpg"
        temp_file2 = temp_dir / "download_456.jpg"
        temp_file1.touch()
        temp_file2.touch()
        
        # Verify files exist
        assert temp_file1.exists()
        assert temp_file2.exists()
        
        # Cleanup
        player_search.cleanup_temp_files()
        
        # Verify files are deleted
        assert not temp_file1.exists()
        assert not temp_file2.exists()

    def test_orientation_rejection(self, player_search, temp_dir):
        """Test that landscape images are rejected."""
        test_img = temp_dir / "landscape.jpg"
        test_img.touch()

        with patch.object(player_search, '_get_image_candidates_from_google') as mock_google, \
             patch.object(player_search, '_download_full_size_image') as mock_download, \
             patch.object(player_search.image_processor, 'get_image_info') as mock_info:
            
            mock_google.return_value = [{'direct_url': 'url', 'source_page': 'page'}]
            mock_download.return_value = test_img
            # Landscape: width > height
            mock_info.return_value = {'width': 800, 'height': 600}
            
            results = player_search.find_first_yankee_image("Test Player")
            
            # Results should be empty because candidate was skipped due to orientation
            assert len(results) == 0
            assert not test_img.exists() # Should be unlinked
