import sys
import os
from pathlib import Path

# Provide access to the `page-generator` python modules during tests
PROJECT_ROOT = Path(__file__).parent.parent
PAGE_GEN_DIR = PROJECT_ROOT / "page-generator"

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PAGE_GEN_DIR))
