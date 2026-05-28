import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'page-generator'))
from scraper import search_and_scrape_player

dossier = search_and_scrape_player("Derek Jeter", automated=True)
print("Positions:", dossier.get('positions', {}))
