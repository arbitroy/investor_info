import scrapy
from datetime import datetime
from urllib.parse import urlparse

class FinancialNewsSpider(scrapy.Spider):
    name = "financial_news"
    allowed_domains = ["finance.yahoo.com"]
    start_urls = ["https://finance.yahoo.com/news/"]

    def parse(self, response):
        articles = response.css('li.stream-item.story-item')

        for article in articles:
            # Extract title and link
            title = article.css('h3::text').get()
            link = article.css('a.subtle-link::attr(href)').get()
            
            if link and not link.startswith(('http://', 'https://')):
                link = response.urljoin(link)

            # Extract source and date (e.g., "Yahoo Personal Finance • 2h ago")
            metadata = article.css('div.publishing::text').get()
            if metadata:
                source, _, date = metadata.partition('•')
                source = source.strip()
                date = date.strip()
            else:
                source = "Unknown"
                date = ""

            # Clean up source name (remove "Yahoo" prefix if redundant)
            if source.startswith("Yahoo"):
                source = source.replace("Yahoo", "").strip()

            yield {
                'title': title.strip() if title else "",
                'link': link,
                'source': source,
                'publish_date': date if date else "Unknown",
                'scraped_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        # Follow pagination (if available)
        next_page = response.css('a.next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse)