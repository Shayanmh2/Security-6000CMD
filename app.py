from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from functools import wraps
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate random secret key for session management

# Database connection helper
def get_db_connection():
    conn = sqlite3.connect('ecommerce.db')
    conn.row_factory = sqlite3.Row
    return conn

# Activity logging helper
def log_activity(user_id, activity_type, details):
    conn = get_db_connection()
    conn.execute('INSERT INTO activity_logs (user_id, activity_type, details) VALUES (?, ?, ?)',
                (user_id, activity_type, details))
    conn.commit()
    conn.close()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Seller required decorator
def seller_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') not in ['seller', 'admin']:
            flash('Seller access required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Home page
@app.route('/')
def index():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products ORDER BY created_at DESC LIMIT 12').fetchall()
    conn.close()
    
    if 'user_id' in session:
        log_activity(session['user_id'], 'page_view', 'Viewed home page')
    
    return render_template('index.html', products=products)

# Register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)',
                        (username, email, hashed_password, 'customer'))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'danger')
            return redirect(url_for('register'))
        finally:
            conn.close()
    
    return render_template('register.html')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            log_activity(user['id'], 'login', 'User logged in')
            flash(f'Welcome back, {user["username"]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('login'))
    
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    if 'user_id' in session:
        log_activity(session['user_id'], 'logout', 'User logged out')
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# Profile page
@app.route('/profile')
@login_required
def profile():
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    return render_template('profile.html', user=user)

# Upgrade to seller
@app.route('/upgrade-to-seller', methods=['POST'])
@login_required
def upgrade_to_seller():
    conn = get_db_connection()
    conn.execute('UPDATE users SET role = ? WHERE id = ?', ('seller', session['user_id']))
    conn.commit()
    conn.close()
    
    session['role'] = 'seller'
    log_activity(session['user_id'], 'account_upgrade', 'Upgraded to seller account')
    flash('Your account has been upgraded to seller!', 'success')
    return redirect(url_for('profile'))

# Search products
@app.route('/search')
def search():
    query = request.args.get('q', '')
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products WHERE name LIKE ? OR description LIKE ?',
                           (f'%{query}%', f'%{query}%')).fetchall()
    conn.close()
    
    if 'user_id' in session:
        log_activity(session['user_id'], 'search', f'Searched for: {query}')
    
    return render_template('search.html', products=products, query=query)

# Product detail page
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    reviews = conn.execute('SELECT r.*, u.username FROM reviews r JOIN users u ON r.user_id = u.id WHERE r.product_id = ?', 
                          (product_id,)).fetchall()
    conn.close()
    
    if product is None:
        flash('Product not found.', 'danger')
        return redirect(url_for('index'))
    
    if 'user_id' in session:
        log_activity(session['user_id'], 'product_view', f'Viewed product: {product["name"]}')
    
    return render_template('product_detail.html', product=product, reviews=reviews)

# Purchase product
@app.route('/purchase/<int:product_id>', methods=['POST'])
@login_required
def purchase_product(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    
    if product:
        conn.execute('INSERT INTO transactions (product_id, buyer_id, seller_id, price) VALUES (?, ?, ?, ?)',
                    (product_id, session['user_id'], product['seller_id'], product['price']))
        conn.commit()
        log_activity(session['user_id'], 'purchase', f'Purchased: {product["name"]}')
        flash(f'Successfully purchased {product["name"]}!', 'success')
    else:
        flash('Product not found.', 'danger')
    
    conn.close()
    return redirect(url_for('product_detail', product_id=product_id))

# Add review
@app.route('/review/<int:product_id>', methods=['POST'])
@login_required
def add_review(product_id):
    rating = request.form.get('rating')
    comment = request.form.get('comment')
    
    conn = get_db_connection()
    conn.execute('INSERT INTO reviews (product_id, user_id, rating, comment) VALUES (?, ?, ?, ?)',
                (product_id, session['user_id'], rating, comment))
    conn.commit()
    conn.close()
    
    log_activity(session['user_id'], 'review', f'Reviewed product ID: {product_id}')
    flash('Review submitted successfully!', 'success')
    return redirect(url_for('product_detail', product_id=product_id))

# My purchases
@app.route('/my-purchases')
@login_required
def my_purchases():
    conn = get_db_connection()
    purchases = conn.execute('''
        SELECT t.*, p.name, p.description 
        FROM transactions t 
        JOIN products p ON t.product_id = p.id 
        WHERE t.buyer_id = ? 
        ORDER BY t.transaction_date DESC
    ''', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('my_purchases.html', purchases=purchases)

# Seller dashboard
@app.route('/seller/dashboard')
@seller_required
def seller_dashboard():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products WHERE seller_id = ?', (session['user_id'],)).fetchall()
    transactions = conn.execute('''
        SELECT t.*, p.name, u.username as buyer_name 
        FROM transactions t 
        JOIN products p ON t.product_id = p.id 
        JOIN users u ON t.buyer_id = u.id 
        WHERE t.seller_id = ?
        ORDER BY t.transaction_date DESC
    ''', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('seller_dashboard.html', products=products, transactions=transactions)

# Add product
@app.route('/seller/add-product', methods=['GET', 'POST'])
@seller_required
def add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        
        conn = get_db_connection()
        conn.execute('INSERT INTO products (name, description, price, seller_id) VALUES (?, ?, ?, ?)',
                    (name, description, price, session['user_id']))
        conn.commit()
        conn.close()
        
        log_activity(session['user_id'], 'product_add', f'Added product: {name}')
        flash('Product added successfully!', 'success')
        return redirect(url_for('seller_dashboard'))
    
    return render_template('add_product.html')

# Edit product
@app.route('/seller/edit-product/<int:product_id>', methods=['GET', 'POST'])
@seller_required
def edit_product(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ? AND seller_id = ?', 
                          (product_id, session['user_id'])).fetchone()
    
    if not product:
        flash('Product not found or you do not have permission.', 'danger')
        return redirect(url_for('seller_dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        
        conn.execute('UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?',
                    (name, description, price, product_id))
        conn.commit()
        conn.close()
        
        log_activity(session['user_id'], 'product_edit', f'Edited product: {name}')
        flash('Product updated successfully!', 'success')
        return redirect(url_for('seller_dashboard'))
    
    conn.close()
    return render_template('edit_product.html', product=product)

# Admin dashboard
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
    products = conn.execute('SELECT p.*, u.username as seller_name FROM products p JOIN users u ON p.seller_id = u.id').fetchall()
    conn.close()
    return render_template('admin_dashboard.html', users=users, products=products)

if __name__ == '__main__':
    app.run(debug=True)