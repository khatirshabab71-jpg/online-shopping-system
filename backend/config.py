"""
ShopNow - Online Shopping System
Backend Configuration Module (Phase 2 Production Ready)
"""

import os
import tempfile

IS_VERCEL = os.environ.get("VERCEL") == "1"

# Server Network Settings
SERVER_HOST = os.environ.get('SERVER_HOST', '0.0.0.0')
SERVER_PORT = int(os.environ.get('SERVER_PORT', 8000))
APP_URL = os.environ.get('APP_URL', f'http://localhost:{SERVER_PORT}')

# Security & Session Settings
SECRET_KEY = os.environ.get('SECRET_KEY', 'ShopNowSecuritySuperSecretKey2026')
SESSION_EXPIRY_DAYS = int(os.environ.get('SESSION_EXPIRY_DAYS', 7))
VERIFICATION_TOKEN_HOURS = int(os.environ.get('VERIFICATION_TOKEN_HOURS', 24))
PASSWORD_RESET_MINUTES = int(os.environ.get('PASSWORD_RESET_MINUTES', 30))
MAX_LOGIN_ATTEMPTS = int(os.environ.get('MAX_LOGIN_ATTEMPTS', 5))
LOGIN_LOCKOUT_MINUTES = int(os.environ.get('LOGIN_LOCKOUT_MINUTES', 15))

# HTTPS / SSL Configuration (Optional for production deployment)
USE_HTTPS = os.environ.get('USE_HTTPS', 'false').lower() == 'true'
SSL_CERT_FILE = os.environ.get('SSL_CERT_FILE', '')
SSL_KEY_FILE = os.environ.get('SSL_KEY_FILE', '')

# MySQL Database Connection Credentials
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')  # Set DB_PASSWORD env var or enter here locally
DB_NAME = os.environ.get('DB_NAME', 'online_shopping')
DB_PORT = int(os.environ.get('DB_PORT', 3306))

DB_CONFIG = {
    'host': DB_HOST,
    'user': DB_USER,
    'password': DB_PASSWORD,
    'database': DB_NAME,
    'port': DB_PORT,
    'raise_on_warnings': True,
    'connection_timeout': 8
}

# Remote MySQL TLS. Supply the CA certificate PEM in DB_SSL_CA_PEM on Vercel.
if IS_VERCEL or os.environ.get('DB_SSL_VERIFY', 'false').lower() == 'true':
    DB_CONFIG.update(ssl_disabled=False, ssl_verify_cert=True, ssl_verify_identity=True)
    ca_pem = os.environ.get('DB_SSL_CA_PEM', '')
    ca_file = os.environ.get('DB_SSL_CA', '')
    if ca_pem:
        ca_file = os.path.join(tempfile.gettempdir(), 'shopnow-mysql-ca.pem')
        with open(ca_file, 'w', encoding='utf-8') as cert_file:
            cert_file.write(ca_pem.replace('\\n', '\n'))
    if ca_file:
        DB_CONFIG['ssl_ca'] = ca_file

# SMTP Email Configuration
SMTP_HOST = os.environ.get('SMTP_HOST', '')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
SMTP_USE_TLS = os.environ.get('SMTP_USE_TLS', 'true').lower() == 'true'
SMTP_FROM_EMAIL = os.environ.get('SMTP_FROM_EMAIL', 'no-reply@shopnow.edu')
SMTP_FROM_NAME = os.environ.get('SMTP_FROM_NAME', 'ShopNow Online Store')

# Base Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')
LOGS_DIR = os.path.join(tempfile.gettempdir(), 'shopnow-logs') if IS_VERCEL else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')

# Shipping Configuration
FIXED_SHIPPING_FEE = 15.00
