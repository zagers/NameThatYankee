import os
from PIL import Image
import google.generativeai as genai
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
