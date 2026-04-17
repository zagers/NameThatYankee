# ABOUTME: Performs systematic metadata cleanup on historical puzzle files.
# ABOUTME: Normalizes internal links and canonical URLs for search optimization.
import re
import os
import glob
import argparse
from bs4 import BeautifulSoup

def extract_metadata(soup, date_stem=None):
    """
    Extract player name and date from the BeautifulSoup object.
    Try to use date_stem if provided, otherwise extract from title.
    Player name: Try <title>, then <h2> in .header-content.
    """
    date = date_stem
    title_tag = soup.title
    title_text = title_tag.get_text() if title_tag else ""
    
    # If date not provided, try to extract from title
    if not date and title_text:
        # Match "Babe Ruth Answer - 2025-03-29 | Name That Yankee"
        match = re.search(r'Answer - \s*(\d{4}-\d{2}-\d{2})', title_text)
        if match:
            date = match.group(1).strip()
        else:
            # Match "Answer for 2026-03-05 | Name That Yankee"
            match = re.search(r'Answer for (\d{4}-\d{2}-\d{2})', title_text)
            if match:
                date = match.group(1).strip()

    player_name = None
    if title_text:
        # Try to extract name from title: "[Player Name] Answer - [Date] | Name That Yankee"
        match = re.search(r'(.*?)\s*Answer -', title_text, re.DOTALL)
        if match:
            player_name = match.group(1).strip()
            # Clean up multiline/extra spaces
            player_name = " ".join(player_name.split())

    if not player_name or player_name.lower() == "answer for":
        # Try <h2> in .header-content
        header_content = soup.find(class_='header-content')
        if header_content:
            h2 = header_content.find('h2')
            if h2:
                player_name = h2.get_text(strip=True)
        
        # Fallback to any <h2> if not found in .header-content
        if not player_name:
            h2 = soup.find('h2')
            if h2:
                player_name = h2.get_text(strip=True)

    return player_name, date

def scrub_and_inject(soup, player_name, date):
    """
    Remove existing description and canonical tags and inject updated ones.
    """
    # Remove existing description and canonical tags
    for tag in soup.find_all('meta', attrs={'name': 'description'}):
        tag.decompose()
    for tag in soup.find_all('link', attrs={'rel': 'canonical'}):
        tag.decompose()
    
    # Create metadata tags
    new_canonical = soup.new_tag('link', rel='canonical', href=f'https://namethatyankeequiz.com/{date}')
    description_content = f'Discover the career highlights and statistics for {player_name}, the featured New York Yankee for the {date} trivia puzzle.'
    new_description = soup.new_tag('meta', attrs={'name': 'description', 'content': description_content})
    
    # Inject into head
    if soup.head:
        # Find viewport tag to inject after it
        viewport = soup.head.find('meta', attrs={'name': 'viewport'})
        if viewport:
            viewport.insert_after(new_canonical)
            new_canonical.insert_after(new_description)
        else:
            # Fallback to appending to head
            soup.head.append(new_canonical)
            soup.head.append(new_description)
            
    return soup

def normalize_links(soup):
    """
    Normalize internal <a> links to be extensionless.
    """
    for a in soup.find_all('a', href=True):
        href = a['href']
        # Replace .html with extensionless for internal links
        # We only target files that look like internal pages (date format or index.html)
        if href.endswith('.html'):
            # Only replace if it doesn't look like an external link (though those usually don't end in .html)
            if not href.startswith(('http://', 'https://')):
                a['href'] = href.replace('.html', '')
    return soup

def process_file(file_path, dry_run=True):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    date_stem = os.path.basename(file_path).replace('.html', '')
    
    player_name, date = extract_metadata(soup, date_stem)
    if not player_name or not date:
        print(f"Skipping {file_path}: Metadata not found")
        return
    
    soup = scrub_and_inject(soup, player_name, date)
    soup = normalize_links(soup)
    
    # Use str(soup) for the new content. BeautifulSoup might reformat slightly.
    new_content = str(soup)
    
    if content != new_content:
        if dry_run:
            print(f"[DRY RUN] Would update {file_path} (Player: {player_name}, Date: {date})")
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated {file_path} (Player: {player_name}, Date: {date})")

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
