"""
ShopNow - Online Shopping System
Pure Python HTTP Web & REST API Server (Phase 2 Production Hardened)
Built with built-in modules: http.server, json, urllib, os, sys, ssl, decimal, datetime
"""

import os
import sys
import ssl
import json
import decimal
import datetime
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Import Backend Business Logic Modules
from config import (
    SERVER_HOST, SERVER_PORT, FRONTEND_DIR, 
    USE_HTTPS, SSL_CERT_FILE, SSL_KEY_FILE
)
from database import init_db_schema
import auth
import products
import cart
import orders
import admin
import wishlist
import reviews

class CustomJSONEncoder(json.JSONEncoder):
    """
    JSON encoder that handles MySQL Decimal objects and datetime/date types cleanly.
    """
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        return super().default(obj)

class ShopNowRequestHandler(BaseHTTPRequestHandler):
    """
    Custom HTTP Request Handler inheriting from Python's built-in BaseHTTPRequestHandler.
    Serves static storefront files (HTML, CSS, JS, Images) and routes JSON REST API Endpoints.
    Includes OWASP security headers and path traversal mitigation.
    """

    def _set_headers(self, status_code=200, content_type='application/json'):
        """
        Sets HTTP Response status code, CORS headers, Content-Type, and OWASP Security Headers.
        """
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE, PATCH')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Session-Token')
        
        # OWASP Security Headers
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('X-XSS-Protection', '1; mode=block')
        self.send_header('Referrer-Policy', 'strict-origin-when-cross-origin')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self';")
        self.end_headers()

    def do_OPTIONS(self):
        """
        Handles pre-flight CORS OPTIONS requests for browser safety.
        """
        self._set_headers(200, 'text/plain')

    def _get_client_ip(self):
        """
        Extracts client IP address safely considering reverse proxies.
        """
        forwarded = self.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
        return self.client_address[0] if self.client_address else '127.0.0.1'

    def _get_auth_session(self):
        """
        Extracts session token from Authorization: Bearer <token> or X-Session-Token header.
        Verifies session in MySQL and returns session record dict, or None if invalid.
        """
        auth_header = self.headers.get('Authorization', '')
        token = ''
        if auth_header.startswith('Bearer '):
            token = auth_header[7:].strip()
        elif 'X-Session-Token' in self.headers:
            token = self.headers.get('X-Session-Token', '').strip()

        if not token:
            return None

        return auth.get_session(token)

    def _send_json(self, data, status_code=200):
        """
        Sends JSON response using the custom JSON encoder.
        """
        self._set_headers(status_code, 'application/json')
        payload = json.dumps(data, cls=CustomJSONEncoder).encode('utf-8')
        self.wfile.write(payload)

    def do_GET(self):
        """
        Handles HTTP GET requests for static files and REST API endpoints.
        """
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)

        # ------------------------------------------------------------------
        # 1. REST API GET ENDPOINTS
        # ------------------------------------------------------------------
        if path.startswith('/api/'):
            self._handle_api_get(path, query_params)
            return

        # ------------------------------------------------------------------
        # 2. STATIC FILE SERVING (HTML, CSS, JS, IMAGES)
        # ------------------------------------------------------------------
        self._serve_static_file(path)

    def do_POST(self):
        """
        Handles HTTP POST requests for REST API endpoints.
        """
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        # Read JSON body payload
        try:
            content_length = int(self.headers.get('Content-Length', 0))
        except ValueError:
            self._send_json({'success': False, 'message': 'Invalid content length'}, 400)
            return
        if content_length < 0 or content_length > 1024 * 1024:
            self._send_json({'success': False, 'message': 'Invalid request size'}, 413)
            return
        post_data = {}

        if content_length > 0:
            body_bytes = self.rfile.read(content_length)
            try:
                post_data = json.loads(body_bytes.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                self._send_json({'success': False, 'message': 'Invalid JSON format in request body'}, 400)
                return

        if not isinstance(post_data, dict):
            self._send_json({'success': False, 'message': 'JSON body must be an object'}, 400)
            return

        if path.startswith('/api/'):
            self._handle_api_post(path, post_data)
        else:
            self._send_json({'success': False, 'message': 'Endpoint not found'}, 404)

    def _handle_api_get(self, path, query):
        """
        Routes API GET Requests
        """
        session = self._get_auth_session()

        # ------------------------------------------------------------------
        # PUBLIC GET ENDPOINTS
        # ------------------------------------------------------------------
        if path == '/api/products':
            category_id = query.get('category', [None])[0]
            search_q = query.get('search', [None])[0]
            sort_by = query.get('sort', [None])[0]
            in_stock = query.get('in_stock', ['false'])[0].lower() == 'true'
            min_price = query.get('min_price', [None])[0]
            max_price = query.get('max_price', [None])[0]
            min_rating = query.get('min_rating', [None])[0]
            page = query.get('page', [1])[0]
            limit = query.get('limit', [12])[0]

            res = products.get_all_products(
                category_id=category_id, 
                search_query=search_q, 
                sort_by=sort_by, 
                in_stock=in_stock,
                min_price=min_price,
                max_price=max_price,
                min_rating=min_rating,
                page=page,
                limit=limit
            )
            if res is None:
                self._send_json({'success': False, 'message': 'Database connection error. Could not load products.'}, 500)
                return

            self._send_json({
                'success': True, 
                'count': len(res['products']),
                'total': res['total'],
                'page': res['page'],
                'limit': res['limit'],
                'total_pages': res['total_pages'],
                'products': res['products']
            })
            return

        elif path == '/api/product':
            p_id = query.get('id', [None])[0]
            if not p_id:
                self._send_json({'success': False, 'message': 'Product ID parameter is required'}, 400)
                return

            prod = products.get_product_by_id(p_id)
            if prod:
                self._send_json({'success': True, 'product': prod})
            else:
                self._send_json({'success': False, 'message': 'Product not found'}, 404)
            return

        elif path == '/api/categories':
            cats = products.get_all_categories()
            if cats is None:
                self._send_json({'success': False, 'message': 'Database error loading categories.'}, 500)
                return
            self._send_json({'success': True, 'categories': cats})
            return

        elif path == '/api/reviews':
            p_id = query.get('product_id', [None])[0]
            if not p_id:
                self._send_json({'success': False, 'message': 'product_id parameter required'}, 400)
                return
            rev_list = reviews.get_product_reviews(p_id)
            self._send_json({'success': True, 'reviews': rev_list})
            return

        elif path == '/api/reviews/summary':
            p_id = query.get('product_id', [None])[0]
            if not p_id:
                self._send_json({'success': False, 'message': 'product_id parameter required'}, 400)
                return
            summary = reviews.get_product_rating_summary(p_id)
            self._send_json({'success': True, 'summary': summary})
            return

        # ------------------------------------------------------------------
        # CUSTOMER AUTH-PROTECTED GET ENDPOINTS
        # ------------------------------------------------------------------
        elif path == '/api/me':
            if not session:
                self._send_json({'success': False, 'message': 'Authentication required. Please log in.'}, 401)
                return
            profile = auth.get_user_profile(session['user_id'])
            self._send_json(profile)
            return

        elif path == '/api/cart':
            if not session:
                self._send_json({'success': False, 'message': 'Authentication required to view cart.'}, 401)
                return
            user_cart = cart.get_user_cart(session['user_id'])
            if user_cart is None:
                self._send_json({'success': False, 'message': 'Database error loading cart.'}, 500)
                return
            self._send_json({'success': True, 'cart': user_cart})
            return

        elif path == '/api/wishlist':
            if not session:
                self._send_json({'success': False, 'message': 'Authentication required to view wishlist.'}, 401)
                return
            user_wishlist = wishlist.get_user_wishlist(session['user_id'])
            if user_wishlist is None:
                self._send_json({'success': False, 'message': 'Database error loading wishlist.'}, 500)
                return
            self._send_json({'success': True, 'wishlist': user_wishlist})
            return

        elif path == '/api/orders':
            if not session:
                self._send_json({'success': False, 'message': 'Authentication required to view orders.'}, 401)
                return
            user_orders = orders.get_user_orders(session['user_id'])
            self._send_json({'success': True, 'orders': user_orders})
            return

        elif path == '/api/order':
            if not session:
                self._send_json({'success': False, 'message': 'Authentication required to view order.'}, 401)
                return

            o_id = query.get('id', [None])[0]
            if not o_id:
                self._send_json({'success': False, 'message': 'Order ID is required'}, 400)
                return

            is_adm = (session.get('role') == 'admin')
            ord_item = orders.get_order_by_id(o_id, user_id=session['user_id'], is_admin=is_adm)

            if ord_item:
                self._send_json({'success': True, 'order': ord_item})
            else:
                self._send_json({'success': False, 'message': 'Order not found or unauthorized'}, 404)
            return

        # ------------------------------------------------------------------
        # ADMIN AUTH-PROTECTED GET ENDPOINTS
        # ------------------------------------------------------------------
        elif path.startswith('/api/admin/'):
            if not session or session.get('role') != 'admin':
                self._send_json({'success': False, 'message': 'Forbidden: Administrator privileges required.'}, 403)
                return

            if path == '/api/admin/dashboard':
                metrics = admin.get_dashboard_metrics()
                if metrics is None:
                    self._send_json({'success': False, 'message': 'Database error loading metrics.'}, 500)
                    return
                self._send_json({'success': True, 'metrics': metrics})

            elif path == '/api/admin/products':
                search_q = query.get('search', [None])[0]
                prods = admin.get_admin_products(search_q)
                self._send_json({'success': True, 'products': prods})

            elif path == '/api/admin/users':
                search_q = query.get('search', [None])[0]
                users = admin.get_admin_users(search_q)
                self._send_json({'success': True, 'users': users})

            elif path == '/api/admin/orders':
                status_f = query.get('status', [None])[0]
                search_q = query.get('search', [None])[0]
                admin_orders = admin.get_admin_orders(status_f, search_q)
                self._send_json({'success': True, 'orders': admin_orders})

            elif path == '/api/admin/reviews':
                search_q = query.get('search', [None])[0]
                revs = reviews.get_admin_reviews(search_q)
                self._send_json({'success': True, 'reviews': revs})

            else:
                self._send_json({'success': False, 'message': 'Admin GET endpoint not found'}, 404)
            return

        else:
            self._send_json({'success': False, 'message': 'API GET endpoint not found'}, 404)

    def _handle_api_post(self, path, data):
        """
        Routes API POST Requests
        """
        session = self._get_auth_session()
        ip_addr = self._get_client_ip()
        user_agent = self.headers.get('User-Agent', '')

        # ------------------------------------------------------------------
        # PUBLIC POST ENDPOINTS
        # ------------------------------------------------------------------
        if path == '/api/register':
            res = auth.register_user(data, ip_address=ip_addr, user_agent=user_agent)
            status_code = 200 if res.get('success') else 400
            self._send_json(res, status_code)
            return

        elif path == '/api/login':
            res = auth.login_user(data, ip_address=ip_addr, user_agent=user_agent)
            status_code = 200 if res.get('success') else 401
            self._send_json(res, status_code)
            return

        elif path == '/api/auth/verify-email':
            token = data.get('token')
            res = auth.verify_email_token(token)
            status_code = 200 if res.get('success') else 400
            self._send_json(res, status_code)
            return

        elif path == '/api/auth/forgot-password':
            email = data.get('email', '')
            res = auth.request_password_reset(email)
            self._send_json(res)
            return

        elif path == '/api/auth/reset-password':
            token = data.get('token', '')
            new_password = data.get('newPassword', '')
            res = auth.reset_password_with_token(token, new_password)
            status_code = 200 if res.get('success') else 400
            self._send_json(res, status_code)
            return

        elif path == '/api/admin/login':
            res = admin.admin_login(data, ip_address=ip_addr, user_agent=user_agent)
            status_code = 200 if res.get('success') else 401
            self._send_json(res, status_code)
            return

        elif path == '/api/logout':
            auth_header = self.headers.get('Authorization', '')
            token = auth_header[7:].strip() if auth_header.startswith('Bearer ') else self.headers.get('X-Session-Token', '').strip()
            auth.delete_session(token)
            self._send_json({'success': True, 'message': 'Logged out successfully.'})
            return

        # ------------------------------------------------------------------
        # CUSTOMER AUTH-PROTECTED POST ENDPOINTS
        # ------------------------------------------------------------------
        customer_routes = [
            '/api/profile/update', '/api/auth/resend-verification',
            '/api/cart/add', '/api/cart/update', '/api/cart/delete', '/api/cart/clear', 
            '/api/wishlist/add', '/api/wishlist/remove', '/api/wishlist/move-to-cart',
            '/api/reviews/add', '/api/reviews/delete',
            '/api/checkout'
        ]

        if path in customer_routes:
            if not session:
                self._send_json({'success': False, 'message': 'Authentication required. Please log in.'}, 401)
                return

            user_id = session['user_id']

            if path == '/api/profile/update':
                res = auth.update_profile(user_id, data)
                self._send_json(res)

            elif path == '/api/auth/resend-verification':
                res = auth.resend_verification_email(user_id)
                self._send_json(res)

            elif path == '/api/cart/add':
                res = cart.add_to_cart(user_id, data)
                self._send_json(res)

            elif path == '/api/cart/update':
                res = cart.update_cart_quantity(user_id, data)
                self._send_json(res)

            elif path == '/api/cart/delete':
                res = cart.remove_from_cart(user_id, data)
                self._send_json(res)

            elif path == '/api/cart/clear':
                res = cart.clear_user_cart(user_id)
                self._send_json(res)

            elif path == '/api/wishlist/add':
                p_id = data.get('product_id')
                res = wishlist.add_to_wishlist(user_id, p_id)
                self._send_json(res)

            elif path == '/api/wishlist/remove':
                p_id = data.get('product_id')
                res = wishlist.remove_from_wishlist(user_id, p_id)
                self._send_json(res)

            elif path == '/api/wishlist/move-to-cart':
                p_id = data.get('product_id')
                res = wishlist.move_to_cart(user_id, p_id)
                self._send_json(res)

            elif path == '/api/reviews/add':
                res = reviews.add_or_update_review(user_id, data)
                status_code = 200 if res.get('success') else 400
                self._send_json(res, status_code)

            elif path == '/api/reviews/delete':
                r_id = data.get('review_id')
                is_admin = (session.get('role') == 'admin')
                res = reviews.delete_review(user_id, r_id, is_admin=is_admin)
                self._send_json(res)

            elif path == '/api/checkout':
                res = orders.create_order(user_id, data)
                status_code = 200 if res.get('success') else 400
                self._send_json(res, status_code)
            return

        # ------------------------------------------------------------------
        # ADMIN AUTH-PROTECTED POST ENDPOINTS
        # ------------------------------------------------------------------
        if path.startswith('/api/admin/'):
            if not session or session.get('role') != 'admin':
                self._send_json({'success': False, 'message': 'Forbidden: Administrator privileges required.'}, 403)
                return

            if path == '/api/admin/product/add':
                res = admin.add_product(data)
                self._send_json(res)

            elif path == '/api/admin/product/update':
                res = admin.update_product(data)
                self._send_json(res)

            elif path == '/api/admin/product/delete':
                p_id = data.get('productId') or data.get('product_id')
                res = admin.delete_product(p_id)
                self._send_json(res)

            elif path == '/api/admin/order/status':
                o_id = data.get('order_id')
                new_status = data.get('status')
                notes = data.get('notes')
                res = admin.update_order_status(o_id, new_status, notes=notes)
                self._send_json(res)

            elif path == '/api/admin/review/delete':
                r_id = data.get('review_id')
                res = reviews.delete_review(session['user_id'], r_id, is_admin=True)
                self._send_json(res)

            else:
                self._send_json({'success': False, 'message': 'Admin POST endpoint not found'}, 404)
            return

        self._send_json({'success': False, 'message': 'API POST endpoint not found'}, 404)

    def _serve_static_file(self, req_path):
        """
        Serves HTML, CSS, JS, and image files safely from frontend directory.
        Includes path traversal mitigation.
        """
        if req_path == '/' or req_path == '':
            req_path = '/index.html'

        clean_path = req_path.lstrip('/')
        file_path = os.path.normpath(os.path.join(FRONTEND_DIR, clean_path))
        abs_frontend = os.path.abspath(FRONTEND_DIR)

        # Path traversal guard
        if not os.path.abspath(file_path).startswith(abs_frontend):
            self._set_headers(403, 'text/html')
            self.wfile.write(b'<h1>403 Forbidden</h1>')
            return

        if not os.path.exists(file_path) or os.path.isdir(file_path):
            self._set_headers(404, 'text/html')
            self.wfile.write(b'<h1>404 Not Found</h1><p>The requested file does not exist on the server.</p>')
            return

        # Determine MIME Content-Type
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            if file_path.endswith('.css'):
                content_type = 'text/css'
            elif file_path.endswith('.js'):
                content_type = 'application/javascript'
            elif file_path.endswith('.svg'):
                content_type = 'image/svg+xml'
            elif file_path.endswith('.json'):
                content_type = 'application/json'
            else:
                content_type = 'application/octet-stream'

        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            self._set_headers(200, content_type)
            self.wfile.write(content)
        except Exception as e:
            self._set_headers(500, 'text/html')
            self.wfile.write(f'<h1>500 Internal Server Error</h1><p>{str(e)}</p>'.encode('utf-8'))

def run_server():
    """
    Initializes database schema updates and starts the pure Python HTTP Server.
    Supports optional TLS / HTTPS for production deployment.
    """
    init_db_schema()

    server_address = (SERVER_HOST, SERVER_PORT)
    httpd = HTTPServer(server_address, ShopNowRequestHandler)

    protocol = "http"
    if USE_HTTPS and SSL_CERT_FILE and SSL_KEY_FILE:
        if os.path.exists(SSL_CERT_FILE) and os.path.exists(SSL_KEY_FILE):
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ctx.load_cert_chain(certfile=SSL_CERT_FILE, keyfile=SSL_KEY_FILE)
            httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
            protocol = "https"
            print("[Security Notice] HTTPS TLS encryption enabled.")

    print("=" * 70)
    print(f"SHOPNOW PYTHON BACKEND RUNNING AT: {protocol}://localhost:{SERVER_PORT}")
    print(f"Serving storefront from: {FRONTEND_DIR}")
    print("API Base URL: /api")
    print("Security Headers: Active (CSP, nosniff, DENY frame, XSS protection)")
    print("=" * 70)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server gracefully...")
        httpd.server_close()
        sys.exit(0)

if __name__ == '__main__':
    run_server()
