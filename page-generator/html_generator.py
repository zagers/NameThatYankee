# ABOUTME: Generates individual trivia puzzle HTML files from player data.
# ABOUTME: Applies SEO standards, canonical tags, and structured data templates.
import json
from bs4 import BeautifulSoup  # type: ignore
from datetime import datetime
import re
from pathlib import Path
from datetime import date
import html
from typing import Dict, List

def build_detail_page_html(player_data: dict, date_str: str, formatted_date: str) -> str:
    """Builds and returns the HTML string for the detail page."""
    name = player_data.get('name', 'N/A')
    nickname = player_data.get('nickname', '')
    facts = player_data.get('facts', [])
    followup_qa = player_data.get('followup_qa', [])
    career_totals_data = player_data.get('career_totals', {})
    yearly_war_data = player_data.get('yearly_war', [])
    script_run_date = date.today().strftime("%d-%b-%Y")
    
    display_name = f'{name} "{nickname}"' if nickname else name
    facts_html = "\n".join([f"                        <li>{fact}</li>" for fact in facts])

    followup_section_html = ""
    if followup_qa:
        items_html_parts: List[str] = []
        for idx, qa in enumerate(followup_qa[:3], start=1):
            question = html.escape(str(qa.get('question', '')).strip())
            answer = html.escape(str(qa.get('answer', '')).strip())
            if not question or not answer:
                continue
            item_html = f"""
                        <div class="followup-item">
                            <button class="followup-btn" data-answer="{answer}">{question}</button>
                            <div class="followup-answer" style="display:none;"></div>
                        </div>
            """
            items_html_parts.append(item_html)

        if items_html_parts:
            items_html = "\n".join(items_html_parts)
            followup_section_html = f"""
                <div class="followup-section" id="followup-section">
                    <h3>Would you like to find out more about {html.escape(name)}?</h3>
                    <div class="followup-buttons">
{items_html}
                    </div>
                </div>
            """

    # Generate Chart.js initialization script if yearly WAR data is present
    career_arc_script = ""
    if yearly_war_data:
        years = [entry['year'] for entry in yearly_war_data]
        war_data = [entry['war'] for entry in yearly_war_data]
        teams_by_year = [entry['team'] for entry in yearly_war_data]
        
        # Color mapping for common MLB teams (Yankees-centric)
        team_colors_json = json.dumps({
            "NYY": {"bg": "rgba(12, 35, 64, 0.7)", "border": "rgba(12, 35, 64, 1)", "name": "NY Yankees"},
            "BAL": {"bg": "rgba(223, 70, 27, 0.7)", "border": "rgba(223, 70, 27, 1)", "name": "Baltimore"},
            "BOS": {"bg": "rgba(189, 48, 57, 0.7)", "border": "rgba(189, 48, 57, 1)", "name": "Boston"},
            "TOR": {"bg": "rgba(19, 74, 142, 0.7)", "border": "rgba(19, 74, 142, 1)", "name": "Toronto"},
            "TBR": {"bg": "rgba(9, 44, 92, 0.7)", "border": "rgba(9, 44, 92, 1)", "name": "Tampa Bay"},
            "LAA": {"bg": "rgba(186, 0, 33, 0.7)", "border": "rgba(186, 0, 33, 1)", "name": "LA Angels"},
            "HOU": {"bg": "rgba(235, 110, 31, 0.7)", "border": "rgba(235, 110, 31, 1)", "name": "Houston"},
            "OAK": {"bg": "rgba(0, 56, 49, 0.7)", "border": "rgba(0, 56, 49, 1)", "name": "Oakland"},
            "SEA": {"bg": "rgba(0, 92, 92, 0.7)", "border": "rgba(0, 92, 92, 1)", "name": "Seattle"},
            "TEX": {"bg": "rgba(0, 50, 120, 0.7)", "border": "rgba(0, 50, 120, 1)", "name": "Texas"},
            "CHW": {"bg": "rgba(39, 37, 31, 0.7)", "border": "rgba(39, 37, 31, 1)", "name": "Chi White Sox"},
            "CLE": {"bg": "rgba(227, 24, 55, 0.7)", "border": "rgba(227, 24, 55, 1)", "name": "Cleveland"},
            "DET": {"bg": "rgba(12, 35, 64, 0.7)", "border": "rgba(12, 35, 64, 1)", "name": "Detroit"},
            "KCR": {"bg": "rgba(0, 70, 135, 0.7)", "border": "rgba(0, 70, 135, 1)", "name": "Kansas City"},
            "MIN": {"bg": "rgba(0, 43, 92, 0.7)", "border": "rgba(0, 43, 92, 1)", "name": "Minnesota"},
            "ATL": {"bg": "rgba(206, 17, 65, 0.7)", "border": "rgba(206, 17, 65, 1)", "name": "Atlanta"},
            "MIA": {"bg": "rgba(0, 163, 224, 0.7)", "border": "rgba(0, 163, 224, 1)", "name": "Miami"},
            "NYM": {"bg": "rgba(0, 45, 114, 0.7)", "border": "rgba(0, 45, 114, 1)", "name": "NY Mets"},
            "PHI": {"bg": "rgba(232, 24, 40, 0.7)", "border": "rgba(232, 24, 40, 1)", "name": "Philadelphia"},
            "WSN": {"bg": "rgba(171, 18, 41, 0.7)", "border": "rgba(171, 18, 41, 1)", "name": "Washington"},
            "CHC": {"bg": "rgba(14, 51, 134, 0.7)", "border": "rgba(14, 51, 134, 1)", "name": "Chi Cubs"},
            "CIN": {"bg": "rgba(198, 1, 31, 0.7)", "border": "rgba(198, 1, 31, 1)", "name": "Cincinnati"},
            "MIL": {"bg": "rgba(18, 40, 75, 0.7)", "border": "rgba(18, 40, 75, 1)", "name": "Milwaukee"},
            "PIT": {"bg": "rgba(255, 184, 28, 0.7)", "border": "rgba(255, 184, 28, 1)", "name": "Pittsburgh"},
            "STL": {"bg": "rgba(196, 30, 58, 0.7)", "border": "rgba(196, 30, 58, 1)", "name": "St. Louis"},
            "ARI": {"bg": "rgba(167, 25, 48, 0.7)", "border": "rgba(167, 25, 48, 1)", "name": "Arizona"},
            "COL": {"bg": "rgba(51, 0, 111, 0.7)", "border": "rgba(51, 0, 111, 1)", "name": "Colorado"},
            "LAD": {"bg": "rgba(0, 90, 156, 0.7)", "border": "rgba(0, 90, 156, 1)", "name": "LA Dodgers"},
            "SDP": {"bg": "rgba(47, 37, 32, 0.7)", "border": "rgba(47, 37, 32, 1)", "name": "San Diego"},
            "SFG": {"bg": "rgba(253, 90, 30, 0.7)", "border": "rgba(253, 90, 30, 1)", "name": "San Francisco"},
            "Total": {"bg": "rgba(128, 128, 128, 0.5)", "border": "rgba(128, 128, 128, 1)", "name": "Career Total"},
            "Default": {"bg": "rgba(150, 150, 150, 0.7)", "border": "rgba(150, 150, 150, 1)", "name": "Other Team"}
        })

        career_arc_script = f"""
        <script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.1" integrity="sha384-jb8JQMbMoBUzgWatfe6COACi2ljcDdZQ2OxczGA3bGNeWe+6DChMTBJemed7ZnvJ" crossorigin="anonymous"></script>
        <script>
            const years = {years};
            const warData = {war_data};
            const teamsByYear = {teams_by_year};
            const teamColors = {team_colors_json};

            let cumulativeTotal = 0;
            const waterfallData = [];
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
                                font: {{ size: 10 }},
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
    <title>{html.escape(display_name)} Answer - {formatted_date} | Name That Yankee</title>
    <link rel="stylesheet" href="style.css">
    <link rel="manifest" href="manifest.json">
    <link rel="shortcut icon" type="image/png" href="images/favicon.png">
    <link rel="apple-touch-icon" sizes="180x180" href="apple-touch-icon.png">
    <link rel="canonical" href="https://namethatyankeequiz.com/{date_str}">
    
    <!-- Meta tags for better social sharing -->
    <meta name="description" content="Discover the career highlights and statistics for {name}, the featured New York Yankee for the {formatted_date} trivia puzzle.">
    <meta property="og:title" content="Name That Yankee - {formatted_date}">
    <meta property="og:description" content="Can you name this New York Yankee based on their career stats?">
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="Name That Yankee">
    <meta property="og:image" content="images/clue-{date_str}.webp">
    
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="Name That Yankee - {formatted_date}">
    <meta name="twitter:description" content="Can you name this New York Yankee based on their career stats?">
    <meta name="twitter:image" content="images/clue-{date_str}.webp">
    
    <meta name="apple-mobile-web-app-title" content="NameThatYankee">

    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "Article",
      "headline": "{display_name} - Trivia Answer",
      "image": "images/answer-{date_str}.webp",
      "datePublished": "{date_str}",
      "author": {{
        "@type": "Person",
        "name": "Scott Zager"
      }},
      "publisher": {{
        "@type": "Organization",
        "name": "Name That Yankee",
        "logo": {{
          "@type": "ImageObject",
          "url": "https://namethatyankeequiz.com/apple-touch-icon.png"
        }}
      }},
      "description": "{html.escape(facts[0]) if facts else 'Daily New York Yankees trivia.'}"
    }}
    </script>
</head>
<body class="detail-page">
    <header>
        <div class="header-content">
            <a href="/" class="back-link">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
                <span>Back to Archives</span>
            </a>
            <h1>Trivia Answer</h1>
            <div style="width: 24px;"></div>
        </div>
    </header>

    <main class="container">
        <article class="answer-card">
            <div class="answer-header">
                <h2 id="player-name">{display_name}</h2>
                <p class="trivia-date">Puzzle Date: {formatted_date}</p>
            </div>

            <div class="answer-images">
                <div class="image-box">
                    <h3>The Clue</h3>
                    <img src="images/clue-{date_str}.webp" alt="Trivia clue for {display_name}" decoding="async">
                </div>
                <div class="image-box">
                    <h3>The Answer</h3>
                    <img src="images/answer-{date_str}.webp" alt="Photo of {display_name}" decoding="async">
                </div>
            </div>

            <div class="facts-section">
                <h3>Key Career Highlights</h3>
                <ul class="facts-list">
{facts_html}
                </ul>
            </div>

            <div class="chart-section">
                <h3>Career Value Arc (WAR)</h3>
                <div class="chart-container">
                    <canvas id="careerArcChart"></canvas>
                </div>
                <p class="chart-disclaimer">WAR (Wins Above Replacement) data courtesy of Baseball-Reference.</p>
            </div>

{followup_section_html}

        </article>

        <div id="quiz-data" style="display:none;">{json.dumps(player_data)}</div>
    </main>

    {career_arc_script}
    
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        const items = document.querySelectorAll('.followup-item');
        items.forEach(function(item) {{
            const btn = item.querySelector('.followup-btn');
            const answerBox = item.querySelector('.followup-answer');
            if (!btn || !answerBox) return;

            btn.addEventListener('click', function() {{
                const answer = btn.getAttribute('data-answer') || '';
                if (!answer) return;

                // Toggle visibility
                const isHidden = answerBox.style.display === 'none' || !answerBox.style.display;
                if (isHidden) {{
                    answerBox.textContent = answer;
                    answerBox.style.display = 'block';
                }} else {{
                    answerBox.style.display = 'none';
                }}
            }});
        }});
    }});
    </script>
    <footer>
		<p class="disclaimer-footer">
	        This site is an unofficial fan project and is not affiliated with the New York Yankees, Major League Baseball, or the YES Network. All trademarks and copyrights belong to their respective owners.
	    </p>
        <p id="last-updated">Last Updated: {script_run_date}</p>
        <p class="copyright">
            <a href="https://namethatyankeequiz.com">Name That Yankee Quiz</a> © 2026 by 
            <a href="https://github.com/zagers/NameThatYankee">Scott Zager</a> is licensed under 
            <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/">CC BY-NC-SA 4.0</a>
            <img src="https://mirrors.creativecommons.org/presskit/icons/cc.svg" alt="CC" style="max-width: 1em;max-height:1em;margin-left: .2em;">
            <img src="https://mirrors.creativecommons.org/presskit/icons/by.svg" alt="BY" style="max-width: 1em;max-height:1em;margin-left: .2em;">
            <img src="https://mirrors.creativecommons.org/presskit/icons/nc.svg" alt="NC" style="max-width: 1em;max-height:1em;margin-left: .2em;">
            <img src="https://mirrors.creativecommons.org/presskit/icons/sa.svg" alt="SA" style="max-width: 1em;max-height:1em;margin-left: .2em;">
        </p>
    </footer>    
</body>
</html>"""
    
    return template

def generate_detail_page(player_data: dict, date_str: str, formatted_date: str, project_dir: Path):
    """Generates and saves the new HTML detail page, now with quiz and search data."""
    print(f"  📄 Generating detail page for {date_str}...")
    
    html_content = build_detail_page_html(player_data, date_str, formatted_date)
    
    file_path = project_dir / f"{date_str}.html"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"  ✅ Detail page saved successfully.")

def generate_gallery_snippet(i, date_str, formatted_date, search_terms):
    """
    Generates a single gallery card snippet with LCP-aware image loading.
    """
    # Only lazy load items below the fold (index > 5)
    loading_attr = 'loading="lazy"' if i > 5 else ''
    
    return f"""<div class="gallery-container">
                <a href="{date_str}" class="gallery-item">
                    <img src="images/clue-{date_str}.webp" alt="Name that Yankee trivia card from {date_str}" {loading_attr} decoding="async">
                </a>
                <div class="p-4">
                    <p class="gallery-date">Trivia Date: {formatted_date}</p>
                    <div class="action-links">
                        <a href="{date_str}" class="action-link reveal-link">
                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
                            <span>Reveal</span>
                        </a>
                        <a href="quiz?date={date_str}" class="action-link quiz-link" rel="nofollow">
                            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/></svg>
                            <span>Quiz</span>
                        </a>
                    </div>
                </div>
            </div>"""

def rebuild_index_page(project_dir: Path):
    print("\n✍️ Rebuilding and re-sorting index.html from all available clues...")
    
    index_path = project_dir / "index.html"
    images_dir = project_dir / "images"
    
    # Get all clue files, sorted by date DESC
    clue_files = sorted(
        images_dir.glob("clue-????-??-??.webp"),
        key=lambda f: f.name.replace('clue-', '').replace('.webp', ''),
        reverse=True
    )
    
    gallery_tiles = []
    stats_summary = []
    
    for i, clue_file in enumerate(clue_files):
        date_str = clue_file.name.replace('clue-', '').replace('.webp', '')
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%B %d, %Y")
            
            # Load player name from detail page for search optimization
            player_name = ""
            detail_path = project_dir / f"{date_str}.html"
            if detail_path.exists():
                with open(detail_path, 'r', encoding='utf-8') as df:
                    d_soup = BeautifulSoup(df, 'html.parser')
                    quiz_data_el = d_soup.select_one('#quiz-data')
                    if quiz_data_el:
                        try:
                            player_data = json.loads(quiz_data_el.textContent)
                            player_name = player_data.get('name', '')
                            
                            # Build search tokens
                            teams = [entry['team'] for entry in player_data.get('yearly_war', [])]
                            years = [entry['year'] for entry in player_data.get('yearly_war', [])]
                            
                            stats_summary.append({
                                "date": date_str,
                                "name": player_name,
                                "nickname": player_data.get('nickname', ''),
                                "teams": list(set(teams)),
                                "years": list(set(years))
                            })
                        except (json.JSONDecodeError, AttributeError):
                            pass

            snippet = generate_gallery_snippet(i, date_str, formatted_date, player_name)
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
    
    # Update the 'Last Updated' timestamp in the footer of all core pages
    script_run_date = date.today().strftime("%d-%b-%Y")
    core_files = ['index.html', 'quiz.html', 'analytics.html', 'instructions.html']
    
    for filename in core_files:
        file_path = project_dir / filename
        if not file_path.exists():
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            f_soup = BeautifulSoup(f, 'html.parser')
            
        update_p = f_soup.select_one('footer #last-updated')
        if update_p:
            update_p.string = f"Last Updated: {script_run_date}"
            
            # If we're updating index.html, we also need to update the copyright while we're at it
            if filename == 'index.html':
                copyright_p = f_soup.select_one('footer .copyright')
                if copyright_p:
                    copyright_p.clear()
                    new_copyright_html = f"""<a href="https://namethatyankeequiz.com">Name That Yankee Quiz</a> © 2026 by 
                        <a href="https://github.com/zagers/NameThatYankee">Scott Zager</a> is licensed under 
                        <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/">CC BY-NC-SA 4.0</a>
                        <img src="https://mirrors.creativecommons.org/presskit/icons/cc.svg" alt="CC" style="max-width: 1em;max-height:1em;margin-left: .2em;">
                        <img src="https://mirrors.creativecommons.org/presskit/icons/by.svg" alt="BY" style="max-width: 1em;max-height:1em;margin-left: .2em;">
                        <img src="https://mirrors.creativecommons.org/presskit/icons/nc.svg" alt="NC" style="max-width: 1em;max-height:1em;margin-left: .2em;">
                        <img src="https://mirrors.creativecommons.org/presskit/icons/sa.svg" alt="SA" style="max-width: 1em;max-height:1em;margin-left: .2em;">"""
                    copyright_p.append(BeautifulSoup(new_copyright_html, 'html.parser'))

                # Update index chevron (since we're already processing index.html)
                index_chevron = f_soup.select_one('#score-display .chevron-icon')
                if index_chevron:
                    index_chevron['aria-hidden'] = 'true'

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f_soup.prettify())
            print(f"✅ Footer timestamp updated for {filename}.")
        else:
            print(f"⚠️ Warning: Could not find footer element with id='last-updated' in {filename}.")
        
    print("✅ index.html rebuilt successfully.")

    # Save the consolidated stats
    stats_path = project_dir / "stats_summary.json"
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats_summary, f, indent=2)
    print(f"✅ stats_summary.json generated with {len(stats_summary)} entries.")
