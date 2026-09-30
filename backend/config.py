"""
ShopNow - Online Shopping System
Backend Configuration Module
"""

import os

# Server Network Settings
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 8000

# MySQL Database Connection Credentials
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Update with your MySQL password
    'database': 'online_shopping',
    'port': 3306,
    'raise_on_warnings': True
}

# Base Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

# Security Settings
SALT = "ShopNowUniversityProject2026"
