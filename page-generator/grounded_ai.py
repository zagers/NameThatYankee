# ABOUTME: Generates grounded trivia facts and Q&A pairs anchored to a player dossier.
# ABOUTME: Uses Gemini 3.1 Flash Lite with a Skeptical Copy Editor persona to ensure accuracy.

import json
import time
import re
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

def contains_spoiler(result, name):
    """Checks if the player name or nicknames appear in the hints."""
    facts = result.get("facts", [])
    # Case insensitive search for the name parts
    name_parts = [p.lower() for p in name.split() if len(p) > 2]
    for fact in facts:
        for part in name_parts:
            if part in fact.lower():
                return True
    return False

def contains_hall_of_shame(result):
    """Checks for low-quality filler and meta-commentary."""
    facts = result.get("facts", [])
    qa = result.get("qa", [])
    all_text = " ".join(facts) + " " + " ".join([q.get('question', '') + " " + q.get('answer', '') for q in qa])
    all_text = all_text.lower()
    
    forbidden = [
        "sabr", "bioproject", "biography remains", "unassigned",
        "born on", "birthplace", "full name is", "middle name",
        "official record", "database"
    ]
    
    for word in forbidden:
        if word in all_text:
            return True, word
    return False, None

def contains_generic_questions(result):
    """Checks for generic or trivial questions about playing for the Yankees."""
    qa = result.get("qa", [])
    for item in qa:
        q_lower = item.get("question", "").lower()
        # Look for questions asking if they played for the Yankees/New York/Bronx or wore pinstripes
        forbidden_patterns = [
            r"\bdid he (ever )?play for the (new york )?yankees?\b",
            r"\bdid he (ever )?wear the pinstripes\b",
            r"\bdid he (ever )?play in the bronx\b",
            r"\bdid he (ever )?play in new york\b",
            r"\bwas he a (member of the )?yankees?\b",
            r"\bdid he play for new york\b",
            r"\bdid he play for the yankees?\b"
        ]
        for pattern in forbidden_patterns:
            if re.search(pattern, q_lower):
                return True, item.get("question")
    return False, None

def is_invalid_hint(fact: str, player_name: str) -> bool:
    """
    Returns True if a quiz hint contains spoilers, years, geographical locations,
    team names, or team/stint count indicators.
    """
    fact_lower = fact.lower()
    
    # 1. Check for player name or parts of the player name (excluding short initials)
    name_parts = [p.lower() for p in player_name.split() if len(p) > 2]
    for part in name_parts:
        if part in fact_lower:
            return True
            
    # 2. Check for years (any 4-digit number starting with 19 or 20)
    if re.search(r'\b(?:19|20)\d{2}\b', fact):
        return True
        
    # 3. Check for geographical or team name references, or pinstripes
    forbidden_words = [
        "yankee", "bronx", "new york", "pinstripe", "brooklyn", "queens", "manhattan",
        "red sox", "boston", "dodger", "mets", "kansas city", "royals", "oakland",
        "athletics", "colorado", "rockies", "tampa bay", "devil rays", "brewers",
        "milwaukee", "angels", "anaheim", "baltimore", "orioles", "phillies",
        "philadelphia", "toronto", "blue jays", "cleveland", "indians", "atlanta",
        "braves", "chicago", "cubs", "white sox", "cincinnati", "reds", "detroit",
        "tigers", "houston", "astros", "miami", "marlins", "minnesota", "twins",
        "pittsburgh", "pirates", "san diego", "padres", "san francisco", "giants",
        "seattle", "mariners", "st. louis", "cardinals", "texas", "rangers", "washington",
        "nationals", "montreal", "expos", "arizona", "diamondbacks", "california"
    ]
    for word in forbidden_words:
        if word in fact_lower:
            return True
            
    # 4. Check for team counts or stint counts
    stint_patterns = [
        r'\b\d+\s+different\b',
        r'\bplayed\s+for\s+\d+\b',
        r'\b\d+\s+franchises\b',
        r'\b\d+\s+teams\b',
        r'\b\d+\s+organizations\b',
        r'\bstint\b',
        r'\bstints\b'
    ]
    for pattern in stint_patterns:
        if re.search(pattern, fact_lower):
            return True
            
    return False

def generate_grounded_trivia(player_dossier, api_key: str):
    """
    Generates trivia facts and Q&A pairs anchored strictly to the provided player dossier.
    Includes a quality guard that forces retries on spoilers or low-quality filler.
    """
    _respect_free_tier_rate_limit()
    client = get_gemini_client(api_key)
    
    player_name = player_dossier.get('name', 'Unknown Player')
    dossier_json = json.dumps(player_dossier, indent=2)
    
    prompt = f"""
You are a passionate New York Yankees historian and fan. Your goal is to generate engaging, high-impact trivia hints and follow-up stories for the player: {player_name}.

**THE SOURCE OF TRUTH (PLAYER DOSSIER)**:
{dossier_json}

**GLOBAL RULES (APPLIES TO BOTH HINTS AND Q&A)**:
1. Every statistic, year, and team name MUST match the dossier exactly. Do NOT round numbers.
2. **NO META-COMMENTARY**: Never mention "SABR," "biography," or "database."
3. **NO REDUNDANT STATS**: DO NOT repeat basic career totals that are already visible in the UI's stats table. Specifically, DO NOT mention:
   * Career WAR, Wins (W), Losses (L), ERA, Games Played (G), Games Started (GS), Saves (SV), Innings Pitched (IP), Strikeouts (SO), or WHIP.
   * Career Batting Average (BA), Home Runs (HR), or RBI.
4. **PRIORITIZE NARRATIVE OVER STATS**: Interesting anecdotes, awards, trades, and family ties are ALWAYS better than numbers.

**TASK 1: QUIZ HINTS (The "facts" list)**:
The "Facts" (Hints) are for a quiz where the user has not yet identified the player.
1. **STRICT SPOILER BAN**: You MUST NOT mention:
   - The player's name or nicknames.
   - Any team names or city/geographical names (e.g., do NOT say "Yankees", "Detroit", "Bronx", "New York", "Boston", etc.).
   - Any specific years or decades (e.g., do NOT say "1995" or "the 90s").
2. **STYLE**: Use vague but descriptive terms like "the club," "the organization," "his draft team," etc.
3. **HIGH-IMPACT STORIES**: If the player was involved in a major trade for a famous Hall of Famer or legendary player, you SHOULD mention it using descriptive terms (e.g., "Was a key piece in a blockbuster trade for a legendary base-stealing Hall of Famer").
4. **NEGATIVE EXAMPLES (DO NOT SAY THESE)**:
   * "Recorded 155 saves." (Redundant - in table).
   * "Played for 9 different franchises." (Boring filler).
   * "Traded to the Oakland Athletics." (Spoiler - mentions team name).

**TASK 2: FOLLOW-UP STORIES (The "qa" list)**:
The Q&A section appears AFTER the quiz is revealed. This is where you tell the BEST stories.
1. **MAXIMUM DETAIL MANDATE**: Unlike the hints, the Q&A **MUST** include specific details:
   - Use the **Player's Name**.
   - Use **Specific Team Names** (e.g., "The Kansas City Royals," "The New York Yankees," etc.).
   - Use **Specific Years** (e.g., "In the 1988 postseason," "During the 1984 trade").
2. **NO REDUNDANCY**: The Q&A MUST NOT repeat or rephrase any facts mentioned in your 3 primary Hints.
3. **RESEARCH MANDATE**: If the provided dossier bio is thin, boring, or missing, **YOU MUST USE YOUR INTERNAL BASEBALL KNOWLEDGE** to find 3 highly interesting, specific anecdotes.
4. **THE HALL OF SHAME (DO NOT DO THESE)**:
   - NEVER use "Full Names" or "Birthplace/Birthdate" as filler unless it is truly extraordinary.
   - NEVER ask generic questions about whether the player played for the Yankees or wore pinstripes. Redundant.
5. Examples of "Good" Q&A anecdotes:
   - "Jay Howell was a centerpiece in the 1984 trade that brought Rickey Henderson to the Yankees."
   - "He was ejected from a 1988 NLCS game against the Mets after umpire Joe West found pine tar on his glove."
6. Format: Exactly 3 question/answer pairs. Focus on weird baseball coincidences, unique family ties, or famous single-game moments.

**TASK 3: ATOMIC CLAIMS (The "claims" list)**
Extract ALL atomic factual statements (specific years, statistics, team names, awards) mentioned in your HINTS and FOLLOW-UP STORIES.
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

    max_attempts = 5
    for attempt in range(max_attempts):
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
        )
        
        try:
            result = json.loads(response.text)
            
            # QUALITY GUARD
            if contains_spoiler(result, player_name):
                print(f"  ⚠️ Quality Guard REJECTED attempt {attempt+1}: Name found in hints.")
                continue
                
            has_junk, word = contains_hall_of_shame(result)
            if has_junk:
                print(f"  ⚠️ Quality Guard REJECTED attempt {attempt+1}: Hall of Shame filler detected ('{word}').")
                continue
                
            has_generic_q, q_text = contains_generic_questions(result)
            if has_generic_q:
                print(f"  ⚠️ Quality Guard REJECTED attempt {attempt+1}: Generic/redundant question detected: '{q_text}'")
                continue
                
            invalid_fact = False
            for fact in result.get("facts", []):
                if is_invalid_hint(fact, player_name):
                    print(f"  ⚠️ Quality Guard REJECTED attempt {attempt+1}: Invalid hint detected: '{fact}'")
                    invalid_fact = True
                    break
            if invalid_fact:
                continue
                
            return result
            
        except Exception as e:
            print(f"Error parsing Gemini response: {e}")
            
    # Fallback if all attempts fail
    return {"facts": [], "qa": [], "claims": []}
