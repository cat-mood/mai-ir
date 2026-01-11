#!/usr/bin/env python3
"""Test script to analyze category-page__members structure."""

import requests
from bs4 import BeautifulSoup

url = "https://fallout.fandom.com/wiki/Category:2020_news"

print(f"Fetching: {url}")
response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
html = response.text

soup = BeautifulSoup(html, 'lxml')

print("\n=== Analyzing category-page__members ===")
category_members = soup.find('div', class_='category-page__members')

if category_members:
    print("Found category-page__members div")
    
    # Find all links in this section
    links = category_members.find_all('a', href=True)
    print(f"\nTotal links in category-page__members: {len(links)}")
    
    # Categorize links
    article_links = []
    for link in links:
        href = link.get('href', '')
        text = link.get_text(strip=True)
        
        # Check if it's a wiki link
        if '/wiki/' in href:
            # Extract the path part
            if href.startswith('http'):
                # Full URL
                parts = href.split('/wiki/')
                if len(parts) > 1:
                    path = parts[1]
                else:
                    continue
            elif href.startswith('/wiki/'):
                # Relative URL
                path = href[6:]  # Remove '/wiki/'
            else:
                continue
            
            # Skip special pages (contain :)
            if ':' not in path:
                article_links.append(href)
                print(f"  Article: {href} -> {text}")

print(f"\n=== Summary ===")
print(f"Found {len(article_links)} article links")



