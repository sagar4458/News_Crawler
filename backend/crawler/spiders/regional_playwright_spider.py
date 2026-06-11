import scrapy

class RegionalPlaywrightSpider(scrapy.Spider):
    name = "regional_playwright"
    start_urls = [
        "https://www.thehindu.com/news/national/",
        "https://indianexpress.com/section/india/",
        "https://timesofindia.indiatimes.com/india",
    ]

    def start_requests(self):
        for url in self.start_urls:
            # The 'playwright' meta flag is all you need to trigger the browser!
            yield scrapy.Request(url, meta={"playwright": True}, callback=self.parse)

    async def parse(self, response):
        # Extract article links
        if "thehindu.com" in response.url:
            links = response.css('a.story-card105x70__link::attr(href)').getall()
        elif "indianexpress.com" in response.url:
            links = response.css('h2.title a::attr(href)').getall()
        else:
            links = response.css('div.article a::attr(href)').getall()

        for link in links[:10]:
            # Use Playwright to fetch each article page as well
            yield scrapy.Request(
                url=response.urljoin(link),
                meta={"playwright": True},
                callback=self.parse_article
            )

    async def parse_article(self, response):
        title = response.css('h1::text, h1.title::text, h1.artTitle::text').get()
        if not title:
            return

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