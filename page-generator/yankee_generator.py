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
    This version is rewritten to correctly handle multi-team seasons.
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

    container = soup.find('div', id=f'switcher_{table_id}')
    if container:
        table = container.find('table', id=table_id)

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
    
    yearly_data = []
    
    # First pass: Get all teams for each year
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

    # Second pass: Get the main season data and combine
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
                
                # Get the full list of teams for this year
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
    
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new")
    options.page_load_strategy = 'eager'
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    try:
        search_query = urllib.parse.quote_plus(player_name)
        search_url = f"https://www.baseball-reference.com/search/search.fcgi?search={search_query}"
        
        print(f"  Navigating to search results for '{player_name}'...")
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

# --- Gemini API Functions ---

def get_player_info_from_image(image_path: Path, api_key: str):
    print(f"🤖 Analyzing clue image with Gemini to identify player...")
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        clue_image = Image.open(image_path)
        
        generation_config = genai.types.GenerationConfig(temperature=0.2)
        
        prompt = """
        You are a baseball historian. Analyze the provided image of a "Name That Yankee" trivia card. 
        Your only task is to identify the player's name.

        Your response must be a valid JSON object with the following structure, and nothing else:
        {
          "name": "Player's Full Name",
          "nickname": "Player's common nickname, or an empty string"
        }
        """
        
        response = model.generate_content([prompt, clue_image], generation_config=generation_config)
        json_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        player_data = json.loads(json_text)

        print(f"  ✅ Player identified as: {player_data['name']}")
        return player_data

    except Exception as e:
        print(f"  ❌ Error communicating with Gemini API: {e}")
        return None

def get_facts_from_gemini(player_name: str, api_key: str):
    print(f"🤖 Asking Gemini for interesting facts about {player_name}...")
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        generation_config = genai.types.GenerationConfig(temperature=0.2)
        
        prompt = f"""
        Provide three interesting and unique career facts about the baseball player {player_name}.

        **Directives:**
        - Keep each fact to a single, short sentence.
        - Do not use embellishing or subjective language (e.g., "remarkable," "renowned").
        - Focus only on career highlights (e.g., "Was a 3-time batting champion") or unique statistical achievements (e.g., "He is the only player to win a batting title in both the AL & NL").
        - Also include facts about family relationships ("Father pitched for the Red Sox from 1992-2000")
        - In the output do not use the players name or the pronoun "he". Just state the fact (e.g. "Was a five time all-star" not "He was a five time all star")

        Your response must be a valid JSON object with the following structure, and nothing else:
        {{
          "facts": [
            "Fact 1.",
            "Fact 2.",
            "Fact 3."
          ]
        }}
        """
        response = model.generate_content(prompt, generation_config=generation_config)
        json_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        fact_data = json.loads(json_text)
        print("  ✅ Facts retrieved.")
        return fact_data.get('facts', [])

    except Exception as e:
        print(f"  ❌ Error getting facts from Gemini API: {e}")
        return []


# --- File Generation and Review Functions ---

def review_and_edit_data(player_data: dict, project_dir: Path) -> dict:
    print("\n" + "="*40)
    print("--- Please Review the Following Data ---")
    print(f"Player Name: {player_data.get('name', 'N/A')}")
    print(f"Nickname: {player_data.get('nickname', 'N/A')}")
    print("Facts:")
    for i, fact in enumerate(player_data.get('facts', []), 1):
        print(f"  {i}. {fact}")
    print("Career Totals (from Baseball-Reference):")
    print(json.dumps(player_data.get('career_totals', {}), indent=2))
    print("Yearly WAR (for chart):")
    print(json.dumps(player_data.get('yearly_war', []), indent=2))
    print("="*40)

    while True:
        is_correct = input("Is all of this information correct? (y/n): ").lower().strip()
        if is_correct in ['y', 'n']: break
        print("Invalid input. Please enter 'y' or 'n'.")

    if is_correct == 'y':
        print("✅ Data confirmed.")
        return player_data
    else:
        temp_file_path = project_dir / "temp_player_data_to_edit.json"
        try:
            with open(temp_file_path, 'w') as f:
                json.dump(player_data, f, indent=4)
            print(f"\n📝 A temporary file has been created. Please open this file in your text editor:\n   {temp_file_path}")
            input("\nPress Enter in this terminal when you are finished editing...")
            with open(temp_file_path, 'r') as f:
                corrected_data = json.load(f)
            print("✅ Data updated with your corrections.")
            return corrected_data
        except Exception as e:
            print(f"❌ An error occurred during the editing process: {e}")
            return player_data
        finally:
            if temp_file_path.exists(): temp_file_path.unlink()

def generate_detail_page(player_data: dict, date_str: str, formatted_date: str, project_dir: Path):
    print(f"  📄 Generating detail page for {date_str}...")
    name = player_data.get('name', 'N/A')
    nickname = player_data.get('nickname', '')
    facts = player_data.get('facts', [])
    career_totals_data = player_data.get('career_totals', {})
    yearly_war_data = player_data.get('yearly_war', [])
    
    display_name = f'{name} "{nickname}"' if nickname else name
    facts_html = "\n".join([f"                        <li>{fact}</li>" for fact in facts])
    
    stats_table_html = ""
    if career_totals_data and any(career_totals_data.values()):
        headers = career_totals_data.keys()
        header_html = "".join([f"<th>{h}</th>" for h in headers])
        row_html = "".join([f"<td>{career_totals_data.get(h, '')}</td>" for h in headers])
        stats_table_html = f"""
        <div class="stats-table-container">
            <h3>Career Totals</h3>
            <div class="table-wrapper">
                <table>
                    <thead><tr>{header_html}</tr></thead>
                    <tbody><tr>{row_html}</tr></tbody>
                </table>
            </div>
            <p class="citation">Statistics via Baseball-Reference.com</p>
        </div>
        """

    chart_html = ""
    if yearly_war_data:
        years = json.dumps([item['year'] for item in yearly_war_data])
        war_data = json.dumps([item['war'] for item in yearly_war_data])
        teams_by_year = json.dumps([item['display_team'] for item in yearly_war_data])
        
        all_teams = set()
        for item in yearly_war_data:
            for team in item['teams']:
                all_teams.add(team)
        all_years = {item['year'] for item in yearly_war_data}
        search_data = {'teams': list(all_teams), 'years': list(all_years)}
        search_data_html = f'<div id="search-data" style="display:none;">{json.dumps(search_data)}</div>'


        chart_html = f"""
        <div class="chart-container">
            <h3>Career Arc by WAR</h3>
            <div class="chart-wrapper">
                <canvas id="careerArcChart"></canvas>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            const years = {years};
            const warData = {war_data};
            const teamsByYear = {teams_by_year};

            const teamColors = {{
                'ARI': {{ bg: 'rgba(167, 25, 48, 0.7)', border: 'rgb(167, 25, 48)', name: 'D-backs' }},
                'ATL': {{ bg: 'rgba(20, 44, 86, 0.7)', border: 'rgb(20, 44, 86)', name: 'Braves' }},
                'BAL': {{ bg: 'rgba(223, 70, 1, 0.7)', border: 'rgb(223, 70, 1)', name: 'Orioles' }},
                'BOS': {{ bg: 'rgba(12, 35, 64, 0.7)', border: 'rgb(12, 35, 64)', name: 'Red Sox' }},
                'CHC': {{ bg: 'rgba(14, 51, 134, 0.7)', border: 'rgb(14, 51, 134)', name: 'Cubs' }},
                'CHW': {{ bg: 'rgba(39, 37, 31, 0.7)', border: 'rgb(39, 37, 31)', name: 'White Sox' }},
                'CIN': {{ bg: 'rgba(198, 12, 48, 0.7)', border: 'rgb(198, 12, 48)', name: 'Reds' }},
                'CLE': {{ bg: 'rgba(12, 35, 64, 0.7)', border: 'rgb(12, 35, 64)', name: 'Guardians' }},
                'COL': {{ bg: 'rgba(51, 0, 111, 0.7)', border: 'rgb(51, 0, 111)', name: 'Rockies' }},
                'DET': {{ bg: 'rgba(12, 35, 64, 0.7)', border: 'rgb(12, 35, 64)', name: 'Tigers' }},
                'HOU': {{ bg: 'rgba(0, 45, 98, 0.7)', border: 'rgb(0, 45, 98)', name: 'Astros' }},
                'KCR': {{ bg: 'rgba(0, 70, 135, 0.7)', border: 'rgb(0, 70, 135)', name: 'Royals' }},
                'LAA': {{ bg: 'rgba(186, 0, 33, 0.7)', border: 'rgb(186, 0, 33)', name: 'Angels' }},
                'LAD': {{ bg: 'rgba(0, 90, 156, 0.7)', border: 'rgb(0, 90, 156)', name: 'Dodgers' }},
                'MIA': {{ bg: 'rgba(0, 142, 204, 0.7)', border: 'rgb(0, 142, 204)', name: 'Marlins' }},
                'MIL': {{ bg: 'rgba(12, 35, 64, 0.7)', border: 'rgb(12, 35, 64)', name: 'Brewers' }},
                'MIN': {{ bg: 'rgba(12, 35, 64, 0.7)', border: 'rgb(12, 35, 64)', name: 'Twins' }},
                'NYM': {{ bg: 'rgba(0, 45, 114, 0.7)', border: 'rgb(0, 45, 114)', name: 'Mets' }},
                'NYY': {{ bg: 'rgba(12, 35, 64, 0.8)', border: 'rgb(12, 35, 64)', name: 'Yankees' }},
                'OAK': {{ bg: 'rgba(0, 56, 49, 0.7)', border: 'rgb(0, 56, 49)', name: 'Athletics' }},
                'PHI': {{ bg: 'rgba(232, 24, 40, 0.7)', border: 'rgb(232, 24, 40)', name: 'Phillies' }},
                'PIT': {{ bg: 'rgba(253, 184, 39, 0.7)', border: 'rgb(253, 184, 39)', name: 'Pirates' }},
                'SDP': {{ bg: 'rgba(79, 64, 51, 0.7)', border: 'rgb(79, 64, 51)', name: 'Padres' }},
                'SFG': {{ bg: 'rgba(253, 90, 30, 0.7)', border: 'rgb(253, 90, 30)', name: 'Giants' }},
                'SEA': {{ bg: 'rgba(12, 35, 64, 0.7)', border: 'rgb(12, 35, 64)', name: 'Mariners' }},
                'STL': {{ bg: 'rgba(196, 30, 58, 0.7)', border: 'rgb(196, 30, 58)', name: 'Cardinals' }},
                'TBR': {{ bg: 'rgba(143, 188, 230, 0.7)', border: 'rgb(143, 188, 230)', name: 'Rays' }},
                'TEX': {{ bg: 'rgba(0, 50, 120, 0.7)', border: 'rgb(0, 50, 120)', name: 'Rangers' }},
                'TOR': {{ bg: 'rgba(20, 54, 136, 0.7)', border: 'rgb(20, 54, 136)', name: 'Blue Jays' }},
                'WSN': {{ bg: 'rgba(171, 0, 3, 0.7)', border: 'rgb(171, 0, 3)', name: 'Nationals' }},
                'MON': {{ bg: 'rgba(0, 45, 114, 0.7)', border: 'rgb(0, 45, 114)', name: 'Expos' }},
                'CAL': {{ bg: 'rgba(186, 0, 33, 0.7)', border: 'rgb(186, 0, 33)', name: 'Angels' }},
                'FLA': {{ bg: 'rgba(0, 142, 204, 0.7)', border: 'rgb(0, 142, 204)', name: 'Marlins' }},
                'BRO': {{ bg: 'rgba(0, 90, 156, 0.7)', border: 'rgb(0, 90, 156)', name: 'Dodgers' }},
                'SLB': {{ bg: 'rgba(139, 69, 19, 0.7)', border: 'rgb(139, 69, 19)', name: 'Browns' }},
                '2TM': {{ bg: 'rgba(107, 114, 128, 0.7)', border: 'rgb(107, 114, 128)', name: 'Multiple' }},
                'Total': {{ bg: 'rgba(107, 114, 128, 0.7)', border: 'rgb(107, 114, 128)', name: 'Career' }},
                'Default': {{ bg: 'rgba(156, 163, 175, 0.7)', border: 'rgb(156, 163, 175)', name: 'Other' }}
            }};

            const waterfallData = [];
            let cumulativeTotal = 0;
            for (const war of warData) {{
                waterfallData.push([cumulativeTotal, cumulativeTotal + war]);
                cumulativeTotal += war;
            }}
            waterfallData.push([0, cumulativeTotal]);

            const labels = [...years, 'Career Total'];
            const backgroundColors = teamsByYear.map(team => (teamColors[team] || teamColors['Default']).bg);
            backgroundColors.push(teamColors['Total'].bg);

            const borderColors = teamsByYear.map(team => (teamColors[team] || teamColors['Default']).border);
            borderColors.push(teamColors['Total'].border);

            const ctx = document.getElementById('careerArcChart').getContext('2d');
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: labels,
                    datasets: [{{
                        label: 'WAR',
                        data: waterfallData,
                        backgroundColor: backgroundColors,
                        borderColor: borderColors,
                        borderWidth: 2,
                        borderRadius: 4,
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        title: {{ display: false }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    const i = context.dataIndex;
                                    if (i < warData.length) {{
                                        return `${{years[i]}} (${{teamsByYear[i]}}): ${{warData[i].toFixed(1)}}`;
                                    }} else {{
                                        return `Total Career WAR: ${{cumulativeTotal.toFixed(1)}}`;
                                    }}
                                }}
                            }}
                        }},
                        legend: {{
                            display: true,
                            position: 'bottom',
                            labels: {{
                                padding: 20,
                                font: {{ size: 10 }}, // Smaller font size for legend
                                generateLabels: function(chart) {{
                                    const uniqueTeams = [...new Set(teamsByYear)];
                                    const legendItems = uniqueTeams.map(teamAbbr => {{
                                        const teamInfo = teamColors[teamAbbr] || teamColors['Default'];
                                        return {{ text: teamInfo.name, fillStyle: teamInfo.bg, strokeStyle: teamInfo.border, lineWidth: 2 }};
                                    }});
                                    legendItems.push({{ text: teamColors['Total'].name, fillStyle: teamColors['Total'].bg, strokeStyle: teamColors['Total'].border, lineWidth: 2 }});
                                    return legendItems;
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        y: {{ title: {{ display: false }} }},
                        x: {{ 
                            title: {{ display: false }}, 
                            grid: {{ display: false }},
                            ticks: {{ maxTicksLimit: 15 }}
                        }}
                    }}
                }}
            }});
        </script>
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
            <div class="left-column">
                <div class="player-profile">
                    <div class="player-photo">
                        <img src="images/answer-{date_str}.jpg" alt="Photo of {name}">
                    </div>
                    <div class="player-info">
                        <h2>{display_name}</h2>
                        <div class="facts-header">
                            <h3>Career Highlights & Facts</h3>
                            <p class="disclaimer">(Facts are AI-generated and may require verification)</p>
                        </div>
                        <ul>
{facts_html}
                        </ul>
                    </div>
                </div>
                {stats_table_html}
            </div>
            <div class="right-column">
                <div class="original-card">
                    <h3>The Original Clue</h3>
                    <img src="images/clue-{date_str}.jpg" alt="Original trivia card">
                </div>
                {chart_html}
            </div>
        </div>
        {search_data_html}
    </main>
</body>
</html>"""
    
    file_path = project_dir / f"{date_str}.html"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(template)
    print(f"  ✅ Detail page saved successfully.")

def rebuild_index_page(project_dir: Path):
    print("\n✍️ Rebuilding and re-sorting index.html from all available clues...")
    index_path = project_dir / "index.html"
    images_dir = project_dir / "images"
    
    if not index_path.exists():
        print(f"❌ Error: index.html not found at {index_path}.")
        return

    all_clue_files = sorted(images_dir.glob("clue-*.jpg"), reverse=True)
    
    if not all_clue_files:
        print("🤷 No clue images found in the 'images' directory.")
        return

    gallery_tiles = []
    date_pattern = re.compile(r"clue-(\d{4}-\d{2}-\d{2})\.jpg")
    
    team_name_map = {
        'NYY': 'new york yankees', 'BOS': 'boston red sox', 'CAL': 'california angels',
        'CHW': 'chicago white sox', 'OAK': 'oakland athletics', 'PHI': 'philadelphia phillies',
        'SDP': 'san diego padres', 'LAD': 'los angeles dodgers', 'CHC': 'chicago cubs',
        'NYM': 'new york mets', 'CIN': 'cincinnati reds', 'ATL': 'atlanta braves',
        'CLE': 'cleveland indians guardians', 'SEA': 'seattle mariners', 'TOR': 'toronto blue jays',
        'TEX': 'texas rangers', 'KCR': 'kansas city royals', 'MIN': 'minnesota twins',
        'DET': 'detroit tigers', 'BAL': 'baltimore orioles', 'TBR': 'tampa bay rays devil',
        'HOU': 'houston astros', 'LAA': 'los angeles angels', 'SFG': 'san francisco giants',
        'ARI': 'arizona diamondbacks', 'COL': 'colorado rockies', 'MIL': 'milwaukee brewers',
        'STL': 'st louis cardinals', 'PIT': 'pittsburgh pirates', 'MIA': 'miami florida marlins',
        'WSN': 'washington nationals', 'MON': 'montreal expos'
    }

    for clue_file in all_clue_files:
        match = date_pattern.search(clue_file.name)
        if match:
            date_str = match.group(1)
            try:
                dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
                formatted_date = dt_obj.strftime("%B %d, %Y")
                
                detail_page_path = project_dir / f"{date_str}.html"
                search_terms = formatted_date.lower().replace(',', '') 

                if detail_page_path.exists():
                    with open(detail_page_path, 'r', encoding='utf-8') as detail_f:
                        detail_soup = BeautifulSoup(detail_f, 'html.parser')
                    
                    search_data_div = detail_soup.find('div', id='search-data')
                    if search_data_div:
                        search_data = json.loads(search_data_div.string)
                        teams = search_data.get('teams', [])
                        years = search_data.get('years', [])
                        
                        search_terms += " " + " ".join(teams).lower()
                        search_terms += " " + " ".join(years)
                        
                        for team_abbr in teams:
                            if team_abbr in team_name_map:
                                search_terms += " " + team_name_map[team_abbr]

                snippet = f"""<div class="gallery-container" data-search-terms="{search_terms}">
                <a href="{date_str}.html" class="gallery-item">
                    <img src="images/clue-{date_str}.jpg" alt="Name that Yankee trivia card from {date_str}">
                    <div class="gallery-item-overlay"><span>Click to Reveal</span></div>
                </a>
                <p class="gallery-date">Trivia Date: {formatted_date}</p>
            </div>"""
                gallery_tiles.append(snippet)
            except ValueError:
                print(f"⚠️  Warning: Skipping file with invalid date format: {clue_file.name}")
    
    with open(index_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    gallery_div = soup.select_one('.gallery')
    if not gallery_div:
        print(f"❌ Could not find insertion point in index.html.")
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
    api_key = config.get("gemini_api_key")
    if not api_key:
        api_key = input("Please enter your Google Gemini API key (will be saved): ").strip()
    config["gemini_api_key"] = api_key
    
    save_config(config)
    
    images_dir = project_dir / "images"
    images_dir.mkdir(exist_ok=True)

    # 3. Choose mode
    mode = input("Enter a specific date (YYYY-MM-DD) or type 'ALL' to process all clue images: ").strip()

    if mode.upper() == 'ALL':
        clue_files_to_process = sorted(images_dir.glob("clue-*.jpg"), reverse=True)
        if not clue_files_to_process:
            print("🤷 No 'clue-*.jpg' files found in the images directory.")
            exit()
        print(f"\nFound {len(clue_files_to_process)} clue images to process.")
        for clue_path in clue_files_to_process:
            print("\n" + "-"*50)
            date_match = re.search(r"clue-(\d{4}-\d{2}-\d{2})\.jpg", clue_path.name)
            if not date_match: continue
            date_str = date_match.group(1)
            dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = dt_obj.strftime("%B %d, %Y")
            player_info = get_player_info_from_image(clue_path, api_key)
            if player_info:
                scraped_data = search_and_scrape_player(player_info['name'])
                if scraped_data:
                    player_info['career_totals'] = scraped_data['career_totals']
                    player_info['yearly_war'] = scraped_data['yearly_war']
                facts = get_facts_from_gemini(player_info['name'], api_key)
                player_info['facts'] = facts
                verified_data = review_and_edit_data(player_info, project_dir)
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
        
        player_info = get_player_info_from_image(clue_image_path, api_key)
        
        if player_info:
            scraped_data = search_and_scrape_player(player_info['name'])
            if scraped_data:
                player_info['career_totals'] = scraped_data['career_totals']
                player_info['yearly_war'] = scraped_data['yearly_war']
            facts = get_facts_from_gemini(player_info['name'], api_key)
            player_info['facts'] = facts
            verified_data = review_and_edit_data(player_info, project_dir)
            generate_detail_page(verified_data, date_str, formatted_date, project_dir)
            rebuild_index_page(project_dir)
            
    print("\n🎉 All tasks completed successfully! 🎉")
