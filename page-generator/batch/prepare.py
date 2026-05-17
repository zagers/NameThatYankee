# ABOUTME: Preparation phase for batch quiz processing.
# ABOUTME: Scrapes player data and generates dossiers for Gemini Batch API requests.

import json
import os
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup

# Ensure we can import from parent directory and sibling batch directory
current_dir = Path(__file__).parent
if str(current_dir.parent) not in sys.path:
    sys.path.append(str(current_dir.parent))

from batch.utils import StateManager, BATCH_PROMPT_TEMPLATE
import scraper

def build_request(dossier):
    """
    Constructs a GenerateContentRequest dictionary for the Gemini Batch API.
    """
    prompt = BATCH_PROMPT_TEMPLATE.format(
        name=dossier["name"],
        dossier_json=json.dumps(dossier, indent=2)
    )
    
    return {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

def extract_player_name(html_content):
    """Extracts player name from <h2> tag in the HTML, stripping nicknames."""
    soup = BeautifulSoup(html_content, 'html.parser')
    h2 = soup.find('h2')
    if h2:
        full_title = h2.get_text(strip=True)
        # Strip nickname in quotes if present (e.g. Don Mattingly "Donnie Baseball")
        player_name = full_title.split('"')[0].strip() if '"' in full_title else full_title
        return player_name
    return None

def prepare_batch(project_root):
    """
    Main loop to scrape dossiers and generate requests.jsonl.
    """
    root_path = Path(project_root)
    state_file = root_path / "page-generator" / "batch" / "state.json"
    dossier_dir = root_path / "temp" / "dossiers"
    requests_file = root_path / "temp" / "requests.jsonl"
    
    dossier_dir.mkdir(parents=True, exist_ok=True)
    
    manager = StateManager(state_file)
    shared_driver = scraper.get_driver()
    
    try:
        # 1. Scrape dossiers
        html_files = sorted(list(root_path.glob("202*.html")))
        for html_file in html_files:
            date_str = html_file.stem # YYYY-MM-DD
            
            status = manager.get_status(date_str)
            if status in ["scraped", "submitted", "completed"]:
                print(f"Skipping {date_str} (status: {status})")
                continue
                
            print(f"Processing {date_str}...")
            with open(html_file, 'r', encoding='utf-8') as f:
                player_name = extract_player_name(f.read())
                
            if not player_name:
                print(f"Could not find player name in {html_file}")
                continue
                
            print(f"Scraping dossier for {player_name}...")
            stats = scraper.search_and_scrape_player(player_name, automated=True, driver=shared_driver)
            bio = scraper.get_sabr_bio(player_name)
            
            # Limit bio to ~2500 words to avoid context overflow
            if bio:
                words = bio.split()
                if len(words) > 2500:
                    bio = " ".join(words[:2500]) + "..."
            
            dossier = {
                "name": player_name,
                "bio": bio or "No SABR bio found."
            }
            if stats:
                dossier.update(stats)
            else:
                dossier.update({
                    "career_totals": {},
                    "yearly_war": [],
                    "transactions": [],
                    "awards": []
                })
                
            dossier_path = dossier_dir / f"{date_str}.json"
            with open(dossier_path, 'w', encoding='utf-8') as f:
                json.dump(dossier, f, indent=2)
                
            manager.set_status(date_str, "scraped", data={"player": player_name})
            manager.save()
            
        # 2. Generate requests.jsonl
        print("Generating requests.jsonl...")
        with open(requests_file, 'w', encoding='utf-8') as f_out:
            for date_str, entry in manager.state.items():
                if entry.get("status") == "scraped":
                    dossier_path = dossier_dir / f"{date_str}.json"
                    if dossier_path.exists():
                        with open(dossier_path, 'r', encoding='utf-8') as f_in:
                            dossier = json.load(f_in)
                            request = build_request(dossier)
                            f_out.write(json.dumps(request) + "\n")
                            
        print(f"Successfully generated {requests_file}")
        
    finally:
        shared_driver.quit()

if __name__ == "__main__":
    import sys
    project_root = sys.argv[1] if len(sys.argv) > 1 else "."
    prepare_batch(project_root)
