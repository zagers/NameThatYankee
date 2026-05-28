import sys
import os
import json
sys.path.append(os.path.join(os.getcwd(), 'page-generator'))
from grounded_ai import generate_grounded_trivia
from scraper import search_and_scrape_player
from config_manager import load_config

config = load_config()
api_key = config.get("gemini_api_key")
dossier = search_and_scrape_player("Billy Butler", automated=True)
res = generate_grounded_trivia(dossier, api_key)
print(json.dumps(res, indent=2))
