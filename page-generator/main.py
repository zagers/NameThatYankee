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
    print("--- Name That Yankee Page Generator (Python Version) ---")
    
    # NEW: Check for the --automated flag
    is_automated = "--automated" in sys.argv
    if is_automated:
        print("🤖 Running in AUTOMATED mode. User prompts will be skipped.")

    config = config_manager.load_config()

    # 1. Get project directory
    last_path = config.get("last_project_path")
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
        clue_files_to_process = sorted(images_dir.glob("clue-*.jpg"), reverse=True)
    elif " to " in mode:
        try:
            start_date_str, end_date_str = mode.split(" to ")
            start_date = datetime.strptime(start_date_str.strip(), "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str.strip(), "%Y-%m-%d")
            
            current_date = start_date
            while current_date <= end_date:
                clue_path = images_dir / f"clue-{current_date.strftime('%Y-%m-%d')}.jpg"
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
            clue_path = images_dir / f"clue-{mode}.jpg"
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
        date_match = re.search(r"clue-(\d{4}-\d{2}-\d{2})\.jpg", clue_path.name)
        if not date_match: continue
        
        date_str = date_match.group(1)
        dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = dt_obj.strftime("%B %d, %Y")
        
        player_info = ai_services.get_player_info_from_image(clue_path, api_key)
        if player_info:
            # Pass the automated flag to the scraper
            scraped_data = scraper.search_and_scrape_player(player_info['name'], automated=is_automated)
            if scraped_data:
                player_info['career_totals'] = scraped_data['career_totals']
                player_info['yearly_war'] = scraped_data['yearly_war']
            
            facts = ai_services.get_facts_from_gemini(player_info['name'], api_key)
            player_info['facts'] = facts
            
            # Pass the automated flag to the review step
            verified_data = user_interaction.review_and_edit_data(player_info, project_dir, automated=is_automated)
            html_generator.generate_detail_page(verified_data, date_str, formatted_date, project_dir)
    
    # Rebuild the index once after all pages in the batch are processed
    html_generator.rebuild_index_page(project_dir)
            
    print("\n🎉 All tasks completed successfully! 🎉")
