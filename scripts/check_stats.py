#!/usr/bin/env python3
import yaml
from pymongo import MongoClient

# Загрузить конфиг
with open('config_fandom.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Подключиться к localhost (для локального запуска)
# В Docker используется 'mongodb', локально - 'localhost'
host = 'localhost'  # Изменено с config['db']['host']
port = config['db']['port']
database = config['db']['database']

client = MongoClient(f"mongodb://{host}:{port}/")
db = client[database]

# Статистика
total = db.documents.count_documents({})
fandom = db.documents.count_documents({'source_domain': 'fallout.fandom.com'})
fallout_wiki = db.documents.count_documents({'source_domain': 'fallout.wiki'})

print(f"📊 Всего документов: {total:,}")
print(f"📄 От Fandom: {fandom:,}")
print(f"📄 От Fallout.wiki: {fallout_wiki:,}")
print()

# Состояние краулеров
print("🤖 Состояние краулеров:")
for state in db.crawl_state.find():
    print(f"\n{state['_id']}:")
    print(f"  Категория: {state.get('current_category_index', 0) + 1}/{state.get('total_categories', '?')}")
    print(f"  Обкачано: {state.get('pages_crawled', 0)}")
    print(f"  Обновлено: {state.get('pages_updated', 0)}")
    print(f"  Пропущено: {state.get('pages_skipped', 0)}")