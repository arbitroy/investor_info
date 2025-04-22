import scrapy
from datetime import datetime
import re
import json
import logging
from investor_info.items import StockPriceItem

class StockPriceSpider(scrapy.Spider):
    name = "stock_prices"
    allowed_domains = ["finance.yahoo.com", "query1.finance.yahoo.com", "query2.finance.yahoo.com"]
    
    # Custom settings to bypass anti-scraping measures
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'DOWNLOAD_DELAY': 2,  # Wait 2 seconds between requests
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,  # Limit concurrent requests
        'HTTPCACHE_ENABLED': True,  # Enable HTTP caching
        'LOG_LEVEL': 'INFO',
        'COOKIES_ENABLED': False,
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Referer': 'https://finance.yahoo.com/',
        }
    }
    
    # List of stock symbols to track
    stock_symbols = [
        "AAPL", "MSFT", "AMZN", "GOOGL", "META", 
        "TSLA", "NVDA", "JPM", "V", "PG",
        "JNJ", "UNH", "HD", "BAC", "MA",
        # Major indices
        "^GSPC", "^DJI", "^IXIC", "^FTSE", "^N225"
    ]
    
    def start_requests(self):
        """Generate request for each stock symbol"""
        for symbol in self.stock_symbols:
            # Primary method: Quote Summary API - best for market cap and detailed data
            summary_url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}?modules=price,summaryDetail,defaultKeyStatistics"
            yield scrapy.Request(
                url=summary_url,
                callback=self.parse_quote_summary,
                meta={'symbol': symbol},
                errback=self.handle_error,
                priority=3  # Highest priority
            )
            
            # Backup method: Quote API 
            api_url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
            yield scrapy.Request(
                url=api_url,
                callback=self.parse_quote_api,
                meta={'symbol': symbol},
                errback=self.handle_error,
                priority=2  # High priority
            )
            
            # Third option: Chart API as backup
            chart_api_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
            yield scrapy.Request(
                url=chart_api_url,
                callback=self.parse_chart_api,
                meta={'symbol': symbol},
                errback=self.handle_error,
                priority=1  # Medium priority
            )
    
    def handle_error(self, failure):
        """Handle request errors"""
        symbol = failure.request.meta.get('symbol', 'Unknown')
        self.logger.error(f"Error scraping {symbol}: {repr(failure)}")
    
    def parse_quote_summary(self, response):
        """Parse stock data from Yahoo Finance Quote Summary API - this has the most complete data"""
        symbol = response.meta['symbol']
        self.logger.info(f"Processing Quote Summary API data for: {symbol}")
        
        try:
            # Parse JSON response
            data = json.loads(response.text)
            
            # Check if we have valid data
            if ('quoteSummary' in data and 'result' in data['quoteSummary'] and 
                data['quoteSummary']['result'] and data['quoteSummary']['result'][0]):
                
                result = data['quoteSummary']['result'][0]
                
                # Extract price data from price module
                price_data = result.get('price', {})
                
                # Current price
                price = self.safe_extract(price_data, 'regularMarketPrice', 'raw')
                
                # Change amount
                change_amount = self.safe_extract(price_data, 'regularMarketChange', 'raw')
                
                # Change percent
                change_percent = self.safe_extract(price_data, 'regularMarketChangePercent', 'raw')
                
                # Volume
                volume = self.safe_extract(price_data, 'regularMarketVolume', 'raw')
                
                # Market cap - from price module
                market_cap = self.safe_extract(price_data, 'marketCap', 'raw')
                
                # If market cap not in price, try defaultKeyStatistics
                if not market_cap and 'defaultKeyStatistics' in result:
                    market_cap = self.safe_extract(result['defaultKeyStatistics'], 'enterpriseValue', 'raw')
                
                # If still no market cap, try summaryDetail
                if not market_cap and 'summaryDetail' in result:
                    market_cap = self.safe_extract(result['summaryDetail'], 'marketCap', 'raw')
                
                # Debug information
                self.logger.info(f"Quote Summary API data: Symbol: {symbol}, Price: {price}, Change: {change_amount}, Percent: {change_percent}, Volume: {volume}, Market Cap: {market_cap}")
                
                # Only proceed if we have at least a price
                if price:
                    # Create item
                    item = StockPriceItem()
                    item['symbol'] = symbol
                    item['price'] = float(price)
                    item['change_amount'] = float(change_amount) if change_amount is not None else 0.0
                    item['change_percent'] = float(change_percent) if change_percent is not None else 0.0
                    item['volume'] = int(volume) if volume else 0
                    item['market_cap'] = int(market_cap) if market_cap else 0
                    item['source'] = 'Yahoo Finance API'
                    item['scraped_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    return item
                else:
                    self.logger.warning(f"Quote Summary API missing price data for {symbol}")
            else:
                self.logger.warning(f"Invalid Quote Summary API response format for {symbol}")
        
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON from Quote Summary API for {symbol}")
        except Exception as e:
            self.logger.error(f"Error processing Quote Summary API data for {symbol}: {str(e)}")
    
    def safe_extract(self, data, key, sub_key=None):
        """Safely extract nested values from API response"""
        if not data or key not in data:
            return None
        
        if sub_key is not None:
            if sub_key in data[key]:
                return data[key][sub_key]
            return None
        
        return data[key]
    
    def parse_quote_api(self, response):
        """Parse stock data from Yahoo Finance Quote API"""
        symbol = response.meta['symbol']
        self.logger.info(f"Processing Quote API data for: {symbol}")
        
        try:
            # Parse JSON response
            data = json.loads(response.text)
            
            # Check if we have valid data
            if 'quoteResponse' in data and 'result' in data['quoteResponse'] and data['quoteResponse']['result']:
                quote = data['quoteResponse']['result'][0]
                
                # Extract data
                price = quote.get('regularMarketPrice')
                change_amount = quote.get('regularMarketChange')
                change_percent = quote.get('regularMarketChangePercent')
                volume = quote.get('regularMarketVolume')
                market_cap = quote.get('marketCap')
                
                # Debug information
                self.logger.info(f"Quote API data: Symbol: {symbol}, Price: {price}, Change: {change_amount}, Percent: {change_percent}, Volume: {volume}, Market Cap: {market_cap}")
                
                # Only proceed if we have at least a price
                if price:
                    # Create item
                    item = StockPriceItem()
                    item['symbol'] = symbol
                    item['price'] = float(price)
                    item['change_amount'] = float(change_amount) if change_amount is not None else 0.0
                    item['change_percent'] = float(change_percent) if change_percent is not None else 0.0
                    item['volume'] = int(volume) if volume else 0
                    item['market_cap'] = int(market_cap) if market_cap else 0
                    item['source'] = 'Yahoo Finance API'
                    item['scraped_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    return item
                else:
                    self.logger.warning(f"Quote API missing price data for {symbol}")
            else:
                self.logger.warning(f"Invalid Quote API response format for {symbol}")
        
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON from Quote API for {symbol}")
        except Exception as e:
            self.logger.error(f"Error processing Quote API data for {symbol}: {str(e)}")
    
    def parse_chart_api(self, response):
        """Parse stock data from Yahoo Finance Chart API"""
        symbol = response.meta['symbol']
        self.logger.info(f"Processing Chart API data for: {symbol}")
        
        try:
            # Parse JSON response
            data = json.loads(response.text)
            
            # Check if we have valid data
            if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                result = data['chart']['result'][0]
                
                # Extract price data
                meta = result.get('meta', {})
                
                # Current price
                price = meta.get('regularMarketPrice')
                
                # Previous close
                previous_close = meta.get('chartPreviousClose')
                
                # Calculate change
                change_amount = None
                change_percent = None
                if price is not None and previous_close is not None and previous_close > 0:
                    change_amount = price - previous_close
                    change_percent = (change_amount / previous_close) * 100
                
                # Volume
                volume = meta.get('regularMarketVolume')
                
                # Market cap - not typically available in chart API
                market_cap = meta.get('marketCap')
                
                # Debug information
                self.logger.info(f"Chart API data: Symbol: {symbol}, Price: {price}, Change: {change_amount}, Percent: {change_percent}, Volume: {volume}, Market Cap: {market_cap}")
                
                # Only proceed if we have at least a price
                if price:
                    # Create item
                    item = StockPriceItem()
                    item['symbol'] = symbol
                    item['price'] = float(price)
                    item['change_amount'] = float(change_amount) if change_amount is not None else 0.0
                    item['change_percent'] = float(change_percent) if change_percent is not None else 0.0
                    item['volume'] = int(volume) if volume else 0
                    item['market_cap'] = int(market_cap) if market_cap else 0
                    item['source'] = 'Yahoo Finance API'
                    item['scraped_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    return item
                else:
                    self.logger.warning(f"Chart API missing price data for {symbol}")
            else:
                self.logger.warning(f"Invalid Chart API response format for {symbol}")
        
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON from Chart API for {symbol}")
        except Exception as e:
            self.logger.error(f"Error processing Chart API data for {symbol}: {str(e)}")
    
    def safe_float(self, value):
        """Convert string to float safely"""
        if value is None:
            return 0.0
        try:
            # Remove any commas and other non-numeric characters except decimal and negative
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