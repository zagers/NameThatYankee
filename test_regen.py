import sys
from unittest.mock import patch
import os

sys.path.append(os.path.join(os.getcwd(), 'page-generator'))

def mock_input(prompt):
    if "Website project folder path" in prompt:
        return ""
    elif "Enter a date" in prompt:
        return "2026-05-26"
    elif "Proceed?" in prompt:
        return "Y"
    return ""

with patch('builtins.input', mock_input):
    from main import main
    sys.argv = ['main.py', '--regenerate-facts', '--automated']
    main()
