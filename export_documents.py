#!/usr/bin/env python3
import json
import yaml
from pymongo import MongoClient
from bs4 import BeautifulSoup
import re
import sys
from urllib.parse import urlparse, urlunparse

_BOILERPLATE_SELECTORS = [
    # Fandom wiki
    ".global-navigation",
    ".fandom-community-header",
    ".page-header__actions",
    ".page-side-tools",
    ".page__right-rail",
    ".notifications-placeholder",
    ".wiki-sidebar",
    ".WikiaBar",
    ".wds-global-footer",
    ".wiki-page-header",
    ".page-footer",
    # Bethesda.net
    ".global-footer",
    # Cookie / consent banners (both sites)
    "[id*='onetrust']",
    "[id*='cookie']",
    "[class*='cookie']",
]


def clean_text(html):
    soup = BeautifulSoup(html, 'lxml')

    for tag in soup(["script", "style", "meta", "link", "noscript"]):
        tag.decompose()

    for tag in soup(["nav", "footer", "header"]):
        tag.decompose()

    for selector in _BOILERPLATE_SELECTORS:
        for el in soup.select(selector):
            el.decompose()

    title = ""
    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.get_text().strip()

    h1_tag = soup.find('h1')
    if h1_tag and not title:
        title = h1_tag.get_text().strip()

    text = soup.get_text(separator=' ')
    text = re.sub(r'\s+', ' ', text).strip()

    return title, text


def normalize_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url.strip())
    path = parsed.path or "/"
    path = re.sub(r"/{2,}", "/", path)
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    return urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        path,
        "",
        "",
        ""
    ))


def is_noise_url(url: str) -> bool:
    if not url:
        return True
    lowered = url.lower()
    media_exts = (
        ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg",
        ".mp4", ".webm", ".pdf", ".css", ".js", ".woff", ".woff2",
    )
    if lowered.endswith(media_exts):
        return True
    noisy_fragments = (
        "images.ctfassets.net",
        "/_next/",
        "/assets/",
        "/static/",
    )
    return any(fragment in lowered for fragment in noisy_fragments)


def is_informative_text(title: str, text: str) -> bool:
    if not text:
        return False
    if len(text) < 350:
        return False
    words = re.findall(r"[a-zA-Z]{3,}", text)
    if len(words) < 60:
        return False
    unique_ratio = len(set(words)) / max(len(words), 1)
    if unique_ratio < 0.12:
        return False
    if not title or len(title.strip()) < 3:
        return False
    return True

def export_documents(config_path='config/config_fandom.yaml', output_file='documents.jsonl', metadata_file='doc_metadata.json'):
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    db_config = config.get('db', {})
    host = 'localhost'
    port = db_config.get('port', 27017)
    database = db_config.get('database', 'fallout_wiki')
    
    print(f"Connecting to MongoDB at {host}:{port}/{database}...")
    client = MongoClient(f"mongodb://{host}:{port}/", serverSelectionTimeoutMS=5000)
    
    try:
        client.server_info()
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        sys.exit(1)
    
    db = client[database]
    documents_collection = db['documents']
    
    total_docs = documents_collection.count_documents({})
    print(f"Total documents in MongoDB: {total_docs:,}")
    
    if total_docs == 0:
        print("No documents found in MongoDB. Exiting.")
        sys.exit(0)
    
    metadata = {
        'total_documents': total_docs,
        'documents': []
    }
    
    print(f"Exporting documents to {output_file}...")
    exported_count = 0
    skipped_count = 0
    skipped_noise_url = 0
    skipped_duplicate_url = 0
    skipped_low_quality = 0
    seen_urls = set()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Stable ordering keeps doc_id consistent between exports.
        cursor = documents_collection.find().sort([("url", 1), ("_id", 1)])
        for doc in cursor:
            url = doc.get('url', '')
            html = doc.get('html', '')
            source = doc.get('source', 'Unknown')
            source_domain = doc.get('source_domain', 'unknown')
            timestamp = doc.get('timestamp', 0)

            normalized_url = normalize_url(url)
            if is_noise_url(normalized_url):
                skipped_count += 1
                skipped_noise_url += 1
                continue
            if normalized_url in seen_urls:
                skipped_count += 1
                skipped_duplicate_url += 1
                continue
            
            if not html or len(html) < 100:
                skipped_count += 1
                skipped_low_quality += 1
                continue
            
            try:
                title, text = clean_text(html)
                
                if not is_informative_text(title, text):
                    skipped_count += 1
                    skipped_low_quality += 1
                    continue

                # Keep doc_ids dense and deterministic across exports.
                doc_id = exported_count
                
                doc_data = {
                    'doc_id': doc_id,
                    'url': normalized_url,
                    'title': title,
                    'text': text
                }
                
                f.write(json.dumps(doc_data, ensure_ascii=False) + '\n')
                
                metadata['documents'].append({
                    'doc_id': doc_id,
                    'url': normalized_url,
                    'title': title,
                    'source': source,
                    'source_domain': source_domain,
                    'timestamp': timestamp,
                    'text_length': len(text)
                })
                seen_urls.add(normalized_url)
                
                exported_count += 1
                
                if exported_count % 100 == 0:
                    print(f"Exported {exported_count} documents...")
                    
            except Exception as e:
                print(f"Error processing document {doc_id} ({url}): {e}")
                skipped_count += 1
                continue
    
    print("\nExport complete!")
    print(f"Exported: {exported_count} documents")
    print(f"Skipped: {skipped_count} documents")
    print(f"  - noise/media URL: {skipped_noise_url}")
    print(f"  - duplicate URL: {skipped_duplicate_url}")
    print(f"  - low quality content: {skipped_low_quality}")
    print(f"Output: {output_file}")
    
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"Metadata: {metadata_file}")
    
    client.close()

if __name__ == '__main__':
    export_documents()

