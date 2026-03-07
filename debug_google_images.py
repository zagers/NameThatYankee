#!/usr/bin/env python3
"""
Debug script to test Google Images search and find correct selectors.
"""

import sys
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import urllib.parse

def debug_google_images_search():
    """Debug Google Images search to find working selectors."""
    
    search_term = "Duke Ellis mlb player"
    
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    
    try:
        # Use Google Images search
        encoded_query = urllib.parse.quote_plus(search_term)
        search_url = f"https://www.google.com/search?q={encoded_query}&tbm=isch"
        
        print(f"Searching: {search_term}")
        print(f"URL: {search_url}")
        
        driver.get(search_url)
        time.sleep(3)
        
        # Try different selectors
        selectors_to_try = [
            "img.Q4LuWd",  # Current selector
            "img.YQ4gaf",  # Alternative
            "img.rg_i",    # Common Google Images selector
            "img[src^='https://encrypted-tbn0.gstatic.com']",  # Google's CDN
            "img[src^='http']",  # Any http images
            "img",  # All images
        ]
        
        print("\nTesting selectors:")
        for selector in selectors_to_try:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"  {selector}: Found {len(elements)} elements")
                
                if elements:
                    # Show first few src attributes
                    for i, elem in enumerate(elements[:3]):
                        src = elem.get_attribute('src')
                        if src:
                            print(f"    [{i}] {src[:100]}...")
                            
            except Exception as e:
                print(f"  {selector}: ERROR - {e}")
        
        # Let's also check the page title and some basic info
        print(f"\nPage title: {driver.title}")
        print(f"Current URL: {driver.current_url}")
        
        # Check if we're on a Google Images page
        if "tbm=isch" in driver.current_url:
            print("✅ Successfully navigated to Google Images")
        else:
            print("❌ Not on Google Images page")
            
        # Try to find any images with different approach
        all_images = driver.find_elements(By.TAG_NAME, "img")
        print(f"\nTotal images on page: {len(all_images)}")
        
        # Count images with different src patterns
        http_count = 0
        https_count = 0
        data_count = 0
        
        for img in all_images:
            src = img.get_attribute('src')
            if src:
                if src.startswith('http://'):
                    http_count += 1
                elif src.startswith('https://'):
                    https_count += 1
                elif src.startswith('data:'):
                    data_count += 1
        
        print(f"  HTTP images: {http_count}")
        print(f"  HTTPS images: {https_count}")
        print(f"  Data URI images: {data_count}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_google_images_search()
