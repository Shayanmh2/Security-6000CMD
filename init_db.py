import sqlite3
from werkzeug.security import generate_password_hash

def init_database():
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'customer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            seller_id INTEGER,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (seller_id) REFERENCES users (id)
        )
    ''')
    
    # Reviews table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            rating INTEGER NOT NULL,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            buyer_id INTEGER NOT NULL,
            seller_id INTEGER NOT NULL,
            price REAL NOT NULL,
            transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id),
            FOREIGN KEY (buyer_id) REFERENCES users (id),
            FOREIGN KEY (seller_id) REFERENCES users (id)
        )
    ''')
    
    # Activity logs table for analytics
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            activity_type TEXT NOT NULL,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create admin account
    admin_password = generate_password_hash('admin123')
    try:
        cursor.execute('INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)',
                      ('admin', 'admin@example.com', admin_password, 'admin'))
    except sqlite3.IntegrityError:
        pass  # Admin already exists
    
    # Create sample seller account
    seller_password = generate_password_hash('seller123')
    try:
        cursor.execute('INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)',
                      ('seller1', 'seller@example.com', seller_password, 'seller'))
    except sqlite3.IntegrityError:
        pass
    
    # Create sample products
    sample_products = [
        ('Laptop', 'High performance laptop', 999.99, 2),
        ('Wireless Mouse', 'Ergonomic wireless mouse', 29.99, 2),
        ('Keyboard', 'Mechanical keyboard', 79.99, 2),
        ('Monitor', '27 inch 4K monitor', 349.99, 2),
    ]
    
    for product in sample_products:
        try:
            cursor.execute('INSERT INTO products (name, description, price, seller_id) VALUES (?, ?, ?, ?)', product)
        except sqlite3.IntegrityError:
            pass
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == '__main__':
    init_database()