"""
Automated workflow orchestrator for puzzle addition.

Coordinates the entire puzzle addition process from screenshot to deployment.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import logging
from typing import Optional, Dict, Any

# Import existing modules
import config_manager
import ai_services
import scraper
import html_generator
import user_interaction

# Import automation modules
from .image_processor import ImageProcessor
from .player_image_search import PlayerImageSearch
from .git_integration import GitIntegration

logger = logging.getLogger(__name__)

class AutomatedWorkflow:
    """Orchestrates the automated puzzle addition workflow."""
    
    def __init__(self, project_dir: Path, config: Dict[str, Any]):
        """
        Initialize the automated workflow.
        
        Args:
            project_dir: Path to the project directory
            config: Configuration dictionary
        """
        self.project_dir = project_dir
        self.config = config
        self.images_dir = project_dir / "images"
        self.api_key = config.get("gemini_api_key")
        
        # Initialize automation components
        self.image_processor = ImageProcessor()
        self.player_image_search = PlayerImageSearch(self.images_dir)
        self.git_integration = GitIntegration(project_dir)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def process_puzzle_screenshot(self, screenshot_path: Path, date_str: Optional[str] = None) -> bool:
        """
        Process a puzzle screenshot through the entire automated workflow.
        
        Args:
            screenshot_path: Path to the puzzle screenshot
            date_str: Date string (YYYY-MM-DD), uses today if None
            
        Returns:
            True if workflow completed successfully, False otherwise
        """
        try:
            # Determine date
            if date_str is None:
                date_str = datetime.now().strftime("%Y-%m-%d")
            
            logger.info(f"Starting automated workflow for {date_str}")
            
            # Step 1: Process puzzle screenshot
            logger.info("Step 1: Processing puzzle screenshot...")
            clue_path = self._process_puzzle_screenshot(screenshot_path, date_str)
            if not clue_path:
                logger.error("Failed to process puzzle screenshot")
                return False
            
            # Step 2: Identify player using AI
            logger.info("Step 2: Identifying player from puzzle...")
            player_info = self._identify_player(clue_path)
            if not player_info:
                logger.error("Failed to identify player")
                return False
            
            # Step 3: Scrape player statistics
            logger.info("Step 3: Scraping player statistics...")
            scraped_data = self._scrape_player_stats(player_info['name'])
            if scraped_data:
                player_info['career_totals'] = scraped_data['career_totals']
                player_info['yearly_war'] = scraped_data['yearly_war']
            
            # Step 4: Generate AI content (facts and follow-up)
            logger.info("Step 4: Generating AI content...")
            self._generate_ai_content(player_info)
            
            # Step 5: Find and process player image
            logger.info("Step 5: Finding and processing player image...")
            answer_path = self._find_player_image(player_info['name'], date_str)
            if not answer_path:
                logger.warning("Failed to find player image, continuing without it")
            
            # Step 6: Generate HTML page
            logger.info("Step 6: Generating HTML page...")
            formatted_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%B %d, %Y")
            verified_data = user_interaction.review_and_edit_data(
                player_info, self.project_dir, automated=True
            )
            html_generator.generate_detail_page(verified_data, date_str, formatted_date, self.project_dir)
            
            # Step 7: Rebuild index page
            logger.info("Step 7: Rebuilding index page...")
            html_generator.rebuild_index_page(self.project_dir)
            
            # Step 8: Optional git operations
            if self.config.get("auto_commit", False):
                logger.info("Step 8: Performing git operations...")
                self._perform_git_operations(date_str)
            
            logger.info(f"✅ Automated workflow completed successfully for {date_str}")
            return True
            
        except Exception as e:
            logger.error(f"Error in automated workflow: {e}")
            return False
        finally:
            # Cleanup temporary files
            self.player_image_search.cleanup_temp_files()
    
    def _process_puzzle_screenshot(self, screenshot_path: Path, date_str: str) -> Optional[Path]:
        """Process the puzzle screenshot into a clue image."""
        if not screenshot_path.exists():
            logger.error(f"Screenshot not found: {screenshot_path}")
            return None
        
        clue_path = self.image_processor.process_puzzle_screenshot(screenshot_path, self.images_dir, date_str)
        return clue_path
    
    def _identify_player(self, clue_path: Path) -> Optional[Dict[str, Any]]:
        """Identify the player from the clue image using AI."""
        try:
            player_info = ai_services.get_player_info_from_image(clue_path, self.api_key)
            if player_info:
                logger.info(f"Player identified: {player_info['name']}")
                # Handle "Unknown" case - continue with workflow but note the issue
                if player_info.get('name') == 'Unknown':
                    logger.warning("AI returned 'Unknown' for player - continuing workflow may have limited results")
                return player_info
            else:
                logger.error("AI could not identify player")
                return None
        except Exception as e:
            logger.error(f"Error identifying player: {e}")
            return None
    
    def _scrape_player_stats(self, player_name: str) -> Optional[Dict[str, Any]]:
        """Scrape player statistics from Baseball-Reference."""
        try:
            # Skip scraping if player is "Unknown"
            if player_name == 'Unknown':
                logger.warning("Skipping stats scraping for 'Unknown' player")
                return None
                
            scraped_data = scraper.search_and_scrape_player(player_name, automated=True)
            if scraped_data:
                logger.info(f"Successfully scraped stats for {player_name}")
                return scraped_data
            else:
                logger.warning(f"Could not scrape stats for {player_name}")
                return None
        except Exception as e:
            logger.error(f"Error scraping player stats: {e}")
            return None
    
    def _generate_ai_content(self, player_info: Dict[str, Any]) -> None:
        """Generate AI content (facts and follow-up Q&A)."""
        try:
            # Skip AI content generation for "Unknown" player
            if player_info.get('name') == 'Unknown':
                logger.warning("Skipping AI content generation for 'Unknown' player")
                player_info['facts'] = []
                player_info['followup_qa'] = []
                return
                
            # Use the single-call method for efficiency
            combined = ai_services.get_facts_and_followup_from_gemini(
                player_info['name'], self.api_key
            )
            player_info['facts'] = combined.get('facts', [])
            player_info['followup_qa'] = combined.get('qa', [])
            logger.info(f"Generated AI content for {player_info['name']}")
        except Exception as e:
            logger.error(f"Error generating AI content: {e}")
            # Set empty lists as fallback
            player_info['facts'] = []
            player_info['followup_qa'] = []
    
    def _find_player_image(self, player_name: str, date_str: str) -> Optional[Path]:
        """Find and process a player image using sequential search."""
        try:
            # Skip image search for "Unknown" player
            if player_name == 'Unknown':
                logger.warning("Skipping player image search for 'Unknown' player")
                return None
                
            # Use new sequential search to find first valid Yankee image
            logger.info(f"Searching for first valid Yankee image of {player_name}")
            image_candidate = self.player_image_search.find_first_yankee_image(player_name, self.api_key)
            
            if not image_candidate:
                logger.warning(f"No valid Yankee image found for {player_name}")
                return None
            
            # Process the found image
            answer_path = self.images_dir / f"answer-{date_str}.webp"
            
            # Convert and save the image
            if image_candidate.get('temp_file'):
                self.image_processor.convert_to_webp(image_candidate['temp_file'], answer_path)
                logger.info(f"Saved Yankee image: {answer_path}")
                return answer_path
            else:
                logger.error("No temp file found in image candidate")
                return None
            
        except Exception as e:
            logger.error(f"Error finding player image: {e}")
            return None
    
    def _perform_git_operations(self, date_str: str) -> bool:
        """Perform git operations (add, commit, push)."""
        try:
            # Add new files
            files_to_add = [
                f"images/clue-{date_str}.webp",
                f"images/answer-{date_str}.webp",
                f"{date_str}.html"
            ]
            
            # Only add files that exist
            existing_files = []
            for file_pattern in files_to_add:
                file_path = self.project_dir / file_pattern
                if file_path.exists():
                    existing_files.append(str(file_path))
            
            if existing_files:
                # Stage files
                self.git_integration.add_files(existing_files)
                
                # Commit with descriptive message
                commit_message = f"Add puzzle for {date_str} - {self._get_player_name_from_html(date_str)}"
                self.git_integration.commit(commit_message)
                
                # Push if configured
                if self.config.get("auto_push", False):
                    self.git_integration.push()
                
                logger.info(f"Git operations completed for {date_str}")
                return True
            else:
                logger.warning("No new files to commit")
                return False
                
        except Exception as e:
            logger.error(f"Error in git operations: {e}")
            return False
    
    def _get_player_name_from_html(self, date_str: str) -> str:
        """Extract player name from generated HTML file."""
        try:
            html_path = self.project_dir / f"{date_str}.html"
            if html_path.exists():
                with open(html_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Simple extraction of player name from h2 tag
                    import re
                    match = re.search(r'<h2>([^<]+)</h2>', content)
                    if match:
                        return match.group(1).strip()
        except Exception as e:
            logger.debug(f"Error extracting player name from HTML: {e}")
        
        return "Unknown Player"
    
    def batch_process_puzzles(self, screenshot_dir: Path, date_range: Optional[tuple] = None) -> Dict[str, bool]:
        """
        Process multiple puzzle screenshots.
        
        Args:
            screenshot_dir: Directory containing puzzle screenshots
            date_range: Optional tuple of (start_date, end_date) as datetime objects
            
        Returns:
            Dictionary mapping dates to success status
        """
        results = {}
        
        # Find all PNG files in the directory
        screenshot_files = list(screenshot_dir.glob("*.png"))
        
        if not screenshot_files:
            logger.warning(f"No PNG files found in {screenshot_dir}")
            return results
        
        # Sort files by modification time
        screenshot_files.sort(key=lambda x: x.stat().st_mtime)
        
        for screenshot_file in screenshot_files:
            try:
                # Extract date from filename or use modification time
                date_str = self._extract_date_from_filename(screenshot_file)
                
                if date_range:
                    file_date = datetime.strptime(date_str, "%Y-%m-%d")
                    if not (date_range[0] <= file_date <= date_range[1]):
                        continue
                
                logger.info(f"Processing batch puzzle: {screenshot_file.name}")
                success = self.process_puzzle_screenshot(screenshot_file, date_str)
                results[date_str] = success
                
            except Exception as e:
                logger.error(f"Error processing {screenshot_file.name}: {e}")
                results[screenshot_file.stem] = False
        
        # Summary
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        logger.info(f"Batch processing completed: {successful}/{total} successful")
        
        return results
    
    def _extract_date_from_filename(self, file_path: Path) -> str:
        """Extract date from filename or use file modification time."""
        # Try to extract date from filename
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{4}_\d{2}_\d{2})',  # YYYY_MM_DD
            r'(\d{8})',  # YYYYMMDD
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, file_path.stem)
            if match:
                date_str = match.group(1)
                # Normalize to YYYY-MM-DD format
                if '_' in date_str or len(date_str) == 8:
                    date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                return date_str
        
        # Fallback to file modification time
        mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
        return mod_time.strftime("%Y-%m-%d")
