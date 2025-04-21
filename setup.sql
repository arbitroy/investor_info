-- Database setup script for Investor Info application

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS investor_info;

-- Use the database
USE investor_info;

-- Create financial_news table
CREATE TABLE IF NOT EXISTS financial_news (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    link VARCHAR(512) UNIQUE NOT NULL,
    summary TEXT,
    content TEXT,
    source VARCHAR(100),
    publish_date VARCHAR(100),
    sentiment FLOAT DEFAULT 0,
    scraped_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL
);

-- Create bookmarks/favorites table
CREATE TABLE IF NOT EXISTS bookmarks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    news_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (news_id) REFERENCES financial_news(id) ON DELETE CASCADE,
    UNIQUE KEY user_news_unique (user_id, news_id)
);

-- Create stock_prices table
CREATE TABLE IF NOT EXISTS stock_prices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    price DECIMAL(10,2),
    change_amount DECIMAL(10,2),
    change_percent DECIMAL(10,2),
    volume BIGINT,
    market_cap BIGINT,
    source VARCHAR(100),
    scraped_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY symbol_date_unique (symbol, scraped_date)
);

-- Create user preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    watch_symbols TEXT,
    preferred_sources TEXT,
    theme VARCHAR(20) DEFAULT 'light',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indices for common query patterns
CREATE INDEX idx_fin_news_date ON financial_news(scraped_date);
CREATE INDEX idx_fin_news_source ON financial_news(source);
CREATE INDEX idx_stock_prices_symbol ON stock_prices(symbol);
CREATE INDEX idx_stock_prices_date ON stock_prices(scraped_date);