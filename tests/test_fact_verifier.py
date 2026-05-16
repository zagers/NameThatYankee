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
