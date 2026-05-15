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

def test_verify_claims_invalid_year():
    claims = ["He played for the Yankees in 1980."]
    raw_data = {
        "yearly_war": [{"year": "1995", "display_team": "NYY"}],
        "career_totals": {},
        "transactions": [],
        "bio": ""
    }
    assert verify_claims(claims, raw_data) is False
