import scrapy

class FinancialNewsItem(scrapy.Item):
    title = scrapy.Field()
    link = scrapy.Field()
    summary = scrapy.Field()
    source = scrapy.Field()
    scraped_date = scrapy.Field()