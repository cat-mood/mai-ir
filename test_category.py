#!/usr/bin/env python3
"""Test script to debug category page parsing."""

import requests
from bs4 import BeautifulSoup

# Test with a category that should have articles
url = "https://fallout.fandom.com/wiki/Category:2020_news"

print(f"Fetching: {url}")
response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
html = response.text

soup = BeautifulSoup(html, 'lxml')

print("\n=== Looking for mw-category ===")
mw_category = soup.find_all(['div', 'ul'], class_=['mw-category', 'mw-category-group'])
print(f"Found {len(mw_category)} elements with mw-category classes")

print("\n=== Looking for category-page__members ===")
category_members = soup.find_all('div', class_='category-page__members')
print(f"Found {len(category_members)} elements with category-page__members class")

print("\n=== Looking for any links with /wiki/ ===")
all_links = soup.find_all('a', href=True)
wiki_links = [link for link in all_links if '/wiki/' in link.get('href', '')]
print(f"Found {len(wiki_links)} links with /wiki/")

# Print first 10 wiki links
print("\n=== First 10 wiki links ===")
for i, link in enumerate(wiki_links[:10]):
    href = link.get('href', '')
    text = link.get_text(strip=True)
    print(f"{i+1}. {href} -> {text}")

print("\n=== Looking for article links (no : in path) ===")
article_links = []
for link in wiki_links:
    href = link.get('href', '')
    if href.startswith('/wiki/'):
        path_part = href.split('/wiki/')[1] if len(href.split('/wiki/')) > 1 else ''
        if ':' not in path_part:
            article_links.append(href)

print(f"Found {len(article_links)} article links (no colon in path)")
for i, href in enumerate(article_links[:10]):
    print(f"{i+1}. {href}")



