import re

def extract_metadata(html_content):
    # Regex to find <title> tag content: [Player Name] Answer - [Date] | Name That Yankee
    match = re.search(r'<title>(.*?) Answer - (.*?) \| Name That Yankee</title>', html_content)
    if match:
        player_name = match.group(1).strip()
        date = match.group(2).strip()
        return player_name, date
    return None, None

def scrub_and_inject(html_content, player_name, date):
    # Remove existing description and canonical tags
    html_content = re.sub(r'\s*<meta name="description" content=".*?">', '', html_content)
    html_content = re.sub(r'\s*<link rel="canonical" href=".*?">', '', html_content)
    
    # Standardized tags
    canonical_tag = f'\n    <link rel="canonical" href="https://namethatyankeequiz.com/{date}">'
    description_tag = f'\n    <meta name="description" content="Discover the career highlights and statistics for {player_name}, the featured New York Yankee for the {date} trivia puzzle.">'
    
    # Inject after viewport tag
    viewport_pattern = r'(<meta name="viewport" content=".*?">)'
    if re.search(viewport_pattern, html_content):
        html_content = re.sub(viewport_pattern, r'\1' + canonical_tag + description_tag, html_content)
        
    return html_content
