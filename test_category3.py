#!/usr/bin/env python3
"""Test script to see all links in category."""

import requests
from bs4 import BeautifulSoup

url = "https://fallout.fandom.com/wiki/Category:2020_news"

print(f"Fetching: {url}")
response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
html = response.text

soup = BeautifulSoup(html, 'lxml')

print("\n=== ALL Links in category-page__members ===")
category_members = soup.find('div', class_='category-page__members')

if category_members:
    links = category_members.find_all('a', href=True)
    print(f"Total links: {len(links)}\n")
    
    for i, link in enumerate(links, 1):
        href = link.get('href', '')
        text = link.get_text(strip=True)
        print(f"{i}. HREF: {href}")
        print(f"   TEXT: {text}")
        print()



