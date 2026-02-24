#!/usr/bin/env python3
"""
Fallout Wiki Crawler - Main Entry Point

Usage:
    python main.py config.yaml
"""

import sys
import yaml
from src.db.db_manager import DatabaseManager
from src.crawlers.crawler import FalloutWikiCrawler


def load_config(config_path: str) -> dict:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to the YAML config file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"❌ Error: Config file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ Error parsing YAML config: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        sys.exit(1)


def main():
    """Main entry point for the crawler."""
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: python main.py <config.yaml>")
        print("\nExample:")
        print("  python main.py config.yaml")
        sys.exit(1)
    
    config_path = sys.argv[1]
    
    print("📋 Loading configuration...")
    config = load_config(config_path)
    
    # Initialize database manager
    print("🔌 Connecting to MongoDB...")
    db_manager = DatabaseManager(config)
    
    try:
        db_manager.connect()
        print("✅ Connected to MongoDB successfully")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        print("\n💡 Tips:")
        print("  - Make sure MongoDB is running")
        print("  - Check your database configuration in config.yaml")
        print("  - If using Docker, ensure MongoDB container is up: docker-compose up -d mongodb")
        sys.exit(1)
    
    # Initialize crawler
    print("🕷️  Initializing crawler...")
    crawler = FalloutWikiCrawler(config, db_manager)
    
    try:
        # Run the crawler
        crawler.run()
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        print("\n🔌 Closing database connection...")
        db_manager.close()
        print("👋 Goodbye!")


if __name__ == '__main__':
    main()



