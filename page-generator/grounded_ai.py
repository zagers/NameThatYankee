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
        r'\bstints\b',
        r'\bfranchise\b',
        r'\bfranchises\b',
        r'\borganization\b',
        r'\borganizations\b'
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
You are a passionate New York Yankees historian and fan. Your goal is to generate engaging, high-impact trivia hints and follow-up "story bites" for the player: {player_name}.

**THE SOURCE OF TRUTH (PLAYER DOSSIER)**:
{dossier_json}

**STRICT ACCURACY RULES FOR STATS**:
1. Every statistic, year, and team name MUST match the dossier exactly. Do NOT round numbers.
2. **NO META-COMMENTARY**: Never mention "SABR," "biography," or "database."
3. **DO NOT HALLUCINATE OR INVENT STORIES**: All follow-up Q&A stories MUST be factually correct and fully grounded in real historical baseball records or the dossier. Never claim a player had multiple stints with an organization if they did not.

**QUIZ CHALLENGE RULES (FOR HINTS)**:
The "Facts" (Hints) are for a quiz where the user sees a visual clue card (which typically shows name, team logo, stats like BA/HR/RBI/ERA/W-L, and a list of teams played for). 
1. **NO SPOILERS**: In the 3 primary "Facts" (Hints), you MUST NOT mention:
   - The player's name or nicknames.
   - Any team names or city/geographical names (e.g., do NOT say "Yankees", "Detroit", "Bronx", "New York", "Boston", etc.).
   - Any specific years or decades (e.g., do NOT say "1995" or "the 90s").
   - **NO CARD BACK STATS**: Do NOT include career batting average (BA), total career home runs (HR), total career RBI, or specific win/loss records. 
   - **NO TEAM, FRANCHISE, OR STINT LISTINGS/COUNTS**: Do NOT count, mention, or list how many teams, organizations, franchises, or stints the player had. Do NOT use the words "stint", "organization", "franchise", "different teams", etc.
   - **NEGATIVE EXAMPLES (DO NOT SAY THESE)**:
     * "Served as a journeyman catcher for 11 different major league organizations."
     * "Played for 9 different franchises over a 12-year career."
     * "Had two separate stints with the Bronx organization."
     * "Wore the pinstripes during a division-winning season."
2. **CATEGORIZED HINTS**: Pick the 3 BEST hints from these categories:
   - Awards & Honors, Positions & Specialties, Family Relationships, or Notable Achievements (e.g., striking out a specific famous player, unique rule situation, signature look/style like a thick handlebar mustache).
3. Format: Short, punchy sentences. Use digits for numbers. Do NOT use pronouns ("he", "his").

**FOLLOW-UP RULES (FOR Q&A) - THE "GENERATIVE MEMORY" MANDATE**:
1. The Q&A section appears AFTER the quiz. This is where you tell the BEST stories about the player.
2. **CRITICAL INSTRUCTION**: If the provided dossier bio is thin, boring, or missing, **YOU MUST USE YOUR INTERNAL BASEBALL KNOWLEDGE** to find 3 highly interesting, specific anecdotes.
3. **THE HALL OF SHAME (DO NOT DO THESE)**:
   - NEVER mention the "SABR BioProject," "biography status," or "unassigned records."
   - NEVER use "Full Names" or "Birthplace/Birthdate" as a fact or Q&A unless it is truly extraordinary.
   - NEVER say "He was born in [City]" or "His full name is [Name]." This is low-quality filler.
   - NEVER invent false or unverified rumors (e.g. do NOT say Sal Fasano had two separate stints with the Yankees; he had exactly one stint).
   - NEVER ask generic questions about whether the player played for the Yankees, wore the pinstripes, or played in New York/Bronx (e.g., "Did he ever play for the New York Yankees?" or "Did he wear the pinstripes?"). Since ALL players in this quiz are former Yankees, these questions are redundant, uninteresting, and lack trivia value.
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
