# ABOUTME: Generates grounded trivia facts and Q&A pairs anchored to a player dossier.
# ABOUTME: Uses Gemini 3.1 Flash Lite with a Skeptical Copy Editor persona to ensure accuracy.

import json
import time
from google import genai  # type: ignore
from google.genai import types  # type: ignore

# --- CONFIGURATION ---
MODEL = 'gemini-3.1-flash-lite'

# Rate limiting state
_LAST_GEMINI_CALL_TS = time.time()

def _respect_free_tier_rate_limit():
    """Enforce a conservative delay between Gemini API calls to respect Free Tier limits."""
    global _LAST_GEMINI_CALL_TS
    now = time.time()
    min_interval = 13.0  # seconds
    elapsed = now - _LAST_GEMINI_CALL_TS
    if elapsed < min_interval:
        sleep_for = min_interval - elapsed
        time.sleep(sleep_for)
    _LAST_GEMINI_CALL_TS = time.time()

def get_gemini_client(api_key: str):
    """Returns a Gemini API client instance."""
    return genai.Client(api_key=api_key)

def generate_grounded_trivia(player_dossier, api_key: str):
    """
    Generates trivia facts and Q&A pairs anchored strictly to the provided player dossier.
    
    Args:
        player_dossier (dict): Contains name, career_totals, yearly_war, transactions, awards, bio.
        api_key (str): Gemini API key.
        
    Returns:
        dict: A dictionary containing 'facts', 'qa', and 'claims'.
    """
    _respect_free_tier_rate_limit()
    client = get_gemini_client(api_key)
    
    dossier_json = json.dumps(player_dossier, indent=2)
    
    prompt = f"""
You are a passionate New York Yankees historian and fan. Your goal is to generate engaging, high-impact trivia hints and follow-up "story bites" for the player: {player_dossier.get('name', 'Unknown Player')}.

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
3. **THE HALL OF SHAME (DO NOT DO THESE)**:
   - NEVER mention the "SABR BioProject," "biography status," or "unassigned records."
   - NEVER use "Full Names" or "Birthplace/Birthdate" as a fact or Q&A unless it is truly extraordinary.
   - NEVER say "He was born in [City]" or "His full name is [Name]." This is low-quality filler.
4. Examples of "Good" Q&A anecdotes (What we want):
   - "He was the #1 overall prospect in baseball according to Baseball America."
   - "He was a centerpiece in a blockbuster trade for a future Hall of Famer."
   - "He caught his brother pitching, forming a rare 'brother battery'."
5. You MUST provide exactly 3 question/answer pairs. Focus on weird baseball coincidences, unique family ties, or famous single-game moments.

**TASK 3: ATOMIC CLAIMS (The "claims" list)**
Extract ALL atomic factual statements (specific years, statistics, team names, awards) mentioned in your HINTS and STORY BITES.
- Each claim should be a single, verifiable sentence.

**OUTPUT FORMAT**:
Return ONLY a JSON object:
{{
  "facts": ["hint 1", "hint 2", "hint 3"],
  "qa": [
    {{"question": "...", "answer": "..."}},
    {{"question": "...", "answer": "..."}},
    {{"question": "...", "answer": "..."}}
  ],
  "claims": ["claim 1", "claim 2", ...]
}}
"""


    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1
        )
    )
    
    try:
        return json.loads(response.text)
    except Exception as e:
        print(f"Error parsing Gemini response: {e}")
        print(f"Raw response: {response.text}")
        # Return a fallback structure if parsing fails
        return {
            "facts": [],
            "qa": [],
            "claims": []
        }
