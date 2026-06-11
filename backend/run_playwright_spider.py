#!/usr/bin/env python
import sys
import os
# Add the current directory to path so 'crawler' package is found
sys.path.insert(0, os.path.dirname(__file__))

from scrapy.crawler import CrawlerProcess

# Define the settings directly (bypass scrapy.cfg)
settings = {
    'BOT_NAME': 'news_crawler',
    'SPIDER_MODULES': ['crawler.spiders'],
    'NEWSPIDER_MODULE': 'crawler.spiders',
    'ROBOTSTXT_OBEY': True,
    'CONCURRENT_REQUESTS': 16,
    'DOWNLOAD_DELAY': 1,
    'FEED_URI': '../data/raw/articles.jsonl',
    'FEED_FORMAT': 'jsonlines',
    'FEED_EXPORT_ENCODING': 'utf-8',
    # Playwright download handler settings
    'DOWNLOAD_HANDLERS': {
        "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    },
    'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
    'PLAYWRIGHT_LAUNCH_OPTIONS': {'headless': True},
    'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 30000,
}

# Import the spider class
from crawler.spiders.regional_playwright_spider import RegionalPlaywrightSpider

if __name__ == "__main__":
    process = CrawlerProcess(settings)
    process.crawl(RegionalPlaywrightSpider)
    process.start()