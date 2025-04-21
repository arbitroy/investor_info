import scrapy

class FinancialNewsItem(scrapy.Item):
    """Item for storing financial news articles"""
    title = scrapy.Field()
    link = scrapy.Field()
    summary = scrapy.Field()
    content = scrapy.Field()  # Full content of the article
    source = scrapy.Field()
    publish_date = scrapy.Field()
    sentiment = scrapy.Field()  # Optional sentiment score
    scraped_date = scrapy.Field()

class StockPriceItem(scrapy.Item):
    """Item for storing stock price information"""
    symbol = scrapy.Field()
    price = scrapy.Field()
    change_amount = scrapy.Field()
    change_percent = scrapy.Field()
    volume = scrapy.Field()
    market_cap = scrapy.Field()
    source = scrapy.Field()
    scraped_date = scrapy.Field()