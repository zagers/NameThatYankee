# ABOUTME: Global pytest configuration and shared fixtures for the Name That Yankee test suite.
# ABOUTME: Manages the local web server lifecycle for E2E and integration tests.
import sys
import os
import subprocess
import requests
import time
import pytest
import socket
from pathlib import Path
from tests.test_config import PROJECT_ROOT, TEST_FIXTURE_DIR, BASE_URL

# Provide access to the `page-generator` python modules during tests
PAGE_GEN_DIR = PROJECT_ROOT / "page-generator"

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PAGE_GEN_DIR))

# --- Test Setup (Fixture) ---
@pytest.fixture(scope="session", autouse=True)
def check_web_server():
    """Starts the web server before running tests and stops it after."""
    
    # Check if port is already in use
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 8001))
    sock.close()
    
    if result == 0:
        pytest.fail("❌ Error: Port 8001 is already in use. Please stop any running web servers before running tests.")
    
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
