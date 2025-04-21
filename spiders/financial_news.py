import scrapy
from datetime import datetime
from urllib.parse import urlparse, urljoin
import re
from investor_info.items import FinancialNewsItem
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

class FinancialNewsSpider(CrawlSpider):
    name = "financial_news"
    allowed_domains = ["finance.yahoo.com", "reuters.com", "cnbc.com"]
    
    # Start URLs for different financial news sources
    start_urls = [
        "https://finance.yahoo.com/news/",
        "https://www.reuters.com/business/finance/",
        "https://www.cnbc.com/finance/"
    ]
    
    # Define rules for following links
    rules = (
        # Follow pagination links
        Rule(LinkExtractor(allow=r'page=\d+'), follow=True),
        
        # Extract article links and follow them
        Rule(LinkExtractor(
            allow=[
                r'finance\.yahoo\.com/news/.*\.html',
                r'reuters\.com/business/finance/.*',
                r'cnbc\.com/\d+/\d+/\d+/.*\.html'
            ]), 
            callback='parse_article', 
            follow=True
        ),
    )
    
    def determine_source(self, url):
        """Determine the source based on the URL domain"""
        domain = urlparse(url).netloc
        if 'yahoo.com' in domain:
            return 'Yahoo Finance'
        elif 'reuters.com' in domain:
            return 'Reuters'
        elif 'cnbc.com' in domain:
            return 'CNBC'
        return 'Unknown'

    def parse_article(self, response):
        """Parse article page for detailed content"""
        source = self.determine_source(response.url)
        
        # Different parsing logic based on source
        if source == 'Yahoo Finance':
            return self.parse_yahoo_article(response)
        elif source == 'Reuters':
            return self.parse_reuters_article(response)
        elif source == 'CNBC':
            return self.parse_cnbc_article(response)
        else:
            self.logger.warning(f"Unknown source for URL: {response.url}")
            return None

    def parse_yahoo_article(self, response):
        """Parse Yahoo Finance article"""
        title = response.css('h1::text').get()
        if not title:
            return None
            
        # Extract article content
        paragraphs = response.css('div.caas-body p::text').getall()
        content = '\n\n'.join([p.strip() for p in paragraphs if p.strip()])
        
        # Extract summary
        summary = response.css('div.caas-description::text').get()
        
        # Extract publish date
        publish_date = response.css('time::text').get()
        if not publish_date:
            publish_date = response.css('time::attr(datetime)').get()
        
        # Create item
        item = FinancialNewsItem()
        item['title'] = title.strip()
        item['link'] = response.url
        item['summary'] = summary.strip() if summary else ''
        item['content'] = content
        item['source'] = 'Yahoo Finance'
        item['publish_date'] = publish_date
        item['scraped_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return item

    def parse_reuters_article(self, response):
        """Parse Reuters article"""
        title = response.css('h1::text').get()
        if not title:
            return None
            
        # Extract article content
        paragraphs = response.css('div.article-body__content__17Yit p::text').getall()
        content = '\n\n'.join([p.strip() for p in paragraphs if p.strip()])
        
        # Extract summary
        summary = response.css('div.article-body__content__17Yit p:first-child::text').get()
        
        # Extract publish date
        publish_date = response.css('time::attr(datetime)').get()
        
        # Create item
        item = FinancialNewsItem()
        item['title'] = title.strip()
        item['link'] = response.url
        item['summary'] = summary.strip() if summary else ''
        item['content'] = content
        item['source'] = 'Reuters'
        item['publish_date'] = publish_date
        item['scraped_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return item

    def parse_cnbc_article(self, response):
        """Parse CNBC article"""
        title = response.css('h1.ArticleHeader-headline::text').get()
        if not title:
            return None
            
        # Extract article content
        paragraphs = response.css('div.ArticleBody-articleBody p::text').getall()
        content = '\n\n'.join([p.strip() for p in paragraphs if p.strip()])
        
        # Extract summary
        summary = response.css('div.ArticleHeader-summary::text').get()
        
        # Extract publish date
        publish_date = response.css('time::attr(datetime)').get()
        
        # Create item
        item = FinancialNewsItem()
        item['title'] = title.strip()
        item['link'] = response.url
        item['summary'] = summary.strip() if summary else ''
        item['content'] = content
        item['source'] = 'CNBC'
        item['publish_date'] = publish_date
        item['scraped_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return item