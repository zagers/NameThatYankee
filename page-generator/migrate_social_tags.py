#!/usr/bin/env python3
"""
ABOUTME: Migrates historical trivia puzzle pages to use updated social tags and branding.
ABOUTME: Updates og:description, twitter:description, og:image, twitter:image, and JSON-LD.
"""

import os
import glob
from bs4 import BeautifulSoup
import json

def migrate_file(file_path):
    print(f"Processing {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    new_desc = "Check out this Name That Yankee puzzle! Can you name this player based on their career stats?"
    new_image = "https://namethatyankeequiz.com/images/social-card.webp"
    
    # Update og:description
    og_desc = soup.find("meta", attrs={"property": "og:description"})
    if og_desc:
        og_desc["content"] = new_desc
        
    # Update twitter:description
    twitter_desc = soup.find("meta", attrs={"name": "twitter:description"})
    if twitter_desc:
        twitter_desc["content"] = new_desc
        
    # Update og:image
    og_image = soup.find("meta", attrs={"property": "og:image"})
    if og_image:
        og_image["content"] = new_image
        
    # Update twitter:image
    twitter_image = soup.find("meta", attrs={"name": "twitter:image"})
    if twitter_image:
        twitter_image["content"] = new_image
        
    # Update JSON-LD
    json_ld_script = soup.find("script", type="application/ld+json")
    if json_ld_script:
        try:
            data = json.loads(json_ld_script.string)
            if "image" in data:
                data["image"] = new_image
                # Prettify JSON-LD output
                json_ld_script.string = json.dumps(data, indent=2)
        except Exception as e:
            print(f"Error updating JSON-LD in {file_path}: {e}")

    # Write back the file
    # We use prettify() only if we want to reformat everything, 
    # but the instruction doesn't say to reformat.
    # However, BeautifulSoup's str(soup) might change some formatting.
    # Let's try to keep it as close as possible.
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))

def main():
    # Root directory is one level up from page-generator
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    pattern = os.path.join(root_dir, "202[0-9]-[0-9][0-9]-[0-9][0-9].html")
    files = glob.glob(pattern)
    
    print(f"Found {len(files)} files to migrate.")
    for file_path in files:
        migrate_file(file_path)
    print("Migration complete.")

if __name__ == "__main__":
    main()
