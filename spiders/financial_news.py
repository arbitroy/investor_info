import scrapy
from datetime import datetime

class FinancialNewsSpider(scrapy.Spider):
    name = "financial_news"
    allowed_domains = ["finance.yahoo.com"]
    start_urls = ["https://finance.yahoo.com/news/"]
    
    def parse(self, response):
        # Your parsing code here
        self.logger.info("Spider running!")
        yield {"test": "This is a test item"}