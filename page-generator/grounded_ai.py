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
You are a "Skeptical Copy Editor" tasked with generating high-accuracy trivia for a New York Yankees trivia game.
Your goal is to generate facts and Q&A pairs about the player: {player_dossier.get('name', 'Unknown Player')}.

**PLAYER DOSSIER**:
{dossier_json}

**STRICT RULES**:
1. ONLY use information provided in the dossier above.
2. If the dossier is missing information needed for a common trivia point, DO NOT use your internal knowledge. Skip it.
3. FORBIDDEN: Do not mention any stats, teams, or awards not explicitly listed in the dossier.
4. Accuracy is paramount. Assume any information NOT in the dossier is false for the purposes of this task.

**TASK**:
Generate exactly 3 trivia facts (strings) and exactly 3 Q&A pairs (objects with 'question' and 'answer').
Also, provide a 'claims' list which is a comprehensive list of every factual claim made in the facts and Q&A pairs.

**OUTPUT FORMAT**:
Return ONLY a JSON object with the following structure:
{{
  "facts": ["fact 1", "fact 2", "fact 3"],
  "qa": [
    {{"question": "q1", "answer": "a1"}},
    {{"question": "q2", "answer": "a2"}},
    {{"question": "q3", "answer": "a3"}}
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
