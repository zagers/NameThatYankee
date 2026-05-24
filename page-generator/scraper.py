# ABOUTME: Fetches and extracts player statistics and details from web sources.
# ABOUTME: Uses Selenium and BeautifulSoup to gather accurate career data.
from bs4 import BeautifulSoup, Comment
import time
import urllib.parse
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import re
import json
from pathlib import Path
import string
import requests

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

    possible_container_ids = [f'switcher_{table_id}', f'all_{table_id}']
    
    for cid in possible_container_ids:
        container = soup.find('div', id=cid)
        if container:
            table = container.find('table', id=table_id)
            if table: break

    if not table:
        table = soup.find('table', id=table_id)

    if not table:
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

def parse_transactions(soup):
    """Parses the transactions section, handling comments and different possible IDs."""
    transactions = []
    
    # Possible IDs for transactions
    possible_ids = ['all_transactions', 'all_transactions_other', 'div_transactions_other']
    
    trans_div = None
    for tid in possible_ids:
        trans_div = soup.find('div', id=tid)
        if trans_div: break
        
    if not trans_div:
        # Check in comments
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            for tid in possible_ids:
                if f'id="{tid}"' in comment:
                    trans_soup = BeautifulSoup(comment, 'html.parser')
                    trans_div = trans_soup.find('div', id=tid)
                    if trans_div: break
            if trans_div: break
                
    if trans_div:
        # Transactions are usually in <p> tags
        for p in trans_div.find_all('p'):
            # Skip the 'note' paragraph
            if 'class' in p.attrs and 'note' in p['class']:
                continue
            text = p.get_text(strip=True)
            if text:
                transactions.append(text)
                
    return transactions

def parse_awards(soup):
    """Parses the awards/honors from the bling or extra_stats div."""
    awards = []
    
    # Possible IDs for awards
    possible_ids = ['bling', 'extra_stats']
    
    awards_div = None
    for aid in possible_ids:
        awards_div = soup.find(['ul', 'div'], id=aid)
        if awards_div: break
        
    if not awards_div:
        # Check in comments
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            for aid in possible_ids:
                if f'id="{aid}"' in comment:
                    awards_soup = BeautifulSoup(comment, 'html.parser')
                    awards_div = awards_soup.find(['ul', 'div'], id=aid)
                    if awards_div: break
            if awards_div: break
            
    if awards_div:
        for li in awards_div.find_all('li'):
            text = li.get_text(strip=True)
            if text:
                awards.append(text)
                
    return awards

def get_driver():
    """Initializes and returns a headless Chrome driver."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.page_load_strategy = 'eager'
    
    # Use system chromium/chromedriver if available (especially for ARM/aarch64 support)
    system_chromedriver = "/usr/bin/chromedriver"
    system_chromium = "/usr/bin/chromium"
    
    if os.path.exists(system_chromedriver) and os.path.exists(system_chromium):
        print(f"  Using system chromium: {system_chromium} and chromedriver: {system_chromedriver}")
        options.binary_location = system_chromium
        service = ChromeService(executable_path=system_chromedriver)
        return webdriver.Chrome(service=service, options=options)
    else:
        print("  Using WebDriver Manager to download ChromeDriver...")
        return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

def parse_appearances(soup):
    """
    Parses games played by position from the 'Appearances' table.
    Often hidden in comments.
    """
    pos_data = {}
    # B-Ref hides many tables in comments.
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    table = None
    for comment in comments:
        if 'id="appearances"' in comment:
            c_soup = BeautifulSoup(comment, "html.parser")
            table = c_soup.find("table", id="appearances")
            break
            
    if not table:
        table = soup.find("table", id="appearances")
        
    if table:
        # Looking for rows in the body
        for row in table.select("tbody tr"):
            th = row.find("th")
            if not th: continue
            pos = th.get_text(strip=True)
            # We want specific positions, not "Total"
            if pos in ["Total", "Year", "Age", "Team", "Lg"]: continue
            
            g_td = row.find("td", {"data-stat": "G"})
            if g_td:
                pos_data[pos] = g_td.get_text(strip=True)
                
    return pos_data

def parse_awards(soup):
    """Extracts awards and honors from the bling items or awards section."""
    awards = []
    # Bling items at the top
    bling = soup.select(".bling-item")
    for item in bling:
        awards.append(item.get_text(strip=True))
        
    # Also check specific awards list
    awards_div = soup.select_one("#awards")
    if awards_div:
        for li in awards_div.find_all('li'):
            awards.append(li.get_text(strip=True))
            
    return list(set(awards))

def search_and_scrape_player(player_name, automated=False, driver=None):
    """
    Opens a browser (if not provided), finds a player's page, and scrapes both career totals and yearly WAR.
    """
    print(f"⚾ Scraping all stats for {player_name} from Baseball-Reference...")

    # Strip trailing Roman numerals (e.g., " III", " IV") to improve search results.
    name_for_search = re.sub(r'\s[IVX]+$', '', player_name.strip())

    if name_for_search != player_name.strip():
        print(f"  (Note: Removed Roman numerals. Using '{name_for_search}' for search)")

    cleaned_name = re.sub(r'[^\w\s]', '', name_for_search)
    print(f"  (Using cleaned name for search: '{cleaned_name}')")
    
    own_driver = False
    if driver is None:
        driver = get_driver()
        own_driver = True

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
            
            if len(major_league_players) == 1 or automated:
                selected_index = 0
                if len(major_league_players) > 1 and automated:
                    print(f"  ⚠️ Multiple players found. Searching for best match for '{cleaned_name}'...")
                    # Try to find a better match than just the first result
                    for i, item in enumerate(major_league_players):
                        name_text = item.get_text().lower()
                        if cleaned_name.lower() in name_text:
                            selected_index = i
                            print(f"  ✅ Found better match at index {i+1}: {item.find('div', class_='search-item-name').get_text(strip=True)}")
                            break
                    if selected_index == 0:
                        print("  ⚠️ No perfect name match found. Defaulting to the first result.")
                else:
                    print("  Found a single Major League player match.")
                
                link = major_league_players[selected_index].find('a')
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
        transactions = parse_transactions(soup)
        awards = parse_awards(soup)
        positions = parse_appearances(soup)

        if career_totals and yearly_war:
            print("  ✅ All stats scraped successfully.")
            return {
                "career_totals": career_totals, 
                "yearly_war": yearly_war,
                "transactions": transactions,
                "awards": awards,
                "positions": positions
            }
        else:
            print("  ❌ Failed to scrape all required data.")
            return None

    finally:
        if own_driver:
            driver.quit()

def generate_master_player_list(project_dir: Path):
    """
    Scrapes all player names from Baseball-Reference and saves them to a JSON file.
    """
    print(" scraping all player names from Baseball-Reference...")
    all_players = []
    base_url = "https://www.baseball-reference.com/players/"
    
    driver = get_driver()

    try:
        total_players_found = 0
        for letter in string.ascii_lowercase:
            page_url = f"{base_url}{letter}/"
            print(f"  Scraping page for letter: {letter.upper()}...")
            driver.get(page_url)
            time.sleep(2) 

            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            content_div = soup.find('div', id='div_players_')
            
            players_on_page = 0
            if content_div:
                player_paragraphs = content_div.find_all('p')
                for p in player_paragraphs:
                    link = p.find('a')
                    if link:
                        all_players.append(link.text)
                        players_on_page += 1
            
            total_players_found += players_on_page
            print(f"    Found {players_on_page} players for '{letter.upper()}'. Total so far: {total_players_found}")

        
        output_path = project_dir / "all_players.js"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("const ALL_PLAYERS = ")
            json.dump(all_players, f, indent=2)
            f.write(";")
        
        print(f"\n✅ Successfully scraped {len(all_players)} player names.")
        print(f"   Master player list saved to: {output_path}")

    finally:
        driver.quit()

def _clean_bio_text(content_element):
    """
    Sanitizes HTML content from biographies, removing technical noise,
    scripts, styles, and normalizing whitespace.
    """
    if not content_element:
        return ""
        
    # Elements to completely remove
    noise_tags = ["script", "style", "noscript", "svg", "iframe", "object", "embed"]
    for tag in content_element.find_all(noise_tags):
        tag.decompose()
        
    # Safely remove elements with explicit noise classes
    noise_classes = {"metadata", "technical", "hidden", "internal", "json-noise", "base64-noise", "wp-block-code"}
    for element in list(content_element.find_all(True)):
        if element.parent is None and element is not content_element:
            continue
        try:
            classes = element.get('class', [])
            if classes and any(cls in noise_classes for cls in classes):
                element.decompose()
        except AttributeError:
            continue

    # Extract text, using double newlines for block separation to preserve paragraphs
    text = content_element.get_text(separator='\n\n', strip=True)
    
    # Remove common technical labels and their associated JSON/junk
    # Matches "Metadata: { ... }" or "Technical: { ... }" etc.
    text = re.sub(r'(?i)(Metadata|Technical|JSON|Source|Author):\s*\{.*?\}', '', text)
    
    # Remove long Base64-like or alphanumeric strings (often technical noise from SABR/WordPress)
    # 40+ chars with no spaces
    text = re.sub(r'[A-Za-z0-9+/]{40,}[=]*', '', text)
    
    # Also catch strings with some technical noise like dots or braces if they are very long
    text = re.sub(r'[A-Za-z0-9+/.\-{}]{70,}', '', text)
    
    # Filter out SABR/Wikipedia boilerplate phrases and metadata
    boilerplate_patterns = [
        r'This bio is not assigned\.\s*Want to write a SABR bio\?\s*Contact bioproject@sabr\.org\s*\.',
        r'If you can help us improve this player[’\']s biography,\s*contact us\s*\.',
        r'Share this entry\s*Share on Facebook\s*Share on X\s*Share on LinkedIn\s*Share on Reddit\s*Share by Mail',
        r'Stats\s*Baseball Reference\s*Retrosheet\s*Oral History',
        r'No items found',
        r'Tags None',
        r'BioProject - Person',
        r'Wikipedia Summary:',
        r'This article was written by.*',
        r'Last revised:.*',
        r'^Sources$',
        r'^Notes$',
        r'^[0-9]{4}s All-Stars$',
        r'^January \d+, \d{4}$',
        r'^February \d+, \d{4}$',
        r'^March \d+, \d{4}$',
        r'^April \d+, \d{4}$',
        r'^May \d+, \d{4}$',
        r'^June \d+, \d{4}$',
        r'^July \d+, \d{4}$',
        r'^August \d+, \d{4}$',
        r'^September \d+, \d{4}$',
        r'^October \d+, \d{4}$',
        r'^November \d+, \d{4}$',
        r'^December \d+, \d{4}$'
    ]
    
    # Process text line by line to remove standalone junk
    lines = text.split('\n\n')
    cleaned_lines = []
    
    # Junk that should be removed if it's a standalone paragraph
    standalone_junk = {'/', 'in', 'by', 'admin', '·', ',', 'None', 'Tags'}
    
    for line in lines:
        line = line.strip()
        if not line or line in standalone_junk:
            continue
            
        skip = False
        for pattern in boilerplate_patterns:
            if re.search(pattern, line, flags=re.IGNORECASE | re.MULTILINE):
                skip = True
                break
        
        if not skip:
            cleaned_lines.append(line)
    
    text = '\n\n'.join(cleaned_lines)
    
    # Normalize horizontal whitespace (spaces and tabs)
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Normalize vertical whitespace (max two newlines for paragraphs)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    
    return text

def get_mlb_bio(player_name, shared_driver=None):
    """
    Scrapes the MLB.com biography/profile for a player as a fallback for SABR.
    """
    print(f"⚾ Attempting MLB.com bio fallback for {player_name}...")
    
    # Use a simpler pattern search if we can't find a direct API
    # format is https://www.mlb.com/player/first-last-ID
    
    driver = shared_driver or get_driver()
    try:
        # Search Bing for the MLB profile URL (often less bot-blocked than Google for scraping)
        search_query = urllib.parse.quote_plus(f"site:mlb.com/player {player_name}")
        driver.get(f"https://www.bing.com/search?q={search_query}")
        time.sleep(2)
        
        # Find the first MLB player link
        links = driver.find_elements(By.TAG_NAME, "a")
        mlb_url = None
        for link in links:
            try:
                href = link.get_attribute("href")
                if href and "mlb.com/player/" in href and "-" in href:
                    mlb_url = href
                    break
            except:
                continue
        
        if not mlb_url:
            print(f"  ⚠️ No MLB.com profile link found for {player_name}")
            return None
            
        print(f"  ✅ Found MLB.com profile: {mlb_url}")
        driver.get(mlb_url)
        time.sleep(3)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Target the bio section
        # MLB.com uses a modal or a bottom profile section
        content = soup.find("div", id="playerBioModalBody")
        if not content:
            content = soup.select_one(".player-profile-bottom")
            
        if content:
            text = _clean_bio_text(content)
            if len(text) > 200:
                return text

        return None

    except Exception as e:
        print(f"  ⚠️ MLB.com fallback failed for {player_name}: {e}")
        return None
    finally:
        if not shared_driver:
            driver.quit()

def get_sabr_bio(player_name):
    """
    Scrapes the SABR biography for a given player name with robust searching.
    """
    print(f"⚾ Scraping SABR bio for {player_name}...")
    
    # 1. Try direct URL guess (most common format)
    slug = player_name.lower().strip().replace(" ", "-")
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    # Remove common suffixes like Jr, Sr, III
    slug = re.sub(r'-(jr|sr|ii|iii|iv)$', '', slug)
    direct_url = f"https://sabr.org/bioproj/person/{slug}/"
    
    urls_to_try = [direct_url]
    
    # 2. Search if direct guess fails or as part of the loop
    search_query = urllib.parse.quote_plus(player_name)
    search_url = f"https://sabr.org/?s={search_query}&post_type=bioproj"
    
    try:
        # Check direct URL first for speed
        for url in urls_to_try:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200 and "bioproj/person" in response.url:
                    bio_soup = BeautifulSoup(response.text, 'html.parser')
                    content = bio_soup.select_one('.entry-content, .tb-field, .standard-content, article')
                    if content:
                        text = _clean_bio_text(content)
                        if len(text) > 500: # Ensure it's a real bio, not a stub
                            print(f"  ✅ Found bio via direct link: {url}")
                            return text
            except:
                continue

        # 3. Perform search if direct link didn't work
        response = requests.get(search_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all result links
        links = soup.select('.post-title a, .entry-title a, .search-result-title a')
        best_link = None
        
        name_parts = player_name.lower().split()
        first_last_only = [name_parts[0], name_parts[-1]] if len(name_parts) > 1 else name_parts

        for link in links:
            href = link.get('href', '')
            text = link.get_text().lower()
            
            # Prioritize person biographies
            if "bioproj/person" in href:
                # First try full name match (excluding initials)
                full_match = all(part in text or part in href for part in name_parts if len(part) > 1 or not part.isalpha())
                # If that fails, try first and last name match (more flexible for middle names/nicknames)
                fl_match = all(part in text or part in href for part in first_last_only)
                
                if full_match or fl_match:
                    best_link = href
                    break
        
        if not best_link:
            print(f"  ❌ No definitive SABR bio found for {player_name}.")
            return ""
        
        print(f"  Found bio URL via search: {best_link}")
        bio_response = requests.get(best_link, timeout=10)
        bio_response.raise_for_status()
        bio_soup = BeautifulSoup(bio_response.text, 'html.parser')
        
        content = bio_soup.select_one('.entry-content, .tb-field, .standard-content, article')
        if content:
            text = _clean_bio_text(content)
            print(f"  ✅ Successfully scraped SABR bio ({len(text)} chars).")
            return text
        else:
            print(f"  ❌ Could not find content in {best_link}")
            return ""
            
    except Exception as e:
        print(f"  ❌ Error scraping SABR bio: {e}")
        return ""


def get_wikipedia_summary(player_name):
    """
    Fetches the introductory summary paragraph of a player from Wikipedia.
    First tries the plain name, then falls back to name + ' (baseball)' for disambiguation.
    """
    print(f"🌐 Fetching Wikipedia summary for {player_name}...")
    
    # Normalize name to Wikipedia title format (spaces replaced with underscores)
    formatted_name = player_name.strip().replace(" ", "_")
    
    # Try both the direct name and the baseball disambiguated page
    titles_to_try = [
        formatted_name,
        f"{formatted_name}_(baseball)"
    ]
    
    for title in titles_to_try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
        headers = {
            "User-Agent": "NameThatYankeeTriviaGenerator/1.0 (https://namethatyankeequiz.com; admin@namethatyankeequiz.com)"
        }
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                extract = data.get("extract", "")
                if extract and len(extract) > 100:
                    print(f"  ✅ Found Wikipedia summary for: {title}")
                    return extract
        except Exception as e:
            print(f"  ⚠️ Error querying Wikipedia API for {title}: {e}")
            
    print(f"  ❌ No Wikipedia summary found for {player_name}.")
    return None


def generate_stats_fallback(player_dossier):
    """
    Generates rich, 100% accurate, dynamic stats-based hints when LLM generation fails.
    Avoids hardcoding, complies strictly with the spoiler guidelines:
    - No player name/nicknames.
    - No team names or city names (except referring generally to 'New York' or 'pinstripes').
    - No specific years.
    - No card back stats (career BA, total HR, total RBI, specific W/L records).
    - No team lists (e.g., do not say 'played for 9 teams').
    """
    yearly_war = player_dossier.get('yearly_war', [])
    positions_data = player_dossier.get('positions', {})
    
    # Translate position abbreviations
    pos_map = {
        'P': 'pitcher', 'C': 'catcher', '1B': 'first baseman', '2B': 'second baseman',
        '3B': 'third baseman', 'SS': 'shortstop', 'LF': 'left fielder', 'CF': 'center fielder',
        'RF': 'right fielder', 'OF': 'outfielder', 'DH': 'designated hitter'
    }
    
    primary_pos = 'player'
    max_games = 0
    if isinstance(positions_data, dict):
        for pos, games_str in positions_data.items():
            try:
                games = int(games_str)
                if games > max_games:
                    max_games = games
                    primary_pos = pos_map.get(pos, 'player')
            except (ValueError, TypeError):
                continue
                
    # Unique seasons count
    seasons_count = len(yearly_war)
    
    hints = []
    
    # Hint 1: Position and career length/tenure
    if seasons_count >= 10:
        hints.append(f"Experienced major league {primary_pos} who enjoyed a career spanning over a decade in the big leagues.")
    elif seasons_count >= 5:
        hints.append(f"Veteran major league {primary_pos} with a multi-season career in the big leagues.")
    else:
        hints.append(f"Major league {primary_pos} who played multiple seasons at the professional level.")
        
    # Hint 2: Defensive appearances
    if max_games > 500:
        hints.append(f"Appeared defensively in over {max_games - (max_games % 100)} games at his primary position of {primary_pos} during his career.")
    elif max_games > 100:
        hints.append(f"Logged more than {max_games - (max_games % 50)} professional appearances defensively at {primary_pos}.")
    else:
        hints.append(f"Featured primarily as a defensive presence at the {primary_pos} position.")

    # Hint 3: Yankees connection
    hints.append(f"Wore the pinstripes in New York during his career as a valuable veteran contributor.")
    
    return hints


