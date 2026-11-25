"""
ShopNow - Online Shopping System
Database Connection & Query Execution Helper (Pure Python + MySQL Connector)
"""

import sys
from config import DB_CONFIG

# Attempt to import mysql.connector (standard library/connector for MySQL)
try:
    import mysql.connector
    from mysql.connector import Error
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    print("WARNING: mysql-connector-python not installed. Please run: pip install mysql-connector-python")

def get_db_connection():
    """
    Establishes and returns a connection to the MySQL Database.
    Returns None if connection cannot be established.
    """
    if not MYSQL_AVAILABLE:
        return None

    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Database Connection Error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected Connection Error: {e}")
        return None
    return None

def execute_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    """
    Helper function to execute SQL statements safely with parameterized queries.
    Prevents SQL injection vulnerabilities.
    Returns:
      - lastrowid if commit=True
      - dict if fetchone=True
      - list of dicts if fetchall=True
      - True for commit without auto-increment
      - None if query fails or database is unavailable
    """
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)

        result = None
        if commit:
            conn.commit()
            result = cursor.lastrowid if cursor.lastrowid else True
        elif fetchone:
            result = cursor.fetchone()
        elif fetchall:
            result = cursor.fetchall()

        cursor.close()
        conn.close()
        return result
    except Exception as err:
        print(f"Database Query Error: {err}\nQuery: {query}\nParams: {params}")
        if conn:
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass
        return None

def init_db_schema():
    """
    Ensures essential tables and columns exist on the MySQL database.
    Includes Phase 2 tables: account_tokens, login_attempts, wishlist, reviews, order_status_history.
    Safe to call repeatedly on startup.
    """
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # 1. Ensure sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id VARCHAR(64) PRIMARY KEY,
                user_id INT NOT NULL,
                role ENUM('customer', 'admin') DEFAULT 'customer',
                ip_address VARCHAR(45) NULL,
                user_agent VARCHAR(255) NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # 2. Ensure account_tokens table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS account_tokens (
                token_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                token_hash VARCHAR(64) NOT NULL UNIQUE,
                token_type ENUM('email_verification', 'password_reset') NOT NULL,
                expires_at DATETIME NOT NULL,
                used_at DATETIME NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # 3. Ensure login_attempts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                attempt_id INT AUTO_INCREMENT PRIMARY KEY,
                identifier VARCHAR(100) NOT NULL,
                ip_address VARCHAR(45) NOT NULL,
                attempt_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                success TINYINT(1) DEFAULT 0
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # 4. Ensure wishlist table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wishlist (
                wishlist_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                product_id INT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_wishlist_user_prod (user_id, product_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # 5. Ensure reviews table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                review_id INT AUTO_INCREMENT PRIMARY KEY,
                product_id INT NOT NULL,
                user_id INT NOT NULL,
                rating INT NOT NULL,
                review_title VARCHAR(150) NOT NULL,
                review_text TEXT NOT NULL,
                is_verified_purchase TINYINT(1) DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_prod_user_rev (product_id, user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # 6. Ensure order_status_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_status_history (
                history_id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT NOT NULL,
                status VARCHAR(50) NOT NULL,
                changed_by VARCHAR(50) DEFAULT 'admin',
                notes VARCHAR(255) NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # 7. Ensure is_active column in products
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.columns 
            WHERE table_schema = %s AND table_name = 'products' AND column_name = 'is_active';
        """, (DB_CONFIG['database'],))
        col_active = cursor.fetchone()
        if col_active and col_active[0] == 0:
            cursor.execute("ALTER TABLE products ADD COLUMN is_active TINYINT(1) DEFAULT 1;")
            cursor.execute("UPDATE products SET is_active = 1 WHERE is_active IS NULL;")

        # 8. Ensure is_verified column in users
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.columns 
            WHERE table_schema = %s AND table_name = 'users' AND column_name = 'is_verified';
        """, (DB_CONFIG['database'],))
        col_verified = cursor.fetchone()
        if col_verified and col_verified[0] == 0:
            cursor.execute("ALTER TABLE users ADD COLUMN is_verified TINYINT(1) DEFAULT 0, ADD COLUMN email_verified_at DATETIME NULL;")
            cursor.execute("UPDATE users SET is_verified = 1 WHERE email IN ('john@example.com', 'jane@example.com');")

        conn.commit()
        cursor.close()
        conn.close()
        print("Database schema verified and updated successfully.")
        return True
    except Exception as e:
        print(f"Schema verification note: {e}")
        if conn:
            conn.close()
        return False
