#!/usr/bin/env python3
"""Database migration script to add source_domain to existing documents."""

import sys
import yaml
from pymongo import MongoClient, ASCENDING


def load_config(config_path):
    """Load YAML configuration file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def migrate_database(config):
    """Migrate existing documents to new schema with source_domain."""
    
    db_config = config.get('db', {})
    host = db_config.get('host', 'localhost')
    port = db_config.get('port', 27017)
    database = db_config.get('database', 'fallout_wiki')
    
    print(f"🔌 Connecting to MongoDB at {host}:{port}/{database}...")
    client = MongoClient(f"mongodb://{host}:{port}/", serverSelectionTimeoutMS=5000)
    
    try:
        # Test connection
        client.server_info()
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return False
    
    db = client[database]
    documents = db['documents']
    
    # Статистика
    total_docs = documents.count_documents({})
    docs_without_source = documents.count_documents({"source_domain": {"$exists": False}})
    
    print(f"📊 Total documents: {total_docs}")
    print(f"📊 Documents without source_domain: {docs_without_source}")
    
    if docs_without_source == 0:
        print("✅ All documents already have source_domain field. No migration needed.")
        return True
    
    print(f"\n🔄 Starting migration of {docs_without_source} documents...")
    
    # Шаг 1: Добавить source_domain ко всем существующим документам
    # Предполагаем, что все существующие документы из fallout.fandom.com
    result = documents.update_many(
        {"source_domain": {"$exists": False}},
        {"$set": {"source_domain": "fallout.fandom.com"}}
    )
    
    print(f"✅ Updated {result.modified_count} documents with source_domain")
    
    # Шаг 2: Проверить и обновить индексы
    print("\n🔧 Updating indexes...")
    
    existing_indexes = list(documents.list_indexes())
    index_names = [idx['name'] for idx in existing_indexes]
    
    print(f"Current indexes: {index_names}")
    
    # Удалить старый unique индекс на url, если существует
    if 'url_1' in index_names:
        print("🗑️  Dropping old 'url_1' index...")
        documents.drop_index('url_1')
        print("✅ Old index dropped")
    
    # Создать новый композитный unique индекс
    if 'url_1_source_domain_1' not in index_names:
        print("📝 Creating new composite unique index (url, source_domain)...")
        documents.create_index(
            [('url', ASCENDING), ('source_domain', ASCENDING)],
            unique=True,
            name='url_1_source_domain_1'
        )
        print("✅ New composite index created")
    
    # Создать индекс на source_domain
    if 'source_domain_1' not in index_names:
        print("📝 Creating index on source_domain...")
        documents.create_index([('source_domain', ASCENDING)])
        print("✅ source_domain index created")
    
    # Индекс на timestamp (должен уже быть)
    if 'timestamp_1' not in index_names:
        print("📝 Creating index on timestamp...")
        documents.create_index([('timestamp', ASCENDING)])
        print("✅ timestamp index created")
    
    # Финальная проверка
    print("\n🔍 Final verification...")
    docs_without_source_after = documents.count_documents({"source_domain": {"$exists": False}})
    
    if docs_without_source_after == 0:
        print("✅ Migration completed successfully!")
        print(f"✅ All {total_docs} documents now have source_domain field")
        
        # Показать пример документа
        sample = documents.find_one()
        if sample:
            print("\n📄 Sample document:")
            print(f"   URL: {sample.get('url', 'N/A')}")
            print(f"   Source: {sample.get('source', 'N/A')}")
            print(f"   Source Domain: {sample.get('source_domain', 'N/A')}")
        
        return True
    else:
        print(f"⚠️  Warning: {docs_without_source_after} documents still without source_domain")
        return False


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python migrate_db.py <config.yaml>")
        print("\nExample:")
        print("  python migrate_db.py config.yaml")
        sys.exit(1)
    
    config_path = sys.argv[1]
    
    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        sys.exit(1)
    
    success = migrate_database(config)
    sys.exit(0 if success else 1)

