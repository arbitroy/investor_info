# Investor Info Web Application

A comprehensive financial data aggregation and presentation web application that collects, organizes, and presents financial data from various reliable online sources.

## Features

- **Financial News Scraping**: Collects financial news articles from Yahoo Finance, Reuters, and CNBC
- **Stock Price Data**: Tracks and displays current and historical stock prices 
- **User Accounts**: User registration and personalized experience
- **Bookmarks**: Save articles for future reference
- **Stock Watchlist**: Track your favorite stocks
- **Search Functionality**: Find articles and stocks by keywords
- **Dark/Light Theme**: Choose your preferred theme

## Technology Stack

- **Backend**: Python, Flask
- **Frontend**: HTML, CSS (Bootstrap 5), JavaScript
- **Database**: MySQL/MariaDB
- **Web Scraping**: Scrapy, BeautifulSoup

## Installation and Setup

### Prerequisites

- Python 3.8+
- MySQL/MariaDB
- pip

### Database Setup

1. Create a database named `investor_info`:

```sql
CREATE DATABASE investor_info CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. The application will automatically create the necessary tables when it first runs.

### Application Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd investor-info
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:

```bash
pip install -r requirements.txt
```

4. Set environment variables (optional, default values are provided):

```bash
# Database connection
export DB_HOST=localhost
export DB_PORT=3306
export DB_USER=root
export DB_PASSWORD=your_password
export DB_NAME=investor_info

# Flask
export SECRET_KEY=your_secret_key
```

### Running the Application

Run the application with:

```bash
python run.py
```

This will:
1. Start the Flask web server
2. Run both the financial news and stock prices spiders
3. Keep the application running

The web application will be available at `http://localhost:5000`

## Usage

1. **Register an account**: Create a new account to personalize your experience
2. **Configure preferences**: Set your theme preference and stocks to watch
3. **Browse news**: View the latest financial news from various sources
4. **Track stocks**: Monitor stock prices and performance
5. **Bookmark articles**: Save articles for later reference
6. **Search functionality**: Find specific news or information

## Scheduled Data Updates

The application automatically updates:
- Stock price data every 30 minutes
- Financial news every 2 hours

## License

[MIT License](LICENSE)