import json
from bs4 import BeautifulSoup
from datetime import datetime
import re
from pathlib import Path

def generate_detail_page(player_data: dict, date_str: str, formatted_date: str, project_dir):
    """Generates and saves the new HTML detail page, now with a stats table and chart."""
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
