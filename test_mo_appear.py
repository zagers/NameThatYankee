import sys
import os
import json
sys.path.append(os.path.join(os.getcwd(), 'page-generator'))
from scraper import search_and_scrape_player

dossier = search_and_scrape_player("Mariano Rivera", automated=True)
print("Positions:", json.dumps(dossier.get('positions', {}), indent=2))
