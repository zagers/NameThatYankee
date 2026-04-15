import re

def extract_metadata(html_content):
    # Regex to find <title> tag content: [Player Name] Answer - [Date] | Name That Yankee
    match = re.search(r'<title>(.*?) Answer - (.*?) \| Name That Yankee</title>', html_content)
    if match:
        player_name = match.group(1).strip()
        date = match.group(2).strip()
        return player_name, date
    return None, None
