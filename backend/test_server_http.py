"""
ShopNow - HTTP Server Live Endpoint Tests
"""

import urllib.request
import urllib.error
import json

BASE_URL = "http://127.0.0.1:8000"

def test_url(url):
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            data = resp.read()
            print(f"PASS: {url} -> Status {resp.status}, Content-Type: {resp.headers.get('Content-Type')}")
            return resp.status, data
    except urllib.error.HTTPError as e:
        data = e.read()
        print(f"HTTPError: {url} -> Status {e.code}")
        return e.code, data
    except Exception as e:
        print(f"Error: {url} -> {e}")
        return None, None

def run_tests():
    print("--- 1. Testing Static File Serving ---")
    status, _ = test_url(f"{BASE_URL}/")
    assert status == 200, f"Expected 200, got {status}"

    status, _ = test_url(f"{BASE_URL}/css/style.css")
    assert status == 200, f"Expected 200, got {status}"

    status, _ = test_url(f"{BASE_URL}/js/main.js")
    assert status == 200, f"Expected 200, got {status}"

    status, _ = test_url(f"{BASE_URL}/images/phone.jpg")
    assert status == 200, f"Expected 200, got {status}"

    print("\n--- 2. Testing Path Traversal Guard ---")
    status, _ = test_url(f"{BASE_URL}/../../backend/config.py")
    assert status in [403, 404], f"Expected 403 or 404, got {status}"

    print("\n--- 3. Testing Authentication & Session Guards ---")
    # /api/cart should require customer session (401)
    status, body = test_url(f"{BASE_URL}/api/cart")
    assert status == 401, f"Expected 401 for unauthenticated cart, got {status}"
    data = json.loads(body.decode('utf-8'))
    assert data['success'] is False
    assert "Authentication required" in data['message']
    print("Unauthenticated /api/cart successfully blocked with 401!")

    # /api/wishlist should require customer session (401)
    status, body = test_url(f"{BASE_URL}/api/wishlist")
    assert status == 401, f"Expected 401 for unauthenticated wishlist, got {status}"
    data = json.loads(body.decode('utf-8'))
    assert data['success'] is False
    assert "Authentication required" in data['message']
    print("Unauthenticated /api/wishlist successfully blocked with 401!")

    # /api/admin/dashboard should require admin session (403)
    status, body = test_url(f"{BASE_URL}/api/admin/dashboard")
    assert status == 403, f"Expected 403 for unauthorized admin dashboard, got {status}"
    data = json.loads(body.decode('utf-8'))
    assert data['success'] is False
    assert "Administrator privileges required" in data['message']
    print("Unauthorized /api/admin/dashboard successfully blocked with 403!")

    # /api/admin/reviews should require admin session (403)
    status, body = test_url(f"{BASE_URL}/api/admin/reviews")
    assert status == 403, f"Expected 403 for unauthorized admin reviews, got {status}"
    data = json.loads(body.decode('utf-8'))
    assert data['success'] is False
    assert "Administrator privileges required" in data['message']
    print("Unauthorized /api/admin/reviews successfully blocked with 403!")

    # /api/orders should require customer session (401)
    status, body = test_url(f"{BASE_URL}/api/orders")
    assert status == 401, f"Expected 401 for unauthenticated orders, got {status}"
    print("Unauthenticated /api/orders successfully blocked with 401!")

    print("\n--- 4. Testing Unknown Endpoints ---")
    status, body = test_url(f"{BASE_URL}/api/unknown-endpoint")
    assert status == 404, f"Expected 404, got {status}"
    print("Unknown endpoint properly returned 404!")

    print("\nALL HTTP SERVER INTEGRATION TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    run_tests()
