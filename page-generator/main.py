import os
from PIL import Image
from pathlib import Path
import json
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import subprocess
import sys
import time
import urllib.parse

# Import functions from our new modules
import config_manager
import ai_services
import scraper
import html_generator
import user_interaction

# Import automation modules
try:
    from automation.automated_workflow import AutomatedWorkflow
    from config.automation_config import AutomationConfig
    AUTOMATION_AVAILABLE = True
except ImportError:
    AUTOMATION_AVAILABLE = False
    print("⚠️  Automation modules not available - using manual workflow only")


# --- Automation Helper Functions ---

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
    
    # Get project directory - use cached path without prompting for automation
    last_path = config.get("last_project_path")
    if last_path:
        project_dir_str = last_path
        print(f"Using default path: {project_dir_str}")
    else:
        project_dir_str = input("Enter the path to your website project folder: ").strip().strip("'\"")
    
    project_dir = Path(project_dir_str).resolve()
    if not project_dir.is_dir():
        print(f"❌ Error: Directory not found at '{project_dir}'")
        exit()
    
    # Save the path for next time
    config["last_project_path"] = str(project_dir)
    config_manager.save_config(config)
    
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
        screenshot_index = sys.argv.index("--automate-workflow") + 1
        if screenshot_index < len(sys.argv):
            screenshot_path = Path(sys.argv[screenshot_index])
            # Check if date is also provided
            if screenshot_index + 1 < len(sys.argv):
                potential_date = sys.argv[screenshot_index + 1]
                # Validate if it's a date format (YYYY-MM-DD)
                try:
                    datetime.strptime(potential_date, "%Y-%m-%d")
                    date_str = potential_date
                except ValueError:
                    # Not a date format, so it's not the date argument
                    pass
    except (ValueError, IndexError):
        pass
    
    if not screenshot_path:
        screenshot_str = input("Enter path to puzzle screenshot: ").strip().strip("'\"")
        screenshot_path = Path(screenshot_str)
    
    if not screenshot_path.exists():
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
        screenshot_str = input("Enter path to screenshot directory: ").strip().strip("'\"")
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

  --generate-player-list
                        Generate a master list of all players from existing
                        detail pages, then exit. Skips normal page generation.

  --id-only             Identify the player from each clue image and scrape
                        stats, but do not call Gemini for facts or follow-up
                        questions. Maximizes number of puzzles per day.

  --facts-only          Identify the player and generate three career facts
                        via Gemini, but do not generate follow-up Q&A.

  --automate-workflow  [screenshot_path] [date]
                        Run fully automated workflow. Takes a screenshot file
                        path as optional argument, and optionally a date (YYYY-MM-DD).
                        If not provided, will prompt for missing values.
                        Processes the entire puzzle addition pipeline automatically.

  --batch-automate      [screenshot_dir]
                        Batch process multiple screenshots from a directory.

  --config             Show or modify automation configuration settings.

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
    config_mode = "--config" in sys.argv

    # Handle automation configuration
    if config_mode and AUTOMATION_AVAILABLE:
        handle_config_mode()
        exit()

    # Handle automated workflow
    if (automate_workflow or batch_automate) and AUTOMATION_AVAILABLE:
        handle_automation_mode(config, automate_workflow, batch_automate)
        exit()
    elif (automate_workflow or batch_automate) and not AUTOMATION_AVAILABLE:
        print("❌ Automation modules not available. Please check installation.")
        exit()

    # NEW: Check for the --generate-player-list flag
    if "--generate-player-list" in sys.argv:
        prompt_message = "Enter the path to your website project folder to save the player list"
        if last_path:
            prompt_message += f" [Default: {last_path}]: "
        else:
            prompt_message += ": "
        project_dir_str = input(prompt_message).strip().strip("'\"")
        if not project_dir_str and last_path:
            project_dir_str = last_path
            print(f"Using default path: {project_dir_str}")
        
        project_dir = Path(project_dir_str).resolve()
        if not project_dir.is_dir():
            print(f"❌ Error: Directory not found at '{project_dir}'")
            exit()
        
        # Save the path for next time
        config["last_project_path"] = str(project_dir)
        config_manager.save_config(config)

        scraper.generate_master_player_list(project_dir)
        exit() # Exit after generating the list

    # 1. Get project directory
    prompt_message = "Enter the path to your website project folder"
    if last_path:
        prompt_message += f" [Default: {last_path}]: "
    else:
        prompt_message += ": "
    project_dir_str = input(prompt_message).strip().strip("'\"")
    if not project_dir_str and last_path:
        project_dir_str = last_path
        print(f"Using default path: {project_dir_str}")
    
    project_dir = Path(project_dir_str).resolve()
    if not project_dir.is_dir():
        print(f"❌ Error: Directory not found at '{project_dir}'")
        exit()
    config["last_project_path"] = str(project_dir)

    # 2. Get API Key
    api_key = config.get("gemini_api_key")
    if not api_key:
        api_key = input("Please enter your Google Gemini API key (will be saved): ").strip()
    config["gemini_api_key"] = api_key
    
    config_manager.save_config(config)
    
    images_dir = project_dir / "images"
    images_dir.mkdir(exist_ok=True)

    # 3. Choose mode
    mode = input("Enter a date (YYYY-MM-DD), a range (YYYY-MM-DD to YYYY-MM-DD), or 'ALL': ").strip()

    clue_files_to_process = []

    if mode.upper() == 'ALL':
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
    
    for clue_path in clue_files_to_process:
        print("\n" + "-"*50)
        date_match = re.search(r"clue-(\d{4}-\d{2}-\d{2})\.webp", clue_path.name)
        if not date_match:
            continue
        
        date_str = date_match.group(1)
        dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = dt_obj.strftime("%B %d, %Y")
        
        try:
            player_info = ai_services.get_player_info_from_image(clue_path, api_key)
            if player_info:
                scraped_data = scraper.search_and_scrape_player(player_info['name'], automated=is_automated)
                if scraped_data:
                    player_info['career_totals'] = scraped_data['career_totals']
                    player_info['yearly_war'] = scraped_data['yearly_war']

                # Determine how much Gemini usage to apply based on mode
                if id_only_mode:
                    # No Gemini text calls; leave facts and follow-up empty
                    player_info['facts'] = []
                    player_info['followup_qa'] = []
                elif facts_only_mode:
                    # Only fetch facts via Gemini, skip follow-up Q&A
                    facts = ai_services.get_facts_from_gemini(player_info['name'], api_key)
                    player_info['facts'] = facts
                    player_info['followup_qa'] = []
                else:
                    # Full mode: single call to get both facts and follow-up Q&A
                    combined = ai_services.get_facts_and_followup_from_gemini(player_info['name'], api_key)
                    player_info['facts'] = combined.get('facts', [])
                    player_info['followup_qa'] = combined.get('qa', [])

                verified_data = user_interaction.review_and_edit_data(player_info, project_dir, automated=is_automated)
                html_generator.generate_detail_page(verified_data, date_str, formatted_date, project_dir)
        except ai_services.GeminiDailyQuotaExceeded as e:
            print("\n❌ Gemini Free Tier daily quota has been reached.")
            print("   Details from API: ")
            print(f"   {e}")
            print("\nStopping processing for today. You can rerun this script tomorrow to continue where you left off.")
            break
    
    html_generator.rebuild_index_page(project_dir)
            
    print("\n🎉 All tasks completed successfully! 🎉")
