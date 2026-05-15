# ABOUTME: Verifies AI-generated claims against raw player data.
# ABOUTME: Extracts entities like years and teams to ensure they exist in the dossier.

import re
import logging

def verify_claims(claims, raw_data):
    """
    Verifies that entities mentioned in claims exist in raw_data.
    """
    # Use string representation of raw_data for simple existence check
    # We also look at specific fields for better accuracy
    all_raw_text = str(raw_data)
    
    for claim in claims:
        # 1. Verify 4-digit years (1800-2099)
        years = re.findall(r'\b((?:18|19|20)\d{2})\b', claim)
        for year in years:
            if year not in all_raw_text:
                logging.error(f"Fact Verification Failed: Year '{year}' mentioned in claim '{claim}' not found in raw data.")
                return False

        # 2. Verify common baseball numbers (averages like .280, ERA like 3.45, counts like 115)
        # Avoid matching small common numbers like 1, 2, 3 unless they are years
        numbers = re.findall(r'\b(\d+\.\d{2,3}|\d{2,})\b', claim)
        for num in numbers:
            # Skip years already checked
            if len(num) == 4 and num.startswith(('18', '19', '20')):
                continue
            if num not in all_raw_text:
                logging.error(f"Fact Verification Failed: Number '{num}' mentioned in claim '{claim}' not found in raw data.")
                return False

        # 3. Verify Team Names (subset of common teams for speed)
        # This is a bit harder, but we can check if any word starts with uppercase
        # and see if it's in the raw data's team lists or bio.
        # For now, let's just stick to years and numbers as they are the primary source of errors.
    
    return True
