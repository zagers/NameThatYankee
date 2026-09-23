#!/usr/bin/env python3
# ABOUTME: Unit tests for the PlayerImageSearch class.
# ABOUTME: Verifies image candidate extraction, prioritization, and orientation handling.
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

        with patch.object(player_search, '_get_image_candidates_from_bing') as mock_bing, \
             patch.object(player_search, '_get_image_candidates_from_google') as mock_google, \
             patch.object(player_search, '_download_full_size_image') as mock_download, \
             patch.object(player_search.image_processor, 'get_image_info') as mock_info, \
             patch('ai_services.analyze_player_image') as mock_analyze:
            
            # Mock candidate
            mock_bing.return_value = [{'direct_url': 'http://ex.com/1.jpg', 'source_page': 'http://ex.com/1'}]
            mock_google.return_value = []
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
        with patch.object(player_search, '_get_image_candidates_from_bing') as mock_bing, \
             patch.object(player_search, '_get_image_candidates_from_google') as mock_google, \
             patch.object(player_search, '_download_full_size_image') as mock_download, \
             patch.object(player_search.image_processor, 'get_image_info') as mock_info, \
             patch('ai_services.analyze_player_image') as mock_analyze:
            
            # 5 candidates
            mock_bing.return_value = [{'direct_url': f'http://ex.com/{i}.jpg', 'source_page': 'url'} for i in range(5)]
            mock_google.return_value = []
            
            # Mock files
            files = []
            for i in range(5):
                f = temp_dir / f"test_{i}.jpg"
                f.touch()
                files.append(f)
            
            mock_download.side_effect = files
            mock_info.return_value = {'width': 400, 'height': 600}
            
            # All are Priority 1
            mock_analyze.side_effect = [
                {'priority': 1}, {'priority': 1}, {'priority': 1}, {'priority': 1}, {'priority': 1}
            ]
            
            results = player_search.find_first_yankee_image("Test Player", "fake_key")
            
            # Final cut is capped at 3
            assert len(results) == 3
            assert all(r['priority'] == 1 for r in results)
            # But all 5 candidates were evaluated (no early stop at 3 P1s)
            assert mock_analyze.call_count == 5

    def test_find_first_yankee_image_ranking_prefers_playing_era(self, player_search, temp_dir):
        """Test that playing-era Priority 1 ranks above a larger modern reissue Priority 1."""
        with patch.object(player_search, '_get_image_candidates_from_bing') as mock_bing, \
             patch.object(player_search, '_get_image_candidates_from_google') as mock_google, \
             patch.object(player_search, '_download_full_size_image') as mock_download, \
             patch.object(player_search.image_processor, 'get_image_info') as mock_info, \
             patch('ai_services.analyze_player_image') as mock_analyze:
            
            mock_bing.return_value = [
                {'direct_url': 'http://ex.com/reissue.jpg', 'source_page': 'url'},
                {'direct_url': 'http://ex.com/vintage.jpg', 'source_page': 'url'},
            ]
            mock_google.return_value = []
            
            reissue_file = temp_dir / "reissue.jpg"
            vintage_file = temp_dir / "vintage.jpg"
            reissue_file.touch()
            vintage_file.touch()
            mock_download.side_effect = [reissue_file, vintage_file]
            
            # Modern reissue is larger but NOT playing-era; vintage card is smaller but IS playing-era
            mock_info.side_effect = [
                {'width': 800, 'height': 1200},
                {'width': 400, 'height': 600},
            ]
            mock_analyze.side_effect = [
                {'priority': 1, 'reasoning': 'reissue', 'is_playing_era_card': False},
                {'priority': 1, 'reasoning': 'vintage', 'is_playing_era_card': True},
            ]
            
            results = player_search.find_first_yankee_image("Berra", "fake_key")
            
            assert len(results) > 0
            # The playing-era card must be ranked first despite being smaller
            assert results[0]['direct_url'] == 'http://ex.com/vintage.jpg'

    def test_find_first_yankee_image_ranking_prefers_larger_pixels(self, player_search, temp_dir):
        """Test that within the same priority/era, higher resolution is ranked first."""
        with patch.object(player_search, '_get_image_candidates_from_bing') as mock_bing, \
             patch.object(player_search, '_get_image_candidates_from_google') as mock_google, \
             patch.object(player_search, '_download_full_size_image') as mock_download, \
             patch.object(player_search.image_processor, 'get_image_info') as mock_info, \
             patch('ai_services.analyze_player_image') as mock_analyze:
            
            mock_bing.return_value = [
                {'direct_url': 'http://ex.com/small.jpg', 'source_page': 'url'},
                {'direct_url': 'http://ex.com/large.jpg', 'source_page': 'url'},
            ]
            mock_google.return_value = []
            
            small_file = temp_dir / "small.jpg"
            large_file = temp_dir / "large.jpg"
            small_file.touch()
            large_file.touch()
            mock_download.side_effect = [small_file, large_file]
            
            # Both playing-era Priority 1, but different resolutions
            mock_info.side_effect = [
                {'width': 400, 'height': 600},
                {'width': 1600, 'height': 2400},
            ]
            mock_analyze.side_effect = [
                {'priority': 1, 'reasoning': 'small', 'is_playing_era_card': True},
                {'priority': 1, 'reasoning': 'large', 'is_playing_era_card': True},
            ]
            
            results = player_search.find_first_yankee_image("Berra", "fake_key")
            
            assert len(results) > 0
            assert results[0]['direct_url'] == 'http://ex.com/large.jpg'

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

    def test_landscape_image_accepted_for_ai_eval(self, player_search, temp_dir):
        """Test that landscape images are accepted for AI evaluation instead of being rejected."""
        test_img = temp_dir / "landscape.jpg"
        test_img.touch()

        with patch.object(player_search, '_get_image_candidates_from_bing') as mock_bing, \
             patch.object(player_search, '_get_image_candidates_from_google') as mock_google, \
             patch.object(player_search, '_download_full_size_image') as mock_download, \
             patch.object(player_search.image_processor, 'get_image_info') as mock_info, \
             patch('ai_services.analyze_player_image') as mock_analyze:
            
            mock_bing.return_value = [{'direct_url': 'url', 'source_page': 'page'}]
            mock_google.return_value = []
            mock_download.return_value = test_img
            # Landscape: width > height
            mock_info.return_value = {'width': 800, 'height': 600}
            # Mock AI rejecting it eventually (but it should REACH the AI)
            mock_analyze.return_value = {'priority': 4} # Rejected by AI
            
            results = player_search.find_first_yankee_image("Test Player", api_key="fake")
            
            # Results should be empty because AI rejected it, but mock_analyze should have been called
            assert len(results) == 0
            assert mock_analyze.called
            assert not test_img.exists() # Should be unlinked after rejection

    def test_career_span_threaded_to_ai(self, player_search, temp_dir):
        """Test that career_span is forwarded down to ai_services.analyze_player_image."""
        test_img = temp_dir / "era.jpg"
        test_img.touch()

        with patch.object(player_search, '_get_image_candidates_from_bing') as mock_bing, \
             patch.object(player_search, '_get_image_candidates_from_google') as mock_google, \
             patch.object(player_search, '_download_full_size_image') as mock_download, \
             patch.object(player_search.image_processor, 'get_image_info') as mock_info, \
             patch('ai_services.analyze_player_image') as mock_analyze:

            mock_bing.return_value = [{'direct_url': 'url', 'source_page': 'page'}]
            mock_google.return_value = []
            mock_download.return_value = test_img
            mock_info.return_value = {'width': 400, 'height': 600}
            mock_analyze.return_value = {'priority': 1, 'reasoning': 'Perfect'}

            results = player_search.find_first_yankee_image("Berra", api_key="fake", career_span=[1946, 1963])

            assert len(results) == 1
            _, kwargs = mock_analyze.call_args
            assert kwargs.get('career_span') == [1946, 1963]

    def test_career_span_defaults_to_none(self, player_search, temp_dir):
        """Test that career_span defaults to None when not provided."""
        test_img = temp_dir / "era_default.jpg"
        test_img.touch()

        with patch.object(player_search, '_get_image_candidates_from_bing') as mock_bing, \
             patch.object(player_search, '_get_image_candidates_from_google') as mock_google, \
             patch.object(player_search, '_download_full_size_image') as mock_download, \
             patch.object(player_search.image_processor, 'get_image_info') as mock_info, \
             patch('ai_services.analyze_player_image') as mock_analyze:

            mock_bing.return_value = [{'direct_url': 'url', 'source_page': 'page'}]
            mock_google.return_value = []
            mock_download.return_value = test_img
            mock_info.return_value = {'width': 400, 'height': 600}
            mock_analyze.return_value = {'priority': 1, 'reasoning': 'Perfect'}

            results = player_search.find_first_yankee_image("Berra", api_key="fake")

            assert 'career_span' in mock_analyze.call_args[1]
            assert mock_analyze.call_args[1]['career_span'] is None

    def test_download_and_process_threads_career_span(self, player_search, temp_dir):
        """Test that download_and_process_player_image forwards career_span to find_first_yankee_image."""
        staging_dir = temp_dir / "temp_player_images"
        staging_dir.mkdir(exist_ok=True)

        with patch.object(player_search, 'find_first_yankee_image') as mock_find, \
             patch.object(player_search.image_processor, 'convert_to_webp'):
            mock_find.return_value = []

            player_search.download_and_process_player_image("Berra", "2026-03-07", api_key="fake", career_span=[1946, 1963])

            _, kwargs = mock_find.call_args
            assert kwargs.get('career_span') == [1946, 1963]

    def test_download_and_process_dedupes_near_duplicate_images(self, player_search, temp_dir):
        """Test that visually identical candidates from different URLs are not both staged."""
        staging_dir = temp_dir / "temp_player_images"
        staging_dir.mkdir(exist_ok=True)

        first = temp_dir / "first.jpg"
        second = temp_dir / "second.jpg"
        img_a = Image.new('RGB', (400, 600), color='blue')
        draw_a = ImageDraw.Draw(img_a)
        draw_a.rectangle([50, 50, 350, 550], fill='red')
        draw_a.ellipse([100, 200, 300, 400], fill='green')
        img_a.save(first, 'JPEG', quality=90)
        img_a.save(second, 'JPEG', quality=60)

        mock_results = [
            {'temp_file': first, 'priority': 1},
            {'temp_file': second, 'priority': 1},
        ]

        with patch.object(player_search, 'find_first_yankee_image') as mock_find, \
             patch.object(player_search.image_processor, 'convert_to_webp'):
            mock_find.return_value = mock_results

            final_paths = player_search.download_and_process_player_image("Berra", "2026-03-07", api_key="fake")

            assert len(final_paths) == 1

    def test_download_and_process_keeps_distinct_images(self, player_search, temp_dir):
        """Test that visually distinct candidates are both staged."""
        staging_dir = temp_dir / "temp_player_images"
        staging_dir.mkdir(exist_ok=True)

        first = temp_dir / "first.jpg"
        second = temp_dir / "second.jpg"
        img_a = Image.new('RGB', (400, 600), color='blue')
        draw_a = ImageDraw.Draw(img_a)
        draw_a.rectangle([50, 50, 350, 500], fill='red')
        img_a.save(first, 'JPEG')
        img_b = Image.new('RGB', (400, 600), color='black')
        draw_b = ImageDraw.Draw(img_b)
        draw_b.rectangle([100, 400, 200, 500], fill='white')
        img_b.save(second, 'JPEG')

        mock_results = [
            {'temp_file': first, 'priority': 1},
            {'temp_file': second, 'priority': 1},
        ]

        with patch.object(player_search, 'find_first_yankee_image') as mock_find, \
             patch.object(player_search.image_processor, 'convert_to_webp'):
            mock_find.return_value = mock_results

            final_paths = player_search.download_and_process_player_image("Berra", "2026-03-07", api_key="fake")

            assert len(final_paths) == 2
