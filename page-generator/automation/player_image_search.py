"""
Player image search automation for puzzle workflow.

Automatically searches for, downloads, and processes player images.
"""

import os
import re
import urllib.parse
import requests
from pathlib import Path
from PIL import Image
from typing import List, Optional, Tuple
import time
import logging

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

from .image_processor import ImageProcessor

logger = logging.getLogger(__name__)

class PlayerImageSearch:
    """Handles automated player image search and download."""
    
    def __init__(self, images_dir: Path, temp_dir: Optional[Path] = None):
        """
        Initialize the player image search.
        
        Args:
            images_dir: Directory to save final player images
            temp_dir: Temporary directory for downloads
        """
        self.images_dir = images_dir
        self.temp_dir = temp_dir or Path.cwd() / "temp_player_images"
        self.temp_dir.mkdir(exist_ok=True)
        self.image_processor = ImageProcessor()
        
        # User agent for requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def search_player_images(self, player_name: str, max_results: int = 10) -> List[dict]:
        """
        Search for player images using multiple strategies.
        
        Args:
            player_name: Name of the player to search for
            max_results: Maximum number of results to return
            
        Returns:
            List of image search results with metadata
        """
        logger.info(f"Searching for images of: {player_name}")
        
        all_results = []
        
        # Strategy 1: Baseball card specific search
        card_results = self._search_baseball_cards(player_name, max_results // 2)
        all_results.extend(card_results)
        
        # Strategy 2: General player image search
        general_results = self._search_general_player_images(player_name, max_results // 2)
        all_results.extend(general_results)
        
        # Sort by relevance score (baseball cards get higher priority)
        all_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        logger.info(f"Found {len(all_results)} potential images for {player_name}")
        return all_results[:max_results]
    
    def _search_baseball_cards(self, player_name: str, max_results: int) -> List[dict]:
        """Search specifically for baseball card images."""
        search_terms = [
            f"{player_name} baseball card yankees",
            f"{player_name} topps card",
            f"{player_name} yankees baseball card"
        ]
        
        results = []
        for term in search_terms:
            term_results = self._search_images_with_selenium(term, max_results, card_search=True)
            results.extend(term_results)
        
        return results
    
    def _search_general_player_images(self, player_name: str, max_results: int) -> List[dict]:
        """Search for general player images."""
        search_terms = [
            f"{player_name} yankees photo",
            f"{player_name} baseball player",
            f"{player_name} mlb player"
        ]
        
        results = []
        for term in search_terms:
            term_results = self._search_images_with_selenium(term, max_results, card_search=False)
            results.extend(term_results)
        
        return results
    
    def _search_images_with_selenium(self, search_term: str, max_results: int, card_search: bool = False) -> List[dict]:
        """Use Selenium to search for images."""
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        
        try:
            # Use Google Images search
            encoded_query = urllib.parse.quote_plus(search_term)
            search_url = f"https://www.google.com/search?q={encoded_query}&tbm=isch"
            
            logger.info(f"Searching: {search_term}")
            driver.get(search_url)
            time.sleep(2)
            
            # Scroll to load more images
            for _ in range(2):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
            
            # Get image elements
            image_elements = driver.find_elements(By.CSS_SELECTOR, "img.Q4LuWd")
            
            results = []
            for i, img_elem in enumerate(image_elements[:max_results]):
                try:
                    src = img_elem.get_attribute('src')
                    if src and src.startswith('http'):
                        # Calculate relevance score
                        relevance_score = self._calculate_relevance_score(search_term, card_search)
                        
                        results.append({
                            'url': src,
                            'search_term': search_term,
                            'relevance_score': relevance_score,
                            'is_card': card_search,
                            'index': i
                        })
                except Exception as e:
                    logger.debug(f"Error processing image element {i}: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Error in Selenium image search: {e}")
            return []
        finally:
            driver.quit()
    
    def _calculate_relevance_score(self, search_term: str, is_card: bool) -> int:
        """Calculate relevance score for an image based on search term."""
        base_score = 50
        
        if is_card:
            base_score += 30  # Prefer baseball cards
        
        if "yankees" in search_term.lower():
            base_score += 20  # Prefer Yankees-related images
        
        if "topps" in search_term.lower():
            base_score += 10  # Prefer well-known card brands
        
        return base_score
    
    def select_best_image(self, search_results: List[dict]) -> Optional[dict]:
        """
        Select the best image from search results.
        
        Args:
            search_results: List of image search results
            
        Returns:
            Best image result or None if no suitable image found
        """
        if not search_results:
            return None
        
        # Sort by relevance score (already done, but ensure)
        search_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Try to download and validate top candidates
        for result in search_results[:5]:  # Try top 5
            if self._download_and_validate_image(result):
                return result
        
        return None
    
    def _download_and_validate_image(self, image_result: dict) -> bool:
        """
        Download and validate an image.
        
        Args:
            image_result: Image search result
            
        Returns:
            True if image downloaded and validated successfully
        """
        try:
            # Download image
            response = requests.get(image_result['url'], headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Save to temp file
            temp_file = self.temp_dir / f"temp_{hash(image_result['url'])}.jpg"
            with open(temp_file, 'wb') as f:
                f.write(response.content)
            
            # Validate image
            if self.image_processor.validate_image_quality(temp_file):
                # Store the temp file path for later use
                image_result['temp_file'] = temp_file
                logger.info(f"Downloaded and validated: {image_result['url']}")
                return True
            else:
                # Remove invalid image
                temp_file.unlink(missing_ok=True)
                logger.debug(f"Image failed validation: {image_result['url']}")
                return False
                
        except Exception as e:
            logger.debug(f"Error downloading image {image_result['url']}: {e}")
            return False
    
    def download_and_process_player_image(self, player_name: str, date_str: str) -> Optional[Path]:
        """
        Complete workflow to download and process a player image.
        
        Args:
            player_name: Name of the player
            date_str: Date string for naming (YYYY-MM-DD)
            
        Returns:
            Path to processed player image or None if failed
        """
        logger.info(f"Starting player image search for: {player_name}")
        
        # Search for images
        search_results = self.search_player_images(player_name)
        
        if not search_results:
            logger.warning(f"No images found for {player_name}")
            return None
        
        # Select best image
        best_result = self.select_best_image(search_results)
        
        if not best_result:
            logger.warning(f"No suitable image found for {player_name}")
            return None
        
        # Process the selected image
        temp_file = best_result.get('temp_file')
        if not temp_file or not temp_file.exists():
            logger.error(f"Temp file not found for {player_name}")
            return None
        
        # Process and save final image
        final_path = self.image_processor.process_player_image(temp_file, self.images_dir, date_str)
        
        # Clean up temp file
        temp_file.unlink(missing_ok=True)
        
        if final_path:
            logger.info(f"Successfully processed player image for {player_name}: {final_path.name}")
            return final_path
        else:
            logger.error(f"Failed to process player image for {player_name}")
            return None
    
    def fallback_image_search(self, player_name: str, date_str: str) -> Optional[Path]:
        """
        Fallback search using alternative methods if primary search fails.
        
        Args:
            player_name: Name of the player
            date_str: Date string for naming
            
        Returns:
            Path to processed player image or None if failed
        """
        logger.info(f"Attempting fallback image search for: {player_name}")
        
        # Try with simplified search terms
        simplified_name = re.sub(r'\s+(Jr\.|Sr\.|II|III|IV)$', '', player_name.strip())
        
        # Try just last name + yankees
        last_name = simplified_name.split()[-1] if simplified_name else player_name
        fallback_terms = [
            f"{last_name} yankees",
            simplified_name,
            player_name
        ]
        
        for term in fallback_terms:
            search_results = self._search_general_player_images(term, max_results=5)
            
            if search_results:
                best_result = self.select_best_image(search_results)
                if best_result:
                    temp_file = best_result.get('temp_file')
                    if temp_file and temp_file.exists():
                        final_path = self.image_processor.process_player_image(temp_file, self.images_dir, date_str)
                        temp_file.unlink(missing_ok=True)
                        
                        if final_path:
                            logger.info(f"Fallback search successful for {player_name}: {final_path.name}")
                            return final_path
        
        logger.warning(f"All fallback searches failed for {player_name}")
        return None
    
    def cleanup_temp_files(self):
        """Clean up temporary image files."""
        try:
            for temp_file in self.temp_dir.glob("temp_*.jpg"):
                temp_file.unlink(missing_ok=True)
            logger.info("Cleaned up temporary image files")
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")
