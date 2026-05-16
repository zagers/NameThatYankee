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
You are a "Skeptical Storyteller" tasked with generating high-accuracy, engaging trivia for a New York Yankees trivia game.
Your goal is to generate trivia "hints" and follow-up "story bites" about the player: {player_dossier.get('name', 'Unknown Player')}.

**PLAYER DOSSIER**:
{dossier_json}

**STRICT RULES**:
1. **NO NAME IN HINTS**: You MUST NEVER use the player's name ({player_dossier.get('name')}) or his nickname in the hints. Refer to him as "this player", "the reliever", etc.
2. **AVOID GIF REPETITION**: The user can already see the player's team list and years (e.g. "NYY 1974-1976") in a GIF. DO NOT simply repeat his tenure or team sequence in the hints.
3. **STORY-DRIVEN**: Use the SABR biography to find interesting anecdotes, weird circumstances, or defining moments.
4. **STRICT GROUNDING**: ONLY use info in the dossier. If you include a year or stat, it must be verbatim from the dossier.

**TASK 1: HINTS (The "facts" list)**
Generate exactly 3 trivia hints. These should be progressively easier. 
- Hint 1: An obscure or early career detail (e.g. college, draft, or a weird minor league story).
- Hint 2: A notable milestone, award, or unique narrative detail (e.g. a specific record or a famous play).
- Hint 3: A career-defining achievement or reputation-based fact (e.g. "Led the league in X", "World Series heroics", or "Known for his devastating curveball").
- **IMPORTANT**: Avoid just saying "He played for the Yankees from X to Y". The user already knows that!

**TASK 2: STORY BITES (The "qa" list)**
Generate exactly 3 Q&A pairs that provide more depth for users who want to "find out more."
- These should reveal interesting narrative arcs.
- The answers should be 1-3 sentences and feel like a story.

**TASK 3: ATOMIC CLAIMS (The "claims" list)**
Extract ALL atomic factual statements (specific years, statistics, team names, awards) mentioned in your HINTS and STORY BITES.
- Each claim should be a single, verifiable sentence.
- Example: "He won the Cy Young Award in 1978."
- Example: "He played for the Yankees from 1974 to 1976."

**OUTPUT FORMAT**:
Return ONLY a JSON object with the following structure:
{{
  "facts": ["hint 1", "hint 2", "hint 3"],
  "qa": [
    {{"question": "How did he...", "answer": "The player..."}},
    {{"question": "What happened...", "answer": "In 1974..."}},
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
