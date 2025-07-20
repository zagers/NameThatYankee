import google.generativeai as genai
from PIL import Image
import json

def get_player_info_from_image(image_path, api_key: str):
    """
    Uses Gemini to get the player's name and nickname from the clue.
    """
    print(f"🤖 Analyzing clue image with Gemini to identify player...")
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-pro')
        clue_image = Image.open(image_path)
        
        generation_config = genai.types.GenerationConfig(temperature=0.2)
        
        prompt = """
        You are a baseball historian. Analyze the provided image of a "Name That Yankee" trivia card. 
        Your only task is to identify the player's name.

        Your response must be a valid JSON object with the following structure, and nothing else:
        {
          "name": "Player's Full Name",
          "nickname": "Player's common nickname, or an empty string"
        }
        """
        
        response = model.generate_content([prompt, clue_image], generation_config=generation_config)
        json_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        player_data = json.loads(json_text)

        print(f"  ✅ Player identified as: {player_data['name']}")
        return player_data

    except Exception as e:
        print(f"  ❌ Error communicating with Gemini API: {e}")
        return None

def get_facts_from_gemini(player_name: str, api_key: str):
    """
    Gets interesting facts for a confirmed player name.
    """
    print(f"🤖 Asking Gemini for interesting facts about {player_name}...")
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        generation_config = genai.types.GenerationConfig(temperature=0.2)
        
        prompt = f"""
        Provide three interesting and unique career facts about the baseball player {player_name}.

        **Directives:**
        - Keep each fact to a single, short sentence.
        - Do not use embellishing or subjective language (e.g., "remarkable," "renowned").
        - Focus only on career highlights (e.g., "Was a 3-time batting champion") or unique statistical achievements (e.g., "He is the only player to win a batting title in both the AL & NL").
        - Also include facts about family relationships ("Father pitched for the Red Sox from 1992-2000")
        - In the output do not use the players name or the pronoun "he". Just state the fact (e.g. "Was a five time all-star" not "He was a five time all star")

        Your response must be a valid JSON object with the following structure, and nothing else:
        {{
          "facts": [
            "Fact 1.",
            "Fact 2.",
            "Fact 3."
          ]
        }}
        """
        response = model.generate_content(prompt, generation_config=generation_config)
        json_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        fact_data = json.loads(json_text)
        print("  ✅ Facts retrieved.")
        return fact_data.get('facts', [])

    except Exception as e:
        print(f"  ❌ Error getting facts from Gemini API: {e}")
        return []
