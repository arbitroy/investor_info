import os
import sys
import subprocess
from threading import Thread
import time
import schedule

def run_flask():
    os.chdir('web_app')
    try:
        subprocess.run(['python', 'app.py'], check=True)
    except KeyboardInterrupt:
        print("Flask server stopped")

def run_financial_news_spider():
    try:
        print("Running Financial News spider...")
        subprocess.run(['python', '-m', 'scrapy', 'crawl', 'financial_news'], check=True)
        print("Financial News spider completed")
    except subprocess.CalledProcessError as e:
        print(f"Error running Financial News spider: {e}")

def run_stock_prices_spider():
    try:
        print("Running Stock Prices spider...")
        subprocess.run(['python', '-m', 'scrapy', 'crawl', 'stock_prices'], check=True)
        print("Stock Prices spider completed")
    except subprocess.CalledProcessError as e:
        print(f"Error running Stock Prices spider: {e}")

def run_all_spiders():
    """Run all spiders sequentially"""
    run_financial_news_spider()
    run_stock_prices_spider()

def schedule_spiders():
    """Set up scheduled runs for the spiders"""
    # Run stock prices spider every 30 minutes (more frequent updates for price data)
    schedule.every(3).minutes.do(run_stock_prices_spider)
    
    # Run news spider every 2 hours
    schedule.every(2).hours.do(run_financial_news_spider)
    
    # Run both immediately on startup
    run_all_spiders()
    
    # Keep checking the schedule
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == '__main__':
    # Start Flask in a separate thread
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True  # This thread will close when the main program ends
    flask_thread.start()
    
    # Give Flask a moment to start
    time.sleep(2)
    
    print("Flask server is running")
    
    # Start the scheduler in a separate thread
    scheduler_thread = Thread(target=schedule_spiders)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    # Keep the main thread running to keep Flask alive
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("Shutting down...")
        sys.exit(0)