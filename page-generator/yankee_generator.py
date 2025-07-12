import os
from PIL import Image
import google.generativeai as genai
from pathlib import Path
import json
from bs4 import BeautifulSoup
from datetime import datetime

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
    print("🤖 Analyzing clue image with Gemini 2.5 Flash...")
    try:
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        clue_image = Image.open(image_path)
        
        prompt = """
        You are a hyper-literal baseball data analyst. Your task is to analyze the provided image of a "Name That Yankee" trivia card.

        1.  **Data Extraction (Internal Step):** Mentally extract every single statistic (AVG, HITS, HR, etc.) and the complete list of teams with their exact corresponding years.
        2.  **Strict Verification (Internal Step):** Cross-reference this complete and exact data against your knowledge base. The player's career stats must match *exactly*. The player's team history, including the *specific years* for each team, must also match *exactly*. There is no room for "close" or "similar". A mismatch in a single year or a single stat point means the player is incorrect.
        3.  **Identify Player:** Based on this strict, exact match, identify the single player.
        4.  **Provide Facts:** Once the player is correctly identified, provide four interesting career facts.

        Your response must be a valid JSON object with the following structure, and nothing else.
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

        print(f"\n✅ Player identified: {player_data['name']}")
        return player_data

    except Exception as e:
        print(f"❌ Error communicating with Gemini API: {e}")
        return None

def generate_detail_page(player_data: dict, date_str: str, project_dir: Path):
    """Generates and saves the new HTML detail page."""
    print("📄 Generating new detail page...")
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
        <h1>The Answer Is...</h1>
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
    print(f"✅ Detail page saved successfully to: {file_path}")

def update_index_page(date_str: str, formatted_date: str, project_dir: Path):
    """
    Adds the new trivia card to the index.html file, re-sorts all cards,
    and updates the footer with the current timestamp.
    """
    print("✍️ Updating and re-sorting index.html...")
    index_path = project_dir / "index.html"
    
    if not index_path.exists():
        print(f"❌ Error: index.html not found at {index_path}. Cannot update.")
        return
        
    new_snippet = f"""            <!-- Trivia from {formatted_date} -->
            <div class="gallery-container">
                <a href="{date_str}.html" class="gallery-item">
                    <img src="images/clue-{date_str}.jpg" alt="Name that Yankee trivia card from {date_str}">
                    <div class="gallery-item-overlay">
                        <span>Click to Reveal</span>
                    </div>
                </a>
                <p class="gallery-date">Trivia Date: {formatted_date}</p>
            </div>"""
            
    with open(index_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    gallery_div = soup.select_one('.gallery')
    if not gallery_div:
        print(f"❌ Could not find insertion point '<div class=\"gallery\">' in index.html.")
        return

    # Find all existing tiles and remove any that match the new date to avoid duplicates
    existing_tiles = []
    for tile in gallery_div.select('.gallery-container'):
        href = tile.find('a')['href']
        if f"{date_str}.html" not in href:
            existing_tiles.append(tile)
        else:
            print(f"ℹ️ Found and removed existing entry for {date_str} to prevent duplication.")

    # Add the new tile
    new_tile_soup = BeautifulSoup(new_snippet, 'html.parser')
    existing_tiles.append(new_tile_soup.div)
    
    # Sort tiles by date (descending) based on the href attribute
    def sort_key(tag):
        # Extracts 'YYYY-MM-DD' from 'YYYY-MM-DD.html'
        return tag.find('a')['href']

    sorted_tiles = sorted(existing_tiles, key=sort_key, reverse=True)
    
    # Clear the gallery and append the sorted tiles
    gallery_div.clear()
    for tile in sorted_tiles:
        gallery_div.append(tile)
        gallery_div.append('\n') # Add a newline for readability in the source

    # Update the footer timestamp
    footer_p = soup.select_one('footer p')
    if footer_p:
        now = datetime.now()
        footer_p.string = f"Last Updated: {now.strftime('%B %d, %Y')}"
        print("✅ Footer timestamp updated.")
    else:
        print("⚠️  Warning: Could not find footer paragraph tag to update.")

    # Write the updated and sorted content back to the file
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
        
    print("✅ index.html updated and sorted successfully.")


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

    # 3. Get date and format it
    date_str = input("Enter the trivia date (YYYY-MM-DD): ")
    try:
        dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = dt_obj.strftime("%B %d, %Y")
    except ValueError:
        print("❌ Invalid date format. Please use YYYY-MM-DD.")
        exit()
        
    # 4. Construct and verify the required clue image path
    images_dir = project_dir / "images"
    images_dir.mkdir(exist_ok=True) # Ensure images directory exists
    
    clue_image_path = images_dir / f"clue-{date_str}.jpg"
    
    if not clue_image_path.is_file():
        print(f"❌ Error: Clue image not found.")
        print(f"    Please make sure the file exists at this exact path: {clue_image_path}")
        exit()

    # 5. Process
    player_data = get_player_data_from_image(clue_image_path, api_key)
    if player_data:
        # Remind the user to get the answer image
        print(f"\nℹ️  ACTION REQUIRED: Please find an image for this player and save it as:")
        print(f"    images/answer-{date_str}.jpg\n")

        # Generate HTML files
        generate_detail_page(player_data, date_str, project_dir)
        update_index_page(date_str, formatted_date, project_dir)
        
        print("\n🎉 All tasks completed successfully! 🎉")
