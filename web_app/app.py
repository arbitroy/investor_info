from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from extensions import db, login_manager  # Import from extensions.py instead
from flask_login import login_user, logout_user, login_required, current_user
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:12345@localhost/investor_info'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize db and login_manager with the app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

# Import models AFTER db is initialized to avoid circular imports
from models import User, FinancialNews, Bookmark

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home page
@app.route('/')
def home():
    # Get the latest news articles
    news = FinancialNews.query.order_by(FinancialNews.scraped_date.desc()).limit(10).all()
    return render_template('index.html', news=news)

# Search functionality
@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('home'))
    
    # Search for news that match the query in title or summary
    news = FinancialNews.query.filter(
        (FinancialNews.title.contains(query)) | 
        (FinancialNews.summary.contains(query))
    ).order_by(FinancialNews.scraped_date.desc()).all()
    
    return render_template('search.html', news=news, query=query)

# User registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        
        # Create new user
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password')
    
    return render_template('login.html')

# User logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# Bookmark functionality
@app.route('/bookmark/<int:news_id>', methods=['POST'])
@login_required
def bookmark(news_id):
    news = FinancialNews.query.get_or_404(news_id)
    
    # Check if already bookmarked
    if Bookmark.query.filter_by(user_id=current_user.id, news_id=news_id).first():
        flash('Already bookmarked')
    else:
        bookmark = Bookmark(user_id=current_user.id, news_id=news_id)
        db.session.add(bookmark)
        db.session.commit()
        flash('Bookmark added')
    
    return redirect(url_for('news_detail', news_id=news_id))

# View bookmarks
@app.route('/bookmarks')
@login_required
def bookmarks():
    user_bookmarks = Bookmark.query.filter_by(user_id=current_user.id).all()
    bookmarked_news = [bookmark.news for bookmark in user_bookmarks]
    
    return render_template('bookmarks.html', news=bookmarked_news)

# News detail page
@app.route('/news/<int:news_id>')
def news_detail(news_id):
    news = FinancialNews.query.get_or_404(news_id)
    return render_template('news_detail.html', news=news)

if __name__ == '__main__':
    app.run(debug=True)