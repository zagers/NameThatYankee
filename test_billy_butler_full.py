import sys
import os
import json
sys.path.append(os.path.join(os.getcwd(), 'page-generator'))
from scraper import search_and_scrape_player

dossier = search_and_scrape_player("Billy Butler", automated=True)
print(json.dumps(dossier, indent=2))
