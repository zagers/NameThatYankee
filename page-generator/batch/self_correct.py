# ABOUTME: Interactive self-correction loop for failed AI fact generation.
# ABOUTME: Uses the standard Gemini API to iteratively fix hallucinations and rounding errors.

import os
import json
import re
import sys
import time
from pathlib import Path
from google import genai
from google.genai import types

# Add page-generator to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from batch.utils import StateManager
from batch.apply import patch_html
from grounded_ai import generate_grounded_trivia
import fact_verifier
import config_manager

MODEL = 'gemini-3.1-flash-lite'

SPOILER_BLACKLIST = [
    "Yankees", "Mets", "Red Sox", "Dodgers", "Giants", "Cubs", "White Sox",
    "Orioles", "Blue Jays", "Rays", "Guardians", "Indians", "Tigers", "Royals", "Twins",
    "Angels", "Astros", "Athletics", "Mariners", "Rangers",
    "Braves", "Marlins", "Phillies", "Nationals", "Expos",
    "Reds", "Brewers", "Pirates", "Cardinals", "Diamondbacks", "Rockies", "Padres",
    "New York", "Boston", "Los Angeles", "Chicago", "Baltimore", "Toronto", "Tampa", "Cleveland", 
    "Detroit", "Kansas City", "Minnesota", "Houston", "Oakland", "Seattle", "Arlington", "Texas",
    "Atlanta", "Miami", "Philadelphia", "Washington", "Cincinnati", "Milwaukee", "Pittsburgh", 
    "St. Louis", "Phoenix", "Arizona", "Denver", "Colorado", "San Diego", "San Francisco"
]

def contains_spoiler(facts):
    for fact in facts:
        for s in SPOILER_BLACKLIST:
            if s.lower() in fact.lower():
                return True, s
    return False, None

class SelfCorrector:
    def __init__(self, project_root):
        self.root_path = Path(project_root)
        self.state_file = self.root_path / "page-generator" / "batch" / "state.json"
        self.dossier_dir = self.root_path / "temp" / "dossiers"
        self.manager = StateManager(self.state_file)
        
        config = config_manager.load_config()
        self.api_key = config.get("gemini_api_key")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in local config")
        self.client = genai.Client(api_key=self.api_key)

    def run(self, limit=None):
        # Find all dates that aren't completed
        all_dates = sorted(self.manager.state.keys())
        failed_dates = [d for d in all_dates if self.manager.get_status(d) != "completed"]
        
        print(f"🔧 Found {len(failed_dates)} puzzles requiring self-correction.")
        
        processed = 0
        for date_str in failed_dates:
            if limit and processed >= limit:
                break
                
            player_name = self.manager.get_data(date_str).get('player', date_str)
            print(f"\n🚀 Processing {player_name} ({date_str})...")
            
            dossier_path = self.dossier_dir / f"{date_str}.json"
            if not dossier_path.exists():
                print(f"  ⚠️ Dossier not found for {date_str}, skipping.")
                continue
                
            with open(dossier_path, 'r', encoding='utf-8') as f:
                dossier = json.load(f)
            
            success = self.correct_player(date_str, player_name, dossier)
            if success:
                processed += 1
                # Small pause to respect rate limits on standard API
                time.sleep(2)

    def correct_player(self, date_str, player_name, dossier):
        # We'll try up to 5 times for these strict rules
        for attempt in range(5):
            print(f"  🤖 Generating verified trivia (Attempt {attempt + 1}/5)...")
            
            try:
                # Use the system's grounded_ai generator which has the Hall of Boredom rules
                result = generate_grounded_trivia(dossier, self.api_key)
                
                facts = result.get("facts", [])
                qa = result.get("qa", [])
                claims = result.get("claims", [])
                
                # Quality Check 1: NO META-COMMENTARY ALLOWED
                all_text = " ".join(facts) + " " + " ".join([q.get('question', '') + " " + q.get('answer', '') for q in qa])
                if any(word in all_text.lower() for word in ["sabr", "bioproject", "biography remains", "unassigned"]):
                    print("  ⚠️ REJECTED: Response contains forbidden meta-commentary.")
                    continue
                
                # Quality Check 2: NO SPOILERS IN HINTS
                has_spoiler, word = contains_spoiler(facts)
                if has_spoiler:
                    print(f"  ⚠️ REJECTED: Hint contains spoiler word '{word}'.")
                    continue

                # Check for 3-hint rule
                if len(facts) != 3:
                    print(f"  ⚠️ Invalid fact count ({len(facts)}), retrying...")
                    continue

                # Run verification
                if fact_verifier.verify_claims(claims, dossier):
                    # Success!
                    html_file = self.root_path / f"{date_str}.html"
                    if html_file.exists():
                        with open(html_file, 'r', encoding='utf-8') as hf:
                            old_html = hf.read()
                        
                        updated_html = patch_html(old_html, result, player_name)
                        
                        with open(html_file, 'w', encoding='utf-8') as hf:
                            hf.write(updated_html)
                        
                        self.manager.set_status(date_str, "completed")
                        self.manager.save()
                        print(f"  ✅ Successfully updated {date_str}")
                        return True
                    else:
                        print(f"  ❌ HTML file not found: {html_file}")
                        return False
                else:
                    print(f"  🔍 Verification failed on stats/years.")
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
                
        print(f"  ⚠️ Failed to generate verified facts for {date_str} after 5 attempts.")
        return False

if __name__ == "__main__":
    project_root = sys.argv[1] if len(sys.argv) > 1 else "."
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    corrector = SelfCorrector(project_root)
    corrector.run(limit=limit)
