import os
from PIL import Image
import google.generativeai as genai
from pathlib import Path
import json
from bs4 import BeautifulSoup
from datetime import datetime
import re
import subprocess
import sys

# --- Configuration ---
CONFIG_FILE_NAME = ".yankee_generator_config.json"

# --- Helper Functions ---

def get_config_path():
    """Gets the full path to the configuration file in the user's home directory."""
    return Path.home() / CONFIG_FILE_NAME

def load_config():
    """Loads the config file and returns its data, or an empty dict if not found."""
    config_path = get_config_path()
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_config(config_data: dict):
    """Saves the given config data to the file."""
    config_path = get_config_path()
    try:
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
    except IOError as e:
        print(f"⚠️  Warning: Could not save config file to {config_path}. Error: {e}")

def get_player_data_from_image(image_path: Path, api_key: str):
    """
    Analyzes the clue image using the Gemini API to identify the player, facts, and career totals.
    """
    print(f"🤖 Analyzing clue image: {image_path.name}...")
    try:
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        clue_image = Image.open(image_path)
        
        prompt = """
        You are a hyper-literal baseball data analyst with a zero-tolerance policy for errors. Your task is to analyze the provided image of a "Name That Yankee" trivia card and provide results of your analysis.
        
        For ALL retreival and verifiction of WAR as a statistic ONLY use WAR from Baseball Reference (www.baseball-reference.com).  There are other versions of WAR which should not be included in the verification or output.
        
        When you are looking for carreer statistic totals use ALL the following for each player type:
            - for hitters use WAR, G, AB, R, H, 2B, 3B, HR, RBI, SB, BB, SO, AVG, OBP, SLG, OPS, OPS+
            - for pitchers use WAR, W, L, ERA, G, GS, CG, SHO, SV, IP, H, R, ER, BB, SO

        **Primary Directive: 100% Accuracy of facts and statistics is mandatory.**

        1.  **Data Extraction:** Extract the complete list of teams from the provided trivia image with their exact corresponding years. Also, extract every single career statistic shown on the trivia card and its value (e.g., `AVG: .267`, `HITS: 1254`, `W-L: 87-108`, `STARTS: 254`).
        2.  **Initial Player Identification:** Use ALL information extracted in step 1 to find a candidate player. Then, retrieve that candidate player's career statistic totals.  When retrieving the candidate player's carreer statistic totals only use authoritative sources such as Baseball Reference (https://www.baseball-reference.com/) or MLB (https://mlb.com) for these statistics.  Do not use low quality sources such as blogs, social media, or e-commerce web sites
        3.  **Final Verification:** Verify that ALL statistics you extracted from the card in Step 1 equals the official career statistic totals you retrieved.  When doing this verification you should only use authoritative sources such as Baseball Reference (https://www.baseball-reference.com/) or MLB (https://mlb.com) for these statistics.  Do not use low quality sources such as blogs, social media, or e-commerce web sites
            * If any statistic does not match the official record perfectly, the candidate is incorrect. You must discard them and find a new candidate whose data is a perfect match.
        4.  **Identify Player:** Based on the verification you performed in step 3, identify the single correct player.
        5.  **Fact retrieval:** Retrieve exactly 4 facts (no more and no less) relating to the player you identified in step 4 and verified in step 3.  Also retrieve the player's nickname if you can find it.  When retreiving player facts and player nickname only use authoritative sources such as Baseball Reference (https://www.baseball-reference.com/) or MLB (https://mlb.com) for these statistics.  Do not use low quality sources such as blogs, social media, or e-commerce web sites
        6.  **Provide Facts:** Provide four interesting career facts retreived in step 5
        7.  **Provide Career Statistics:** Provide ALL career statistics that were retrieved and verified in steps 2 & 3.  Before providing the statistics, verify that each career statistic is equal to what is noted in the official career stastic total that is recorded in an authoritative source such as Baseball Reference (https://www.baseball-reference.com/) or MLB (https://mlb.com) for these statistics.  Do not use low quality sources such as blogs, social media, or e-commerce web sites to perform this verification.  If you can not verify an individual career statistic, do not estimate it - leave it blank in the output.

        Your response must be a valid JSON object with the following structure, and nothing else:
        {
          "name": "Player's Full Name",
          "nickname": "Player's common nickname, or an empty string",
          "facts": [
            "A fascinating career fact.",
            "Another interesting career fact.",
            "A third unique career fact.",
            "A fourth interesting career fact."
          ],
          "career_totals": {
            // For hitters, include WAR, G, AB, R, H, 2B, 3B, HR, RBI, SB, BB, SO, AVG, OBP, SLG, OPS, OPS+
            // For pitchers, include WAR, W, L, ERA, G, GS, CG, SHO, SV, IP, H, R, ER, BB, SO
            "WAR": "111.1", "AB": "2931", "...": "..."
          }
        }
        """
        
        response = model.generate_content([prompt, clue_image])
        
        json_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        player_data = json.loads(json_text)

        print(f"  ✅ AI analysis complete.")
        return player_data

    except Exception as e:
        print(f"  ❌ Error communicating with Gemini API: {e}")
        return None

def review_and_edit_data(player_data: dict, project_dir: Path) -> dict:
    """
    Displays the AI-generated data to the user for review and allows for manual correction.
    """
    print("\n" + "="*40)
    print("--- Please Review the Following Data ---")
    print(f"Player Name: {player_data.get('name', 'N/A')}")
    print(f"Nickname: {player_data.get('nickname', 'N/A')}")
    print("Facts:")
    for i, fact in enumerate(player_data.get('facts', []), 1):
        print(f"  {i}. {fact}")
    print("Career Totals:")
    print(json.dumps(player_data.get('career_totals', {}), indent=2))
    print("="*40)

    while True:
        is_correct = input("Is all of this information correct? (y/n): ").lower().strip()
        if is_correct in ['y', 'n']:
            break
        print("Invalid input. Please enter 'y' or 'n'.")

    if is_correct == 'y':
        print("✅ Data confirmed.")
        return player_data
    else:
        temp_file_path = project_dir / "temp_player_data_to_edit.json"
        try:
            with open(temp_file_path, 'w') as f:
                json.dump(player_data, f, indent=4)
            
            # Updated instructions for the user
            print(f"\n📝 A temporary file has been created with the data.")
            print(f"   Please open this file in your preferred text editor:")
            print(f"   {temp_file_path}")
            print(f"   Correct any errors, SAVE the file, and then return to this terminal.")

            input("\nPress Enter in this terminal when you are finished editing...")

            with open(temp_file_path, 'r') as f:
                corrected_data = json.load(f)
            
            print("✅ Data updated with your corrections.")
            return corrected_data
        
        except Exception as e:
            print(f"❌ An error occurred during the editing process: {e}")
            return player_data # Return original data on error
        finally:
            # Clean up the temporary file
            if temp_file_path.exists():
                temp_file_path.unlink()


def generate_detail_page(player_data: dict, date_str: str, formatted_date: str, project_dir: Path):
    """Generates and saves the new HTML detail page, now with a career totals table."""
    print(f"  📄 Generating detail page for {date_str}...")
    name = player_data.get('name', 'N/A')
    nickname = player_data.get('nickname', '')
    facts = player_data.get('facts', [])
    career_totals_data = player_data.get('career_totals', {})
    
    display_name = f'{name} "{nickname}"' if nickname else name
    facts_html = "\n".join([f"                        <li>{fact}</li>" for fact in facts])
    
    stats_table_html = ""
    if career_totals_data:
        headers = career_totals_data.keys()
        header_html = "".join([f"<th>{h}</th>" for h in headers])
        row_html = "".join([f"<td>{career_totals_data.get(h, '')}</td>" for h in headers])
        stats_table_html = f"""
        <div class="stats-table-container">
            <h3>Career Totals</h3>
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>{header_html}</tr>
                    </thead>
                    <tbody>
                        <tr>{row_html}</tr>
                    </tbody>
                </table>
            </div>
        </div>
        """

    template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Answer for {date_str} | Name That Yankee</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <h1>The answer for {formatted_date} is...</h1>
    </header>

    <main>
        <a href="index.html" class="back-link">← Back to All Questions</a>

        <div class="detail-layout">
            <div class="player-profile">
                <div class="player-photo">
                    <img src="images/answer-{date_str}.jpg" alt="Photo of {name}">
                </div>
                <div class="player-info">
                    <h2>{display_name}</h2>
                    <h3>Career Highlights & Facts</h3>
                    <ul>
{facts_html}
                    </ul>
                </div>
            </div>
            <div class="original-card">
                <h3>The Original Clue</h3>
                <img src="images/clue-{date_str}.jpg" alt="Original trivia card">
            </div>
        </div>
        {stats_table_html}
    </main>
</body>
</html>"""
    
    file_path = project_dir / f"{date_str}.html"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(template)
    print(f"  ✅ Detail page saved successfully.")

def rebuild_index_page(project_dir: Path):
    """
    Scans the images directory, finds all clues, and rebuilds the entire
    index.html gallery from scratch, sorted by date.
    """
    print("\n✍️ Rebuilding and re-sorting index.html from all available clues...")
    index_path = project_dir / "index.html"
    images_dir = project_dir / "images"
    
    if not index_path.exists():
        print(f"❌ Error: index.html not found at {index_path}. Cannot update.")
        return

    all_clue_files = sorted(images_dir.glob("clue-*.jpg"), reverse=True)
    
    if not all_clue_files:
        print("🤷 No clue images found in the 'images' directory.")
        return

    gallery_tiles = []
    date_pattern = re.compile(r"clue-(\d{4}-\d{2}-\d{2})\.jpg")

    for clue_file in all_clue_files:
        match = date_pattern.search(clue_file.name)
        if match:
            date_str = match.group(1)
            try:
                dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
                formatted_date = dt_obj.strftime("%B %d, %Y")
                
                snippet = f"""<div class="gallery-container">
                <a href="{date_str}.html" class="gallery-item">
                    <img src="images/clue-{date_str}.jpg" alt="Name that Yankee trivia card from {date_str}">
                    <div class="gallery-item-overlay">
                        <span>Click to Reveal</span>
                    </div>
                </a>
                <p class="gallery-date">Trivia Date: {formatted_date}</p>
            </div>"""
                gallery_tiles.append(snippet)
            except ValueError:
                print(f"⚠️  Warning: Skipping file with invalid date format in name: {clue_file.name}")

    with open(index_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    gallery_div = soup.select_one('.gallery')
    if not gallery_div:
        print(f"❌ Could not find insertion point '<div class=\"gallery\">' in index.html.")
        return

    gallery_div.clear()
    
    for tile_html in gallery_tiles:
        tile_soup = BeautifulSoup(tile_html, 'html.parser')
        gallery_div.append(tile_soup)
        gallery_div.append('\n')
    
    footer_p = soup.select_one('footer p')
    if footer_p:
        now = datetime.now()
        footer_p.string = f"Last Updated: {now.strftime('%B %d, %Y')}"
        print("✅ Footer timestamp updated.")

    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
        
    print("✅ index.html rebuilt successfully.")


# --- Main Execution ---
if __name__ == "__main__":
    print("--- Name That Yankee Page Generator (Python Version) ---")
    
    config = load_config()

    # 1. Get project directory
    last_path = config.get("last_project_path")
    prompt_message = "Enter the path to your website project folder"
    if last_path:
        prompt_message += f" [Default: {last_path}]: "
    else:
        prompt_message += ": "

    project_dir_str = input(prompt_message).strip().strip("'\"")
    if not project_dir_str and last_path:
        project_dir_str = last_path
        print(f"Using default path: {project_dir_str}")
    
    project_dir = Path(project_dir_str).resolve()
    if not project_dir.is_dir():
        print(f"❌ Error: Directory not found at '{project_dir}'")
        exit()
    config["last_project_path"] = str(project_dir)

    # 2. Get API Key
    api_key = config.get("api_key")
    if not api_key:
        print("Gemini API key not found.")
        try:
            import getpass
            api_key = getpass.getpass("Please enter your Google AI Studio API key (will be saved for future use): ")
        except ImportError:
            api_key = input("Please enter your Google AI Studio API key (will be saved for future use): ")
    
    if not api_key:
        print("❌ API Key is required to proceed.")
        exit()
    config["api_key"] = api_key

    save_config(config)
    
    images_dir = project_dir / "images"
    images_dir.mkdir(exist_ok=True)

    # 3. Choose mode: Single Date or ALL
    mode = input("Enter a specific date (YYYY-MM-DD) or type 'ALL' to process all clue images: ").strip()

    if mode.upper() == 'ALL':
        clue_files_to_process = sorted(images_dir.glob("clue-*.jpg"), reverse=True)
        if not clue_files_to_process:
            print("🤷 No 'clue-*.jpg' files found in the images directory.")
            exit()
        print(f"\nFound {len(clue_files_to_process)} clue images to process.")

        for clue_path in clue_files_to_process:
            date_match = re.search(r"clue-(\d{4}-\d{2}-\d{2})\.jpg", clue_path.name)
            if not date_match:
                continue
            
            date_str = date_match.group(1)
            dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = dt_obj.strftime("%B %d, %Y")
            
            player_data = get_player_data_from_image(clue_path, api_key)
            if player_data:
                verified_data = review_and_edit_data(player_data, project_dir)
                generate_detail_page(verified_data, date_str, formatted_date, project_dir)
        
        rebuild_index_page(project_dir)

    else: # Single Date Mode
        date_str = mode
        try:
            dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = dt_obj.strftime("%B %d, %Y")
        except ValueError:
            print("❌ Invalid date format. Please use YYYY-MM-DD.")
            exit()
            
        clue_image_path = images_dir / f"clue-{date_str}.jpg"
        
        if not clue_image_path.is_file():
            print(f"❌ Error: Clue image not found at {clue_image_path}")
            exit()

        player_data = get_player_data_from_image(clue_image_path, api_key)
        if player_data:
            verified_data = review_and_edit_data(player_data, project_dir)
            generate_detail_page(verified_data, date_str, formatted_date, project_dir)
            rebuild_index_page(project_dir)
            
    print("\n🎉 All tasks completed successfully! 🎉")
