# Run this script to manually start the crawler
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from crawler.spiders.regional_spider import RegionalNewsSpider

if __name__ == "__main__":
    settings = get_project_settings()
    settings.set('FEEDS', {'../data/raw/articles.jsonl': {'format': 'jsonlines', 'overwrite': True}})
    process = CrawlerProcess(settings)
    process.crawl(RegionalNewsSpider)
    process.start()