# Scrapy settings for investor_info project
BOT_NAME = 'investor_info'

SPIDER_MODULES = ['investor_info.spiders']
NEWSPIDER_MODULE = 'investor_info.spiders'

# Enable the pipeline
ITEM_PIPELINES = {
   'investor_info.pipelines.DatabasePipeline': 300,
}

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure a reasonable download delay to be respectful
DOWNLOAD_DELAY = 2

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 8

# User agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'