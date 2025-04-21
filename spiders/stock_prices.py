import scrapy
from datetime import datetime
import re
from investor_info.items import StockPriceItem

class StockPriceSpider(scrapy.Spider):
    name = "stock_prices"
    allowed_domains = ["finance.yahoo.com"]
    
    # List of stock symbols to track - could be expanded or loaded from a configuration file
    stock_symbols = [
        "AAPL", "MSFT", "AMZN", "GOOGL", "META", 
        "TSLA", "NVDA", "JPM", "V", "PG",
        "JNJ", "UNH", "HD", "BAC", "MA"
    ]
    
    def start_requests(self):
        """Generate request for each stock symbol"""
        for symbol in self.stock_symbols:
            url = f"https://finance.yahoo.com/quote/{symbol}"
            yield scrapy.Request(
                url=url,
                callback=self.parse_stock,
                meta={'symbol': symbol}
            )
    
    def parse_stock(self, response):
        """Parse stock price information based on the updated Yahoo Finance structure"""
        symbol = response.meta['symbol']
        self.logger.info(f"Processing stock: {symbol}")
        
        # Extract price - using the new data-testid selectors
        price_xpath = '//span[@data-testid="qsp-price"]/text()'
        price = response.xpath(price_xpath).get()
        
        # Extract change amount
        change_amount_xpath = '//span[@data-testid="qsp-price-change"]/text()'
        change_amount = response.xpath(change_amount_xpath).get()
        
        # Extract change percentage
        change_percent_xpath = '//span[@data-testid="qsp-price-change-percent"]/text()'
        change_percent_text = response.xpath(change_percent_xpath).get()
        change_percent = None
        if change_percent_text:
            # Extract percentage value from text like "+(1.39%)"
            percent_match = re.search(r'[-+]?[\d.]+', change_percent_text)
            if percent_match:
                change_percent = percent_match.group(0)
        
        # Extract volume - try different selectors as this may be in a different location
        volume = None
        # Try different possible volume selectors
        volume_selectors = [
            '//td[@data-test="VOLUME-value"]//text()',
            '//fin-streamer[@data-field="regularMarketVolume"]//text()',
            '//td[contains(text(), "Volume")]/following-sibling::td//text()'
        ]
        
        for selector in volume_selectors:
            volume_text = response.xpath(selector).get()
            if volume_text:
                # Remove commas from volume
                volume = volume_text.replace(',', '')
                break
        
        # Extract market cap
        market_cap = None
        market_cap_selectors = [
            '//td[@data-test="MARKET_CAP-value"]//text()',
            '//td[contains(text(), "Market Cap")]/following-sibling::td//text()'
        ]
        
        for selector in market_cap_selectors:
            market_cap_text = response.xpath(selector).get()
            if market_cap_text:
                # Parse market cap (e.g., "1.23T" or "456.78B")
                market_cap = self.parse_market_cap(market_cap_text)
                break
        
        # Debug logging
        self.logger.info(f"Symbol: {symbol}, Price: {price}, Change: {change_amount}, Percent: {change_percent_text}, Volume: {volume}")
        
        # Only proceed if we have at least a price
        if price:
            # Create item
            item = StockPriceItem()
            item['symbol'] = symbol
            item['price'] = self.safe_float(price)
            item['change_amount'] = self.safe_float(change_amount) if change_amount else 0.0
            item['change_percent'] = self.safe_float(change_percent) if change_percent else 0.0
            item['volume'] = self.safe_int(volume) if volume else 0
            item['market_cap'] = market_cap if market_cap else 0
            item['source'] = 'Yahoo Finance'
            item['scraped_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            yield item
        else:
            self.logger.error(f"Failed to extract price for {symbol}")
    
    def safe_float(self, value):
        """Convert string to float safely"""
        if value is None:
            return 0.0
        try:
            # Remove any commas and other non-numeric characters except decimal
            cleaned_value = re.sub(r'[^\d.-]', '', str(value))
            return float(cleaned_value)
        except (ValueError, TypeError):
            return 0.0
    
    def safe_int(self, value):
        """Convert string to int safely"""
        if value is None:
            return 0
        try:
            # Remove any commas and other non-numeric characters
            cleaned_value = re.sub(r'[^\d]', '', str(value))
            return int(cleaned_value)
        except (ValueError, TypeError):
            return 0
    
    def parse_market_cap(self, market_cap_text):
        """Parse market cap text to get numeric value"""
        if not market_cap_text:
            return 0
            
        market_cap_text = market_cap_text.strip()
        
        # Remove any commas
        market_cap_text = market_cap_text.replace(',', '')
        
        # Try to match the pattern like 1.23T or 456.78B
        match = re.search(r'([\d.]+)([TBM])', market_cap_text)
        if match:
            value = float(match.group(1))
            unit = match.group(2)
            
            # Convert to a consistent unit (e.g., millions)
            if unit == 'T':  # Trillion
                return int(value * 1_000_000_000_000)
            elif unit == 'B':  # Billion
                return int(value * 1_000_000_000)
            elif unit == 'M':  # Million
                return int(value * 1_000_000)
        
        # If we couldn't parse it, return 0
        return 0
    