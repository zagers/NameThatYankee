import os
from PIL import Image
import google.generativeai as genai
from pathlib import Path
import json
from bs4 import BeautifulSoup, Comment
from datetime import datetime
import re
import subprocess
import sys
import time
import urllib.parse

# Imports for the new custom scraper
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


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


# --- Scraper Functions ---

def parse_career_totals(soup):
    """Parses the 'stats_pullout' div for career totals."""
    stats_dict = {}
    stats_pullout = soup.find('div', class_='stats_pullout')
    if not stats_pullout: return None

    header_div = stats_pullout.find('div')
    if not header_div: return None

    labels = [p.get_text(strip=True) for p in header_div.find_all('p')]
    try:
        career_stats_index = labels.index('Career')
    except ValueError:
        return None

    stat_divs = stats_pullout.find_all('div', class_=['p1', 'p2', 'p3'])
    if not stat_divs: return None

    for group in stat_divs:
        for stat_container in group.find_all('div'):
            stat_name_tag = stat_container.find('span')
            stat_value_tags = stat_container.find_all('p')
            if stat_name_tag and len(stat_value_tags) > career_stats_index:
                stat_name = stat_name_tag.get_text(strip=True)
                stat_value = stat_value_tags[career_stats_index].get_text(strip=True)
                stats_dict[stat_name] = stat_value
    return stats_dict

def parse_yearly_war(soup):
    """
    Parses the main stats table for year-by-year WAR and team data.
    This version is updated to handle multiple possible page layouts.
    """
    table = None
    war_stat_id = None
    
    player_type = 'hitter'
    info_div = soup.find('div', id='info')
    if info_div:
        p_tags = info_div.find_all('p')
        for p_tag in p_tags:
            full_text = p_tag.get_text()
            if "Position:" in full_text and "Pitcher" in full_text:
                player_type = 'pitcher'
                break
    
    if player_type == 'hitter':
        table_id = 'players_standard_batting'
        war_stat_id = 'b_war'
    else:
        table_id = 'players_standard_pitching'
        war_stat_id = 'p_war' 

    # Check for multiple possible container IDs and the table ID directly.
    possible_container_ids = [f'switcher_{table_id}', f'all_{table_id}']
    
    for cid in possible_container_ids:
        container = soup.find('div', id=cid)
        if container:
            table = container.find('table', id=table_id)
            if table: break

    if not table:
        table = soup.find('table', id=table_id)

    if not table:
        print("  Table not found directly, searching in comments (fallback)...")
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        table_html = ""
        for comment in comments:
            if f'id="{table_id}"' in comment:
                table_html = comment
                break
        if table_html:
            table_soup = BeautifulSoup(table_html, 'html.parser')
            table = table_soup.find('table')

    if not table:
        print(f"  Could not find stats table with id '{table_id}'.")
        return []

    rows = table.find('tbody').find_all('tr')
    
    teams_per_year = {}
    for row in rows:
        if 'partial_table' in row.get('class', []):
            year_cell = row.find('th', {'data-stat': 'year_id'})
            team_cell = row.find('td', {'data-stat': 'team_name_abbr'})
            if year_cell and team_cell:
                year = year_cell.text.strip()
                if year not in teams_per_year:
                    teams_per_year[year] = []
                teams_per_year[year].append(team_cell.text.strip())

    yearly_data = []
    for row in rows:
        if 'partial_table' in row.get('class', []) or 'thead' in row.get('class', []) or not row.get('id'):
            continue

        year_cell = row.find('th', {'data-stat': 'year_id'})
        team_cell = row.find('td', {'data-stat': 'team_name_abbr'}) 
        war_cell = row.find('td', {'data-stat': war_stat_id})

        if year_cell and team_cell and war_cell and year_cell.text.strip():
            year = year_cell.text.strip()
            display_team = team_cell.text.strip()
            
            try:
                war = float(war_cell.text.strip())
                all_teams_for_year = teams_per_year.get(year, [display_team])
                
                yearly_data.append({
                    'year': year,
                    'teams': all_teams_for_year,
                    'display_team': display_team,
                    'war': war
                })
            except (ValueError, TypeError):
                continue

    return sorted(yearly_data, key=lambda x: x['year'])


def search_and_scrape_player(player_name):
    """
    Opens a browser, finds a player's page, and scrapes both career totals and yearly WAR.
    """
    print(f"⚾ Scraping all stats for {player_name} from Baseball-Reference...")
    
    cleaned_name = re.sub(r'[^\w\s]', '', player_name)
    print(f"  (Using cleaned name for search: '{cleaned_name}')")
    
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new")
    options.page_load_strategy = 'eager'
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    try:
        search_query = urllib.parse.quote_plus(cleaned_name)
        search_url = f"https://www.baseball-reference.com/search/search.fcgi?search={search_query}"
        
        print(f"  Navigating to search results for '{cleaned_name}'...")
        driver.get(search_url)
        time.sleep(2)

        player_url_to_scrape = None

        if "/players/" in driver.current_url:
            print("  Direct match found!")
            player_url_to_scrape = driver.current_url
        else:
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            major_leagues_header = soup.find('h3', string=lambda text: text and "major leagues" in text.lower())
            major_league_players = []
            if major_leagues_header:
                for sibling in major_leagues_header.find_next_siblings():
                    if sibling.name == 'div' and 'search-item' in sibling.get('class', []):
                        major_league_players.append(sibling)
                    if sibling.name == 'h3': break
            else:
                major_league_players = soup.find_all('div', class_='search-item')

            if not major_league_players:
                print("  No matching player links found.")
                return None
            if len(major_league_players) == 1:
                link = major_league_players[0].find('a')
                player_url_to_scrape = f"https://www.baseball-reference.com{link['href']}"
            else:
                print("\n  Multiple players found. Please choose one:")
                player_options = []
                for i, item in enumerate(major_league_players):
                    link = item.find('a')
                    description = item.find('div', class_='search-item-name').get_text(strip=True)
                    player_options.append({"url": link['href']})
                    print(f"    {i + 1}: {description}")
                while True:
                    try:
                        choice = int(input("  Enter the number of the correct player: "))
                        if 1 <= choice <= len(player_options):
                            selected_player = player_options[choice - 1]
                            player_url_to_scrape = f"https://www.baseball-reference.com{selected_player['url']}"
                            break
                        else: print("  Invalid number.")
                    except ValueError: print("  Invalid input.")
        
        if driver.current_url != player_url_to_scrape:
            print(f"  Navigating to player page: {player_url_to_scrape}")
            driver.get(player_url_to_scrape)
            time.sleep(2)
        
        print(f"  Attempting to scrape stats from final URL: {driver.current_url}")
        
        print("  Scraping page source...")
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        career_totals = parse_career_totals(soup)
        yearly_war = parse_yearly_war(soup)

        if career_totals and yearly_war:
            print("  ✅ All stats scraped successfully.")
            return {"career_totals": career_totals, "yearly_war": yearly_war}
        else:
            print("  ❌ Failed to scrape all required data.")
            return None

    finally:
        driver.quit()
