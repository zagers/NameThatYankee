from google import genai  # type: ignore
from google.genai import types, errors  # type: ignore
from PIL import Image  # type: ignore
import json
import time


# --- CONFIGURATION ---
# The number of times to retry the API call if it returns an empty response.
MAX_RETRIES = 5
SLEEP_TIME = 30
MODEL = 'gemini-3-flash-preview'

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
    current_date = "March 7, 2026"
    generation_config = types.GenerateContentConfig(
        temperature=0.1,
        tools=[types.Tool(
            google_search=types.GoogleSearch()
        )]
    )
    prompt = f"""
    You are a baseball historian and statistical auditor. Analyze the provided image of a "Name That Yankee" trivia card. 
    Accuracy is your only priority. A wrong name is far worse than returning "Unknown".

    **CONTEXT**: The current date is {current_date}. Statistics for the 2024 and 2025 seasons are historical facts and should NOT be treated as futuristic or fictitious.

    Follow these steps precisely:

    1.  **Statistical Extraction**: Transcribe the career stats shown on the card. For each row, list: Year, Team, and the primary stats (e.g., W-L and ERA for pitchers, or HR and AVG for hitters).
    2.  **Targeted Search**: Use your search tool to find the player who recorded these EXACT statistics in these specific years for these teams. 
        *Search Strategy*: Search for the most unique stat line on the card. 
        *Example*: "MLB pitcher [Year] [W-L Record] [ERA]"
    3.  **Rigorous Audit**: Compare your search results against every single row on the card.
    4.  **Final Decision (Ultra-Strict)**: 
        - **Stats Must Match**: The primary statistics (Wins, Losses, ERA, Home Runs, Average) must match the card exactly. 
        - **No Leeway**: Do NOT assume OCR errors. If you cannot find a player whose statistics and team history match every row on the card, you MUST return "Unknown".
        - **Team Sequence**: The chronological order of teams must be identical.

    Your response must be a single valid JSON object with the following structure, and nothing else:
    {{
      "step_by_step_reasoning": {{
        "transcribed_stats": "...",
        "search_query_used": "...",
        "audit_findings": "Detailed comparison of card stats vs search data"
      }},
      "name": "Player's Full Name or 'Unknown'",
      "nickname": "Player's common nickname, or an empty string"
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

            print(f"  ✅ Player identified as: {player_data['name']}")
            if player_data.get('step_by_step_reasoning'):
                findings = player_data['step_by_step_reasoning'].get('audit_findings', 'No findings provided')
                print(f"     AI Reasoning: {findings}")

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
    1. **Orientation:** Reject or downgrade to Priority 3 any image that is in landscape orientation (width > height). The website ONLY supports portrait images.
    2. **Transient Text:** Reject or downgrade to Priority 3 any image that contains "point-in-time" or transient text overlays (e.g., "HE'S BACK", "SIGNED", "BREAKING NEWS").
    3. **Multi-Player/Collages:** Reject or downgrade to Priority 3 any image that shows more than one baseball card or more than one primary player (e.g., a 4-card collage or a group shot). Priority 1 and 2 MUST feature a SINGLE baseball card or a SINGLE player.

    Rate the image based on the following priority levels:

    **Priority 1: Single Portrait Baseball Card in Yankee Uniform**
    - The image is a portrait-oriented physical or digital baseball card featuring ONE player.
    - The player is clearly wearing a New York Yankees uniform.
    - Contains NO transient/event-based text overlays and is NOT a collage of multiple cards.

    **Priority 2: Clean Single Portrait Photo in Yankee Uniform**
    - The image is a clean portrait-oriented action photo or portrait featuring ONE player.
    - The player is clearly wearing a New York Yankees uniform.
    - Contains NO transient/event-based text overlays, intrusive graphics, or multiple players.

    **Priority 3: Any Other Image (Landscape, Collage, Non-Yankee, Ambiguous, or Graphic)**
    - The image shows multiple cards or a collage.
    - OR the image is in landscape orientation.
    - OR the player is NOT in a Yankees uniform.
    - OR the image contains transient text overlays.

    Your response must be a valid JSON object with the following structure, and nothing else:
    {{
      "is_yankee_uniform": true/false,
      "is_baseball_card": true/false,
      "is_portrait": true/false,
      "has_transient_text": true/false,
      "priority_level": 1 | 2 | 3,
      "confidence": "high/medium/low",
      "reasoning": "Brief explanation of your decision"
    }}
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
            is_portrait = data.get('is_portrait', True) # Default to True to allow if not specified
            
            # Additional check based on AI's finding of portrait status
            if not is_portrait:
                priority = 3
                reasoning = f"(AI identified as landscape): {reasoning}"

            if priority > 0 and confidence in ['high', 'medium']:
                print(f"  ✅ Image Rated: Priority {priority} ({confidence} confidence)")
                print(f"     Reasoning: {reasoning}")
                return {"success": True, "priority": priority, "reasoning": reasoning}
            else:
                # If confidence is low, we still treat it as Priority 3 rather than rejecting
                print(f"  ⚠️ Low Confidence Match: Falling back to Priority 3")
                return {"success": True, "priority": 3, "reasoning": f"Low confidence: {reasoning}"}

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