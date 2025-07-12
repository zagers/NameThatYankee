import os
from PIL import Image
import google.generativeai as genai
from pathlib import Path
import json
from bs4 import BeautifulSoup
from datetime import datetime
import re

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
    Analyzes the clue image using the Gemini API to identify the player and facts.
    """
    print(f"🤖 Analyzing clue image: {image_path.name}...")
    try:
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        clue_image = Image.open(image_path)
        
        # Final, zero-tolerance prompt to maximize accuracy.
        prompt = """
        You are a hyper-literal baseball data analyst with a zero-tolerance policy for errors. Your task is to analyze the provided image of a "Name That Yankee" trivia card.

        **Primary Directive: 100% Accuracy is Mandatory.**

        1.  **Data Extraction:** Meticulously extract every single statistic and the complete list of teams with their exact corresponding years from the image.
        2.  **Zero-Tolerance Verification:** Cross-reference the extracted data against your knowledge base. The player's career stats must match perfectly. The player's team history, including the specific years for each team, must also match perfectly.
        3.  **Crucial Rule:** If a player's data is merely "close" or "similar" but not a 100% perfect match to all data points on the card, you must discard that player and continue searching. Do not guess based on prominence or fame. The data is the only truth.
        4.  **Identify Player:** Based on this strict, exact match, identify the single correct player.
        5.  **Provide Facts:** Once the player is correctly identified, provide four interesting career facts.

        Your response must be a valid JSON object with the following structure, and nothing else:
        {
          "name": "Player's Full Name",
          "nickname": "Player's common nickname, or an empty string if they don't have one",
          "facts": [
            "A fascinating career fact not related to the stats or teams on the card.",
            "Another interesting career fact.",
            "A third unique career fact, like draft info, a famous trade, or post-career activity.",
            "A fourth interesting fact."
          ]
        }
        """
        
        response = model.generate_content([prompt, clue_image])
        
        json_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        player_data = json.loads(json_text)

        print(f"  ✅ Player identified: {player_data['name']}")
        return player_data

    except Exception as e:
        print(f"  ❌ Error communicating with Gemini API: {e}")
        return None

def generate_detail_page(player_data: dict, date_str: str, formatted_date: str, project_dir: Path):
    """Generates and saves the new HTML detail page."""
    print(f"  📄 Generating detail page for {date_str}...")
    name = player_data['name']
    nickname = player_data['nickname']
    facts = player_data['facts']
    
    display_name = f'{name} "{nickname}"' if nickname else name
    facts_html = "\n".join([f"                        <li>{fact}</li>" for fact in facts])
    
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
            <!-- Main Content: Player Profile -->
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

            <!-- Sidebar Content: Original Clue -->
            <div class="original-card">
                <h3>The Original Clue</h3>
                <img src="images/clue-{date_str}.jpg" alt="Original trivia card">
            </div>
        </div>
    </main>

    <!-- Footer has been removed as requested -->
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

    # Clear the gallery completely
    gallery_div.clear()
    
    # Loop through the HTML snippets, parse each one, and append it as a proper tag
    for tile_html in gallery_tiles:
        tile_soup = BeautifulSoup(tile_html, 'html.parser')
        gallery_div.append(tile_soup)
        gallery_div.append('\n') # Add a newline for readability in the source
    
    # Update the footer timestamp
    footer_p = soup.select_one('footer p')
    if footer_p:
        now = datetime.now()
        footer_p.string = f"Last Updated: {now.strftime('%B %d, %Y')}"
        print("✅ Footer timestamp updated.")

    # Write the updated and sorted content back to the file
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

    # Save the updated config now
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
        print(f"Found {len(clue_files_to_process)} clue images to process.")

        for clue_path in clue_files_to_process:
            date_match = re.search(r"clue-(\d{4}-\d{2}-\d{2})\.jpg", clue_path.name)
            if not date_match:
                continue
            
            date_str = date_match.group(1)
            
            dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = dt_obj.strftime("%B %d, %Y")
            
            player_data = get_player_data_from_image(clue_path, api_key)
            if player_data:
                # Remind user to get answer image if it doesn't exist
                answer_path = images_dir / f"answer-{date_str}.jpg"
                if not answer_path.is_file():
                    print(f"  ℹ️  ACTION REQUIRED: Please find an image for {player_data['name']} and save it as:")
                    print(f"      images/answer-{date_str}.jpg\n")
                
                generate_detail_page(player_data, date_str, formatted_date, project_dir)
        
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
            print(f"\nℹ️  ACTION REQUIRED: Please find an image for this player and save it as:")
            print(f"    images/answer-{date_str}.jpg\n")

            generate_detail_page(player_data, date_str, formatted_date, project_dir)
            rebuild_index_page(project_dir) # Rebuild index even for single to ensure sorting
            
    print("\n🎉 All tasks completed successfully! 🎉")
