# ABOUTME: Verifies AI-generated claims against raw player data.
# ABOUTME: Extracts entities like years and teams to ensure they exist in the dossier.

import re
import logging

def verify_claims(claims, raw_data):
    """
    Verifies that entities mentioned in claims exist in specific fields of raw_data.
    """
    # 1. Gather all valid years
    valid_years = set()
    
    # From yearly stats
    for entry in raw_data.get('yearly_war', []):
        if 'year' in entry:
            valid_years.add(str(entry['year']))
            
    # From transactions (extract any 4-digit years)
    for trans in raw_data.get('transactions', []):
        trans_years = re.findall(r'\b((?:18|19|20)\d{2})\b', trans)
        valid_years.update(trans_years)
        
    # From bio (extract any 4-digit years)
    bio = raw_data.get('bio', '')
    bio_years = re.findall(r'\b((?:18|19|20)\d{2})\b', bio)
    valid_years.update(bio_years)

    # 2. Gather all valid numbers (stats)
    valid_numbers = set()
    career_totals = raw_data.get('career_totals', {})
    for val in career_totals.values():
        # Normalize to string and remove potential leading dots or commas
        s_val = str(val).strip().lstrip('.')
        if s_val:
            valid_numbers.add(s_val)
            # Also add with the dot if it was there (e.g. .280)
            if str(val).startswith('.'):
                valid_numbers.add(str(val))

    # 3. Check claims
    for claim in claims:
        # Check years
        claim_years = re.findall(r'\b((?:18|19|20)\d{2})\b', claim)
        for year in claim_years:
            if year not in valid_years:
                logging.error(f"Fact Verification Failed: Year '{year}' mentioned in claim '{claim}' not found in player's history.")
                return False

        # Check numbers (stats like 3.45, 115, .280)
        # We look for decimals or numbers > 10 (to avoid common small numbers like 1, 2, 3)
        claim_numbers = re.findall(r'\b(\d+\.\d{2,3}|\.\d{3}|\d{2,})\b', claim)
        for num in claim_numbers:
            # Skip years already checked
            if len(num) == 4 and num.startswith(('18', '19', '20')):
                continue
            
            # Remove leading dot for comparison if necessary
            check_num = num.lstrip('.')
            if check_num not in valid_numbers and num not in valid_numbers:
                # Special case: allow small integers if they appear in bio text (e.g. "3 pickoffs")
                if num.isdigit() and int(num) < 100:
                    if num in bio:
                        continue
                
                logging.error(f"Fact Verification Failed: Statistical number '{num}' mentioned in claim '{claim}' not found in raw data.")
                return False
    
    return True
