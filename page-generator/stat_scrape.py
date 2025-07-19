import requests
from bs4 import BeautifulSoup, Comment # Import Comment
import os
import urllib.parse
import time
import json # Import the json library
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

def parse_stats_from_html(page_source):
    """
    Parses the HTML source of a player page to find the 'stats_pullout' div
    and extracts only the career stats.
    """
    stats_dict = {}
    soup = BeautifulSoup(page_source, 'html.parser')

    # Target the 'stats_pullout' div
    stats_pullout = soup.find('div', class_='stats_pullout')
    
    if not stats_pullout:
        print("Could not find the 'stats_pullout' div.")
        return None

    # --- NEW LOGIC for Active vs. Retired Players ---
    # First, find the header div that contains the labels (e.g., "2025", "Career")
    header_div = stats_pullout.find('div')
    if not header_div:
        print("Could not find header div in stats_pullout.")
        return None

    # Find all the labels (like '2025', 'Career')
    labels = [p.get_text(strip=True) for p in header_div.find_all('p')]
    
    # Determine the index of the 'Career' stats row
    try:
        career_stats_index = labels.index('Career')
    except ValueError:
        print("Could not find 'Career' label in the stats summary.")
        return None

    # Find all the individual stat divs inside the pullout
    stat_divs = stats_pullout.find_all('div', class_=['p1', 'p2', 'p3'])
    
    if not stat_divs:
        print("Could not find stat divs (p1, p2, p3) inside the pullout.")
        return None

    # Iterate through the stat groups (p1, p2, etc.)
    for group in stat_divs:
        # Iterate through each individual stat container in the group
        for stat_container in group.find_all('div'):
            stat_name_tag = stat_container.find('span')
            # Find ALL stat values for this category
            stat_value_tags = stat_container.find_all('p')

            # Ensure the name tag exists and there are enough value tags
            if stat_name_tag and len(stat_value_tags) > career_stats_index:
                stat_name = stat_name_tag.get_text(strip=True)
                # Select the correct value using the career_stats_index
                stat_value = stat_value_tags[career_stats_index].get_text(strip=True)
                stats_dict[stat_name] = stat_value
    
    return stats_dict

def search_and_scrape_player(player_name):
    """
    Opens a single browser session to find a player's page, handles choices,
    navigates to the correct page, and scrapes the stats.
    """
    # Initialize the Chrome driver
    service = Service()
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new")
    
    # Change the page load strategy to prevent hanging
    options.page_load_strategy = 'eager'
    
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Format the search query for the URL
        search_query = urllib.parse.quote_plus(player_name)
        search_url = f"https://www.baseball-reference.com/search/search.fcgi?search={search_query}"
        
        print(f"Searching for '{player_name}' at: {search_url}")
        driver.get(search_url)
        time.sleep(2)

        player_url_to_scrape = None

        # First, determine the final URL we need to be on.
        if "/players/" in driver.current_url:
            print("Direct match found!")
            player_url_to_scrape = driver.current_url
        else:
            # If not a direct redirect, parse the search results page
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            major_leagues_header = soup.find('h3', string=lambda text: text and "major leagues" in text.lower())
            
            major_league_players = []
            if major_leagues_header:
                for sibling in major_leagues_header.find_next_siblings():
                    if sibling.name == 'div' and 'search-item' in sibling.get('class', []):
                        major_league_players.append(sibling)
                    if sibling.name == 'h3':
                        break
            else:
                major_league_players = soup.find_all('div', class_='search-item')

            if not major_league_players:
                print("No matching player links found on the search page.")
                return None

            if len(major_league_players) == 1:
                print("Found a single Major League player match.")
                link = major_league_players[0].find('a')
                player_url_to_scrape = f"https://www.baseball-reference.com{link['href']}"
            else:
                # Fallback to user prompt if 0 or >1 Major Leaguers are found
                print("\nMultiple players found. Please choose one:")
                player_options = []
                for i, item in enumerate(major_league_players):
                    link = item.find('a')
                    description = item.find('div', class_='search-item-name').get_text(strip=True)
                    player_options.append({"url": link['href']})
                    print(f"  {i + 1}: {description}")

                while True:
                    try:
                        choice = int(input("Enter the number of the correct player: "))
                        if 1 <= choice <= len(player_options):
                            selected_player = player_options[choice - 1]
                            player_url_to_scrape = f"https://www.baseball-reference.com{selected_player['url']}"
                            break
                        else:
                            print("Invalid number. Please try again.")
                    except ValueError:
                        print("Invalid input. Please enter a number.")
        
        # Now, check if we need to navigate. If we're already there, don't do anything.
        if driver.current_url != player_url_to_scrape:
            print(f"\nNavigating to player page: {player_url_to_scrape}")
            driver.get(player_url_to_scrape)
            time.sleep(2)
        
        # At this point, we are definitely on the correct page. Scrape it.
        print("Scraping stats...")
        page_source = driver.page_source
        return parse_stats_from_html(page_source)

    finally:
        # Important: always close the browser window at the very end
        driver.quit()


if __name__ == "__main__":
    player_name_input = input("Enter the full name of the baseball player to search for: ")
    
    if not player_name_input:
        print("No name entered. Exiting.")
    else:
        career_stats = search_and_scrape_player(player_name_input)
        
        if career_stats:
            print("\n--- Career Stats (JSON) ---")
            print(json.dumps(career_stats, indent=4))
        else:
            print("Could not retrieve career stats.")
