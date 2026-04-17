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
    
    def find_first_yankee_image(self, player_name: str, api_key: str = None) -> List[dict]:
        """
        Find up to 3 best images of the player based on prioritized criteria.
        
        Search Term: "<player name> yankees card"
        Priorities:
        1. Baseball card + Yankee uniform
        2. Any image + Yankee uniform
        3. Any image of the player
        """
        search_term = f"{player_name} yankees card"
        logger.info(f"🚀 Searching Google Images for: {search_term}")
        
        candidates = self._get_image_candidates_from_google(search_term)
        if not candidates:
            logger.warning("No image candidates found in Google Search.")
            return []

        logger.info(f"Total candidates available from search: {len(candidates)}")
        best_matches = []
        fallbacks = []
        max_candidates_to_check = 25
        
        # Determine actual number to check
        num_to_check = min(len(candidates), max_candidates_to_check)
        logger.info(f"🔍 Will evaluate up to {num_to_check} candidates...")

        for i, candidate in enumerate(candidates[:max_candidates_to_check]):
            current_idx = i + 1
            logger.info(f"\n--- 🧐 Evaluating Candidate {current_idx}/{num_to_check} ---")
            logger.info(f"Source: {candidate['source_page'][:80]}...")
            
            # Step 2 & 3: Download full scale and check suitability
            temp_file = self._download_full_size_image(candidate)
            if not temp_file:
                continue
                
            # Check suitability (size & format)
            img_info = self.image_processor.get_image_info(temp_file)
            if img_info:
                width, height = img_info.get('width', 0), img_info.get('height', 0)
                if width < 200 or height < 200:
                    logger.info(f"  ❌ Image too small ({width}x{height}). Minimum required is 200x200. Skipping.")
                    temp_file.unlink(missing_ok=True)
                    continue

                # Orientation check: Reject landscape (width > height)

                if width > height:
                    logger.info(f"  ❌ Image is landscape format ({width}x{height}). Skipping.")
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
                    priority = analysis.get('priority', 3)
                    crop_box = analysis.get('crop_box')
                    
                    if priority in [1, 2]:
                        # Perform smart crop if requested by AI
                        if crop_box:
                            if self.image_processor.crop_to_bounding_box(temp_file, crop_box):
                                # Re-validate dimensions after crop
                                img_info = self.image_processor.get_image_info(temp_file)
                                if img_info:
                                    w, h = img_info.get('width', 0), img_info.get('height', 0)
                                    if w < 100 or h < 100: # Slightly more lenient after crop
                                        logger.info(f"  ❌ Cropped image too small ({w}x{h}). Skipping.")
                                        temp_file.unlink(missing_ok=True)
                                        continue
                        
                        logger.info(f"  ✨ Found High Priority Match (Level {priority})!")
                        candidate['temp_file'] = temp_file
                        candidate['priority'] = priority
                        best_matches.append(candidate)
                        
                        # Stop ONLY if we have 3 Priority 1 images specifically
                        p1_count = len([m for m in best_matches if m['priority'] == 1])
                        if p1_count >= 3:
                            logger.info(f"  🏁 Found {p1_count} Priority 1 matches. Stopping search early.")
                            break
                    
                    elif priority == 3:
                        if len(fallbacks) < 3:
                            logger.info(f"  📍 Found Priority 3 (Fallback). Staging as option {len(fallbacks)+1}...")
                            candidate['temp_file'] = temp_file
                            candidate['priority'] = 3
                            fallbacks.append(candidate)
                        else:
                            logger.info("  ⏭️ Already have 3 fallbacks. Skipping.")
                            temp_file.unlink(missing_ok=True)
                    else:
                        logger.info(f"  ❌ Image rejected by AI (Priority {priority}).")
                        temp_file.unlink(missing_ok=True)
                        
                except Exception as e:
                    logger.error(f"  ⚠️ Error during AI analysis: {e}")
                    temp_file.unlink(missing_ok=True)
            else:
                # No API key, just take the first 3 suitable images
                logger.warning("  ⚠️ No API key provided for verification.")
                candidate['temp_file'] = temp_file
                candidate['priority'] = 99
                best_matches.append(candidate)
                if len(best_matches) >= 3:
                    return best_matches

        # Combine results: Best matches first, then fill with fallbacks until we have 3
        final_results = best_matches + fallbacks
        final_results = final_results[:3]
        
        # Cleanup any fallbacks that didn't make the final cut
        for f in fallbacks:
            if f not in final_results and 'temp_file' in f:
                f['temp_file'].unlink(missing_ok=True)

        if final_results:
            logger.info(f"  🏁 Finished search. Providing {len(final_results)} candidates for review.")
            return final_results
            
        logger.warning(f"  ❌ No suitable images found for {player_name} after checking {max_candidates_to_check} results.")
        return []

    def _get_image_candidates_from_google(self, search_term: str) -> List[dict]:
        """Uses Selenium to extract image candidate URLs using a robust hybrid strategy."""
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        
        # More sophisticated headers to avoid bot detection
        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        options.add_argument(f"user-agent={user_agent}")
        
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        candidates = []
        
        try:
            encoded_query = urllib.parse.quote_plus(search_term)
            # Use a standard image search URL
            search_url = f"https://www.google.com/search?q={encoded_query}&tbm=isch"
            logger.info(f"🔍 Searching Google Images: {search_url}")
            driver.get(search_url)
            
            # Allow time for the page to settle
            time.sleep(5)
            
            # Scroll multiple times to trigger lazy loading of primary results
            for _ in range(3):
                driver.execute_script("window.scrollBy(0, 800);")
                time.sleep(1)
            
            # --- Method 1: Direct DOM Attribute Extraction ---
            # Modern Google Images often puts the source URL in a data attribute or script-linked ID
            # We'll look for common patterns in <img> and <a> tags
            elements = driver.find_elements(By.CSS_SELECTOR, "img[src^='http'], a[href*='imgurl']")
            for el in elements:
                try:
                    # If it's a link, extract from query params
                    href = el.get_attribute("href")
                    if href and "imgurl=" in href:
                        parsed = urllib.parse.urlparse(href)
                        img_url = urllib.parse.parse_qs(parsed.query).get('imgurl', [None])[0]
                        if img_url:
                            candidates.append({'direct_url': img_url, 'source_page': img_url})
                    
                    # If it's an image, check for data-src (lazy load source)
                    data_src = el.get_attribute("data-src")
                    if data_src and data_src.startswith("http") and "gstatic" not in data_src:
                        candidates.append({'direct_url': data_src, 'source_page': data_src})
                except:
                    continue

            # --- Method 2: Comprehensive Regex Parsing ---
            page_source = driver.page_source
            self._last_page_source = page_source
            # Pattern for the standard data array
            patterns = [
                r'\[0,"[^"]+",\["https?://encrypted-tbn\d+\.gstatic\.com/images\?q=tbn:[^"]+",\d+,\d+\],\["(https?://[^"]+)",(\d+),(\d+)\]',
                r'\["(https?://[^"]+\.(?:jpg|jpeg|png|webp))",(\d+),(\d+)\]'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_source)
                for match in matches:
                    img_url = match[0] if isinstance(match, tuple) else match
                    img_url = img_url.replace('\\u003d', '=').replace('\\u0026', '&')
                    if "google.com" not in img_url and "gstatic.com" not in img_url:
                        candidates.append({'direct_url': img_url, 'source_page': img_url})

            # Deduplicate and Prioritize
            seen = set()
            unique_candidates = []
            priority_domains = ['showzone.io', 'showzone.gg', 'cards.theshow.com', 'topps.com', 'ebayimg.com', 'ebay.com']
            
            # First pass: Priority domains
            for c in candidates:
                url = c['direct_url']
                if url not in seen and any(domain in url.lower() for domain in priority_domains):
                    seen.add(url)
                    unique_candidates.append(c)
            
            # Second pass: General results
            for c in candidates:
                url = c['direct_url']
                if url not in seen:
                    seen.add(url)
                    unique_candidates.append(c)
            
            logger.info(f"Total unique candidates identified: {len(unique_candidates)}")
            
            # Fallback to Bing if Google returns nothing (often due to bot detection)
            if not unique_candidates:
                logger.info("⚠️ No candidates from Google. Attempting fallback to Bing...")
                unique_candidates = self._try_bing_search(search_term, driver)

            if unique_candidates:
                logger.info(f"Top candidate: {unique_candidates[0]['direct_url'][:80]}...")
                
            return unique_candidates
            
        except Exception as e:
            logger.error(f"Error extracting Google Image results: {e}")
            return []
        finally:
            driver.quit()

    def _try_bing_search(self, search_term: str, driver: webdriver.Chrome) -> List[dict]:
        """Fallback image search using Bing."""
        candidates = []
        try:
            encoded_query = urllib.parse.quote_plus(search_term)
            search_url = f"https://www.bing.com/images/search?q={encoded_query}"
            logger.info(f"🔍 Searching Bing Images: {search_url}")
            driver.get(search_url)
            time.sleep(5)
            
            # Scroll to trigger lazy loading
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(2)
            
            # Bing often uses 'm' attribute in 'iusc' class for image metadata
            elements = driver.find_elements(By.CSS_SELECTOR, "a.iusc")
            for el in elements:
                try:
                    m_data = el.get_attribute("m")
                    if m_data:
                        import json
                        data = json.loads(m_data)
                        img_url = data.get('murl')
                        if img_url:
                            candidates.append({'direct_url': img_url, 'source_page': img_url})
                except:
                    continue
            
            # Deduplicate
            seen = set()
            unique_candidates = []
            for c in candidates:
                url = c['direct_url']
                if url not in seen:
                    seen.add(url)
                    unique_candidates.append(c)
            
            logger.info(f"Total unique candidates from Bing: {len(unique_candidates)}")
            return unique_candidates
        except Exception as e:
            logger.error(f"Error extracting Bing Image results: {e}")
            return []

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

    def download_and_process_player_image(self, player_name: str, date_str: str, api_key: str = None) -> List[Path]:
        """Complete workflow orchestrator for finding and saving multiple player image candidates."""
        staging_dir = self.images_dir.parent / "temp_player_images"
        staging_dir.mkdir(exist_ok=True)
        
        # --- Archive existing candidates ---
        # Reset state to ensure a clean slate for search candidates
        old_dir = staging_dir / "old"
        if old_dir.exists():
            # Clear previous "old" candidates to avoid accumulation
            for old_file in old_dir.glob("*.webp"):
                old_file.unlink(missing_ok=True)
        else:
            old_dir.mkdir(exist_ok=True)
            
        for current_file in staging_dir.glob("*.webp"):
            try:
                import shutil
                shutil.move(str(current_file), str(old_dir / current_file.name))
            except Exception as e:
                logger.debug(f"Could not archive {current_file.name}: {e}")

        results = self.find_first_yankee_image(player_name, api_key)
        
        if not results:
            return []
            
        final_paths = []
        
        for i, result in enumerate(results):
            temp_file = result.get('temp_file')
            if not temp_file or not temp_file.exists():
                continue
                
            # Name: answer-YYYY-MM-DD-N.webp
            target_name = f"answer-{date_str}-{i+1}.webp"
            target_path = staging_dir / target_name
            
            # Process and convert to webp
            try:
                self.image_processor.convert_to_webp(temp_file, target_path)
                final_paths.append(target_path)
            except Exception as e:
                logger.error(f"Error converting {temp_file} to webp: {e}")
            
            # Clean up original temp download
            temp_file.unlink(missing_ok=True)
            
        # Final cleanup of any stray downloads in the temp folder
        self.cleanup_temp_files()
        
        logger.info(f"✅ Staged {len(final_paths)} candidate images in {staging_dir}")
        return final_paths

    def cleanup_temp_files(self):
        """Clean up temporary image files."""
        try:
            for temp_file in self.temp_dir.glob("download_*.jpg"):
                temp_file.unlink(missing_ok=True)
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")
