#!/usr/bin/env python3
"""
Tests for the AutomatedWorkflow class in the automation module.
"""

import pytest
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw
from unittest.mock import Mock, patch, MagicMock
import sys
import json

# Add the page-generator directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "page-generator"))

from automation.automated_workflow import AutomatedWorkflow
from automation.image_processor import ImageProcessor
from automation.player_image_search import PlayerImageSearch
from automation.git_integration import GitIntegration


class TestAutomatedWorkflow:
    """Test cases for AutomatedWorkflow functionality."""

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
    def sample_screenshot(self, temp_dir):
        """Create a sample screenshot for testing."""
        screenshot_path = temp_dir / "screenshot.png"
        img = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(img)
        draw.rectangle([100, 100, 700, 500], fill='lightblue')
        draw.text((350, 280), "Puzzle Screenshot", fill='black')
        img.save(screenshot_path, 'PNG')
        return screenshot_path

    @pytest.fixture
    def automated_workflow(self, images_dir):
        """Create an AutomatedWorkflow instance."""
        config = {"gemini_api_key": "test_api_key", "auto_commit": True}
        return AutomatedWorkflow(images_dir.parent, config)

    def test_init(self, images_dir):
        """Test AutomatedWorkflow initialization."""
        config = {"gemini_api_key": "test_api_key"}
        workflow = AutomatedWorkflow(images_dir.parent, config)
        
        assert workflow.images_dir == images_dir
        assert workflow.api_key == "test_api_key"
        assert isinstance(workflow.image_processor, ImageProcessor)
        assert isinstance(workflow.player_image_search, PlayerImageSearch)
        assert isinstance(workflow.git_integration, GitIntegration)

    def test_process_puzzle_screenshot_success(self, automated_workflow, sample_screenshot):
        """Test successful puzzle screenshot processing."""
        with patch.object(automated_workflow, '_identify_player') as mock_identify, \
             patch.object(automated_workflow, '_scrape_player_stats') as mock_scrape, \
             patch.object(automated_workflow, '_generate_ai_content') as mock_ai, \
             patch.object(automated_workflow, '_find_player_image') as mock_image, \
             patch.object(automated_workflow, '_perform_git_operations') as mock_git:
            
            # Mock successful responses
            mock_identify.return_value = {'name': 'Test Player', 'position': 'SS'}
            mock_scrape.return_value = {'career_totals': {'HR': 100}, 'yearly_war': []}
            mock_ai.return_value = None
            mock_image.return_value = Path('/tmp/answer.webp')
            mock_git.return_value = True
            
            result = automated_workflow.process_puzzle_screenshot(sample_screenshot, "2025-03-06")
            
            assert result is True
            mock_identify.assert_called_once()
            mock_scrape.assert_called_once_with('Test Player')
            mock_ai.assert_called_once()
            mock_image.assert_called_once_with('Test Player', '2025-03-06')
            # Git operations should be called by default
            mock_git.assert_called_once()

    def test_process_puzzle_screenshot_identification_failure(self, automated_workflow, sample_screenshot):
        """Test puzzle screenshot processing when player identification fails."""
        with patch.object(automated_workflow, '_identify_player') as mock_identify:
            mock_identify.return_value = None
            
            result = automated_workflow.process_puzzle_screenshot(sample_screenshot, "2025-03-06")
            
            assert result is False

    def test_process_puzzle_screenshot_missing_file(self, automated_workflow, temp_dir):
        """Test puzzle screenshot processing with missing file."""
        missing_file = temp_dir / "missing.png"
        
        result = automated_workflow.process_puzzle_screenshot(missing_file, "2025-03-06")
        
        assert result is False

    def test_identify_player_success(self, automated_workflow, temp_dir):
        """Test successful player identification."""
        with patch('automation.automated_workflow.ai_services') as mock_ai_services:
            mock_ai_services.get_player_info_from_image.return_value = {
                'name': 'Test Player',
                'position': 'SS',
                'team': 'Yankees'
            }
            
            clue_path = str(temp_dir / "clue-2025-03-06.webp")
            
            result = automated_workflow._identify_player(clue_path)
            
            assert result is not None
            assert result['name'] == 'Test Player'
            assert result['position'] == 'SS'

    def test_identify_player_unknown(self, automated_workflow, temp_dir):
        """Test player identification when AI returns 'Unknown'."""
        with patch('automation.automated_workflow.ai_services') as mock_ai_services:
            mock_ai_services.get_player_info_from_image.return_value = {
                'name': 'Unknown',
                'position': 'Unknown'
            }
            
            clue_path = str(temp_dir / "clue-2025-03-06.webp")
            
            result = automated_workflow._identify_player(clue_path)
            
            assert result is not None
            assert result['name'] == 'Unknown'

    def test_identify_player_failure(self, automated_workflow, temp_dir):
        """Test player identification when AI service fails."""
        with patch('automation.automated_workflow.ai_services') as mock_ai_services:
            mock_ai_services.get_player_info_from_image.return_value = None
            
            clue_path = str(temp_dir / "clue-2025-03-06.webp")
            
            result = automated_workflow._identify_player(clue_path)
            
            assert result is None

    def test_identify_player_exception(self, automated_workflow, temp_dir):
        """Test player identification when AI service raises exception."""
        with patch('automation.automated_workflow.ai_services') as mock_ai_services:
            mock_ai_services.get_player_info_from_image.side_effect = Exception("API Error")
            
            clue_path = str(temp_dir / "clue-2025-03-06.webp")
            
            result = automated_workflow._identify_player(clue_path)
            
            assert result is None

    def test_scrape_player_stats_success(self, automated_workflow):
        """Test successful player stats scraping."""
        with patch('automation.automated_workflow.scraper') as mock_scraper:
            mock_scraper.search_and_scrape_player.return_value = {
                'career_totals': {'HR': 100, 'AVG': 0.300},
                'yearly_war': [{'year': 2023, 'war': 2.5}]
            }
            
            result = automated_workflow._scrape_player_stats("Test Player")
            
            assert result is not None
            assert 'career_totals' in result
            assert 'yearly_war' in result

    def test_scrape_player_stats_failure(self, automated_workflow):
        """Test player stats scraping when scraper fails."""
        with patch('automation.automated_workflow.scraper') as mock_scraper:
            mock_scraper.search_and_scrape_player.return_value = None
            
            result = automated_workflow._scrape_player_stats("Test Player")
            
            assert result is None

    def test_scrape_player_stats_unknown_player(self, automated_workflow):
        """Test player stats scraping for 'Unknown' player."""
        result = automated_workflow._scrape_player_stats("Unknown")
        
        assert result is None

    def test_generate_ai_content_success(self, automated_workflow):
        """Test successful AI content generation."""
        with patch('automation.automated_workflow.ai_services') as mock_ai_services:
            mock_ai_services.get_facts_and_followup_from_gemini.return_value = {
                'facts': ['Fact 1', 'Fact 2'],
                'qa': [{'q': 'Question 1', 'a': 'Answer 1'}]
            }
            
            player_info = {'name': 'Test Player'}
            
            automated_workflow._generate_ai_content(player_info)
            
            assert player_info['facts'] == ['Fact 1', 'Fact 2']
            assert player_info['followup_qa'] == [{'q': 'Question 1', 'a': 'Answer 1'}]

    def test_generate_ai_content_unknown_player(self, automated_workflow):
        """Test AI content generation for 'Unknown' player."""
        player_info = {'name': 'Unknown'}
        
        automated_workflow._generate_ai_content(player_info)
        
        assert player_info['facts'] == []
        assert player_info['followup_qa'] == []

    def test_generate_ai_content_failure(self, automated_workflow):
        """Test AI content generation when service fails."""
        with patch('automation.automated_workflow.ai_services') as mock_ai_services:
            mock_ai_services.get_facts_and_followup_from_gemini.side_effect = Exception("API Error")
            
            player_info = {'name': 'Test Player'}
            
            automated_workflow._generate_ai_content(player_info)
            
            assert player_info['facts'] == []
            assert player_info['followup_qa'] == []

    def test_find_player_image_success(self, automated_workflow, temp_dir):
        """Test successful player image finding."""
        mock_file = temp_dir / "answer.webp"
        mock_file.touch()
        with patch.object(automated_workflow.player_image_search, 'download_and_process_player_image') as mock_download:
            mock_download.return_value = [mock_file]
            
            result = automated_workflow._find_player_image("Test Player", "2025-03-06")
            
            assert result is not None
            assert result.name == "answer-2025-03-06.webp"

    def test_find_player_image_unknown_player(self, automated_workflow):
        """Test player image finding for 'Unknown' player."""
        result = automated_workflow._find_player_image("Unknown", "2025-03-06")
        
        assert result is None

    def test_find_player_image_failure(self, automated_workflow):
        """Test player image finding when search fails."""
        with patch.object(automated_workflow.player_image_search, 'download_and_process_player_image') as mock_download:
            
            mock_download.return_value = []
            
            result = automated_workflow._find_player_image("Test Player", "2025-03-06")
            
            # The method returns None when no image is found
            assert result is None

    def test_perform_git_operations_success(self, automated_workflow, temp_dir):
        """Test successful git operations."""
        # Create mock files that the method will look for
        (temp_dir / "images" / "clue-2025-03-06.webp").touch()
        (temp_dir / "images" / "answer-2025-03-06.webp").touch()
        (temp_dir / "2025-03-06.html").touch()
        
        with patch.object(automated_workflow.git_integration, 'add_files') as mock_add, \
             patch.object(automated_workflow.git_integration, 'safe_commit_and_push') as mock_git:
            
            mock_add.return_value = True  # Files were added successfully
            mock_git.return_value = True
            
            result = automated_workflow._perform_git_operations("2025-03-06")
            
            assert result is True

    def test_perform_git_operations_failure(self, automated_workflow):
        """Test git operations when they fail."""
        with patch.object(automated_workflow.git_integration, 'safe_commit_and_push') as mock_git:
            mock_git.return_value = False
            
            result = automated_workflow._perform_git_operations("2025-03-06")
            
            assert result is False

    def test_process_puzzle_screenshot_partial_failure_continues(self, automated_workflow, sample_screenshot):
        """Test that workflow continues even when some steps fail."""
        with patch.object(automated_workflow, '_identify_player') as mock_identify, \
             patch.object(automated_workflow, '_scrape_player_stats') as mock_scrape, \
             patch.object(automated_workflow, '_generate_ai_content') as mock_ai, \
             patch.object(automated_workflow, '_find_player_image') as mock_image, \
             patch.object(automated_workflow, '_perform_git_operations') as mock_git:
            
            # Mock some failures
            mock_identify.return_value = {'name': 'Test Player', 'position': 'SS'}
            mock_scrape.return_value = None  # Stats scraping fails
            mock_ai.return_value = None
            mock_image.return_value = None  # Image search fails
            mock_git.return_value = True
            
            result = automated_workflow.process_puzzle_screenshot(sample_screenshot, "2025-03-06")
            
            assert result is True  # Should still succeed despite failures
            mock_identify.assert_called_once()
            mock_scrape.assert_called_once()
            mock_ai.assert_called_once()
            mock_image.assert_called_once()
            mock_git.assert_called_once()
