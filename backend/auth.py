"""
ShopNow - Online Shopping System
Authentication & Password Hashing Module (Pure Python)
"""

import hashlib
import re
from datetime import datetime
from database import execute_query
from config import SALT

# Fallback Mock In-Memory User Store (active before MySQL database import in Part 5)
MOCK_USERS = [
    {
        'user_id': 101,
        'name': 'John Doe',
        'email': 'john@example.com',
        'phone': '+1234567890',
        'password': hashlib.sha256(('123456' + SALT).encode('utf-8')).hexdigest(),
        'address': '123 University Campus St, Apt 4B, NY 10001',
        'created_at': '2026-09-01 10:00:00'
    }
]

def hash_password(password):
    """
    Hashes plain text password using SHA-256 cryptographic hash + Salt.
    """
    salted = password + SALT
    return hashlib.sha256(salted.encode('utf-8')).hexdigest()

def validate_email(email):
    """
    Validates email format using built-in regular expression.
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def register_user(data):
    """
    Registers a new customer account.
    """
    name = data.get('fullName', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    password = data.get('password', '')
    address = data.get('address', '').strip()

    # Validation
    if not name or not email or not password or not address:
        return {'success': False, 'message': 'All required fields must be filled.'}

    if not validate_email(email):
        return {'success': False, 'message': 'Invalid email format.'}

    if len(password) < 6:
        return {'success': False, 'message': 'Password must be at least 6 characters long.'}

    hashed_pwd = hash_password(password)

    # 1. Try MySQL Database
    existing_db_user = execute_query(
        "SELECT * FROM users WHERE email = %s",
        (email,),
        fetchone=True
    )

    if existing_db_user:
        return {'success': False, 'message': 'Email address is already registered.'}

    # Insert into DB if connected
    db_result = execute_query(
        "INSERT INTO users (name, email, phone, password, address, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
        (name, email, phone, hashed_pwd, address, datetime.now()),
        commit=True
    )

    if db_result:
        return {'success': True, 'message': 'Registration successful!'}

    # 2. Fallback memory check
    for u in MOCK_USERS:
        if u['email'].lower() == email.lower():
            return {'success': False, 'message': 'Email address is already registered.'}

    new_id = len(MOCK_USERS) + 101
    MOCK_USERS.append({
        'user_id': new_id,
        'name': name,
        'email': email,
        'phone': phone,
        'password': hashed_pwd,
        'address': address,
        'created_at': str(datetime.now())
    })

    return {'success': True, 'message': 'Registration successful!'}

def login_user(data):
    """
    Authenticates customer login credentials.
    """
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return {'success': False, 'message': 'Email and password are required.'}

    hashed_pwd = hash_password(password)

    # 1. Try DB
    db_user = execute_query(
        "SELECT user_id, name, email, phone, address, password FROM users WHERE email = %s",
        (email,),
        fetchone=True
    )

    if db_user:
        if db_user['password'] == hashed_pwd:
            del db_user['password']
            return {'success': True, 'message': 'Login successful!', 'user': db_user}
        else:
            return {'success': False, 'message': 'Invalid email or password.'}

    # 2. Try Fallback memory
    for u in MOCK_USERS:
        if u['email'].lower() == email.lower() and u['password'] == hashed_pwd:
            user_data = {
                'user_id': u['user_id'],
                'name': u['name'],
                'email': u['email'],
                'phone': u['phone'],
                'address': u['address']
            }
            return {'success': True, 'message': 'Login successful!', 'user': user_data}

    return {'success': False, 'message': 'Invalid email or password.'}

def update_profile(data):
    """
    Updates user personal information.
    """
    user_id = data.get('user_id')
    name = data.get('fullName', '').strip()
    phone = data.get('phone', '').strip()
    address = data.get('address', '').strip()

    if not user_id or not name:
        return {'success': False, 'message': 'User ID and Name required.'}

    # Update in DB
    execute_query(
        "UPDATE users SET name = %s, phone = %s, address = %s WHERE user_id = %s",
        (name, phone, address, user_id),
        commit=True
    )

    # Update in fallback memory
    for u in MOCK_USERS:
        if str(u['user_id']) == str(user_id):
            u['name'] = name
            u['phone'] = phone
            u['address'] = address
            break

    return {'success': True, 'message': 'Profile updated successfully!'}
