# ABOUTME: Migrates existing answer pages to include static quiz pages and JSON-LD schemas.
# ABOUTME: Extracts player data from existing HTML files and uses html_generator to rebuild them.
import sys
import os
import json
import re
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup

# Add page-generator to path to import html_generator
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'page-generator')))
import html_generator

def extract_player_data(soup):
    player_data = {}
    
    # 1. Name and Nickname from h2
    h2 = soup.find('h2')
    if h2:
        full_text = h2.get_text(strip=True)
        if '"' in full_text:
            parts = full_text.split('"')
            player_data['name'] = parts[0].strip()
            player_data['nickname'] = parts[1].strip()
        else:
            player_data['name'] = full_text
            player_data['nickname'] = ""
    
    # 2. Facts and Answer from quiz-data (easiest)
    quiz_data_div = soup.find('div', id='quiz-data')
    if quiz_data_div:
        try:
            quiz_data = json.loads(quiz_data_div.string)
            player_data['name'] = quiz_data.get('answer', player_data.get('name', ''))
            player_data['facts'] = quiz_data.get('hints', [])
        except Exception:
            player_data['facts'] = []
    else:
        # Fallback to ul
        facts_ul = soup.find('div', class_='player-info').find('ul')
        if facts_ul:
            player_data['facts'] = [li.get_text(strip=True) for li in facts_ul.find_all('li')]
        else:
            player_data['facts'] = []

    # 3. Followup QA
    followup_qa = []
    followup_items = soup.find_all('div', class_='followup-item')
    for item in followup_items:
        btn = item.find('button', class_='followup-btn')
        if btn:
            question = btn.get_text(strip=True)
            answer = btn.get('data-answer', '')
            followup_qa.append({'question': question, 'answer': answer})
    player_data['followup_qa'] = followup_qa

    # 4. Career Totals
    career_totals = {}
    stats_container = soup.find('div', class_='stats-table-container')
    if stats_container:
        table = stats_container.find('table')
        if table:
            headers = [th.get_text(strip=True) for th in table.find_all('th')]
            values = [td.get_text(strip=True) for td in table.find_all('td')]
            career_totals = dict(zip(headers, values))
    player_data['career_totals'] = career_totals

    # 5. Yearly WAR from script
    yearly_war = []
    scripts = soup.find_all('script')
    for script in scripts:
        content = script.string
        if content and 'const years =' in content and 'const warData =' in content:
            try:
                years_match = re.search(r'const years = (\[.*?\]);', content)
                war_match = re.search(r'const warData = (\[.*?\]);', content)
                teams_match = re.search(r'const teamsByYear = (\[.*?\]);', content)
                
                if years_match and war_match and teams_match:
                    years = json.loads(years_match.group(1))
                    wars = json.loads(war_match.group(1))
                    teams = json.loads(teams_match.group(1))
                    
                    for y, w, t in zip(years, wars, teams):
                        yearly_war.append({
                            'year': y,
                            'war': float(w),
                            'display_team': t,
                            'teams': [t] # Minimal fallback
                        })
                break
            except Exception as e:
                print(f"Error parsing script data: {e}")
    player_data['yearly_war'] = yearly_war
    
    return player_data

def main():
    project_dir = Path.cwd()
    html_files = sorted(project_dir.glob('202[56]-*.html'))
    
    # Filter out -quiz.html if any already exist
    html_files = [f for f in html_files if not f.name.endswith('-quiz.html')]
    
    print(f"Found {len(html_files)} files to migrate.")
    
    count = 0
    for file_path in html_files:
        date_str = file_path.stem # e.g. 2025-03-29
        
        # Skip if it's not a date format
        if not re.match(r'\d{4}-\d{2}-\d{2}', date_str):
            continue
            
        try:
            dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = dt_obj.strftime("%B %d, %Y")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')
            
            player_data = extract_player_data(soup)
            
            # Use html_generator to rebuild the detail page and create the quiz page
            html_generator.generate_detail_page(player_data, date_str, formatted_date, project_dir)
            count += 1
            
        except Exception as e:
            print(f"Failed to process {file_path.name}: {e}")

    print(f"\nMigration complete. Processed {count} files.")
    
    # Rebuild index.html to ensure all links are updated (if needed)
    print("Rebuilding index.html...")
    html_generator.rebuild_index_page(project_dir)

if __name__ == "__main__":
    main()
