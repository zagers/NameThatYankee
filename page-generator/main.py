# ABOUTME: CLI entry point for the Python-based puzzle automation pipeline.
# ABOUTME: Dispatches tasks for scraping, image processing, and HTML generation.
import os
from PIL import Image
from pathlib import Path
import json
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Any
import re
import subprocess
import sys
import time
import urllib.parse

# Import core functional modules
import config_manager
import ai_services
import scraper
import html_generator
import user_interaction
import fact_verifier
import grounded_ai

# Import automation modules
try:
    from automation.automated_workflow import AutomatedWorkflow
    from automation.player_image_search import PlayerImageSearch
    from config.automation_config import AutomationConfig
    AUTOMATION_AVAILABLE = True
except ImportError:
    AUTOMATION_AVAILABLE = False
    print("⚠️  Automation modules not available - using manual workflow only")



# --- Automation Helper Functions ---

def get_project_directory(config: dict) -> Path:
    """
    Get the project directory from config or user input.
    
    Args:
        config: Current configuration dictionary
        
    Returns:
        Resolved Path to the project directory
    """
    last_path = config.get("last_project_path")
    if last_path:
        project_dir_str = last_path
        print(f"Using default path: {project_dir_str}")
    else:
        try:
            project_dir_str = input("Enter the path to your website project folder: ").strip().strip("'\"")
        except EOFError:
            project_dir_str = "."
            print("No input available, using current directory")
    
    project_dir = Path(project_dir_str).resolve()
    if not project_dir.is_dir():
        print(f"❌ Error: Directory not found at '{project_dir}'")
        sys.exit(1)
    
    # Save the path for next time
    config["last_project_path"] = str(project_dir)
    config_manager.save_config(config)
    return project_dir

def enrich_player_bio(player_name: str, existing_bio: Optional[str]) -> str:
    """
    Enrich a player's biography with Wikipedia data if necessary.
    
    Args:
        player_name: Name of the player
        existing_bio: Current biography text (e.g. from SABR)
        
    Returns:
        Enriched biography string
    """
    bio = existing_bio or ""
    # Enrichment fallback for thin/missing biography
    if not bio or len(bio) < 500:
        wiki_summary = scraper.get_wikipedia_summary(player_name)
        if wiki_summary:
            bio = (bio + "\n\nWikipedia Summary:\n" + wiki_summary).strip()
    return bio

def handle_config_mode():
    """Handle configuration mode for automation settings."""
    print("\n--- Automation Configuration ---")
    
    automation_config = AutomationConfig()
    
    while True:
        print("\nConfiguration Options:")
        print("1. Show current configuration")
        print("2. Set image quality")
        print("3. Enable/disable auto-commit")
        print("4. Enable/disable auto-push")
        print("5. Reset to defaults")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == "1":
            print("\nCurrent Configuration:")
            print(json.dumps(automation_config.config, indent=2))
        
        elif choice == "2":
            try:
                quality = int(input("Enter image quality (1-100): ").strip())
                if 1 <= quality <= 100:
                    automation_config.set_image_quality(quality)
                    print(f"✅ Image quality set to {quality}")
                else:
                    print("❌ Quality must be between 1 and 100")
            except ValueError:
                print("❌ Invalid number")
        
        elif choice == "3":
            enabled = automation_config.is_auto_commit_enabled()
            new_setting = not enabled
            automation_config.set_auto_commit(new_setting)
            print(f"✅ Auto-commit {'enabled' if new_setting else 'disabled'}")
        
        elif choice == "4":
            enabled = automation_config.is_auto_push_enabled()
            new_setting = not enabled
            automation_config.set_auto_push(new_setting)
            print(f"✅ Auto-push {'enabled' if new_setting else 'disabled'}")
        
        elif choice == "5":
            if input("Reset to defaults? (y/N): ").lower().startswith('y'):
                automation_config.reset_to_defaults()
                print("✅ Configuration reset to defaults")
        
        elif choice == "6":
            break
        
        else:
            print("❌ Invalid choice")

def handle_automation_mode(config: dict, automate_workflow: bool, batch_automate: bool):
    """Handle automation mode for puzzle processing."""
    print("\n--- Automated Workflow ---")
    
    # Get project directory
    project_dir = get_project_directory(config)
    
    # Get API key
    api_key = config.get("gemini_api_key")
    if not api_key:
        api_key = input("Please enter your Google Gemini API key: ").strip()
        config["gemini_api_key"] = api_key
        config_manager.save_config(config)
    
    # Initialize automation workflow
    workflow = AutomatedWorkflow(project_dir, config)
    
    if automate_workflow:
        handle_single_automation(workflow)
    elif batch_automate:
        handle_batch_automation(workflow)

def handle_single_automation(workflow: AutomatedWorkflow):
    """Handle single puzzle automation."""
    # Get screenshot path
    screenshot_path = None
    date_str = None
    
    try:
        idx = sys.argv.index("--automate-workflow")
        path_parts = []
        next_idx = idx + 1
        while next_idx < len(sys.argv):
            arg = sys.argv[next_idx]
            if arg.startswith("--"):
                break
            try:
                datetime.strptime(arg, "%Y-%m-%d")
                if not date_str:
                    date_str = arg
                break
            except ValueError:
                path_parts.append(arg)
            next_idx += 1
            
        if path_parts:
            screenshot_path = Path(" ".join(path_parts))
    except (ValueError, IndexError):
        pass
    
    if not screenshot_path:
        default_dir = Path.home() / "Downloads"
        prompt = f"Enter screenshot filename (looks in {default_dir}) or full path: "
        screenshot_str = input(prompt).strip().strip("'\"")
        
        if not screenshot_str:
            # Fallback to nty.png if nothing entered
            screenshot_path = default_dir / "nty.png"
        else:
            provided_path = Path(screenshot_str)
            if provided_path.is_absolute():
                screenshot_path = provided_path
            elif (default_dir / provided_path).exists():
                screenshot_path = default_dir / provided_path
            else:
                screenshot_path = provided_path
    
    if not screenshot_path.exists():
        # Last-ditch check: maybe they typed just the filename but it's not in Downloads?
        # If we already tried that above, it will still fail here.
        print(f"❌ Screenshot not found: {screenshot_path}")
        exit()
    
    # Get optional date if not provided via command line
    if not date_str:
        date_str = input("Enter date (YYYY-MM-DD) or press Enter for today: ").strip()
    
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    else:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            print("❌ Invalid date format. Use YYYY-MM-DD")
            exit()
    
    print(f"\n🚀 Starting automated workflow for {date_str}...")
    success = workflow.process_puzzle_screenshot(screenshot_path, date_str)
    
    if success:
        print(f"\n✅ Automation completed successfully for {date_str}!")
    else:
        print(f"\n❌ Automation failed for {date_str}. Check logs for details.")

def handle_identify_player(config: dict):
    """Handle standalone player identification from a screenshot."""
    print("\n--- Standalone Player Identification ---")
    
    screenshot_path = None
    try:
        idx = sys.argv.index("--identify-player")
        path_parts = []
        next_idx = idx + 1
        while next_idx < len(sys.argv):
            arg = sys.argv[next_idx]
            if arg.startswith("--"):
                break
            path_parts.append(arg)
            next_idx += 1
            
        if path_parts:
            screenshot_path = Path(" ".join(path_parts))
    except (ValueError, IndexError):
        pass
        
    if not screenshot_path:
        default_dir = Path.home() / "Downloads"
        prompt = f"Enter screenshot filename (looks in {default_dir}) or full path: "
        screenshot_str = input(prompt).strip().strip("'\"")
        
        if not screenshot_str:
            # Fallback to nty.png if nothing entered
            screenshot_path = default_dir / "nty.png"
        else:
            provided_path = Path(screenshot_str)
            if provided_path.is_absolute():
                screenshot_path = provided_path
            elif (default_dir / provided_path).exists():
                screenshot_path = default_dir / provided_path
            else:
                screenshot_path = provided_path
    
    if not screenshot_path.exists():
        # Last-ditch check: maybe they typed just the filename but it's not in Downloads?
        # If we already tried that above, it will still fail here.
        print(f"❌ Screenshot not found: {screenshot_path}")
        exit()
        
    api_key = config.get("gemini_api_key")
    if not api_key:
        api_key = input("Please enter your Google Gemini API key: ").strip()
        config["gemini_api_key"] = api_key
        config_manager.save_config(config)
        
    print(f"🚀 Analyzing {screenshot_path.name}...")
    try:
        player_info = ai_services.get_player_info_from_image(screenshot_path, api_key)
        if player_info:
            print(f"\n✅ Identification Result:")
            print(f"   Name:     {player_info.get('name')}")
            print(f"   Nickname: {player_info.get('nickname', 'None')}")
        else:
            print(f"\n❌ AI could not identify the player in the image.")
    except Exception as e:
        print(f"❌ Error during identification: {e}")

def handle_find_image(config: dict):
    """Handle standalone player image search."""
    print("\n--- Standalone Player Image Search ---")
    
    player_name = None
    date_str = None
    direct_url = None
    
    try:
        # Check for --url flag first
        if "--url" in sys.argv:
            url_idx = sys.argv.index("--url")
            if url_idx + 1 < len(sys.argv):
                direct_url = sys.argv[url_idx + 1]
        
        idx = sys.argv.index("--find-image")
        
        # Collect all arguments after --find-image that are not flags and not dates
        name_parts = []
        next_idx = idx + 1
        while next_idx < len(sys.argv):
            arg = sys.argv[next_idx]
            if arg.startswith("--"):
                break
            
            # Check if it's a date
            try:
                datetime.strptime(arg, "%Y-%m-%d")
                # If we haven't found a date yet, this is the date
                if not date_str:
                    date_str = arg
                break
            except ValueError:
                # Not a date, add to name parts
                name_parts.append(arg)
            
            next_idx += 1
            
        if name_parts:
            player_name = " ".join(name_parts)
    except (ValueError, IndexError):
        pass
        
    if not player_name:
        player_name = input("Enter player name: ").strip()
    
    if not date_str:
        date_str = input("Enter date (YYYY-MM-DD) or press Enter for today: ").strip()
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
            
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print("❌ Invalid date format. Use YYYY-MM-DD")
        exit()

    # Get project directory
    project_dir = get_project_directory(config)
        
    images_dir = project_dir / "images"
    api_key = config.get("gemini_api_key")
    
    # Initialize searcher
    searcher = PlayerImageSearch(images_dir)
    
    if direct_url:
        print(f"🚀 Processing direct URL for {player_name}: {direct_url}")
        candidate = {'direct_url': direct_url, 'source_page': direct_url}
        staging_dir = project_dir / "temp_player_images"
        staging_dir.mkdir(exist_ok=True)
        
        temp_file = searcher._download_full_size_image(candidate)
        if temp_file:
            target_path = staging_dir / f"answer-{date_str}-direct.webp"
            searcher.image_processor.convert_to_webp(temp_file, target_path)
            temp_file.unlink(missing_ok=True)
            print(f"\n✅ Successfully saved direct image to: {target_path}")
        else:
            print(f"❌ Failed to download image from: {direct_url}")
        return

    print(f"🚀 Searching for {player_name} for date {date_str}...")
    final_paths = searcher.download_and_process_player_image(player_name, date_str, api_key)
    
    if final_paths:
        print(f"\n✅ Successfully saved {len(final_paths)} candidate(s) to temp_player_images/:")
        for path in final_paths:
            print(f"   - {path}")
        print("\nReview these in 'temp_player_images/' and move the correct one to 'images/' renamed appropriately.")
    else:
        print(f"\n❌ Failed to find or process any suitable images for {player_name}")

def handle_regeneration_mode(config, project_dir, mode_input):
    """Regenerates facts/QA for existing puzzles using the grounded pipeline."""
    print(f"\n--- Fact Regeneration Mode ---")
    
    api_key = config.get("gemini_api_key")
    if not api_key:
        print("❌ Error: API key not found in config.")
        return

    # Load existing stats to find player names
    stats_path = project_dir / "stats_summary.json"
    if not stats_path.exists():
        print("❌ Error: stats_summary.json not found. Run a normal generation first.")
        return
        
    with open(stats_path, 'r') as f:
        all_stats = json.load(f)
    
    # Filter dates based on input
    dates_to_process = []
    if mode_input.upper() == 'ALL':
        dates_to_process = [s['date'] for s in all_stats]
    elif " to " in mode_input:
        try:
            start_str, end_str = mode_input.split(" to ")
            start_date = datetime.strptime(start_str.strip(), "%Y-%m-%d")
            end_date = datetime.strptime(end_str.strip(), "%Y-%m-%d")
            dates_to_process = [s['date'] for s in all_stats if start_date <= datetime.strptime(s['date'], "%Y-%m-%d") <= end_date]
        except ValueError:
            print("❌ Invalid date range format.")
            return
    else:
        dates_to_process = [mode_input.strip()]

    print(f"Plan to process {len(dates_to_process)} dates.")

    # Initialize shared driver for performance
    shared_driver = scraper.get_driver()

    try:
        for date_str in dates_to_process:
            print(f"\nProcessing {date_str}...")
            
            # Find player info in stats
            player_entry = next((s for s in all_stats if s['date'] == date_str), None)
            if not player_entry:
                print(f"  ⚠️ Skipping {date_str}: No entry found in stats_summary.json")
                continue
                
            player_name = player_entry['name']
            if player_name == "Unknown":
                print(f"  ⚠️ Skipping {date_str}: Player name is 'Unknown'")
                continue

            # Check for necessary files
            html_file = project_dir / f"{date_str}.html"
            clue_img = project_dir / "images" / f"clue-{date_str}.webp"
            ans_img = project_dir / "images" / f"answer-{date_str}.webp"
            
            if not (html_file.exists() and clue_img.exists() and ans_img.exists()):
                print(f"  ⚠️ Skipping {date_str}: Missing required files (HTML or images).")
                continue

            try:
                # 1. Scrape Enhanced Data (Using shared driver)
                scraped_data = scraper.search_and_scrape_player(player_name, automated=True, driver=shared_driver)
                sabr_bio = scraper.get_sabr_bio(player_name)
                
                # Enrichment fallback for thin/missing biography
                sabr_bio = enrich_player_bio(player_name, sabr_bio)
                
                if not scraped_data:
                    print(f"  ❌ Failed to scrape BR stats for {player_name}")
                    continue

                player_dossier = {
                    "name": player_name,
                    "career_totals": scraped_data.get('career_totals', {}),
                    "yearly_war": scraped_data.get('yearly_war', []),
                    "transactions": scraped_data.get('transactions', []),
                    "awards": scraped_data.get('awards', []),
                    "positions": scraped_data.get('positions', {}),
                    "bio": sabr_bio
                }

                # 2. Generate Grounded AI Content
                max_retries = 3
                generation_success = False
                for attempt in range(max_retries):
                    print(f"  🤖 Generating grounded trivia (Attempt {attempt + 1}/{max_retries})...")
                    result = grounded_ai.generate_grounded_trivia(player_dossier, api_key)
                    
                    print(f"  🔍 Verifying claims...")
                    if fact_verifier.verify_claims(result.get("claims", []), player_dossier):
                        print("  ✅ All claims verified successfully.")
                        player_data = {
                            'name': player_name,
                            'nickname': player_entry.get('nickname', ''),
                            'facts': result.get("facts", []),
                            'followup_qa': result.get("qa", []),
                            'career_totals': scraped_data['career_totals'],
                            'yearly_war': scraped_data['yearly_war']
                        }
                        
                        # 3. Save updated HTML
                        dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
                        formatted_date = dt_obj.strftime("%B %d, %Y")
                        html_generator.generate_detail_page(player_data, date_str, formatted_date, project_dir)
                        generation_success = True
                        break
                    else:
                        print(f"  ❌ Verification failed.")

                if not generation_success:
                    print(f"  ⚠️ Failed to regenerate verified facts for {date_str} after {max_retries} attempts. Using dynamic stats fallback.")
                    fallback_facts = scraper.generate_stats_fallback(player_dossier)
                    fallback_qa = ai_services.get_followup_qa_from_gemini(player_name, fallback_facts, api_key)
                    player_data = {
                        'name': player_name,
                        'nickname': player_entry.get('nickname', ''),
                        'facts': fallback_facts,
                        'followup_qa': fallback_qa,
                        'career_totals': scraped_data['career_totals'],
                        'yearly_war': scraped_data['yearly_war']
                    }
                    dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    formatted_date = dt_obj.strftime("%B %d, %Y")
                    html_generator.generate_detail_page(player_data, date_str, formatted_date, project_dir)

            except Exception as e:
                print(f"  ❌ Error processing {date_str}: {e}")
    finally:
        shared_driver.quit()

    # Rebuild index at the end
    html_generator.rebuild_index_page(project_dir)
    print("\n✅ Regeneration session complete.")

def handle_batch_automation(workflow: AutomatedWorkflow):
    """Handle batch puzzle automation."""
    # Get screenshot directory
    screenshot_dir = None
    try:
        dir_index = sys.argv.index("--batch-automate") + 1
        if dir_index < len(sys.argv):
            screenshot_dir = Path(sys.argv[dir_index])
    except (ValueError, IndexError):
        pass
    
    if not screenshot_dir:
        default_dir = Path.home() / "Downloads"
        prompt = f"Enter path to screenshot directory [Default: {default_dir}]: "
        screenshot_str = input(prompt).strip().strip("'\"")
        if not screenshot_str:
            screenshot_dir = default_dir
        else:
            screenshot_dir = Path(screenshot_str)
    
    if not screenshot_dir.is_dir():
        print(f"❌ Directory not found: {screenshot_dir}")
        exit()
    
    # Get optional date range
    print("\nOptional date range (leave blank for all files):")
    start_date_str = input("Start date (YYYY-MM-DD): ").strip()
    end_date_str = input("End date (YYYY-MM-DD): ").strip()
    
    date_range = None
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            date_range = (start_date, end_date)
        except ValueError:
            print("❌ Invalid date format. Use YYYY-MM-DD")
            exit()
    
    print(f"\n🚀 Starting batch automation...")
    results = workflow.batch_process_puzzles(screenshot_dir, date_range)
    
    # Summary
    successful = sum(1 for success in results.values() if success)
    total = len(results)
    print(f"\n📊 Batch processing completed: {successful}/{total} successful")
    
    if successful < total:
        print("\nFailed puzzles:")
        for date, success in results.items():
            if not success:
                print(f"  ❌ {date}")


# --- Main Execution ---
if __name__ == "__main__":
    # Help / usage flag
    if "-h" in sys.argv or "--help" in sys.argv:
        print("""
Name That Yankee Page Generator (Python Version)

Usage:
  python main.py [options]

Options:
  --automated           Run without manual review prompts. The script will
                        skip the interactive stats/facts confirmation step.

  --refresh-player-list
                        Scrape all player names from Baseball-Reference.com
                        to update the autocomplete list, then exit.

  --generate-player-list
                        Legacy alias for --refresh-player-list.

  --id-only             Identify the player from each clue image and scrape
                        stats, but do not call Gemini for facts or follow-up
                        questions. Maximizes number of puzzles per day.

  --facts-only          Identify the player and generate three career facts
                        via Gemini, but do not generate follow-up Q&A.

  --identify-player    [screenshot_path]
                        Standalone player identification. Analyzes a puzzle 
                        screenshot and returns the player's name and nickname.

  --automate-workflow  [screenshot_path] [date]
                        Run fully automated workflow. Takes a screenshot file
                        path as optional argument, and optionally a date (YYYY-MM-DD).
                        If not provided, will prompt for missing values.
                        Processes the entire puzzle addition pipeline automatically.

  --find-image         [player_name] [date]
                        Standalone player image search and processing. Finds a 
                        suitable player image, downloads it, converts it to 
                        WEBP, and saves it to the staging folder.

  --url                [direct_url]
                        Used with --find-image to process a specific image 
                        URL directly, skipping the Google search.

  --batch-automate      [screenshot_dir]
                        Batch process multiple screenshots from a directory.

  --config             Show or modify automation configuration settings.

  --regenerate-facts   Regenerate trivia facts for existing puzzles using 
                       the new grounded pipeline. Requires selecting dates.

  --rebuild-index      Rebuild and re-sort index.html and update 
                       stats_summary.json from all available clue images.

  --submit-indexing    Submit new URLs to Google Indexing API.

  --add-nickname       [date] [nickname]
                       Add an alternate accepted answer (nickname/easter egg)
                       to an existing puzzle page. Prompts if not provided.

  -h, --help            Show this help message and exit.

Interactive prompts (normal generation mode):
  1) Website project folder path (uses last path as default if available).
  2) Date selection:
       - A single date:          YYYY-MM-DD
       - A range of dates:      YYYY-MM-DD to YYYY-MM-DD
       - All available clues:   ALL

Notes:
  - Clue images are expected in the 'images' folder as
      clue-YYYY-MM-DD.webp
  - Missing images inside a date range are skipped.
        """)
        sys.exit(0)

    print("--- Name That Yankee Page Generator (Python Version) ---")
    
    is_automated = "--automated" in sys.argv
    if is_automated:
        print("🤖 Running in AUTOMATED mode. User prompts will be skipped.")

    id_only_mode = "--id-only" in sys.argv
    facts_only_mode = "--facts-only" in sys.argv

    if id_only_mode and facts_only_mode:
        print("❌ Error: --id-only and --facts-only cannot be used together. Please choose one mode.")
        sys.exit(1)

    if id_only_mode:
        print("⚙️  Running in ID-ONLY mode (no Gemini facts or follow-up Q&A).")
    elif facts_only_mode:
        print("⚙️  Running in FACTS-ONLY mode (no follow-up Q&A).")

    config = config_manager.load_config()
    last_path = config.get("last_project_path")

    # Check for automation flags
    automate_workflow = "--automate-workflow" in sys.argv
    batch_automate = "--batch-automate" in sys.argv
    find_image = "--find-image" in sys.argv
    identify_player = "--identify-player" in sys.argv
    config_mode = "--config" in sys.argv
    regenerate_mode = "--regenerate-facts" in sys.argv
    rebuild_index_mode = "--rebuild-index" in sys.argv
    add_nickname_mode = "--add-nickname" in sys.argv
    submit_indexing_mode = "--submit-indexing" in sys.argv

    # Handle submit indexing
    if submit_indexing_mode:
        from indexing.submit_urls import main as submit_main
        submit_main()
        sys.exit(0)

    # Handle automation configuration
    if config_mode and AUTOMATION_AVAILABLE:
        handle_config_mode()
        exit()

    # Handle standalone identification
    if identify_player:
        handle_identify_player(config)
        exit()

    # Handle index rebuilding
    if rebuild_index_mode:
        project_dir = get_project_directory(config)
        html_generator.rebuild_index_page(project_dir)
        exit()

    # Handle adding a nickname to an existing puzzle
    if add_nickname_mode:
        project_dir = get_project_directory(config)
        flag_idx = sys.argv.index("--add-nickname")
        remaining = sys.argv[flag_idx + 1:]
        date_str = remaining[0] if len(remaining) >= 1 else input("Enter puzzle date (YYYY-MM-DD): ").strip()
        nickname = remaining[1] if len(remaining) >= 2 else input("Enter nickname to add: ").strip()
        if not nickname:
            print("❌ Nickname cannot be empty.")
            exit(1)
        success = html_generator.add_nickname_to_page(project_dir, date_str, nickname)
        if not success:
            exit(1)
        exit()

    # Handle standalone image search
    if find_image and AUTOMATION_AVAILABLE:
        handle_find_image(config)
        exit()
    elif find_image and not AUTOMATION_AVAILABLE:
        print("❌ Automation modules not available. Please check installation.")
        exit()

    # Handle automated workflow
    if (automate_workflow or batch_automate) and AUTOMATION_AVAILABLE:
        handle_automation_mode(config, automate_workflow, batch_automate)
        exit()
    elif (automate_workflow or batch_automate) and not AUTOMATION_AVAILABLE:
        print("❌ Automation modules not available. Please check installation.")
        exit()

    # Check for player list refresh flags
    if "--refresh-player-list" in sys.argv or "--generate-player-list" in sys.argv:
        project_dir = get_project_directory(config)

        scraper.generate_master_player_list(project_dir)
        exit() # Exit after generating the list

    # 1. Get project directory
    project_dir = get_project_directory(config)
    
    # 2. Get API Key
    api_key = config.get("gemini_api_key")
    if not api_key:
        api_key = input("Please enter your Google Gemini API key (will be saved): ").strip()
    config["gemini_api_key"] = api_key
    
    config_manager.save_config(config)
    
    images_dir = project_dir / "images"
    images_dir.mkdir(exist_ok=True)

    # 3. Choose mode
    if regenerate_mode:
        mode = input("Enter a date (YYYY-MM-DD), a range (YYYY-MM-DD to YYYY-MM-DD), or 'ALL' to REGENERATE facts: ").strip()
        handle_regeneration_mode(config, project_dir, mode)
        exit()

    mode = input("Enter a date (YYYY-MM-DD), a range (YYYY-MM-DD to YYYY-MM-DD), 'REFRESH', or 'ALL': ").strip()

    clue_files_to_process = []

    if mode.upper() == 'REFRESH':
        scraper.generate_master_player_list(project_dir)
        exit()
    elif mode.upper() == 'ALL':
        clue_files_to_process = sorted(images_dir.glob("clue-*.webp"), reverse=True)
    elif " to " in mode:
        try:
            start_date_str, end_date_str = mode.split(" to ")
            start_date = datetime.strptime(start_date_str.strip(), "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str.strip(), "%Y-%m-%d")
            
            current_date = start_date
            while current_date <= end_date:
                clue_path = images_dir / f"clue-{current_date.strftime('%Y-%m-%d')}.webp"
                if clue_path.exists():
                    clue_files_to_process.append(clue_path)
                current_date += timedelta(days=1)
            clue_files_to_process.sort(reverse=True)
        except ValueError:
            print("❌ Invalid date range format. Please use 'YYYY-MM-DD to YYYY-MM-DD'.")
            exit()
    else: # Single Date Mode
        try:
            datetime.strptime(mode, "%Y-%m-%d") # Just to validate format
            clue_path = images_dir / f"clue-{mode}.webp"
            if clue_path.is_file():
                clue_files_to_process.append(clue_path)
            else:
                print(f"❌ Error: Clue image not found at {clue_path}")
                exit()
        except ValueError:
            print("❌ Invalid input. Please enter a date, a range, or 'ALL'.")
            exit()

    if not clue_files_to_process:
        print("🤷 No matching clue images found to process.")
        exit()

    print(f"\nFound {len(clue_files_to_process)} clue images to process.")
    
    # Initialize shared driver for performance
    shared_driver = scraper.get_driver()

    try:
        for clue_path in clue_files_to_process:
            print("\n" + "-"*50)
            
            # Health check for driver
            try:
                shared_driver.current_url
            except Exception:
                print("  ⚠️ Selenium driver unresponsive. Re-initializing...")
                try: shared_driver.quit()
                except: pass
                shared_driver = scraper.get_driver()

            date_match = re.search(r"clue-(\d{4}-\d{2}-\d{2})\.webp", clue_path.name)
            if not date_match:
                continue
            
            date_str = date_match.group(1)
            dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = dt_obj.strftime("%B %d, %Y")
            try:
                player_info = ai_services.get_player_info_from_image(clue_path, api_key)
                if player_info:
                    scraped_data = scraper.search_and_scrape_player(player_info['name'], automated=is_automated, driver=shared_driver)
                    sabr_bio = scraper.get_sabr_bio(player_info['name'])
                    
                    # Enrichment fallback for thin/missing biography
                    sabr_bio = enrich_player_bio(player_info['name'], sabr_bio)
                    
                    if scraped_data:
                        player_info['career_totals'] = scraped_data['career_totals']
                        player_info['yearly_war'] = scraped_data['yearly_war']
                        player_info['transactions'] = scraped_data.get('transactions', [])
                        player_info['awards'] = scraped_data.get('awards', [])

                    player_dossier = {
                        "name": player_info['name'],
                        "career_totals": scraped_data.get('career_totals', {}) if scraped_data else {},
                        "yearly_war": scraped_data.get('yearly_war', []) if scraped_data else [],
                        "transactions": scraped_data.get('transactions', []) if scraped_data else [],
                        "awards": scraped_data.get('awards', []) if scraped_data else [],
                        "positions": scraped_data.get('positions', {}) if scraped_data else {},
                        "bio": sabr_bio
                    }

                    # Determine how much Gemini usage to apply based on mode
                    if id_only_mode:
                        # No Gemini text calls; leave facts and follow-up empty
                        player_info['facts'] = []
                        player_info['followup_qa'] = []
                    else:
                        max_retries = 3
                        generation_success = False
                        
                        for attempt in range(max_retries):
                            print(f"  🤖 Generating grounded trivia (Attempt {attempt + 1}/{max_retries})...")
                            result = grounded_ai.generate_grounded_trivia(player_dossier, api_key)
                            
                            print(f"  🔍 Verifying claims...")
                            if fact_verifier.verify_claims(result.get("claims", []), player_dossier):
                                facts = result.get("facts", [])
                                if not facts:
                                    print(f"  ⚠️ Verification passed but no facts generated. Retrying...")
                                    continue
                                print("  ✅ All claims verified successfully.")
                                player_info['facts'] = facts
                                if not facts_only_mode:
                                    player_info['followup_qa'] = result.get("qa", [])
                                else:
                                    player_info['followup_qa'] = []
                                generation_success = True
                                break
                            else:
                                print(f"  ❌ Verification failed on attempt {attempt + 1}.")
                        
                        if not generation_success:
                            print("  ⚠️ All generation attempts failed verification. Using basic fallback.")
                            fallback_facts = scraper.generate_stats_fallback(player_dossier)
                            player_info['facts'] = fallback_facts
                            if not facts_only_mode:
                                player_info['followup_qa'] = ai_services.get_followup_qa_from_gemini(player_name, fallback_facts, api_key)
                            else:
                                player_info['followup_qa'] = []

                    verified_data = user_interaction.review_and_edit_data(player_info, project_dir, automated=is_automated)
                    html_generator.generate_detail_page(verified_data, date_str, formatted_date, project_dir)
            except ai_services.GeminiDailyQuotaExceeded as e:
                print("\n❌ Gemini Free Tier daily quota has been reached.")
                print("   Details from API: ")
                print(f"   {e}")
                print("\nStopping processing for today. You can rerun this script tomorrow to continue where you left off.")
                break
    finally:
        shared_driver.quit()
    
    html_generator.rebuild_index_page(project_dir)
            
    print("\n🎉 All tasks completed successfully! 🎉")
