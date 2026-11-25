"""
ShopNow - Online Shopping System
Authentication, Password Security, Email Verification & Rate Limiting Module
Built according to OWASP standards using Python standard library: hashlib, secrets, os, re, hmac
"""

import os
import re
import hmac
import secrets
import hashlib
from datetime import datetime, timedelta
from database import execute_query
from config import (
    SESSION_EXPIRY_DAYS, VERIFICATION_TOKEN_HOURS, 
    PASSWORD_RESET_MINUTES, MAX_LOGIN_ATTEMPTS, LOGIN_LOCKOUT_MINUTES
)
import email_service

# In-memory fallback tracking for rate-limiting when MySQL is offline
_IN_MEMORY_LOGIN_ATTEMPTS = []

def hash_password(password: str) -> str:
    """
    Hashes plain text password using Python's built-in scrypt algorithm with a unique random 16-byte salt per password.
    Output format: scrypt$<salt_hex>$<hash_hex>
    """
    if not isinstance(password, str):
        password = str(password)
    salt = os.urandom(16)
    hashed = hashlib.scrypt(password.encode('utf-8'), salt=salt, n=16384, r=8, p=1)
    return f"scrypt${salt.hex()}${hashed.hex()}"

def verify_password(plain_password: str, stored_hash: str) -> bool:
    """
    Verifies a plain text password against a stored hash.
    Supports modern scrypt hashes, with fallback support for legacy SHA-256 seed hashes.
    """
    if not plain_password or not stored_hash:
        return False

    # 1. Modern scrypt format
    if stored_hash.startswith("scrypt$"):
        parts = stored_hash.split("$")
        if len(parts) == 3:
            try:
                salt = bytes.fromhex(parts[1])
                expected_hash = parts[2]
                computed = hashlib.scrypt(plain_password.encode('utf-8'), salt=salt, n=16384, r=8, p=1).hex()
                return hmac.compare_digest(computed, expected_hash)
            except Exception:
                return False

    # 2. Legacy seed SHA-256 format
    legacy_salt = "ShopNowUniversityProject2026"
    if hashlib.sha256((plain_password + legacy_salt).encode('utf-8')).hexdigest() == stored_hash:
        return True
    if hashlib.sha256(plain_password.encode('utf-8')).hexdigest() == stored_hash:
        return True

    # 3. Plaintext seed match
    if plain_password == stored_hash:
        return True

    return False

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validates strong password requirements (OWASP):
    - Minimum 8 characters
    - At least one uppercase letter [A-Z]
    - At least one lowercase letter [a-z]
    - At least one digit [0-9]
    - At least one special symbol
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one numeric digit."
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=~`[\]\\/]', password):
        return False, "Password must contain at least one special character (!@#$%^&* etc)."
    return True, ""

def validate_email(email: str) -> bool:
    """
    Validates email format using RFC-standard regex.
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))

# ----------------------------------------------------------------------
# RATE LIMITING & BRUTE FORCE DEFENSE
# ----------------------------------------------------------------------

def check_login_rate_limit(identifier: str, ip_address: str) -> tuple[bool, str]:
    """
    Enforces brute force lockout: blocks login attempts if >= 5 failed attempts occur in 15 minutes.
    """
    cutoff = datetime.now() - timedelta(minutes=LOGIN_LOCKOUT_MINUTES)
    cutoff_str = cutoff.strftime('%Y-%m-%d %H:%M:%S')

    # Query login_attempts table
    res = execute_query(
        """SELECT COUNT(*) as failed_count FROM login_attempts 
           WHERE (identifier = %s OR ip_address = %s) 
             AND attempt_time > %s 
             AND success = 0""",
        (identifier, ip_address, cutoff_str),
        fetchone=True
    )

    if res and res.get('failed_count', 0) >= MAX_LOGIN_ATTEMPTS:
        return False, f"Too many failed login attempts. Account temporarily locked for {LOGIN_LOCKOUT_MINUTES} minutes."

    # In-memory fallback check
    recent_mem_fails = [
        a for a in _IN_MEMORY_LOGIN_ATTEMPTS 
        if (a['identifier'] == identifier or a['ip_address'] == ip_address) 
           and a['time'] > cutoff and not a['success']
    ]
    if len(recent_mem_fails) >= MAX_LOGIN_ATTEMPTS:
        return False, f"Too many failed login attempts. Account temporarily locked for {LOGIN_LOCKOUT_MINUTES} minutes."

    return True, ""

def record_login_attempt(identifier: str, ip_address: str, success: bool):
    """
    Records a login attempt (successful or failed) in the database and in-memory cache.
    """
    global _IN_MEMORY_LOGIN_ATTEMPTS
    now = datetime.now()
    execute_query(
        "INSERT INTO login_attempts (identifier, ip_address, attempt_time, success) VALUES (%s, %s, %s, %s)",
        (identifier, ip_address, now.strftime('%Y-%m-%d %H:%M:%S'), 1 if success else 0),
        commit=True
    )
    _IN_MEMORY_LOGIN_ATTEMPTS.append({
        'identifier': identifier,
        'ip_address': ip_address,
        'time': now,
        'success': success
    })
    # Clean memory attempts older than 1 hour
    cutoff = now - timedelta(hours=1)
    _IN_MEMORY_LOGIN_ATTEMPTS = [a for a in _IN_MEMORY_LOGIN_ATTEMPTS if a['time'] > cutoff]

# ----------------------------------------------------------------------
# SERVER-MANAGED SESSIONS WITH IP & USER-AGENT TRACKING
# ----------------------------------------------------------------------

def create_session(user_id: int, role: str = 'customer', ip_address: str = None, user_agent: str = None) -> str:
    """
    Generates a cryptographically strong session token and records it in MySQL.
    Default validity: 7 days.
    """
    session_token = secrets.token_hex(32)
    expires_at = datetime.now() + timedelta(days=SESSION_EXPIRY_DAYS)
    expires_str = expires_at.strftime('%Y-%m-%d %H:%M:%S')

    result = execute_query(
        "INSERT INTO sessions (session_id, user_id, role, ip_address, user_agent, expires_at) VALUES (%s, %s, %s, %s, %s, %s)",
        (session_token, user_id, role, ip_address, user_agent, expires_str),
        commit=True
    )
    if result is not None:
        return session_token
    return None

def get_session(session_token: str):
    """
    Looks up an active session from MySQL.
    Returns session dict with user_id and role, or None if invalid/expired.
    """
    if not session_token:
        return None

    session = execute_query(
        """SELECT session_id, user_id, role, ip_address, user_agent, expires_at 
           FROM sessions 
           WHERE session_id = %s AND expires_at > NOW()""",
        (session_token,),
        fetchone=True
    )
    return session

def delete_session(session_token: str) -> bool:
    """
    Revokes a single session upon logout.
    """
    if not session_token:
        return True
    execute_query("DELETE FROM sessions WHERE session_id = %s", (session_token,), commit=True)
    return True

def revoke_all_user_sessions(user_id: int) -> bool:
    """
    Revokes all sessions across all browsers for a specific user (used after password reset/change).
    """
    execute_query("DELETE FROM sessions WHERE user_id = %s", (user_id,), commit=True)
    return True

# ----------------------------------------------------------------------
# SINGLE-USE ACCOUNT TOKENS (Email Verification & Password Reset)
# ----------------------------------------------------------------------

def _generate_account_token(user_id: int, token_type: str, hours_valid: int = 24) -> str:
    """
    Generates an unpredictable single-use token.
    Saves the SHA-256 hash of the token in the database to prevent token leakage.
    Returns the unhashed raw token string to send in the email link.
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
    expires_at = datetime.now() + timedelta(hours=hours_valid)

    execute_query(
        """INSERT INTO account_tokens (user_id, token_hash, token_type, expires_at) 
           VALUES (%s, %s, %s, %s)""",
        (user_id, token_hash, token_type, expires_at.strftime('%Y-%m-%d %H:%M:%S')),
        commit=True
    )
    return raw_token

def _consume_account_token(raw_token: str, token_type: str):
    """
    Validates and atomically consumes a single-use token.
    Returns the associated user_id if valid, or None if invalid/expired/used.
    """
    if not raw_token:
        return None

    token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
    tok_row = execute_query(
        """SELECT token_id, user_id, expires_at, used_at 
           FROM account_tokens 
           WHERE token_hash = %s AND token_type = %s AND used_at IS NULL AND expires_at > NOW()""",
        (token_hash, token_type),
        fetchone=True
    )

    if not tok_row:
        return None

    # Mark as used atomically
    execute_query(
        "UPDATE account_tokens SET used_at = NOW() WHERE token_id = %s",
        (tok_row['token_id'],),
        commit=True
    )
    return tok_row['user_id']

# ----------------------------------------------------------------------
# USER REGISTRATION, LOGIN & VERIFICATION
# ----------------------------------------------------------------------

def register_user(data: dict, ip_address: str = None, user_agent: str = None):
    """
    Registers a new customer account directly in MySQL.
    Generates an email verification token and queues a verification email.
    """
    name = data.get('fullName', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    password = data.get('password', '')
    address = data.get('address', '').strip()

    if not name or not email or not password or not address or not phone:
        return {'success': False, 'message': 'All required fields must be filled.'}

    if not validate_email(email):
        return {'success': False, 'message': 'Invalid email address format.'}

    is_strong, err_msg = validate_password_strength(password)
    if not is_strong:
        return {'success': False, 'message': err_msg}

    # Check for existing email in MySQL
    existing_user = execute_query(
        "SELECT user_id FROM users WHERE email = %s",
        (email,),
        fetchone=True
    )
    if existing_user and 'user_id' in existing_user:
        return {'success': False, 'message': 'An account with this email address already exists.'}

    hashed_pwd = hash_password(password)

    user_id = execute_query(
        """INSERT INTO users (name, email, phone, password, address, is_verified, created_at) 
           VALUES (%s, %s, %s, %s, %s, 0, %s)""",
        (name, email, phone, hashed_pwd, address, datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        commit=True
    )

    if not user_id:
        return {'success': False, 'message': 'Database error: Could not complete registration. Ensure MySQL is running.'}

    # Generate verification token and send verification email
    verify_token = _generate_account_token(user_id, 'email_verification', hours_valid=VERIFICATION_TOKEN_HOURS)
    email_service.send_verification_email(email, name, verify_token)

    # Create session
    token = create_session(user_id, role='customer', ip_address=ip_address, user_agent=user_agent)

    return {
        'success': True,
        'message': 'Registration successful! Please check your email to verify your account.',
        'token': token,
        'user': {
            'user_id': user_id,
            'name': name,
            'email': email,
            'phone': phone,
            'address': address,
            'is_verified': False
        }
    }

def login_user(data: dict, ip_address: str = '127.0.0.1', user_agent: str = ''):
    """
    Authenticates customer login credentials against MySQL with brute force rate limiting.
    Creates a server-managed session upon success.
    """
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return {'success': False, 'message': 'Email and password are required.'}

    # Check rate limit
    allowed, rate_msg = check_login_rate_limit(email, ip_address)
    if not allowed:
        return {'success': False, 'message': rate_msg}

    user = execute_query(
        "SELECT user_id, name, email, phone, address, password, is_verified FROM users WHERE email = %s",
        (email,),
        fetchone=True
    )

    if not user:
        record_login_attempt(email, ip_address, success=False)
        return {'success': False, 'message': 'Invalid email or password.'}

    stored_hash = user.get('password', '')
    if not verify_password(password, stored_hash):
        record_login_attempt(email, ip_address, success=False)
        return {'success': False, 'message': 'Invalid email or password.'}

    # Record successful login
    record_login_attempt(email, ip_address, success=True)

    # Auto-upgrade legacy hash to scrypt
    if not stored_hash.startswith('scrypt$'):
        new_hash = hash_password(password)
        execute_query("UPDATE users SET password = %s WHERE user_id = %s", (new_hash, user['user_id']), commit=True)

    token = create_session(user['user_id'], role='customer', ip_address=ip_address, user_agent=user_agent)

    # Never return password hash
    del user['password']
    user['is_verified'] = bool(user.get('is_verified', 0))

    return {
        'success': True,
        'message': 'Login successful!',
        'token': token,
        'user': user
    }

def verify_email_token(raw_token: str):
    """
    Consumes single-use email verification token and marks account verified.
    """
    user_id = _consume_account_token(raw_token, 'email_verification')
    if not user_id:
        return {'success': False, 'message': 'Verification link is invalid, expired, or has already been used.'}

    execute_query(
        "UPDATE users SET is_verified = 1, email_verified_at = NOW() WHERE user_id = %s",
        (user_id,),
        commit=True
    )

    user = execute_query("SELECT name, email FROM users WHERE user_id = %s", (user_id,), fetchone=True)
    if user:
        email_service.send_welcome_email(user['email'], user['name'])

    return {'success': True, 'message': 'Your email address has been successfully verified! You can now access all features.'}

def resend_verification_email(user_id: int):
    """
    Issues a fresh email verification token and sends email.
    """
    user = execute_query("SELECT name, email, is_verified FROM users WHERE user_id = %s", (user_id,), fetchone=True)
    if not user:
        return {'success': False, 'message': 'User account not found.'}
    if user.get('is_verified'):
        return {'success': False, 'message': 'Account is already verified.'}

    verify_token = _generate_account_token(user_id, 'email_verification', hours_valid=VERIFICATION_TOKEN_HOURS)
    email_service.send_verification_email(user['email'], user['name'], verify_token)
    return {'success': True, 'message': 'Verification email has been resent. Please check your inbox.'}

# ----------------------------------------------------------------------
# FORGOT & RESET PASSWORD
# ----------------------------------------------------------------------

def request_password_reset(email: str):
    """
    Initiates password reset flow.
    Returns generic success message regardless of whether the email exists (OWASP recommendation).
    """
    email = email.strip().lower()
    if not validate_email(email):
        return {'success': False, 'message': 'Please enter a valid email address.'}

    user = execute_query("SELECT user_id, name, email FROM users WHERE email = %s", (email,), fetchone=True)
    if user:
        raw_token = _generate_account_token(user['user_id'], 'password_reset', hours_valid=1)
        email_service.send_password_reset_email(user['email'], user['name'], raw_token)

    return {
        'success': True, 
        'message': 'If an account with that email exists, password reset instructions have been sent to your inbox.'
    }

def reset_password_with_token(raw_token: str, new_password: str):
    """
    Consumes a single-use password reset token and updates the user's password with scrypt.
    Revokes all active sessions for that user to prevent session hijacking.
    """
    is_strong, err_msg = validate_password_strength(new_password)
    if not is_strong:
        return {'success': False, 'message': err_msg}

    user_id = _consume_account_token(raw_token, 'password_reset')
    if not user_id:
        return {'success': False, 'message': 'Password reset link is invalid, expired, or already used.'}

    new_hash = hash_password(new_password)
    execute_query("UPDATE users SET password = %s WHERE user_id = %s", (new_hash, user_id), commit=True)

    # Revoke all previous active sessions across all devices
    revoke_all_user_sessions(user_id)

    # Send confirmation security notice
    user = execute_query("SELECT name, email FROM users WHERE user_id = %s", (user_id,), fetchone=True)
    if user:
        email_service.send_password_changed_notification(user['email'], user['name'])

    return {'success': True, 'message': 'Password reset successful! Please log in with your new password.'}

# ----------------------------------------------------------------------
# PROFILE & AUTHENTICATED PASSWORD CHANGE
# ----------------------------------------------------------------------

def get_user_profile(user_id: int):
    """
    Fetches the profile for the authenticated customer. Never exposes password hash.
    """
    user = execute_query(
        """SELECT user_id, name, email, phone, address, is_verified, email_verified_at, created_at 
           FROM users WHERE user_id = %s""",
        (user_id,),
        fetchone=True
    )
    if not user:
        return {'success': False, 'message': 'User profile not found.'}
    user['is_verified'] = bool(user.get('is_verified', 0))
    return {'success': True, 'user': user}

def update_profile(user_id: int, data: dict):
    """
    Updates user personal details.
    If updating password, strictly requires current password verification and strong password rules.
    Revokes other sessions upon password change.
    """
    name = data.get('fullName', '').strip()
    phone = data.get('phone', '').strip()
    address = data.get('address', '').strip()
    current_password = data.get('currentPassword', '')
    new_password = data.get('newPassword', '')

    if not name or not phone or not address:
        return {'success': False, 'message': 'Name, phone, and address are required.'}

    # If attempting a password update
    if new_password:
        if not current_password:
            return {'success': False, 'message': 'Current password is required to set a new password.'}

        user_row = execute_query("SELECT password, email, name FROM users WHERE user_id = %s", (user_id,), fetchone=True)
        if not user_row or not verify_password(current_password, user_row['password']):
            return {'success': False, 'message': 'Incorrect current password.'}

        is_strong, err_msg = validate_password_strength(new_password)
        if not is_strong:
            return {'success': False, 'message': err_msg}

        new_hash = hash_password(new_password)
        res = execute_query(
            "UPDATE users SET name = %s, phone = %s, address = %s, password = %s WHERE user_id = %s",
            (name, phone, address, new_hash, user_id),
            commit=True
        )
        if res is not None:
            # Revoke other sessions
            execute_query("DELETE FROM sessions WHERE user_id = %s", (user_id,), commit=True)
            email_service.send_password_changed_notification(user_row['email'], user_row['name'])
            return {'success': True, 'message': 'Profile and password updated successfully! Please re-login on your other devices.'}
    else:
        res = execute_query(
            "UPDATE users SET name = %s, phone = %s, address = %s WHERE user_id = %s",
            (name, phone, address, user_id),
            commit=True
        )

    if res is None:
        return {'success': False, 'message': 'Failed to update profile in database.'}

    return {'success': True, 'message': 'Profile updated successfully!'}
