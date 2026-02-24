# Fallout Wiki Crawler

Поисковый робот для обкачки Fallout Wiki с поддержкой возобновления и детектирования изменений.

## Архитектура

```
mai-ir/
├── src/                     # Исходный код
│   ├── crawlers/           # Логика краулеров
│   │   ├── main.py         # Точка входа для MediaWiki краулеров
│   │   ├── main_bethesda.py # Точка входа для Bethesda краулера
│   │   ├── crawler.py      # Основная логика MediaWiki краулера
│   │   └── crawler_bethesda.py # Логика Bethesda site краулера
│   ├── fetchers/           # Системы загрузки страниц
│   │   ├── base_fetcher.py # Базовый класс для fetcher'ов
│   │   ├── requests_fetcher.py # Быстрый fetcher через requests
│   │   ├── playwright_fetcher.py # Browser-based fetcher через Playwright
│   │   └── fetcher_factory.py # Фабрика для создания fetcher'ов
│   ├── db/                 # Работа с базой данных
│   │   └── db_manager.py   # Менеджер работы с MongoDB
│   └── utils/              # Утилиты
│       └── url_normalizer.py # Нормализация URL
├── config/                 # Конфигурационные файлы
│   ├── config_fandom.yaml  # Конфигурация для Fandom (requests)
│   ├── config_fallout_wiki.yaml # Конфигурация для fallout.wiki (Playwright)
│   └── config_bethesda.yaml # Конфигурация для Bethesda.net
├── scripts/                # Вспомогательные скрипты
│   ├── check_stats.py      # Скрипт для проверки статистики
│   └── migrate_db.py       # Скрипт миграции БД
├── requirements.txt        # Python зависимости
├── Dockerfile              # Docker образ
├── docker-compose.yml      # Docker Compose конфигурация
└── .dockerignore           # Исключения для Docker
```

### Гибридная система fetching

Краулер поддерживает два способа загрузки страниц:

1. **RequestsFetcher** (быстрый):
   - Использует библиотеку `requests`
   - ~2-5x быстрее чем браузер
   - Не выполняет JavaScript
   - Идеален для сайтов без bot detection (Fandom)

2. **PlaywrightFetcher** (надёжный):
   - Использует настоящий браузер Chromium
   - Выполняет JavaScript
   - Имитирует поведение человека
   - Обходит bot detection системы
   - Медленнее, но работает с fallout.wiki

## Быстрый старт с Docker (Рекомендуется)

### 1. Запуск

```bash
# Запустить MongoDB и оба краулера (Fandom + fallout.wiki)
docker-compose up -d

# Посмотреть логи обоих краулеров
docker-compose logs -f

# Или логи отдельных краулеров
docker-compose logs -f crawler_fandom
docker-compose logs -f crawler_fallout_wiki
```

### 2. Остановка

```bash
# Остановить один краулер (MongoDB продолжит работать)
docker-compose stop crawler_fandom
docker-compose stop crawler_fallout_wiki

# Остановить всё
docker-compose down

# Остановить и удалить данные
docker-compose down -v
```

### 3. Перезапуск

```bash
# Краулеры автоматически продолжат с места остановки
docker-compose restart crawler_fandom
docker-compose restart crawler_fallout_wiki
```

## Локальная разработка

### 1. Установка зависимостей

```bash
# Установить Python зависимости
pip install -r requirements.txt

# Установить Playwright браузер (для fallout.wiki краулера)
playwright install chromium
```

### 2. Запуск MongoDB

```bash
# Через Docker (рекомендуется)
docker-compose up -d mongodb

# Или установите MongoDB локально
```

### 3. Настройка конфигурации

Отредактируйте нужный конфиг (`config_fandom.yaml` или `config_fallout_wiki.yaml`):
```yaml
db:
  host: "localhost"  # Измените с "mongodb" на "localhost"
  port: 27017
  # ... остальные настройки
```

### 4. Запуск краулера

```bash
# Запустить Fandom краулер (быстрый, requests)
python main.py config_fandom.yaml

# Запустить fallout.wiki краулер (Playwright)
python main.py config_fallout_wiki.yaml
```

## Конфигурация

Проект использует два конфига для разных источников:

### config_fandom.yaml (быстрый requests)

```yaml
db:
  host: "mongodb"              # Хост MongoDB
  port: 27017                  # Порт MongoDB
  database: "fallout_wiki"     # Имя базы данных

logic:
  delay_seconds: 2.0           # Задержка между запросами (секунды)
  recrawl_age_days: 30         # Переобкачивать страницы старше N дней
  user_agent: "rotate"         # Ротация User-Agent
  max_retries: 3               # Максимум попыток при ошибке
  timeout_seconds: 30          # Таймаут запроса

crawler:
  crawler_id: "fandom_crawler"
  source_name: "Fallout Fandom"
  source_domain: "fallout.fandom.com"
  fetch_method: "requests"     # Быстрый метод для Fandom
  start_url: "https://fallout.fandom.com/wiki/Special:Categories"
  domain_whitelist:
    - "fallout.fandom.com"
```

### config_fallout_wiki.yaml (Playwright для обхода bot detection)

```yaml
db:
  host: "mongodb"
  port: 27017
  database: "fallout_wiki"

logic:
  delay_seconds: 4.5           # Больше задержка для fallout.wiki
  recrawl_age_days: 30
  user_agent: "rotate"
  max_retries: 3
  timeout_seconds: 30

crawler:
  crawler_id: "fallout_wiki_crawler"
  source_name: "Fallout Wiki"
  source_domain: "fallout.wiki"
  fetch_method: "playwright"  # Браузер для обхода bot detection
  start_url: "https://fallout.wiki/wiki/Special:Categories"
  domain_whitelist:
    - "fallout.wiki"

browser:                       # Настройки Playwright
  headless: true               # Запуск без GUI
  browser_type: "chromium"     # chromium/firefox/webkit
  viewport_width: 1920
  viewport_height: 1080
  block_images: true           # Блокировка изображений для скорости
  block_ads: true              # Блокировка рекламы
  timeout_seconds: 30
```

### Параметры fetch_method

- `"requests"` - быстрый HTTP-клиент без JavaScript (для Fandom)
- `"playwright"` - полноценный браузер с JavaScript (для fallout.wiki)

## Структура данных в MongoDB

### Коллекция `documents`

```javascript
{
  "_id": ObjectId,
  "url": "https://fallout.fandom.com/wiki/Article_Name",
  "html": "<html>...</html>",
  "source": "Fallout Fandom",           // Имя источника
  "source_domain": "fallout.fandom.com", // Домен источника
  "timestamp": 1734480000,
  "content_hash": "5d41402abc4b2a76b9719d911017c592"
}
```

**Примечание**: Уникальность документов определяется композитным индексом `(url, source_domain)`, что позволяет хранить одинаковые URL с разных источников.

### Коллекция `crawl_state`

```javascript
// Для Fandom краулера
{
  "_id": "fandom_crawler",
  "current_category_index": 42,
  "current_category_url": "https://...",
  "current_article_index": 15,
  "total_categories": 100,
  "pages_crawled": 1500,
  "pages_updated": 200,
  "pages_skipped": 1300,
  "last_updated": 1734480000
}

// Для fallout.wiki краулера
{
  "_id": "fallout_wiki_crawler",
  "current_category_index": 10,
  "current_category_url": "https://...",
  "current_article_index": 5,
  "total_categories": 80,
  "pages_crawled": 500,
  "pages_updated": 100,
  "pages_skipped": 400,
  "last_updated": 1734480000
}
```

## Как это работает

1. **Сбор категорий**: Краулер начинает со страницы Special:Categories и собирает все категории с учетом пагинации
2. **Обход категорий**: Для каждой категории извлекаются все статьи (также с пагинацией)
3. **Обкачка статей**: Каждая статья скачивается и сохраняется в MongoDB
4. **Проверка изменений**: Перед сохранением вычисляется MD5-хеш и сравнивается с существующим
5. **Сохранение состояния**: Каждые 10 статей состояние сохраняется в БД
6. **Возобновление**: При повторном запуске краулер продолжит с последней обработанной статьи

### Anti-Detection меры (Playwright)

PlaywrightFetcher использует продвинутые техники для обхода bot detection:

- **Удаление webdriver flag**: `navigator.webdriver = undefined`
- **Рандомизация viewport**: Случайное изменение разрешения экрана ±50px
- **User-Agent rotation**: Ротация между популярными браузерными User-Agent'ами
- **Блокировка аналитики**: Автоматическая блокировка Google Analytics, Facebook Pixel и др.
- **Блокировка изображений**: Отключение загрузки изображений для скорости
- **Реалистичные заголовки**: Accept-Language, timezone и другие браузерные параметры
- **Headless режим**: Работа без GUI для экономии ресурсов

Эти меры позволяют Playwright имитировать поведение настоящего браузера и обходить системы защиты fallout.wiki.

## Остановка и возобновление

Краулер можно безопасно остановить в любой момент:

- **Ctrl+C**: Корректно сохранит состояние и завершит работу
- **docker-compose stop**: Остановит контейнер с сохранением состояния

При следующем запуске краулер автоматически продолжит с места остановки.

## Мониторинг

### Просмотр логов в реальном времени

```bash
# Оба краулера
docker-compose logs -f

# Только Fandom
docker-compose logs -f crawler_fandom

# Только fallout.wiki
docker-compose logs -f crawler_fallout_wiki
```

### Проверка статистики

```bash
# Быстрая проверка через Python скрипт
python check_stats.py config_fandom.yaml
```

### Подключение к MongoDB

```bash
# Через Docker
docker exec -it fallout_wiki_mongodb mongosh fallout_wiki

# Локально
mongosh mongodb://localhost:27017/fallout_wiki
```

### Полезные MongoDB запросы

```javascript
// Количество документов всего
db.documents.countDocuments()

// Количество по источникам
db.documents.countDocuments({"source_domain": "fallout.fandom.com"})
db.documents.countDocuments({"source_domain": "fallout.wiki"})

// Последние обкаченные страницы
db.documents.find().sort({timestamp: -1}).limit(10)

// Состояние Fandom краулера
db.crawl_state.findOne({"_id": "fandom_crawler"})

// Состояние fallout.wiki краулера
db.crawl_state.findOne({_id: "main_crawler"})

// Статистика по датам
db.documents.aggregate([
  {$group: {
    _id: {$dateToString: {format: "%Y-%m-%d", date: {$toDate: {$multiply: ["$timestamp", 1000]}}}},
    count: {$sum: 1}
  }},
  {$sort: {_id: -1}}
])
```

## Производительность

### RequestsFetcher (Fandom)
- **Скорость**: ~500-1000 страниц/час
- **Задержка**: 2 секунды между запросами
- **Память**: ~50-100 МБ RAM
- **Время**: Полная обкачка ~2-4 часа

### PlaywrightFetcher (fallout.wiki)
- **Скорость**: ~200-400 страниц/час (медленнее из-за браузера)
- **Задержка**: 4.5 секунды между запросами
- **Память**: ~300-500 МБ RAM (браузер Chromium)
- **Время**: Полная обкачка ~5-8 часов

### Общее
- **Диск**: ~2-5 ГБ для всех страниц обоих источников
- **MongoDB**: ~1-2 ГБ данных + индексы
