#!/usr/bin/env python3
"""
Tests for the ImageProcessor class in the automation module.
"""

import pytest
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw
import sys

# Add the page-generator directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "page-generator"))

from automation.image_processor import ImageProcessor


class TestImageProcessor:
    """Test cases for ImageProcessor functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def sample_png(self, temp_dir):
        """Create a sample PNG image for testing."""
        img_path = temp_dir / "test.png"
        img = Image.new('RGB', (400, 300), color='blue')
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 50, 350, 250], fill='red')
        img.save(img_path, 'PNG')
        return img_path

    @pytest.fixture
    def sample_jpg(self, temp_dir):
        """Create a sample JPG image for testing."""
        img_path = temp_dir / "test.jpg"
        img = Image.new('RGB', (500, 400), color='green')
        draw = ImageDraw.Draw(img)
        draw.ellipse([100, 100, 400, 300], fill='yellow')
        img.save(img_path, 'JPEG')
        return img_path

    @pytest.fixture
    def small_image(self, temp_dir):
        """Create a small image for testing validation."""
        img_path = temp_dir / "small.png"
        img = Image.new('RGB', (50, 50), color='purple')
        img.save(img_path, 'PNG')
        return img_path

    @pytest.fixture
    def image_processor(self):
        """Create an ImageProcessor instance."""
        return ImageProcessor()

    def test_init(self):
        """Test ImageProcessor initialization."""
        processor = ImageProcessor(quality=90, max_width=1000, max_height=800)
        
        assert processor.quality == 90
        assert processor.max_width == 1000
        assert processor.max_height == 800

    def test_init_defaults(self):
        """Test ImageProcessor initialization with defaults."""
        processor = ImageProcessor()
        
        assert processor.quality == 85
        assert processor.max_width == 800
        assert processor.max_height == 600

    def test_convert_to_webp_png_to_webp(self, image_processor, sample_png, temp_dir):
        """Test converting PNG to WEBP."""
        output_path = temp_dir / "output.webp"
        
        result = image_processor.convert_to_webp(sample_png, output_path)
        
        assert result is True
        assert output_path.exists()
        
        # Verify the converted image
        with Image.open(output_path) as img:
            assert img.format == 'WEBP'
            assert img.size == (400, 300)

    def test_convert_to_webp_jpg_to_webp(self, image_processor, sample_jpg, temp_dir):
        """Test converting JPG to WEBP."""
        output_path = temp_dir / "output.webp"
        
        result = image_processor.convert_to_webp(sample_jpg, output_path)
        
        assert result is True
        assert output_path.exists()
        
        # Verify the converted image
        with Image.open(output_path) as img:
            assert img.format == 'WEBP'
            assert img.size == (500, 400)

    def test_convert_to_webp_nonexistent_file(self, image_processor, temp_dir):
        """Test converting a non-existent file."""
        input_path = temp_dir / "nonexistent.png"
        output_path = temp_dir / "output.webp"
        
        result = image_processor.convert_to_webp(input_path, output_path)
        
        assert result is False
        assert not output_path.exists()

    def test_convert_to_webp_corrupted_file(self, image_processor, temp_dir):
        """Test converting a corrupted file."""
        input_path = temp_dir / "corrupted.png"
        input_path.write_text("This is not an image file")
        output_path = temp_dir / "output.webp"
        
        result = image_processor.convert_to_webp(input_path, output_path)
        
        assert result is False

    def test_validate_image_quality_good_size(self, image_processor, sample_png):
        """Test image validation with good size."""
        result = image_processor.validate_image_quality(sample_png)
        assert result is True

    def test_validate_image_quality_custom_size(self, image_processor, sample_png):
        """Test image validation with custom size requirements."""
        result = image_processor.validate_image_quality(sample_png, min_width=300, min_height=200)
        assert result is True

    def test_validate_image_quality_too_small(self, image_processor, small_image):
        """Test image validation with image too small."""
        result = image_processor.validate_image_quality(small_image, min_width=100, min_height=100)
        assert result is False

    def test_validate_image_quality_nonexistent_file(self, image_processor, temp_dir):
        """Test image validation with non-existent file."""
        img_path = temp_dir / "nonexistent.png"
        
        result = image_processor.validate_image_quality(img_path)
        
        assert result is False

    def test_validate_image_quality_corrupted_file(self, image_processor, temp_dir):
        """Test image validation with corrupted file."""
        img_path = temp_dir / "corrupted.png"
        # Create a file that's not a valid image
        img_path.write_text("This is not an image file")
        
        result = image_processor.validate_image_quality(img_path)
        
        assert result is False

    def test_get_image_info(self, image_processor, sample_png):
        """Test getting image information."""
        info = image_processor.get_image_info(sample_png)
        
        assert info is not None
        assert info['format'] == 'PNG'
        assert info['width'] == 400
        assert info['height'] == 300
        assert info['mode'] == 'RGB'
        assert 'size_bytes' in info

    def test_get_image_info_nonexistent_file(self, image_processor, temp_dir):
        """Test getting image info for non-existent file."""
        img_path = temp_dir / "nonexistent.png"
        
        info = image_processor.get_image_info(img_path)
        
        assert info is None

    def test_get_image_info_corrupted_file(self, image_processor, temp_dir):
        """Test getting image info for corrupted file."""
        img_path = temp_dir / "corrupted.png"
        img_path.write_text("This is not an image file")
        
        info = image_processor.get_image_info(img_path)
        
        assert info is None

    def test_process_puzzle_screenshot(self, image_processor, sample_png, temp_dir):
        """Test processing a puzzle screenshot."""
        images_dir = temp_dir / "images"
        images_dir.mkdir()
        
        result = image_processor.process_puzzle_screenshot(sample_png, images_dir, "2025-03-06")
        
        assert result is not None
        assert result.exists()
        assert result.name == "clue-2025-03-06.webp"
        
        # Verify it's a WEBP file
        with Image.open(result) as img:
            assert img.format == 'WEBP'

    def test_process_puzzle_screenshot_nonexistent_file(self, image_processor, temp_dir):
        """Test processing a non-existent screenshot."""
        images_dir = temp_dir / "images"
        images_dir.mkdir()
        missing_file = temp_dir / "missing.png"
        
        result = image_processor.process_puzzle_screenshot(missing_file, images_dir, "2025-03-06")
        
        assert result is None

    def test_process_player_image(self, image_processor, sample_jpg, temp_dir):
        """Test processing a player image."""
        images_dir = temp_dir / "images"
        images_dir.mkdir()
        
        result = image_processor.process_player_image(sample_jpg, images_dir, "2025-03-06")
        
        assert result is not None
        assert result.exists()
        assert result.name == "answer-2025-03-06.webp"
        
        # Verify it's a WEBP file
        with Image.open(result) as img:
            assert img.format == 'WEBP'

    def test_process_player_image_nonexistent_file(self, image_processor, temp_dir):
        """Test processing a non-existent player image."""
        images_dir = temp_dir / "images"
        images_dir.mkdir()
        missing_file = temp_dir / "missing.jpg"
        
        result = image_processor.process_player_image(missing_file, images_dir, "2025-03-06")
        
        assert result is None

    def test_batch_process_images(self, image_processor, sample_png, sample_jpg, temp_dir):
        """Test batch processing images."""
        input_dir = temp_dir / "input"
        output_dir = temp_dir / "output"
        input_dir.mkdir()
        
        # Copy test images to input directory
        import shutil
        shutil.copy(sample_png, input_dir / "test1.png")
        shutil.copy(sample_jpg, input_dir / "test2.jpg")
        
        # Test with PNG pattern (should only process PNG files)
        results = image_processor.batch_process_images(input_dir, output_dir, pattern="*.png")
        
        assert len(results) == 1
        assert (output_dir / "test1.webp").exists()

    def test_batch_process_images_all_patterns(self, image_processor, sample_png, sample_jpg, temp_dir):
        """Test batch processing with different patterns."""
        input_dir = temp_dir / "input"
        output_dir = temp_dir / "output"
        input_dir.mkdir()
        
        # Copy test images to input directory
        import shutil
        shutil.copy(sample_png, input_dir / "test1.png")
        shutil.copy(sample_jpg, input_dir / "test2.jpg")
        
        # Process PNG files first
        png_results = image_processor.batch_process_images(input_dir, output_dir, pattern="*.png")
        assert len(png_results) == 1
        
        # Process JPG files
        jpg_results = image_processor.batch_process_images(input_dir, output_dir, pattern="*.jpg")
        assert len(jpg_results) == 1
        
        # Verify both files exist
        assert (output_dir / "test1.webp").exists()
        assert (output_dir / "test2.webp").exists()

    def test_batch_process_images_empty_directory(self, image_processor, temp_dir):
        """Test batch processing with empty directory."""
        input_dir = temp_dir / "input"
        output_dir = temp_dir / "output"
        input_dir.mkdir()
        
        results = image_processor.batch_process_images(input_dir, output_dir)
        
        assert len(results) == 0

    def test_batch_process_images_nonexistent_directory(self, image_processor, temp_dir):
        """Test batch processing with non-existent directory."""
        input_dir = temp_dir / "nonexistent"
        output_dir = temp_dir / "output"
        
        results = image_processor.batch_process_images(input_dir, output_dir)
        
        assert len(results) == 0

    def test_resize_if_needed_no_resize(self, image_processor, sample_png):
        """Test _resize_if_needed when no resize is needed."""
        with Image.open(sample_png) as img:
            original_size = img.size
            
            resized_img = image_processor._resize_if_needed(img)
            
            assert resized_img.size == original_size

    def test_resize_if_needed_resize_required(self, image_processor):
        """Test _resize_if_needed when resize is required."""
        # Create a large image
        img = Image.new('RGB', (1200, 900), color='blue')
        
        resized_img = image_processor._resize_if_needed(img)
        
        # Should be resized to within max dimensions
        assert resized_img.size[0] <= image_processor.max_width
        assert resized_img.size[1] <= image_processor.max_height

    def test_resize_if_needed_maintains_aspect_ratio(self, image_processor):
        """Test that _resize_if_needed maintains aspect ratio."""
        # Create a wide image
        img = Image.new('RGB', (1600, 600), color='blue')
        original_aspect = 1600 / 600
        
        resized_img = image_processor._resize_if_needed(img)
        new_aspect = resized_img.size[0] / resized_img.size[1]
        
        # Aspect ratio should be preserved (within small floating point error)
        assert abs(original_aspect - new_aspect) < 0.01
