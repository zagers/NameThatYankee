# ABOUTME: Evaluation harness for Grounded Enthusiast trivia generation.
# ABOUTME: Validates factual precision and quality criteria across a sample player pool.
import os
import json
import sys
import time
from pathlib import Path
from google import genai
from google.genai import types

# Add page-generator to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config_manager

MODEL = 'gemini-3.1-flash-lite'

ENTHUSIAST_PROMPT_TEMPLATE = """
You are a passionate New York Yankees historian and fan. Your goal is to generate engaging, high-impact trivia hints and follow-up stories for the player: {name}.

**THE SOURCE OF TRUTH (PLAYER DOSSIER)**:
{dossier_json}

**STRICT ACCURACY RULES FOR STATS**:
1. Every statistic, year, and team name MUST match the dossier exactly. Do NOT round numbers.
2. **NO META-COMMENTARY**: Never mention "SABR," "biography," or "database."

**QUIZ CHALLENGE RULES (FOR HINTS)**:
The "Facts" (Hints) are for a quiz where the user sees a visual clue card (which typically shows name, team logo, stats like BA/HR/RBI/ERA/W-L, and a list of teams played for). 
1. **NO SPOILERS**: In the 3 primary "Facts", you MUST NOT mention:
   - The player's name or nicknames.
   - Any team names or city names (e.g., do NOT say "Yankees" or "Detroit").
   - Any specific years (e.g., do NOT say "1995").
   - **NO CARD BACK STATS**: Do NOT include career batting average (BA), total career home runs (HR), total career RBI, or specific win/loss records. 
   - **NO TEAM LISTS**: Do NOT mention how many teams they played for.
2. **CATEGORIZED HINTS**: Pick the 3 BEST hints from these categories:
   - Awards & Honors, Positions & Specialties, Family Relationships, or Notable Achievements.
3. Format: Short, punchy sentences. Use digits for numbers. Do NOT use pronouns ("he", "his").

**FOLLOW-UP RULES (FOR Q&A) - THE "GENERATIVE MEMORY" MANDATE**:
1. The Q&A section appears AFTER the quiz. This is where you tell the BEST stories about the player.
2. **CRITICAL INSTRUCTION**: If the provided dossier bio is thin, boring, or missing, **YOU MUST USE YOUR INTERNAL BASEBALL KNOWLEDGE** to find 3 highly interesting, specific anecdotes.
4. **THE HALL OF BOREDOM (DO NOT DO THESE)**:
   - NEVER use "Full Names" or "Birthplace/Birthdate" as filler unless it is truly extraordinary.
   - NEVER ask generic questions about whether the player played for the Yankees or wore pinstripes. Redundant.
   - NEVER use generic clichés like "played for multiple organizations," "utility player," or "professional journey."
5. Examples of "Good" Q&A anecdotes:
   - "He was the #1 overall prospect in baseball according to Baseball America."
   - "He was a centerpiece in a blockbuster trade for a future Hall of Famer."
   - "He caught his brother pitching, forming a rare 'brother battery'."
5. You MUST provide exactly 3 question/answer pairs. Focus on weird baseball coincidences, unique family ties, or famous single-game moments.

**OUTPUT FORMAT**:
Return ONLY a JSON object:
{{
  "facts": ["hint 1", "hint 2", "hint 3"],
  "qa": [
    {{"question": "...", "answer": "..."}},
    {{"question": "...", "answer": "..."}},
    {{"question": "...", "answer": "..."}}
  ],
  "claims": ["List every atomic claim for verification"]
}}
"""

def run_harness():
    config = config_manager.load_config()
    api_key = config.get("gemini_api_key")
    client = genai.Client(api_key=api_key)
    
    harness_dates = [
        ("1", "2025-07-06", "Darryl Strawberry"),
        ("2", "2026-05-08", "Gary Sheffield"),
        ("3", "2026-05-09", "Willie Randolph"),
        ("4", "2025-06-16", "Austin Romine"),
        ("5", "2025-05-21", "Mike Stanley"),
        ("6", "2026-05-10", "Graeme Lloyd"),
        ("7", "2026-05-13", "Tippy Martinez"),
        ("8", "2026-05-12", "Gary Roenicke"),
        ("9", "2026-05-07", "Andre Robertson"),
        ("10", "2026-05-17", "Marv Throneberry")
    ]
    
    results = []
    dossier_dir = Path("temp/dossiers")
    
    print("🏟️ Starting Grounded Enthusiast Evaluation Loop...\n")
    
    for level, date, name in harness_dates:
        print(f"[{level}/10] Testing {name} ({date})...")
        dossier_path = dossier_dir / f"{date}.json"
        
        with open(dossier_path, 'r', encoding='utf-8') as f:
            dossier = json.load(f)
            
        prompt = ENTHUSIAST_PROMPT_TEMPLATE.format(
            name=name,
            dossier_json=json.dumps(dossier, indent=2)
        )
        
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json"
                )
            )
            
            output = json.loads(response.text)
            results.append({
                "level": level,
                "name": name,
                "date": date,
                "output": output
            })
            time.sleep(2) # Rate limit cushion
        except Exception as e:
            print(f"  ❌ Error for {name}: {e}")
            
    # Save results for presentation
    with open("temp/harness_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\n✅ Evaluation complete. Results saved to temp/harness_results.json")

if __name__ == "__main__":
    run_harness()
