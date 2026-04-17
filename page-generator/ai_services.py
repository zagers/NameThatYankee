# ABOUTME: Integrates with external AI APIs to generate player summaries and hints.
# ABOUTME: Provides natural language clues for trivia puzzles.
from google import genai  # type: ignore
from google.genai import types, errors  # type: ignore
from PIL import Image  # type: ignore
import json
import time


# --- CONFIGURATION ---
# The number of times to retry the API call if it returns an empty response.
MAX_RETRIES = 5
SLEEP_TIME = 30
#MODEL = 'gemini-2.5-flash'
MODEL = 'gemini-3.1-flash-lite-preview'

# Simple in-process rate limiter to respect Free Tier limit
# (5 requests per minute per model). We maintain at most one
# Gemini request every ~13 seconds, which keeps any 60s window
# at <= 5 requests with a conservative buffer.
_LAST_GEMINI_CALL_TS = time.time()  # Initialize to current time, not 0.0


class GeminiDailyQuotaExceeded(Exception):
    """Raised when the Gemini Free Tier daily quota has been exhausted."""
    pass


def _respect_free_tier_rate_limit():
    """Enforce a conservative delay between Gemini API calls.

    This keeps total request rate safely under the Free Tier limit
    of 5 requests per minute by ensuring at least ~13 seconds
    between *any* Gemini requests in this process.
    """
    global _LAST_GEMINI_CALL_TS
    now = time.time()
    min_interval = 13.0  # seconds; conservative vs 12s (60s/5 requests)
    elapsed = now - _LAST_GEMINI_CALL_TS
    if elapsed < min_interval:
        sleep_for = min_interval - elapsed
        print(f"  ⏱ Respecting Gemini Free Tier rate limit, sleeping {sleep_for:.1f}s before next API call...")
        time.sleep(sleep_for)
    else:
        print(f"  ⚡ No rate limit needed, {elapsed:.1f}s since last call")
    _LAST_GEMINI_CALL_TS = time.time()

def get_player_info_from_image(image_path, api_key: str):
    """
    Uses Gemini to get the player's name and nickname from the clue.
    Includes retry logic for empty responses and Chain of Thought reasoning.
    """
    print(f"🤖 Analyzing clue image with Gemini to identify player...")
    
    client = genai.Client(api_key=api_key)
    clue_image = Image.open(image_path)
    from datetime import datetime
    current_date = datetime.now().strftime("%B %d, %Y")
    generation_config = types.GenerateContentConfig(
        temperature=0.1,
        tools=[types.Tool(
            google_search=types.GoogleSearch()
        )],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            disable=False
        )
    )
    prompt = f"""
    You are an expert MLB Statistical Auditor. Your goal is to identify the player on the provided "Name That Yankee" trivia card with 100% accuracy.

    **CONTEXT**: Today is {current_date}. 2024 and 2025 stats are historical facts.
    
    All of the following steps MUST be followed exactly as listed.

    ### STEP 1: DATA EXTRACTION (OCR)
    1.  **Transcribe the Card**: Extract every statistic and team logo as shown on the card.
    2.  **Identify Stat Categories**: Determine what the stat column headers represent (e.g., ERA, HR, W-L, GMS/GS).
    3.  **Team History**: Note the teams that the player played for (based on the logos shown) and the years that the player played for each team (e.g. Mets Logo over the numbers 2024-2025 means the player played for the mets in both 2024 and 2025).

    ### STEP 2: SEARCH STRATEGY
    You MUST find the specific individual Baseball-Reference player profile.
    1.  **Select Anchor Stat**: Choose a high-leverage stat. Favor Batting Average (e.g., .228 AVG) for hitters and ERA (e.g., 3.81 ERA) for pitchers.
    2.  **STRICT RULE**: Do NOT use "Games", "GMS", "Games Started", or "GS" in your search query. These keywords trigger "Team Season" pages which you must avoid.
    3.  **Formulate Query**: Use the site operator, the anchor stat, and the two most recent teams.
    4.  **Year Disambiguation**: Use the most recent year for the current team. For the prior team, use the year PRIOR to the current team's year (e.g., if Current Team is 2025 Yankees and Prior Team is Rays, use 2025 Yankees and 2024 Rays).
    5.  **STRICT PATTERN**: `site:baseball-reference.com/players/ [Anchor Stat] [Recent Team Year] [Recent Team] [Prior Team Year] [Prior Team]`
    6.  **Example**: `site:baseball-reference.com/players/ .228 AVG 2025 Yankees 2024 Rays`
    7.  **Extract Candidates**: List the Names and URLs of the first 3 results.

    ### STEP 3: SEQUENTIAL VERIFICATION (ADVERSARIAL AUDIT)
    You are a skeptic. Your default assumption is that the search engine is giving you the WRONG player.
    Audit the top 3 candidates one-by-one. For each candidate:
    1.  **Identity**: What is the full name of the player?
    2.  **STRICT NON-HALLUCINATION**: Do NOT use your internal knowledge about players. Rely ONLY on verbatim text from the search tool.
    3.  **Snippet Proof**: Quote the exact verbatim text from the search result's snippet that shows their career stats. 
    4.  **Audit Table**: 
        - [Stat Category] | [Card Value] | [Candidate Value in Snippet] | [Match?]
        - **CRITICAL**: If the exact number (e.g., 4.97) is NOT explicitly visible in the snippet for that player, you MUST write "NOT FOUND" in the Candidate Value column and mark Match as "NO". Do NOT 'fill in' stats from memory.
    5.  **Final Decision**: Only if EVERY numeric value matches exactly can you identify the player. It is better to return 'Unknown' than to provide a false positive.
    
    ### OUTPUT FORMAT
    Return ONLY a JSON object:
    {{
      "step_by_step_reasoning": {{
        "extracted_stats": "Markdown table of what you see on the card",
        "search_query_used": "The exact string used for the site: search",
        "top_3_search_results": [
          {{"name": "...", "url": "..."}}
        ],
        "verification_table": "Markdown table with the Snippet Quotes and Card vs Candidate comparisons",
        "final_audit_summary": "Explanation of why the match was accepted or rejected"
      }},
      "name": "Full Player Name or 'Unknown'",
      "nickname": "Player's common nickname, or empty string"
    }}
    """
    for attempt in range(MAX_RETRIES):
        _respect_free_tier_rate_limit()
        response = None
        try:
            response = client.models.generate_content(model=MODEL, contents=[prompt, clue_image], config=generation_config)
            
            # This line will raise ValueError on an empty response
            json_text = (response.text or "").strip().replace("```json", "").replace("```", "").strip()
            
            player_data = json.loads(json_text)

            # Check if player was identified - if not, retry
            # We retry if name is 'Unknown' regardless of whether search returned results.
            # This allows the model to try a different query if the previous results didn't contain a verified match.
            if player_data.get('name') == 'Unknown':
                print(f"  ⚠️ Player not identified. Retrying... (Attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(SLEEP_TIME)
                continue

            print(f"  ✅ Player identified as: {player_data['name']}")
            if player_data.get('step_by_step_reasoning'):
                reasoning = player_data['step_by_step_reasoning']
                stats = reasoning.get('extracted_stats', 'No stats extracted')
                query = reasoning.get('search_query_used', 'No query provided')
                results = reasoning.get('top_3_search_results', 'No results listed')
                audit = reasoning.get('verification_table', 'No table provided')
                summary = reasoning.get('final_audit_summary', 'No summary provided')
                
                print(f"     Extracted Stats:\n{stats}\n")
                print(f"     Search Query:  {query}")
                print(f"     Top Results:   {results}")
                print(f"     Audit Table:\n{audit}")
                print(f"     AI Summary:    {summary}")

            return player_data # Success, exit the function
        except ValueError:
            print(f"  ⚠️ Gemini returned an empty response. Retrying... (Attempt {attempt + 1}/{MAX_RETRIES})")
            if response:
                print(f"     Finish Reason: {response.candidates[0].finish_reason if response.candidates else 'N/A'}")
            time.sleep(SLEEP_TIME)

        except Exception as e:
            # Handle connection-related errors
            error_msg = str(e).lower()
            is_connection_error = any(keyword in error_msg for keyword in [
                'server disconnected', 'connection', 'timeout', 'network'
            ])
            
            if is_connection_error and attempt < MAX_RETRIES - 1:
                print(f"  plug Connection error: {e}. Retrying...")
                time.sleep(SLEEP_TIME)
                continue
            else:
                print(f"  ❌ Error during identification: {e}")
                return None

    return {"name": "Unknown", "nickname": ""}


def get_facts_from_gemini(player_name: str, api_key: str):
    """
    Gets interesting facts for a confirmed player name.
    Includes retry logic for empty responses.
    """
    print(f"🤖 Asking Gemini for interesting facts about {player_name}...")

    client = genai.Client(api_key=api_key)
    generation_config = types.GenerateContentConfig(temperature=0.1)
    prompt = f"""
    Provide three interesting and unique career facts about the baseball player {player_name}.

    **Directives:**
    - Keep each fact to a single, short sentence.
    - Do not use embellishing or subjective language (e.g., "remarkable," "renowned").
    - Focus only on career highlights (e.g., "Was a 3-time batting champion") or unique statistical achievements (e.g., "Is the only player to win a batting title in both the AL & NL").
    - You can also include facts about family relationships (e.g., "Father pitched for the Red Sox from 1992-2000").
    - Do not use the player's name or the pronoun "he" in the output. Just state the fact (e.g. "Was a five-time all-star" not "He was a five-time all-star").
    - If a player has an unremarkable career, just pick 3 stats from his career to highlight (e.g. "Hit 2 home runs in a 9-year MLB career").

    Your response must be a valid JSON object with the following structure, and nothing else:
    {{
      "facts": [
        "Fact 1.",
        "Fact 2.",
        "Fact 3."
      ]
    }}
    """

    for attempt in range(MAX_RETRIES):
        _respect_free_tier_rate_limit()
        response = None
        try:
            response = client.models.generate_content(model=MODEL, contents=prompt, config=generation_config)
            
            # This line will raise ValueError on an empty response
            json_text = (response.text or "").strip().replace("```json", "").replace("```", "").strip()
            fact_data = json.loads(json_text)
            
            print("  ✅ Facts retrieved.")
            return fact_data.get('facts', []) # Success, exit the function
            
        except ValueError:
            print(f"  ⚠️ Gemini returned an empty response. Retrying... (Attempt {attempt + 1}/{MAX_RETRIES})")
            if response:
                print(f"     Finish Reason: {response.candidates[0].finish_reason if response.candidates else 'N/A'}")
            time.sleep(SLEEP_TIME) # Wait before the next attempt

        except Exception as e:
            # For other errors (API key, network, etc.), fail immediately
            print(f"  ❌ Error getting facts from Gemini API: {e}")
            return []

    print(f"  ❌ All {MAX_RETRIES} retry attempts failed.")
    return []


def get_followup_qa_from_gemini(player_name: str, facts, api_key: str):
    """
    Generates three follow-up questions and answers about the player, using
    varied angles:
      a) a career overview question
      b) a Yankees-specific question focused on postseason or team records
      c) a quirky / off-field question when possible; if not, generate
         another Yankees-focused question.
    """
    print(f"🤖 Asking Gemini for follow-up Q&A about {player_name}...")

    client = genai.Client(api_key=api_key)
    generation_config = types.GenerateContentConfig(temperature=0.2)

    facts_list = facts or []
    try:
        facts_json = json.dumps(facts_list)
    except Exception:
        facts_json = "[]"

    prompt = f"""
    You are a precise baseball historian.

    The player is: {player_name}
    Here are AI-generated career facts about this player (they may not be exhaustive):
    {facts_json}

    Task: Create three natural-sounding follow-up questions a fan might ask
    to learn more about this player, and provide concise, factual answers.

    The three questions must follow this pattern:
    1. A career overview / big-picture question about the player's overall
       career impact, style, or accomplishments.
    2. A Yankees-specific question that focuses on postseason performance,
       memorable Yankees moments, or notable records or milestones achieved
       while playing for the New York Yankees (for example, single-season
       records, franchise records, or key playoff performances).
    3. A quirky or off-field question (personality, famous quotes, unusual
       jobs, military service, broadcasting career, or other notable
       non-playing aspects). If there is no reliable quirky/off-field
       angle available, then instead generate a second Yankees-specific
       question following the description in #2.

    Rules for questions:
    - Refer to the player by name (e.g. "Yogi Berra") or as "he" where
      appropriate.
    - Each question should be one clear sentence, written as something a
      fan might click on from a web page.
    - Do not mention that the questions are AI-generated.

    Rules for answers:
    - Keep each answer to 2–4 sentences.
    - Be factual and specific; avoid vague praise like "legendary" unless
      it is historically common language for this player.
    - Focus on historically grounded information: key stats, awards,
      famous moments, quotes, or specific anecdotes.
    - If information is uncertain, omit it rather than guessing.

    Output format:
    You must respond with a single valid JSON object and nothing else,
    with this structure:
    {{
      "qa": [
        {{ "question": "Question 1?", "answer": "Answer 1." }},
        {{ "question": "Question 2?", "answer": "Answer 2." }},
        {{ "question": "Question 3?", "answer": "Answer 3." }}
      ]
    }}
    """

    for attempt in range(MAX_RETRIES):
        _respect_free_tier_rate_limit()
        response = None
        try:
            response = client.models.generate_content(model=MODEL, contents=prompt, config=generation_config)

            json_text = (response.text or "").strip().replace("```json", "").replace("```", "").strip()
            qa_data = json.loads(json_text)

            qa_list = qa_data.get("qa", [])
            if not isinstance(qa_list, list):
                print("  ⚠️ Follow-up QA data was not a list; falling back to empty list.")
                return []

            print("  ✅ Follow-up Q&A retrieved.")
            return qa_list

        except ValueError:
            print(f"  ⚠️ Gemini returned an empty response for follow-up Q&A. Retrying... (Attempt {attempt + 1}/{MAX_RETRIES})")
            if response:
                print(f"     Finish Reason: {response.candidates[0].finish_reason if response.candidates else 'N/A'}")
            time.sleep(SLEEP_TIME)

        except Exception as e:
            print(f"  ⚠️ Error getting follow-up Q&A from Gemini API: {e}. Retrying... (Attempt {attempt + 1}/{MAX_RETRIES})")
            time.sleep(SLEEP_TIME)
            continue

    print(f"  All {MAX_RETRIES} retry attempts for follow-up Q&A failed.")
    return []


def analyze_player_image(image_path, player_name: str, api_key: str) -> dict:
    """
    Uses Gemini to analyze a player image based on prioritized criteria:
    1. Baseball card + Yankee uniform
    2. Any image + Yankee uniform
    3. Any image of the player
    
    Returns a dict with verification results and priority level.
    """
    print(f"🤖 Analyzing image for {player_name} with prioritized criteria...")
    
    client = genai.Client(api_key=api_key)
    
    try:
        verification_image = Image.open(image_path)
    except Exception as e:
        print(f"  ❌ Error opening image for analysis: {e}")
        return {"success": False, "priority": 0, "reasoning": str(e)}
    
    generation_config = types.GenerateContentConfig(temperature=0.1)
    prompt = f"""
    Analyze the provided baseball player image and determine if the player is in a New York Yankees uniform, if the image is a baseball card, and if it is in portrait orientation.
    
    You do NOT need to verify the player's identity; assume the image is of the correct player.
    Focus ONLY on the uniform, the format (card vs photo), the text content, and the orientation.

    **CRITICAL REJECTION CRITERIA:**
    1. **Orientation:** REJECT (Priority 0) any image that is in landscape orientation (width > height). The website ONLY supports portrait images.
    2. **Transient/Event Text:** REJECT (Priority 0) any image that contains "point-in-time" overlays (e.g., "HE'S BACK", "SIGNED") or promotional event text (e.g., "FANATICS FEST", "NATIONAL CONVENTION", "SPECIAL EDITION").
    3. **Autographs:** REJECT (Priority 0) any image that contains a hand-written or printed autograph (player signature) on the card or photo. The image MUST be a clean, unsigned version.
    4. **Multi-Player/Collages:** REJECT (Priority 0) any image that shows more than one baseball card or more than one primary player.
    5. **Non-Rectangular / Perspective:** REJECT (Priority 0) any baseball card that is die-cut, non-rectangular, OR is a photo of a card sitting on a surface/table. The card MUST be the full frame of the image (no visible backgrounds, shadows, or angled perspective). Standard rectangular cards only.
    6. **Holders & Grading:** REJECT (Priority 0) any image that shows a card inside a plastic holder, protector, top-loader, or grading slab (e.g., PSA, Beckett/BGS, SGC).
    7. **Card Backs:** REJECT (Priority 0) any image that shows the BACK of a baseball card (text-heavy, stats-only, or no player photo). Priority 1 MUST be the FRONT of the card showing the player's face.
    8. **Unofficial Uniforms:** REJECT (Priority 0) if the player is in a generic pinstripe jersey without official Yankees branding or if it's a promotional/fantasy jersey.

    Rate the image based on the following priority levels:

    **Priority 1: Front of Single Portrait Rectangular Baseball Card in Official Yankee Uniform**
    - The image is a CLEAN DIGITAL SCAN or FULL-FRAME crop of the FRONT of a portrait-oriented, standard rectangular baseball card featuring ONE player.
    - The player MUST be clearly visible and wearing an OFFICIAL New York Yankees uniform in the photo.
    - Contains NO autographs, NO event/promotional text, NO backgrounds/surfaces, NO plastic holders/slabs, and is NOT a card back or a collage.

    **Priority 2: Clean Single Portrait Photo in Official Yankee Uniform**
    - The image is a clean portrait-oriented action photo or portrait featuring ONE player.
    - The player MUST be clearly visible and wearing an OFFICIAL New York Yankees uniform.
    - Contains NO autographs, NO transient/event-based text, intrusive graphics, or multiple players.

    **Priority 3: Any Other Image (Non-Yankee, Ambiguous, or Graphic)**
    - The player is NOT in an official Yankees uniform.
    - OR the image is otherwise clean but doesn't meet Priority 1 or 2.
    - NOTE: Images meeting ANY Rejection Criteria above MUST be Priority 0, NOT Priority 3.

    Your response must be a valid JSON object with the following structure, and nothing else:
    {{
      "is_yankee_uniform": true/false,
      "is_official_uniform": true/false,
      "is_baseball_card": true/false,
      "is_front_of_card": true/false,
      "is_rectangular": true/false,
      "is_clean_scan": true/false,
      "is_in_holder": true/false,
      "is_autographed": true/false,
      "is_portrait": true/false,
      "is_single_player": true/false,
      "has_transient_text": true/false,
      "priority_level": 0 | 1 | 2 | 3,
      "crop_box": [ymin, xmin, ymax, xmax],
      "confidence": "high/medium/low",
      "reasoning": "Brief explanation of your decision"
    }}

    **CROP BOX INSTRUCTIONS:**
    - If the image shows a single baseball card or player but it is NOT a clean digital scan (e.g., it has a visible background, table, or borders), provide the normalized coordinates [ymin, xmin, ymax, xmax] of the CARD or PLAYER area only. 
    - Coordinates should be integers from 0 to 1000.
    - If the image is already a clean full-frame scan, return [0, 0, 1000, 1000] or null.
    """

    for attempt in range(MAX_RETRIES):
        _respect_free_tier_rate_limit()
        response = None
        try:
            response = client.models.generate_content(model=MODEL, contents=[prompt, verification_image], config=generation_config)
            
            json_text = (response.text or "").strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(json_text)

            priority = data.get('priority_level', 3)
            confidence = data.get('confidence', 'low')
            reasoning = data.get('reasoning', 'No reasoning provided')
            crop_box = data.get('crop_box')
            is_portrait = data.get('is_portrait', True)
            is_single_player = data.get('is_single_player', True)
            is_rectangular = data.get('is_rectangular', True)
            is_clean_scan = data.get('is_clean_scan', True)
            is_in_holder = data.get('is_in_holder', False)
            is_autographed = data.get('is_autographed', False)
            is_front_of_card = data.get('is_front_of_card', True)
            is_official_uniform = data.get('is_official_uniform', True)
            has_transient_text = data.get('has_transient_text', False)
            
            # Smart Crop Logic: If we have a crop box and it's otherwise a good image, 
            # we can potentially promote it even if 'is_clean_scan' is false.
            can_be_fixed_by_crop = crop_box and not is_clean_scan and is_portrait and is_single_player and not is_in_holder and not is_autographed and not has_transient_text
            
            # Strict Enforcement of Rejection Criteria
            if not is_portrait or not is_single_player or not is_rectangular or (not is_clean_scan and not can_be_fixed_by_crop) or is_in_holder or is_autographed or not is_front_of_card or not is_official_uniform or has_transient_text:
                priority = 0
                reasons = []
                if not is_portrait: reasons.append("landscape")
                if not is_single_player: reasons.append("multiple players/collage")
                if not is_rectangular: reasons.append("non-rectangular/perspective")
                if not is_clean_scan and not can_be_fixed_by_crop: reasons.append("not a clean scan")
                if is_in_holder: reasons.append("in holder/slab")
                if is_autographed: reasons.append("autographed")
                if not is_front_of_card: reasons.append("card back")
                if not is_official_uniform: reasons.append("unofficial uniform")
                if has_transient_text: reasons.append("transient/event text")
                reasoning = f"(REJECTED due to {', '.join(reasons)}): {reasoning}"

            # Handle Rejections First
            if priority == 0:
                print(f"  ❌ Image REJECTED: {reasoning}")
                return {"success": True, "priority": 0, "reasoning": reasoning}

            # Handle High/Medium Confidence Priority 1/2
            if priority in [1, 2] and confidence in ['high', 'medium']:
                # If it needs a crop, we'll signal that in the response
                if can_be_fixed_by_crop:
                    print(f"  ✂️ Image can be saved by cropping: {reasoning}")
                    return {"success": True, "priority": priority, "reasoning": reasoning, "crop_box": crop_box}
                
                print(f"  ✅ Image Rated: Priority {priority} ({confidence} confidence)")
                print(f"     Reasoning: {reasoning}")
                return {"success": True, "priority": priority, "reasoning": reasoning}
            else:
                # If confidence is low or it's Priority 3, we treat it as Priority 3 fallback
                msg = "Priority 3" if priority == 3 else f"Low confidence Priority {priority}"
                print(f"  ⚠️ {msg}: Falling back to Priority 3")
                return {"success": True, "priority": 3, "reasoning": f"{msg}: {reasoning}"}

        except Exception as e:
            print(f"  ⚠️ Error during image analysis: {e}. Retrying... (Attempt {attempt + 1}/{MAX_RETRIES})")
            time.sleep(SLEEP_TIME)

    return {"success": False, "priority": 3, "reasoning": "All attempts failed, defaulted to 3"}


def verify_yankee_uniform(image_path, player_name: str, api_key: str) -> bool:
    """
    Backward compatibility wrapper for verify_yankee_uniform.
    """
    result = analyze_player_image(image_path, player_name, api_key)
    return result["success"] and result["priority"] in [1, 2]


def get_facts_and_followup_from_gemini(player_name: str, api_key: str):
    """
    Single-call helper that retrieves both facts and follow-up Q&A
    for a given player using one Gemini text request.

    Returns a dict with structure:
      { "facts": [...], "qa": [ {"question": ..., "answer": ...}, ... ] }
    On failure, returns {"facts": [], "qa": []}.
    """
    print(f" Asking Gemini for facts and follow-up Q&A about {player_name} in a single call...")

    client = genai.Client(api_key=api_key)
    generation_config = types.GenerateContentConfig(temperature=0.15)

    prompt = f"""
    You are a precise baseball historian.

    The player is: {player_name}

    Task:
      1. Provide three interesting, concise career facts about this player.
      2. Provide three follow-up question-and-answer pairs a fan might ask to
         learn more about the player.

    Facts requirements:
      - Each fact must be a single, short sentence.
      - Focus on career highlights, notable awards, unique statistical
        achievements, or family/baseball lineage.
      - Do not use the player's name or pronouns like "he" inside the facts
        themselves; just state the facts.

    Follow-up Q&A requirements:
      - You must return exactly three Q&A pairs in total.
      - The three questions must follow this pattern:
        1) A career overview / big-picture question.
        2) A Yankees-specific question about postseason performance,
           memorable Yankees moments, or notable Yankees records.
        3) A quirky or off-field question (personality, quotes, unusual
           jobs, military service, broadcasting, or similar). If there is no
           reliable quirky/off-field angle, instead provide a second
           Yankees-focused question as described in (2).
      - Each question should be one clear, natural-sounding sentence.
      - Answers should be 2–4 sentences, factual and specific. Avoid vague
        praise; focus on concrete accomplishments, stats, or anecdotes.
      - If information is uncertain, omit it rather than guessing.

    Output format:
      Respond with a single valid JSON object and nothing else, with this
      structure:

      {{
        "facts": [
          "Fact 1.",
          "Fact 2.",
          "Fact 3."
        ],
        "qa": [
          {{ "question": "Question 1?", "answer": "Answer 1." }},
          {{ "question": "Question 2?", "answer": "Answer 2." }},
          {{ "question": "Question 3?", "answer": "Answer 3." }}
        ]
      }}
    """

    for attempt in range(MAX_RETRIES):
        _respect_free_tier_rate_limit()
        response = None
        try:
            response = client.models.generate_content(model=MODEL, contents=prompt, config=generation_config)

            json_text = (response.text or "").strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(json_text)

            facts = data.get("facts", [])
            qa_list = data.get("qa", [])
            if not isinstance(facts, list):
                facts = []
            if not isinstance(qa_list, list):
                qa_list = []

            print("  Facts and follow-up Q&A retrieved in a single call.")
            return {"facts": facts, "qa": qa_list}

        except ValueError:
            print(f"  Gemini returned an empty or malformed response for combined facts/Q&A. Retrying... (Attempt {attempt + 1}/{MAX_RETRIES})")
            if response:
                print(f"     Finish Reason: {response.candidates[0].finish_reason if response.candidates else 'N/A'}")
            time.sleep(SLEEP_TIME)

        except Exception as e:
            # Handle connection-related errors that should be retried
            error_msg = str(e).lower()
            is_connection_error = any(keyword in error_msg for keyword in [
                'server disconnected', 'connection', 'timeout', 'network', 
                'read timeout', 'connection reset'
            ])
            
            if isinstance(e, errors.APIError) and getattr(e, 'code', None) == 429:
                message = str(e)
                # Detect daily quota exhaustion (GenerateRequestsPerDay...)
                if "GenerateRequestsPerDayPerProjectPerModel-FreeTier" in message or "quota_value: 50" in message:
                    print("  ❌ Gemini daily Free Tier quota appears to be exhausted.")
                    raise GeminiDailyQuotaExceeded(message)
                else:
                    print(f"  ⚠️ Gemini API rate limit exceeded (429): {message}. Retrying... (Attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(SLEEP_TIME)
                    continue
            elif is_connection_error and attempt < MAX_RETRIES - 1:
                print(f"  🔌 Connection error from Gemini API: {e}. Retrying... (Attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(SLEEP_TIME)
                continue
            else:
                print(f"  ⚠️ Error getting combined facts and follow-up Q&A from Gemini API: {e}. Retrying... (Attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(SLEEP_TIME)
                continue

    print(f"  All {MAX_RETRIES} retry attempts for combined facts/Q&A failed.")
    return {"facts": [], "qa": []}
