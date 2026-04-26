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
    
    # Escape name and nickname for HTML safety
    display_name = html.escape(f'{name} "{nickname}"' if nickname else name)
    facts_html = "\n".join([f"                        <li>{fact}</li>" for fact in facts])

    # Generate career totals table rows with consistent indentation
    stats_rows_html = ""
    for label, val in career_totals_data.items():
        stats_rows_html += f"""
                <div class="stat-item">
                    <span class="stat-label">{label}</span>
                    <span class="stat-value">{val}</span>
                </div>"""

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
        years = [entry.get('year', 'N/A') for entry in yearly_war_data]
        war_data = [entry.get('war', 0.0) for entry in yearly_war_data]
        teams_by_year = [entry.get('team', 'Default') for entry in yearly_war_data]
        
        career_arc_script = f"""
        <script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.1" integrity="sha384-jb8JQMbMoBUzgWatfe6COACi2ljcDdZQ2OxczGA3bGNeWe+6DChMTBJemed7ZnvJ" crossorigin="anonymous"></script>
        <script src="js/team_colors.js"></script>
        <script>
            const years = {years};
            const warData = {war_data};
            const teamsByYear = {teams_by_year};
            const teamColors = window.TEAM_COLORS;

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
    <meta property="og:image" content="https://namethatyankeequiz.com/images/clue-{date_str}.webp">
    
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="Name That Yankee - {formatted_date}">
    <meta name="twitter:description" content="Can you name this New York Yankee based on their career stats?">
    <meta name="twitter:image" content="https://namethatyankeequiz.com/images/clue-{date_str}.webp">
    
    <meta name="apple-mobile-web-app-title" content="NameThatYankee">

    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "Article",
      "headline": "Name That Yankee Answer for {formatted_date}",
      "image": "https://namethatyankeequiz.com/images/answer-{date_str}.webp",
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
      "description": {json.dumps(f"Discover the career highlights and statistics for {name}, the featured New York Yankee for the {formatted_date} trivia puzzle.")}
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
            <h1>The answer for {formatted_date} is...</h1>
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

            <div class="stats-table-container">
                <h3>Career Statistics</h3>
                <div class="stats-grid">
{stats_rows_html}
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

        <div id="quiz-data" style="display:none;">{json.dumps({**player_data, 'answer': player_data.get('answer', name), 'hints': player_data.get('hints', facts)})}</div>
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

def generate_gallery_snippet(i, date_str, formatted_date):
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
    if not index_path.exists():
        print(f"⚠️  Warning: index.html not found in {project_dir}. Skipping rebuild.")
        return

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
            teams = []
            years = []
            nickname = ""
            
            detail_path = project_dir / f"{date_str}.html"
            if detail_path.exists():
                with open(detail_path, 'r', encoding='utf-8') as df:
                    d_soup = BeautifulSoup(df, 'html.parser')
                    # Try current standard #quiz-data first, fall back to legacy #search-data
                    quiz_data_el = d_soup.select_one('#quiz-data') or d_soup.select_one('#search-data')
                    if quiz_data_el:
                        try:
                            raw_json = quiz_data_el.get_text().strip()
                            if raw_json:
                                player_data = json.loads(raw_json)
                                p_name = player_data.get('name', '')
                                if not p_name:
                                    h2_el = d_soup.select_one('h2')
                                    p_name = h2_el.get_text().strip() if h2_el else ""
                                
                                if p_name:
                                    player_name = p_name

                                nickname = player_data.get('nickname', '')

                                # Extract teams and years for search tokens
                                teams = player_data.get('teams', [])
                                if not teams:
                                    teams = [entry.get('team', '') for entry in player_data.get('yearly_war', []) if entry.get('team')]
                                
                                years = player_data.get('years', [])
                                if not years:
                                    years = [entry.get('year', '') for entry in player_data.get('yearly_war', []) if entry.get('year')]
                        except (json.JSONDecodeError, AttributeError):
                            pass

            stats_summary.append({
                "date": date_str,
                "name": player_name,
                "nickname": nickname,
                "teams": list(set(teams)),
                "years": list(set(years))
            })

            # Snippet MUST be generated and appended OUTSIDE of the detail_path check
            snippet = generate_gallery_snippet(i, date_str, formatted_date)
            gallery_tiles.append(snippet)
        except ValueError:
            print(f"⚠️  Warning: Skipping file with invalid date format: {clue_file.name}")
    
    # Update the 'Last Updated' timestamp in the footer of all core pages
    script_run_date = date.today().strftime("%d-%b-%Y")
    core_files = ['index.html', 'quiz.html', 'analytics.html', 'instructions.html']
    
    for filename in core_files:
        file_path = project_dir / filename
        if not file_path.exists():
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f_soup = BeautifulSoup(f, 'html.parser')
                
            # If we're processing index.html, we ALSO need to update the gallery
            is_index = (filename == 'index.html')
            if is_index:
                gallery_div = f_soup.select_one('.gallery')
                if gallery_div:
                    gallery_div.clear()
                    for tile_html in gallery_tiles:
                        tile_soup = BeautifulSoup(tile_html, 'html.parser')
                        gallery_div.append(tile_soup)
                        gallery_div.append('\n')
                else:
                    print(f"❌ Could not find insertion point in {filename}.")

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

                # Update index chevron
                index_chevron = f_soup.select_one('#score-display .chevron-icon')
                if index_chevron:
                    index_chevron['aria-hidden'] = 'true'

            # Update footer timestamp - be more robust with selectors
            update_p = f_soup.select_one('#last-updated')
            if update_p:
                update_p.string = f"Last Updated: {script_run_date}"
                
            # ALWAYS write the file if we're in this block, ensuring index.html gallery is saved
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f_soup.prettify())
            
            if update_p:
                print(f"✅ Footer timestamp updated for {filename}.")
            elif is_index:
                print(f"✅ index.html updated (gallery refreshed, but footer timestamp element not found).")
        except Exception as e:
            print(f"⚠️ Warning: Failed to update {filename}: {e}")
        
    print("✅ index.html rebuilt successfully.")

    # Save the consolidated stats
    stats_path = project_dir / "stats_summary.json"
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats_summary, f, indent=2)
    print(f"✅ stats_summary.json generated with {len(stats_summary)} entries.")
