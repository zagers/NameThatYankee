# ABOUTME: Unit tests for the Fact Verifier engine.
# ABOUTME: Ensures that AI-generated claims are correctly validated against raw player data.

import pytest
from fact_verifier import verify_claims

def test_verify_claims_valid_year():
    claims = ["He played for the Yankees in 1995."]
    raw_data = {
        "yearly_war": [{"year": "1995", "display_team": "NYY"}],
        "career_totals": {},
        "transactions": [],
        "bio": ""
    }
    assert verify_claims(claims, raw_data) is True

def test_verify_claims_valid_number():
    claims = ["He had a 3.45 ERA and 115 saves."]
    raw_data = {
        "career_totals": {"ERA": "3.45", "SV": "115"},
        "yearly_war": [],
        "transactions": [],
        "bio": ""
    }
    assert verify_claims(claims, raw_data) is True

def test_verify_claims_invalid_number():
    claims = ["He hit 50 home runs."]
    raw_data = {
        "career_totals": {"HR": "12"},
        "yearly_war": [],
        "transactions": [],
        "bio": ""
    }
    assert verify_claims(claims, raw_data) is False

def test_verify_claims_with_teams_list():
    # This specifically tests the fix for the 'list' has no attribute 'split' bug
    claims = ["This player played for 3 teams."]
    raw_data = {
        "yearly_war": [
            {"year": "1960", "teams": ["NYY"], "display_team": "NYY"},
            {"year": "1961", "teams": ["BAL", "KCA"], "display_team": "TOT"},
        ],
        "career_totals": {},
        "transactions": [],
        "bio": ""
    }
    # 3 unique teams: NYY, BAL, KCA. Length of yearly_war is 2.
    # verify_claims adds the number of unique teams (3) to valid_numbers.
    assert verify_claims(claims, raw_data) is True

def test_verify_claims_with_teams_string():
    # Tests backward compatibility/robustness for string teams
    claims = ["This player played for 2 teams."]
    raw_data = {
        "yearly_war": [
            {"year": "1960", "teams": "NYY, LAD", "display_team": "TOT"},
        ],
        "career_totals": {},
        "transactions": [],
        "bio": ""
    }
    assert verify_claims(claims, raw_data) is True
