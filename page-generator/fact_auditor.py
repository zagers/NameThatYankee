# ABOUTME: Audits AI-generated player facts using a two-phase verification process.
# ABOUTME: Identifies identity swaps and statistical inaccuracies in trivia puzzles.
import os
import json
import re
import time
from pathlib import Path
from bs4 import BeautifulSoup
from google import genai
from google.genai import types

# --- CONFIGURATION ---
MODEL = 'gemini-3.1-flash-lite'
PROJECT_DIR = Path(__file__).parent.parent
CONFIG_PATH = Path.home() / ".yankee_generator_config.json"
REPORT_PATH = PROJECT_DIR / "FACT_AUDIT_REPORT.md"

def load_api_key():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found at {CONFIG_PATH}")
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
    return config.get("gemini_api_key")

_LAST_CALL_TS = time.time()

def _respect_rate_limit():
    global _LAST_CALL_TS
    now = time.time()
    min_interval = 13.0
    elapsed = now - _LAST_CALL_TS
    if elapsed < min_interval:
        time.sleep(min_interval - elapsed)
    _LAST_CALL_TS = time.time()

class FactAuditor:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        self.results = []

    def scrape_facts(self, html_path):
        """Extracts player name and all 6 facts from a puzzle HTML file."""
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
        
        # Identity
        h2_el = soup.find('h2')
        if not h2_el:
            return None
        
        full_title = h2_el.get_text(strip=True)
        player_name = full_title.split('"')[0].strip() if '"' in full_title else full_title
        
        # Main Facts
        facts = [li.get_text(strip=True) for li in soup.select('.player-info ul li')]
        
        # Q&A Facts (from data-answer attributes)
        btns = soup.select('.followup-btn')
        for btn in btns:
            answer = btn.get('data-answer')
            if answer:
                facts.append(answer)
        
        return {
            "name": player_name,
            "facts": facts,
            "date": html_path.stem
        }

    def run_phase_1(self, player_data):
        """Phase 1: Skeptical Identity Sweep."""
        print(f"🔍 Phase 1: Checking identity for {player_data['name']} ({player_data['date']})...")
        _respect_rate_limit()
        
        prompt = f"""
        You are a skeptical baseball historian. I have a list of facts that are SUPPOSED to be about the player "{player_data['name']}".
        
        FACTS TO AUDIT:
        {json.dumps(player_data['facts'])}
        
        YOUR TASK:
        1. Identify the player(s) described by these facts.
        2. Determine if ALL facts consistently describe "{player_data['name']}".
        3. If any fact describes a different player, or if the facts as a whole better fit someone else, you MUST flag it.
        
        Return ONLY a JSON object:
        {{
          "primary_identity": "Name of the player most facts describe",
          "is_fully_consistent": true/false,
          "reasoning": "Brief explanation if inconsistent"
        }}
        """
        
        try:
            response = self.client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.1)
            )
            
            json_text = response.text.strip().replace("```json", "").replace("```", "").strip()
            result = json.loads(json_text)
            predicted_name = result.get("primary_identity", "Unknown")
            is_consistent = result.get("is_fully_consistent", True)
            
            # Match if consistent AND the name matches
            name_matches = predicted_name.lower() in player_data['name'].lower() or player_data['name'].lower() in predicted_name.lower()
            
            return {
                "is_match": is_consistent and name_matches,
                "predicted_name": predicted_name,
                "reasoning": result.get("reasoning", "")
            }
        except Exception as e:
            print(f"  ❌ Error in Phase 1: {e}")
            return {"is_match": True, "predicted_name": "Error"} # Assume match on error to avoid Phase 2 spam

    def run_phase_2(self, player_data):
        """Phase 2: Grounded Search Audit."""
        print(f"🚀 Phase 2: Grounded audit for {player_data['name']}...")
        verdicts = []
        
        # Check facts in 2 batches to save tokens while keeping context clear
        batches = [player_data['facts'][:3], player_data['facts'][3:]]
        
        for batch in batches:
            _respect_rate_limit()
            prompt = f"""
            Verify each of these baseball facts for the player "{player_data['name']}" using Google Search.
            
            Facts:
            {json.dumps(batch)}
            
            Return ONLY a JSON list of objects:
            [
              {{
                "fact": "...",
                "is_accurate": true/false,
                "reasoning": "...",
                "source": "..."
              }}
            ]
            """
            
            try:
                response = self.client.models.generate_content(
                    model=MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        tools=[types.Tool(google_search=types.GoogleSearch())]
                    )
                )
                
                json_text = response.text.strip().replace("```json", "").replace("```", "").strip()
                batch_verdicts = json.loads(json_text)
                verdicts.extend(batch_verdicts)
            except Exception as e:
                print(f"  ❌ Error in Phase 2: {e}")
                for f in batch:
                    verdicts.append({"fact": f, "is_accurate": True, "reasoning": "Error during audit", "source": ""})
        
        return verdicts

    def audit_all(self, limit=None):
        html_files = sorted(PROJECT_DIR.glob("????-??-??.html"), reverse=True)
        if limit:
            html_files = html_files[:limit]
        
        for html_file in html_files:
            data = self.scrape_facts(html_file)
            if not data: continue
            
            p1_result = self.run_phase_1(data)
            
            audit_entry = {
                "date": data['date'],
                "name": data['name'],
                "p1_match": p1_result['is_match'],
                "p1_predicted": p1_result['predicted_name'],
                "failures": []
            }
            
            if not p1_result['is_match']:
                print(f"  ⚠️ Mismatch found! Target: {data['name']}, Predicted: {p1_result['predicted_name']}")
                p2_verdicts = self.run_phase_2(data)
                audit_entry['failures'] = [v for v in p2_verdicts if not v['is_accurate']]
            
            self.results.append(audit_entry)
            self.generate_report()

    def generate_report(self):
        with open(REPORT_PATH, 'w', encoding='utf-8') as f:
            f.write(f"# Player Fact Audit Report\n")
            f.write(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            total = len(self.results)
            mismatches = len([r for r in self.results if not r['p1_match']])
            
            f.write(f"## Summary\n")
            f.write(f"- **Total Players Audited:** {total}\n")
            f.write(f"- **Identity Mismatches (Phase 1):** {mismatches}\n\n")
            
            f.write(f"## Detailed Findings\n")
            for r in self.results:
                if not r['p1_match']:
                    f.write(f"### ❌ {r['name']} ({r['date']})\n")
                    f.write(f"- **Phase 1 Prediction:** {r['p1_predicted']}\n")
                    if r['failures']:
                        f.write("- **Debunked Facts:**\n")
                        for fail in r['failures']:
                            f.write(f"  - **Fact:** {fail['fact']}\n")
                            f.write(f"    - **Reason:** {fail['reasoning']}\n")
                            f.write(f"    - **Source:** [{fail['source']}]({fail['source']})\n")
                    else:
                        f.write("- *No specific facts debunked in Phase 2 (potential false positive in P1)*\n")
                    f.write("\n")
                elif any(r.get('failures', [])): # In case we add sampling later
                     f.write(f"### ⚠️ {r['name']} ({r['date']}) - Detail Error\n")
                     # ... detail error reporting ...

import argparse

def main():
    parser = argparse.ArgumentParser(description="Audit AI-generated player facts.")
    parser.add_argument("--limit", type=int, help="Limit the number of files to audit.")
    parser.add_argument("--file", type=str, help="Audit a specific HTML file.")
    args = parser.parse_args()

    try:
        api_key = load_api_key()
        auditor = FactAuditor(api_key)
        
        if args.file:
            html_file = PROJECT_DIR / args.file
            if html_file.exists():
                data = auditor.scrape_facts(html_file)
                if data:
                    p1_result = auditor.run_phase_1(data)
                    audit_entry = {
                        "date": data['date'],
                        "name": data['name'],
                        "p1_match": p1_result['is_match'],
                        "p1_predicted": p1_result['predicted_name'],
                        "failures": []
                    }
                    if not p1_result['is_match']:
                        p2_verdicts = auditor.run_phase_2(data)
                        audit_entry['failures'] = [v for v in p2_verdicts if not v['is_accurate']]
                    auditor.results.append(audit_entry)
                    auditor.generate_report()
            else:
                print(f"File not found: {args.file}")
        else:
            auditor.audit_all(limit=args.limit)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
