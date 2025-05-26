#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import time

def test_bleeping_computer():
    """Test scraping BleepingComputer directly"""
    
    # Better User-Agent
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    url = "https://www.bleepingcomputer.com/news/security/"
    
    print(f"Testing URL: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Test different selectors
            selectors = [
                'a[href*="/news/security/"]',
                'a[href*="/news/"]',
                '.nmic',
                'a.nmic'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                print(f"Selector '{selector}': found {len(elements)} elements")
                
                if elements:
                    for i, elem in enumerate(elements[:3]):  # Show first 3
                        href = elem.get('href')
                        text = elem.get_text(strip=True)[:50]
                        print(f"  {i+1}. {href} - {text}")
                    print()
        else:
            print(f"Failed to fetch page: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_bleeping_computer()