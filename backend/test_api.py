"""
ShopNow - Online Shopping System
Automated Test Suite for API Logic, Security, and Database Rules
"""

import os
import sys
import unittest
import decimal
import datetime
import json
import hashlib
import time

# Ensure backend folder is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import auth
from server import CustomJSONEncoder
import config
import email_service

class ShopNowSecurityAndLogicTests(unittest.TestCase):

    def test_scrypt_password_hashing_and_verification(self):
        """Verify that password hashing uses scrypt, generates unique salts, and verifies correctly."""
        password = "SecurePassword123!"
        hash1 = auth.hash_password(password)
        hash2 = auth.hash_password(password)

        # Output format should be scrypt$<salt_hex>$<hash_hex>
        self.assertTrue(hash1.startswith("scrypt$"), "Hash should start with scrypt$")
        self.assertTrue(hash2.startswith("scrypt$"), "Hash should start with scrypt$")
        self.assertNotEqual(hash1, hash2, "Unique random salt per password must produce distinct hashes")

        # Verification tests
        self.assertTrue(auth.verify_password(password, hash1), "Correct password must verify against hash1")
        self.assertTrue(auth.verify_password(password, hash2), "Correct password must verify against hash2")
        self.assertFalse(auth.verify_password("WrongPassword", hash1), "Incorrect password must fail verification")
        self.assertFalse(auth.verify_password("", hash1), "Empty password must fail verification")

    def test_legacy_password_compatibility(self):
        """Verify that legacy SHA-256 seed passwords can still verify for smooth migration."""
        legacy_salt = "ShopNowUniversityProject2026"
        legacy_sha = hashlib.sha256(("123456" + legacy_salt).encode('utf-8')).hexdigest()

        self.assertTrue(auth.verify_password("123456", legacy_sha), "Legacy salted SHA-256 must verify")
        self.assertFalse(auth.verify_password("wrong", legacy_sha), "Wrong password must fail")

        # Plaintext seed admin123
        self.assertTrue(auth.verify_password("admin123", "admin123"), "Plaintext seed admin123 must verify for auto-upgrade")

    def test_password_strength_validator(self):
        """Verify OWASP strong password requirements enforcement."""
        # Short password (< 8 chars)
        ok, msg = auth.validate_password_strength("Pass1!")
        self.assertFalse(ok)
        self.assertIn("at least 8 characters", msg)

        # Missing uppercase
        ok, msg = auth.validate_password_strength("password123!")
        self.assertFalse(ok)
        self.assertIn("uppercase letter", msg)

        # Missing lowercase
        ok, msg = auth.validate_password_strength("PASSWORD123!")
        self.assertFalse(ok)
        self.assertIn("lowercase letter", msg)

        # Missing number
        ok, msg = auth.validate_password_strength("Password!@#")
        self.assertFalse(ok)
        self.assertIn("numeric digit", msg)

        # Missing special character
        ok, msg = auth.validate_password_strength("Password123")
        self.assertFalse(ok)
        self.assertIn("special character", msg)

        # Strong valid password
        ok, msg = auth.validate_password_strength("ShopNow#2026Secure")
        self.assertTrue(ok)
        self.assertEqual(msg, "")

    def test_email_validation(self):
        """Verify RFC-compliant email regex validation."""
        self.assertTrue(auth.validate_email("test@example.com"))
        self.assertTrue(auth.validate_email("student.university@sub.domain.edu"))
        self.assertFalse(auth.validate_email("invalid-email"))
        self.assertFalse(auth.validate_email("@missing-user.com"))
        self.assertFalse(auth.validate_email("user@no-tld"))
        self.assertFalse(auth.validate_email(""))

    def test_login_rate_limiting_defense(self):
        """Verify that repeated failed login attempts trigger the brute-force lockout."""
        test_ip = "192.168.1.99"
        test_user = "brute_target@example.com"

        # Initially, rate limit check should pass
        allowed, msg = auth.check_login_rate_limit(test_user, test_ip)
        self.assertTrue(allowed, "Initial login should be permitted")

        # Record 5 consecutive failed login attempts
        for _ in range(5):
            auth.record_login_attempt(test_user, test_ip, success=False)

        # 6th attempt must be blocked by rate limiter
        allowed, msg = auth.check_login_rate_limit(test_user, test_ip)
        self.assertFalse(allowed, "After 5 failed attempts, login must be locked out")
        self.assertIn("Too many failed login attempts", msg)

    def test_custom_json_encoder(self):
        """Verify CustomJSONEncoder handles Decimal and datetime without raising TypeError."""
        data = {
            'price': decimal.Decimal('699.99'),
            'created_at': datetime.datetime(2026, 9, 1, 10, 30, 0),
            'order_date': datetime.date(2026, 9, 1),
            'name': 'Smartphone'
        }

        serialized = json.dumps(data, cls=CustomJSONEncoder)
        self.assertIn('"price": 699.99', serialized)
        self.assertIn('"created_at": "2026-09-01T10:30:00"', serialized)
        self.assertIn('"order_date": "2026-09-01"', serialized)

    def test_email_service_templates_and_outbox(self):
        """Verify email notification templates and background outbox logging."""
        outbox_file = email_service.OUTBOX_LOG_FILE

        # Test verification email
        email_service.send_verification_email("customer@shopnow.edu", "Alice", "test_verification_token_123")
        time.sleep(0.1) # Allow thread to log

        # Test password reset email
        email_service.send_password_reset_email("customer@shopnow.edu", "Alice", "test_reset_token_456")
        time.sleep(0.1)

        # Test order placed email
        email_service.send_order_placed_email(
            "customer@shopnow.edu", "Alice", 1001, 714.99, "123 University Ave",
            [{'product_name': 'Pro Wireless Smartphone', 'quantity': 1, 'price': 699.99}]
        )
        time.sleep(0.1)

        self.assertTrue(os.path.exists(outbox_file), "Email outbox log file must be created")
        with open(outbox_file, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn("Verify Your ShopNow Customer Account", content)
        self.assertIn("Reset Your ShopNow Password", content)
        self.assertIn("Order Confirmation #ORD-1001", content)
        self.assertIn("customer@shopnow.edu", content)

    def test_input_validation_rules(self):
        """Verify registration input validation catches short passwords and empty fields."""
        res_empty = auth.register_user({'fullName': '', 'email': 'test@test.com', 'password': '123'})
        self.assertFalse(res_empty['success'])
        self.assertIn('required fields', res_empty['message'])

        res_weak = auth.register_user({
            'fullName': 'John',
            'email': 'valid@test.com',
            'phone': '12345678',
            'password': 'short',
            'address': 'Campus'
        })
        self.assertFalse(res_weak['success'])
        self.assertIn('at least 8 characters', res_weak['message'])

if __name__ == '__main__':
    unittest.main()
