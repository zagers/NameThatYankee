import re
import os
import glob
import argparse

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

def normalize_links(html_content):
    # Replace href="YYYY-MM-DD.html" with href="YYYY-MM-DD"
    # Matches href="2025-03-29.html" -> href="2025-03-29"
    pattern = r'href="(\d{4}-\d{2}-\d{2})\.html"'
    return re.sub(pattern, r'href="\1"', html_content)

def process_file(file_path, dry_run=True):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    player_name, date = extract_metadata(content)
    if not player_name or not date:
        print(f"Skipping {file_path}: Metadata not found")
        return
    
    new_content = scrub_and_inject(content, player_name, date)
    new_content = normalize_links(new_content)
    
    if content != new_content:
        if dry_run:
            print(f"[DRY RUN] Would update {file_path}")
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated {file_path}")

def main():
    parser = argparse.ArgumentParser(description="SEO Cleanup Utility")
    parser.add_argument("--no-dry-run", action="store_false", dest="dry_run", help="Apply changes")
    parser.set_defaults(dry_run=True)
    args = parser.parse_args()
    
    # Find YYYY-MM-DD.html files in the current root
    html_files = glob.glob("????-??-??.html")
    for file_path in html_files:
        process_file(file_path, args.dry_run)

if __name__ == "__main__":
    main()
