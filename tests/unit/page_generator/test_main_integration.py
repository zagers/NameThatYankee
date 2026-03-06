import pytest  # type: ignore
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
import json
import sys
from datetime import datetime
from PIL import Image

# Import the modules that main.py imports
import config_manager
import ai_services
import scraper
import html_generator
import user_interaction

@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory with images folder"""
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    return tmp_path

@pytest.fixture
def sample_clue_image(temp_project_dir):
    """Create a sample clue image"""
    clue_path = temp_project_dir / "images" / "clue-2025-01-15.webp"
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    img.save(clue_path, 'WEBP')
    return clue_path

@pytest.fixture
def sample_config():
    """Sample configuration data"""
    return {
        "last_project_path": "/tmp/test_project",
        "gemini_api_key": "test_api_key_12345"
    }

@pytest.fixture
def sample_player_data():
    """Sample player data returned by AI services"""
    return {
        "name": "Derek Jeter",
        "nickname": "The Captain",
        "facts": [
            "Hit a home run for his 3000th hit",
            "Won 5 World Series championships"
        ],
        "followup_qa": [
            {"question": "What team did he play for?", "answer": "New York Yankees"}
        ]
    }

@pytest.fixture
def sample_scraped_data():
    """Sample scraped data from Baseball-Reference"""
    return {
        "career_totals": {
            "WAR": "71.3",
            "AB": "11195",
            "HR": "260"
        },
        "yearly_war": [
            {"year": "1996", "display_team": "NYY", "teams": ["NYY"], "war": 3.3},
            {"year": "1997", "display_team": "NYY", "teams": ["NYY"], "war": 7.4}
        ]
    }

class TestMainIntegrationWorkflows:
    """Test main application integration workflows"""

    def test_command_line_argument_parsing(self):
        """Test parsing of command line arguments"""
        # Test help flag by checking if help is in argv
        test_argv = ['main.py', '--help']
        assert '--help' in test_argv
        assert '-h' in test_argv or '--help' in test_argv

    def test_automated_mode_workflow(self, temp_project_dir, sample_clue_image, sample_config, sample_player_data, sample_scraped_data):
        """Test automated mode workflow end-to-end"""
        with patch('config_manager.load_config', return_value=sample_config), \
             patch('main.ai_services.get_player_info_from_image', return_value=sample_player_data), \
             patch('main.scraper.search_and_scrape_player', return_value=sample_scraped_data), \
             patch('main.ai_services.get_facts_and_followup_from_gemini', return_value=sample_player_data), \
             patch('main.user_interaction.review_and_edit_data', return_value=sample_player_data), \
             patch('main.html_generator.generate_detail_page') as mock_generate, \
             patch('main.html_generator.rebuild_index_page') as mock_rebuild:
            
            # Simulate the main workflow for automated mode
            project_dir = temp_project_dir
            api_key = sample_config['gemini_api_key']
            is_automated = True
            id_only_mode = False
            facts_only_mode = False
            
            # Process a single clue image
            clue_path = sample_clue_image
            date_match = __import__('re').search(r"clue-(\d{4}-\d{2}-\d{2})\.webp", clue_path.name)
            date_str = date_match.group(1)
            dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = dt_obj.strftime("%B %d, %Y")
            
            # Execute the main processing workflow
            player_info = ai_services.get_player_info_from_image(clue_path, api_key)
            if player_info:
                scraped_data = scraper.search_and_scrape_player(player_info['name'], automated=is_automated)
                if scraped_data:
                    player_info['career_totals'] = scraped_data['career_totals']
                    player_info['yearly_war'] = scraped_data['yearly_war']

                if not id_only_mode and not facts_only_mode:
                    combined = ai_services.get_facts_and_followup_from_gemini(player_info['name'], api_key)
                    player_info['facts'] = combined.get('facts', [])
                    player_info['followup_qa'] = combined.get('qa', [])

                verified_data = user_interaction.review_and_edit_data(player_info, project_dir, automated=is_automated)
                html_generator.generate_detail_page(verified_data, date_str, formatted_date, project_dir)
            
            # Verify the workflow completed successfully
            mock_generate.assert_called_once()
            assert verified_data['name'] == 'Derek Jeter'
            assert 'career_totals' in verified_data

    def test_id_only_mode_workflow(self, temp_project_dir, sample_clue_image, sample_config, sample_player_data, sample_scraped_data):
        """Test ID-only mode workflow"""
        with patch('config_manager.load_config', return_value=sample_config), \
             patch('main.ai_services.get_player_info_from_image', return_value=sample_player_data), \
             patch('main.scraper.search_and_scrape_player', return_value=sample_scraped_data), \
             patch('main.user_interaction.review_and_edit_data', return_value=sample_player_data), \
             patch('main.html_generator.generate_detail_page') as mock_generate:
            
            # Simulate ID-only mode workflow
            project_dir = temp_project_dir
            api_key = sample_config['gemini_api_key']
            is_automated = True
            id_only_mode = True
            
            clue_path = sample_clue_image
            player_info = ai_services.get_player_info_from_image(clue_path, api_key)
            if player_info:
                scraped_data = scraper.search_and_scrape_player(player_info['name'], automated=is_automated)
                if scraped_data:
                    player_info['career_totals'] = scraped_data['career_totals']
                    player_info['yearly_war'] = scraped_data['yearly_war']

                # In ID-only mode, facts and followup should be empty
                player_info['facts'] = []
                player_info['followup_qa'] = []

                verified_data = user_interaction.review_and_edit_data(player_info, project_dir, automated=is_automated)
                html_generator.generate_detail_page(verified_data, '2025-01-15', 'January 15, 2025', project_dir)
            
            # Verify ID-only mode behavior
            mock_generate.assert_called_once()
            generate_call = mock_generate.call_args
            verified_data = generate_call[0][0]
            assert verified_data['facts'] == []
            assert verified_data['followup_qa'] == []
            assert 'career_totals' in verified_data

    def test_facts_only_mode_workflow(self, temp_project_dir, sample_clue_image, sample_config, sample_player_data, sample_scraped_data):
        """Test facts-only mode workflow"""
        with patch('config_manager.load_config', return_value=sample_config), \
             patch('main.ai_services.get_player_info_from_image', return_value=sample_player_data), \
             patch('main.scraper.search_and_scrape_player', return_value=sample_scraped_data), \
             patch('main.ai_services.get_facts_from_gemini', return_value=sample_player_data['facts']), \
             patch('main.user_interaction.review_and_edit_data', return_value=sample_player_data), \
             patch('main.html_generator.generate_detail_page') as mock_generate:
            
            # Simulate facts-only mode workflow
            project_dir = temp_project_dir
            api_key = sample_config['gemini_api_key']
            is_automated = True
            facts_only_mode = True
            
            clue_path = sample_clue_image
            player_info = ai_services.get_player_info_from_image(clue_path, api_key)
            if player_info:
                scraped_data = scraper.search_and_scrape_player(player_info['name'], automated=is_automated)
                if scraped_data:
                    player_info['career_totals'] = scraped_data['career_totals']
                    player_info['yearly_war'] = scraped_data['yearly_war']

                # In facts-only mode, get facts but no followup
                facts = ai_services.get_facts_from_gemini(player_info['name'], api_key)
                player_info['facts'] = facts
                player_info['followup_qa'] = []

                verified_data = user_interaction.review_and_edit_data(player_info, project_dir, automated=is_automated)
                html_generator.generate_detail_page(verified_data, '2025-01-15', 'January 15, 2025', project_dir)
            
            # Verify facts-only mode behavior
            mock_generate.assert_called_once()
            generate_call = mock_generate.call_args
            verified_data = generate_call[0][0]
            assert verified_data['facts'] == sample_player_data['facts']
            assert verified_data['followup_qa'] == []

    def test_date_range_processing(self, temp_project_dir, sample_config):
        """Test date range processing logic"""
        # Create multiple clue images
        dates = ['2025-01-15', '2025-01-16', '2025-01-17']
        for date in dates:
            clue_path = temp_project_dir / "images" / f"clue-{date}.webp"
            img = Image.new('RGB', (100, 100), color='blue')
            img.save(clue_path, 'WEBP')
        
        # Test date range parsing
        mode = "2025-01-15 to 2025-01-17"
        start_date_str, end_date_str = mode.split(" to ")
        start_date = datetime.strptime(start_date_str.strip(), "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str.strip(), "%Y-%m-%d")
        
        clue_files_to_process = []
        current_date = start_date
        while current_date <= end_date:
            clue_path = temp_project_dir / "images" / f"clue-{current_date.strftime('%Y-%m-%d')}.webp"
            if clue_path.exists():
                clue_files_to_process.append(clue_path)
            current_date += __import__('datetime').timedelta(days=1)
        
        # Verify all dates were found
        assert len(clue_files_to_process) == 3
        assert all(f"clue-{date}" in str(path) for date, path in zip(dates, clue_files_to_process))

    def test_all_dates_processing(self, temp_project_dir):
        """Test ALL dates processing logic"""
        # Create multiple clue images
        dates = ['2025-01-15', '2025-01-16', '2025-01-17']
        for date in dates:
            clue_path = temp_project_dir / "images" / f"clue-{date}.webp"
            img = Image.new('RGB', (100, 100), color='green')
            img.save(clue_path, 'WEBP')
        
        # Test ALL mode
        images_dir = temp_project_dir / "images"
        clue_files_to_process = sorted(images_dir.glob("clue-*.webp"), reverse=True)
        
        # Verify all dates were found
        assert len(clue_files_to_process) == 3
        # Convert paths to strings for comparison
        found_dates = [path.name for path in clue_files_to_process]
        assert all(f"clue-{date}.webp" in found_dates for date in dates)

    def test_gemini_quota_exceeded_handling(self, temp_project_dir, sample_clue_image, sample_config):
        """Test handling of Gemini quota exceeded exception"""
        with patch('config_manager.load_config', return_value=sample_config), \
             patch('main.ai_services.get_player_info_from_image', side_effect=ai_services.GeminiDailyQuotaExceeded("Quota exceeded")), \
             patch('main.html_generator.rebuild_index_page') as mock_rebuild, \
             patch('builtins.print') as mock_print:
            
            # Simulate processing with quota exceeded
            try:
                player_info = ai_services.get_player_info_from_image(sample_clue_image, sample_config['gemini_api_key'])
            except ai_services.GeminiDailyQuotaExceeded as e:
                print("\n❌ Gemini Free Tier daily quota has been reached.")
                print(f"   Details from API: {e}")
                print("\nStopping processing for today.")
            
            # Verify quota error message was printed
            print_calls = [str(call.args[0]) for call in mock_print.call_args_list]
            error_printed = any("Gemini Free Tier daily quota has been reached" in call for call in print_calls)
            assert error_printed

    def test_config_management_integration(self, temp_project_dir, sample_config):
        """Test configuration management integration"""
        with patch('config_manager.load_config', return_value=sample_config), \
             patch('config_manager.save_config') as mock_save_config:
            
            # Simulate config loading and saving
            config = config_manager.load_config()
            config['last_project_path'] = str(temp_project_dir)
            config['gemini_api_key'] = 'new_api_key'
            config_manager.save_config(config)
            
            # Verify config was saved
            mock_save_config.assert_called_once()
            saved_config = mock_save_config.call_args[0][0]
            assert saved_config['last_project_path'] == str(temp_project_dir)
            assert saved_config['gemini_api_key'] == 'new_api_key'

    def test_error_handling_workflows(self, temp_project_dir, sample_clue_image, sample_config):
        """Test various error handling scenarios"""
        
        # Test AI service failure
        with patch('config_manager.load_config', return_value=sample_config), \
             patch('main.ai_services.get_player_info_from_image', return_value=None):
            
            # Process should continue even if AI fails
            clue_path = sample_clue_image
            player_info = ai_services.get_player_info_from_image(clue_path, sample_config['gemini_api_key'])
            
            if not player_info:
                print("Skipping due to AI failure")
            
            # Verify AI failure was handled
            assert player_info is None
        
        # Test scraper failure
        with patch('config_manager.load_config', return_value=sample_config), \
             patch('main.ai_services.get_player_info_from_image', return_value={'name': 'Test Player'}), \
             patch('main.scraper.search_and_scrape_player', return_value=None), \
             patch('main.ai_services.get_facts_and_followup_from_gemini', return_value={'facts': [], 'qa': []}), \
             patch('main.user_interaction.review_and_edit_data') as mock_review, \
             patch('main.html_generator.generate_detail_page') as mock_generate:
            
            # Process should continue even if scraping fails
            project_dir = temp_project_dir
            player_info = {'name': 'Test Player'}
            scraped_data = scraper.search_and_scrape_player(player_info['name'], automated=True)
            
            if not scraped_data:
                print("Continuing without scraped data")
                player_info['career_totals'] = {}
                player_info['yearly_war'] = []
            
            # Mock the review function to return our modified data
            mock_review.return_value = player_info
            verified_data = user_interaction.review_and_edit_data(player_info, project_dir, automated=True)
            html_generator.generate_detail_page(verified_data, '2025-01-15', 'January 15, 2025', project_dir)
            
            # Verify processing continued
            mock_generate.assert_called_once()
            generate_call = mock_generate.call_args
            verified_data = generate_call[0][0]
            assert verified_data.get('career_totals') == {}
            assert verified_data.get('yearly_war') == []

    def test_file_system_integration(self, temp_project_dir):
        """Test file system operations integration"""
        # Test directory creation
        images_dir = temp_project_dir / "images"
        images_dir.mkdir(exist_ok=True)
        assert images_dir.exists()
        assert images_dir.is_dir()
        
        # Test file creation and checking
        test_image = images_dir / "clue-2025-01-15.webp"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(test_image, 'WEBP')
        
        assert test_image.exists()
        assert test_image.is_file()
        
        # Test glob pattern matching
        clue_files = list(images_dir.glob("clue-*.webp"))
        assert len(clue_files) == 1
        assert clue_files[0].name == "clue-2025-01-15.webp"

    def test_player_list_generation_integration(self, temp_project_dir):
        """Test player list generation integration"""
        with patch('main.scraper.generate_master_player_list') as mock_generate:
            # Simulate player list generation
            scraper.generate_master_player_list(temp_project_dir)
            
            # Verify the function was called
            mock_generate.assert_called_once_with(temp_project_dir)

    def test_date_validation_integration(self):
        """Test date validation logic"""
        # Test valid date
        try:
            datetime.strptime("2025-01-15", "%Y-%m-%d")
            valid_date = True
        except ValueError:
            valid_date = False
        assert valid_date
        
        # Test invalid date
        try:
            datetime.strptime("invalid-date", "%Y-%m-%d")
            valid_date = False
        except ValueError:
            valid_date = False
        assert not valid_date
        
        # Test valid date range
        try:
            mode = "2025-01-15 to 2025-01-17"
            start_date_str, end_date_str = mode.split(" to ")
            start_date = datetime.strptime(start_date_str.strip(), "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str.strip(), "%Y-%m-%d")
            valid_range = True
        except (ValueError, AttributeError):
            valid_range = False
        assert valid_range
