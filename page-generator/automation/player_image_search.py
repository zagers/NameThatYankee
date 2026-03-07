"""
Player image search automation for puzzle workflow.

Automatically searches for, downloads, and processes player images with a prioritized 
verification system using Gemini AI.
"""

import os
import re
import urllib.parse
import requests
from pathlib import Path
from PIL import Image
from typing import List, Optional, Dict, Any
import time
import logging

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from .image_processor import ImageProcessor

logger = logging.getLogger(__name__)

class PlayerImageSearch:
    """Handles automated player image search and download with prioritized verification."""
    
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
    
    def find_first_yankee_image(self, player_name: str, api_key: str = None) -> Optional[dict]:
        """
        Find the best image of the player based on prioritized criteria.
        
        Search Term: "<player name> yankees baseball card"
        Priorities:
        1. Baseball card + Yankee uniform
        2. Any image + Yankee uniform
        3. Any image of the player
        """
        search_term = f"{player_name} yankees baseball card"
        logger.info(f"🚀 Searching Google Images for: {search_term}")
        
        candidates = self._get_image_candidates_from_google(search_term)
        if not candidates:
            logger.warning("No image candidates found in Google Search.")
            return None

        best_fallback = None
        max_candidates_to_check = 10
        
        for i, candidate in enumerate(candidates[:max_candidates_to_check]):
            logger.info(f"🧐 Checking candidate {i+1}/{max_candidates_to_check}: {candidate['source_page'][:60]}...")
            
            # Step 2 & 3: Download full scale and check suitability
            temp_file = self._download_full_size_image(candidate)
            if not temp_file:
                continue
                
            # Check suitability (size & format)
            img_info = self.image_processor.get_image_info(temp_file)
            if img_info:
                width, height = img_info.get('width', 0), img_info.get('height', 0)
                if width < 300 or height < 300:
                    logger.info(f"  ❌ Image too small ({width}x{height}). Minimum required is 300x300. Skipping.")
                    temp_file.unlink(missing_ok=True)
                    continue
            else:
                logger.info("  ❌ Could not determine image dimensions. Skipping.")
                temp_file.unlink(missing_ok=True)
                continue

            # Step 4: Use Gemini to verify priority
            if api_key:
                try:
                    import ai_services
                    analysis = ai_services.analyze_player_image(temp_file, player_name, api_key)
                    priority = analysis.get('priority', 0)
                    
                    if priority in [1, 2]:
                        logger.info(f"  ✨ Found High Priority Match (Level {priority})! Stopping search.")
                        candidate['temp_file'] = temp_file
                        candidate['priority'] = priority
                        return candidate
                    
                    if priority == 3:
                        if not best_fallback:
                            logger.info("  📍 Found Priority 3 (Any image of player). Saving as fallback and continuing...")
                            candidate['temp_file'] = temp_file
                            candidate['priority'] = 3
                            best_fallback = candidate
                        else:
                            logger.info("  ⏭️ Another Priority 3. Already have a fallback. Continuing...")
                            temp_file.unlink(missing_ok=True)
                    else:
                        logger.info(f"  ❌ Image rejected by AI (Priority {priority}).")
                        temp_file.unlink(missing_ok=True)
                        
                except Exception as e:
                    logger.error(f"  ⚠️ Error during AI analysis: {e}")
                    temp_file.unlink(missing_ok=True)
            else:
                # No API key, just take the first suitable image
                logger.warning("  ⚠️ No API key provided for verification. Using first suitable image.")
                candidate['temp_file'] = temp_file
                candidate['priority'] = 99
                return candidate

            # Optimization: If we've checked 5 images and have a fallback, settle
            if i >= 4 and best_fallback:
                logger.info("  🏁 Settle: Found a good enough player image after 5 checks.")
                return best_fallback

        if best_fallback:
            logger.info("  🏁 Finished search. Using the best fallback found.")
            return best_fallback
            
        logger.warning(f"  ❌ No suitable images found for {player_name} after checking {max_candidates_to_check} results.")
        return None

    def _get_image_candidates_from_google(self, search_term: str) -> List[dict]:
        """Uses Selenium and regex to extract image candidate URLs from Google's internal data arrays."""
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        candidates = []
        
        try:
            encoded_query = urllib.parse.quote_plus(search_term)
            search_url = f"https://www.google.com/search?q={encoded_query}&tbm=isch"
            driver.get(search_url)
            
            # Wait a moment for dynamic content
            time.sleep(2)
            
            # Get the full page source to parse script tags
            page_source = driver.page_source
            
            # Pattern: [0,"DOCID",["THUMB_URL",H,W],["SOURCE_URL",H,W],...]
            # This regex captures the SOURCE_URL which is the second URL in the array structure
            pattern = r'\[0,"[^"]+",\["https?://encrypted-tbn\d+\.gstatic\.com/images\?q=tbn:[^"]+",\d+,\d+\],\["(https?://[^"]+)",(\d+),(\d+)\]'
            matches = re.findall(pattern, page_source)
            
            for img_url, height, width in matches:
                # Clean up escaped characters (e.g., \u003d -> =)
                img_url = img_url.replace('\\u003d', '=').replace('\\u0026', '&')
                
                # Filter out Google domains to ensure we have the actual source
                if "google.com" not in img_url and "gstatic.com" not in img_url:
                    candidates.append({
                        'direct_url': img_url,
                        'source_page': img_url  # For this strategy, source page is usually same as direct url
                    })
            
            # If regex fails, fall back to a broader search for high-res looking URLs in scripts
            if not candidates:
                logger.info("  Primary regex failed. Trying fallback pattern search.")
                # Look for strings that look like full-res image URLs in JSON-like structures
                potential_urls = re.findall(r'\["(https?://[^"]+\.(?:jpg|jpeg|png|webp))",(\d+),(\d+)\]', page_source)
                for img_url, h, w in potential_urls:
                    if "google.com" not in img_url and "gstatic.com" not in img_url:
                        candidates.append({
                            'direct_url': img_url,
                            'source_page': img_url
                        })

            # Deduplicate
            seen = set()
            unique_candidates = []
            for c in candidates:
                if c['direct_url'] not in seen:
                    seen.add(c['direct_url'])
                    unique_candidates.append(c)
            
            logger.info(f"Found {len(unique_candidates)} unique candidates using data-array extraction.")
            return unique_candidates
            
        except Exception as e:
            logger.error(f"Error extracting Google Image results: {e}")
            return []
        finally:
            driver.quit()

    def _download_full_size_image(self, candidate: dict) -> Optional[Path]:
        """Downloads the full-size image, prioritizing the direct URL but falling back to page scraping."""
        temp_path = self.temp_dir / f"download_{hash(candidate['direct_url'])}.jpg"
        
        # Strategy A: Try direct download from imgurl
        try:
            logger.debug(f"  Attempting direct download: {candidate['direct_url'][:60]}...")
            response = requests.get(candidate['direct_url'], headers=self.headers, timeout=10)
            if response.status_code == 200 and len(response.content) > 5000: # Simple check for non-thumbnail
                with open(temp_path, 'wb') as f:
                    f.write(response.content)
                return temp_path
        except Exception as e:
            logger.debug(f"  Direct download failed: {e}")

        # Strategy B: Navigate to source site and scrape (User requirement Step 2)
        if candidate['source_page'] and candidate['source_page'] != candidate['direct_url']:
            try:
                logger.info(f"  Navigating to source site to find full-scale image: {candidate['source_page'][:60]}...")
                scraped_url = self._extract_image_from_generic_page(candidate['source_page'])
                if scraped_url:
                    response = requests.get(scraped_url, headers=self.headers, timeout=10)
                    if response.status_code == 200:
                        with open(temp_path, 'wb') as f:
                            f.write(response.content)
                        return temp_path
            except Exception as e:
                logger.debug(f"  Source site scraping failed: {e}")
                
        return None

    def _extract_image_from_generic_page(self, page_url: str) -> Optional[str]:
        """Scrapes a webpage to find the primary image (likely the high-res player card)."""
        try:
            response = requests.get(page_url, headers=self.headers, timeout=10)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Common selectors for main high-res images on collector/sports sites
            selectors = [
                'meta[property="og:image"]', 
                'link[rel="image_src"]',
                '.main-image img', '.primary-image img',
                'img.player-card', 'img.card-image',
                '#main-image', '[data-main-image] img'
            ]
            
            for selector in selectors:
                found = soup.select_one(selector)
                if found:
                    url = found.get('src') or found.get('content') or found.get('href')
                    if url:
                        return urllib.parse.urljoin(page_url, url)
            
            # Fallback: Find the largest image on the page
            images = soup.find_all('img')
            if images:
                # Prioritize images with 'player' or 'card' in their name/alt
                for img in images:
                    src = img.get('src')
                    alt = img.get('alt', '').lower()
                    if src and ('card' in alt or 'player' in alt or 'yankees' in alt):
                        return urllib.parse.urljoin(page_url, src)
            
            return None
        except Exception:
            return None

    def download_and_process_player_image(self, player_name: str, date_str: str, api_key: str = None) -> Optional[Path]:
        """Complete workflow orchestrator for finding and saving a player image."""
        result = self.find_first_yankee_image(player_name, api_key)
        
        if not result or 'temp_file' not in result:
            return None
            
        temp_file = result['temp_file']
        
        # Process and save final image (converts to WEBP and moves to images/ folder)
        final_path = self.image_processor.process_player_image(temp_file, self.images_dir, date_str)
        
        # Clean up
        temp_file.unlink(missing_ok=True)
        return final_path

    def cleanup_temp_files(self):
        """Clean up temporary image files."""
        try:
            for temp_file in self.temp_dir.glob("download_*.jpg"):
                temp_file.unlink(missing_ok=True)
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")
