#!/usr/bin/env python3
"""
Main entry point for Bethesda Fallout Site Crawler
"""

import sys
import yaml
from src.db.db_manager import DatabaseManager
from src.crawlers.crawler_bethesda import BethesdaSiteCrawler


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ Configuration file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ Error parsing configuration file: {e}")
        sys.exit(1)


def main():
    """Main function."""
    # Get config file path from command line or use default
    config_path = sys.argv[1] if len(sys.argv) > 1 else 'config_bethesda.yaml'
    
    print("📋 Loading configuration...")
    config = load_config(config_path)
    
    # Initialize database manager
    print("🔌 Connecting to MongoDB...")
    db_manager = DatabaseManager(config)
    db_manager.connect()
    print("✅ Connected to MongoDB successfully")
    
    try:
        # Initialize crawler
        print("🕷️  Initializing crawler...")
        crawler = BethesdaSiteCrawler(config, db_manager)
        
        # Start crawling
        crawler.run()
        
    except KeyboardInterrupt:
        print("\n⏸️  Crawler interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔌 Closing database connection...")
        db_manager.close()
        print("👋 Goodbye!")


if __name__ == '__main__':
    main()

