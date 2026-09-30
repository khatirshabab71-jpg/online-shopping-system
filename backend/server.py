"""
ShopNow - Online Shopping System
Pure Python HTTP Web & API Server
Built with built-in modules: http.server, json, urllib, os, sys
"""

import os
import sys
import json
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Import Backend Business Logic Modules
from config import SERVER_HOST, SERVER_PORT, FRONTEND_DIR
import auth
import products
import cart
import orders
import admin

class ShopNowRequestHandler(BaseHTTPRequestHandler):
    """
    Custom HTTP Request Handler inheriting from Python's built-in BaseHTTPRequestHandler.
    Handles static website files (HTML, CSS, JS, Images) & JSON REST API Endpoints.
    """

    def _set_headers(self, status_code=200, content_type='application/json'):
        """
        Sets HTTP Response status code, CORS headers, and Content-Type.
        """
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_OPTIONS(self):
        """
        Handles pre-flight CORS OPTIONS requests for browser safety.
        """
        self._set_headers(200, 'text/plain')

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
        content_length = int(self.headers.get('Content-Length', 0))
        body_bytes = self.rfile.read(content_length)
        
        post_data = {}
        if body_bytes:
            try:
                post_data = json.loads(body_bytes.decode('utf-8'))
            except json.JSONDecodeError:
                self._set_headers(400)
                self.wfile.write(json.dumps({'success': False, 'message': 'Invalid JSON format'}).encode('utf-8'))
                return

        if path.startswith('/api/'):
            self._handle_api_post(path, post_data)
        else:
            self._set_headers(44)
            self.wfile.write(json.dumps({'success': False, 'message': 'Endpoint not found'}).encode('utf-8'))

    def _handle_api_get(self, path, query):
        """
        Routes API GET Requests
        """
        response_data = {}

        if path == '/api/products':
            category_id = query.get('category', [None])[0]
            search_q = query.get('search', [None])[0]
            sort_by = query.get('sort', [None])[0]
            in_stock = query.get('in_stock', ['false'])[0].lower() == 'true'

            prods = products.get_all_products(category_id, search_q, sort_by, in_stock)
            response_data = {'success': True, 'count': len(prods), 'products': prods}

        elif path == '/api/product':
            p_id = query.get('id', [None])[0]
            prod = products.get_product_by_id(p_id)
            if prod:
                response_data = {'success': True, 'product': prod}
            else:
                response_data = {'success': False, 'message': 'Product not found'}

        elif path == '/api/cart':
            u_id = query.get('user_id', ['GUEST'])[0]
            user_cart = cart.get_user_cart(u_id)
            response_data = {'success': True, 'cart': user_cart}

        elif path == '/api/orders':
            u_id = query.get('user_id', [101])[0]
            user_orders = orders.get_user_orders(u_id)
            response_data = {'success': True, 'orders': user_orders}

        elif path == '/api/order':
            o_id = query.get('id', [None])[0]
            ord_item = orders.get_order_by_id(o_id)
            if ord_item:
                response_data = {'success': True, 'order': ord_item}
            else:
                response_data = {'success': False, 'message': 'Order not found'}

        elif path == '/api/admin/dashboard':
            metrics = admin.get_dashboard_metrics()
            response_data = {'success': True, 'metrics': metrics}

        elif path == '/api/admin/users':
            response_data = {'success': True, 'users': auth.MOCK_USERS}

        elif path == '/api/admin/orders':
            response_data = {'success': True, 'orders': orders.MOCK_ORDERS}

        else:
            self._set_headers(44)
            response_data = {'success': False, 'message': 'API GET endpoint not found'}
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            return

        self._set_headers(200)
        self.wfile.write(json.dumps(response_data).encode('utf-8'))

    def _handle_api_post(self, path, data):
        """
        Routes API POST Requests
        """
        response_data = {}

        if path == '/api/register':
            response_data = auth.register_user(data)

        elif path == '/api/login':
            response_data = auth.login_user(data)

        elif path == '/api/profile/update':
            response_data = auth.update_profile(data)

        elif path == '/api/cart/add':
            response_data = cart.add_to_cart(data)

        elif path == '/api/cart/update':
            response_data = cart.update_cart_quantity(data)

        elif path == '/api/cart/delete':
            response_data = cart.remove_from_cart(data)

        elif path == '/api/checkout':
            response_data = orders.create_order(data)

        elif path == '/api/admin/login':
            response_data = admin.admin_login(data)

        elif path == '/api/admin/product/add':
            response_data = admin.add_product(data)

        elif path == '/api/admin/product/update':
            response_data = admin.update_product(data)

        elif path == '/api/admin/product/delete':
            p_id = data.get('productId')
            response_data = admin.delete_product(p_id)

        elif path == '/api/admin/order/status':
            o_id = data.get('order_id')
            status = data.get('status')
            response_data = admin.update_order_status(o_id, status)

        else:
            self._set_headers(404)
            response_data = {'success': False, 'message': 'API POST endpoint not found'}
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            return

        self._set_headers(200)
        self.wfile.write(json.dumps(response_data).encode('utf-8'))

    def _serve_static_file(self, req_path):
        """
        Serves HTML, CSS, JS, and image files directly from frontend directory.
        """
        if req_path == '/' or req_path == '':
            req_path = '/index.html'

        # Relativize path
        clean_path = req_path.lstrip('/')
        file_path = os.path.join(FRONTEND_DIR, clean_path)

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
    Initializes and starts the pure Python HTTP Server.
    """
    server_address = (SERVER_HOST, SERVER_PORT)
    httpd = HTTPServer(server_address, ShopNowRequestHandler)
    print("=" * 70)
    print(f"SHOPNOW PYTHON BACKEND SERVER RUNNING AT: http://localhost:{SERVER_PORT}")
    print(f"Serving static storefront from: {FRONTEND_DIR}")
    print("=" * 70)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server gracefully...")
        httpd.server_close()
        sys.exit(0)

if __name__ == '__main__':
    run_server()
