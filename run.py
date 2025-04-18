import os
import sys
import subprocess
from threading import Thread
import time

def run_flask():
    os.chdir('web_app')
    try:
        subprocess.run(['python', 'app.py'], check=True)
    except KeyboardInterrupt:
        print("Flask server stopped")

def run_scrapy_spider():
    try:
        subprocess.run(['python', '-m', 'scrapy', 'crawl', 'financial_news'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running spider: {e}")

if __name__ == '__main__':
    # Start Flask in a separate thread
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True  # This thread will close when the main program ends
    flask_thread.start()
    
    # Give Flask a moment to start
    time.sleep(2)
    
    print("Flask server is running")
    print("Running Scrapy spider...")
    
    # Run the spider
    run_scrapy_spider()
    
    # Keep the main thread running to keep Flask alive
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("Shutting down...")
        sys.exit(0)