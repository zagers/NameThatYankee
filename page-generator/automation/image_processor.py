"""
Image processing automation for puzzle workflow.

Handles conversion, optimization, and validation of puzzle and player images.
"""

import os
from pathlib import Path
from PIL import Image, ImageOps
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class ImageProcessor:
    """Handles automated image processing for puzzle workflow."""
    
    def __init__(self, quality: int = 85, max_width: int = 800, max_height: int = 600):
        """
        Initialize the image processor.
        
        Args:
            quality: WEBP quality (1-100)
            max_width: Maximum image width for optimization
            max_height: Maximum image height for optimization
        """
        self.quality = quality
        self.max_width = max_width
        self.max_height = max_height
    
    def convert_to_webp(self, input_path: Path, output_path: Path) -> bool:
        """
        Convert an image to WEBP format with optimization.
        
        Args:
            input_path: Path to source image
            output_path: Path for output WEBP file
            
        Returns:
            True if conversion successful, False otherwise
        """
        try:
            with Image.open(input_path) as img:
                # Convert to RGB if necessary (for PNG with transparency)
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Auto-orient based on EXIF
                img = ImageOps.exif_transpose(img)
                
                # Resize if necessary
                img = self._resize_if_needed(img)
                
                # Save as WEBP
                output_path.parent.mkdir(parents=True, exist_ok=True)
                img.save(output_path, 'WEBP', quality=self.quality, method=6)
                
                logger.info(f"Converted {input_path.name} to WEBP: {output_path.name}")
                return True
                
        except Exception as e:
            logger.error(f"Error converting {input_path} to WEBP: {e}")
            return False
    
    def _resize_if_needed(self, img: Image.Image) -> Image.Image:
        """
        Resize image if it exceeds maximum dimensions while maintaining aspect ratio.
        
        Args:
            img: PIL Image object
            
        Returns:
            Resized image or original if no resize needed
        """
        if img.width <= self.max_width and img.height <= self.max_height:
            return img
        
        # Calculate target dimensions maintaining aspect ratio
        ratio = min(self.max_width / img.width, self.max_height / img.height)
        new_width = int(img.width * ratio)
        new_height = int(img.height * ratio)
        
        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def process_puzzle_screenshot(self, screenshot_path: Path, images_dir: Path, date_str: str) -> Optional[Path]:
        """
        Process a puzzle screenshot and save as clue image.
        
        Args:
            screenshot_path: Path to puzzle screenshot
            images_dir: Directory to save processed images
            date_str: Date string for naming (YYYY-MM-DD)
            
        Returns:
            Path to processed clue image or None if failed
        """
        if not screenshot_path.exists():
            logger.error(f"Screenshot not found: {screenshot_path}")
            return None
        
        clue_path = images_dir / f"clue-{date_str}.webp"
        
        if self.convert_to_webp(screenshot_path, clue_path):
            logger.info(f"Processed puzzle clue: {clue_path.name}")
            return clue_path
        
        return None
    
    def process_player_image(self, player_image_path: Path, images_dir: Path, date_str: str) -> Optional[Path]:
        """
        Process a player image and save as answer image.
        
        Args:
            player_image_path: Path to player image
            images_dir: Directory to save processed images
            date_str: Date string for naming (YYYY-MM-DD)
            
        Returns:
            Path to processed answer image or None if failed
        """
        if not player_image_path.exists():
            logger.error(f"Player image not found: {player_image_path}")
            return None
        
        answer_path = images_dir / f"answer-{date_str}.webp"
        
        if self.convert_to_webp(player_image_path, answer_path):
            logger.info(f"Processed player answer image: {answer_path.name}")
            return answer_path
        
        return None
    
    def batch_process_images(self, input_dir: Path, output_dir: Path, pattern: str = "*.png") -> List[Path]:
        """
        Batch process images from input directory to output directory.
        
        Args:
            input_dir: Directory containing source images
            output_dir: Directory for processed images
            pattern: File pattern to match (default: *.png)
            
        Returns:
            List of successfully processed image paths
        """
        processed_files = []
        
        for input_file in input_dir.glob(pattern):
            output_file = output_dir / f"{input_file.stem}.webp"
            
            if self.convert_to_webp(input_file, output_file):
                processed_files.append(output_file)
        
        logger.info(f"Batch processed {len(processed_files)} images")
        return processed_files
    
    def validate_image_quality(self, image_path: Path, min_width: int = 200, min_height: int = 200) -> bool:
        """
        Validate that an image meets minimum quality standards.
        
        Args:
            image_path: Path to image file
            min_width: Minimum width requirement
            min_height: Minimum height requirement
            
        Returns:
            True if image meets quality standards, False otherwise
        """
        try:
            with Image.open(image_path) as img:
                return img.width >= min_width and img.height >= min_height
        except Exception as e:
            logger.error(f"Error validating image quality for {image_path}: {e}")
            return False
    
    def get_image_info(self, image_path: Path) -> Optional[dict]:
        """
        Get information about an image file.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with image info or None if failed
        """
        try:
            with Image.open(image_path) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'mode': img.mode,
                    'format': img.format,
                    'size_bytes': image_path.stat().st_size
                }
        except Exception as e:
            logger.error(f"Error getting image info for {image_path}: {e}")
            return None

    def crop_to_bounding_box(self, image_path: Path, crop_box: List[int]) -> bool:
        """
        Crop an image to a specific bounding box using normalized coordinates.
        
        Args:
            image_path: Path to the image to crop (modifies in place)
            crop_box: List of [ymin, xmin, ymax, xmax] in 0-1000 scale
            
        Returns:
            True if crop was successful
        """
        if not crop_box or len(crop_box) != 4:
            return False
            
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                
                # Convert normalized coordinates to pixel coordinates
                # crop_box is [ymin, xmin, ymax, xmax]
                top = int((crop_box[0] / 1000) * height)
                left = int((crop_box[1] / 1000) * width)
                bottom = int((crop_box[2] / 1000) * height)
                right = int((crop_box[3] / 1000) * width)
                
                # Ensure coordinates are within image bounds and valid
                left = max(0, left)
                top = max(0, top)
                right = min(width, right)
                bottom = min(height, bottom)
                
                if right <= left or bottom <= top:
                    logger.warning(f"Invalid crop box for {image_path}: {crop_box}")
                    return False
                
                # Perform crop
                cropped_img = img.crop((left, top, right, bottom))
                
                # Save back to same path (maintain original format for now)
                cropped_img.save(image_path)
                logger.info(f"✂️ Successfully cropped image {image_path.name}")
                return True
                
        except Exception as e:
            logger.error(f"Error cropping {image_path}: {e}")
            return False
