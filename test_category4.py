#!/usr/bin/env python3
"""Test with a category that should have actual articles."""

import requests
from bs4 import BeautifulSoup

# This category should have 9 members (characters)
url = "https://fallout.fandom.com/wiki/Category:188_Trading_Post_characters"

print(f"Fetching: {url}")
response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
html = response.text

soup = BeautifulSoup(html, 'lxml')

print("\n=== ALL Links in category-page__members ===")
category_members = soup.find('div', class_='category-page__members')

if category_members:
    links = category_members.find_all('a', href=True)
    print(f"Total links: {len(links)}\n")
    
    articles = []
    subcategories = []
    
    for i, link in enumerate(links, 1):
        href = link.get('href', '')
        text = link.get_text(strip=True)
        
        # Check if it's a category or article
        if 'Category:' in href:
            subcategories.append((href, text))
        else:
            articles.append((href, text))
            
        print(f"{i}. HREF: {href}")
        print(f"   TEXT: {text}")
        print(f"   TYPE: {'Category' if 'Category:' in href else 'Article'}")
        print()
    
    print(f"\n=== Summary ===")
    print(f"Articles: {len(articles)}")
    print(f"Subcategories: {len(subcategories)}")



