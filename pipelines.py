import mysql.connector
from mysql.connector import Error
import logging
from investor_info.items import FinancialNewsItem, StockPriceItem

class DatabasePipeline:
    def __init__(self):
        self.conn = None
        self.cur = None
        self.logger = logging.getLogger(__name__)
    
    def open_spider(self, spider):
        try:
            # Update these with your MySQL credentials - consider using environment variables
            self.conn = mysql.connector.connect(
                host='localhost',
                port=3306,
                user='root',  # Change this or use environment variables
                password='12345',  # Change this or use environment variables
                database='investor_info'
            )
            if self.conn.is_connected():
                self.cur = self.conn.cursor()
                spider.logger.info("Connected to MySQL database")
        except Error as e:
            spider.logger.error(f"Error connecting to MySQL: {e}")
    
    def close_spider(self, spider):
        if self.conn and self.conn.is_connected():
            self.cur.close()
            self.conn.close()
            spider.logger.info("MySQL connection closed")
    
    def process_item(self, item, spider):
        if not self.conn or not self.conn.is_connected():
            spider.logger.error("No database connection available")
            return item
            
        try:
            if isinstance(item, FinancialNewsItem):
                return self._process_news_item(item, spider)
            elif isinstance(item, StockPriceItem):
                return self._process_stock_item(item, spider)
            else:
                spider.logger.warning(f"Unknown item type: {type(item)}")
                return item
        except Error as e:
            spider.logger.error(f"Error processing item: {e}")
            return item
            
    def _process_news_item(self, item, spider):
        try:
            # Check if article already exists
            check_sql = "SELECT id FROM financial_news WHERE link = %s"
            self.cur.execute(check_sql, (item.get('link', ''),))
            result = self.cur.fetchone()
            
            if result:
                # Update existing article
                update_sql = """
                UPDATE financial_news 
                SET title = %s, summary = %s, content = %s, source = %s, 
                    publish_date = %s, sentiment = %s, scraped_date = %s
                WHERE link = %s
                """
                self.cur.execute(update_sql, (
                    item.get('title', ''),
                    item.get('summary', ''),
                    item.get('content', ''),
                    item.get('source', ''),
                    item.get('publish_date', ''),
                    item.get('sentiment', 0.0),
                    item.get('scraped_date', ''),
                    item.get('link', '')
                ))
                spider.logger.info(f"Updated article: {item.get('title', '')}")
            else:
                # Insert new article
                insert_sql = """
                INSERT INTO financial_news 
                (title, link, summary, content, source, publish_date, sentiment, scraped_date) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                self.cur.execute(insert_sql, (
                    item.get('title', ''),
                    item.get('link', ''),
                    item.get('summary', ''),
                    item.get('content', ''),
                    item.get('source', ''),
                    item.get('publish_date', ''),
                    item.get('sentiment', 0.0),
                    item.get('scraped_date', '')
                ))
                spider.logger.info(f"Saved new article: {item.get('title', '')}")
                
            self.conn.commit()
            
        except Error as e:
            spider.logger.error(f"Error saving to database: {e}")
            
        return item
        
    def _process_stock_item(self, item, spider):
        try:
            # Check if stock price already exists for this symbol and date
            check_sql = """
            SELECT id FROM stock_prices 
            WHERE symbol = %s AND DATE(scraped_date) = DATE(%s)
            """
            self.cur.execute(check_sql, (
                item.get('symbol', ''),
                item.get('scraped_date', '')
            ))
            result = self.cur.fetchone()
            
            if result:
                # Update existing stock price
                update_sql = """
                UPDATE stock_prices 
                SET price = %s, change_amount = %s, change_percent = %s,
                    volume = %s, market_cap = %s, source = %s
                WHERE symbol = %s AND DATE(scraped_date) = DATE(%s)
                """
                self.cur.execute(update_sql, (
                    item.get('price', 0.0),
                    item.get('change_amount', 0.0),
                    item.get('change_percent', 0.0),
                    item.get('volume', 0),
                    item.get('market_cap', 0),
                    item.get('source', ''),
                    item.get('symbol', ''),
                    item.get('scraped_date', '')
                ))
                spider.logger.info(f"Updated stock price for {item.get('symbol', '')}")
            else:
                # Insert new stock price
                insert_sql = """
                INSERT INTO stock_prices 
                (symbol, price, change_amount, change_percent, volume, market_cap, source, scraped_date) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                self.cur.execute(insert_sql, (
                    item.get('symbol', ''),
                    item.get('price', 0.0),
                    item.get('change_amount', 0.0),
                    item.get('change_percent', 0.0),
                    item.get('volume', 0),
                    item.get('market_cap', 0),
                    item.get('source', ''),
                    item.get('scraped_date', '')
                ))
                spider.logger.info(f"Saved new stock price for {item.get('symbol', '')}")
                
            self.conn.commit()
            
        except Error as e:
            spider.logger.error(f"Error saving stock price to database: {e}")
            
        return item