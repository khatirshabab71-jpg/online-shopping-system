"""
ShopNow - Online Shopping System
Database Connection & Query Execution Helper (Pure Python + MySQL Connector)
"""

import sys
from config import DB_CONFIG

# Attempt to import mysql.connector (Only external library allowed for MySQL connection)
try:
    import mysql.connector
    from mysql.connector import Error
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    print("WARNING: mysql-connector-python not installed yet. Running in fallback memory mode until Part 5 MySQL connection.")

def get_db_connection():
    """
    Establishes and returns a connection to the MySQL Database.
    """
    if not MYSQL_AVAILABLE:
        return None

    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        # Connection warnings captured gracefully
        return None
    return None

def execute_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    """
    Helper function to execute SQL statements safely with parametrized queries.
    Prevents SQL injection vulnerabilities.
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
            result = cursor.lastrowid
        elif fetchone:
            result = cursor.fetchone()
        elif fetchall:
            result = cursor.fetchall()

        cursor.close()
        conn.close()
        return result
    except Exception as err:
        print(f"Database Query Error: {err}")
        if conn:
            conn.close()
        return None
