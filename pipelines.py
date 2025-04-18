import mysql.connector
from mysql.connector import Error

class DatabasePipeline:
    def __init__(self):
        self.conn = None
        self.cur = None
    
    def open_spider(self, spider):
        try:
            # Update these with your MySQL credentials
            self.conn = mysql.connector.connect(
                host='localhost',
                port=3306,
                user='root',  # Change this
                password='12345',  # Change this
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
            # Check if article already exists
            check_sql = "SELECT id FROM financial_news WHERE link = %s"
            self.cur.execute(check_sql, (item.get('link', ''),))
            result = self.cur.fetchone()
            
            if result:
                # Update existing article
                update_sql = """
                UPDATE financial_news 
                SET title = %s, summary = %s, source = %s, scraped_date = %s
                WHERE link = %s
                """
                self.cur.execute(update_sql, (
                    item.get('title', ''),
                    item.get('summary', ''),
                    item.get('source', ''),
                    item.get('scraped_date', ''),
                    item.get('link', '')
                ))
                spider.logger.info(f"Updated article: {item.get('title', '')}")
            else:
                # Insert new article
                insert_sql = """
                INSERT INTO financial_news (title, link, summary, source, scraped_date) 
                VALUES (%s, %s, %s, %s, %s)
                """
                self.cur.execute(insert_sql, (
                    item.get('title', ''),
                    item.get('link', ''),
                    item.get('summary', ''),
                    item.get('source', ''),
                    item.get('scraped_date', '')
                ))
                spider.logger.info(f"Saved new article: {item.get('title', '')}")
                
            self.conn.commit()
            
        except Error as e:
            spider.logger.error(f"Error saving to database: {e}")
            
        return item