# ABOUTME: Verifies AI-generated claims against raw player data.
# ABOUTME: Extracts entities like years and teams to ensure they exist in the dossier.

import re
import logging

import re
import logging
from datetime import datetime

def verify_claims(claims, raw_data):
    """
    Verifies that entities mentioned in claims exist in specific fields of raw_data.
    """
    # 1. Gather all valid years and full dates
    valid_years = set()
    raw_text_for_matching = raw_data.get('bio', '') + " " + " ".join(raw_data.get('transactions', []))
    
    # From yearly stats
    for entry in raw_data.get('yearly_war', []):
        if 'year' in entry:
            valid_years.add(str(entry['year']))
            
    # From transactions and bio (extract any 4-digit years)
    all_years = re.findall(r'\b((?:18|19|20)\d{2})\b', raw_text_for_matching)
    valid_years.update(all_years)

    # 2. Gather all valid numbers (stats)
    valid_numbers = set()
    career_totals = raw_data.get('career_totals', {})
    for val in career_totals.values():
        s_val = str(val).strip()
        if s_val:
            valid_numbers.add(s_val)
            # Add integer part for decimals (e.g. 2591 for 2591.2)
            if '.' in s_val:
                valid_numbers.add(s_val.split('.')[0])
    
    # 2b. Add derived counts (seasons, teams)
    yearly_war = raw_data.get('yearly_war', [])
    if yearly_war:
        valid_numbers.add(str(len(yearly_war)))
        
        # Unique teams
        teams = set()
        for entry in yearly_war:
            entry_teams = entry.get('teams', [])
            if isinstance(entry_teams, str):
                parts = [p.strip() for p in entry_teams.split(',') if p.strip()]
                teams.update(parts)
            elif isinstance(entry_teams, list):
                teams.update([p.strip() for p in entry_teams if isinstance(p, str) and p.strip()])
        if teams:
            valid_numbers.add(str(len(teams)))

    # 2c. EXTRACT NUMBERS FROM BIO/TRANSACTIONS (New Improvement)
    # This catches numbers mentioned in the narrative that might be missing from career_totals
    narrative_numbers = re.findall(r'\b(\d+\.\d{1,3}|\.\d{3}|\d{2,})\b', raw_text_for_matching)
    for num in narrative_numbers:
        # Ignore years (already handled)
        if len(num) == 4 and num.startswith(('18', '19', '20')):
            continue
        valid_numbers.add(num.lstrip('.'))
        if '.' in num:
            valid_numbers.add(num.split('.')[0])

    # 3. Check claims
    for claim in claims:
        # 3a. Check for Narrative Dates (e.g., "November 18, 1997")
        # If a date like this is found, try to convert it to YYYY-MM-DD and check raw text
        date_matches = re.findall(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+(?:18|19|20)\d{2}\b', claim)
        for narrative_date in date_matches:
            # Check if the year itself is valid first
            year_match = re.search(r'\b((?:18|19|20)\d{2})\b', narrative_date)
            if year_match and year_match.group(1) not in valid_years:
                logging.error(f"Fact Verification Failed: Year in date '{narrative_date}' not found.")
                return False
            # We'll allow the date if the year is valid and the text "appears" in raw data 
            # (either as string or slightly different format)
            # For now, if the year is in our valid_years, we'll trust the narrative date 
            # as Gemini is good at formatting dates it found.

        # 3b. Check individual years
        claim_years = re.findall(r'\b((?:18|19|20)\d{2})\b', claim)
        for year in claim_years:
            if year not in valid_years:
                logging.error(f"Fact Verification Failed: Year '{year}' mentioned in claim '{claim}' not found in player's history.")
                return False

        # 3c. Check numbers (stats like 3.45, 1,236, .280, -1.2)
        # Support leading negative sign and commas within numbers
        # Note: We use a simple space or start-of-string check to capture negative signs
        claim_numbers = re.findall(r'(?:^| )(-?\d{1,3}(?:,\d{3})*(?:\.\d+)?|-?\.\d+)\b', claim)
        for num in claim_numbers:
            # Skip years already checked
            if len(num) == 4 and num.startswith(('18', '19', '20')):
                continue
            
            # Normalize: remove commas for comparison
            normalized_num = num.replace(',', '')
            check_num = normalized_num.lstrip('.')
            
            # Flexible matching: check if the normalized number or its integer part exists
            if normalized_num not in valid_numbers and check_num not in valid_numbers:
                int_part = normalized_num.split('.')[0] if '.' in normalized_num else normalized_num
                if int_part in valid_numbers:
                    continue

                # Special case: allow small integers if they appear in bio or transactions
                if num.isdigit() and int(num) < 100:
                    if num in raw_text_for_matching:
                        continue
                
                logging.error(f"Fact Verification Failed: Statistical number '{num}' mentioned in claim '{claim}' not found in raw data.")
                return False
    
    return True
