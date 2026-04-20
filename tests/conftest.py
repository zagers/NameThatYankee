import sys
import os
import subprocess
import requests
import time
import pytest
from pathlib import Path

# Provide access to the `page-generator` python modules during tests
PROJECT_ROOT = Path(__file__).parent.parent
PAGE_GEN_DIR = PROJECT_ROOT / "page-generator"
TEST_FIXTURE_DIR = PROJECT_ROOT / "tests" / "fixtures" / "www"
BASE_URL = "http://localhost:8001/"

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PAGE_GEN_DIR))

# --- Test Setup (Fixture) ---
@pytest.fixture(scope="session", autouse=True)
def check_web_server():
    """Starts the web server before running tests and stops it after."""
    import socket
    
    # Check if port is already in use
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 8001))
    sock.close()
    
    # Start the server using our custom serve.py which supports clean URLs
    server_process = subprocess.Popen(
        ["python3", str(PROJECT_ROOT / "serve.py")],
        env={**os.environ, "PORT": "8001", "DIRECTORY": str(TEST_FIXTURE_DIR)},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait up to 15 seconds for the server to become responsive
    for _ in range(30):
        try:
            response = requests.get(BASE_URL, timeout=1)
            if response.status_code == 200:
                print(f"\n✅  Web server running at {BASE_URL}")
                break
        except requests.exceptions.RequestException:
            pass
        time.sleep(0.5)
    else:
        server_process.kill()
        pytest.fail(f"❌  Web server failed to start at {BASE_URL}")

    yield

    server_process.terminate()
    try:
        server_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        server_process.kill()
    print(f"\n🛑  Web server at {BASE_URL} stopped.")
