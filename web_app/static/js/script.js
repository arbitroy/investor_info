/**
 * Custom JavaScript for Investor Info application
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 100 + (index * 50));
    });
    
    // Handle theme toggle if present
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('change', function() {
            document.body.classList.toggle('dark-theme');
            
            // Store preference in localStorage
            if (document.body.classList.contains('dark-theme')) {
                localStorage.setItem('theme', 'dark');
            } else {
                localStorage.setItem('theme', 'light');
            }
        });
        
        // Check for saved theme preference
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            document.body.classList.add('dark-theme');
            themeToggle.checked = true;
        }
    }
    
    // Automatically update relative timestamps
    updateRelativeTimes();
    setInterval(updateRelativeTimes, 60000); // Update every minute
    
    // Handle bookmark buttons with AJAX if available
    setupAjaxBookmarks();
    
    // Setup stock watchlist
    setupWatchlist();
    
    // Initialize search autocomplete if available
    initSearchAutocomplete();
});

/**
 * Updates all elements with the class 'relative-time' to show
 * a human-readable relative time (e.g., "2 hours ago")
 */
function updateRelativeTimes() {
    const timeElements = document.querySelectorAll('.relative-time');
    timeElements.forEach(element => {
        const timestamp = element.getAttribute('data-timestamp');
        if (timestamp) {
            element.textContent = getRelativeTimeString(new Date(timestamp));
        }
    });
}

/**
 * Converts a date to a relative time string (e.g., "2 hours ago")
 */
function getRelativeTimeString(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.round(diffMs / 1000);
    const diffMin = Math.round(diffSec / 60);
    const diffHr = Math.round(diffMin / 60);
    const diffDays = Math.round(diffHr / 24);
    
    if (diffSec < 60) {
        return diffSec + ' seconds ago';
    } else if (diffMin < 60) {
        return diffMin + ' minutes ago';
    } else if (diffHr < 24) {
        return diffHr + ' hours ago';
    } else if (diffDays < 30) {
        return diffDays + ' days ago';
    } else {
        // Format as MM/DD/YYYY for older dates
        return date.toLocaleDateString();
    }
}

/**
 * Sets up AJAX for bookmark functionality to avoid page reloads
 */
function setupAjaxBookmarks() {
    const bookmarkForms = document.querySelectorAll('.bookmark-form');
    bookmarkForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const newsId = this.getAttribute('data-news-id');
            const bookmarkButton = this.querySelector('button');
            const isBookmarked = bookmarkButton.classList.contains('btn-warning');
            
            // Show loading state
            bookmarkButton.disabled = true;
            bookmarkButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
            
            // Perform AJAX request
            fetch('/bookmark/' + newsId, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (isBookmarked) {
                        // Remove bookmark
                        bookmarkButton.classList.replace('btn-warning', 'btn-outline-secondary');
                        bookmarkButton.innerHTML = '<i class="far fa-bookmark"></i> Save';
                    } else {
                        // Add bookmark
                        bookmarkButton.classList.replace('btn-outline-secondary', 'btn-warning');
                        bookmarkButton.innerHTML = '<i class="fas fa-bookmark"></i> Saved';
                    }
                } else {
                    // If there was an error, restore original state
                    bookmarkButton.innerHTML = isBookmarked ? 
                        '<i class="fas fa-bookmark"></i> Saved' : 
                        '<i class="far fa-bookmark"></i> Save';
                    
                    // Show error message
                    alert('Error: ' + (data.message || 'Could not update bookmark'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                bookmarkButton.innerHTML = isBookmarked ? 
                    '<i class="fas fa-bookmark"></i> Saved' : 
                    '<i class="far fa-bookmark"></i> Save';
            })
            .finally(() => {
                bookmarkButton.disabled = false;
            });
        });
    });
}

/**
 * Sets up the stock watchlist with real-time updates
 */
function setupWatchlist() {
    const watchlistContainer = document.getElementById('watchlist');
    if (!watchlistContainer) return;
    
    // Refresh watchlist data every 5 minutes
    updateWatchlistData();
    setInterval(updateWatchlistData, 300000);
    
    function updateWatchlistData() {
        const symbols = watchlistContainer.getAttribute('data-symbols');
        if (!symbols) return;
        
        // Add loading indicator
        watchlistContainer.classList.add('loading');
        
        fetch('/api/stocks?symbols=' + symbols)
            .then(response => response.json())
            .then(data => {
                // Remove loading indicator
                watchlistContainer.classList.remove('loading');
                
                // Update each stock card with new data
                data.forEach(stock => {
                    const stockCard = document.querySelector(`.stock-card[data-symbol="${stock.symbol}"]`);
                    if (stockCard) {
                        const priceEl = stockCard.querySelector('.stock-price');
                        const changeEl = stockCard.querySelector('.stock-change');
                        
                        if (priceEl) priceEl.textContent = ' + stock.price';
                        
                        if (changeEl) {
                            changeEl.textContent = stock.change_amount + ' (' + stock.change_percent + '%)';
                            changeEl.className = 'stock-change';
                            if (stock.change_amount > 0) {
                                changeEl.classList.add('text-success');
                            } else if (stock.change_amount < 0) {
                                changeEl.classList.add('text-danger');
                            }
                        }
                    }
                });
            })
            .catch(error => {
                console.error('Error updating watchlist:', error);
                watchlistContainer.classList.remove('loading');
            });
    }
}

/**
 * Initializes search autocomplete functionality
 */
function initSearchAutocomplete() {
    const searchInput = document.querySelector('input[name="q"]');
    if (!searchInput) return;
    
    let timeoutId;
    
    searchInput.addEventListener('input', function() {
        clearTimeout(timeoutId);
        
        const query = this.value.trim();
        if (query.length < 2) return;
        
        // Add a small delay to prevent too many requests while typing
        timeoutId = setTimeout(() => {
            fetch('/api/search/autocomplete?q=' + encodeURIComponent(query))
                .then(response => response.json())
                .then(data => {
                    // Create or update autocomplete dropdown
                    let dropdown = document.getElementById('search-autocomplete');
                    
                    if (!dropdown) {
                        dropdown = document.createElement('div');
                        dropdown.id = 'search-autocomplete';
                        dropdown.className = 'dropdown-menu';
                        searchInput.parentNode.appendChild(dropdown);
                    }
                    
                    // Clear previous results
                    dropdown.innerHTML = '';
                    
                    if (data.length > 0) {
                        // Show dropdown
                        dropdown.classList.add('show');
                        
                        // Add results
                        data.forEach(item => {
                            const option = document.createElement('a');
                            option.className = 'dropdown-item';
                            option.href = '#';
                            option.textContent = item;
                            option.addEventListener('click', function(e) {
                                e.preventDefault();
                                searchInput.value = item;
                                dropdown.classList.remove('show');
                                searchInput.closest('form').submit();
                            });
                            dropdown.appendChild(option);
                        });
                    } else {
                        dropdown.classList.remove('show');
                    }
                })
                .catch(error => {
                    console.error('Error with autocomplete:', error);
                });
        }, 300);
    });
    
    // Hide dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target)) {
            const dropdown = document.getElementById('search-autocomplete');
            if (dropdown) {
                dropdown.classList.remove('show');
            }
        }
    });
}