from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from sqlalchemy import or_, desc, func
import os
from extensions import db, login_manager
from models import User, FinancialNews, Bookmark, StockPrice, UserPreference

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_change_in_production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', 'mysql+pymysql://root:12345@localhost/investor_info')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize db and login_manager with the app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home page
@app.route('/')
def home():
    # Get the latest news articles
    news = FinancialNews.query.order_by(FinancialNews.scraped_date.desc()).limit(10).all()
    
    # Get stock data for major indexes
    major_indexes = ["^GSPC", "^DJI", "^IXIC", "^FTSE", "^N225"]
    index_data = StockPrice.query.filter(StockPrice.symbol.in_(major_indexes)).all()
    
    # Get stock data for top trending stocks
    trending_stocks = StockPrice.query.order_by(
        desc(func.abs(StockPrice.change_percent))
    ).limit(5).all()
    
    return render_template('index.html', 
                          news=news, 
                          index_data=index_data,
                          trending_stocks=trending_stocks)

# Stock details page
@app.route('/stock/<symbol>')
def stock_detail(symbol):
    # Get the latest stock data for the symbol
    stock = StockPrice.query.filter_by(symbol=symbol).order_by(StockPrice.scraped_date.desc()).first()
    
    if not stock:
        flash('Stock symbol not found', 'danger')
        return redirect(url_for('home'))
    
    # Get historical data (last 7 days)
    seven_days_ago = datetime.now() - timedelta(days=7)
    historical_data = StockPrice.query.filter_by(symbol=symbol)\
        .filter(StockPrice.scraped_date >= seven_days_ago)\
        .order_by(StockPrice.scraped_date).all()
    
    # Get related news articles
    related_news = FinancialNews.query.filter(
        or_(
            FinancialNews.title.contains(symbol),
            FinancialNews.summary.contains(symbol),
            FinancialNews.content.contains(symbol)
        )
    ).order_by(FinancialNews.scraped_date.desc()).limit(5).all()
    
    return render_template('stock_detail.html', 
                          stock=stock, 
                          historical_data=historical_data,
                          related_news=related_news)

# Search functionality
@app.route('/search')
def search():
    query = request.args.get('q', '')
    source = request.args.get('source', '')
    date_range = request.args.get('date_range', 'all')
    
    if not query:
        return redirect(url_for('home'))
    
    # Build base query
    base_query = FinancialNews.query.filter(
        or_(
            FinancialNews.title.contains(query),
            FinancialNews.summary.contains(query),
            FinancialNews.content.contains(query)
        )
    )
    
    # Apply source filter if specified
    if source:
        base_query = base_query.filter(FinancialNews.source == source)
    
    # Apply date filter
    if date_range == 'today':
        today = datetime.now().date()
        base_query = base_query.filter(func.date(FinancialNews.scraped_date) == today)
    elif date_range == 'week':
        week_ago = datetime.now() - timedelta(days=7)
        base_query = base_query.filter(FinancialNews.scraped_date >= week_ago)
    elif date_range == 'month':
        month_ago = datetime.now() - timedelta(days=30)
        base_query = base_query.filter(FinancialNews.scraped_date >= month_ago)
    
    # Get available sources for filter dropdown
    sources = db.session.query(FinancialNews.source).distinct().all()
    sources = [s[0] for s in sources if s[0]]  # Clean up the sources list
    
    # Execute the query and get results
    news = base_query.order_by(FinancialNews.scraped_date.desc()).all()
    
    return render_template('search.html', 
                          news=news, 
                          query=query,
                          current_source=source,
                          current_date_range=date_range,
                          sources=sources)

# News detail page
@app.route('/news/<int:news_id>')
def news_detail(news_id):
    news = FinancialNews.query.get_or_404(news_id)
    
    # Determine if the current user has bookmarked this article
    is_bookmarked = False
    if current_user.is_authenticated:
        bookmark = Bookmark.query.filter_by(user_id=current_user.id, news_id=news_id).first()
        is_bookmarked = bookmark is not None
    
    # Get related news based on content similarity
    # This is a simple implementation - could be improved with NLP
    words_in_title = set(news.title.lower().split())
    related_news = FinancialNews.query.filter(
        FinancialNews.id != news_id,
        FinancialNews.source == news.source
    ).order_by(FinancialNews.scraped_date.desc()).limit(10).all()
    
    # Filter to find truly related articles
    filtered_related = []
    for article in related_news:
        article_words = set(article.title.lower().split())
        if len(words_in_title.intersection(article_words)) >= 2:
            filtered_related.append(article)
        if len(filtered_related) >= 3:  # Limit to 3 related articles
            break
    
    return render_template('news_detail.html', 
                          news=news,
                          is_bookmarked=is_bookmarked,
                          related_news=filtered_related)

# User registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        # Validate form data
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return render_template('register.html')
            
        if password != password_confirm:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return render_template('register.html')
            
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'danger')
            return render_template('register.html')
        
        # Create new user
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        # Create default user preferences
        preferences = UserPreference(user=new_user)
        
        db.session.add(new_user)
        db.session.add(preferences)
        db.session.commit()
        
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Redirect to requested page or home
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

# User logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# User profile page
@app.route('/profile')
@login_required
def profile():
    # Get user bookmarks with news information
    bookmarks = Bookmark.query.filter_by(user_id=current_user.id).order_by(Bookmark.created_at.desc()).all()
    
    # Get user preferences
    preferences = current_user.preferences
    if not preferences:
        preferences = UserPreference(user=current_user)
        db.session.add(preferences)
        db.session.commit()
    
    # Get stock data for watched symbols
    watched_stocks = []
    if preferences.watch_symbols:
        symbols = preferences.get_watch_symbols()
        for symbol in symbols:
            stock = StockPrice.query.filter_by(symbol=symbol).order_by(StockPrice.scraped_date.desc()).first()
            if stock:
                watched_stocks.append(stock)
    
    return render_template('profile.html',
                          user=current_user,
                          bookmarks=bookmarks,
                          preferences=preferences,
                          watched_stocks=watched_stocks)

# Update user preferences
@app.route('/preferences', methods=['POST'])
@login_required
def update_preferences():
    # Get form data
    theme = request.form.get('theme', 'light')
    watch_symbols = request.form.get('watch_symbols', '')
    preferred_sources = request.form.getlist('preferred_sources')
    
    # Clean and validate watch symbols
    symbols = [s.strip().upper() for s in watch_symbols.split(',') if s.strip()]
    
    # Get or create user preferences
    preferences = current_user.preferences
    if not preferences:
        preferences = UserPreference(user=current_user)
        db.session.add(preferences)
    
    # Update preferences
    preferences.theme = theme
    preferences.set_watch_symbols(symbols)
    preferences.set_preferred_sources(preferred_sources)
    
    db.session.commit()
    
    flash('Preferences updated successfully', 'success')
    return redirect(url_for('profile'))

# Bookmark functionality
@app.route('/bookmark/<int:news_id>', methods=['POST'])
@login_required
def toggle_bookmark(news_id):
    news = FinancialNews.query.get_or_404(news_id)
    
    # Check if already bookmarked
    bookmark = Bookmark.query.filter_by(user_id=current_user.id, news_id=news_id).first()
    
    if bookmark:
        # Remove bookmark
        db.session.delete(bookmark)
        db.session.commit()
        flash('Bookmark removed', 'info')
    else:
        # Add bookmark
        bookmark = Bookmark(user_id=current_user.id, news_id=news_id)
        db.session.add(bookmark)
        db.session.commit()
        flash('Bookmark added', 'success')
    
    # Redirect back to the referring page
    return redirect(request.referrer or url_for('news_detail', news_id=news_id))

# View bookmarks
@app.route('/bookmarks')
@login_required
def bookmarks():
    user_bookmarks = Bookmark.query.filter_by(user_id=current_user.id).order_by(Bookmark.created_at.desc()).all()
    
    return render_template('bookmarks.html', bookmarks=user_bookmarks)

# API endpoint for stock data (for charts)
@app.route('/api/stock/<symbol>/history')
def stock_history_api(symbol):
    days = request.args.get('days', 30, type=int)
    start_date = datetime.now() - timedelta(days=days)
    
    # Get historical data
    history = StockPrice.query.filter_by(symbol=symbol)\
        .filter(StockPrice.scraped_date >= start_date)\
        .order_by(StockPrice.scraped_date).all()
    
    # Format data for chart
    data = [{
        'date': stock.scraped_date.strftime('%Y-%m-%d'),
        'price': stock.price,
        'volume': stock.volume
    } for stock in history]
    
    return jsonify(data)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        # Create all tables if they don't exist
        db.create_all()
    app.run(debug=True)


def analyze_content_relevance(sample_size=100):
    """Analyze the relevance of collected articles to financial decision-making"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get a random sample of articles
    cursor.execute("""
        SELECT id, title, summary 
        FROM financial_news
        ORDER BY RAND()
        LIMIT %s
    """, (sample_size,))
    
    articles = cursor.fetchall()
    
    # Define relevance categories and associated keywords
    relevance_categories = {
        'investment': ['stocks', 'bonds', 'invest', 'portfolio', 'dividend', 'yield'],
        'market_analysis': ['market', 'trend', 'analysis', 'forecast', 'prediction'],
        'company_performance': ['earnings', 'revenue', 'profit', 'loss', 'performance'],
        'economic_indicators': ['gdp', 'inflation', 'unemployment', 'interest rate', 'fed'],
        'irrelevant': ['celebrity', 'entertainment', 'sports', 'weather', 'politics']
    }
    
    # Analyze each article
    results = {category: 0 for category in relevance_categories}
    total_relevant = 0
    
    for article in articles:
        content = f"{article['title']} {article['summary'] or ''}".lower()
        max_score = 0
        best_category = None
        
        for category, keywords in relevance_categories.items():
            score = sum(1 for keyword in keywords if keyword in content)
            if score > max_score:
                max_score = score
                best_category = category
        
        results[best_category] += 1
        if best_category != 'irrelevant':
            total_relevant += 1
    
    # Calculate percentage relevant
    percent_relevant = (total_relevant / sample_size) * 100
    
    # Print results
    print(f"Content relevance analysis of {sample_size} articles:")
    for category, count in results.items():
        print(f"  {category}: {count} articles ({count/sample_size*100:.1f}%)")
    print(f"Total relevant to financial decision-making: {percent_relevant:.1f}%")
    
    return results, percent_relevant


