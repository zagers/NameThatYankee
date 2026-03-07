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
    def image_processor(self):
        """Create an ImageProcessor instance."""
        return ImageProcessor()

    @pytest.fixture
    def player_search(self, images_dir, temp_dir):
        """Create a PlayerImageSearch instance."""
        return PlayerImageSearch(images_dir, temp_dir)

    @pytest.fixture
    def sample_image_data(self):
        """Create sample image data for testing."""
        img = Image.new('RGB', (200, 200), color='blue')
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 50, 150, 150], fill='red')
        return img

    @pytest.fixture
    def sample_data_uri(self, sample_image_data):
        """Create a sample data URI for testing."""
        import io
        img_buffer = io.BytesIO()
        sample_image_data.save(img_buffer, format='JPEG')
        img_bytes = img_buffer.getvalue()
        encoded = base64.b64encode(img_bytes).decode('utf-8')
        return f"data:image/jpeg;base64,{encoded}"

    def test_init(self, images_dir, temp_dir):
        """Test PlayerImageSearch initialization."""
        search = PlayerImageSearch(images_dir, temp_dir)
        
        assert search.images_dir == images_dir
        assert search.temp_dir == temp_dir
        assert isinstance(search.image_processor, ImageProcessor)
        assert 'User-Agent' in search.headers

    def test_init_with_default_temp_dir(self, images_dir):
        """Test PlayerImageSearch initialization with default temp dir."""
        search = PlayerImageSearch(images_dir)
        
        assert search.images_dir == images_dir
        assert search.temp_dir is not None
        assert search.temp_dir.exists()

    def test_search_player_images_basic(self, player_search):
        """Test basic player image search."""
        with patch('automation.player_image_search.webdriver') as mock_webdriver:
            # Mock the WebDriver
            mock_driver = Mock()
            mock_webdriver.Chrome.return_value = mock_driver
            
            # Mock image elements
            mock_img1 = Mock()
            mock_img1.get_attribute.return_value = "https://example.com/image1.jpg"
            mock_img2 = Mock()
            mock_img2.get_attribute.return_value = "data:image/jpeg;base64,test"
            
            mock_driver.find_elements.return_value = [mock_img1, mock_img2]
            
            results = player_search.search_player_images("Test Player", max_results=2)
            
            # Should get results from 4 search terms, but only 1 result per search = 4 total
            assert len(results) == 4
            assert all(result['url'] in ["https://example.com/image1.jpg", "data:image/jpeg;base64,test"] for result in results)

    def test_search_player_images_with_showzone_links(self, player_search):
        """Test player image search with showzone.gg links."""
        with patch('automation.player_image_search.webdriver') as mock_webdriver:
            # Mock the WebDriver
            mock_driver = Mock()
            mock_webdriver.Chrome.return_value = mock_driver
            
            # Mock showzone.gg links
            mock_link1 = Mock()
            mock_link1.get_attribute.return_value = "https://showzone.gg/players/test-player"
            mock_link2 = Mock()
            mock_link2.get_attribute.return_value = "https://example.com/image.jpg"
            
            mock_driver.find_elements.return_value = [mock_link1, mock_link2]
            
            results = player_search.search_player_images("Test Player", max_results=2)
            
            # Should get results from 4 search terms, but only 1 result per search = 4 total
            assert len(results) == 4
            assert all(result['url'] in ["https://showzone.gg/players/test-player", "https://example.com/image.jpg"] for result in results)

    def test_search_player_images_with_imgurl_redirects(self, player_search):
        """Test player image search with Google imgurl redirects."""
        with patch('automation.player_image_search.webdriver') as mock_webdriver:
            # Mock the WebDriver
            mock_driver = Mock()
            mock_webdriver.Chrome.return_value = mock_driver
            
            # Mock imgurl redirect links
            mock_link = Mock()
            mock_link.get_attribute.return_value = "https://www.google.com/imgurl?https://example.com/high-res.jpg&other=params"
            
            mock_driver.find_elements.return_value = [mock_link]
            
            results = player_search.search_player_images("Test Player", max_results=1)
            
            # Should get results from 4 search terms, but only 1 result per search = 4 total
            assert len(results) == 4
            assert all(result['url'] == "https://example.com/high-res.jpg" for result in results)

    def test_search_player_images_filters_google_logos(self, player_search):
        """Test that Google logos are filtered out."""
        with patch('automation.player_image_search.webdriver') as mock_webdriver:
            # Mock the WebDriver
            mock_driver = Mock()
            mock_webdriver.Chrome.return_value = mock_driver
            
            # Mock images including Google logos
            mock_img1 = Mock()
            mock_img1.get_attribute.return_value = "https://example.com/player.jpg"
            mock_img2 = Mock()
            mock_img2.get_attribute.return_value = "https://www.google.com/logos/doodle.png"
            mock_img3 = Mock()
            mock_img3.get_attribute.return_value = "data:image/jpeg;base64,small"
            mock_img4 = Mock()
            mock_img4.get_attribute.return_value = "data:image/jpeg;base64," + "x" * 2000  # Large data URI
            
            mock_driver.find_elements.return_value = [mock_img1, mock_img2, mock_img3, mock_img4]
            
            results = player_search.search_player_images("Test Player", max_results=10)
            
            # Should get results from 4 search terms, each filtered to 1 valid image = 4 total
            assert len(results) == 4
            assert all(result['url'] in ["https://example.com/player.jpg", "data:image/jpeg;base64," + "x" * 2000] for result in results)

    def test_download_and_validate_image_http_success(self, player_search, sample_image_data, temp_dir):
        """Test downloading and validating an HTTP image."""
        with patch('automation.player_image_search.requests') as mock_requests:
            # Mock successful HTTP response
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            
            # Convert image to bytes
            import io
            img_buffer = io.BytesIO()
            sample_image_data.save(img_buffer, format='JPEG')
            mock_response.content = img_buffer.getvalue()
            
            mock_requests.get.return_value = mock_response
            
            image_result = {'url': 'https://example.com/image.jpg'}
            
            result = player_search._download_and_validate_image(image_result)
            
            assert result is True
            assert 'temp_file' in image_result
            assert image_result['temp_file'].exists()

    def test_download_and_validate_image_data_uri_success(self, player_search, sample_data_uri):
        """Test downloading and validating a data URI image."""
        image_result = {'url': sample_data_uri}
        
        result = player_search._download_and_validate_image(image_result)
        
        assert result is True
        assert 'temp_file' in image_result
        assert image_result['temp_file'].exists()

    def test_download_and_validate_image_http_failure(self, player_search):
        """Test downloading HTTP image with request failure."""
        with patch('automation.player_image_search.requests') as mock_requests:
            # Mock failed HTTP response
            mock_requests.get.side_effect = Exception("Network error")
            
            image_result = {'url': 'https://example.com/image.jpg'}
            
            result = player_search._download_and_validate_image(image_result)
            
            assert result is False
            assert 'temp_file' not in image_result

    def test_download_and_validate_image_invalid_data_uri(self, player_search):
        """Test downloading invalid data URI."""
        image_result = {'url': 'data:image/jpeg;base64,invalid'}
        
        result = player_search._download_and_validate_image(image_result)
        
        assert result is False

    def test_download_and_validate_image_too_small(self, player_search, temp_dir):
        """Test downloading image that's too small."""
        # Create a small image
        small_img = Image.new('RGB', (50, 50), color='red')
        import io
        img_buffer = io.BytesIO()
        small_img.save(img_buffer, format='JPEG')
        
        with patch('automation.player_image_search.requests') as mock_requests:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.content = img_buffer.getvalue()
            mock_requests.get.return_value = mock_response
            
            image_result = {'url': 'https://example.com/small.jpg'}
            
            result = player_search._download_and_validate_image(image_result)
            
            assert result is False

    def test_extract_image_from_showzone_success(self, player_search):
        """Test extracting image from showzone.gg page."""
        mock_html = """
        <html>
            <body>
                <img class="player-card" src="https://showzone.gg/cards/player-card.jpg" />
                <img src="https://showzone.gg/logo.png" />
            </body>
        </html>
        """
        
        with patch('automation.player_image_search.requests') as mock_requests:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.content = mock_html.encode('utf-8')
            mock_requests.get.return_value = mock_response
            
            result = player_search._extract_image_from_showzone("https://showzone.gg/players/test")
            
            assert result == "https://showzone.gg/cards/player-card.jpg"

    def test_extract_image_from_showzone_relative_url(self, player_search):
        """Test extracting image with relative URL from showzone.gg page."""
        mock_html = """
        <html>
            <body>
                <img src="/cards/player-card.png" />
            </body>
        </html>
        """
        
        with patch('automation.player_image_search.requests') as mock_requests:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.content = mock_html.encode('utf-8')
            mock_requests.get.return_value = mock_response
            
            result = player_search._extract_image_from_showzone("https://showzone.gg/players/test")
            
            assert result == "https://showzone.gg/cards/player-card.png"

    def test_extract_image_from_showzone_failure(self, player_search):
        """Test extracting image from showzone.gg page with no images."""
        mock_html = "<html><body><p>No images here</p></body></html>"
        
        with patch('automation.player_image_search.requests') as mock_requests:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.content = mock_html.encode('utf-8')
            mock_requests.get.return_value = mock_response
            
            result = player_search._extract_image_from_showzone("https://showzone.gg/players/test")
            
            assert result is None

    def test_extract_image_from_showzone_request_failure(self, player_search):
        """Test extracting image from showzone.gg with request failure."""
        with patch('automation.player_image_search.requests') as mock_requests:
            mock_requests.get.side_effect = Exception("Network error")
            
            result = player_search._extract_image_from_showzone("https://showzone.gg/players/test")
            
            assert result is None

    def test_calculate_relevance_score(self, player_search):
        """Test relevance score calculation."""
        # Test baseball card search
        score = player_search._calculate_relevance_score("player yankees baseball card", is_card=True)
        assert score == 100  # 50 + 30 (card) + 20 (yankees)
        
        # Test regular yankees search
        score = player_search._calculate_relevance_score("player yankees", is_card=False)
        assert score == 70  # 50 + 20 (yankees)
        
        # Test topps card search
        score = player_search._calculate_relevance_score("player topps card", is_card=True)
        assert score == 90  # 50 + 30 (card) + 10 (topps)
        
        # Test basic search
        score = player_search._calculate_relevance_score("player", is_card=False)
        assert score == 50  # Base score only

    def test_download_and_process_player_image_success(self, player_search, sample_image_data, images_dir):
        """Test complete workflow for downloading and processing player image."""
        with patch('automation.player_image_search.requests') as mock_requests:
            # Mock successful HTTP response
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            
            import io
            img_buffer = io.BytesIO()
            sample_image_data.save(img_buffer, format='JPEG')
            mock_response.content = img_buffer.getvalue()
            
            mock_requests.get.return_value = mock_response
            
            # Mock the search results
            with patch.object(player_search, 'search_player_images') as mock_search:
                mock_search.return_value = [{'url': 'https://example.com/player.jpg'}]
                
                result = player_search.download_and_process_player_image("Test Player", "2025-03-06")
                
                assert result is not None
                assert result.name == "answer-2025-03-06.webp"
                assert result.exists()

    def test_download_and_process_player_image_no_results(self, player_search):
        """Test workflow when no images are found."""
        with patch.object(player_search, 'search_player_images') as mock_search:
            mock_search.return_value = []
            
            result = player_search.download_and_process_player_image("Test Player", "2025-03-06")
            
            assert result is None

    def test_download_and_process_player_image_download_failure(self, player_search):
        """Test workflow when image download fails."""
        with patch.object(player_search, 'search_player_images') as mock_search:
            mock_search.return_value = [{'url': 'https://example.com/player.jpg'}]
            
            with patch.object(player_search, '_download_and_validate_image') as mock_download:
                mock_download.return_value = False
                
                result = player_search.download_and_process_player_image("Test Player", "2025-03-06")
                
                assert result is None

    def test_fallback_image_search(self, player_search):
        """Test fallback image search."""
        with patch.object(player_search, '_search_general_player_images') as mock_search, \
             patch.object(player_search, 'select_best_image') as mock_select, \
             patch.object(player_search.image_processor, 'process_player_image') as mock_process:
            
            mock_search.return_value = [{'url': 'https://example.com/fallback.jpg'}]
            mock_select.return_value = {'temp_file': Path('/tmp/temp.jpg')}
            mock_process.return_value = Path("/tmp/fallback.webp")
            
            result = player_search.fallback_image_search("Test Player", "2025-03-06")
            
            assert result is not None
            mock_search.assert_called()

    def test_cleanup_temp_files(self, player_search, temp_dir):
        """Test cleanup of temporary files."""
        # Create some temporary files
        temp_file1 = temp_dir / "temp_123.jpg"
        temp_file2 = temp_dir / "temp_456.jpg"
        temp_file1.write_text("test")
        temp_file2.write_text("test")
        
        # Verify files exist
        assert temp_file1.exists()
        assert temp_file2.exists()
        
        # Cleanup
        player_search.cleanup_temp_files()
        
        # Verify files are deleted
        assert not temp_file1.exists()
        assert not temp_file2.exists()
