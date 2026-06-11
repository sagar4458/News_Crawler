  
import scrapy
from scrapy import signals
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By

class RegionalNewsSpider(scrapy.Spider):
    name = "regional_news"
    allowed_domains = ["thehindu.com", "indianexpress.com", "timesofindia.indiatimes.com"]
    start_urls = [
        "https://www.thehindu.com/news/national/",
        "https://indianexpress.com/section/india/",
        "https://timesofindia.indiatimes.com/india",
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield SeleniumRequest(url=url, callback=self.parse, wait_time=3)

    def parse(self, response):
        # Extract article links
        if "thehindu.com" in response.url:
            article_links = response.css('a.story-card105x70__link::attr(href)').getall()
        elif "indianexpress.com" in response.url:
            article_links = response.css('h2.title a::attr(href)').getall()
        else:  # TOI
            article_links = response.css('div.article a::attr(href)').getall()

        for link in article_links[:10]:  # limit per page
            yield SeleniumRequest(url=response.urljoin(link), callback=self.parse_article, wait_time=2)

    def parse_article(self, response):
        title = response.css('h1::text, h1.title::text, h1.artTitle::text').get()
        if not title:
            return

        # Get paragraphs
        paragraphs = response.css('p::text, div.article-content p::text, div.paragraph p::text').getall()
        body = ' '.join(paragraphs).strip()

        if not body:
            return

        yield {
            'title': title.strip(),
            'body': body,
            'url': response.url,
            'source': response.url.split('/')[2],
            'date': response.css('time::attr(datetime)').get(),
        }