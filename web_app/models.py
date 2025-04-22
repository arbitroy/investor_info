from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    bookmarks = db.relationship('Bookmark', backref='user', lazy='dynamic')
    preferences = db.relationship('UserPreference', backref='user', uselist=False)
    
    def set_password(self, password):
        # Use method='pbkdf2:sha256' to generate shorter hashes
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class FinancialNews(db.Model):
    __tablename__ = 'financial_news'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(512), unique=True, nullable=False)
    summary = db.Column(db.Text)
    content = db.Column(db.Text)
    source = db.Column(db.String(100))
    publish_date = db.Column(db.String(100))
    sentiment = db.Column(db.Float, default=0)
    scraped_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    bookmarks = db.relationship('Bookmark', backref='news', lazy='dynamic')
    
    def __repr__(self):
        return f'<FinancialNews {self.title}>'

class Bookmark(db.Model):
    __tablename__ = 'bookmarks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    news_id = db.Column(db.Integer, db.ForeignKey('financial_news.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Bookmark {self.id}>'

class StockPrice(db.Model):
    __tablename__ = 'stock_prices'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    price = db.Column(db.Float)
    change_amount = db.Column(db.Float)
    change_percent = db.Column(db.Float)
    volume = db.Column(db.BigInteger)
    market_cap = db.Column(db.BigInteger)
    source = db.Column(db.String(100))
    scraped_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<StockPrice {self.symbol}>'

class UserPreference(db.Model):
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    watch_symbols = db.Column(db.Text)
    preferred_sources = db.Column(db.Text)
    theme = db.Column(db.String(20), default='light')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_watch_symbols(self):
        """Return watch_symbols as a list"""
        if not self.watch_symbols:
            return []
        return self.watch_symbols.split(',')
    
    def set_watch_symbols(self, symbols_list):
        """Set watch_symbols from a list"""
        if not symbols_list:
            self.watch_symbols = ''
        else:
            self.watch_symbols = ','.join(symbols_list)
    
    def get_preferred_sources(self):
        """Return preferred_sources as a list"""
        if not self.preferred_sources:
            return []
        return self.preferred_sources.split(',')
    
    def set_preferred_sources(self, sources_list):
        """Set preferred_sources from a list"""
        if not sources_list:
            self.preferred_sources = ''
        else:
            self.preferred_sources = ','.join(sources_list)
    
    def __repr__(self):
        return f'<UserPreference for User {self.user_id}>'