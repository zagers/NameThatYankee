import google.generativeai as genai
from PIL import Image
import json
import time

# --- CONFIGURATION ---
# The number of times to retry the API call if it returns an empty response.
MAX_RETRIES = 5
SLEEP_TIME = 30
MODEL = 'gemini-2.5-pro'

def get_player_info_from_image(image_path, api_key: str):
    """
    Uses Gemini to get the player's name and nickname from the clue.
    Includes retry logic for empty responses.
    """
    print(f"🤖 Analyzing clue image with Gemini to identify player...")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL) 
    clue_image = Image.open(image_path)
    generation_config = genai.types.GenerationConfig(temperature=0.1)
    prompt = """
    You are a baseball historian. Analyze the provided image of a "Name That Yankee" trivia card and return the name and nickname of the player whose stats are shown.

    Your only task is to identify the player's name. Accuracy is paramount. Do not guess.

    **Verification Steps:**
    1.  Verify that every single career stat on the card exactly matches the player you identify.
    2.  Verify that the player was on each team listed for the corresponding year.

    **Output Rules:**
    - If, and only if, you can verify a perfect match based on the verification steps, return the player's data.
    - If you cannot find a player who perfectly matches all stats and team history, or if the image is unreadable, **you must** return "Unknown" as the player's name.

    Your response must be a valid JSON object with the following structure, and nothing else:
    {
      "name": "Player's Full Name",
      "nickname": "Player's common nickname, or an empty string"
    }
    """

    for attempt in range(MAX_RETRIES):
        response = None
        try:
            response = model.generate_content([prompt, clue_image], generation_config=generation_config)
            
            # This line will raise ValueError on an empty response
            json_text = response.text.strip().replace("```json", "").replace("```", "").strip()
            player_data = json.loads(json_text)

            print(f"  ✅ Player identified as: {player_data['name']}")
            return player_data # Success, exit the function

        except ValueError:
            print(f"  ⚠️ Gemini returned an empty response. Retrying... (Attempt {attempt + 1}/{MAX_RETRIES})")
            if response:
                print(f"     Finish Reason: {response.candidates[0].finish_reason if response.candidates else 'N/A'}")
            time.sleep(SLEEP_TIME) # Wait before the next attempt

        except Exception as e:
            # For other errors (API key, network, etc.), fail immediately
            print(f"  ❌ An unexpected error occurred: {e}")
            return None

    print(f"  ❌ All {MAX_RETRIES} retry attempts failed.")
    return None


def get_facts_from_gemini(player_name: str, api_key: str):
    """
    Gets interesting facts for a confirmed player name.
    Includes retry logic for empty responses.
    """
    print(f"🤖 Asking Gemini for interesting facts about {player_name}...")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL)
    generation_config = genai.types.GenerationConfig(temperature=0.1)
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
        response = None
        try:
            response = model.generate_content(prompt, generation_config=generation_config)
            
            # This line will raise ValueError on an empty response
            json_text = response.text.strip().replace("```json", "").replace("```", "").strip()
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

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL)
    generation_config = genai.types.GenerationConfig(temperature=0.2)

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
        response = None
        try:
            response = model.generate_content(prompt, generation_config=generation_config)

            json_text = response.text.strip().replace("```json", "").replace("```", "").strip()
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
            print(f"  ❌ Error getting follow-up Q&A from Gemini API: {e}")
            return []

    print(f"  ❌ All {MAX_RETRIES} retry attempts for follow-up Q&A failed.")
    return []